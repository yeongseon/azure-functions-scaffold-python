from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import TemplateContext
from azure_functions_scaffold.scaffolder import (
    _initialize_git_repository,
    _iter_template_files,
    _render_path,
    _slugify,
    build_template_context,
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

    assert [template.name for template in templates] == ["http", "timer"]
    assert all(template.root.is_dir() for template in templates)


def test_get_template_rejects_unknown_name() -> None:
    with pytest.raises(ScaffoldError, match="Unknown template"):
        get_template("queue")


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
    ["", "   ", ".", "..", "foo/bar", "foo\\bar", "-name"],
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
    context = build_template_context("My API", options)

    assert context == TemplateContext(
        project_name="My API",
        project_slug="my-api",
        python_version="3.10",
        python_upper_bound="3.11",
        preset_name="standard",
        include_github_actions=False,
        initialize_git=False,
        include_ruff=True,
        include_mypy=False,
        include_pytest=True,
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

    with pytest.raises(ScaffoldError, match="Target directory already exists"):
        scaffold_project("sample", tmp_path)


def test_scaffold_project_renders_template_option(tmp_path: Path) -> None:
    project_path = scaffold_project("sample", tmp_path, template_name="http")

    assert project_path == tmp_path / "sample"
    assert (project_path / "README.md").exists()


def test_scaffold_project_renders_timer_template_option(tmp_path: Path) -> None:
    project_path = scaffold_project("sample-job", tmp_path, template_name="timer")

    assert project_path == tmp_path / "sample-job"
    assert (project_path / "app/functions/timer.py").exists()
    assert (project_path / "tests/test_timer.py").exists()
    function_app_text = (project_path / "function_app.py").read_text(encoding="utf-8")
    assert "from app.functions.timer import timer_blueprint" in function_app_text


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
