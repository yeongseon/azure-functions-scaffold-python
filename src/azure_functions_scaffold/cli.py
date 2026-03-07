from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from azure_functions_scaffold import __version__
from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import list_templates

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
    project_name: str = typer.Argument(..., help="Directory name for the new project."),
    destination: DestinationOption = Path("."),
    template: TemplateOption = "http",
) -> None:
    """Create a new Azure Functions HTTP scaffold."""
    try:
        project_path = scaffold_project(
            project_name=project_name,
            destination=destination,
            template_name=template,
        )
    except ScaffoldError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Created project at {project_path}")


@app.command("templates")
def show_templates() -> None:
    """List available scaffold templates."""
    for template in list_templates():
        typer.echo(f"{template.name}: {template.description}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
