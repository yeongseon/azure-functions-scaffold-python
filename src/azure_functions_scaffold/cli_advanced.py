"""``afs advanced`` subcommand group — full power-user CLI with direct option control."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from azure_functions_scaffold.cli_common import (
    AzdOption,
    DestinationOption,
    DryRunOption,
    OverwriteOption,
    run_scaffold,
)
from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator import (
    SUPPORTED_TRIGGERS,
    add_function,
    add_resource,
    add_route,
    describe_add_function,
    describe_add_resource,
    describe_add_route,
)
from azure_functions_scaffold.template_registry import (
    build_project_options,
    list_presets,
    list_templates,
)

advanced_app = typer.Typer(
    add_completion=False,
    help="Power-user project scaffolding with full option control.",
)

TemplateOption = Annotated[
    str,
    typer.Option(
        "--template",
        "-t",
        help="Template to render.",
    ),
]

PresetOption = Annotated[
    str,
    typer.Option(
        "--preset",
        help="Project preset to apply.",
    ),
]


@advanced_app.command("new")
def advanced_new(
    project_name: str = typer.Argument(..., help="Directory name for the new project."),
    destination: DestinationOption = Path("."),
    template: TemplateOption = "http",
    preset: PresetOption = "standard",
    python_version: Annotated[
        str,
        typer.Option(
            "--python-version",
            help="Python version for the generated project.",
        ),
    ] = "3.10",
    include_github_actions: Annotated[
        bool,
        typer.Option(
            "--github-actions/--no-github-actions",
            help="Include a basic GitHub Actions CI workflow.",
        ),
    ] = False,
    initialize_git: Annotated[
        bool,
        typer.Option(
            "--git/--no-git",
            help="Initialize a git repository in the generated project.",
        ),
    ] = False,
    with_openapi: Annotated[
        bool,
        typer.Option(
            "--with-openapi/--no-openapi",
            help="Include OpenAPI documentation support (HTTP template only).",
        ),
    ] = False,
    with_validation: Annotated[
        bool,
        typer.Option(
            "--with-validation/--no-validation",
            help="Include request validation support (HTTP template only).",
        ),
    ] = False,
    with_doctor: Annotated[
        bool,
        typer.Option(
            "--with-doctor/--no-doctor",
            help="Include azure-functions-doctor health checks.",
        ),
    ] = False,
    with_azd: AzdOption = False,
    dry_run: DryRunOption = False,
    overwrite: OverwriteOption = False,
) -> None:
    """Create a new project with full option control (power-user mode)."""
    try:
        options = build_project_options(
            preset_name=preset,
            python_version=python_version,
            include_github_actions=include_github_actions,
            initialize_git=initialize_git,
            include_openapi=with_openapi,
            include_validation=with_validation,
            include_doctor=with_doctor,
            include_azd=with_azd,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    run_scaffold(
        project_name=project_name,
        template_name=template,
        options=options,
        destination=destination,
        dry_run=dry_run,
        overwrite=overwrite,
    )


@advanced_app.command("add")
def advanced_add(
    trigger: Annotated[
        str,
        typer.Argument(
            ...,
            help=f"Trigger type to add. Supported: {', '.join(SUPPORTED_TRIGGERS)}",
        ),
    ],
    function_name: Annotated[
        str,
        typer.Argument(..., help="Function name to add."),
    ],
    project_root: Annotated[
        Path,
        typer.Option(
            ".",
            "--project-root",
            help="Existing scaffolded project directory.",
        ),
    ] = Path("."),
    dry_run: DryRunOption = False,
) -> None:
    """Add a function module to an existing project (any trigger type)."""
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


@advanced_app.command("templates")
def advanced_templates() -> None:
    """List available scaffold templates."""
    for template in list_templates():
        typer.echo(f"{template.name}: {template.description}")


@advanced_app.command("presets")
def advanced_presets() -> None:
    """List available project presets."""
    for preset in list_presets():
        tooling = ", ".join(preset.tooling) or "none"
        typer.echo(f"{preset.name}: {preset.description} [tooling: {tooling}]")


@advanced_app.command("add-route")
def advanced_add_route(
    route_name: Annotated[
        str,
        typer.Argument(..., help="Route name to add."),
    ],
    project_root: Annotated[
        Path,
        typer.Option(
            ".",
            "--project-root",
            help="Existing scaffolded project directory.",
        ),
    ] = Path("."),
    dry_run: DryRunOption = False,
) -> None:
    """Add a simple HTTP route to an existing project."""
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


@advanced_app.command("add-resource")
def advanced_add_resource(
    resource_name: Annotated[
        str,
        typer.Argument(..., help="Resource name to add (e.g. products)."),
    ],
    project_root: Annotated[
        Path,
        typer.Option(
            ".",
            "--project-root",
            help="Existing scaffolded project directory.",
        ),
    ] = Path("."),
    dry_run: DryRunOption = False,
) -> None:
    """Add a full CRUD resource (blueprint, service, schema, test) to an existing project."""
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
