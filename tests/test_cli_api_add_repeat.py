"""Repeating ``afs api add`` must fail without modifying the project (#485).

``tests/test_generator.py`` covers the ``add_function`` library error and
``tests/test_cli_intents.py`` covers the CLI rejecting a repeated ``add-route`` and
``add-resource``. Neither exercises the documented ``afs api add`` command twice through the CLI
or proves that the rejected second call leaves the whole project tree byte-for-byte unchanged.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re

from typer.testing import CliRunner

from azure_functions_scaffold.cli import app

runner = CliRunner()
TROUBLESHOOTING = Path(__file__).resolve().parent.parent / "docs" / "guide" / "troubleshooting.md"


def _tree_snapshot(root: Path) -> dict[str, str]:
    """Map every path (files and directories) to a content digest, symlinks unfollowed."""
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[relative] = f"symlink:{path.readlink()}"
        elif path.is_dir():
            snapshot[relative] = "dir"
        else:
            snapshot[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def test_repeated_api_add_fails_without_changing_the_project(tmp_path: Path) -> None:
    created = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path), "--no-git"])
    assert created.exit_code == 0, created.output
    project = tmp_path / "my-api"
    command = ["api", "add", "get-status", "--project-root", str(project)]

    first = runner.invoke(app, command)
    assert first.exit_code == 0, first.output
    assert (project / "app" / "functions" / "get_status.py").is_file()
    before = _tree_snapshot(project)

    second = runner.invoke(app, command)

    assert second.exit_code == 1
    assert "Function module already exists" in second.output
    assert "get_status.py" in second.output
    assert _tree_snapshot(project) == before


def test_troubleshooting_shows_the_repeated_add_command() -> None:
    text = TROUBLESHOOTING.read_text(encoding="utf-8")
    section = text.split("### Function already exists")[1].split("\n## ")[0]

    assert re.search(
        r"^afs api add users --project-root \./my-api +# fails: Function module already exists$",
        section,
        re.MULTILINE,
    )
    assert "Function module already exists" in section
