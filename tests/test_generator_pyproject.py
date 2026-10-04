from __future__ import annotations

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
