"""``afs worker`` subcommand group — background worker scaffolding intents."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer

from azure_functions_scaffold.cli_common import (
    AzdOption,
    DestinationOption,
    DryRunOption,
    GithubActionsOption,
    GitOption,
    OverwriteOption,
    PythonVersionOption,
    YesOption,
    run_intent,
)

worker_app = typer.Typer(
    add_completion=False,
    help="Background worker project scaffolding.",
)


# (command name, intent id, help text). The worker commands are otherwise
# identical — same option surface, same ``run_intent`` dispatch — so they are
# generated from this single spec table instead of hand-duplicated.
_WORKER_INTENTS: tuple[tuple[str, str, str], ...] = (
    ("timer", "worker/timer", "Create a timer-trigger worker project."),
    ("queue", "worker/queue", "Create a queue-trigger worker project."),
    ("blob", "worker/blob", "Create a blob-trigger worker project."),
    ("servicebus", "worker/servicebus", "Create a Service Bus-trigger worker project."),
    ("eventhub", "worker/eventhub", "Create an EventHub-trigger worker project."),
)


def _make_worker_command(intent: str) -> Callable[..., None]:
    """Build a Typer command callable that dispatches ``intent`` via ``run_intent``."""

    def command(
        project_name: str = typer.Argument(..., help="Directory name for the new project."),
        destination: DestinationOption = Path("."),
        python_version: PythonVersionOption = "3.10",
        include_github_actions: GithubActionsOption = False,
        initialize_git: GitOption = False,
        include_azd: AzdOption = False,
        dry_run: DryRunOption = False,
        overwrite: OverwriteOption = False,
        yes: YesOption = False,
    ) -> None:
        run_intent(
            intent,
            project_name,
            destination=destination,
            python_version=python_version,
            include_github_actions=include_github_actions,
            initialize_git=initialize_git,
            include_azd=include_azd,
            dry_run=dry_run,
            overwrite=overwrite,
            yes=yes,
        )

    return command


for _name, _intent, _help in _WORKER_INTENTS:
    worker_app.command(_name, help=_help)(_make_worker_command(_intent))
