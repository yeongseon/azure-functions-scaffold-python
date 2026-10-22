from datetime import date
import json
from pathlib import Path
import subprocess

import pytest

from tools.dependency_audit_policy import classify_audit, run_audit
from tools.security_evidence import apply_bandit_policy, classify_bandit
from tools.security_report import Status

TODAY = date(2026, 10, 23)


def test_runtime_exception_requires_current_owned_exact_advisory() -> None:
    raw = json.dumps(
        {
            "dependencies": [
                {
                    "name": "example",
                    "version": "1",
                    "vulns": [
                        {"id": "CVE-2026-12345", "fix_versions": []},
                    ],
                }
            ]
        }
    )
    policy = {
        "schema_version": 1,
        "blocking": "all-known-runtime",
        "exceptions": [
            {
                "id": "CVE-2026-12345",
                "package": "example",
                "kind": "fix-not-available",
                "reason": "no patched release",
                "owner": "maintainer",
                "added": "2026-10-01",
                "expires": "2026-11-01",
            }
        ],
    }
    assert classify_audit(raw, 1, policy_raw=json.dumps(policy), today=TODAY).status == Status.PASS
    assert (
        classify_audit(raw, 1, policy_raw=json.dumps(policy), today=date(2026, 11, 2)).status
        == Status.FAIL
    )
    assert (
        classify_audit(
            raw.replace('"fix_versions": []', '"fix_versions": ["2"]'),
            1,
            policy_raw=json.dumps(policy),
            today=TODAY,
        ).status
        == Status.FAIL
    )
    assert (
        classify_audit(
            raw, 1, policy_raw=json.dumps(policy).replace('"owner": "maintainer",', ""), today=TODAY
        ).status
        == Status.TOOL_ERROR
    )


def test_static_exception_is_location_specific() -> None:
    raw = json.dumps(
        {
            "errors": [],
            "metrics": {"_totals": {"loc": 2}, "src/x.py": {}},
            "results": [
                {
                    "test_id": "B404",
                    "filename": "src/x.py",
                    "line_number": 1,
                    "issue_severity": "LOW",
                    "issue_confidence": "HIGH",
                }
            ],
        }
    )
    check = classify_bandit(raw, 1, floor=1)
    policy = json.dumps(
        {
            "schema_version": 1,
            "exceptions": [
                {
                    "id": "B404",
                    "file": "src/x.py",
                    "line": 1,
                    "kind": "reviewed-static",
                    "reason": "fixed shell-free process",
                    "owner": "maintainer",
                    "added": "2026-10-01",
                    "expires": "2026-11-01",
                }
            ],
        }
    )
    assert apply_bandit_policy(check, policy, TODAY).status == Status.PASS
    assert (
        apply_bandit_policy(check, policy.replace('"line": 1', '"line": 2'), TODAY).status
        == Status.FAIL
    )


@pytest.mark.parametrize("failure", [OSError("fake"), subprocess.TimeoutExpired("fake", 1)])
def test_auditor_execution_failure_is_tool_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
) -> None:
    (tmp_path / "example.dist-info").mkdir()

    def crash(*args: object, **kwargs: object) -> None:
        raise failure

    monkeypatch.setattr(subprocess, "run", crash)
    assert run_audit(tmp_path, tmp_path / "policy").status == Status.TOOL_ERROR


def test_candidate_installation_cannot_be_empty(tmp_path: Path) -> None:
    assert run_audit(tmp_path, tmp_path / "policy").status == Status.INCOMPLETE
