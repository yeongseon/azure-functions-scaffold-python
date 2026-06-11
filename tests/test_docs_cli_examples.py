"""Regression test: docs CLI examples must not drift from current CLI surface.

Top-level ``afs new`` no longer accepts ``--template``, ``--preset``,
``--with-*``, or ``--interactive`` (issue #112). It is the shortcut for
``afs api new`` (HTTP only). Trigger-specific scaffolding lives under
``afs worker <type>``, ``afs ai agent``, or ``afs advanced new``, and no
interactive wizard currently ships with the CLI.

The legacy ``azure-functions-scaffold-python`` distribution entry-point was
renamed to ``azure-functions-scaffold`` (CLI: ``afs``). It must not appear in
docs except inside the migration guide that explains the rename.

These checks normalize shell line-continuations (``\\\\\\n``) before scanning
so that multi-line code blocks are validated the same way as single-line ones.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

# Collapse shell line-continuations (``\`` followed by newline + indent) into a
# single space so multi-line examples are scanned identically to single-line.
LINE_CONTINUATION_RE = re.compile(r"\\\s*\n\s*")

# Flags that no longer belong on top-level ``afs new`` (issue #112).
TOP_LEVEL_AFS_NEW_RE = re.compile(
    r"\bafs\s+new\b[^\n]*"
    r"--(template|preset|with-openapi|with-validation|with-doctor|interactive)\b"
)

LEGACY_NEW_RE = re.compile(r"\bazure-functions-scaffold-python\s+new\b")

# Files that intentionally retain historical CLI examples (e.g. migration
# guides explaining the rename). Paths are relative to the repo root.
ALLOWLIST: frozenset[Path] = frozenset(
    {
        Path("docs/migration/0.6.0.md"),
    }
)


def _docs_files() -> list[Path]:
    return sorted(p for p in DOCS_ROOT.rglob("*.md") if p.is_file())


def _relative(path: Path) -> Path:
    return path.relative_to(REPO_ROOT)


def _normalized_text(path: Path) -> str:
    return LINE_CONTINUATION_RE.sub(" ", path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "doc_path",
    _docs_files(),
    ids=lambda p: str(_relative(p)),
)
def test_no_stale_top_level_afs_new_flags(doc_path: Path) -> None:
    relative = _relative(doc_path)
    if relative in ALLOWLIST:
        pytest.skip(f"intentional historical content: {relative}")
    text = _normalized_text(doc_path)
    snippets = [match.group(0) for match in TOP_LEVEL_AFS_NEW_RE.finditer(text)]
    assert not snippets, (
        f"{relative}: top-level `afs new` no longer accepts "
        "--template/--preset/--with-*/--interactive. Use `afs advanced new ...`, "
        "`afs worker <type>`, or `afs ai agent` instead.\n" + "\n".join(snippets)
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
    text = _normalized_text(doc_path)
    snippets = [match.group(0) for match in LEGACY_NEW_RE.finditer(text)]
    assert not snippets, (
        f"{relative}: `azure-functions-scaffold-python` is no longer a valid "
        "CLI entry; use `afs` or `azure-functions-scaffold` instead.\n" + "\n".join(snippets)
    )
