from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_http_handler_emits_json_with_invocation_id(tmp_path: Path) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "structured-logging",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version=python_version,
            include_github_actions=False,
            initialize_git=False,
        ),
    )
    subprocess.run(
        ["uv", "sync", "--python", python_version, "--all-extras"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )
    script = """
import io
import json
import logging
from types import SimpleNamespace

import azure.functions as func
from azure_functions_logging import JsonFormatter
import function_app
from app.functions.health import health

stream = io.StringIO()
handler = logging.StreamHandler(stream)
handler.setFormatter(JsonFormatter())
logging.getLogger().handlers[:] = [handler]
logging.getLogger().setLevel(logging.INFO)
request = func.HttpRequest(method="GET", url="http://localhost/api/health", body=b"")
context = SimpleNamespace(invocation_id="inv-123", function_name="health", trace_context=None)
health(request, context)
print(stream.getvalue())
"""
    result = subprocess.run(
        [str(project_root / ".venv" / "bin" / "python"), "-c", script],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["invocation_id"] == "inv-123"
    assert payload["message"] == "Health check requested"
