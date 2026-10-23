from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from email.parser import BytesParser
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import zipfile

from tools.verification_diagnostics import diagnose
from tools.verification_evidence import Summary, collect, publish, save
from tools.verification_manifest import TEMPLATES
from tools.verification_process import configured, run


class LaneFailure(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Candidate:
    python: Path
    wheel: Path
    digest: str
    version: str


def checked(command: list[str], directory: Path, *, cwd: Path | None = None) -> None:
    with configured(
        dict.fromkeys(("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONUSERBASE"), "")
    ):
        code = run(command, directory, 900, cwd=cwd)
    if code:
        raise LaneFailure(f"{command[0]} failed with exit {code}")


@contextmanager
def candidate(directory: Path) -> Iterator[Candidate]:
    root = Path.cwd().resolve()
    with tempfile.TemporaryDirectory(prefix="scaffold-candidate-") as temporary:
        work = Path(temporary)
        configured_wheel = os.environ.get("VERIFICATION_WHEEL", "")
        if configured_wheel:
            wheel = Path(configured_wheel).resolve(strict=True)
        else:
            checked(
                [sys.executable, "-m", "build", "--wheel", "--outdir", str(work / "dist")],
                directory / "logs/build.log",
            )
            wheels = list((work / "dist").glob("*.whl"))
            if len(wheels) != 1:
                raise LaneFailure("Expected exactly one candidate wheel")
            wheel = wheels[0]
        checked([sys.executable, "-m", "venv", str(work / "venv")], directory / "logs/venv.log")
        python = work / "venv/bin/python"
        checked(
            [str(python), "-m", "pip", "install", str(wheel)],
            directory / "logs/install.log",
            cwd=work,
        )
        script = (
            "import azure_functions_scaffold as a; from pathlib import Path; "
            "from importlib.metadata import version; "
            f"assert not Path(a.__file__).resolve().is_relative_to(Path({str(root)!r})); "
            "assert a.__version__ == version('azure-functions-scaffold'); "
            "print(a.__version__)"
        )
        checked([str(python), "-I", "-c", script], directory / "logs/identity.log", cwd=work)
        installed_version = (directory / "logs/identity.log").read_text().strip()
        with zipfile.ZipFile(wheel) as archive:
            metadata_paths = [
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_paths) != 1:
                raise LaneFailure("Candidate wheel must have exactly one metadata record")
            metadata = BytesParser().parsebytes(archive.read(metadata_paths[0]))
            if metadata["Version"] != installed_version:
                raise LaneFailure("Installed candidate differs from wheel version")
        yield Candidate(python, wheel, sha256(wheel.read_bytes()).hexdigest(), installed_version)


def generate(candidate: Candidate, work: Path, template: str) -> Path:
    directory = work / "evidence"
    checked(
        [
            str(candidate.python.parent / "afs"),
            "advanced",
            "new",
            "generated-app",
            "--destination",
            str(work),
            "--template",
            template,
            "--preset",
            "strict",
            "--python-version",
            f"{sys.version_info.major}.{sys.version_info.minor}",
            "--no-git",
            "--no-github-actions",
            *shlex.split(os.environ.get("VERIFICATION_FEATURE_FLAGS", "")),
        ],
        directory / "generate.log",
        cwd=work,
    )
    project = work / "generated-app"
    for name in ("function_app.py", "host.json", "pyproject.toml", "requirements.txt"):
        if not (project / name).is_file():
            raise LaneFailure(f"Generated project missing {name}")
    if json.loads((project / "host.json").read_text()).get("version") != "2.0":
        raise LaneFailure("Generated host.json must target runtime 2.0")
    if os.environ.get("VERIFICATION_ADDITIONS") == "1":
        for arguments in (
            ["api", "add", "get-status"],
            ["api", "add-route", "status"],
            ["api", "add-resource", "products"],
            ["advanced", "add", "servicebus", "process-events"],
        ):
            checked(
                [str(candidate.python.parent / "afs"), *arguments, "--project-root", str(project)],
                directory / f"add-{arguments[1]}.log",
                cwd=work,
            )
    return project


def install_project(project: Path, directory: Path) -> Path:
    venv = project.parent / "project-env"
    checked([sys.executable, "-m", "venv", str(venv)], directory / "logs/project-venv.log")
    python = venv / "bin/python"
    checked(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "-e",
            f"{project}[dev]",
            "azure-functions-doctor>=0.22",
        ],
        directory / "logs/dependencies.log",
        cwd=project,
    )
    checked([str(python), "-m", "pip", "check"], directory / "logs/pip-check.log", cwd=project)
    checked(
        [
            str(python),
            "-c",
            "from importlib.metadata import version; print(version('azure-functions'))",
        ],
        directory / "logs/sdk-version.log",
        cwd=project,
    )
    return python


