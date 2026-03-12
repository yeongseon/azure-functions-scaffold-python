from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from azure_functions_scaffold import __version__, cli
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
    assert 'requires-python = ">=3.10,<3.11"' in generated_pyproject
    assert 'target-version = "py310"' in generated_pyproject
    assert (project_dir / "Makefile").exists()
    assert "azure-functions-logging>=0.2.0" in generated_pyproject


def test_new_command_creates_timer_project(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "my-job", "--destination", str(tmp_path), "--template", "timer"],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "my-job"
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    assert (project_dir / "app/functions/timer.py").exists()
    assert (project_dir / "tests/test_timer.py").exists()
    assert "from app.functions.timer import timer_blueprint" in function_app_text
    assert "app.register_functions(timer_blueprint)" in function_app_text


@pytest.mark.parametrize(
    ("template_name", "function_module", "test_module", "import_name"),
    [
        ("queue", "app/functions/queue.py", "tests/test_queue.py", "queue_blueprint"),
        ("blob", "app/functions/blob.py", "tests/test_blob.py", "blob_blueprint"),
        (
            "servicebus",
            "app/functions/servicebus.py",
            "tests/test_servicebus.py",
            "servicebus_blueprint",
        ),
    ],
)
def test_new_command_creates_additional_trigger_projects(
    tmp_path: Path,
    template_name: str,
    function_module: str,
    test_module: str,
    import_name: str,
) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            f"{template_name}-app",
            "--destination",
            str(tmp_path),
            "--template",
            template_name,
        ],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / f"{template_name}-app"
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    assert (project_dir / function_module).exists()
    assert (project_dir / test_module).exists()
    assert f"from app.functions.{template_name} import {import_name}" in function_app_text


def test_new_command_fails_when_target_exists(tmp_path: Path) -> None:
    existing_dir = tmp_path / "my-api"
    existing_dir.mkdir()

    result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])

    assert result.exit_code == 1
    assert "Use --overwrite to replace it" in result.stdout


def test_new_command_supports_overwrite(tmp_path: Path) -> None:
    project_dir = tmp_path / "my-api"
    project_dir.mkdir()
    (project_dir / "stale.txt").write_text("stale", encoding="utf-8")

    result = runner.invoke(
        app,
        ["new", "my-api", "--destination", str(tmp_path), "--overwrite"],
    )

    assert result.exit_code == 0
    assert not (project_dir / "stale.txt").exists()
    assert (project_dir / "function_app.py").exists()


def test_new_command_rejects_unknown_template(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "my-api", "--destination", str(tmp_path), "--template", "durable"],
    )

    assert result.exit_code == 1
    assert "Unknown template 'durable'" in result.stdout


def test_new_command_supports_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "preview-api",
            "--destination",
            str(tmp_path),
            "--template",
            "queue",
            "--preset",
            "strict",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Dry run: create project at" in result.stdout
    assert "Template: queue" in result.stdout
    assert "Preset: strict" in result.stdout
    assert "app/functions/queue.py" in result.stdout
    assert not (tmp_path / "preview-api").exists()


def test_new_command_dry_run_reports_existing_target_without_overwrite(tmp_path: Path) -> None:
    (tmp_path / "preview-api").mkdir()

    result = runner.invoke(
        app,
        ["new", "preview-api", "--destination", str(tmp_path), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "Overwrite: blocked (target already exists)" in result.stdout


def test_new_command_dry_run_reports_overwrite_enabled(tmp_path: Path) -> None:
    (tmp_path / "preview-api").mkdir()

    result = runner.invoke(
        app,
        ["new", "preview-api", "--destination", str(tmp_path), "--dry-run", "--overwrite"],
    )

    assert result.exit_code == 0
    assert "Overwrite: enabled" in result.stdout


def test_new_command_supports_minimal_preset(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "minimal-api",
            "--destination",
            str(tmp_path),
            "--preset",
            "minimal",
            "--python-version",
            "3.12",
        ],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "minimal-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.12,<3.13"' in pyproject_text
    assert "pytest" not in pyproject_text
    assert "ruff" not in pyproject_text
    assert not (project_dir / "tests").exists()


def test_new_command_supports_interactive_mode(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "--destination", str(tmp_path), "--interactive"],
        input="interactive-api\nhttp\nstrict\n3.12\ny\nn\ny\ny\ny\nn\nn\nn\n",
    )

    assert result.exit_code == 0
    project_dir = tmp_path / "interactive-api"
    assert project_dir.exists()
    assert (project_dir / ".github/workflows/ci.yml").exists()
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert "mypy>=1.17.1" in pyproject_text


def test_new_command_supports_interactive_custom_tooling(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "--destination", str(tmp_path), "--interactive"],
        input="custom-api\nhttp\nstandard\n3.11\nn\nn\ny\ny\nn\nn\nn\nn\n",
    )

    assert result.exit_code == 0
    project_dir = tmp_path / "custom-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    readme_text = (project_dir / "README.md").read_text(encoding="utf-8")
    assert "ruff>=0.11.0" in pyproject_text
    assert "mypy>=1.17.1" in pyproject_text
    assert "pytest" not in pyproject_text
    assert "Preset: `custom`" in readme_text
    assert not (project_dir / "tests").exists()


