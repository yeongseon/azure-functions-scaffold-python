from collections.abc import Iterable
from pathlib import Path

from azure_functions_scaffold.errors import ScaffoldError


def resolve_path(path: Path) -> Path:
    try:
        return path.resolve()
    except (RuntimeError, OSError) as error:
        raise ScaffoldError(f"Cannot resolve selected project path: {path}") from error


def preflight_paths(root: Path, paths: Iterable[Path]) -> None:
    for path in paths:
        resolved = resolve_path(path)
        if not resolved.is_relative_to(root):
            raise ScaffoldError(f"Path escapes the selected project root: {path}")
        for component in (path, *path.parents):
            if component == root:
                break
            if component.is_symlink() and not component.exists():
                raise ScaffoldError(
                    f"Selected project path is a dangling symbolic link: {component}"
                )


def expansion_root(project_root: Path) -> Path:
    root = resolve_path(project_root)
    preflight_paths(
        root,
        (
            root / name
            for name in (
                "app/functions",
                "app/functions/__init__.py",
                "app/services",
                "app/schemas",
                "tests",
                "function_app.py",
                "host.json",
                "pyproject.toml",
                "requirements.txt",
                "local.settings.json.example",
            )
        ),
    )
    return root
