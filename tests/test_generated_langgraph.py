from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_langgraph_project_installs_and_imports_function_app(tmp_path: Path) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "langgraph-runtime",
        tmp_path,
        template_name="langgraph",
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
    result = subprocess.run(
        [str(project_root / ".venv" / "bin" / "python"), "-c", "import function_app"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
