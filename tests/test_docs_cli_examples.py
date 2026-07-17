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
    r"\b(?:afs|azure-functions-scaffold)\s+new\b[^\n]*"
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


class TestTopLevelAfsNewRegex:
    """Unit tests for :data:`TOP_LEVEL_AFS_NEW_RE` covering both CLI aliases."""

    def test_matches_short_alias_with_drifted_flag(self) -> None:
        """``afs new`` + a drifted flag still triggers the regex."""
        assert TOP_LEVEL_AFS_NEW_RE.search(
            "afs new my-api --template http"
        ) is not None

    def test_matches_long_alias_with_drifted_flag(self) -> None:
        """``azure-functions-scaffold new`` + a drifted flag also triggers."""
        assert TOP_LEVEL_AFS_NEW_RE.search(
            "azure-functions-scaffold new my-api --template http"
        ) is not None

    def test_matches_long_alias_with_interactive_flag(self) -> None:
        """``--interactive`` on the long alias also triggers."""
        assert TOP_LEVEL_AFS_NEW_RE.search(
            "azure-functions-scaffold new my-api --interactive"
        ) is not None

    def test_ignores_short_alias_advanced_new(self) -> None:
        """``afs advanced new`` with drifted flag is a valid, current CLI shape."""
        assert TOP_LEVEL_AFS_NEW_RE.search(
            "afs advanced new my-api --template http"
        ) is None

    def test_ignores_long_alias_advanced_new(self) -> None:
        """``azure-functions-scaffold advanced new`` is a valid, current CLI shape."""
        assert TOP_LEVEL_AFS_NEW_RE.search(
            "azure-functions-scaffold advanced new my-api --template http"
        ) is None

    def test_ignores_legacy_scaffold_python_distribution(self) -> None:
        """``azure-functions-scaffold-python new`` must be caught by LEGACY_NEW_RE,
        not TOP_LEVEL_AFS_NEW_RE. The two regexes must remain distinct.
        """
        text = "azure-functions-scaffold-python new my-api --template http"
        assert TOP_LEVEL_AFS_NEW_RE.search(text) is None
        assert LEGACY_NEW_RE.search(text) is not None

    def test_ignores_bare_afs_new_without_drifted_flags(self) -> None:
        """Current, correct ``afs new`` invocations must not trip the regex."""
        assert TOP_LEVEL_AFS_NEW_RE.search("afs new my-api") is None
        assert TOP_LEVEL_AFS_NEW_RE.search(
            "azure-functions-scaffold new my-api"
        ) is None


CLI_REFERENCE = DOCS_ROOT / "reference" / "cli.md"


def _cli_reference_text() -> str:
    return CLI_REFERENCE.read_text(encoding="utf-8")


def _iter_command_paths() -> list[str]:
    """Return every implemented command path from the live Typer app tree.

    Walks the top-level app plus every registered sub-group so the set reflects
    the real command surface (``api new``, ``worker timer``, ``advanced add`` ...).
    Deprecated shims are excluded — they are documented separately.
    """
    from azure_functions_scaffold.cli import app

    paths: list[str] = []

    def _walk(typer_app: object, prefix: str) -> None:
        for command in getattr(typer_app, "registered_commands", []):
            if getattr(command, "deprecated", False):
                continue
            name = command.name or command.callback.__name__.replace("_", "-")
            paths.append(f"{prefix}{name}".strip())
        for group in getattr(typer_app, "registered_groups", []):
            _walk(group.typer_instance, f"{prefix}{group.name} ")

    _walk(app, "")
    return sorted(set(paths))


# Flags that the CLI reference must document (implemented across the command groups).
REQUIRED_FLAGS: frozenset[str] = frozenset(
    {
        "--destination",
        "--python-version",
        "--github-actions",
        "--git",
        "--azd",
        "--dry-run",
        "--overwrite",
        "--yes",
        "--template",
        "--preset",
        "--with-openapi",
        "--with-validation",
        "--with-doctor",
        "--project-root",
        "--version",
    }
)


class TestCliReferenceCoverage:
    """Guard: ``docs/reference/cli.md`` must cover the implemented command surface."""

    @pytest.mark.parametrize("command_path", _iter_command_paths())
    def test_every_command_group_is_documented(self, command_path: str) -> None:
        """Each non-deprecated command (e.g. ``api new``) must appear in the reference."""
        text = _cli_reference_text()
        assert command_path in text, (
            f"docs/reference/cli.md does not document the `afs {command_path}` command. "
            "Update the CLI reference when the command surface changes."
        )

    @pytest.mark.parametrize("flag", sorted(REQUIRED_FLAGS))
    def test_every_implemented_flag_is_documented(self, flag: str) -> None:
        """Each implemented CLI flag must be documented in the reference."""
        text = _cli_reference_text()
        assert flag in text, (
            f"docs/reference/cli.md does not document the `{flag}` flag. "
            "Update the CLI reference when flags change."
        )
