from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from azure_functions_scaffold.cli import app
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

runner = CliRunner()


def test_cli_emits_no_preview_warning_for_314(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "ga-api",
            "--destination",
            str(tmp_path),
            "--python-version",
            "3.14",
        ],
    )

    assert result.exit_code == 0
    output = (result.stderr or "") + result.stdout
    assert "Preview on Azure Functions" not in output
    assert "supported-languages" not in (result.stderr or "")


def test_generated_readme_omits_preview_note_for_314(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "ga-readme",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version="3.14",
            include_github_actions=False,
            initialize_git=False,
        ),
    )

    readme_text = (project_path / "README.md").read_text(encoding="utf-8")

    assert "which is **Preview** on Azure Functions today" not in readme_text
