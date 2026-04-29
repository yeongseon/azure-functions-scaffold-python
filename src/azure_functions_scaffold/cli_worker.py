"""``afs worker`` subcommand group — background worker scaffolding intents."""

from __future__ import annotations

from pathlib import Path

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


@worker_app.command("timer")
def worker_timer(
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
    """Create a timer-trigger worker project."""
    run_intent(
        "worker/timer",
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


@worker_app.command("queue")
def worker_queue(
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
    """Create a queue-trigger worker project."""
    run_intent(
        "worker/queue",
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


@worker_app.command("blob")
def worker_blob(
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
    """Create a blob-trigger worker project."""
    run_intent(
        "worker/blob",
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


@worker_app.command("servicebus")
def worker_servicebus(
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
    """Create a Service Bus-trigger worker project."""
    run_intent(
        "worker/servicebus",
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


@worker_app.command("eventhub")
def worker_eventhub(
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
    """Create an EventHub-trigger worker project."""
    run_intent(
        "worker/eventhub",
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
