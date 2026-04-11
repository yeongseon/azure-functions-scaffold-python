"""``afs ai`` subcommand group — AI/agent scaffolding intents."""

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
    build_ai_options,
    run_scaffold,
)

ai_app = typer.Typer(
    add_completion=False,
    help="AI agent project scaffolding.",
)


@ai_app.command("agent")
def ai_agent(
    project_name: str = typer.Argument(..., help="Directory name for the new project."),
    destination: DestinationOption = Path("."),
    python_version: PythonVersionOption = "3.10",
    include_github_actions: GithubActionsOption = False,
    initialize_git: GitOption = False,
    include_azd: AzdOption = False,
    dry_run: DryRunOption = False,
    overwrite: OverwriteOption = False,
) -> None:
    """Create a LangGraph agent project."""
    options = build_ai_options(
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
    )
    run_scaffold(
        project_name=project_name,
        template_name="langgraph",
        options=options,
        destination=destination,
        dry_run=dry_run,
        overwrite=overwrite,
    )
