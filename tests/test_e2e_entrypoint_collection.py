"""Regression check for the local/Azure E2E pytest entrypoint (#414).

``make e2e-local`` and ``make e2e-azure`` both run the Hatch ``e2e-azure``
script, which selects tests with ``-m e2e``. If the ``e2e`` marker is ever
removed from the tests in ``tests/e2e/`` (or the marker expression drifts),
the entrypoint silently selects zero tests instead of failing loudly.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent


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
