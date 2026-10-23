from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import shutil

import pytest
import yaml

from tools.lint_release_workflows import lint
from tools.verification import aggregate
from tools.verification_environment import clean
from tools.verification_evidence import Summary, collect
from tools.verification_manifest import TEMPLATES

ROOT = Path(__file__).resolve().parents[1]


def test_release_gate_and_pins() -> None:
    # Given the actual workflows, when linting, then release prerequisites remain intact.
    assert lint() == []


def test_removed_release_gate_fails(tmp_path: Path) -> None:
    # Given a publish workflow missing Azure certification.
    shutil.copytree(ROOT / ".github", tmp_path / ".github")
    workflow = tmp_path / ".github/workflows/publish-pypi.yml"
    workflow.write_text(
        workflow.read_text().replace("[build, lib-tests, azure-e2e]", "[build, lib-tests]")
    )
    # When checking release wiring, then it fails closed.
    assert any("publish must require" in error for error in lint(tmp_path))


def test_clean_preserves_environment_and_user_files(tmp_path: Path) -> None:
    # Given generated evidence, a developer environment and user-owned files.
    for name in ("test-results", "dist", ".venv", "personal"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "keep").write_text("content")
    # When cleaning generated artifacts.
    clean(tmp_path)
    # Then environments and unrelated files survive.
    assert (tmp_path / ".venv/keep").read_text() == "content"
    assert (tmp_path / "personal/keep").read_text() == "content"
    assert not (tmp_path / "test-results").exists()


@pytest.mark.parametrize("status", ["FAIL", "INCOMPLETE", "NOT_APPLICABLE"])
def test_required_lane_cannot_disappear(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    # Given one successful lane and one required unproven lane.
    monkeypatch.chdir(tmp_path)
    passed = Summary(1, "generator", ("pytest",), 1, 1, 0, 0, "PASS", 0)
    missing = replace(passed, lane="host", status="INCOMPLETE")
    if status == "FAIL":
        missing = replace(missing, status="FAIL")
    elif status == "NOT_APPLICABLE":
        missing = replace(missing, status="NOT_APPLICABLE")
    # When aggregating full local verification, then it cannot pass.
    assert aggregate("verify", [passed, missing]) != 0
    assert (
        json.loads((tmp_path / "test-results/verify/summary.json").read_text())["status"] != "PASS"
    )


def test_forged_junit_counts_fail(tmp_path: Path) -> None:
    # Given counters that hide a skipped case, when collecting, then reject evidence.
    (tmp_path / "junit.xml").write_text(
        '<testsuite tests="1" skipped="0"><testcase><skipped/></testcase></testsuite>'
    )
    with pytest.raises(ValueError, match="counter mismatch"):
        collect(tmp_path, ["pytest"], 0)


def test_ci_matrix_and_required_names_are_preserved() -> None:
    # Given the shared manifest and workflow, when inspecting jobs, then retain all versions.
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci-test.yml").read_text())
    assert workflow["jobs"]["test"]["strategy"]["matrix"]["python-version"] == [
        "3.11",
        "3.12",
        "3.13",
        "3.14",
    ]
    assert workflow["jobs"]["generated-host-smoke"]["name"] == (
        "Generated HTTP app host smoke (Py ${{ matrix.python-version }})"
    )
    assert len(TEMPLATES) == 10


def test_azure_phases_require_independent_execution(tmp_path: Path) -> None:
    # Given generator-only success and a remote phase with no executed tests.
    passed = Summary(1, "azure-generation", ("pytest",), 2, 2, 0, 0, "PASS", 0)
    missing = collect(tmp_path, ["pytest", "-k", "not scaffolded"], 5)
    # When combining proof, then generator success cannot certify deployment.
    assert passed.status == "PASS"
    assert missing.status != "PASS"
