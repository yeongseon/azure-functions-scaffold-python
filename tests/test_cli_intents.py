"""Tests for intent-centric CLI subcommand groups (api, worker, ai, advanced)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from azure_functions_scaffold.cli import app
from azure_functions_scaffold.template_registry import INTENT_SPECS, list_presets, list_templates

runner = CliRunner()


# ---------------------------------------------------------------------------
# afs api new
# ---------------------------------------------------------------------------


class TestApiNew:
    def test_creates_api_project_with_openapi_validation_doctor(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])

        assert result.exit_code == 0

        project_dir = tmp_path / "my-api"
        assert project_dir.exists()
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        http_text = (project_dir / "app/functions/http.py").read_text(encoding="utf-8")
        makefile_text = (project_dir / "Makefile").read_text(encoding="utf-8")
        # api intent: strict preset + openapi + validation + doctor
        assert "azure-functions-openapi>=0.13.0" in pyproject_text
        assert "azure-functions-validation>=0.5.0" in pyproject_text
        assert "azure-functions-doctor>=0.15.0" in pyproject_text
        assert "mypy>=1.17.1" in pyproject_text  # strict preset
        assert "@openapi(" in http_text
        assert "@validate_http(" in http_text
        assert "get_openapi_json" in function_app_text
        assert "doctor:" in makefile_text or "make doctor" in makefile_text
        # no azd by default
        assert not (project_dir / "azure.yaml").exists()
        # no db by default
        assert "azure-functions-db" not in pyproject_text

    def test_with_azd_flag(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["api", "new", "azd-api", "--destination", str(tmp_path), "--azd"]
        )
        assert result.exit_code == 0
        assert (tmp_path / "azd-api" / "azure.yaml").exists()

    def test_dry_run(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["api", "new", "dry-api", "--destination", str(tmp_path), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Dry run: create project at" in result.stdout
        assert not (tmp_path / "dry-api").exists()

    def test_overwrite(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-api"
        project_dir.mkdir()
        (project_dir / "stale.txt").write_text("stale", encoding="utf-8")

        result = runner.invoke(
            app, ["api", "new", "my-api", "--destination", str(tmp_path), "--overwrite"]
        )
        assert result.exit_code == 0
        assert not (project_dir / "stale.txt").exists()
        assert (project_dir / "function_app.py").exists()

    def test_custom_python_version(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "api", "new", "py312-api",
                "--destination", str(tmp_path),
                "--python-version", "3.12",
            ],
        )
        assert result.exit_code == 0
        pyproject_text = (tmp_path / "py312-api" / "pyproject.toml").read_text(encoding="utf-8")
        assert 'requires-python = ">=3.12,<3.13"' in pyproject_text


# ---------------------------------------------------------------------------
# afs api crud
# ---------------------------------------------------------------------------


class TestApiCrud:
    def test_creates_crud_project_with_db(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["api", "crud", "my-crud", "--destination", str(tmp_path)])

        assert result.exit_code == 0

        project_dir = tmp_path / "my-crud"
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        # crud = api + db
        assert "azure-functions-openapi>=0.13.0" in pyproject_text
        assert "azure-functions-validation>=0.5.0" in pyproject_text
        assert "azure-functions-doctor>=0.15.0" in pyproject_text
        assert "azure-functions-db[postgres]>=0.1.0" in pyproject_text
        assert "mypy>=1.17.1" in pyproject_text
        assert (project_dir / "app/functions/db_items.py").exists()
        assert "db_items_blueprint" in function_app_text


# ---------------------------------------------------------------------------
# afs api add
# ---------------------------------------------------------------------------


class TestApiAdd:
    def test_adds_http_function(self, tmp_path: Path) -> None:
        # First create a project
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["api", "add", "get-user", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 0
        assert (project_dir / "app/functions/get_user.py").exists()
        assert (project_dir / "tests/test_get_user.py").exists()
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        assert "get_user_blueprint" in function_app_text

    def test_dry_run(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["api", "add", "list-items", "--project-root", str(project_dir), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Dry run:" in result.stdout
        assert not (project_dir / "app/functions/list_items.py").exists()


# ---------------------------------------------------------------------------
# afs worker <trigger>
# ---------------------------------------------------------------------------


class TestWorker:
    @pytest.mark.parametrize(
        ("subcommand", "template_name", "function_module"),
        [
            ("timer", "timer", "app/functions/timer.py"),
            ("queue", "queue", "app/functions/queue.py"),
            ("blob", "blob", "app/functions/blob.py"),
            ("servicebus", "servicebus", "app/functions/servicebus.py"),
            ("eventhub", "eventhub", "app/functions/eventhub.py"),
        ],
    )
    def test_creates_worker_project(
        self,
        tmp_path: Path,
        subcommand: str,
        template_name: str,
        function_module: str,
    ) -> None:
        result = runner.invoke(
            app,
            ["worker", subcommand, f"{template_name}-worker", "--destination", str(tmp_path)],
        )
        assert result.exit_code == 0

        project_dir = tmp_path / f"{template_name}-worker"
        assert project_dir.exists()
        assert (project_dir / function_module).exists()
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        assert f"{template_name}_blueprint" in function_app_text

    def test_timer_uses_standard_preset(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["worker", "timer", "my-job", "--destination", str(tmp_path)]
        )
        assert result.exit_code == 0

        project_dir = tmp_path / "my-job"
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        # standard preset includes ruff and pytest but NOT mypy
        assert "ruff" in pyproject_text
        assert "mypy" not in pyproject_text

    def test_worker_dry_run(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["worker", "queue", "my-worker", "--destination", str(tmp_path), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Dry run: create project at" in result.stdout
        assert not (tmp_path / "my-worker").exists()

    def test_worker_with_azd(self, tmp_path: Path) -> None:
        """Regression: --azd flag must produce azure.yaml for worker commands."""
        result = runner.invoke(
            app,
            ["worker", "timer", "azd-job", "--destination", str(tmp_path), "--azd"],
        )
        assert result.exit_code == 0
        project_dir = tmp_path / "azd-job"
        assert project_dir.exists()
        assert (project_dir / "azure.yaml").exists()


# ---------------------------------------------------------------------------
# afs ai agent
# ---------------------------------------------------------------------------


class TestAiAgent:
    def test_creates_langgraph_project(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["ai", "agent", "my-agent", "--destination", str(tmp_path)]
        )
        assert result.exit_code == 0

        project_dir = tmp_path / "my-agent"
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        assert (project_dir / "app/graphs/echo_agent.py").exists()
        assert "LangGraphApp" in function_app_text
        assert "azure-functions-langgraph>=0.5.0" in pyproject_text

    def test_dry_run(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["ai", "agent", "my-agent", "--destination", str(tmp_path), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Dry run: create project at" in result.stdout
        assert not (tmp_path / "my-agent").exists()

    def test_ai_agent_with_azd(self, tmp_path: Path) -> None:
        """Regression: --azd flag must produce azure.yaml for ai commands."""
        result = runner.invoke(
            app,
            ["ai", "agent", "azd-agent", "--destination", str(tmp_path), "--azd"],
        )
        assert result.exit_code == 0
        project_dir = tmp_path / "azd-agent"
        assert project_dir.exists()
        assert (project_dir / "azure.yaml").exists()


# ---------------------------------------------------------------------------
# afs advanced new / add
# ---------------------------------------------------------------------------


class TestAdvanced:
    def test_new_creates_project(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["advanced", "new", "my-api", "--destination", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert (tmp_path / "my-api" / "function_app.py").exists()

    def test_new_with_all_flags(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced", "new", "full-api",
                "--destination", str(tmp_path),
                "--preset", "strict",
                "--with-openapi",
                "--with-validation",
                "--with-doctor",
                "--with-db",
                "--azd",
            ],
        )
        assert result.exit_code == 0
        project_dir = tmp_path / "full-api"
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        assert "azure-functions-openapi>=0.13.0" in pyproject_text
        assert "azure-functions-validation>=0.5.0" in pyproject_text
        assert "azure-functions-doctor>=0.15.0" in pyproject_text
        assert "azure-functions-db[postgres]>=0.1.0" in pyproject_text
        assert (project_dir / "azure.yaml").exists()

    def test_new_dry_run(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["advanced", "new", "dry", "--destination", str(tmp_path), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Dry run: create project at" in result.stdout

    def test_add_function(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app,
            ["advanced", "add", "timer", "cleanup", "--project-root", str(project_dir)],
        )
        assert result.exit_code == 0
        assert (project_dir / "app/functions/cleanup.py").exists()

    def test_add_dry_run(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app,
            [
                "advanced", "add", "servicebus", "process-events",
                "--project-root", str(project_dir),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Dry run:" in result.stdout

    def test_add_rejects_invalid_trigger(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app,
            ["advanced", "add", "graphql", "sync", "--project-root", str(project_dir)],
        )
        assert result.exit_code == 1
        assert "Unsupported trigger 'graphql'" in result.stdout

    def test_templates_command(self) -> None:
        result = runner.invoke(app, ["advanced", "templates"])
        assert result.exit_code == 0
        assert "http:" in result.stdout
        assert "timer:" in result.stdout

    def test_presets_command(self) -> None:
        result = runner.invoke(app, ["advanced", "presets"])
        assert result.exit_code == 0
        assert "minimal:" in result.stdout
        assert "strict:" in result.stdout


# ---------------------------------------------------------------------------
# Legacy commands are removed
# ---------------------------------------------------------------------------


class TestLegacyRemoved:
    def test_legacy_new_command_not_available(self) -> None:
        result = runner.invoke(app, ["new", "my-api"])
        assert result.exit_code != 0
        assert "No such command" in result.stdout or "No such command" in (result.stderr or "")

    def test_legacy_add_command_not_available(self) -> None:
        result = runner.invoke(app, ["add", "http", "get-user"])
        assert result.exit_code != 0
        assert "No such command" in result.stdout or "No such command" in (result.stderr or "")

    def test_legacy_profiles_command_not_available(self) -> None:
        result = runner.invoke(app, ["profiles"])
        assert result.exit_code != 0
        assert "No such command" in result.stdout or "No such command" in (result.stderr or "")


# ---------------------------------------------------------------------------
# INTENT_SPECS completeness
# ---------------------------------------------------------------------------


class TestIntentSpecsCompleteness:
    """Verify every INTENT_SPECS entry references a valid template and preset."""

    @pytest.mark.parametrize("intent_key", list(INTENT_SPECS.keys()))
    def test_intent_spec_references_valid_template(self, intent_key: str) -> None:
        spec = INTENT_SPECS[intent_key]
        template_names = {t.name for t in list_templates()}
        assert spec.template in template_names, (
            f"Intent '{intent_key}' references unknown template '{spec.template}'"
        )

    @pytest.mark.parametrize("intent_key", list(INTENT_SPECS.keys()))
    def test_intent_spec_references_valid_preset(self, intent_key: str) -> None:
        spec = INTENT_SPECS[intent_key]
        preset_names = {p.name for p in list_presets()}
        assert spec.preset in preset_names, (
            f"Intent '{intent_key}' references unknown preset '{spec.preset}'"
        )


# ---------------------------------------------------------------------------
# Error path tests
# ---------------------------------------------------------------------------


class TestErrorPaths:
    """Verify invalid inputs produce clean CLI errors, not raw tracebacks."""

    def test_api_new_rejects_invalid_python_version(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["api", "new", "bad", "--destination", str(tmp_path), "--python-version", "3.9"]
        )
        assert result.exit_code == 1
        assert "Unsupported Python version" in result.stdout

    def test_advanced_new_rejects_invalid_preset(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["advanced", "new", "bad", "--destination", str(tmp_path), "--preset", "enterprise"],
        )
        assert result.exit_code == 1
        assert "Unknown preset" in result.stdout

    def test_advanced_new_rejects_invalid_python_version(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["advanced", "new", "bad", "--destination", str(tmp_path), "--python-version", "2.7"],
        )
        assert result.exit_code == 1
        assert "Unsupported Python version" in result.stdout

    def test_advanced_new_rejects_invalid_template(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["advanced", "new", "bad", "--destination", str(tmp_path), "--template", "graphql"],
        )
        assert result.exit_code == 1
        assert "Unknown template" in result.stdout
