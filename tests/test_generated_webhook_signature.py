"""Regression tests for webhook signature validation (#423).

The generated webhook verifier checked only the ``sha256=`` prefix before
passing the remaining header value directly to ``hmac.compare_digest``.
That function requires ASCII-only string operands, so a header such as
``X-Signature: sha256=\u00e9`` raised ``TypeError`` instead of returning
``False``, bypassing the handler's intended 401 response.

These tests import the generated helper and handler directly (no network,
no uv sync) and exercise malformed-ASCII, non-ASCII, and valid digests.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import hmac
import importlib
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import azure.functions as func
import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

_SECRET = "test-secret-key"
_VALID_PAYLOAD = json.dumps(
    {
        "event_type": "order.completed",
        "source": "shopify",
        "occurred_at": "2026-04-12T12:00:00Z",
        "data": {"order_id": "12345"},
    }
).encode()
_CONTEXT = SimpleNamespace(
    invocation_id="test", function_name="receive_webhook", trace_context=None
)


def _sign(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@contextmanager
def _imported(root: Path, module_name: str) -> Iterator[ModuleType]:
    sys.path.insert(0, str(root))
    try:
        importlib.invalidate_caches()
        yield importlib.import_module(module_name)
    finally:
        sys.path.remove(str(root))
        for name in list(sys.modules):
            if name == "app" or name == module_name or name.startswith(("app.", f"{module_name}.")):
                del sys.modules[name]


@pytest.fixture
def webhook_project(tmp_path: Path) -> Path:
    return scaffold_project(
        "webhook-signature",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.12",
            include_github_actions=False,
            initialize_git=False,
        ),
    )


@pytest.mark.parametrize("bad_signature", ["sha256=not-hex", "sha256=\u00e9"])
def test_verify_signature_rejects_malformed_digest_without_raising(
    webhook_project: Path, bad_signature: str
) -> None:
    with _imported(webhook_project, "app.services.webhook_service") as service:
        assert service.verify_signature(b"{}", bad_signature, _SECRET) is False


def test_verify_signature_accepts_valid_digest(webhook_project: Path) -> None:
    with _imported(webhook_project, "app.services.webhook_service") as service:
        signature = _sign(b"{}", _SECRET)
        assert service.verify_signature(b"{}", signature, _SECRET) is True


@pytest.mark.parametrize("bad_signature", ["sha256=not-hex", "sha256=\u00e9"])
def test_receive_webhook_returns_401_for_malformed_signature(
    webhook_project: Path, bad_signature: str
) -> None:
    with (
        _imported(webhook_project, "app.functions.webhooks") as webhooks,
        _imported(webhook_project, "app.services.webhook_service") as service,
    ):
        service.webhook_store.clear()
        with patch.dict(os.environ, {"WEBHOOK_SECRET": _SECRET}):
            request = func.HttpRequest(
                method="POST",
                url="http://localhost/api/webhooks/inbound",
                params={},
                body=_VALID_PAYLOAD,
                route_params={},
                headers={"Content-Type": "application/json", "X-Signature": bad_signature},
            )
            response = webhooks.receive_webhook(request, _CONTEXT)

        assert response.status_code == 401
        assert service.webhook_store.list_recent() == []


def test_receive_webhook_accepts_valid_signature(webhook_project: Path) -> None:
    with (
        _imported(webhook_project, "app.functions.webhooks") as webhooks,
        _imported(webhook_project, "app.services.webhook_service") as service,
    ):
        service.webhook_store.clear()
        signature = _sign(_VALID_PAYLOAD, _SECRET)
        with patch.dict(os.environ, {"WEBHOOK_SECRET": _SECRET}):
            request = func.HttpRequest(
                method="POST",
                url="http://localhost/api/webhooks/inbound",
                params={},
                body=_VALID_PAYLOAD,
                route_params={},
                headers={"Content-Type": "application/json", "X-Signature": signature},
            )
            response = webhooks.receive_webhook(request, _CONTEXT)

        assert response.status_code == 202
        assert len(service.webhook_store.list_recent()) == 1
