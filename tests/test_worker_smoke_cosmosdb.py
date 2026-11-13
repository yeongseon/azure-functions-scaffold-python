"""Offline smoke test for the generated Cosmos DB change-feed template (#484).

Generates the documented ``afs advanced new --template cosmosdb`` project into a temporary
directory, imports it the way the Functions worker does, and calls the generated handler with
synthetic change-feed documents (``azure.functions.DocumentList``). No Cosmos account, emulator,
credentials, network or Functions host is needed. This verifies handler/service logic and how the
trigger is declared; it does not validate leases, checkpointing, permissions, partitioning or
production change-feed behavior.
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


def _documents(*ids: str) -> func.DocumentList:
    return func.DocumentList([func.Document.from_dict({"id": item, "data": "x"}) for item in ids])


@pytest.fixture
def template_root(tmp_path: Path) -> Path:
    result = runner.invoke(
        app,
        [
            "advanced",
            "new",
            "--template",
            "cosmosdb",
            "--preset",
            "standard",
            "cosmos-worker",
            "--destination",
            str(tmp_path),
            "--no-git",
        ],
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "cosmos-worker"


def test_handler_reports_the_number_of_synthetic_changes(
    template_root: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with _imported(template_root):
        from app.functions.cosmosdb import process_cosmos_changes

        caplog.clear()  # drop records emitted while importing the project
        with caplog.at_level(logging.INFO):
            process_cosmos_changes(_documents("a", "b", "c"))

    assert [record.getMessage() for record in caplog.records] == [
        "Processed 3 Cosmos DB change(s)."
    ]


def test_service_counts_documents_including_an_empty_batch(template_root: Path) -> None:
    with _imported(template_root):
        from app.services.cosmosdb_service import describe_documents

        assert describe_documents(_documents("only")) == 1
        assert describe_documents(func.DocumentList([])) == 0


def test_function_app_indexes_the_cosmos_trigger(template_root: Path) -> None:
    with _imported(template_root):
        import function_app

        functions = function_app.app.get_functions()
        assert [function.get_function_name() for function in functions] == [
            "process_cosmos_changes"
        ]
        trigger = functions[0].get_trigger()
        assert trigger is not None
        binding = trigger.get_dict_repr()

    assert binding["type"] == "cosmosDBTrigger"
    assert binding["name"] == "documents"
    assert binding["databaseName"] == "my-database"
    assert binding["containerName"] == "my-container"
    assert binding["connection"] == "CosmosDBConnection"


def test_templates_guide_documents_the_offline_command_and_its_limits() -> None:
    guide = (Path(__file__).resolve().parent.parent / "docs" / "guide" / "templates.md").read_text(
        encoding="utf-8"
    )
    section = guide.split("### CosmosDB Template")[1].split("\n### ")[0]
    section = " ".join(section.split())

    assert "pytest tests/test_worker_smoke_cosmosdb.py" in section
    assert "does not validate" in section and "leases" in section
