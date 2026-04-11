from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import TemplateContext
from azure_functions_scaffold.scaffolder import (
    _initialize_git_repository,
    _iter_template_files,
    _render_path,
    _slugify,
    build_template_context,
    describe_scaffold_project,
    resolve_target_dir,
    scaffold_project,
    validate_project_name,
)
from azure_functions_scaffold.template_registry import (
    build_project_options,
    get_preset,
    get_template,
    list_presets,
    list_templates,
    validate_python_version,
    validate_tooling,
)


def test_list_templates_returns_http_template() -> None:
    templates = list_templates()

    assert [template.name for template in templates] == [
        "http",
        "timer",
        "queue",
        "blob",
        "servicebus",
        "eventhub",
        "cosmosdb",
        "durable",
        "ai",
        "langgraph",
    ]
    assert all(template.root.is_dir() for template in templates)


def test_get_template_rejects_unknown_name() -> None:
    with pytest.raises(ScaffoldError, match="Unknown template"):
        get_template("graphql")


@pytest.mark.parametrize(
    ("project_name", "expected"),
    [
        ("my-api", "my-api"),
        ("  my-api  ", "my-api"),
        ("hello_world", "hello_world"),
    ],
)
def test_validate_project_name_accepts_supported_names(
    project_name: str,
    expected: str,
) -> None:
    assert validate_project_name(project_name) == expected


@pytest.mark.parametrize(
    "project_name",
    ["", "   ", ".", "..", "foo/bar", "foo\\bar", "-name", "my project", "한글이름"],
)
def test_validate_project_name_rejects_invalid_values(project_name: str) -> None:
    with pytest.raises(ScaffoldError):
        validate_project_name(project_name)


def test_build_template_context_creates_slug() -> None:
    options = build_project_options(
        preset_name="standard",
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
    )
    context = build_template_context("My_API", options)

    assert context == TemplateContext(
        project_name="My_API",
        project_slug="my-api",
        python_version="3.10",
        python_upper_bound="3.11",
        preset_name="standard",
        include_github_actions=False,
        initialize_git=False,
        include_ruff=True,
        include_mypy=False,
        include_pytest=True,
        include_openapi=False,
        include_validation=False,
        include_doctor=False,
        include_azd=False,
        include_db=False,
    )


def test_resolve_target_dir_rejects_file_destination(tmp_path: Path) -> None:
    file_path = tmp_path / "target.txt"
    file_path.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ScaffoldError, match="Destination must be a directory"):
        resolve_target_dir(file_path, "sample")


def test_iter_template_files_returns_template_files() -> None:
    template_root = get_template("http").root

    template_files = _iter_template_files(template_root)

    assert template_files
    assert all(path.is_file() for path in template_files)


def test_render_path_strips_jinja_suffix_and_replaces_placeholders() -> None:
    context = TemplateContext(
        project_name="Sample API",
        project_slug="sample-api",
        python_version="3.10",
        python_upper_bound="3.11",
        preset_name="standard",
        include_github_actions=False,
        initialize_git=False,
        include_ruff=True,
        include_mypy=False,
        include_pytest=True,
        include_openapi=False,
        include_validation=False,
        include_doctor=False,
        include_azd=False,
        include_db=False,
    )

    rendered = _render_path(Path("__project_name__/README.md.j2"), context)

    assert rendered == Path("sample-api/README.md")


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("My API", "my-api"),
        ("hello_world", "hello-world"),
        ("***", "azure-functions-app"),
    ],
)
def test_slugify_normalizes_names(raw_value: str, expected: str) -> None:
    assert _slugify(raw_value) == expected


def test_scaffold_project_rejects_existing_target(tmp_path: Path) -> None:
    target_dir = tmp_path / "sample"
    target_dir.mkdir()

    with pytest.raises(ScaffoldError, match="Use --overwrite to replace it"):
        scaffold_project("sample", tmp_path)


def test_scaffold_project_can_overwrite_existing_target(tmp_path: Path) -> None:
    target_dir = tmp_path / "sample"
    target_dir.mkdir()
    stale_file = target_dir / "stale.txt"
    stale_file.write_text("stale", encoding="utf-8")

    project_path = scaffold_project("sample", tmp_path, overwrite=True)

    assert project_path == target_dir
    assert not stale_file.exists()
    assert (project_path / "function_app.py").exists()


