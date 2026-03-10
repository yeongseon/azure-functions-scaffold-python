from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from azure_functions_scaffold import __version__
from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator import SUPPORTED_TRIGGERS, add_function
from azure_functions_scaffold.models import ProjectOptions
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import (
    build_project_options,
    get_preset,
    list_presets,
    list_templates,
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
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive",
            "-i",
            help="Prompt for project options interactively.",
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
            interactive=interactive or project_name is None,
        )
        project_path = scaffold_project(
            project_name=resolved_name,
            destination=destination,
            template_name=resolved_template,
            options=resolved_options,
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
) -> None:
    """Add a new function module to an existing scaffolded project."""
    try:
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
    interactive: bool,
) -> tuple[str, str, ProjectOptions]:
    if interactive:
        resolved_name = typer.prompt("Project name", default=project_name or "my-api").strip()
        resolved_template = typer.prompt("Template", default=template).strip().lower()
        resolved_preset = typer.prompt("Preset", default=preset).strip().lower()
        resolved_python_version = typer.prompt(
            "Python version",
            default=python_version,
        ).strip()
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

    options = build_project_options(
        preset_name=resolved_preset,
        python_version=resolved_python_version,
        include_github_actions=resolved_include_github_actions,
        initialize_git=resolved_initialize_git,
        tooling=resolved_tooling,
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
