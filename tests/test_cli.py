from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from azure_functions_scaffold import __version__
from azure_functions_scaffold.cli import app

runner = CliRunner()


def test_new_command_creates_http_project(tmp_path: Path) -> None:
    result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])

    assert result.exit_code == 0

    project_dir = tmp_path / "my-api"
    assert project_dir.exists()
    assert (project_dir / "function_app.py").read_text(encoding="utf-8")
    assert (project_dir / "app/functions/http.py").read_text(encoding="utf-8")
    assert (project_dir / "tests/test_http.py").read_text(encoding="utf-8")
    generated_pyproject = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "my-api"' in generated_pyproject
    assert 'requires-python = ">=3.10"' in generated_pyproject
    assert 'target-version = "py310"' in generated_pyproject


def test_new_command_fails_when_target_exists(tmp_path: Path) -> None:
    existing_dir = tmp_path / "my-api"
    existing_dir.mkdir()

    result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])

    assert result.exit_code == 1
    assert "Target directory already exists" in result.stdout


def test_new_command_rejects_unknown_template(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "my-api", "--destination", str(tmp_path), "--template", "timer"],
    )

    assert result.exit_code == 1
    assert "Unknown template 'timer'" in result.stdout


def test_templates_command_lists_available_templates() -> None:
    result = runner.invoke(app, ["templates"])

    assert result.exit_code == 0
    assert "http: HTTP-trigger Azure Functions Python v2 application." in result.stdout


def test_version_option_prints_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout
