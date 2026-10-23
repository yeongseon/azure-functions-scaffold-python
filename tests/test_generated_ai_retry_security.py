from pathlib import Path
import subprocess

import pytest

from azure_functions_scaffold.generator import add_function
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


@pytest.fixture(scope="module")
def ai_security_projects(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    destination = tmp_path_factory.mktemp("ai-retry-security")
    projects = []
    for template in ("ai", "http"):
        project = scaffold_project(
            template,
            destination,
            template_name=template,
            options=build_project_options(
                preset_name="strict",
                python_version="3.11",
                initialize_git=False,
                include_github_actions=False,
            ),
        )
        if template == "http":
            add_function(project_root=project, trigger="ai", function_name="chat_added")
        subprocess.run(
            ["uv", "sync", "--python", "3.11", "--all-extras"],
            cwd=project,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        projects.append(project)
    return projects[0], projects[1]


@pytest.mark.parametrize("partial", [False, True])
@pytest.mark.parametrize("failures", [0, 1, 3])
def test_ai_canary_success_error_and_sdk_retry_paths(
    ai_security_projects: tuple[Path, Path], partial: bool, failures: int
) -> None:
    project = ai_security_projects[int(partial)]
    script = r"""
import asyncio
import io
import json
import logging
import os
from unittest.mock import patch

import azure.functions as func

canary = "CANARY_RETRY_PROMPT_must_never_reach_logs"
output = io.StringIO()
handler = logging.StreamHandler(output)
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)
logging.getLogger("app").setLevel(logging.DEBUG)
logging.getLogger("app").addHandler(handler)
calls = []
failures = FAILURES
partial = PARTIAL
error_text = ""

async def run():
    global error_text
    request = func.HttpRequest("POST", "http://localhost/api/chat",
                              body=json.dumps({"prompt": canary}).encode())
    if partial:
        from app.functions.chat_added import chat_added
        response = await chat_added(request)
        assert response.status_code == 200
        assert canary in response.get_body().decode()
        assert calls == []
        return
    import httpx2 as httpx
    from openai import AsyncAzureOpenAI, InternalServerError
    from app.services import ai_service
    from app.functions.ai import chat

    def backend(request):
        calls.append(request)
        assert canary in request.content.decode()
        if len(calls) <= failures:
            return httpx.Response(500, headers={"retry-after-ms": "1"},
                                  json={"error": {"message": "backend unavailable"}})
        return httpx.Response(200, json={"id": "completion", "object": "chat.completion",
            "created": 0, "model": "test", "choices": [{"index": 0,
            "message": {"role": "assistant", "content": "safe answer"}, "finish_reason": "stop"}]})

    os.environ.update(AZURE_OPENAI_ENDPOINT="https://example.test/",
                      AZURE_OPENAI_API_KEY="local-test")
    async with httpx.AsyncClient(transport=httpx.MockTransport(backend)) as transport:
        async with AsyncAzureOpenAI(azure_endpoint="https://example.test/", api_key="local-test",
                                    api_version="2024-02-01", http_client=transport) as client:
            with patch.object(ai_service, "AsyncAzureOpenAI", return_value=client):
                try:
                    response = await chat(request)
                    assert failures < 3 and response.status_code == 200
                except InternalServerError as error:
                    assert failures == 3
                    error_text = str(error)
    assert len(calls) == min(failures + 1, 3)

asyncio.run(run())
assert canary not in output.getvalue(), output.getvalue()
assert canary not in error_text
print("backend_calls", len(calls))
""".replace("FAILURES", str(failures)).replace("PARTIAL", str(partial))
    result = subprocess.run(
        [str(project / ".venv/bin/python"), "-c", script],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"backend_calls {0 if partial else min(failures + 1, 3)}" in result.stdout
