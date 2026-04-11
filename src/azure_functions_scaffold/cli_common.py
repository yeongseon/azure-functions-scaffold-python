"""Shared option builders and intent-to-ProjectOptions mapping for intent-centric CLI commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
import warnings

import typer

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import ProjectOptions
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

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
# Intent → ProjectOptions mapping
# ---------------------------------------------------------------------------


def build_api_options(
    *,
    python_version: str = "3.10",
    include_github_actions: bool = False,
    initialize_git: bool = False,
    include_azd: bool = False,
) -> ProjectOptions:
    """Map ``afs api new`` intent to ProjectOptions (profile: api)."""
    return build_project_options(
        preset_name="strict",
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_openapi=True,
        include_validation=True,
        include_doctor=True,
        include_azd=include_azd,
        include_db=False,
    )


def build_api_crud_options(
    *,
    python_version: str = "3.10",
    include_github_actions: bool = False,
    initialize_git: bool = False,
    include_azd: bool = False,
) -> ProjectOptions:
    """Map ``afs api crud`` intent to ProjectOptions (profile: db-api)."""
    return build_project_options(
        preset_name="strict",
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
        include_openapi=True,
        include_validation=True,
        include_doctor=True,
        include_azd=include_azd,
        include_db=True,
    )


def build_worker_options(
    *,
    python_version: str = "3.10",
    include_github_actions: bool = False,
    initialize_git: bool = False,
    include_azd: bool = False,
) -> ProjectOptions:
    """Map ``afs worker <trigger>`` intent to ProjectOptions (standard preset, no features)."""
    return build_project_options(
        preset_name="standard",
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
    )


def build_ai_options(
    *,
    python_version: str = "3.10",
    include_github_actions: bool = False,
    initialize_git: bool = False,
    include_azd: bool = False,
) -> ProjectOptions:
    """Map ``afs ai agent`` intent to ProjectOptions (standard preset, no features)."""
    return build_project_options(
        preset_name="standard",
        python_version=python_version,
        include_github_actions=include_github_actions,
        initialize_git=initialize_git,
    )


# ---------------------------------------------------------------------------
# Shared scaffold execution
# ---------------------------------------------------------------------------


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
    from azure_functions_scaffold.scaffolder import describe_scaffold_project

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


# ---------------------------------------------------------------------------
# Deprecation warning helper
# ---------------------------------------------------------------------------

_DEPRECATION_MESSAGE = (
    "'{old_command}' is deprecated and will be removed in a future release. "
    "Use '{new_command}' instead."
)


def emit_deprecation_warning(*, old_command: str, new_command: str) -> None:
    """Emit a deprecation warning for legacy CLI commands."""
    msg = _DEPRECATION_MESSAGE.format(old_command=old_command, new_command=new_command)
    warnings.warn(msg, FutureWarning, stacklevel=3)
    typer.secho(f"Warning: {msg}", fg=typer.colors.YELLOW, err=True)
