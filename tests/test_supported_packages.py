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

# Bare toolkit pins like `"azure-functions-openapi>=0.21.0"` must not survive in
# the templates — they have to flow through the catalog instead.
_BARE_PIN = re.compile(r'"azure-functions[a-z-]*>=')


def test_requirement_builds_full_specifier() -> None:
    assert requirement("azure-functions") == "azure-functions>=1.23.0,<2.0.0"
    assert requirement("azure-functions-doctor") == "azure-functions-doctor>=0.19.0"


def test_templates_have_no_hardcoded_toolkit_pins() -> None:
    offenders: list[str] = []
    for template_pyproject in sorted(_TEMPLATES_ROOT.glob("*/pyproject.toml.j2")):
        for lineno, line in enumerate(
            template_pyproject.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if _BARE_PIN.search(line):
                offender = template_pyproject.relative_to(_REPO_ROOT).as_posix()
                offenders.append(f"{offender}:{lineno}: {line.strip()}")
    assert offenders == [], (
        "Template pyproject files must reference SUPPORTED_PACKAGES, not hardcoded "
        f"toolkit pins:\n{chr(10).join(offenders)}"
    )


def test_templates_reference_catalog() -> None:
    # Every template pyproject that pins a toolkit package must do so via the
    # `supported_packages` render variable.
    for template_pyproject in sorted(_TEMPLATES_ROOT.glob("*/pyproject.toml.j2")):
        text = template_pyproject.read_text(encoding="utf-8")
        if "azure-functions" in text:
            rel = template_pyproject.relative_to(_REPO_ROOT).as_posix()
            assert "supported_packages[" in text, (
                f"{rel} pins toolkit packages but does not use the catalog"
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


def test_requirement_unknown_name_raises_descriptive_error() -> None:
    with pytest.raises(KeyError) as excinfo:
        requirement("not-a-real-package")
    message = str(excinfo.value)
    assert "not-a-real-package" in message
    # The error lists the valid keys so callers can self-correct.
    assert "azure-functions" in message


# --- constraints-min.txt (CI "minimum" resolution axis) coverage guard -------
#
# `constraints-min.txt` pins each direct declared dependency to a low version so
# the minimum-resolution CI axis (ci-test.yml: `pip install -c constraints-min
# .txt -e .[dev]`) catches compatibility breaks at the declared floor. The
# sibling toolkit floors are declared in three places that must stay coherent:
#
#   1. `SUPPORTED_PACKAGES` (packages.py)      -> the catalog templates render
#   2. `[project.optional-dependencies].dev`   -> the scaffold's own smoke-test
#      floors (only the http-template siblings, since test_template_smoke.py
#      builds and runs the http template exclusively)
#   3. `constraints-min.txt`                   -> the minimum-resolution axis
#
# (1)<->(2) and (1)<->templates are already guarded above. This guards (2)<->(3):
# the minimum axis must cover EXACTLY the same sibling set as the dev extras and
# must never resolve BELOW a declared floor.

_SIBLING_FLOOR_RE = re.compile(r'"(azure-functions-[a-z-]+)>=([0-9][0-9.]*)"')
_CONSTRAINT_PIN_RE = re.compile(r"^(azure-functions-[a-z-]+)==([0-9][0-9.]*)", re.MULTILINE)


def _version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def test_constraints_min_covers_declared_sibling_floors() -> None:
    """The minimum-resolution axis must cover the same siblings as the dev extras.

    Completeness: every `azure-functions-*` sibling pinned as a smoke-test floor
    in the root `[dev]` extras must also appear in `constraints-min.txt`, and
    vice versa. This is the completeness half of issue #256 — a dev-extra floor
    that is missing from the minimum axis (or an orphaned constraint pin) is a
    silent coverage gap.
    """
    pyproject = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    constraints = (_REPO_ROOT / "constraints-min.txt").read_text(encoding="utf-8")

    dev_floor_siblings = {name for name, _ in _SIBLING_FLOOR_RE.findall(pyproject)}
    constraint_siblings = {name for name, _ in _CONSTRAINT_PIN_RE.findall(constraints)}

    assert dev_floor_siblings, "expected sibling floors in the [dev] extras"
    assert dev_floor_siblings == constraint_siblings, (
        "constraints-min.txt sibling coverage drifted from the [dev] extras.\n"
        f"  in [dev] but not constraints-min: {sorted(dev_floor_siblings - constraint_siblings)}\n"
        f"  in constraints-min but not [dev]: {sorted(constraint_siblings - dev_floor_siblings)}"
    )


def test_constraints_min_pins_are_at_or_above_declared_floors() -> None:
    """The minimum axis must never resolve a sibling BELOW its declared floor.

    Consistency: each `constraints-min.txt` sibling pin must be >= the lower
    bound declared in the root `[dev]` extras. A constraint pin below the floor
    would let CI's "minimum" axis test a version the package no longer claims to
    support; a floor raised above the pin (dependabot bump drift) is caught here
    too. This is the consistency half of issue #256.
    """
    pyproject = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    constraints = (_REPO_ROOT / "constraints-min.txt").read_text(encoding="utf-8")

    floors = {name: ver for name, ver in _SIBLING_FLOOR_RE.findall(pyproject)}
    pins = {name: ver for name, ver in _CONSTRAINT_PIN_RE.findall(constraints)}

    for name, floor in floors.items():
        assert name in pins, (
            f"{name} declared as a [dev] floor but not pinned in constraints-min.txt"
        )
        assert _version_tuple(pins[name]) >= _version_tuple(floor), (
            f"constraints-min.txt pins {name}=={pins[name]} which is BELOW the "
            f"declared [dev] floor {name}>={floor}"
        )
