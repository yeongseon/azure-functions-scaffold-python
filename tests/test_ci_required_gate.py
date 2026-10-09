from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "ci_required_gate.py"
MATRIX_JOBS = (
    "quality",
    "test",
    "minimum-dependencies",
    "artifact-build",
    "artifact-python310-negative",
    "artifact-python311",
    "generated-host-smoke",
)


def evaluate(
    *, full_required: bool, docs_changed: bool, overrides: dict[str, str] | None = None
) -> int:
    results = {job: {"result": "success" if full_required else "skipped"} for job in MATRIX_JOBS}
    results["changes"] = {"result": "success"}
    results["docs-check"] = {"result": "success" if docs_changed else "skipped"}
    for job, result in (overrides or {}).items():
        results[job] = {"result": result}
    completed = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            str(full_required).lower(),
            str(docs_changed).lower(),
        ],
        input=json.dumps(results),
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode


@pytest.mark.parametrize(
    ("full_required", "docs_changed"),
    [(False, True), (True, True), (True, False)],
)
def test_expected_results_pass(full_required: bool, docs_changed: bool) -> None:
    assert evaluate(full_required=full_required, docs_changed=docs_changed) == 0


@pytest.mark.parametrize(
    ("full_required", "docs_changed", "overrides"),
    [
        (False, True, {"docs-check": "failure"}),
        (True, False, {"test": "skipped"}),
        (True, False, {"test": "failure"}),
        (True, False, {"changes": "failure"}),
        (True, False, {"generated-host-smoke": "cancelled"}),
    ],
)
def test_unexpected_results_fail(
    full_required: bool, docs_changed: bool, overrides: dict[str, str]
) -> None:
    assert (
        evaluate(
            full_required=full_required,
            docs_changed=docs_changed,
            overrides=overrides,
        )
        == 1
    )
