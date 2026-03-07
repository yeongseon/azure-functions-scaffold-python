from __future__ import annotations

from pathlib import Path

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.models import TemplateContext
from azure_functions_scaffold.scaffolder import (
    _iter_template_files,
    _render_path,
    _slugify,
    build_template_context,
    resolve_target_dir,
    scaffold_project,
    validate_project_name,
)
from azure_functions_scaffold.template_registry import get_template, list_templates


def test_list_templates_returns_http_template() -> None:
    templates = list_templates()

    assert [template.name for template in templates] == ["http"]
    assert templates[0].root.is_dir()


def test_get_template_rejects_unknown_name() -> None:
    with pytest.raises(ScaffoldError, match="Unknown template"):
        get_template("timer")


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
    context = build_template_context("My API")

    assert context == TemplateContext(project_name="My API", project_slug="my-api")


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
    context = TemplateContext(project_name="Sample API", project_slug="sample-api")

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