def test_describe_scaffold_project_reports_expected_files(tmp_path: Path) -> None:
    lines = describe_scaffold_project(
        "sample",
        tmp_path,
        template_name="queue",
        options=build_project_options(
            preset_name="strict",
            python_version="3.12",
            include_github_actions=True,
            initialize_git=True,
        ),
    )

    assert lines[0] == f"Dry run: create project at {tmp_path / 'sample'}"
    assert "Template: queue" in lines
    assert "Preset: strict" in lines
    assert "GitHub Actions: enabled" in lines
    assert "Git initialization: enabled" in lines
    assert "  - function_app.py" in lines
    assert "  - app/functions/queue.py" in lines
    assert "  - .github/workflows/ci.yml" in lines


def test_describe_scaffold_project_reports_overwrite_status(tmp_path: Path) -> None:
    target_dir = tmp_path / "sample"
    target_dir.mkdir()

    blocked_lines = describe_scaffold_project("sample", tmp_path)
    overwrite_lines = describe_scaffold_project("sample", tmp_path, overwrite=True)

    assert "Overwrite: blocked (target already exists)" in blocked_lines
    assert "Overwrite: enabled" in overwrite_lines


def test_scaffold_project_renders_template_option(tmp_path: Path) -> None:
    project_path = scaffold_project("sample", tmp_path, template_name="http")

    assert project_path == tmp_path / "sample"
    assert (project_path / "README.md").exists()


@pytest.mark.parametrize(
    ("template_name", "expected_function", "expected_service"),
    [
        ("http", "app/functions/http.py", "app/services/hello_service.py"),
        ("timer", "app/functions/timer.py", "app/services/maintenance_service.py"),
        ("queue", "app/functions/queue.py", "app/services/queue_service.py"),
        ("blob", "app/functions/blob.py", "app/services/blob_service.py"),
        ("servicebus", "app/functions/servicebus.py", "app/services/servicebus_service.py"),
        ("eventhub", "app/functions/eventhub.py", "app/services/eventhub_service.py"),
        ("cosmosdb", "app/functions/cosmosdb.py", "app/services/cosmosdb_service.py"),
        ("durable", "app/functions/durable.py", "app/services/durable_service.py"),
        ("ai", "app/functions/ai.py", "app/services/ai_service.py"),
    ],
)
def test_scaffold_project_generates_expected_project_contract(
    tmp_path: Path,
    template_name: str,
    expected_function: str,
    expected_service: str,
) -> None:
    project_path = scaffold_project(
        f"{template_name}-sample",
        tmp_path,
        template_name=template_name,
        options=build_project_options(
            preset_name="strict",
            python_version="3.12",
            include_github_actions=True,
            initialize_git=False,
        ),
    )

    pyproject_text = (project_path / "pyproject.toml").read_text(encoding="utf-8")
    readme_text = (project_path / "README.md").read_text(encoding="utf-8")

    assert (project_path / "function_app.py").exists()
    assert (project_path / "host.json").exists()
    assert (project_path / "local.settings.json.example").exists()
    assert (project_path / "Makefile").exists()
    assert (project_path / ".github/workflows/ci.yml").exists()
    assert (project_path / expected_function).exists()
    assert (project_path / expected_service).exists()
    assert 'requires-python = ">=3.12,<3.13"' in pyproject_text
    assert "ruff>=0.11.0" in pyproject_text
    assert "mypy>=1.17.1" in pyproject_text
    assert "pytest>=8.3.5" in pyproject_text
    assert "Preset: `strict`" in readme_text
    assert "azure-functions-logging>=0.2.0" in pyproject_text


@pytest.mark.parametrize("template_name", ["queue", "blob", "servicebus", "eventhub", "cosmosdb"])
def test_binding_templates_include_extension_bundle(tmp_path: Path, template_name: str) -> None:
    project_path = scaffold_project(
        f"{template_name}-sample",
        tmp_path,
        template_name=template_name,
    )

    host_config = json.loads((project_path / "host.json").read_text(encoding="utf-8"))
    assert host_config["extensionBundle"]["id"] == "Microsoft.Azure.Functions.ExtensionBundle"


