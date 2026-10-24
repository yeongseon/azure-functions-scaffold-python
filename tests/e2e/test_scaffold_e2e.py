"""E2E tests for azure-functions-scaffold.

Tests that:
1. `azure-functions-scaffold init` generates a valid project
2. The generated project deploys to Azure Functions
3. The deployed app responds to HTTP requests

Both inputs are required and are never optional: a missing value fails the
run, it does not skip. ``e2e-azure.yml`` sets them in two phases:
``E2E_SCAFFOLDED_DIR`` for ``-k scaffolded`` and ``E2E_BASE_URL`` for
``-k "not scaffolded"``.

Usage:
    E2E_SCAFFOLDED_DIR=<generated project> E2E_BASE_URL=https://<app>.azurewebsites.net \\
        pytest tests/e2e -o addopts= -v
    (the workflow sets both after generating and deploying the project)
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest
import requests


def _required(name: str) -> str:
    """A required e2e input is never optional: a missing value fails the run, it does not skip."""
    value = os.environ.get(name, "").strip()
    if not value:
        pytest.fail(f"{name} is required for this e2e test and is not set", pytrace=False)
    return value


@pytest.fixture(scope="session")
def base_url() -> str:
    url = _required("E2E_BASE_URL").rstrip("/")
    deadline = time.time() + 300
    while time.time() < deadline:
        try:
            r = requests.get(f"{url}/api/health", timeout=10)
            if r.status_code == 200:
                return url
        except requests.RequestException:
            pass
        time.sleep(3)
    pytest.fail("Warmup failed: /api/health did not respond within 300 s")


# ── Scaffold generation tests (no Azure needed) ────────────────────────────


@pytest.mark.e2e
def test_scaffolded_project_has_required_files() -> None:
    """Verify the scaffold CLI generated the expected file structure."""
    import pathlib

    root = pathlib.Path(_required("E2E_SCAFFOLDED_DIR"))
    assert (root / "function_app.py").exists(), "function_app.py missing"
    assert (root / "host.json").exists(), "host.json missing"
    assert (root / "pyproject.toml").exists(), "pyproject.toml missing"
    assert (root / "app" / "functions").is_dir(), "app/functions/ missing"


@pytest.mark.e2e
def test_scaffolded_function_app_imports_cleanly() -> None:
    """Verify generated function_app.py is importable (syntax valid)."""
    import pathlib

    app_file = pathlib.Path(_required("E2E_SCAFFOLDED_DIR")) / "function_app.py"
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open('{app_file}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in generated function_app.py: {result.stderr}"


# ── Deployed app HTTP tests ────────────────────────────────────────────────


@pytest.mark.e2e
def test_health_endpoint_returns_200(base_url: str) -> None:
    r = requests.get(f"{base_url}/api/health", timeout=30)
    assert r.status_code == 200
    try:
        payload = r.json()
    except ValueError as exc:
        raise AssertionError(f"Health response body is not valid JSON: {r.text!r}") from exc
    assert payload.get("status") == "ok", f"Unexpected health payload: {payload!r}"
