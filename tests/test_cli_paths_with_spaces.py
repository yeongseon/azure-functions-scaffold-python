"""CLI generation into a destination path that contains spaces (#478).

Project names may not contain whitespace (see ``validate_project_name``), so spaces can only
appear in the *destination* path. These tests pass such a path through the real CLI as a single
argument, the way a quoted shell argument arrives, and check the generated root and entrypoint.
No Core Tools, Azure resources or shell quoting are involved.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re

from typer.testing import CliRunner

from azure_functions_scaffold.cli import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parent.parent
TROUBLESHOOTING = REPO_ROOT / "docs" / "guide" / "troubleshooting.md"


def test_new_into_destination_with_spaces_generates_a_correct_root(tmp_path: Path) -> None:
    parent = tmp_path / "My Azure  Projects" / "team one"
    parent.mkdir(parents=True)

    result = runner.invoke(app, ["new", "orders-api", "--destination", str(parent), "--no-git"])

    assert result.exit_code == 0, result.output
    root = parent / "orders-api"
    assert root.is_dir()
    assert {path.name for path in parent.iterdir()} == {"orders-api"}
    entrypoint = root / "function_app.py"
    assert entrypoint.is_file()
    tree = ast.parse(entrypoint.read_text(encoding="utf-8"))
    assert any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "app" for target in node.targets)
        for node in tree.body
    )
    assert (root / "host.json").is_file()
    assert (root / "app" / "functions" / "health.py").is_file()
    assert str(tmp_path) not in entrypoint.read_text(encoding="utf-8")


def test_destination_with_spaces_does_not_relax_project_name_validation(tmp_path: Path) -> None:
    parent = tmp_path / "with space"
    parent.mkdir()

    result = runner.invoke(app, ["new", "bad name", "--destination", str(parent), "--no-git"])

    assert result.exit_code != 0
    assert list(parent.iterdir()) == []


def test_troubleshooting_documents_a_quoted_path_with_spaces() -> None:
    text = TROUBLESHOOTING.read_text(encoding="utf-8")

    assert re.search(r'^afs new orders-api --destination "[^"]* [^"]*"$', text, re.MULTILINE)
