from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_python_310_project_installs_on_newer_supported_python(tmp_path: Path) -> None:
    project_root = scaffold_project(
        "python-compatible",
        tmp_path,
        options=build_project_options(
            preset_name="standard",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
        ),
    )

    result = subprocess.run(
        ["uv", "sync", "--python", sys.executable, "--all-extras"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_generated_makefile_uses_configurable_python(tmp_path: Path) -> None:
    project_root = scaffold_project("configurable-python", tmp_path)

    makefile = (project_root / "Makefile").read_text(encoding="utf-8")

    assert "PYTHON ?= python3" in makefile
    assert "$(PYTHON) -m venv $(VENV_DIR)" in makefile
