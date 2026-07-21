"""Marker-based ``function_app.py`` registration updates."""

from __future__ import annotations

from pathlib import Path

from azure_functions_scaffold.errors import ScaffoldError

FUNCTION_IMPORT_MARKER = "# azure-functions-scaffold: function imports"
FUNCTION_REGISTRATION_MARKER = "# azure-functions-scaffold: function registrations"
LEGACY_FUNCTION_IMPORT_MARKER = "# azure-functions-scaffold-python: function imports"
LEGACY_FUNCTION_REGISTRATION_MARKER = "# azure-functions-scaffold-python: function registrations"


def _validate_function_app_updatable(
    function_app_path: Path,
    *,
    import_stmt: str,
    registration_stmt: str,
) -> None:
    """Pre-validate that function_app.py can be updated before writing files.

    Raises ScaffoldError if markers/anchors are missing or the function is
    already registered.  This must be called **before** creating any files so
    that a failure never leaves the project in a half-applied state.
    """
    content = function_app_path.read_text(encoding="utf-8")

    if import_stmt in content or registration_stmt in content:
        raise ScaffoldError("Function is already registered in function_app.py.")

    has_import_target = (
        FUNCTION_IMPORT_MARKER in content
        or LEGACY_FUNCTION_IMPORT_MARKER in content
        or "configure_logging()" in content
    )
    has_registration_target = (
        FUNCTION_REGISTRATION_MARKER in content
        or LEGACY_FUNCTION_REGISTRATION_MARKER in content
        or "app = func.FunctionApp()" in content
    )

    if not has_import_target:
        raise ScaffoldError(
            "Cannot update function_app.py: neither the import marker nor "
            "'configure_logging()' was found."
        )
    if not has_registration_target:
        raise ScaffoldError(
            "Cannot update function_app.py: neither the registration marker nor "
            "'app = func.FunctionApp()' was found."
        )


def _compute_updated_function_app(
    content: str,
    *,
    import_stmt: str,
    registration_stmt: str,
) -> str:
    if import_stmt in content or registration_stmt in content:
        raise ScaffoldError("Function is already registered in function_app.py.")

    updated = _insert_near_marker(
        content,
        marker=FUNCTION_IMPORT_MARKER,
        line=import_stmt,
        fallback_anchor="configure_logging()",
    )
    return _insert_near_marker(
        updated,
        marker=FUNCTION_REGISTRATION_MARKER,
        line=registration_stmt,
        fallback_anchor="app = func.FunctionApp()",
        after_anchor=True,
    )


def _insert_near_marker(
    content: str,
    *,
    marker: str,
    line: str,
    fallback_anchor: str,
    after_anchor: bool = False,
) -> str:
    legacy_marker = _legacy_marker_for(marker)
    target_marker = marker

    if target_marker not in content and legacy_marker is not None and legacy_marker in content:
        target_marker = legacy_marker

    if target_marker in content:
        # Insert new import before the blank line that separates imports from
        # the marker comment, keeping all imports in one contiguous block.
        blank_then_marker = f"\n\n{target_marker}"
        if blank_then_marker in content:
            updated = content.replace(blank_then_marker, f"\n{line}\n\n{target_marker}", 1)
        else:
            updated = content.replace(target_marker, f"{line}\n{target_marker}", 1)
        if marker == FUNCTION_IMPORT_MARKER or marker == LEGACY_FUNCTION_IMPORT_MARKER:
            updated = _sort_app_functions_imports(updated, target_marker)
        return updated

    if fallback_anchor not in content:
        raise ScaffoldError(
            f"Could not update function_app.py because '{fallback_anchor}' was not found."
        )

    if after_anchor:
        return content.replace(fallback_anchor, f"{fallback_anchor}\n{line}", 1)

    return content.replace(fallback_anchor, f"{line}\n\n{fallback_anchor}", 1)


def _sort_app_functions_imports(content: str, marker: str) -> str:
    """Sort the contiguous ``from app.functions.* import ...`` block alphabetically.

    Ruff's ``I001`` rule requires imports within the same isort section to be
    sorted. New entries are appended in insertion order, so we re-sort the
    contiguous run that ends just before the import marker. Only ``app.functions.*``
    lines are reordered; surrounding imports keep their original positions.
    """

    lines = content.split("\n")
    marker_index = next((i for i, ln in enumerate(lines) if ln.strip() == marker), -1)
    if marker_index <= 0:
        return content

    # Walk backwards from the marker, skipping the blank line that separates
    # imports from the marker, then collect the contiguous app.functions.* run.
    end = marker_index
    while end > 0 and lines[end - 1].strip() == "":
        end -= 1
    start = end
    while start > 0 and lines[start - 1].startswith("from app.functions."):
        start -= 1
    if end - start < 2:
        return content

    block = lines[start:end]
    sorted_block = sorted(block)
    if block == sorted_block:
        return content
    lines[start:end] = sorted_block
    return "\n".join(lines)


def _legacy_marker_for(marker: str) -> str | None:
    if marker == FUNCTION_IMPORT_MARKER:
        return LEGACY_FUNCTION_IMPORT_MARKER
    if marker == FUNCTION_REGISTRATION_MARKER:
        return LEGACY_FUNCTION_REGISTRATION_MARKER
    return None
