"""Atomic multi-file write path with rollback for scaffold generators."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path

from azure_functions_scaffold.errors import ScaffoldError

logger = logging.getLogger(__name__)


@dataclass
class _PendingWrite:
    path: Path
    new_content: str
    original_content: str | None
    created_parent: Path | None = None


def _commit_pending_writes(writes: list[_PendingWrite]) -> None:
    written: list[_PendingWrite] = []
    try:
        for write in writes:
            write.path.parent.mkdir(parents=True, exist_ok=True)
            write.path.write_text(write.new_content, encoding="utf-8")
            written.append(write)
    except Exception as exc:
        for write in reversed(written):
            try:
                if write.original_content is None:
                    if write.path.exists():
                        write.path.unlink()
                    if (
                        write.created_parent is not None
                        and write.created_parent.exists()
                        and not any(write.created_parent.iterdir())
                    ):
                        write.created_parent.rmdir()
                else:
                    write.path.write_text(write.original_content, encoding="utf-8")
            except OSError:
                logger.exception("Rollback failed for %s", write.path)
        raise ScaffoldError(
            f"Atomic write failed; rolled back {len(written)} file(s): {exc}"
        ) from exc
