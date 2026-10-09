from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "ci_required_gate.py"
WORKFLOW = SCRIPT.parents[1] / ".github" / "workflows" / "ci-test.yml"


def ci_required_needs() -> tuple[str, ...]:
    lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
    job_start = lines.index("  ci-required:")
    needs_start = lines.index("    needs:", job_start)
    needs: list[str] = []
    for line in lines[needs_start + 1 :]:
        if not line.startswith("      - "):
            break
        needs.append(line.removeprefix("      - "))
    return tuple(needs)


def evaluate(
    *,
    full_required: bool | str,
    docs_changed: bool | str,
    overrides: dict[str, str] | None = None,
) -> int:
    full_required_arg = (
        str(full_required).lower() if isinstance(full_required, bool) else full_required
    )
    docs_changed_arg = str(docs_changed).lower() if isinstance(docs_changed, bool) else docs_changed
    results = {
        job: {"result": "success" if full_required_arg == "true" else "skipped"}
        for job in ci_required_needs()
    }
    results["changes"] = {"result": "success"}
    results["docs-check"] = {"result": "success" if docs_changed_arg == "true" else "skipped"}
    for job, result in (overrides or {}).items():
        results[job] = {"result": result}
    completed = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            full_required_arg,
            docs_changed_arg,
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


@pytest.mark.parametrize("value", ["", "TRUE", "yes", "unknown"])
def test_invalid_full_required_output_fails(value: str) -> None:
    # Given: the classifier produced a missing or malformed boolean.
    # When: the required-check gate evaluates its outputs.
    # Then: the gate fails closed.
    assert evaluate(full_required=value, docs_changed=True) == 1


@pytest.mark.parametrize("value", ["", "TRUE", "yes", "unknown"])
def test_invalid_docs_changed_output_fails(value: str) -> None:
    # Given: the classifier produced a missing or malformed boolean.
    # When: the required-check gate evaluates its outputs.
    # Then: the gate fails closed.
    assert evaluate(full_required=True, docs_changed=value) == 1


def test_classifier_cannot_disable_all_ci() -> None:
    # Given: both classifier outputs say no checks are required.
    # When: the required-check gate evaluates the impossible state.
    # Then: the gate fails closed.
    assert evaluate(full_required=False, docs_changed=False) == 1


@pytest.mark.parametrize("result", ["failure", "skipped"])
def test_unknown_dependency_must_succeed(result: str) -> None:
    # Given: ci-required gains a dependency without an explicit skip policy.
    # When: that dependency does not succeed.
    # Then: the gate treats it as required and fails.
    assert (
        evaluate(
            full_required=True,
            docs_changed=False,
            overrides={"new-required-job": result},
        )
        == 1
    )
