from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from unittest.mock import patch

import azure.functions as func
import pytest

from tests.test_generated_webhook_signature import _CONTEXT, _SECRET, _imported, _sign
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

CANARY = "CANARY_SECRET_webhook_payload_449"


@pytest.mark.parametrize("validation", [False, True])
@pytest.mark.parametrize("case", ["missing", "wrong", "malformed", "tampered", "oversized", "valid", "invalid"])
def test_webhook_input_boundaries(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, validation: bool, case: str,
) -> None:
    root = scaffold_project(
        "webhook-boundary", tmp_path,
        options=build_project_options(
            preset_name="standard", python_version="3.11", include_github_actions=False,
            initialize_git=False, include_validation=validation,
        ),
    )
    body = json.dumps({
        "event_type": CANARY, "source": CANARY,
        "occurred_at": "2026-04-12T12:00:00Z", "data": {"value": CANARY},
    }).encode()
    if case == "invalid":
        body = json.dumps({"event_type": CANARY, "source": CANARY, "occurred_at": {"value": CANARY}}).encode()
    if case == "oversized":
        body += b" " * (1024 * 1024)
    signature = _sign(body, _SECRET)
    if case == "missing":
        signature = ""
    if case == "wrong":
        signature = "sha256=" + "0" * 64
    if case == "malformed":
        signature = "sha256=not-hex"
    if case == "tampered":
        body += b" "
    with _imported(root, "app.functions.webhooks") as module, patch.dict(
        os.environ, {"WEBHOOK_SECRET": _SECRET},
    ):
        caplog.set_level(logging.DEBUG)
        response = module.receive_webhook(func.HttpRequest(
            "POST", "http://localhost/api/webhooks/inbound", body=body,
            headers={"X-Signature": signature},
        ), _CONTEXT)
    expected = 401
    if case in {"valid", "invalid"}:
        expected = 422 if case == "invalid" and validation else 202
    if case == "oversized":
        expected = 413
    assert response.status_code == expected
    assert CANARY not in caplog.text
    assert CANARY.encode() not in response.get_body()