def test_new_command_reprompts_invalid_interactive_choices(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "--destination", str(tmp_path), "--interactive"],
        input="\ninvalid-template\nhttp\ninvalid-preset\nstandard\n3.9\n3.12\nn\nn\ny\nn\ny\nn\nn\nn\n",
    )

    assert result.exit_code == 0
    project_dir = tmp_path / "my-api"
    assert project_dir.exists()
    assert "Unsupported template 'invalid-template'" in result.stdout
    assert "Unsupported preset 'invalid-preset'" in result.stdout
    assert "Unsupported Python version '3.9'" in result.stdout


def test_new_command_with_openapi_flag(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "openapi-api", "--destination", str(tmp_path), "--with-openapi"],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "openapi-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    http_text = (project_dir / "app/functions/http.py").read_text(encoding="utf-8")
    assert "azure-functions-openapi>=0.13.0" in pyproject_text
    assert "azure-functions-validation" not in pyproject_text
    assert "get_openapi_json" in function_app_text
    assert "get_openapi_yaml" in function_app_text
    assert "render_swagger_ui" in function_app_text
    assert "@openapi(" in http_text
    assert "validate_http" not in http_text


def test_new_command_with_validation_flag(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "validation-api", "--destination", str(tmp_path), "--with-validation"],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "validation-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    http_text = (project_dir / "app/functions/http.py").read_text(encoding="utf-8")
    models_text = (project_dir / "app/schemas/request_models.py").read_text(encoding="utf-8")
    assert "azure-functions-validation>=0.5.0" in pyproject_text
    assert "pydantic>=2.0.0" in pyproject_text
    assert "azure-functions-openapi" not in pyproject_text
    assert "@validate_http(" in http_text
    assert "methods=[\"POST\"]" in http_text
    assert "class HelloRequest(BaseModel):" in models_text
    assert "class HelloResponse(BaseModel):" in models_text


def test_new_command_with_openapi_and_validation_flags(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "full-api",
            "--destination",
            str(tmp_path),
            "--with-openapi",
            "--with-validation",
        ],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "full-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    http_text = (project_dir / "app/functions/http.py").read_text(encoding="utf-8")
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    assert "azure-functions-openapi>=0.13.0" in pyproject_text
    assert "azure-functions-validation>=0.5.0" in pyproject_text
    assert "pydantic>=2.0.0" in pyproject_text
    assert "@openapi(" in http_text
    assert "request_model=HelloRequest" in http_text
    assert "response_model=HelloResponse" in http_text
    assert "@validate_http(" in http_text
    assert "get_openapi_json" in function_app_text


def test_new_command_without_flags_excludes_openapi_and_validation(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "plain-api", "--destination", str(tmp_path)],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "plain-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    http_text = (project_dir / "app/functions/http.py").read_text(encoding="utf-8")
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    assert "azure-functions-openapi" not in pyproject_text
    assert "azure-functions-validation" not in pyproject_text
    assert "pydantic" not in pyproject_text
    assert "@openapi(" not in http_text
    assert "validate_http" not in http_text
    assert "get_openapi_json" not in function_app_text
    assert 'methods=["GET"]' in http_text


def test_new_command_interactive_with_openapi_and_validation(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "--destination", str(tmp_path), "--interactive"],
        input="full-interactive-api\nhttp\nstandard\n3.10\nn\nn\ny\nn\ny\ny\ny\nn\n",
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "full-interactive-api"
    assert project_dir.exists()
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    http_text = (project_dir / "app/functions/http.py").read_text(encoding="utf-8")
    assert "azure-functions-openapi>=0.13.0" in pyproject_text
    assert "azure-functions-validation>=0.5.0" in pyproject_text
    assert "@openapi(" in http_text
    assert "@validate_http(" in http_text
    assert "get_openapi_json" in function_app_text


def test_new_command_dry_run_reports_openapi_and_validation(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "dry-api",
            "--destination",
            str(tmp_path),
            "--with-openapi",
            "--with-validation",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "OpenAPI: enabled" in result.stdout
    assert "Validation: enabled" in result.stdout
    assert not (tmp_path / "dry-api").exists()


def test_new_command_with_doctor_flag(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "doctor-api", "--destination", str(tmp_path), "--with-doctor"],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "doctor-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    makefile_text = (project_dir / "Makefile").read_text(encoding="utf-8")
    assert "azure-functions-doctor>=0.15.0" in pyproject_text
    assert "make doctor" in makefile_text or "doctor:" in makefile_text


def test_new_command_without_doctor_excludes_doctor(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "no-doctor-api", "--destination", str(tmp_path)],
    )

    assert result.exit_code == 0

    project_dir = tmp_path / "no-doctor-api"
    pyproject_text = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
    makefile_text = (project_dir / "Makefile").read_text(encoding="utf-8")
    assert "azure-functions-doctor" not in pyproject_text
    assert "doctor:" not in makefile_text


