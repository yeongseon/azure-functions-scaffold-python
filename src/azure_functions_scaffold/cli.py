from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from azure_functions_scaffold import __version__
from azure_functions_scaffold.cli_advanced import advanced_app
from azure_functions_scaffold.cli_ai import ai_app
from azure_functions_scaffold.cli_api import api_app, api_new
from azure_functions_scaffold.cli_common import run_add_function, show_presets, show_templates
from azure_functions_scaffold.cli_worker import worker_app

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
    ctx: typer.Context,
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
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


# Listing and creation reuse the callables behind ``afs advanced templates|presets`` and
# ``afs api new`` so each operation has one implementation and one option surface.
app.command("templates")(show_templates)
app.command("presets")(show_presets)
app.command("new", help="Create a new API project (shortcut for 'afs api new').")(api_new)


@app.command(
    "add",
    deprecated=True,
    help="DEPRECATED: use 'afs api add' (http) or 'afs advanced add <trigger>' instead.",
    hidden=False,
)
def legacy_add(
    ctx: typer.Context,
    trigger: str = typer.Argument(..., help="Trigger type (e.g. http, timer, queue)."),
    function_name: str = typer.Argument(..., help="Function name."),
    project_root: Path = typer.Option(Path("."), "--project-root", "-p", help="Project root."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """DEPRECATED shim. Forwards to the modern command."""
    del ctx
    normalized = trigger.strip().lower()
    if normalized == "http":
        replacement = f"afs api add {function_name} --project-root {project_root}"
    else:
        replacement = f"afs advanced add {normalized} {function_name} --project-root {project_root}"
    typer.echo(
        f"warning: 'afs add' is deprecated and will be removed in a future release. "
        f"Use: {replacement}",
        err=True,
    )
    run_add_function(
        project_root=project_root,
        trigger=normalized,
        function_name=function_name,
        dry_run=dry_run,
        legacy=True,
    )


@app.command(
    "profiles",
    deprecated=True,
    help="DEPRECATED: use 'afs presets' instead.",
    hidden=False,
)
def legacy_profiles() -> None:
    """DEPRECATED shim. Forwards to 'afs presets'."""
    typer.echo(
        "warning: 'afs profiles' is deprecated and will be removed in a future release. "
        "Use: afs presets",
        err=True,
    )
    show_presets()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
