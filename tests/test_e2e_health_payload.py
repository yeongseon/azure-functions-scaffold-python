"""Regression guard for the live-release health payload assertion (#415).

Loads tests/e2e/test_scaffold_e2e.py as a module and invokes its
test_health_endpoint_returns_200() against in-memory requests.Response
objects (no network access), confirming the certification gate strictly
requires {"status": "ok"} rather than any HTTP 200 response whose text
happens to contain the substring "ok".
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

_REPO_ROOT = Path(__file__).resolve().parent.parent
_E2E_TEST_PATH = _REPO_ROOT / "tests" / "e2e" / "test_scaffold_e2e.py"

_spec = importlib.util.spec_from_file_location("scaffold_e2e", _E2E_TEST_PATH)
assert _spec and _spec.loader
e2e_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e2e_mod)


def _response(status_code: int, body: bytes) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = body
    response.encoding = "utf-8"
    return response


@pytest.mark.parametrize(
    "body",
    [
        b'{"status":"broken"}',
        b'{"status":"not ok"}',
        b"<html>token validation failed</html>",
    ],
)
def test_health_check_rejects_invalid_payloads(
    monkeypatch: pytest.MonkeyPatch, body: bytes
) -> None:
    monkeypatch.setattr(e2e_mod, "BASE_URL", "https://offline.invalid")
    with patch.object(e2e_mod.requests, "get", return_value=_response(200, body)):
        with pytest.raises(AssertionError):
            e2e_mod.test_health_endpoint_returns_200()


def test_health_check_accepts_valid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(e2e_mod, "BASE_URL", "https://offline.invalid")
    with patch.object(e2e_mod.requests, "get", return_value=_response(200, b'{"status":"ok"}')):
        e2e_mod.test_health_endpoint_returns_200()


def test_health_check_rejects_non_200_even_with_valid_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(e2e_mod, "BASE_URL", "https://offline.invalid")
    with patch.object(e2e_mod.requests, "get", return_value=_response(503, b'{"status":"ok"}')):
        with pytest.raises(AssertionError):
            e2e_mod.test_health_endpoint_returns_200()
