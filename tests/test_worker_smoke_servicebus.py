"""Offline smoke test for the generated Service Bus worker (#482).

Generates the documented ``afs worker servicebus`` project into a temporary directory, imports it
the way the Functions worker does, and calls the generated handler with a synthetic
``azure.functions.ServiceBusMessage``. No broker, namespace, credentials, network or Functions
host is needed. This verifies handler/service logic, the handler signature and how the trigger is
declared; locks, completion/abandon, dead-lettering, sessions and delivery counts need a real host
and Service Bus. It is independent of the Storage queue (#480) and Event Hub (#479) smoke tests.
"""

from __future__ import annotations

from collections.abc import Iterator
import contextlib
import logging
from pathlib import Path
import sys
import typing

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
        app, ["worker", "servicebus", "bus-worker", "--destination", str(tmp_path), "--no-git"]
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "bus-worker"


def test_handler_processes_a_synthetic_service_bus_message(
    worker_root: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with _imported(worker_root):
        from app.functions.servicebus import process_servicebus_message

        message = func.ServiceBusMessage(body=b'{"invoice": "INV-7"}')
        with caplog.at_level(logging.INFO):
            process_servicebus_message(message)

    assert [record.getMessage() for record in caplog.records] == [
        'Processed Service Bus message: {"invoice": "INV-7"}'
    ]


def test_service_decodes_the_message_body_as_utf8(worker_root: Path) -> None:
    with _imported(worker_root):
        from app.services.servicebus_service import decode_servicebus_message

        message = func.ServiceBusMessage(body="größe".encode())
        assert decode_servicebus_message(message) == "größe"


def test_handler_signature_and_trigger_declaration(worker_root: Path) -> None:
    with _imported(worker_root):
        import function_app

        functions = function_app.app.get_functions()
        assert [function.get_function_name() for function in functions] == [
            "process_servicebus_message"
        ]
        hints = typing.get_type_hints(functions[0].get_user_function())
        trigger = functions[0].get_trigger()
        assert trigger is not None
        binding = trigger.get_dict_repr()

    assert hints == {"message": func.ServiceBusMessage, "return": type(None)}
    assert binding["type"] == "serviceBusTrigger"
    assert binding["name"] == "message"
    assert binding["queueName"] == "work-items"
    assert binding["connection"] == "ServiceBusConnection"


def test_templates_guide_documents_the_offline_command() -> None:
    guide = (Path(__file__).resolve().parent.parent / "docs" / "guide" / "templates.md").read_text(
        encoding="utf-8"
    )
    section = guide.split("### Service Bus Template")[1].split("\n### ")[0]
    section = " ".join(section.split())

    assert "pytest tests/test_worker_smoke_servicebus.py" in section
    assert "does not require" in section and "Functions host" in section
