from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools.verification_manifest import REQUIRED_DIAGNOSTICS


@pytest.mark.parametrize(
    ("body", "code", "status"),
    [
        ('<testcase name="works"/>', 0, "PASS"),
        ("", 5, "FAIL"),
        ("", 0, "INCOMPLETE"),
        ("<testcase><skipped/></testcase>", 0, "INCOMPLETE"),
        ("<testcase/><testcase><skipped/></testcase>", 0, "INCOMPLETE"),
        ("<testcase><failure/></testcase>", 1, "FAIL"),
        ("<testcase/>", 5, "FAIL"),
    ],
)
def test_required_pytest_execution(tmp_path: Path, body: str, code: int, status: str) -> None:
    # Given a generated suite's actual JUnit cases.
    (tmp_path / "junit.xml").write_text(f"<testsuites><testsuite>{body}</testsuite></testsuites>")
    policy = importlib.import_module("tools.verification_evidence")
    # When classifying its process and execution evidence.
    result = policy.collect(tmp_path, ["pytest"], code)
    # Then no exit-5, empty or skipped suite passes.
    assert result.status == status
    assert (result.exit_code == 0) == (status == "PASS")


@pytest.mark.parametrize("empty", [False, True])
def test_real_generated_pytest_gate(tmp_path: Path, empty: bool) -> None:
    # Given a real test directory outside the checkout.
    (tmp_path / "tests").mkdir()
    if not empty:
        (tmp_path / "tests/test_example.py").write_text(
            "def test_example():\n    assert 2 + 2 == 4\n"
        )
    runner = importlib.import_module("tools.verification_generated")
    # When running actual pytest with the shared smoke gate.
    result = runner.test_project(tmp_path, Path(sys.executable), tmp_path / "evidence")
    # Then positive execution passes and exit 5 fails.
    assert (result.status == "PASS") == (not empty)
    assert result.exit_code == (5 if empty else 0)


@pytest.mark.parametrize(
    ("rule", "severity", "finding", "code", "expected"),
    [
        ("check_venv", "warning", "warn", 1, "ADVISORY"),
        ("check_host_json", "error", "fail", 1, "REQUIRED_FINDING"),
        ("check_host_json", "info", "pass", 0, "PASS"),
        ("check_venv", "warning", "warn", 2, "CLI_ERROR"),
        ("check_venv", "warning", "warn", 139, "CRASH"),
    ],
)
def test_machine_diagnostics_policy(
    rule: str, severity: str, finding: str, code: int, expected: str
) -> None:
    # Given machine-readable Doctor output, not human summary prose.
    document = json.dumps(
        {
            "results": [
                {
                    "category": "structure",
                    "items": [
                        {"rule_id": rule, "severity": severity, "status": finding},
                        *[
                            {"rule_id": required, "severity": "info", "status": "pass"}
                            for required in REQUIRED_DIAGNOSTICS
                            if required != rule
                        ],
                    ],
                }
            ]
        }
    )
    policy = importlib.import_module("tools.verification_diagnostics")
    # When applying the explicit required-rule policy, then classify narrowly.
    assert policy.classify(document, code).category == expected


def test_crash_without_json_fails() -> None:
    # Given a traceback instead of JSON, when classifying, then it is not advisory.
    policy = importlib.import_module("tools.verification_diagnostics")
    assert policy.classify("Traceback: boom", 1).category == "CRASH"


@pytest.mark.parametrize(
    "value",
    [
        "AccountKey=CANARYsecret;",
        "token=CANARYsecret",
        "code=CANARYsecret&x=1",
        "Authorization: Bearer CANARYsecret",
        '"connection_string": "CANARYsecret"',
        "https://user:CANARYsecret@example.com",
        "x-functions-key: CANARYsecret",
    ],
)
def test_redaction_surfaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], value: str
) -> None:
    # Given secrets in commands, logs and summary metadata.
    policy = importlib.import_module("tools.verification_evidence")
    (tmp_path / "runner.log").write_text(value)
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "job-summary"))
    summary = policy.Summary(1, "canary", (value,), 1, 1, 0, 0, "PASS", 0, reason=value)
    # When saving and publishing evidence.
    policy.publish(policy.save(tmp_path, summary))
    # Then every persisted and displayed surface is redacted.
    assert "CANARYsecret" not in capsys.readouterr().out
    assert all("CANARYsecret" not in path.read_text() for path in tmp_path.iterdir())


def test_unconfigured_azure_fails_before_pytest(tmp_path: Path) -> None:
    # Given no deployed input or endpoint.
    runner = importlib.import_module("tools.verification_azure")
    # When preflighting, then missing input prevents test execution.
    assert runner.preflight({})


def test_exit_five_mutation_is_detected(tmp_path: Path) -> None:
    # Given the historical mutation: a wrapper turns pytest exit 5 into success.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 5
    policy = importlib.import_module("tools.verification_evidence")
    # When the process falsely reports success but has no execution evidence.
    summary = policy.collect(tmp_path, ["pytest"], 0)
    # Then the gate still rejects the false green.
    assert summary.status == "INCOMPLETE"
    assert summary.exit_code != 0
