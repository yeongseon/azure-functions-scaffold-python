from pathlib import Path
import subprocess
import sys

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.scaffolder import scaffold_project


@pytest.mark.parametrize("chain", [False, True])
def test_real_cli_accepts_destination_below_symlinked_ancestors(
    tmp_path: Path, chain: bool
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    if chain:
        second = tmp_path / "second"
        second.symlink_to(alias, target_is_directory=True)
        alias = second
    result = subprocess.run(
        [
            str(Path(sys.executable).parent / "afs"),
            "advanced",
            "new",
            "project",
            "--destination",
            str(alias / "selected"),
            "--no-git",
            "--no-github-actions",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (real / "selected/project/function_app.py").is_file()


def test_selected_destination_symlink_is_an_explicit_root_alias(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    assert scaffold_project("project", alias) == real / "project"


def test_relative_parent_segments_are_canonicalized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "nested").mkdir()
    monkeypatch.chdir(tmp_path / "nested")
    root = scaffold_project("project", Path("../selected/../selected"))
    assert root == tmp_path / "selected/project"


def test_project_directory_symlink_cannot_redirect_publication(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "keep"
    sentinel.write_text("original")
    (tmp_path / "project").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ScaffoldError):
        scaffold_project("project", tmp_path, overwrite=True, yes=True)
    assert sentinel.read_text() == "original"