def digest_project(project: Path) -> str:
    digest = sha256()
    for path in sorted(project.rglob("*")):
        if path.is_file() and not any(
            part.startswith(".") or part == "__pycache__"
            for part in path.relative_to(project).parts
        ):
            digest.update(path.relative_to(project).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_project(project: Path, python: Path, directory: Path) -> Summary:
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    command = [
        str(python),
        "-m",
        "pytest",
        "-q",
        "-o",
        "addopts=",
        "tests",
        "--junitxml=" + str(directory / "junit.xml"),
    ]
    with configured({"PYTHONPATH": "", "PYTEST_ADDOPTS": "", "WEBHOOK_SECRET": "test-secret-key"}):
        code = run(command, directory / "logs/pytest.log", cwd=project)
    return collect(directory, command, code)


def project_lane(candidate: Candidate, template: str, directory: Path) -> Summary:
    with tempfile.TemporaryDirectory(prefix=f"scaffold-{template}-") as temporary:
        work = Path(temporary)
        project = generate(candidate, work, template)
        generated_digest = digest_project(project)
        python = install_project(project, directory)
        for label, arguments in (
            ("compile", ["-m", "compileall", "-q", "app", "tests", "function_app.py"]),
            ("lint", ["-m", "ruff", "check", "."]),
            ("types", ["-m", "mypy", "."]),
        ):
            checked([str(python), *arguments], directory / f"logs/{label}.log", cwd=project)
        summary = test_project(project, python, directory)
        if template == "langgraph":
            checked(
                [
                    str(python),
                    "-c",
                    "import azure.functions as f; import function_app as a; "
                    "assert isinstance(a.func_app, f.FunctionApp); "
                    "assert len(a.func_app.get_functions()) > 0",
                ],
                directory / "logs/adapter-export.log",
                cwd=project,
            )
        diagnostic = diagnose(project, python, directory / "logs", template=template)
        if diagnostic.exit_code:
            summary = replace(summary, status="FAIL", exit_code=diagnostic.exit_code)
        sdk = (directory / "logs/sdk-version.log").read_text().strip()
        return replace(
            summary,
            reason=f"diagnostics={diagnostic.category}"
            + (
                f"; exemption={diagnostic.exemption.issue}; expires={diagnostic.exemption.expires}"
                if diagnostic.exemption
                else ""
            ),
            diagnostics_status=diagnostic.category,
            candidate_version=candidate.version,
            artifact_sha256=candidate.digest,
            generated_python=f"{sys.version_info.major}.{sys.version_info.minor}",
            sdk_version=sdk,
            generated_digest=generated_digest,
        )


def existing_project(project: Path, directory: Path) -> Summary:
    python = install_project(project, directory)
    for label, arguments in (
        ("compile", ["-m", "compileall", "-q", "app", "tests", "function_app.py"]),
        ("lint", ["-m", "ruff", "check", "."]),
        ("types", ["-m", "mypy", "."]),
    ):
        checked([str(python), *arguments], directory / f"logs/{label}.log", cwd=project)
    summary = test_project(project, python, directory)
    diagnostic = diagnose(project, python, directory / "logs")
    return replace(
        summary,
        status="FAIL" if diagnostic.exit_code else summary.status,
        exit_code=diagnostic.exit_code or summary.exit_code,
        reason=f"diagnostics={diagnostic.category}",
    )


def generated(directory: Path, selected: tuple[str, ...] = TEMPLATES) -> list[Summary]:
    outcomes = []
    with candidate(directory) as artifact:
        for template in selected:
            destination = directory / template
            try:
                summary = project_lane(artifact, template, destination)
            except (OSError, LaneFailure, ValueError) as error:
                summary = Summary(
                    1,
                    template,
                    ("generated-project", template),
                    0,
                    0,
                    0,
                    0,
                    "FAIL",
                    1,
                    reason=str(error),
                    candidate_version=artifact.version,
                    artifact_sha256=artifact.digest,
                )
            publish(save(destination, summary))
            outcomes.append(summary)
    return outcomes
