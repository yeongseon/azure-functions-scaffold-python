"""Regression tests for AI template request/prompt type validation (#421).

Both the standalone `ai` template and the add-AI-function partial caught
JSON parsing errors but called ``body.get`` unconditionally, so valid JSON
values such as ``null``, ``[]``, or ``42`` raised ``AttributeError``
instead of a controlled 400 response. A non-string ``prompt`` (e.g. ``42``)
passed the truthiness check and later raised ``TypeError`` at
``prompt[:50]`` or reached the completion backend.

These tests import the generated handler modules directly (no ``uv sync``
subprocess, no model backend) and assert that malformed request shapes are
rejected with a 400 JSON error before any completion call, while a valid
string prompt still succeeds.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import azure.functions as func
import pytest

from azure_functions_scaffold.generator import add_function
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

_INVALID_BODIES: list[Any] = [None, [], 42, {"prompt": 42}, {"prompt": True}, {"prompt": ["x"]}]


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


def _request(body: Any) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="http://localhost/api/chat",
        params={},
        headers={"Content-Type": "application/json"},
        body=json.dumps(body).encode(),
    )


def _options(python_version: str) -> Any:
    return build_project_options(
        preset_name="standard",
        python_version=python_version,
        include_github_actions=False,
        initialize_git=False,
    )


@pytest.mark.parametrize("body", _INVALID_BODIES)
def test_ai_project_chat_rejects_malformed_request(tmp_path: Path, body: Any) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "ai-validate", tmp_path, template_name="ai", options=_options(python_version)
    )

    called: list[Any] = []

    async def fake_completion(prompt: str) -> str:
        called.append(prompt)
        return "fake completion"

    service = ModuleType("app.services.ai_service")
    service.generate_completion = fake_completion  # type: ignore[attr-defined]
    sys.modules[service.__name__] = service
    try:
        with _imported(project_root, "app.functions.ai") as module:
            response = asyncio.run(module.chat(_request(body)))
    finally:
        sys.modules.pop(service.__name__, None)

    assert response.status_code == 400
    assert json.loads(response.get_body())["error"]
    assert called == []


def test_ai_project_chat_accepts_valid_string_prompt(tmp_path: Path) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "ai-validate-ok", tmp_path, template_name="ai", options=_options(python_version)
    )

    called: list[Any] = []

    async def fake_completion(prompt: str) -> str:
        called.append(prompt)
        return "fake completion"

    service = ModuleType("app.services.ai_service")
    service.generate_completion = fake_completion  # type: ignore[attr-defined]
    sys.modules[service.__name__] = service
    try:
        with _imported(project_root, "app.functions.ai") as module:
            response = asyncio.run(module.chat(_request({"prompt": "hello"})))
    finally:
        sys.modules.pop(service.__name__, None)

    assert response.status_code == 200
    assert json.loads(response.get_body())["response"] == "fake completion"
    assert called == ["hello"]


@pytest.mark.parametrize("body", _INVALID_BODIES)
def test_added_ai_function_rejects_malformed_request(tmp_path: Path, body: Any) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "ai-added-validate", tmp_path, template_name="http", options=_options(python_version)
    )
    add_function(project_root=project_root, trigger="ai", function_name="chat_added")

    with _imported(project_root, "app.functions.chat_added") as module:
        response = asyncio.run(module.chat_added(_request(body)))

    assert response.status_code == 400
    assert json.loads(response.get_body())["error"]


def test_added_ai_function_accepts_valid_string_prompt(tmp_path: Path) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "ai-added-validate-ok", tmp_path, template_name="http", options=_options(python_version)
    )
    add_function(project_root=project_root, trigger="ai", function_name="chat_added")

    with _imported(project_root, "app.functions.chat_added") as module:
        response = asyncio.run(module.chat_added(_request({"prompt": "hello"})))

    assert response.status_code == 200
    assert json.loads(response.get_body())["response"] == "Echo: hello"
