"""Contract tests for the supported generated HTTP option combinations (#471).

Covers requirements per enabled feature, documented routes and the Swagger spec
URL against the generated ``host.json`` prefix, and the signature-before-parse
webhook ordering when ``--with-validation`` uses direct Pydantic parsing.
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
import re
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import azure.functions as func
import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

_SECRET = "matrix-secret"
_CONTEXT = SimpleNamespace(invocation_id="t", function_name="receive_webhook", trace_context=None)
_EVENT = {
    "event_type": "order.completed",
    "source": "shopify",
    "occurred_at": "2026-04-12T12:00:00Z",
    "data": {},
}
# (id, openapi, validation, doctor) - the supported matrix, not a Cartesian product.
MATRIX = (
    ("baseline", False, False, False),
    ("openapi", True, False, False),
    ("validation", False, True, False),
    ("all", True, True, True),
)
_PACKAGES = {
    "azure-functions-openapi": 1,
    "azure-functions-validation": 2,
    "azure-functions-doctor": 3,
}


def _generate(tmp_path: Path, openapi: bool, validation: bool, doctor: bool) -> Path:
    return scaffold_project(
        "matrix-app",
        tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="standard",
            python_version="3.12",
            include_github_actions=False,
            initialize_git=False,
            include_openapi=openapi,
            include_validation=validation,
            include_doctor=doctor,
        ),
    )


@contextmanager
def _imported(root: Path, module_name: str) -> Iterator[ModuleType]:
    sys.path.insert(0, str(root))
    try:
        importlib.invalidate_caches()
        yield importlib.import_module(module_name)
    finally:
        sys.path.remove(str(root))
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]


def _post(webhooks: ModuleType, body: bytes, signature: str) -> func.HttpResponse:
    request = func.HttpRequest(
        method="POST",
        url="http://localhost/api/webhooks/inbound",
        params={},
        body=body,
        route_params={},
        headers={"Content-Type": "application/json", "X-Signature": signature},
    )
    with patch.dict(os.environ, {"WEBHOOK_SECRET": _SECRET}):
        response: func.HttpResponse = webhooks.receive_webhook(request, _CONTEXT)
    return response


def _sign(body: bytes) -> str:
    return "sha256=" + hmac.new(_SECRET.encode(), body, hashlib.sha256).hexdigest()


@pytest.mark.parametrize(("combo", "openapi", "validation", "doctor"), MATRIX)
def test_requirements_match_enabled_features(
    tmp_path: Path, combo: str, openapi: bool, validation: bool, doctor: bool
) -> None:
    # Given/When: a project generated with this option combination.
    root = _generate(tmp_path, openapi, validation, doctor)
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    enabled = {
        "azure-functions-openapi": openapi,
        "azure-functions-validation": validation,
        "azure-functions-doctor": doctor,
    }

    # Then: each optional package is declared exactly when its flag is on.
    for package, expected in enabled.items():
        assert (package in pyproject) is expected, f"{combo}: {package}"
    assert ("pydantic" in pyproject.lower()) is validation


@pytest.mark.parametrize(("combo", "openapi", "validation", "doctor"), MATRIX)
def test_documented_routes_are_registered_by_the_matrix(
    tmp_path: Path, combo: str, openapi: bool, validation: bool, doctor: bool
) -> None:
    # Given: a generated project for the combination.
    root = _generate(tmp_path, openapi, validation, doctor)
    source = (root / "function_app.py").read_text(encoding="utf-8")
    webhooks = (root / "app/functions/webhooks.py").read_text(encoding="utf-8")
    health = (root / "app/functions/health.py").read_text(encoding="utf-8")

    # Then: core routes always exist; docs routes exist only with --with-openapi.
    assert 'route="webhooks/inbound"' in webhooks, combo
    assert "route=" in health, combo
    doc_routes = {'route="openapi.json"', 'route="openapi.yaml"', 'route="docs"'}
    assert all((route in source) is openapi for route in doc_routes), combo


def test_swagger_spec_url_matches_default_host_route_prefix(tmp_path: Path) -> None:
    # Given: an OpenAPI project and its generated host.json.
    root = _generate(tmp_path, True, False, False)
    host = json.loads((root / "host.json").read_text(encoding="utf-8"))
    prefix = host.get("extensions", {}).get("http", {}).get("routePrefix", "api")

    # When: reading the spec URL the Swagger UI route points at.
    source = (root / "function_app.py").read_text(encoding="utf-8")
    match = re.search(r'openapi_url="([^"]+)"', source)

    # Then: it resolves under the configured prefix (default "api"; the template
    # does not derive a custom prefix, which docs/guide/configuration.md states).
    assert match is not None
    assert match.group(1) == f"/{prefix}/openapi.json"


def test_validation_webhook_verifies_signature_before_parsing_and_avoids_validate_http(
    tmp_path: Path,
) -> None:
    # Given: a validation-enabled project.
    root = _generate(tmp_path, False, True, False)
    source = (root / "app/functions/webhooks.py").read_text(encoding="utf-8")
    assert "validate_http" not in source
    assert source.index("verify_signature(") < source.index("req.get_json()")

    with _imported(root, "app.functions.webhooks") as webhooks:
        bad = b"{not json"
        good = json.dumps(_EVENT).encode()
        wrong_shape = json.dumps({"event_type": "x"}).encode()

        # When/Then: an invalid signature wins over an invalid body (401, not 400/422).
        assert _post(webhooks, bad, "sha256=" + "0" * 64).status_code == 401
        assert _post(webhooks, wrong_shape, "sha256=" + "0" * 64).status_code == 401
        # Signed but malformed JSON -> 400; signed but wrong schema -> 422; valid -> 202.
        assert _post(webhooks, bad, _sign(bad)).status_code == 400
        assert _post(webhooks, wrong_shape, _sign(wrong_shape)).status_code == 422
        assert _post(webhooks, good, _sign(good)).status_code == 202


def test_openapi_with_validation_documents_runtime_status_codes(tmp_path: Path) -> None:
    # Given: openapi + validation project.
    root = _generate(tmp_path, True, True, False)
    source = (root / "app/functions/webhooks.py").read_text(encoding="utf-8")

    # Then: the documented responses match the direct-Pydantic runtime behavior.
    for status in ("202", "400", "401", "422"):
        assert re.search(rf"\b{status}:", source), status
    assert "validate_http" not in source
