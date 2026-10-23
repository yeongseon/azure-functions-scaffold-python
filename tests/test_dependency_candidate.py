from pathlib import Path
import subprocess

import pytest

from tools.dependency_audit_policy import run_audit
from tools.security_report import Status


def installed(root: Path, name: str, version: str) -> None:
    directory = root / f"{name}-{version}.dist-info"
    directory.mkdir(parents=True)
    (directory / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    )


@pytest.mark.parametrize(
    ("response", "code", "status"),
    [
        ('{"name":"idna","version":"3.11","vulns":[]}', 0, Status.PASS),
        (
            '{"name":"idna","version":"3.11","vulns":[{"id":"CVE-2026-12345","fix_versions":[]}]}',
            1,
            Status.FAIL,
        ),
        ('{"name":"idna","skip_reason":"not on PyPI"}', 0, Status.INCOMPLETE),
    ],
)
def test_unpublished_candidate_audits_only_exact_third_party_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response: str, code: int, status: Status
) -> None:
    # Given an unpublished first-party candidate and its resolved dependency.
    installed(tmp_path, "azure-functions-scaffold", "9999.0.0")
    installed(tmp_path, "idna", "3.11")
    policy = tmp_path / "policy.json"
    policy.write_text('{"schema_version":1,"blocking":"all-known-runtime","exceptions":[]}')

    def audit(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "--path" not in command
        assert "--no-deps" in command and "--disable-pip" in command
        requirements = Path(command[command.index("--requirement") + 1]).read_text()
        assert requirements == "idna==3.11\n"
        return subprocess.CompletedProcess(command, code, '{"dependencies":[' + response + "]}")

    monkeypatch.setattr(subprocess, "run", audit)
    monkeypatch.setattr("tools.dependency_audit_policy.version", lambda name: "2.10.1")
    # When the verified candidate is excluded from the audit.
    result = run_audit(
        tmp_path, policy, candidate_name="azure-functions-scaffold", candidate_version="9999.0.0"
    )
    # Then third-party findings/skips retain their blocking meaning.
    assert result.status == status


def test_candidate_identity_mismatch_blocks_before_audit(tmp_path: Path) -> None:
    # Given a different installed version.
    installed(tmp_path, "azure-functions-scaffold", "1.0")
    installed(tmp_path, "idna", "3.11")
    # When the requested candidate does not match.
    result = run_audit(
        tmp_path,
        tmp_path / "policy",
        candidate_name="azure-functions-scaffold",
        candidate_version="9999.0.0",
    )
    # Then no audit can certify it.
    assert result.status == Status.INCOMPLETE