def test_scaffold_project_renders_timer_template_option(tmp_path: Path) -> None:
    project_path = scaffold_project("sample-job", tmp_path, template_name="timer")

    assert project_path == tmp_path / "sample-job"
    assert (project_path / "app/functions/timer.py").exists()
    assert (project_path / "tests/test_timer.py").exists()
    function_app_text = (project_path / "function_app.py").read_text(encoding="utf-8")
    assert "from app.functions.timer import timer_blueprint" in function_app_text


@pytest.mark.parametrize(
    ("template_name", "expected_module", "expected_test"),
    [
        ("queue", "app/functions/queue.py", "tests/test_queue.py"),
        ("blob", "app/functions/blob.py", "tests/test_blob.py"),
        ("servicebus", "app/functions/servicebus.py", "tests/test_servicebus.py"),
        ("eventhub", "app/functions/eventhub.py", "tests/test_eventhub.py"),
        ("cosmosdb", "app/functions/cosmosdb.py", "tests/test_cosmosdb.py"),
        ("durable", "app/functions/durable.py", "tests/test_durable.py"),
        ("ai", "app/functions/ai.py", "tests/test_ai.py"),
    ],
)
def test_scaffold_project_renders_additional_trigger_templates(
    tmp_path: Path,
    template_name: str,
    expected_module: str,
    expected_test: str,
) -> None:
    project_path = scaffold_project("sample-worker", tmp_path, template_name=template_name)

    assert project_path == tmp_path / "sample-worker"
    assert (project_path / expected_module).exists()
    assert (project_path / expected_test).exists()


def test_list_presets_returns_supported_presets() -> None:
    presets = list_presets()

    assert [preset.name for preset in presets] == ["minimal", "standard", "strict"]


def test_get_preset_rejects_unknown_name() -> None:
    with pytest.raises(ScaffoldError, match="Unknown preset"):
        get_preset("custom")


def test_validate_python_version_rejects_unsupported_version() -> None:
    with pytest.raises(ScaffoldError, match="Unsupported Python version"):
        validate_python_version("3.9")


def test_validate_tooling_rejects_unknown_tool() -> None:
    with pytest.raises(ScaffoldError, match="Unsupported tooling selection"):
        validate_tooling(("ruff", "semgrep"))


def test_build_project_options_marks_custom_tooling() -> None:
    options = build_project_options(
        preset_name="standard",
        python_version="3.11",
        include_github_actions=False,
        initialize_git=False,
        tooling=("ruff", "mypy"),
    )

    assert options.preset_name == "custom"
    assert options.tooling == ("ruff", "mypy")


def test_scaffold_project_can_initialize_git_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], Path]] = []

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> object:
        calls.append((command, cwd))
        return object()

    monkeypatch.setattr(
        "azure_functions_scaffold.scaffolder.shutil.which",
        lambda _: "/usr/bin/git",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    project_path = scaffold_project(
        "sample",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=True,
        ),
    )

    assert project_path.exists()
    assert calls == [(["/usr/bin/git", "init"], project_path)]


def test_initialize_git_repository_rejects_missing_git(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "azure_functions_scaffold.scaffolder.shutil.which",
        lambda _: None,
    )

    with pytest.raises(ScaffoldError, match="Git is not installed"):
        _initialize_git_repository(tmp_path)


