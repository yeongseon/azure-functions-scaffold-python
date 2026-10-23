"""Atomic multi-file write path with rollback for scaffold generators."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import tempfile

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.filesystem import preflight_paths

logger = logging.getLogger(__name__)


@dataclass
class _PendingWrite:
    path: Path
    new_content: str
    original_content: str | None
    created_parent: Path | None = None


def _atomic_write(path: Path, content: str) -> None:
    """Write *content* to *path* without ever exposing a partially written
    destination (#408).

    The new content is staged in a temp file in the same directory, flushed
    and fsynced, then committed with a single ``os.replace()`` -- which is
    atomic on the same filesystem. If staging fails partway through (e.g. a
    disk-full error), only the disposable temp file is affected; the real
    destination is never touched, so there is nothing to roll back for this
    entry specifically.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def _commit_pending_writes(
    writes: list[_PendingWrite], *, project_root: Path | None = None
) -> None:
    if project_root is not None:
        preflight_paths(project_root, (write.path for write in writes))
    written: list[_PendingWrite] = []
    try:
        for write in writes:
            _atomic_write(write.path, write.new_content)
            written.append(write)
    except Exception as exc:
        rollback_failures: list[Path] = []
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
                    _atomic_write(write.path, write.original_content)
            except OSError:
                rollback_failures.append(write.path)
                logger.exception("Rollback failed for %s", write.path)
        if rollback_failures:
            failed_paths = ", ".join(str(path) for path in rollback_failures)
            raise ScaffoldError(
                f"Atomic write failed and rollback was incomplete; failed paths: {failed_paths}"
            ) from exc
        raise ScaffoldError(
            f"Atomic write failed; rolled back {len(written)} file(s): {exc}"
        ) from exc
