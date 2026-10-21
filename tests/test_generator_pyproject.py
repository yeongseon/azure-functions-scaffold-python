from __future__ import annotations

import tomllib

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator.pyproject import _compute_updated_pyproject_dependency


def test_dependency_is_added_to_main_dependency_list() -> None:
    content = '[project]\ndependencies = [\n  "azure-functions>=1.23.0",\n]\n'

    result = _compute_updated_pyproject_dependency(
        content,
        "azure-functions-durable>=1.2.9",
    )

    assert result == (
        '[project]\ndependencies = [\n  "azure-functions>=1.23.0",\n'
        '  "azure-functions-durable>=1.2.9",\n]\n'
    )


def test_existing_dependency_is_unchanged() -> None:
    content = '[project]\ndependencies = [\n  "azure-functions-durable>=1.2.9",\n]\n'

    result = _compute_updated_pyproject_dependency(
        content,
        "azure-functions-durable>=1.2.9",
    )

    assert result is None


def test_missing_dependency_list_is_rejected() -> None:
    with pytest.raises(ScaffoldError, match="project dependencies list was not found"):
        _compute_updated_pyproject_dependency(
            '[project]\nname = "sample"\n',
            "azure-functions-durable>=1.2.9",
        )


def test_dependency_edit_targets_project_table_not_an_earlier_tool_table() -> None:
    """Regression (#411): the helper searched for the first line exactly
    equal to "dependencies = [" without tracking which TOML table it
    belonged to. A valid pyproject.toml with [tool.hatch.envs.default]
    declared before [project] (both happen to have their own
    "dependencies = [" array) added the runtime dependency to the Hatch
    environment's dependency list instead, leaving [project].dependencies
    -- the actual runtime dependency table -- unchanged."""
    content = (
        "[tool.hatch.envs.default]\n"
        'dependencies = [\n  "pytest>=8",\n]\n\n'
        "[project]\n"
        'name = "sample"\n'
        'version = "0.1.0"\n'
        'dependencies = [\n  "azure-functions>=1.23",\n]\n'
    )

    result = _compute_updated_pyproject_dependency(content, "azure-functions-durable>=1.2.9")

    assert result is not None
    parsed = tomllib.loads(result)
    assert "azure-functions-durable>=1.2.9" in parsed["project"]["dependencies"]
    assert (
        "azure-functions-durable>=1.2.9"
        not in parsed["tool"]["hatch"]["envs"]["default"]["dependencies"]
    )
    assert parsed["tool"]["hatch"]["envs"]["default"]["dependencies"] == ["pytest>=8"]


def test_dependency_matching_text_outside_runtime_array_is_not_treated_as_present() -> None:
    """Regression (#411): the "already present" check was a global substring
    search over the raw file text, so a matching requirement string
    anywhere else in the file (a different table, a comment) made the
    helper skip adding it to [project].dependencies entirely."""
    content = (
        "[project]\n"
        'name = "sample"\n'
        'dependencies = [\n  "azure-functions>=1.23",\n]\n\n'
        "[tool.hatch.envs.default]\n"
        'dependencies = [\n  "azure-functions-durable>=1.2.9",\n]\n'
    )

    result = _compute_updated_pyproject_dependency(content, "azure-functions-durable>=1.2.9")

    assert result is not None
    parsed = tomllib.loads(result)
    assert "azure-functions-durable>=1.2.9" in parsed["project"]["dependencies"]


def test_invalid_toml_is_rejected() -> None:
    with pytest.raises(ScaffoldError, match="invalid TOML"):
        _compute_updated_pyproject_dependency(
            "[project\nname = sample",
            "azure-functions-durable>=1.2.9",
        )


def test_inline_single_line_dependency_array_is_rejected() -> None:
    """Regression (#411): the line-based editor only recognizes the
    multi-line "dependencies = [" ... "]" array shape. An inline
    single-line array is valid TOML but an unsupported edit shape here --
    it must be rejected explicitly rather than silently left unedited."""
    with pytest.raises(ScaffoldError, match="expected multi-line array format"):
        _compute_updated_pyproject_dependency(
            '[project]\nname = "sample"\ndependencies = ["azure-functions>=1.23"]\n',
            "azure-functions-durable>=1.2.9",
        )