def test_initialize_git_repository_handles_missing_stderr_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> object:
        raise subprocess.CalledProcessError(returncode=1, cmd=command, stderr=None)

    monkeypatch.setattr(
        "azure_functions_scaffold.scaffolder.shutil.which",
        lambda _: "/usr/bin/git",
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(
        ScaffoldError,
        match="Failed to initialize a git repository: git init failed",
    ):
        _initialize_git_repository(tmp_path)


def _run_generated_project_checks(project_path: Path) -> None:
    subprocess.run(
        ["make", "install"],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["make", "check-all"],
        cwd=project_path,
        check=True,
        capture_output=True,
        text=True,
    )


def _current_python_minor() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.mark.parametrize(
    ("template_name", "preset_name"),
    [
        ("http", "strict"),
        ("timer", "standard"),
        ("queue", "standard"),
        ("blob", "standard"),
        ("servicebus", "standard"),
        ("eventhub", "standard"),
        ("cosmosdb", "standard"),
        ("durable", "standard"),
        ("ai", "standard"),
    ],
)
def test_simple_trigger_templates_pass_generated_checks(
    tmp_path: Path,
    template_name: str,
    preset_name: str,
) -> None:
    project_path = scaffold_project(
        f"{template_name}-e2e",
        tmp_path,
        template_name=template_name,
        options=build_project_options(
            preset_name=preset_name,
            python_version=_current_python_minor(),
            include_github_actions=False,
            initialize_git=False,
        ),
    )

    _run_generated_project_checks(project_path)


def test_scaffold_project_with_azd_generates_azure_yaml(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "azd-sample",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_azd=True,
        ),
    )

    azure_yaml = project_path / "azure.yaml"
    assert azure_yaml.exists()
    azure_yaml_text = azure_yaml.read_text(encoding="utf-8")
    assert "name: azd-sample" in azure_yaml_text
    assert "language: python" in azure_yaml_text
    assert "host: function" in azure_yaml_text


def test_scaffold_project_without_azd_excludes_azure_yaml(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "no-azd-sample",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_azd=False,
        ),
    )

    assert not (project_path / "azure.yaml").exists()


def test_describe_scaffold_project_reports_azd_when_enabled(tmp_path: Path) -> None:
    lines = describe_scaffold_project(
        "sample",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_azd=True,
        ),
    )

    assert "Azure Developer CLI (azd): enabled" in lines
    assert "  - azure.yaml" in lines


def test_describe_scaffold_project_excludes_azd_when_disabled(tmp_path: Path) -> None:
    lines = describe_scaffold_project(
        "sample",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_azd=False,
        ),
    )

    assert "Azure Developer CLI (azd): enabled" not in lines
    assert "  - azure.yaml" not in lines



def test_scaffold_project_with_db_generates_db_items(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "db-sample",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_db=True,
        ),
    )

    assert (project_path / "app/functions/db_items.py").exists()
    assert (project_path / "tests/test_db_items.py").exists()
    function_app_text = (project_path / "function_app.py").read_text(encoding="utf-8")
    assert "from app.functions.db_items import db_items_blueprint" in function_app_text
    assert "app.register_functions(db_items_blueprint)" in function_app_text
    pyproject_text = (project_path / "pyproject.toml").read_text(encoding="utf-8")
    assert "azure-functions-db[postgres]>=0.1.0" in pyproject_text
    local_settings = (project_path / "local.settings.json.example").read_text(encoding="utf-8")
    assert "DB_URL" in local_settings


def test_scaffold_project_without_db_excludes_db_items(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "no-db-sample",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_db=False,
        ),
    )

    assert not (project_path / "app/functions/db_items.py").exists()
    assert not (project_path / "tests/test_db_items.py").exists()
    function_app_text = (project_path / "function_app.py").read_text(encoding="utf-8")
    assert "db_items_blueprint" not in function_app_text
    pyproject_text = (project_path / "pyproject.toml").read_text(encoding="utf-8")
    assert "azure-functions-db" not in pyproject_text


def test_describe_scaffold_project_reports_db_when_enabled(tmp_path: Path) -> None:
    lines = describe_scaffold_project(
        "sample",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_db=True,
        ),
    )

    assert "Database: enabled" in lines
    assert "  - app/functions/db_items.py" in lines


def test_scaffold_project_renders_langgraph_template(tmp_path: Path) -> None:
    project_path = scaffold_project(
        "agent-sample",
        tmp_path,
        template_name="langgraph",
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
        ),
    )

    assert (project_path / "function_app.py").exists()
    assert (project_path / "host.json").exists()
    assert (project_path / "pyproject.toml").exists()
    assert (project_path / "app/graphs/echo_agent.py").exists()
    assert (project_path / "tests/test_echo_agent.py").exists()
    function_app_text = (project_path / "function_app.py").read_text(encoding="utf-8")
    assert "LangGraphApp" in function_app_text
    assert "lg_app.register" in function_app_text
    pyproject_text = (project_path / "pyproject.toml").read_text(encoding="utf-8")
    assert "azure-functions-langgraph>=0.5.0" in pyproject_text
    assert "langgraph>=0.2.0" in pyproject_text


