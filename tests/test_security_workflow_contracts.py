from pathlib import Path
import subprocess


def test_semgrep_evidence_is_always_collected_without_overriding_action_gate(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            "make",
            "security-semgrep",
            "SECURITY_RUN=python3.11",
            "SEMGREP_OUTCOME=success",
            f"SECURITY_OUTPUT={tmp_path}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status": "INCOMPLETE"' in (tmp_path / "semgrep/summary.json").read_text()
    workflow = Path(".github/workflows/security.yml").read_text()
    assert "if: always()\n        env:\n          OUTCOME:" in workflow
    assert "make security-semgrep" in workflow
    assert "continue-on-error" not in workflow


def test_release_audit_uses_make_and_verified_candidate_version() -> None:
    workflow = Path(".github/workflows/publish-pypi.yml").read_text()
    assert "make security-audit" in workflow
    assert 'CANDIDATE_VERSION="$candidate_version"' in workflow
    assert ".dist-info/METADATA" in workflow
    assert "needs: [build, lib-tests, azure-e2e, runtime-dependency-audit]" in workflow
