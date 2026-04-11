from __future__ import annotations

from typing import Annotated

import typer

from azure_functions_scaffold import __version__
from azure_functions_scaffold.cli_advanced import advanced_app
from azure_functions_scaffold.cli_ai import ai_app
from azure_functions_scaffold.cli_api import api_app
from azure_functions_scaffold.cli_worker import worker_app
from azure_functions_scaffold.template_registry import list_presets, list_templates

app = typer.Typer(
    add_completion=False,
    help="Generate opinionated Azure Functions Python v2 projects.",
    invoke_without_command=True,
)

# ---------------------------------------------------------------------------
# Register intent-centric subcommand groups
# ---------------------------------------------------------------------------
app.add_typer(api_app, name="api")
app.add_typer(worker_app, name="worker")
app.add_typer(ai_app, name="ai")
app.add_typer(advanced_app, name="advanced")


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
