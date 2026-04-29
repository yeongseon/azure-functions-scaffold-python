# pyright: reportMissingImports=false
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
        webhooks_text = (project_dir / "app/functions/webhooks.py").read_text(encoding="utf-8")
        makefile_text = (project_dir / "Makefile").read_text(encoding="utf-8")
        # api intent: strict preset + openapi + validation + doctor
        assert "azure-functions-openapi>=0.17.0" in pyproject_text
        assert "azure-functions-validation>=0.7.0" in pyproject_text
        assert "azure-functions-doctor>=0.16.0" in pyproject_text
        assert "mypy>=1.17.1" in pyproject_text  # strict preset
        assert "@openapi(" in webhooks_text
        assert "ValidationError" in webhooks_text  # manual Pydantic validation
        assert (project_dir / "app/functions/health.py").exists()
        assert (project_dir / "app/functions/webhooks.py").exists()
        assert "health_blueprint" in function_app_text
        assert "webhooks_blueprint" in function_app_text
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
            app,
            ["api", "new", "my-api", "--destination", str(tmp_path), "--overwrite", "--yes"],
        )
        assert result.exit_code == 0
        assert not (project_dir / "stale.txt").exists()
        assert (project_dir / "function_app.py").exists()

    def test_custom_python_version(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "api",
                "new",
                "py312-api",
                "--destination",
                str(tmp_path),
                "--python-version",
                "3.12",
            ],
        )
        assert result.exit_code == 0
        pyproject_text = (tmp_path / "py312-api" / "pyproject.toml").read_text(encoding="utf-8")
        assert 'requires-python = ">=3.12,<3.13"' in pyproject_text


# ---------------------------------------------------------------------------
# afs new (top-level alias for afs api new)
# ---------------------------------------------------------------------------


