from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def _port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@pytest.mark.skipif(
    os.environ.get("RUN_LOCAL_HOST_SECURITY") != "true", reason="explicit local host run"
)
def test_real_host_indexes_function_authenticated_graph_routes(tmp_path: Path) -> None:
    root = scaffold_project(
        "host-agent",
        tmp_path,
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
        capture_output=True,
        text=True,
        check=True,
        timeout=300,
    )
    ports = [_port() for _ in range(4)]
    host_port, blob_port, queue_port, table_port = ports
    connection = (
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
        "K1SZFPTOtr/KBHBeksoGMGw==;"
        f"BlobEndpoint=http://127.0.0.1:{blob_port}/devstoreaccount1;"
        f"QueueEndpoint=http://127.0.0.1:{queue_port}/devstoreaccount1;"
        f"TableEndpoint=http://127.0.0.1:{table_port}/devstoreaccount1;"
    )
    environment = {
        **os.environ,
        "PATH": f"{root / '.venv/bin'}:{os.environ['PATH']}",
        "VIRTUAL_ENV": str(root / ".venv"),
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AzureWebJobsStorage": connection,
        "LANGGRAPH_PUBLIC_DEMO": "false",
    }
    processes: list[subprocess.Popen[bytes]] = []
    with (
        (tmp_path / "host.log").open("wb") as host_log,
        (tmp_path / "azurite.log").open("wb") as azurite_log,
    ):
        try:
            processes.append(
                subprocess.Popen(
                    [
                        "azurite",
                        "--silent",
                        "--location",
                        str(tmp_path / "storage"),
                        "--blobPort",
                        str(blob_port),
                        "--queuePort",
                        str(queue_port),
                        "--tablePort",
                        str(table_port),
                    ],
                    stdout=azurite_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            )
            processes.append(
                subprocess.Popen(
                    [
                        "func",
                        "start",
                        "--port",
                        str(host_port),
                    ],
                    cwd=root,
                    env=environment,
                    stdout=host_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            )
            deadline = time.monotonic() + 120
            functions = []
            while time.monotonic() < deadline:
                try:
                    with urlopen(
                        f"http://127.0.0.1:{host_port}/admin/functions", timeout=2
                    ) as response:
                        functions = json.load(response)
                    if functions:
                        break
                except (URLError, TimeoutError):
                    if processes[-1].poll() is not None:
                        pytest.fail("Host exited: " + (tmp_path / "host.log").read_text())
                time.sleep(0.5)
            bindings = [
                binding
                for function in functions
                for binding in function["config"]["bindings"]
                if binding["type"] == "httpTrigger"
                and binding.get("route", "").endswith(("/invoke", "/stream"))
            ]
            assert len(bindings) == 2, (tmp_path / "host.log").read_text()
            assert {binding["authLevel"].lower() for binding in bindings} == {"function"}
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=15)
