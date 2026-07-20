"""Shared option types and intent-based scaffold execution for CLI commands."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator import (
    add_function,
    add_resource,
    add_route,
    describe_add_function,
    describe_add_resource,
    describe_add_route,
)
from azure_functions_scaffold.models import ProjectOptions
from azure_functions_scaffold.scaffolder import describe_scaffold_project, scaffold_project
from azure_functions_scaffold.template_registry import (
    INTENT_SPECS,
    PREVIEW_PYTHON_VERSIONS,
    build_project_options,
    is_preview_python,
)

logger = logging.getLogger(__name__)

PREVIEW_PYTHON_VERSIONS_LABEL = "/".join(sorted(PREVIEW_PYTHON_VERSIONS))
PYTHON_VERSION_HELP = (
    f"Python version target. {PREVIEW_PYTHON_VERSIONS_LABEL} is PREVIEW on Azure Functions "
    "(limited regional/plan support)."
)
PREVIEW_PYTHON_WARNING = (
    "GA support is limited; Flex Consumption remote build may be unavailable in your region. "
    "See https://learn.microsoft.com/azure/azure-functions/supported-languages for the "
    "current support matrix."
)

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
        help=PYTHON_VERSION_HELP,
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

YesOption = Annotated[
    bool,
    typer.Option(
        "--yes",
        "-y",
        help=(
            "Skip confirmation prompts (required when --overwrite runs in a "
            "non-TTY session or against a directory containing .git)."
        ),
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
    yes: bool = False,
) -> None:
    """Look up *intent_key* in ``INTENT_SPECS`` and scaffold accordingly."""
    try:
        spec = INTENT_SPECS.get(intent_key)
        if spec is None:
            raise ScaffoldError(f"Unknown intent '{intent_key}'.")
        logger.debug(
            "Resolving intent '%s' with preset=%s, features=%s",
            intent_key,
            spec.preset,
            spec.features,
        )

        options = build_project_options(
            preset_name=spec.preset,
            python_version=python_version,
            include_github_actions=include_github_actions,
            initialize_git=initialize_git,
            include_openapi="openapi" in spec.features,
            include_validation="validation" in spec.features,
            include_doctor="doctor" in spec.features,
            include_azd=include_azd,
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
        yes=yes,
    )


def run_scaffold(
    *,
    project_name: str,
    template_name: str,
    options: ProjectOptions,
    destination: Path = Path("."),
    dry_run: bool = False,
    overwrite: bool = False,
    yes: bool = False,
) -> None:
    """Execute scaffold_project (or describe if dry_run) with unified error handling."""
    logger.debug(
        "Running scaffold: project=%s, template=%s, dry_run=%s",
        project_name,
        template_name,
        dry_run,
    )

    _emit_preview_python_warning(options.python_version)

    try:
        if dry_run:
            for line in describe_scaffold_project(
                project_name=project_name,
                destination=destination,
                template_name=template_name,
                options=options,
                overwrite=overwrite,
                yes=yes,
            ):
                typer.echo(line)
            return
        project_path = scaffold_project(
            project_name=project_name,
            destination=destination,
            template_name=template_name,
            options=options,
            overwrite=overwrite,
            yes=yes,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    _print_success_message(project_path, template_name, options)


def _emit_preview_python_warning(version: str) -> None:
    if not is_preview_python(version):
        return

    typer.secho(
        f"Warning: Python {version} is Preview on Azure Functions. {PREVIEW_PYTHON_WARNING}",
        fg=typer.colors.YELLOW,
        err=True,
    )


def _print_success_message(
    project_path: Path,
    template_name: str,
    options: ProjectOptions,
) -> None:
    """Print a rich post-scaffold landing message with next steps."""
    typer.secho("\n  Project created successfully!\n", fg=typer.colors.GREEN, bold=True)

    typer.echo(f"  Location:  {project_path}")
    typer.echo(f"  Template:  {template_name}")
    typer.echo(f"  Preset:    {options.preset_name}")
    typer.echo(f"  Python:    {options.python_version}")

    # Feature badges
    features: list[str] = []
    if options.include_openapi:
        features.append("openapi")
    if options.include_validation:
        features.append("validation")
    if options.include_doctor:
        features.append("doctor")
    if options.include_azd:
        features.append("azd")
    if options.include_github_actions:
        features.append("github-actions")
    if features:
        typer.echo(f"  Features:  {', '.join(features)}")

    # Next steps
    typer.echo("")
    typer.secho("  Next steps:", bold=True)
    typer.echo(f"    cd {project_path}")
    typer.echo("    python -m venv .venv")
    typer.echo("    source .venv/bin/activate   # Linux/macOS")
    typer.echo("    .venv\\Scripts\\activate      # Windows")
    dev_extra = "[dev]" if options.tooling else ""
    typer.echo(f"    pip install -e .{dev_extra}")
    typer.echo("    func start")
    if options.include_openapi:
        typer.echo("")
        typer.secho("  API docs:", bold=True)
        typer.echo("    http://localhost:7071/api/docs")
    typer.echo("")


# ---------------------------------------------------------------------------
# Shared add-* intent execution (used by both `api` and `advanced` groups)
# ---------------------------------------------------------------------------


def run_add_function(
    *,
    project_root: Path,
    trigger: str,
    function_name: str,
    dry_run: bool = False,
) -> None:
    """Add a function module (or preview via *dry_run*) with unified error handling."""
    try:
        if dry_run:
            for line in describe_add_function(
                project_root=project_root,
                trigger=trigger,
                function_name=function_name,
            ):
                typer.echo(line)
            return
        function_path = add_function(
            project_root=project_root,
            trigger=trigger,
            function_name=function_name,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Created function at {function_path}")


def run_add_route(
    *,
    project_root: Path,
    route_name: str,
    dry_run: bool = False,
) -> None:
    """Add an HTTP route (or preview via *dry_run*) with unified error handling."""
    try:
        if dry_run:
            for line in describe_add_route(
                project_root=project_root,
                route_name=route_name,
            ):
                typer.echo(line)
            return
        route_path = add_route(
            project_root=project_root,
            route_name=route_name,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Created route at {route_path}")


def run_add_resource(
    *,
    project_root: Path,
    resource_name: str,
    dry_run: bool = False,
) -> None:
    """Add a CRUD resource (or preview via *dry_run*) with unified error handling."""
    try:
        if dry_run:
            for line in describe_add_resource(
                project_root=project_root,
                resource_name=resource_name,
            ):
                typer.echo(line)
            return
        created = add_resource(
            project_root=project_root,
            resource_name=resource_name,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    for path in created:
        typer.echo(f"Created {path}")
