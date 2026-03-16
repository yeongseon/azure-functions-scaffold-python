"""E2E tests for azure-functions-scaffold.

Tests that:
1. `azure-functions-scaffold init` generates a valid project
2. The generated project deploys to Azure Functions
3. The deployed app responds to HTTP requests

Usage:
    E2E_BASE_URL=https://<app>.azurewebsites.net pytest tests/e2e -v
    (BASE_URL is set by the workflow after deployment)
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest
import requests

BASE_URL = os.environ.get("E2E_BASE_URL", "").rstrip("/")
SCAFFOLDED_DIR = os.environ.get("E2E_SCAFFOLDED_DIR", "")
SKIP_REASON = "E2E_BASE_URL not set — skipping real-Azure e2e tests"
SKIP_SCAFFOLD_REASON = "E2E_SCAFFOLDED_DIR not set — skipping scaffold generation tests"


@pytest.fixture(scope="session", autouse=True)
def warmup() -> None:
    if not BASE_URL:
        return
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/api/health", timeout=10)
            if r.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(3)
    pytest.fail("Warmup failed: /api/health did not respond within 120 s")


# ── Scaffold generation tests (no Azure needed) ────────────────────────────

@pytest.mark.skipif(not SCAFFOLDED_DIR, reason=SKIP_SCAFFOLD_REASON)
def test_scaffolded_project_has_required_files() -> None:
    """Verify the scaffold CLI generated the expected file structure."""
    import pathlib
    root = pathlib.Path(SCAFFOLDED_DIR)
    assert (root / "function_app.py").exists(), "function_app.py missing"
    assert (root / "host.json").exists(), "host.json missing"
    assert (root / "requirements.txt").exists(), "requirements.txt missing"
    assert (root / "app" / "functions").is_dir(), "app/functions/ missing"


@pytest.mark.skipif(not SCAFFOLDED_DIR, reason=SKIP_SCAFFOLD_REASON)
def test_scaffolded_function_app_imports_cleanly() -> None:
    """Verify generated function_app.py is importable (syntax valid)."""
    import pathlib
    app_file = pathlib.Path(SCAFFOLDED_DIR) / "function_app.py"
    result = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open('{app_file}').read())"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in generated function_app.py: {result.stderr}"


# ── Deployed app HTTP tests ────────────────────────────────────────────────

@pytest.mark.skipif(not BASE_URL, reason=SKIP_REASON)
def test_hello_endpoint_returns_200() -> None:
    r = requests.get(f"{BASE_URL}/api/hello", params={"name": "e2e"}, timeout=30)
    assert r.status_code == 200
    assert "e2e" in r.text or "hello" in r.text.lower()
