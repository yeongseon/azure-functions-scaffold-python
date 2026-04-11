"""Shared option types and intent-based scaffold execution for CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import ProjectOptions
from azure_functions_scaffold.scaffolder import describe_scaffold_project, scaffold_project
from azure_functions_scaffold.template_registry import INTENT_SPECS, build_project_options

# ---------------------------------------------------------------------------
# Reusable Typer option types
# ---------------------------------------------------------------------------

DestinationOption = Annotated[
    Path,
    typer.Option(
        ".",
        "--destination",
        "-d",
        help="Base directory where the project folder will be created.",
    ),
]

PythonVersionOption = Annotated[
    str,
    typer.Option(
        "--python-version",
        help="Python version for the generated project.",
    ),
]

GithubActionsOption = Annotated[
    bool,
    typer.Option(
        "--github-actions/--no-github-actions",
        help="Include a basic GitHub Actions CI workflow.",
    ),
]

GitOption = Annotated[
    bool,
    typer.Option(
        "--git/--no-git",
        help="Initialize a git repository in the generated project.",
    ),
]

AzdOption = Annotated[
    bool,
    typer.Option(
        "--azd/--no-azd",
        help="Include Azure Developer CLI (azd) support files.",
    ),
]

DryRunOption = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Preview the generated project without writing files.",
    ),
]

OverwriteOption = Annotated[
    bool,
    typer.Option(
        "--overwrite",
        help="Replace an existing target directory before generating the project.",
    ),
]


# ---------------------------------------------------------------------------
# Intent-based scaffold execution
# ---------------------------------------------------------------------------


def run_intent(
    intent_key: str,
    project_name: str,
    *,
    destination: Path = Path("."),
    python_version: str = "3.10",
    include_github_actions: bool = False,
    initialize_git: bool = False,
    include_azd: bool = False,
    dry_run: bool = False,
    overwrite: bool = False,
) -> None:
    """Look up *intent_key* in ``INTENT_SPECS`` and scaffold accordingly."""
    try:
        spec = INTENT_SPECS.get(intent_key)
        if spec is None:
            raise ScaffoldError(f"Unknown intent '{intent_key}'.")

        options = build_project_options(
            preset_name=spec.preset,
            python_version=python_version,
            include_github_actions=include_github_actions,
            initialize_git=initialize_git,
            include_openapi="openapi" in spec.features,
            include_validation="validation" in spec.features,
            include_doctor="doctor" in spec.features,
            include_azd=include_azd,
            include_db="db" in spec.features,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    run_scaffold(
        project_name=project_name,
        template_name=spec.template,
        options=options,
        destination=destination,
        dry_run=dry_run,
        overwrite=overwrite,
    )


def run_scaffold(
    *,
    project_name: str,
    template_name: str,
    options: ProjectOptions,
    destination: Path = Path("."),
    dry_run: bool = False,
    overwrite: bool = False,
) -> None:
    """Execute scaffold_project (or describe if dry_run) with unified error handling."""

    try:
        if dry_run:
            for line in describe_scaffold_project(
                project_name=project_name,
                destination=destination,
                template_name=template_name,
                options=options,
                overwrite=overwrite,
            ):
                typer.echo(line)
            return
        project_path = scaffold_project(
            project_name=project_name,
            destination=destination,
            template_name=template_name,
            options=options,
            overwrite=overwrite,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Created project at {project_path}")
