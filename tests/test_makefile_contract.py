"""Contract of the Makefile targets that set up and check a checkout.

``make -n`` prints recipes without running them, so most cases need no network, Hatch or virtual
environment. The ``doctor`` cases run in an empty directory to prove it creates nothing, and the
bootstrap case runs ``check-all`` against stub ``pip`` and ``hatch`` programs to count real calls.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import tomllib

import pytest

ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = ROOT / "Makefile"
_HATCH = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["hatch"]
HATCH_SCRIPTS = {name: str(cmd) for name, cmd in _HATCH["envs"]["default"]["scripts"].items()}


def make(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    command = ["make", "--no-print-directory", "-f", str(MAKEFILE), *args]
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


def mypy_runs(commands: str) -> int:
    """Count mypy runs in ``commands``, expanding ``hatch run <script>`` from pyproject.toml."""
    nested = (HATCH_SCRIPTS.get(name, "") for name in re.findall(r"hatch run ([\w-]+)", commands))
    return commands.count("mypy") + sum(mypy_runs(script) for script in nested)


def test_check_runs_the_type_check_once() -> None:
    assert mypy_runs(make("-n", "check").stdout) == 1


@pytest.mark.parametrize("target", ["check", "check-all", "test"])
def test_routine_targets_never_upgrade_pip(target: str) -> None:
    assert "upgrade" not in make("-n", target).stdout


def test_makefile_never_upgrades_pip() -> None:
    # Also covers `docs`, which `make -n` would run for real: its recipe line contains $(MAKE).
    assert "--upgrade" not in MAKEFILE.read_text(encoding="utf-8")


def test_bootstrap_installs_hatch_once_and_only_while_it_is_missing(tmp_path: Path) -> None:
    venv, calls = tmp_path / "venv", tmp_path / "pip-calls"
    pip = venv / "bin" / "pip"  # records its arguments, then "installs" a no-op hatch
    pip.parent.mkdir(parents=True)
    pip.write_text(
        f"#!/bin/sh\necho \"$@\" >> {calls}\nprintf '#!/bin/sh\\n' > {venv}/bin/hatch\n"
        f"chmod +x {venv}/bin/hatch\n",
        encoding="utf-8",
    )
    pip.chmod(0o755)

    for _ in range(2):
        assert make("check-all", f"VENV_DIR={venv}").returncode == 0

    (call,) = calls.read_text(encoding="utf-8").splitlines()  # one call across both runs
    assert call.split()[0] == "install"
    assert call.split()[-1] == "hatch"
    assert "--upgrade" not in call


def test_doctor_fails_for_a_missing_tool_and_installs_nothing(tmp_path: Path) -> None:
    result = make("doctor", "REQUIRED_TOOLS=nonexistent", cwd=tmp_path)

    assert result.returncode != 0
    assert "MISSING  nonexistent" in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_doctor_passes_when_only_optional_tools_are_absent(tmp_path: Path) -> None:
    result = make(
        "doctor",
        f"PYTHON={sys.executable}",
        f"REQUIRED_TOOLS={sys.executable} sh",
        "OPTIONAL_TOOLS=nonexistent",
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert "absent   nonexistent" in result.stdout


def test_doctor_rejects_an_interpreter_older_than_python_311(tmp_path: Path) -> None:
    # Runs the Makefile's own version probe under a real interpreter that reports 3.10.
    old = tmp_path / "python3.10"
    probe = "import sys; sys.version_info = (3, 10, 0); exec(sys.argv[1])"
    old.write_text(f'#!/bin/sh\nexec "{sys.executable}" -c "{probe}" "$2"\n', encoding="utf-8")
    old.chmod(0o755)

    result = make("doctor", f"PYTHON={old}", f"REQUIRED_TOOLS={old}", cwd=tmp_path)

    assert result.returncode != 0
    assert f"TOO OLD  {old}" in result.stdout


def test_install_ci_installs_into_the_selected_interpreter() -> None:
    out = make("-n", "install-ci", "PYTHON=python3.12").stdout

    assert 'python3.12 -m pip install -e ".[dev,docs]"' in out
    assert "hatch" not in out
