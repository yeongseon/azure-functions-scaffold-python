from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from azure_functions_scaffold.generator import add_function
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_added_durable_function_passes_generated_project_checks(tmp_path: Path) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "durable-added",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version=python_version,
            include_github_actions=False,
            initialize_git=False,
        ),
    )
    add_function(project_root=project_root, trigger="durable", function_name="durable")

    subprocess.run(
        ["uv", "sync", "--python", python_version, "--all-extras"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )
    generated_python = project_root / ".venv" / "bin" / "python"
    commands = [
        [str(generated_python), "-m", "compileall", "-q", str(project_root)],
        [str(generated_python), "-m", "pytest", "-q", str(project_root / "tests")],
        [str(generated_python), "-m", "ruff", "check", str(project_root)],
    ]
    results = [
        subprocess.run(command, cwd=project_root, capture_output=True, text=True, check=False)
        for command in commands
    ]

    failures = [
        f"{' '.join(command)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        for command, result in zip(commands, results, strict=True)
        if result.returncode != 0
    ]
    assert not failures, "\n\n".join(failures)
