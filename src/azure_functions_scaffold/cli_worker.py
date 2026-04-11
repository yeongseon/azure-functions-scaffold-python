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
    build_worker_options,
    run_scaffold,
)

worker_app = typer.Typer(
    add_completion=False,
    help="Background worker project scaffolding.",
)


def _worker_new(
    *,
    template_name: str,
    project_name: str,
    destination: Path,
    python_version: str,
    include_github_actions: bool,
    initialize_git: bool,
    include_azd: bool,
    dry_run: bool,
    overwrite: bool,
) -> None:
    """Shared implementation for all worker subcommands."""
    options = build_worker_options(
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
    )
    run_scaffold(
        project_name=project_name,
        template_name=template_name,
        options=options,
        destination=destination,
        dry_run=dry_run,
        overwrite=overwrite,
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
) -> None:
    """Create a timer-trigger worker project."""
    _worker_new(
        template_name="timer",
        project_name=project_name,
        destination=destination,
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
        dry_run=dry_run,
        overwrite=overwrite,
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
) -> None:
    """Create a queue-trigger worker project."""
    _worker_new(
        template_name="queue",
        project_name=project_name,
        destination=destination,
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
        dry_run=dry_run,
        overwrite=overwrite,
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
) -> None:
    """Create a blob-trigger worker project."""
    _worker_new(
        template_name="blob",
        project_name=project_name,
        destination=destination,
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
        dry_run=dry_run,
        overwrite=overwrite,
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
) -> None:
    """Create a Service Bus-trigger worker project."""
    _worker_new(
        template_name="servicebus",
        project_name=project_name,
        destination=destination,
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
        dry_run=dry_run,
        overwrite=overwrite,
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
) -> None:
    """Create an EventHub-trigger worker project."""
    _worker_new(
        template_name="eventhub",
        project_name=project_name,
        destination=destination,
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
        dry_run=dry_run,
        overwrite=overwrite,
    )
