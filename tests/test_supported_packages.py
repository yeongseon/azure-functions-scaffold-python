"""Tests for the centralized supported-package version catalog (issue #195)."""

from __future__ import annotations

from pathlib import Path
import re

import pytest

from azure_functions_scaffold.packages import SUPPORTED_PACKAGES, requirement
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_ROOT = _REPO_ROOT / "src" / "azure_functions_scaffold" / "templates"

# Bare toolkit pins like `"azure-functions-openapi>=0.17.0"` must not survive in
# the templates — they have to flow through the catalog instead.
_BARE_PIN = re.compile(r'"azure-functions[a-z-]*>=')


def test_requirement_builds_full_specifier() -> None:
    assert requirement("azure-functions") == "azure-functions>=1.23.0"
    assert requirement("azure-functions-doctor") == "azure-functions-doctor>=0.16.0"


def test_templates_have_no_hardcoded_toolkit_pins() -> None:
    offenders: list[str] = []
    for template_pyproject in _TEMPLATES_ROOT.glob("*/pyproject.toml.j2"):
        for lineno, line in enumerate(
            template_pyproject.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if _BARE_PIN.search(line):
                offenders.append(f"{template_pyproject.name}:{lineno}: {line.strip()}")
    assert offenders == [], (
        "Template pyproject files must reference SUPPORTED_PACKAGES, not hardcoded "
        f"toolkit pins:\n{chr(10).join(offenders)}"
    )


def test_templates_reference_catalog() -> None:
    # Every template pyproject that pins a toolkit package must do so via the
    # `supported_packages` render variable.
    for template_pyproject in _TEMPLATES_ROOT.glob("*/pyproject.toml.j2"):
        text = template_pyproject.read_text(encoding="utf-8")
        if "azure-functions" in text:
            assert "supported_packages[" in text, (
                f"{template_pyproject} pins toolkit packages but does not use the catalog"
            )


def test_root_pyproject_floors_match_catalog() -> None:
    root_pyproject = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for name, spec in SUPPORTED_PACKAGES.items():
        # Not every catalog entry is a smoke-test floor of the root project
        # (durable/langgraph are template-only), but any that appears must agree.
        pin = re.search(rf'"{re.escape(name)}(>=[^"]*)"', root_pyproject)
        if pin is not None:
            assert pin.group(1) == spec, (
                f"Root pyproject pins {name}{pin.group(1)} but catalog says {name}{spec}"
            )


@pytest.mark.parametrize(
    ("template_name", "expected"),
    [
        ("http", ("azure-functions", "azure-functions-logging", "azure-functions-openapi")),
        ("durable", ("azure-functions", "azure-functions-durable")),
    ],
)
def test_rendered_pyproject_uses_catalog_specs(
    tmp_path: Path, template_name: str, expected: tuple[str, ...]
) -> None:
    options = build_project_options(
        preset_name="standard",
        python_version="3.11",
        include_github_actions=False,
        initialize_git=False,
        include_openapi=True,
        include_validation=True,
        include_doctor=True,
    )
    project_path = scaffold_project(
        "sample", tmp_path, template_name=template_name, options=options
    )
    pyproject = (project_path / "pyproject.toml").read_text(encoding="utf-8")
    for name in expected:
        assert requirement(name) in pyproject, (
            f"{template_name} pyproject missing catalog pin {requirement(name)}"
        )
