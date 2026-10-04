from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from azure_functions_scaffold.generator import add_function
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_added_ai_functions_have_unique_routes_and_pass_ruff(tmp_path: Path) -> None:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    project_root = scaffold_project(
        "ai-routes",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version=python_version,
            include_github_actions=False,
            initialize_git=False,
        ),
    )
    add_function(project_root=project_root, trigger="ai", function_name="ai-one")
    add_function(project_root=project_root, trigger="ai", function_name="ai-two")
    subprocess.run(
        ["uv", "sync", "--python", python_version, "--all-extras"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )
    python = project_root / ".venv" / "bin" / "python"
    routes = subprocess.run(
        [
            str(python),
            "-c",
            "import function_app; functions = function_app.app.get_functions(); "
            "print(sorted(function.get_trigger().route for function in functions))",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
    )
    lint = subprocess.run(
        [str(python), "-m", "ruff", "check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert "['ai-one', 'ai-two'" in routes.stdout
    assert lint.returncode == 0, lint.stdout + lint.stderr
