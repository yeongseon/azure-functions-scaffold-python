"""Keep the literal test paths in the testing guides in step with the tree (#496)."""

from __future__ import annotations

import ast
from pathlib import Path
import re

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDES = (
    REPO_ROOT / "docs" / "testing.md",
    REPO_ROOT / "docs" / "contributing" / "testing.md",
)
# ``tests/<path>.py`` optionally followed by ``::test_name``; a trailing ``[param]`` is ignored.
TEST_REF_RE = re.compile(r"\btests/([A-Za-z0-9_./-]+\.py)(?:::(test_[A-Za-z0-9_]+))?")


def _references() -> list[tuple[Path, str, str | None]]:
    found: set[tuple[Path, str, str | None]] = set()
    for guide in GUIDES:
        for match in TEST_REF_RE.finditer(guide.read_text(encoding="utf-8")):
            found.add((guide.relative_to(REPO_ROOT), match.group(1), match.group(2)))
    return sorted(found, key=lambda ref: (str(ref[0]), ref[1], ref[2] or ""))


REFERENCES = _references()


def test_guides_reference_test_files() -> None:
    assert REFERENCES, "the testing guides no longer name any tests/ path"


@pytest.mark.parametrize(("guide", "path", "function"), REFERENCES)
def test_documented_test_path_exists(guide: Path, path: str, function: str | None) -> None:
    target = REPO_ROOT / "tests" / path
    assert target.is_file(), f"{guide} references missing test file tests/{path}"
    if function is not None:
        names = {
            node.name
            for node in ast.walk(ast.parse(target.read_text(encoding="utf-8")))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert function in names, f"{guide} references missing test {path}::{function}"


def test_documented_make_targets_exist() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    text = GUIDES[0].read_text(encoding="utf-8")
    for target in ("security-host", "e2e-azure"):
        assert f"`make {target}`" in text
        assert re.search(rf"^{re.escape(target)}:", makefile, re.MULTILINE), target


def test_documented_ci_host_job_exists() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "ci-test.yml").read_text(encoding="utf-8")
    assert "`generated-host-smoke`" in GUIDES[0].read_text(encoding="utf-8")
    assert re.search(r"^  generated-host-smoke:", workflow, re.MULTILINE)