class TestNew:
    """Tests for `afs new` — the top-level shortcut for `afs api new`."""

    def test_creates_api_project(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])

        assert result.exit_code == 0

        project_dir = tmp_path / "my-api"
        assert project_dir.exists()
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        # Same defaults as afs api new: strict + openapi + validation + doctor
        assert "azure-functions-openapi>=0.17.0" in pyproject_text
        assert "azure-functions-validation>=0.7.0" in pyproject_text
        assert "azure-functions-doctor>=0.16.0" in pyproject_text
        assert "mypy>=1.17.1" in pyproject_text  # strict preset
        assert (project_dir / "app/functions/health.py").exists()
        assert (project_dir / "app/functions/webhooks.py").exists()
        assert "health_blueprint" in function_app_text
        assert "webhooks_blueprint" in function_app_text

    def test_dry_run(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["new", "dry-api", "--destination", str(tmp_path), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run: create project at" in result.stdout
        assert not (tmp_path / "dry-api").exists()

    def test_overwrite(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-api"
        project_dir.mkdir()
        (project_dir / "stale.txt").write_text("stale", encoding="utf-8")

        result = runner.invoke(
            app,
            ["new", "my-api", "--destination", str(tmp_path), "--overwrite", "--yes"],
        )
        assert result.exit_code == 0
        assert not (project_dir / "stale.txt").exists()
        assert (project_dir / "function_app.py").exists()

    def test_overwrite_with_yes_flag(self, tmp_path: Path) -> None:
        project_dir = tmp_path / "my-api"
        project_dir.mkdir()
        (project_dir / "stale.txt").write_text("stale", encoding="utf-8")

        result = runner.invoke(
            app,
            ["new", "my-api", "--destination", str(tmp_path), "--overwrite", "--yes"],
        )

        assert result.exit_code == 0
        assert not (project_dir / "stale.txt").exists()
        assert (project_dir / "function_app.py").exists()

    def test_with_azd_flag(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["new", "azd-api", "--destination", str(tmp_path), "--azd"])
        assert result.exit_code == 0
        assert (tmp_path / "azd-api" / "azure.yaml").exists()

    def test_custom_python_version(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "new",
                "py312-api",
                "--destination",
                str(tmp_path),
                "--python-version",
                "3.12",
            ],
        )
        assert result.exit_code == 0
        pyproject_text = (tmp_path / "py312-api" / "pyproject.toml").read_text(encoding="utf-8")
        assert 'requires-python = ">=3.12,<3.13"' in pyproject_text

    def test_produces_same_output_as_api_new(self, tmp_path: Path) -> None:
        """Verify `afs new` and `afs api new` generate identical project structures."""
        api_dir = tmp_path / "via-api"
        new_dir = tmp_path / "via-new"
        api_dir.mkdir()
        new_dir.mkdir()

        result_api = runner.invoke(app, ["api", "new", "proj", "--destination", str(api_dir)])
        result_new = runner.invoke(app, ["new", "proj", "--destination", str(new_dir)])

        assert result_api.exit_code == 0, result_api.stdout
        assert result_new.exit_code == 0, result_new.stdout

        api_files = sorted(
            str(p.relative_to(api_dir / "proj"))
            for p in (api_dir / "proj").rglob("*")
            if p.is_file()
        )
        new_files = sorted(
            str(p.relative_to(new_dir / "proj"))
            for p in (new_dir / "proj").rglob("*")
            if p.is_file()
        )
        assert api_files == new_files


# ---------------------------------------------------------------------------
# afs api add
# ---------------------------------------------------------------------------


class TestApiAdd:
    def test_adds_http_function(self, tmp_path: Path) -> None:
        # First create a project
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(app, ["api", "add", "get-user", "--project-root", str(project_dir)])
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


class TestApiAddRoute:
    def test_adds_route(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["api", "add-route", "status", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 0
        assert (project_dir / "app/functions/status.py").exists()
        assert (project_dir / "tests/test_status.py").exists()
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        assert "status_blueprint" in function_app_text

    def test_dry_run(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["api", "add-route", "status", "--project-root", str(project_dir), "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Dry run:" in result.stdout
        assert not (project_dir / "app/functions/status.py").exists()

    def test_rejects_existing_route(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"
        runner.invoke(app, ["api", "add-route", "status", "--project-root", str(project_dir)])

        result = runner.invoke(
            app, ["api", "add-route", "status", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 1
        assert "already exists" in result.stdout


class TestApiAddResource:
    def test_adds_resource(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["api", "add-resource", "products", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 0
        assert (project_dir / "app/functions/products.py").exists()
        assert (project_dir / "app/services/products_service.py").exists()
        assert (project_dir / "app/schemas/products.py").exists()
        assert (project_dir / "tests/test_products.py").exists()
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        assert "products_blueprint" in function_app_text

    def test_dry_run(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app,
            ["api", "add-resource", "products", "--project-root", str(project_dir), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Dry run:" in result.stdout
        assert not (project_dir / "app/functions/products.py").exists()

    def test_rejects_existing_resource(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"
        runner.invoke(app, ["api", "add-resource", "products", "--project-root", str(project_dir)])

        result = runner.invoke(
            app, ["api", "add-resource", "products", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 1
        assert "already exists" in result.stdout


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
        result = runner.invoke(app, ["worker", "timer", "my-job", "--destination", str(tmp_path)])
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
        result = runner.invoke(app, ["ai", "agent", "my-agent", "--destination", str(tmp_path)])
        assert result.exit_code == 0

        project_dir = tmp_path / "my-agent"
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        assert (project_dir / "app/graphs/echo_agent.py").exists()
        assert "LangGraphApp" in function_app_text
        assert '# "azure-functions-langgraph>=0.5.1",' in pyproject_text
        assert "Uncomment after azure-functions-langgraph is published on PyPI." in pyproject_text

    def test_function_app_imports_have_no_blank_lines_within_third_party_section(
        self, tmp_path: Path
    ) -> None:
        result = runner.invoke(app, ["ai", "agent", "my-agent", "--destination", str(tmp_path)])
        assert result.exit_code == 0

        function_app_text = (tmp_path / "my-agent" / "function_app.py").read_text(encoding="utf-8")
        head = function_app_text.split("# Create LangGraph app")[0]
        assert "import azure.functions as func\nfrom azure_functions_langgraph" in head

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
        result = runner.invoke(app, ["advanced", "new", "my-api", "--destination", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "my-api" / "function_app.py").exists()

    def test_new_with_all_flags(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "full-api",
                "--destination",
                str(tmp_path),
                "--preset",
                "strict",
                "--with-openapi",
                "--with-validation",
                "--with-doctor",
                "--azd",
            ],
        )
        assert result.exit_code == 0
        project_dir = tmp_path / "full-api"
        pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
        assert "azure-functions-openapi>=0.17.0" in pyproject_text
        assert "azure-functions-validation>=0.7.0" in pyproject_text
        assert "azure-functions-doctor>=0.16.0" in pyproject_text
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
                "advanced",
                "add",
                "servicebus",
                "process-events",
                "--project-root",
                str(project_dir),
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


class TestAdvancedNewFlagValidation:
    def test_with_openapi_rejected_for_timer_template(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "myproj",
                "--destination",
                str(tmp_path),
                "--template",
                "timer",
                "--with-openapi",
            ],
        )

        assert result.exit_code != 0
        out = (result.stdout or "") + (result.stderr or "")
        assert "timer" in out
        assert "--with-openapi" in out
        assert not (tmp_path / "myproj").exists()

    def test_with_validation_rejected_for_queue_template(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "myproj",
                "--destination",
                str(tmp_path),
                "--template",
                "queue",
                "--with-validation",
            ],
        )

        assert result.exit_code != 0
        out = (result.stdout or "") + (result.stderr or "")
        assert "--with-validation" in out

    def test_with_doctor_rejected_for_langgraph_template(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "myproj",
                "--destination",
                str(tmp_path),
                "--template",
                "langgraph",
                "--with-doctor",
            ],
        )

        assert result.exit_code != 0
        out = (result.stdout or "") + (result.stderr or "")
        assert "--with-doctor" in out

    def test_http_template_accepts_all_features(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "myproj",
                "--destination",
                str(tmp_path),
                "--template",
                "http",
                "--with-openapi",
                "--with-validation",
                "--with-doctor",
                "--azd",
            ],
        )

        assert result.exit_code == 0, (
            f"Expected success, got: {result.stdout}\n{result.stderr or ''}"
        )

    def test_azd_allowed_for_non_http_templates(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "myproj",
                "--destination",
                str(tmp_path),
                "--template",
                "timer",
                "--azd",
            ],
        )

        assert result.exit_code == 0, (
            f"Expected success, got: {result.stdout}\n{result.stderr or ''}"
        )

    def test_doctor_allowed_for_timer_template(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "myproj",
                "--destination",
                str(tmp_path),
                "--template",
                "timer",
                "--with-doctor",
            ],
        )

        assert result.exit_code == 0, (
            f"Expected success, got: {result.stdout}\n{result.stderr or ''}"
        )

    def test_multiple_invalid_flags_listed_together(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "advanced",
                "new",
                "myproj",
                "--destination",
                str(tmp_path),
                "--template",
                "blob",
                "--with-openapi",
                "--with-validation",
            ],
        )

        assert result.exit_code != 0
        out = (result.stdout or "") + (result.stderr or "")
        assert "--with-openapi" in out
        assert "--with-validation" in out


class TestAdvancedAddRoute:
    def test_adds_route(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["advanced", "add-route", "status", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 0
        assert (project_dir / "app/functions/status.py").exists()
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        assert "status_blueprint" in function_app_text

    def test_dry_run(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app,
            ["advanced", "add-route", "status", "--project-root", str(project_dir), "--dry-run"],
        )
        assert result.exit_code == 0
        assert "Dry run:" in result.stdout
        assert not (project_dir / "app/functions/status.py").exists()


class TestAdvancedAddResource:
    def test_adds_resource(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app, ["advanced", "add-resource", "products", "--project-root", str(project_dir)]
        )
        assert result.exit_code == 0
        assert (project_dir / "app/functions/products.py").exists()
        assert (project_dir / "app/services/products_service.py").exists()
        assert (project_dir / "app/schemas/products.py").exists()
        function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
        assert "products_blueprint" in function_app_text

    def test_dry_run(self, tmp_path: Path) -> None:
        runner.invoke(app, ["api", "new", "my-api", "--destination", str(tmp_path)])
        project_dir = tmp_path / "my-api"

        result = runner.invoke(
            app,
            [
                "advanced",
                "add-resource",
                "products",
                "--project-root",
                str(project_dir),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "Dry run:" in result.stdout
        assert not (project_dir / "app/functions/products.py").exists()


# ---------------------------------------------------------------------------
# Legacy commands are deprecated shims
# ---------------------------------------------------------------------------


class TestLegacyDeprecated:
    """Legacy commands now print a deprecation warning and forward to the new command."""

    def test_legacy_add_warns_and_forwards_for_http(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["add", "http", "get-user", "--project-root", str(tmp_path)])
        assert "deprecated" in result.stderr.lower()
        assert "afs api add" in result.stderr

    def test_legacy_add_suggests_advanced_for_non_http(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["add", "queue", "sync", "--project-root", str(tmp_path)])
        assert "deprecated" in result.stderr.lower()
        assert "afs advanced add queue" in result.stderr

    def test_legacy_profiles_warns_and_lists_presets(self) -> None:
        result = runner.invoke(app, ["profiles"])
        assert result.exit_code == 0
        assert "deprecated" in result.stderr.lower()
        assert (
            "minimal" in result.stdout or "standard" in result.stdout or "strict" in result.stdout
        )


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


class TestSuccessMessage:
    """Verify the post-scaffold landing message content."""

    def test_success_message_shows_project_info(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["api", "new", "msg-test", "--destination", str(tmp_path)])
        assert result.exit_code == 0
        assert "Project created successfully" in result.stdout
        assert "Template:  http" in result.stdout
        assert "Preset:    strict" in result.stdout
        assert "Features:" in result.stdout
        assert "openapi" in result.stdout

    def test_success_message_shows_full_path_in_cd(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["api", "new", "cd-test", "--destination", str(tmp_path)])
        assert result.exit_code == 0
        # Must show the full project path, not just the project name
        expected_path = str(tmp_path / "cd-test")
        assert f"cd {expected_path}" in result.stdout

    def test_success_message_shows_platform_aware_activate(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["api", "new", "act-test", "--destination", str(tmp_path)])
        assert result.exit_code == 0
        assert "source .venv/bin/activate" in result.stdout
        assert ".venv\\Scripts\\activate" in result.stdout

    def test_success_message_shows_openapi_docs_url(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["api", "new", "docs-test", "--destination", str(tmp_path)])
        assert result.exit_code == 0
        assert "http://localhost:7071/api/docs" in result.stdout

    def test_success_message_omits_openapi_url_for_worker(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app, ["worker", "timer", "timer-test", "--destination", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "Project created successfully" in result.stdout
        assert "http://localhost:7071/api/docs" not in result.stdout
