from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from azure_functions_scaffold.cli import app
from azure_functions_scaffold.cli_common import PREVIEW_PYTHON_WARNING
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options, is_preview_python

runner = CliRunner()


def test_is_preview_python_returns_true_for_314() -> None:
    assert is_preview_python("3.14") is True


def test_is_preview_python_returns_false_for_312() -> None:
    assert is_preview_python("3.12") is False


def test_cli_emits_preview_warning_for_314(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "preview-api",
            "--destination",
            str(tmp_path),
            "--python-version",
            "3.14",
        ],
    )

    assert result.exit_code == 0
    assert (f"Warning: Python 3.14 is Preview on Azure Functions. {PREVIEW_PYTHON_WARNING}") in (
        (result.stderr or "") + result.stdout
    )


def test_cli_no_warning_for_312(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "ga-api",
            "--destination",
            str(tmp_path),
            "--python-version",
            "3.12",
        ],
    )

    assert result.exit_code == 0
    output = (result.stderr or "") + result.stdout
    assert "Warning: Python 3.12 is Preview on Azure Functions." not in output
    assert "supported-languages" not in (result.stderr or "")


def test_generated_readme_includes_preview_note_for_314(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "preview-readme",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version="3.14",
            include_github_actions=False,
            initialize_git=False,
        ),
    )

    readme_text = (project_path / "README.md").read_text(encoding="utf-8")

    assert "which is **Preview** on Azure Functions today" in readme_text
    assert "Flex Consumption remote build and some regions may not yet support it" in readme_text


def test_generated_readme_omits_preview_note_for_312(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "ga-readme",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version="3.12",
            include_github_actions=False,
            initialize_git=False,
        ),
    )

    readme_text = (project_path / "README.md").read_text(encoding="utf-8")

    assert "which is **Preview** on Azure Functions today" not in readme_text
