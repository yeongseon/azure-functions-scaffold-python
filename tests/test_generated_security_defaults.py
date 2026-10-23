"""Behavior checks against rendered applications, without paid model calls."""

from __future__ import annotations

import importlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys

import anyio
import azure.functions as func
import pytest

from azure_functions_scaffold.generator import add_function
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options

CANARY = "CANARY_SECRET_prompt_do_not_log_449"


@pytest.mark.parametrize("partial", [False, True])
@pytest.mark.parametrize("outcome", ["success", "invalid", "error"])
@pytest.mark.parametrize("preset", ["minimal", "standard", "strict"])
def test_prompt_is_absent_from_generated_logs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    partial: bool,
    outcome: str,
    preset: str,
) -> None:
    # Given a rendered endpoint and a fake completion backend (no external service).
    root = scaffold_project(
        "safe-ai",
        tmp_path,
        template_name="http" if partial else "ai",
        options=build_project_options(
            preset_name=preset,
            python_version="3.11",
            include_github_actions=False,
            initialize_git=False,
        ),
    )
    if partial:
        add_function(project_root=root, trigger="ai", function_name="chat_added")
    monkeypatch.syspath_prepend(str(root))
    module_name = "app.functions.chat_added" if partial else "app.functions.ai"
    if not partial:
        # The completion SDK is not needed to exercise the handler's logging boundary.
        from types import ModuleType

        service = ModuleType("app.services.ai_service")

        async def completion(prompt: str) -> str:
            if outcome == "error":
                raise RuntimeError("backend unavailable")
            return "fake completion"

        monkeypatch.setattr(service, "generate_completion", completion, raising=False)
        monkeypatch.setitem(sys.modules, service.__name__, service)
    try:
        module = importlib.import_module(module_name)
        handler = getattr(module, "chat_added" if partial else "chat")
        request = func.HttpRequest(
            "POST",
            "http://localhost/api/chat",
            body=(
                json.dumps({"prompt": CANARY}).encode()
                if outcome != "invalid"
                else ('{"prompt": ' + CANARY).encode()
            ),
        )
        caplog.set_level(logging.DEBUG)
        # When the endpoint handles success, malformed input, or a backend failure.
        if outcome == "error" and not partial:
            with pytest.raises(RuntimeError) as error:
                anyio.run(handler, request)
            assert CANARY not in str(error.value)
        else:
            response = anyio.run(handler, request)
            assert response.status_code == (400 if outcome == "invalid" else 200)
        # Then neither the user prompt nor a prefix enters the log stream.
        assert CANARY not in caplog.text
        assert "CANARY_SECRET" not in caplog.text
    finally:
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                sys.modules.pop(name, None)


@pytest.fixture(scope="module")
def isolated_langgraph(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = scaffold_project(
        "secure-agent",
        tmp_path_factory.mktemp("agent-security"),
        template_name="langgraph",
        options=build_project_options(
            preset_name="strict",
            python_version="3.11",
            include_github_actions=False,
            initialize_git=False,
        ),
    )
    subprocess.run(
        ["uv", "sync", "--python", "3.11", "--all-extras"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return root


@pytest.mark.parametrize(
    "demo", ["true", "True", "TRUE", "1", "yes", "false", "", " true ", "true\n"]
)
def test_langgraph_registered_routes_have_explicit_auth(
    isolated_langgraph: Path,
    demo: str,
) -> None:
    # Given the actual installed generated app in an isolated interpreter.
    script = (
        "import json, function_app; "
        "print(json.dumps([f.get_trigger().get_dict_repr() "
        "for f in function_app.func_app.get_functions()], default=lambda v: v.value))"
    )
    # When app settings select the default or explicitly public profile at import.
    result = subprocess.run(
        [str(isolated_langgraph / ".venv/bin/python"), "-c", script],
        cwd=isolated_langgraph,
        env={**os.environ, "LANGGRAPH_PUBLIC_DEMO": demo},
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    bindings = json.loads(result.stdout)
    execution = [b for b in bindings if b["route"].endswith(("/invoke", "/stream"))]
    # Then execution routes declare FUNCTION unless the exact public opt-in is true.
    assert len(execution) == 2
    expected = "anonymous" if demo == "true" else "function"
    assert {b["authLevel"] for b in execution} == {expected}
    assert ("LANGGRAPH_PUBLIC_DEMO=true: graph routes are public" in result.stderr) == (
        expected == "anonymous"
    )
