"""Regression guard for the fleet-wide workflow pin-hygiene lint.

Exercises tools/lint_workflow_pins.py against this repo (must be clean) and
against synthetic drift (must be caught). Keeps the vendored lint honest.
"""

from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path
import re
import string
import subprocess
import sys
from typing import Any

import yaml

from azure_functions_scaffold.template_registry import TEMPLATE_SPECS

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LINT_PATH = _REPO_ROOT / "tools" / "lint_workflow_pins.py"
_SMOKE_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "templates-smoke.yml"
_LANE = "tests/test_generated_projects.py"

_spec = importlib.util.spec_from_file_location("lint_workflow_pins", _LINT_PATH)
assert _spec and _spec.loader
lint_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint_mod)


def test_repo_workflows_are_pin_clean() -> None:
    """Every committed workflow must satisfy pin-hygiene."""
    assert lint_mod.lint() == []


def test_workflow_path_filters_reference_existing_paths() -> None:
    # Given: all path-filter entries declared by committed workflows.
    workflows = (_REPO_ROOT / ".github" / "workflows").glob("*.yml")
    filters: list[tuple[Path, str]] = []
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        for block in re.findall(r"(?m)^\s+paths:\s*\n((?:\s+-\s+.+\n)+)", text):
            filters.extend(
                (workflow, line.split("-", 1)[1].strip().strip("\"'"))
                for line in block.splitlines()
            )

    # When: each glob is reduced to its existing, non-pattern prefix.
    missing = []
    for workflow, path_filter in filters:
        anchor = re.split(r"[*?[]", path_filter.lstrip("!"), maxsplit=1)[0].rstrip("/")
        if not (_REPO_ROOT / anchor).exists():
            missing.append(f"{workflow.name}: {path_filter}")

    # Then: no filter is anchored to a removed path.
    assert missing == []


def test_template_smoke_workflow_covers_inputs_and_registry() -> None:
    workflow = yaml.safe_load(_SMOKE_WORKFLOW.read_text(encoding="utf-8"))
    required_filters = (
        "src/azure_functions_scaffold/templates/**",
        "src/azure_functions_scaffold/template_registry.py",
        "src/azure_functions_scaffold/scaffolder.py",
        "src/azure_functions_scaffold/generator/**",
        _LANE,
        "pyproject.toml",
        "*.lock",
        ".github/workflows/templates-smoke.yml",
    )
    triggers = workflow[True]
    assert tuple(triggers["pull_request"]["paths"]) == required_filters
    assert tuple(triggers["push"]["paths"]) == required_filters
    assert set(workflow["jobs"]["scaffold-and-validate"]["strategy"]["matrix"]["template"]) == {
        template.name for template in TEMPLATE_SPECS
    }


def test_template_smoke_workflow_tolerates_no_exit_status() -> None:
    workflow = yaml.safe_load(_SMOKE_WORKFLOW.read_text(encoding="utf-8"))
    steps = [step for job in workflow["jobs"].values() for step in job["steps"]]
    scripts = "\n".join(step.get("run", "") for step in steps)

    # Then: no exit-5 tolerance, no swallowed failure, no step or job allowed to fail.
    assert [word for word in ("-ne 5", "|| true", "set +e") if word in scripts] == []
    assert not [job for job in workflow["jobs"].values() if "continue-on-error" in job]
    assert not [step for step in steps if "continue-on-error" in step]


def _lane_node_ids(job: dict[str, Any]) -> set[str]:
    """Node ids a job's pytest steps select, with ``${MATRIX_KEY}`` expanded per matrix cell."""
    matrix = job.get("strategy", {}).get("matrix", {})
    cells = [
        {key.upper().replace("-", "_"): value for key, value in zip(matrix, values, strict=True)}
        for values in itertools.product(*matrix.values())
    ]
    scripts = "\n".join(step.get("run", "") for step in job["steps"])
    nodes = re.findall(rf'{re.escape(_LANE)}::[^"\s]+', scripts)
    return {string.Template(node).substitute(cell) for node in nodes for cell in cells}


def test_template_smoke_cells_select_existing_lane_node_ids() -> None:
    workflow = yaml.safe_load(_SMOKE_WORKFLOW.read_text(encoding="utf-8"))
    pytest = [sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "no:cacheprovider"]
    listing = subprocess.run(
        [*pytest, "--collect-only", "-q", _LANE],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert listing.returncode == 0, listing.stdout + listing.stderr
    collected = {line for line in listing.stdout.splitlines() if "::" in line}

    for job_id, job in workflow["jobs"].items():
        selected = _lane_node_ids(job)
        assert selected, f"{job_id} selects no node id of {_LANE}"
        assert selected <= collected, (
            f"{job_id} selects unknown ids: {sorted(selected - collected)}"
        )


def test_sha_with_comment_passes() -> None:
    text = "      - uses: actions/checkout@" + "a" * 40 + " # v7.0.1\n"
    assert lint_mod.check_pin_hygiene(text, "fake.yml") == []


def test_local_composite_action_passes() -> None:
    text = "      - uses: ./.github/actions/setup\n"
    assert lint_mod.check_pin_hygiene(text, "fake.yml") == []


def test_documented_exception_passes() -> None:
    text = "      - uses: pypa/gh-action-pypi-publish@release/v1 # pin-exempt: trusted publisher\n"
    assert lint_mod.check_pin_hygiene(text, "fake.yml") == []


def test_unpinned_tag_fails() -> None:
    text = "      - uses: actions/checkout@v4\n"
    errors = lint_mod.check_pin_hygiene(text, "fake.yml")
    assert errors and "not a 40-hex" in errors[0]


def test_branch_ref_without_exemption_fails() -> None:
    text = "      - uses: pypa/gh-action-pypi-publish@release/v1\n"
    errors = lint_mod.check_pin_hygiene(text, "fake.yml")
    assert errors and "not a 40-hex" in errors[0]


def test_sha_without_version_comment_fails() -> None:
    text = "      - uses: actions/checkout@" + "b" * 40 + "\n"
    errors = lint_mod.check_pin_hygiene(text, "fake.yml")
    assert errors and "missing the trailing" in errors[0]


def test_pin_exempt_marker_requires_a_reason() -> None:
    # A bare "pin-exempt" with no reason must NOT satisfy the exemption.
    text = "      - uses: pypa/gh-action-pypi-publish@release/v1 # pin-exempt:\n"
    errors = lint_mod.check_pin_hygiene(text, "fake.yml")
    assert errors and "not a 40-hex" in errors[0]
