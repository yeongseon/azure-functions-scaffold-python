from __future__ import annotations

from pathlib import Path

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.scaffolder import scaffold_project


def test_destination_symlink_cannot_write_outside_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = tmp_path / "selected"
    destination.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ScaffoldError):
        scaffold_project("project", destination)
    assert list(outside.iterdir()) == []


def test_nested_symlink_does_not_modify_external_data(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "user.txt"
    sentinel.write_text("original")
    root = tmp_path / "selected"
    root.mkdir()
    target = root / "project"
    target.mkdir()
    (target / "app").symlink_to(outside, target_is_directory=True)
    scaffold_project("project", root, overwrite=True, yes=True)
    assert sentinel.read_text() == "original"
    assert list(outside.iterdir()) == [sentinel]


def test_nonempty_tree_requires_explicit_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()
    sentinel = target / "user.txt"
    sentinel.write_text("original")
    with pytest.raises(ScaffoldError):
        scaffold_project("project", tmp_path)
    assert sentinel.read_text() == "original"


def test_failed_publish_restores_tree_and_external_symlinks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "user.txt"
    sentinel.write_text("external")
    root = tmp_path / "selected"
    root.mkdir()
    target = root / "project"
    target.mkdir()
    (target / "user.txt").write_text("original")
    (target / "linked").symlink_to(outside, target_is_directory=True)
    replace = Path.replace

    def fail_publish(self: Path, destination: Path) -> Path:
        if self.name == "project" and self.parent.name.startswith(".project-"):
            raise OSError("injected publish failure")
        return replace(self, destination)

    monkeypatch.setattr(Path, "replace", fail_publish)
    with pytest.raises(OSError, match="injected"):
        scaffold_project("project", root, overwrite=True, yes=True)
    assert (target / "user.txt").read_text() == "original"
    assert (target / "linked").is_symlink()
    assert sentinel.read_text() == "external"
    assert list(outside.iterdir()) == [sentinel]
