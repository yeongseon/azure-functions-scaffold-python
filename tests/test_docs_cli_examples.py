"""Regression test: docs CLI examples must not drift from current CLI surface.

Top-level ``afs new`` no longer accepts ``--template`` (issue #112). It is the
shortcut for ``afs api new`` (HTTP only). Trigger-specific scaffolding lives
under ``afs worker <type>``, ``afs ai agent``, or ``afs advanced new``.

The legacy ``azure-functions-scaffold-python`` distribution entry-point was
renamed to ``azure-functions-scaffold`` (CLI: ``afs``). It must not appear in
docs except inside the migration guide that explains the rename.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

TOP_LEVEL_TEMPLATE_RE = re.compile(r"\bafs\s+new\b[^\n]*--template\b")
LEGACY_NEW_RE = re.compile(r"\bazure-functions-scaffold-python\s+new\b")

ALLOWLIST: frozenset[Path] = frozenset(
    {
        Path("docs/migration/0.6.0.md"),
    }
)


def _docs_files() -> list[Path]:
    return sorted(p for p in DOCS_ROOT.rglob("*.md") if p.is_file())


def _relative(path: Path) -> Path:
    return path.relative_to(REPO_ROOT)


@pytest.mark.parametrize(
    "doc_path",
    _docs_files(),
    ids=lambda p: str(_relative(p)),
)
def test_no_stale_afs_new_template(doc_path: Path) -> None:
    relative = _relative(doc_path)
    if relative in ALLOWLIST:
        pytest.skip(f"intentional historical content: {relative}")
    text = doc_path.read_text(encoding="utf-8")
    matches = [
        f"{relative}:{idx + 1}: {line.rstrip()}"
        for idx, line in enumerate(text.splitlines())
        if TOP_LEVEL_TEMPLATE_RE.search(line)
    ]
    assert not matches, (
        "Top-level `afs new` no longer accepts `--template`. "
        + "Use `afs advanced new --template ...`, `afs worker <type>`, "
        + "or `afs ai agent` instead.\n"
        + "\n".join(matches)
    )


@pytest.mark.parametrize(
    "doc_path",
    _docs_files(),
    ids=lambda p: str(_relative(p)),
)
def test_no_legacy_scaffold_python_new(doc_path: Path) -> None:
    relative = _relative(doc_path)
    if relative in ALLOWLIST:
        pytest.skip(f"intentional historical content: {relative}")
    text = doc_path.read_text(encoding="utf-8")
    matches = [
        f"{relative}:{idx + 1}: {line.rstrip()}"
        for idx, line in enumerate(text.splitlines())
        if LEGACY_NEW_RE.search(line)
    ]
    assert not matches, (
        "`azure-functions-scaffold-python` is no longer a valid CLI entry; "
        + "use `afs` or `azure-functions-scaffold` instead.\n"
        + "\n".join(matches)
    )
