"""Offline smoke example for the generated Blob worker (#481).

Generates the documented ``afs worker blob`` project into a temporary directory, imports it the
way the Functions worker does, and calls the generated handler with a fake
``azure.functions.InputStream`` backed by in-memory bytes. No Storage account, Azurite,
credentials, network or Functions host is needed. This verifies handler/service logic and how the
trigger is declared; blob event delivery, polling latency, blob receipts and the real stream
implementation need a real host and Azure Storage.
"""

from __future__ import annotations

from collections.abc import Iterator
import contextlib
import io
import logging
from pathlib import Path
import sys

import azure.functions as func
import pytest
from typer.testing import CliRunner

from azure_functions_scaffold.cli import app

runner = CliRunner()


class FakeInputStream(func.InputStream):
    """In-memory stand-in for the stream the host passes to a blob trigger."""

    def __init__(self, name: str, data: bytes) -> None:
        self._name = name
        self._data = data
        self._buffer = io.BytesIO(data)

    def read(self, size: int | None = -1) -> bytes:
        return self._buffer.read(size)

    @property
    def name(self) -> str | None:
        return self._name

    @property
    def length(self) -> int | None:
        return len(self._data)

    @property
    def uri(self) -> str | None:
        return None


@contextlib.contextmanager
def _imported(project_root: Path) -> Iterator[None]:
    """Make the generated project importable, then forget its modules again."""
    sys.path.insert(0, str(project_root))
    try:
        yield
    finally:
        sys.path.remove(str(project_root))
        for name in list(sys.modules):
            if name in {"app", "function_app"} or name.startswith("app."):
                del sys.modules[name]


@pytest.fixture
def worker_root(tmp_path: Path) -> Path:
    result = runner.invoke(
        app, ["worker", "blob", "blob-worker", "--destination", str(tmp_path), "--no-git"]
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "blob-worker"


def test_handler_processes_a_fake_input_stream(
    worker_root: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with _imported(worker_root):
        from app.functions.blob import process_blob

        blob = FakeInputStream("samples-workitems/report.csv", b"id,total\n1,9\n")
        with caplog.at_level(logging.INFO):
            process_blob(blob)

    assert [record.getMessage() for record in caplog.records] == [
        "Processed blob samples-workitems/report.csv (13 bytes)"
    ]


def test_service_describes_name_and_length(worker_root: Path) -> None:
    with _imported(worker_root):
        from app.services.blob_service import describe_blob

        assert (
            describe_blob(FakeInputStream("c/empty.bin", b""))
            == "Processed blob c/empty.bin (0 bytes)"
        )


def test_function_app_indexes_the_blob_trigger(worker_root: Path) -> None:
    with _imported(worker_root):
        import function_app

        functions = function_app.app.get_functions()
        assert [function.get_function_name() for function in functions] == ["process_blob"]
        trigger = functions[0].get_trigger()
        assert trigger is not None
        binding = trigger.get_dict_repr()

    assert binding["type"] == "blobTrigger"
    assert binding["name"] == "blob"
    assert binding["path"] == "samples-workitems/{name}"
    assert binding["connection"] == "AzureWebJobsStorage"


def test_templates_guide_documents_the_offline_command() -> None:
    guide = (Path(__file__).resolve().parent.parent / "docs" / "guide" / "templates.md").read_text(
        encoding="utf-8"
    )
    section = guide.split("### Blob Template")[1].split("\n### ")[0]
    section = " ".join(section.split())

    assert "pytest tests/test_worker_smoke_blob.py" in section
    assert "does not require" in section and "Functions host" in section
