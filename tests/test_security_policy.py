from datetime import date
import json
from pathlib import Path

import pytest

from tools.dependency_audit_policy import classify_audit
from tools.security_evidence import classify_bandit, semgrep_evidence
from tools.security_exceptions import parse_exceptions
from tools.security_report import EvidenceError, Status, write_report

POLICY = '{"schema_version":1,"blocking":"all-known-runtime","exceptions":[]}'
TODAY = date(2026, 10, 23)


@pytest.mark.parametrize("raw", ["", "{}", "invalid"])
def test_missing_audit_output_cannot_pass(raw: str) -> None:
    assert classify_audit(raw, 0, policy_raw=POLICY, today=TODAY).status == Status.TOOL_ERROR


@pytest.mark.parametrize("dependencies", [[], [{"skip_reason": "not installed"}]])
def test_empty_or_skipped_audit_cannot_pass(dependencies: list[dict[str, str]]) -> None:
    raw = json.dumps({"dependencies": dependencies})
    assert classify_audit(raw, 0, policy_raw=POLICY, today=TODAY).status == Status.INCOMPLETE


@pytest.mark.parametrize("severity", ["LOW", "MEDIUM", "HIGH", "UNKNOWN"])
def test_all_runtime_advisories_block_without_leaking_descriptions(
    severity: str,
    tmp_path: Path,
) -> None:
    raw = json.dumps(
        {
            "dependencies": [
                {
                    "name": "example",
                    "version": "1",
                    "vulns": [
                        {
                            "id": "CVE-2026-12345",
                            "severity": severity,
                            "fix_versions": [],
                            "description": "CANARY_SECRET_do_not_export",
                        }
                    ],
                }
            ]
        }
    )
    check = classify_audit(raw, 1, policy_raw=POLICY, today=TODAY)
    assert check.status == Status.FAIL
    assert write_report([check], tmp_path) == 1
    assert "CANARY_SECRET" not in (tmp_path / "summary.json").read_text()


@pytest.mark.parametrize("days", [0, 91])
def test_exception_validity_is_bounded(days: int) -> None:
    from datetime import timedelta

    with pytest.raises(EvidenceError):
        parse_exceptions(
            [
                {
                    "id": "B404",
                    "file": "src/x.py",
                    "line": 1,
                    "kind": "reviewed-static",
                    "owner": "maintainer",
                    "reason": "fixed subprocess",
                    "added": TODAY.isoformat(),
                    "expires": (TODAY + timedelta(days=days)).isoformat(),
                }
            ],
            TODAY,
        )


@pytest.mark.parametrize(
    "raw,code,status",
    [
        ("", 2, Status.TOOL_ERROR),
        ('{"errors":[],"metrics":{"_totals":{"loc":0}},"results":[]}', 0, Status.INCOMPLETE),
        (
            '{"errors":[],"metrics":{"_totals":{"loc":1,"nosec":1},"x.py":{}},"results":[]}',
            0,
            Status.INCOMPLETE,
        ),
    ],
)
def test_static_scan_fails_closed(raw: str, code: int, status: Status) -> None:
    assert classify_bandit(raw, code, floor=1).status == status


@pytest.mark.parametrize(
    "outcome,status",
    [
        ("success", Status.INCOMPLETE),
        ("failure", Status.TOOL_ERROR),
        ("skipped", Status.INCOMPLETE),
    ],
)
def test_semgrep_action_counts_are_unknown(outcome: str, status: Status) -> None:
    check = semgrep_evidence(outcome)
    assert check.status == status
    assert check.counts == {}
