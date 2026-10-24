"""Regression check for the local/Azure E2E pytest entrypoint (#414).

``make e2e-local`` and ``make e2e-azure`` both run the Hatch ``e2e-azure``
script, which selects tests with ``-m e2e``. If the ``e2e`` marker is ever
removed from the tests in ``tests/e2e/`` (or the marker expression drifts),
the entrypoint silently selects zero tests instead of failing loudly.

The same entrypoint must also fail, never skip, when a required input
(``E2E_BASE_URL`` / ``E2E_SCAFFOLDED_DIR``) is missing (#448), otherwise a
misconfigured run reports success without exercising anything.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
E2E_INPUTS = ("E2E_BASE_URL", "E2E_SCAFFOLDED_DIR")


def test_e2e_marker_entrypoint_selects_at_least_one_test() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "e2e",
            "-o",
            "addopts=",
            "tests/e2e/",
            "--collect-only",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no tests collected" not in result.stdout.lower()
    assert "3 items" in result.stdout


def test_default_suite_excludes_e2e_tests_regardless_of_env() -> None:
    env_without_url = dict(os.environ)
    env_without_url.pop("E2E_BASE_URL", None)
    result_without_url = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e/", "--collect-only", "--no-cov"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env_without_url,
    )
    assert "3 deselected" in result_without_url.stdout

    env_with_url = dict(env_without_url)
    env_with_url["E2E_BASE_URL"] = "http://localhost:7071"
    result_with_url = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e/", "--collect-only", "--no-cov"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env_with_url,
    )
    assert "3 deselected" in result_with_url.stdout


def _run_e2e(*selection: str, **inputs: str) -> tuple[int, str]:
    """Run ``tests/e2e`` like ``e2e-azure.yml`` does, with only ``inputs`` set."""
    env = {k: v for k, v in os.environ.items() if k not in E2E_INPUTS}
    env.update(PY_COLORS="0", **inputs)  # plain summary line even under FORCE_COLOR
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e", "-o", "addopts=", "-o", "pythonpath=."]
        + ["-p", "no:warnings", "-v", *selection],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout + result.stderr


@pytest.fixture
def scaffolded_dir(tmp_path: Path) -> str:
    (tmp_path / "app" / "functions").mkdir(parents=True)
    for name in ("function_app.py", "host.json", "pyproject.toml"):
        (tmp_path / name).touch()
    return str(tmp_path)


def test_e2e_without_inputs_fails_instead_of_skipping() -> None:
    code, output = _run_e2e()
    assert code != 0, output
    assert "skipped" not in output.lower(), output
    assert "2 failed, 1 error" in output
    assert "E2E_SCAFFOLDED_DIR is required" in output
    assert "E2E_BASE_URL is required" in output


def test_e2e_scaffold_input_only_errors_the_health_test(scaffolded_dir: str) -> None:
    code, output = _run_e2e(E2E_SCAFFOLDED_DIR=scaffolded_dir)
    assert code != 0, output
    assert "skipped" not in output.lower(), output
    assert "2 passed, 1 error" in output
    assert "E2E_BASE_URL is required" in output


def test_e2e_scaffolded_selection_without_scaffold_input_fails() -> None:
    code, output = _run_e2e("-k", "scaffolded")
    assert code != 0, output
    assert "skipped" not in output.lower(), output
    assert "2 failed, 1 deselected" in output
    assert "E2E_SCAFFOLDED_DIR is required" in output


def test_e2e_scaffolded_selection_with_scaffold_input_passes(scaffolded_dir: str) -> None:
    code, output = _run_e2e("-k", "scaffolded", E2E_SCAFFOLDED_DIR=scaffolded_dir)
    assert code == 0, output
    assert "2 passed, 1 deselected" in output
