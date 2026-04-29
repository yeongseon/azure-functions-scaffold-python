# pyright: reportMissingImports=false
from __future__ import annotations

from pathlib import Path

import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options, list_templates


def _templates_with_generated_tests() -> list[str]:
    return [template.name for template in list_templates() if (template.root / "tests").is_dir()]


@pytest.mark.parametrize("template_name", _templates_with_generated_tests())
def test_generated_projects_include_pytest_pythonpath(tmp_path: Path, template_name: str) -> None:
    project_root = scaffold_project(
        project_name=f"{template_name}-pytest-pythonpath",
        destination=tmp_path,
        template_name=template_name,
        options=build_project_options(
            preset_name="standard",
            python_version="3.12",
            include_github_actions=False,
            initialize_git=False,
            include_openapi=False,
            include_validation=False,
            include_doctor=False,
        ),
    )

    generated_pyproject_text = (project_root / "pyproject.toml").read_text(encoding="utf-8")

    assert 'pythonpath = ["."]' in generated_pyproject_text
