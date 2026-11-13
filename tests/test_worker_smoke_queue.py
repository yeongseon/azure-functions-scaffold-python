"""Offline smoke example for the generated Queue worker (#480).

Generates the documented ``afs worker queue`` project into a temporary directory, imports it the
way the Functions worker does, and calls the generated handler with a synthetic
``azure.functions.QueueMessage``. No Storage account, Azurite, credentials, network or Functions
host is needed. This verifies handler/service logic and how the trigger is declared; polling,
visibility timeout, dequeue counts and poison-queue behavior need a real host and Storage Queue.
"""

from __future__ import annotations

from collections.abc import Iterator
import contextlib
import logging
from pathlib import Path
import sys

import azure.functions as func
import pytest
from typer.testing import CliRunner

from azure_functions_scaffold.cli import app

runner = CliRunner()


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
        app, ["worker", "queue", "queue-worker", "--destination", str(tmp_path), "--no-git"]
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "queue-worker"


def test_handler_processes_a_synthetic_queue_message(
    worker_root: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with _imported(worker_root):
        from app.functions.queue import process_queue_message

        message = func.QueueMessage(body=b'{"order_id": 17}')
        with caplog.at_level(logging.INFO):
            process_queue_message(message)

    assert [record.getMessage() for record in caplog.records] == [
        'Processed queue message: {"order_id": 17}'
    ]


def test_service_decodes_the_message_body_as_utf8(worker_root: Path) -> None:
    with _imported(worker_root):
        from app.services.queue_service import decode_queue_message

        assert decode_queue_message(func.QueueMessage(body="café".encode())) == "café"


def test_function_app_indexes_the_queue_trigger(worker_root: Path) -> None:
    with _imported(worker_root):
        import function_app

        functions = function_app.app.get_functions()
        assert [function.get_function_name() for function in functions] == ["process_queue_message"]
        trigger = functions[0].get_trigger()
        assert trigger is not None
        binding = trigger.get_dict_repr()

    assert binding["type"] == "queueTrigger"
    assert binding["name"] == "message"
    assert binding["queueName"] == "work-items"
    assert binding["connection"] == "AzureWebJobsStorage"


def test_templates_guide_documents_the_offline_command() -> None:
    guide = (Path(__file__).resolve().parent.parent / "docs" / "guide" / "templates.md").read_text(
        encoding="utf-8"
    )
    section = guide.split("### Queue Template")[1].split("\n### ")[0]
    section = " ".join(section.split())

    assert "pytest tests/test_worker_smoke_queue.py" in section
    assert "does not require" in section and "Functions host" in section