def test_new_command_dry_run_reports_doctor(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "dry-api",
            "--destination",
            str(tmp_path),
            "--with-doctor",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Doctor: enabled" in result.stdout
    assert not (tmp_path / "dry-api").exists()

def test_add_http_command_updates_existing_project(tmp_path: Path) -> None:
    create_result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
    assert create_result.exit_code == 0

    project_dir = tmp_path / "my-api"
    result = runner.invoke(
        app,
        ["add", "http", "get-user", "--project-root", str(project_dir)],
    )

    assert result.exit_code == 0
    assert (project_dir / "app/functions/get_user.py").exists()
    assert (project_dir / "tests/test_get_user.py").exists()
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    assert "from app.functions.get_user import get_user_blueprint" in function_app_text
    assert "app.register_functions(get_user_blueprint)" in function_app_text


def test_add_timer_command_updates_existing_project(tmp_path: Path) -> None:
    create_result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
    assert create_result.exit_code == 0

    project_dir = tmp_path / "my-api"
    result = runner.invoke(
        app,
        ["add", "timer", "cleanup", "--project-root", str(project_dir)],
    )

    assert result.exit_code == 0
    assert (project_dir / "app/functions/cleanup.py").exists()
    assert (project_dir / "tests/test_cleanup.py").exists()


def test_add_command_supports_dry_run(tmp_path: Path) -> None:
    create_result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
    assert create_result.exit_code == 0

    project_dir = tmp_path / "my-api"
    result = runner.invoke(
        app,
        ["add", "servicebus", "process-events", "--project-root", str(project_dir), "--dry-run"],
    )

    assert result.exit_code == 0
    assert "Dry run: add servicebus function 'process_events'" in result.stdout
    assert "app/functions/process_events.py" in result.stdout
    assert "local.settings.json.example ServiceBusConnection" in result.stdout
    assert not (project_dir / "app/functions/process_events.py").exists()


def test_presets_command_lists_available_presets() -> None:
    result = runner.invoke(app, ["presets"])

    assert result.exit_code == 0
    assert "minimal: Minimal Azure Functions project" in result.stdout
    assert "strict: Azure Functions project with Ruff, mypy, and pytest defaults." in result.stdout


def test_add_command_rejects_invalid_trigger(tmp_path: Path) -> None:
    create_result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
    assert create_result.exit_code == 0

    result = runner.invoke(
        app,
        ["add", "durable", "sync-data", "--project-root", str(tmp_path / "my-api")],
    )

    assert result.exit_code == 1
    assert "Unsupported trigger 'durable'" in result.stdout


@pytest.mark.parametrize(
    ("trigger", "function_name"),
    [
        ("queue", "sync-data"),
        ("blob", "ingest-reports"),
        ("servicebus", "process-events"),
    ],
)
def test_add_additional_trigger_commands_update_existing_project(
    tmp_path: Path,
    trigger: str,
    function_name: str,
) -> None:
    create_result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
    assert create_result.exit_code == 0

    project_dir = tmp_path / "my-api"
    result = runner.invoke(
        app,
        ["add", trigger, function_name, "--project-root", str(project_dir)],
    )

    assert result.exit_code == 0
    normalized_name = function_name.replace("-", "_")
    assert (project_dir / f"app/functions/{normalized_name}.py").exists()
    assert (project_dir / f"tests/test_{normalized_name}.py").exists()
    function_app_text = (project_dir / "function_app.py").read_text(encoding="utf-8")
    assert (
        f"from app.functions.{normalized_name} import {normalized_name}_blueprint"
        in function_app_text
    )
    assert f"app.register_functions({normalized_name}_blueprint)" in function_app_text


def test_main_invokes_typer_app(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"value": False}

    def fake_app() -> None:
        called["value"] = True

    monkeypatch.setattr(cli, "app", fake_app)

    cli.main()

    assert called["value"] is True


def test_templates_command_lists_available_templates() -> None:
    result = runner.invoke(app, ["templates"])

    assert result.exit_code == 0
    assert "http: HTTP-trigger Azure Functions Python v2 application." in result.stdout
    assert "timer: Timer-trigger Azure Functions Python v2 application." in result.stdout
    assert "queue: Queue-trigger Azure Functions Python v2 application." in result.stdout
    assert "blob: Blob-trigger Azure Functions Python v2 application." in result.stdout
    assert "servicebus: Service Bus-trigger Azure Functions Python v2 application." in result.stdout


def test_version_option_prints_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout
