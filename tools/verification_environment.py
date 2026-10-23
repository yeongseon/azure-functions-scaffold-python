from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
import shutil
import sys


def doctor() -> int:
    missing = not (3, 11) <= sys.version_info[:2] < (3, 15)
    print(f"Python: {sys.version.split()[0]} required >=3.11,<3.15")
    for module in ("pytest", "pytest_cov", "ruff", "mypy", "build", "mkdocs", "bandit"):
        present = find_spec(module) is not None
        print(f"{module}: {'available' if present else 'MISSING'} (required for check/test/verify)")
        missing |= not present
    for tool in ("git", "make", "func", "azurite"):
        present = shutil.which(tool) is not None
        target = "integration/verify" if tool in {"func", "azurite"} else "check"
        print(f"{tool}: {'available' if present else 'MISSING'} (required for {target})")
        missing |= not present
    if missing:
        print(
            "development environment not created: run make install "
            "(or install missing prerequisites)"
        )
    return int(missing)


def clean(root: Path) -> None:
    for name in (
        "test-results",
        "dist",
        "build",
        "site",
        "htmlcov",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    ):
        shutil.rmtree(root / name, ignore_errors=True)
    for pattern in (".coverage*", "coverage.xml", "*.egg-info"):
        for path in root.glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    for path in root.rglob("__pycache__"):
        if not any(part in {".git", ".venv", "venv", "env"} for part in path.parts):
            shutil.rmtree(path)
