from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from azure_functions_scaffold.scaffolder import scaffold_project

KINDS = (
    "timer",
    "queue",
    "blob",
    "servicebus",
    "eventhub",
    "cosmosdb",
    "durable",
    "http",
    "ai",
    "route",
    "resource",
)


def command(kind: str, root: Path) -> list[str]:
    arguments = (
        ["api", "add-resource", "cli_items"]
        if kind == "resource"
        else ["api", "add-route", "cli_escape"]
        if kind == "route"
        else ["advanced", "add", kind, "cli_escape"]
    )
    return [str(Path(sys.executable).parent / "afs"), *arguments, "--project-root", str(root)]


def inventory(root: Path) -> dict[str, tuple[int, int, str]]:
    result = {}
    for path in [root, *root.rglob("*")]:
        stat = path.lstat()
        content = (
            os.readlink(path)
            if path.is_symlink()
            else sha256(path.read_bytes()).hexdigest()
            if path.is_file()
            else "directory"
        )
        result[str(path.relative_to(root))] = (stat.st_ino, stat.st_mtime_ns, content)
    return result


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(
    "surface", ["app/functions", "tests", "function_app.py", "app/functions/__init__.py"]
)
def test_cli_refuses_escape_without_any_mutation(tmp_path: Path, kind: str, surface: str) -> None:
    root = scaffold_project("project", tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    target = root / surface
    if target.is_dir():
        shutil.copytree(target, outside, dirs_exist_ok=True)
        shutil.rmtree(target)
        target.symlink_to(outside, target_is_directory=True)
    else:
        shutil.copyfile(target, outside / "registration.py")
        target.unlink()
        target.symlink_to(outside / "registration.py")
    (outside / "sentinel").write_text("unchanged")
    before = inventory(root), inventory(outside)
    result = subprocess.run(command(kind, root), capture_output=True, text=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert (inventory(root), inventory(outside)) == before


@pytest.mark.parametrize(
    "surface",
    [
        "app/schemas",
        "app/services",
        "host.json",
        "pyproject.toml",
        "requirements.txt",
        "local.settings.json.example",
    ],
)
def test_resource_and_configuration_escape_preflight(tmp_path: Path, surface: str) -> None:
    root = scaffold_project("project", tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    path = root / surface
    if path.is_dir():
        shutil.rmtree(path)
        path.symlink_to(outside, target_is_directory=True)
    else:
        shutil.copyfile(path, outside / "data")
        path.unlink()
        path.symlink_to(outside / "data")
    before = inventory(root), inventory(outside)
    result = subprocess.run(
        command("resource" if surface.startswith("app/") else "durable", root),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert (inventory(root), inventory(outside)) == before


@pytest.mark.parametrize("loop", [False, True])
def test_expansion_unresolvable_links_are_user_errors(tmp_path: Path, loop: bool) -> None:
    root = scaffold_project("project", tmp_path)
    path = root / "tests"
    shutil.rmtree(path)
    path.symlink_to(path if loop else tmp_path / "missing", target_is_directory=True)
    before = inventory(root)
    result = subprocess.run(command("timer", root), capture_output=True, text=True)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert inventory(root) == before


def test_scaffold_loop_is_user_error_without_mutation(tmp_path: Path) -> None:
    root = scaffold_project("project", tmp_path)
    path = root / "README.md"
    path.unlink()
    path.symlink_to(path)
    before = inventory(root)
    result = subprocess.run(
        [
            str(Path(sys.executable).parent / "afs"),
            "advanced",
            "new",
            "project",
            "--destination",
            str(tmp_path),
            "--overwrite",
            "--yes",
            "--no-git",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert inventory(root) == before


@pytest.mark.parametrize("kind", KINDS)
def test_cli_supports_canonical_alias_relative_root_and_internal_links(
    tmp_path: Path, kind: str
) -> None:
    root = scaffold_project("project", tmp_path)
    functions = root / "app/functions"
    functions.rename(root / "internal-functions")
    functions.symlink_to(root / "internal-functions", target_is_directory=True)
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    result = subprocess.run(
        command(kind, alias / "project/../project"), capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    before = inventory(root)
    repeated = subprocess.run(command(kind, root), capture_output=True, text=True)
    assert repeated.returncode == 1
    assert inventory(root) == before


@pytest.mark.parametrize("kind", KINDS)
def test_normal_expansion_output_matches_main(tmp_path: Path, kind: str) -> None:
    root = scaffold_project("project", tmp_path)
    before = {
        p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }
    result = subprocess.run(command(kind, root), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    changed = {
        p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file() and before.get(p.relative_to(root).as_posix()) != p.read_bytes()
    }
    golden = json.loads(
        (Path(__file__).parent / "fixtures/expansion-main-f8a45fa.json").read_text()
    )
    assert sha256(json.dumps(changed, sort_keys=True).encode()).hexdigest() == golden[kind]
