from contextlib import nullcontext
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from tools import verification_azure
from tools.verification import focused
from tools.verification_host import readiness
from tools.verification_process import run


@pytest.mark.parametrize("kind", ["text", "name", "version", "hash"])
def test_azure_rejects_unverified_wheels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    for name in ("function_app.py", "host.json", "pyproject.toml"):
        (tmp_path / name).touch()
    wheel = tmp_path / "candidate.whl"
    if kind == "text":
        wheel.write_text("not a wheel")
    else:
        with zipfile.ZipFile(wheel, "w") as archive:
            name = "other" if kind == "name" else "azure-functions-scaffold"
            version = "2" if kind == "version" else "1"
            archive.writestr("candidate.dist-info/METADATA", f"Name: {name}\nVersion: {version}\n")
    monkeypatch.setattr(verification_azure, "version", lambda name: "1")
    environment = {
        "E2E_SCAFFOLDED_DIR": str(tmp_path),
        "E2E_BASE_URL": "https://app.azurewebsites.net",
        "E2E_EXPECTED_VERSION": "1",
        "VERIFICATION_WHEEL": str(wheel),
    }
    assert verification_azure.preflight(environment)


def test_quality_failure_saves_redacted_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert (
        focused("check", [sys.executable, "-c", "print('password=CANARY'); raise SystemExit(7)"])
        == 7
    )
    summary = json.loads((tmp_path / "test-results/check/summary.json").read_text())
    assert summary["status"] == "FAIL" and summary["exit_code"] == 7
    assert "CANARY" not in (tmp_path / "test-results/check/logs/runner.log").read_text()


def test_timeout_cleans_separate_session_and_runs_cleanup(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    service = tmp_path / "service.py"
    service.write_text(
        "import signal,time,os\nfrom pathlib import Path\n"
        f"Path({str(tmp_path / 'pid')!r}).write_text(str(os.getpid()))\n"
        "def stop(*args):\n"
        f"    Path({str(tmp_path / 'cleaned')!r}).touch()\n"
        "    raise SystemExit(0)\n"
        "signal.signal(signal.SIGTERM, stop)\nwhile True: time.sleep(1)\n"
    )
    script = (
        f"import sys; sys.path.insert(0,{str(root)!r}); "
        "from pathlib import Path; from tools.verification_process import child; import time; "
        f"\nwith child([sys.executable,{str(service)!r}],"
        f"Path({str(tmp_path / 'service.log')!r})):\n"
        " while True: time.sleep(1)\n"
    )
    assert run([sys.executable, "-c", script], tmp_path / "runner.log", timeout=2) == 124
    assert (tmp_path / "cleaned").exists()
    pid = int((tmp_path / "pid").read_text())
    stat = Path(f"/proc/{pid}/stat")
    assert not stat.exists() or stat.read_text().rsplit(")", 1)[1].split()[0] == "Z"


def test_maintenance_does_not_create_hatch_environment(tmp_path: Path) -> None:
    data = tmp_path / "hatch"
    environment = {**os.environ, "HATCH_DATA_DIR": str(data), "CI": ""}
    environment.pop("VIRTUAL_ENV", None)
    result = subprocess.run(
        ["make", "doctor", "HATCH=false", f"MAINTENANCE_PYTHON={sys.base_prefix}/bin/python3.11"],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert "development environment not created" in result.stdout
    assert not data.exists() or not list(data.rglob("pyvenv.cfg"))


def test_readiness_retries_timeout_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts: list[int] = []

    def connect(*args: object, **kwargs: object) -> nullcontext[None]:
        attempts.append(1)
        if len(attempts) == 1:
            raise TimeoutError("not ready")
        return nullcontext()

    monkeypatch.setattr("tools.verification_host.socket.create_connection", connect)
    monkeypatch.setattr("tools.verification_host.time.sleep", lambda seconds: None)
    readiness((1234,))
    assert len(attempts) == 2
