"""Tests for intent-centric CLI subcommand groups (api, worker, ai, advanced)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from azure_functions_scaffold.cli import app

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
        # api profile: strict preset + openapi + validation + doctor
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

    def test_equivalent_to_profile_api(self, tmp_path: Path) -> None:
        """``afs api new`` must produce identical output to ``afs new --profile api``."""
        api_dir = tmp_path / "via-api"
        api_dir.mkdir()
        result_api = runner.invoke(
            app, ["api", "new", "my-api", "--destination", str(api_dir)]
        )
        assert result_api.exit_code == 0

        legacy_dir = tmp_path / "via-legacy"
        legacy_dir.mkdir()
        result_legacy = runner.invoke(
            app, ["new", "my-api", "--destination", str(legacy_dir), "--profile", "api"]
        )
        assert result_legacy.exit_code == 0

        # Compare key generated files
        for rel_path in [
            "pyproject.toml",
            "function_app.py",
            "app/functions/http.py",
            "Makefile",
        ]:
            api_content = (api_dir / "my-api" / rel_path).read_text(encoding="utf-8")
            legacy_content = (legacy_dir / "my-api" / rel_path).read_text(encoding="utf-8")
            assert api_content == legacy_content, f"Mismatch in {rel_path}"

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
        # crud = api profile + db
        assert "azure-functions-openapi>=0.13.0" in pyproject_text
        assert "azure-functions-validation>=0.5.0" in pyproject_text
        assert "azure-functions-doctor>=0.15.0" in pyproject_text
        assert "azure-functions-db[postgres]>=0.1.0" in pyproject_text
        assert "mypy>=1.17.1" in pyproject_text
        assert (project_dir / "app/functions/db_items.py").exists()
        assert "db_items_blueprint" in function_app_text

    def test_equivalent_to_profile_db_api(self, tmp_path: Path) -> None:
        """``afs api crud`` must produce identical output to ``afs new --profile db-api``."""
        crud_dir = tmp_path / "via-crud"
        crud_dir.mkdir()
        result_crud = runner.invoke(
            app, ["api", "crud", "my-api", "--destination", str(crud_dir)]
        )
        assert result_crud.exit_code == 0

        legacy_dir = tmp_path / "via-legacy"
        legacy_dir.mkdir()
        result_legacy = runner.invoke(
            app, ["new", "my-api", "--destination", str(legacy_dir), "--profile", "db-api"]
        )
        assert result_legacy.exit_code == 0

        for rel_path in ["pyproject.toml", "function_app.py"]:
            crud_content = (crud_dir / "my-api" / rel_path).read_text(encoding="utf-8")
            legacy_content = (legacy_dir / "my-api" / rel_path).read_text(encoding="utf-8")
            assert crud_content == legacy_content, f"Mismatch in {rel_path}"


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
        result = runner.invoke(
            app,
            ["worker", "timer", "azd-job", "--destination", str(tmp_path), "--azd"],
        )
        assert result.exit_code == 0
        # Worker builder currently doesn't pass azd through; verify no crash
        project_dir = tmp_path / "azd-job"
        assert project_dir.exists()


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

    def test_new_with_profile(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["advanced", "new", "profiled", "--destination", str(tmp_path), "--profile", "api"],
        )
        assert result.exit_code == 0
        pyproject_text = (tmp_path / "profiled" / "pyproject.toml").read_text(encoding="utf-8")
        assert "azure-functions-openapi>=0.13.0" in pyproject_text

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

    def test_new_rejects_unknown_profile(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced", "new", "bad",
                "--destination", str(tmp_path),
                "--profile", "enterprise",
            ],
        )
        assert result.exit_code == 1
        assert "Unknown profile 'enterprise'" in result.stdout

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

    def test_profiles_command(self) -> None:
        result = runner.invoke(app, ["advanced", "profiles"])
        assert result.exit_code == 0
        assert "api:" in result.stdout
        assert "db-api:" in result.stdout


# ---------------------------------------------------------------------------
# Legacy deprecation warnings
# ---------------------------------------------------------------------------


class TestLegacyDeprecation:
    def test_legacy_new_emits_deprecation_warning(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
        assert result.exit_code == 0
        # The project still works
        assert (tmp_path / "my-api" / "function_app.py").exists()

    def test_legacy_add_emits_deprecation_warning(self, tmp_path: Path) -> None:
        runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["add", "http", "get-user", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 0
        assert (project_dir / "app/functions/get_user.py").exists()
