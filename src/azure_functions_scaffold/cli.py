from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from azure_functions_scaffold import __version__
from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator import (
    SUPPORTED_TRIGGERS,
    add_function,
    describe_add_function,
)
from azure_functions_scaffold.models import ProjectOptions
from azure_functions_scaffold.scaffolder import (
    describe_scaffold_project,
    scaffold_project,
    validate_project_name,
)
from azure_functions_scaffold.template_registry import (
    build_project_options,
    get_preset,
    list_presets,
    list_templates,
    validate_python_version,
)

app = typer.Typer(
    add_completion=False,
    help="Generate opinionated Azure Functions Python v2 projects.",
    invoke_without_command=True,
)

DestinationOption = Annotated[
    Path,
    typer.Option(
        ".",
        "--destination",
        "-d",
        help="Base directory where the project folder will be created.",
    ),
]

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


@app.callback()
def callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the installed version and exit.",
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Azure Functions scaffold CLI."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()


@app.command("new")
def new_project(
    project_name: str | None = typer.Argument(
        None,
        help="Directory name for the new project. Omit to enter interactive mode.",
    ),
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
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Prompt for project options interactively.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview the generated project without writing files.",
        ),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Replace an existing target directory before generating the project.",
        ),
    ] = False,
) -> None:
    """Create a new Azure Functions Python v2 scaffold."""
    try:
        resolved_name, resolved_template, resolved_options = _resolve_new_project_inputs(
            project_name=project_name,
            template=template,
            preset=preset,
            python_version=python_version,
            include_github_actions=include_github_actions,
            initialize_git=initialize_git,
            include_openapi=with_openapi,
            include_validation=with_validation,
            interactive=interactive or project_name is None,
        )
        if dry_run:
            for line in describe_scaffold_project(
                project_name=resolved_name,
                destination=destination,
                template_name=resolved_template,
                options=resolved_options,
                overwrite=overwrite,
            ):
                typer.echo(line)
            return
        project_path = scaffold_project(
            project_name=resolved_name,
            destination=destination,
            template_name=resolved_template,
            options=resolved_options,
            overwrite=overwrite,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Created project at {project_path}")


@app.command("add")
def add_project_function(
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
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview the added files without modifying the project.",
        ),
    ] = False,
) -> None:
    """Add a new function module to an existing scaffolded project."""
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


@app.command("templates")
def show_templates() -> None:
    """List available scaffold templates."""
    for template in list_templates():
        typer.echo(f"{template.name}: {template.description}")


@app.command("presets")
def show_presets() -> None:
    """List available project presets."""
    for preset in list_presets():
        tooling = ", ".join(preset.tooling) or "none"
        typer.echo(f"{preset.name}: {preset.description} [tooling: {tooling}]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()


def _resolve_new_project_inputs(
    *,
    project_name: str | None,
    template: str,
    preset: str,
    python_version: str,
    include_github_actions: bool,
    initialize_git: bool,
    include_openapi: bool,
    include_validation: bool,
    interactive: bool,
) -> tuple[str, str, ProjectOptions]:
    if interactive:
        resolved_name = _prompt_project_name(project_name or "my-api")
        resolved_template = _prompt_choice(
            label="Template",
            default=template,
            choices=tuple(template_spec.name for template_spec in list_templates()),
        )
        resolved_preset = _prompt_choice(
            label="Preset",
            default=preset,
            choices=tuple(preset_spec.name for preset_spec in list_presets()),
        )
        resolved_python_version = _prompt_python_version(python_version)
        resolved_include_github_actions = typer.confirm(
            "Include GitHub Actions?",
            default=include_github_actions,
        )
        resolved_initialize_git = typer.confirm(
            "Initialize git repository?",
            default=initialize_git,
        )
        preset_spec = get_preset(resolved_preset)
        resolved_tooling = _prompt_tooling_selection(preset_spec.tooling)
        resolved_include_openapi = typer.confirm(
            "Include OpenAPI documentation? (HTTP template only)",
            default=include_openapi,
        )
        resolved_include_validation = typer.confirm(
            "Include request validation? (HTTP template only)",
            default=include_validation,
        )
    else:
        if project_name is None:
            raise ScaffoldError("Project name is required unless --interactive is used.")
        resolved_name = project_name
        resolved_template = template
        resolved_preset = preset
        resolved_python_version = python_version
        resolved_include_github_actions = include_github_actions
        resolved_initialize_git = initialize_git
        resolved_tooling = None
        resolved_include_openapi = include_openapi
        resolved_include_validation = include_validation

    options = build_project_options(
        preset_name=resolved_preset,
        python_version=resolved_python_version,
        include_github_actions=resolved_include_github_actions,
        initialize_git=resolved_initialize_git,
        tooling=resolved_tooling,
        include_openapi=resolved_include_openapi,
        include_validation=resolved_include_validation,
    )

    return resolved_name, resolved_template, options


def _prompt_tooling_selection(default_tooling: tuple[str, ...]) -> tuple[str, ...]:
    selections: list[str] = []
    prompts = [
        ("ruff", "Include Ruff?"),
        ("mypy", "Include mypy?"),
        ("pytest", "Include pytest?"),
    ]

    typer.echo("Select tooling for the generated project:")
    for tool_name, prompt in prompts:
        if typer.confirm(prompt, default=tool_name in default_tooling):
            selections.append(tool_name)

    return tuple(selections)


def _prompt_project_name(default: str) -> str:
    while True:
        candidate = str(typer.prompt("Project name", default=default)).strip()
        try:
            return validate_project_name(candidate)
        except ScaffoldError as exc:
            typer.secho(str(exc), fg=typer.colors.YELLOW)


def _prompt_choice(*, label: str, default: str, choices: tuple[str, ...]) -> str:
    available = ", ".join(choices)
    while True:
        candidate = str(typer.prompt(label, default=default)).strip().lower()
        if candidate in choices:
            return candidate
        typer.secho(
            f"Unsupported {label.lower()} '{candidate}'. Choose one of: {available}",
            fg=typer.colors.YELLOW,
        )


def _prompt_python_version(default: str) -> str:
    while True:
        candidate = str(typer.prompt("Python version", default=default)).strip()
        try:
            return validate_python_version(candidate)
        except ScaffoldError as exc:
            typer.secho(str(exc), fg=typer.colors.YELLOW)
