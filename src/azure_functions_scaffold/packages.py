"""Single source of truth for Azure Functions DX-toolkit dependency floors.

The scaffolder and every generated ``pyproject.toml`` derive their toolkit
dependency pins from :data:`SUPPORTED_PACKAGES` so a version bump happens in
exactly one place instead of drifting across the root project and each
template.
"""

from __future__ import annotations

# Mapping of toolkit package name -> PEP 508 version specifier.
# Keep this in sync with the smoke-test dependency floors in the root
# ``pyproject.toml``; ``tests/test_supported_packages.py`` fails CI on drift.
SUPPORTED_PACKAGES: dict[str, str] = {
    "azure-functions": ">=1.23.0",
    "azure-functions-logging": ">=0.5.0",
    "azure-functions-openapi": ">=0.17.0",
    "azure-functions-validation": ">=0.7.0",
    "azure-functions-doctor": ">=0.16.0",
    "azure-functions-durable": ">=1.2.9",
    "azure-functions-langgraph": ">=0.5.1",
}


def requirement(name: str) -> str:
    """Return the full PEP 508 requirement string for a supported package.

    Example: ``requirement("azure-functions")`` -> ``"azure-functions>=1.23.0"``.
    """
    return f"{name}{SUPPORTED_PACKAGES[name]}"
