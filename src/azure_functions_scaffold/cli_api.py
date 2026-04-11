"""``afs api`` subcommand group — REST API scaffolding intents."""

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
    run_intent,
)
from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator import add_function, describe_add_function

api_app = typer.Typer(
    add_completion=False,
    help="REST API project scaffolding.",
)


@api_app.command("new")
def api_new(
    project_name: str = typer.Argument(..., help="Directory name for the new project."),
    destination: DestinationOption = Path("."),
    python_version: PythonVersionOption = "3.10",
    include_github_actions: GithubActionsOption = False,
    initialize_git: GitOption = False,
    include_azd: AzdOption = False,
    dry_run: DryRunOption = False,
    overwrite: OverwriteOption = False,
) -> None:
    """Create a REST API project with OpenAPI, validation, and doctor."""
    run_intent(
        "api/new",
        project_name,
        destination=destination,
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_azd=include_azd,
        dry_run=dry_run,
        overwrite=overwrite,
    )


@api_app.command("add")
def api_add(
    function_name: str = typer.Argument(..., help="Function name to add."),
    project_root: Path = typer.Option(
        ".",
        "--project-root",
        help="Existing scaffolded project directory.",
    ),
    dry_run: DryRunOption = False,
) -> None:
    """Add an HTTP function to an existing API project."""
    try:
        if dry_run:
            for line in describe_add_function(
                project_root=project_root,
                trigger="http",
                function_name=function_name,
            ):
                typer.echo(line)
            return
        function_path = add_function(
            project_root=project_root,
            trigger="http",
            function_name=function_name,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Created function at {function_path}")
