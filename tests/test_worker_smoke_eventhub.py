"""Offline smoke test for the generated Event Hub worker (#479).

Generates the documented ``afs worker eventhub`` project into a temporary directory, imports it
the way the Functions worker does, and calls the generated handler with a synthetic
``azure.functions.EventHubEvent``. No Azure resources, credentials, network or Functions host are
needed: this verifies handler/service logic and how the trigger is declared, not host binding
behavior (listener, checkpointing, partitions), which needs a real host and Event Hubs.
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
        app, ["worker", "eventhub", "hub-worker", "--destination", str(tmp_path), "--no-git"]
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "hub-worker"


def test_handler_processes_a_synthetic_event_hub_message(
    worker_root: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with _imported(worker_root):
        from app.functions.eventhub import process_event

        event = func.EventHubEvent(body=b'{"device": "sensor-1", "reading": 42}')
        with caplog.at_level(logging.INFO):
            process_event(event)

    assert [record.getMessage() for record in caplog.records] == [
        'Processed Event Hub message: {"device": "sensor-1", "reading": 42}'
    ]


def test_service_decodes_the_event_body_as_utf8(worker_root: Path) -> None:
    with _imported(worker_root):
        from app.services.eventhub_service import decode_event

        assert decode_event(func.EventHubEvent(body="température".encode())) == "température"


def test_function_app_indexes_the_event_hub_trigger(worker_root: Path) -> None:
    with _imported(worker_root):
        import function_app

        functions = function_app.app.get_functions()
        assert [function.get_function_name() for function in functions] == ["process_event"]
        trigger = functions[0].get_trigger()
        assert trigger is not None
        binding = trigger.get_dict_repr()

    assert binding["type"] == "eventHubTrigger"
    assert binding["name"] == "event"
    assert binding["eventHubName"] == "my-event-hub"
    assert binding["connection"] == "EventHubConnection"


def test_templates_guide_documents_the_offline_command() -> None:
    guide = (Path(__file__).resolve().parent.parent / "docs" / "guide" / "templates.md").read_text(
        encoding="utf-8"
    )
    section = guide.split("### Event Hub Template")[1].split("\n### ")[0]
    section = " ".join(section.split())

    assert "pytest tests/test_worker_smoke_eventhub.py" in section
    assert "does not require" in section and "Functions host" in section
