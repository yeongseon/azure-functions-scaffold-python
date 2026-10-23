from pathlib import Path

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.filesystem import preflight_paths, resolve_path


@pytest.mark.parametrize("error", [OSError("unreadable"), RuntimeError("loop")])
def test_resolution_failure_becomes_scaffold_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def fail(path: Path, strict: bool = False) -> Path:
        raise error

    monkeypatch.setattr(Path, "resolve", fail)
    with pytest.raises(ScaffoldError, match="Cannot resolve selected project path"):
        resolve_path(tmp_path)


def test_dangling_internal_target_is_refused(tmp_path: Path) -> None:
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "missing")
    with pytest.raises(ScaffoldError, match="dangling"):
        preflight_paths(tmp_path, [link / "child.py"])
