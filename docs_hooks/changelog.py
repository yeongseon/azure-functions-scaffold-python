"""MkDocs hook: render the changelog page from the canonical root ``CHANGELOG.md``.

The docs site historically shipped a hand-maintained ``docs/changelog.md`` that drifted
behind the canonical ``CHANGELOG.md`` (git-cliff generated) at the repository root. This hook
overrides the source of the ``changelog.md`` page at build time so the published changelog is
always the canonical one, eliminating the drift by construction.

Registered via the ``hooks:`` key in ``mkdocs.yml``; requires no extra dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# The nav slug (relative to ``docs/``) whose content is replaced with canonical CHANGELOG.md.
_CHANGELOG_PAGE = "changelog.md"


def on_page_read_source(page: Any, config: Any, **_kwargs: Any) -> str | None:
    """Return canonical changelog text for the changelog page, else defer to disk.

    MkDocs calls this for every page; returning ``None`` lets MkDocs read the on-disk
    source as usual. For the changelog page we return the root ``CHANGELOG.md`` content.
    """
    if page.file.src_uri != _CHANGELOG_PAGE:
        return None

    repo_root = Path(config["docs_dir"]).resolve().parent
    canonical = repo_root / "CHANGELOG.md"
    if not canonical.is_file():
        return None
    return canonical.read_text(encoding="utf-8")
