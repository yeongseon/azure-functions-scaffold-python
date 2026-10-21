from __future__ import annotations

import tomllib

from azure_functions_scaffold.errors import ScaffoldError


def _compute_updated_pyproject_dependency(content: str, dependency: str) -> str | None:
    try:
        parsed = tomllib.loads(content)
    except tomllib.TOMLDecodeError as exc:
        raise ScaffoldError(f"Cannot update pyproject.toml: invalid TOML ({exc}).") from exc

    project_dependencies = parsed.get("project", {}).get("dependencies")
    if not isinstance(project_dependencies, list):
        raise ScaffoldError(
            "Cannot update pyproject.toml: project dependencies list was not found."
        )
    if dependency in project_dependencies:
        return None

    # Line-based edit, not a TOML rewrite, to preserve exact formatting,
    # comments, and key order elsewhere in the file. The target array must
    # be tracked by TOML TABLE, not by raw line content (#411): a valid
    # pyproject.toml can declare other tables (e.g. a Hatch environment)
    # with their own "dependencies = [" array before [project]'s, and the
    # SAME requirement string can legitimately appear in those other
    # tables without meaning it is already a declared runtime dependency.
    lines = content.splitlines(keepends=True)
    current_table: str | None = None
    in_project_dependencies = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and not stripped.startswith("[["):
            current_table = stripped[1:-1].strip()
            in_project_dependencies = False
            continue
        if current_table == "project" and stripped == "dependencies = [":
            in_project_dependencies = True
            continue
        if in_project_dependencies and stripped == "]":
            lines.insert(index, f'  "{dependency}",\n')
            return "".join(lines)

    raise ScaffoldError(
        "Cannot update pyproject.toml: [project].dependencies was not found in the "
        "expected multi-line array format."
    )


def _compute_requirements_txt(pyproject_content: str) -> str:
    """Render deployment ``requirements.txt`` content from ``pyproject_content``'s
    direct ``[project].dependencies`` -- the same deterministic, sorted,
    direct-specifier format used by initial scaffolding (#410). Not a
    transitive lockfile: one line per declared direct dependency.
    """
    dependencies = tomllib.loads(pyproject_content)["project"]["dependencies"]
    return "".join(f"{dependency}\n" for dependency in sorted(dependencies, key=str.casefold))
