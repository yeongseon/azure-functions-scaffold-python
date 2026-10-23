from __future__ import annotations

from contextlib import ExitStack
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

import requests

from tools.verification_evidence import Summary, collect
from tools.verification_generated import Candidate, digest_project, generate, install_project
from tools.verification_process import child, configured, run

STORAGE_KEY = (
    "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
)


class MissingPrerequisite(RuntimeError):
    pass


def port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def readiness(ports: tuple[int, ...]) -> None:
    deadline = time.monotonic() + 30
    while True:
        try:
            for number in ports:
                with socket.create_connection(("127.0.0.1", number), timeout=1):
                    continue
            return
        except OSError as error:
            if time.monotonic() >= deadline:
                raise MissingPrerequisite("Owned Azurite readiness timed out") from error
            time.sleep(0.2)


def host_smoke(artifact: Candidate, directory: Path) -> Summary:
    if any(shutil.which(tool) is None for tool in ("func", "azurite")):
        return Summary(
            1,
            "host-smoke",
            ("func", "start"),
            0,
            0,
            0,
            0,
            "INCOMPLETE",
            2,
            reason="func and azurite required",
        )
    with ExitStack() as stack:
        work = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="scaffold-host-")))
        project = generate(artifact, work, "http")
        generated_digest = digest_project(project)
        python = install_project(project, directory)
        ports = tuple(port() for _ in range(4))
        command = [
            "azurite",
            "--silent",
            "--skipApiVersionCheck",
            "--location",
            str(work / "storage"),
        ]
        connection = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        connection += f"AccountKey={STORAGE_KEY};"
        for service, number in zip(("blob", "queue", "table"), ports[:3], strict=True):
            command += [f"--{service}Host", "127.0.0.1", f"--{service}Port", str(number)]
            connection += f"{service.title()}Endpoint=http://127.0.0.1:{number}/devstoreaccount1;"
        stack.enter_context(child(command, directory / "logs/azurite.log"))
        readiness(ports[:3])
        values = {
            "AzureWebJobsStorage": connection,
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "PATH": str(python.parent) + os.pathsep + os.environ["PATH"],
            "PYTHONPATH": "",
            "VIRTUAL_ENV": str(python.parent.parent),
            "PYTHON_ISOLATE_WORKER_DEPENDENCIES": "1",
        }
        (project / "local.settings.json").write_text(
            json.dumps(
                {
                    "IsEncrypted": False,
                    "Values": {
                        "AzureWebJobsStorage": connection,
                        "FUNCTIONS_WORKER_RUNTIME": "python",
                    },
                }
            )
        )
        stack.enter_context(configured(values))
        process = stack.enter_context(
            child(
                ["func", "start", "--python", "--port", str(ports[3])],
                directory / "logs/host.log",
                project,
            )
        )
        deadline = time.monotonic() + 120
        while True:
            try:
                response = requests.get(f"http://127.0.0.1:{ports[3]}/api/health", timeout=2)
                if response.status_code == 200:
                    if response.json().get("status") != "ok":
                        raise MissingPrerequisite("Generated health response has incorrect payload")
                    break
            except requests.RequestException:
                if process.poll() is not None:
                    raise MissingPrerequisite(
                        "Owned Functions host exited before readiness"
                    ) from None
            if time.monotonic() >= deadline:
                raise MissingPrerequisite("Generated HTTP host readiness/invocation timed out")
            time.sleep(0.5)
        suite = ET.Element("testsuite", tests="1", failures="0", errors="0", skipped="0")
        ET.SubElement(suite, "testcase", classname="generated_http_host", name="health_invocation")
        directory.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(suite).write(directory / "junit.xml")
        for tool in ("func", "azurite"):
            run([tool, "--version"], directory / f"logs/{tool}-version.log", 15)
        return replace(
            collect(directory, ["func", "start", "generated-http"], 0),
            candidate_version=artifact.version,
            artifact_sha256=artifact.digest,
            generated_digest=generated_digest,
            sdk_version=(directory / "logs/sdk-version.log").read_text().strip(),
            generated_python=f"{sys.version_info.major}.{sys.version_info.minor}",
        )
