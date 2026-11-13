"""Offline smoke test for the generated timer worker (#483).

Generates the documented ``afs worker timer`` project into a temporary directory, imports it the
way the Functions worker does, and calls the generated handler with a locally constructed
``azure.functions.TimerRequest`` stand-in. Nothing depends on wall-clock time or the scheduler. This
verifies the handler contract and how the trigger is declared; it does not certify that the CRON
schedule fires when expected, catch-up/past-due semantics, singleton locking or an Azure deployment.
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


class FakeTimerRequest(func.TimerRequest):
    """Fixed timer payload; the only member the handler reads is ``past_due``."""

    def __init__(self, *, past_due: bool) -> None:
        self._past_due = past_due

    @property
    def past_due(self) -> bool:
        return self._past_due


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
        app, ["worker", "timer", "timer-worker", "--destination", str(tmp_path), "--no-git"]
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "timer-worker"


def test_on_time_tick_logs_only_the_tick_message(
    worker_root: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with _imported(worker_root):
        from app.functions.timer import cleanup

        with caplog.at_level(logging.INFO):
            cleanup(FakeTimerRequest(past_due=False))

    assert [(record.levelname, record.getMessage()) for record in caplog.records] == [
        ("INFO", "Timer trigger executed.")
    ]


def test_past_due_tick_warns_before_running(
    worker_root: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with _imported(worker_root):
        from app.functions.timer import cleanup

        with caplog.at_level(logging.INFO):
            cleanup(FakeTimerRequest(past_due=True))

    assert [(record.levelname, record.getMessage()) for record in caplog.records] == [
        ("WARNING", "Timer trigger 'cleanup' is running late."),
        ("INFO", "Timer trigger executed."),
    ]


def test_function_app_indexes_the_timer_trigger(worker_root: Path) -> None:
    with _imported(worker_root):
        import function_app

        functions = function_app.app.get_functions()
        assert [function.get_function_name() for function in functions] == ["cleanup"]
        trigger = functions[0].get_trigger()
        assert trigger is not None
        binding = trigger.get_dict_repr()

    assert binding["type"] == "timerTrigger"
    assert binding["name"] == "timer"
    assert binding["schedule"] == "0 */5 * * * *"
    assert binding["runOnStartup"] is False
    assert binding["useMonitor"] is True


def test_templates_guide_documents_the_offline_command_and_its_limits() -> None:
    guide = (Path(__file__).resolve().parent.parent / "docs" / "guide" / "templates.md").read_text(
        encoding="utf-8"
    )
    section = guide.split("### Timer Template")[1].split("\n### ")[0]
    section = " ".join(section.split())

    assert "pytest tests/test_worker_smoke_timer.py" in section
    assert "does not certify" in section and "cron" in section.lower()
