from __future__ import annotations

import tomllib

from azure_functions_scaffold.errors import ScaffoldError


def _compute_updated_pyproject_dependency(content: str, dependency: str) -> str | None:
    if f'"{dependency}"' in content:
        return None

    lines = content.splitlines(keepends=True)
    in_dependencies = False
    for index, line in enumerate(lines):
        if line.strip() == "dependencies = [":
            in_dependencies = True
            continue
        if in_dependencies and line.strip() == "]":
            lines.insert(index, f'  "{dependency}",\n')
            return "".join(lines)

    raise ScaffoldError("Cannot update pyproject.toml: project dependencies list was not found.")


def _compute_requirements_txt(pyproject_content: str) -> str:
    """Render deployment ``requirements.txt`` content from ``pyproject_content``'s
    direct ``[project].dependencies`` -- the same deterministic, sorted,
    direct-specifier format used by initial scaffolding (#410). Not a
    transitive lockfile: one line per declared direct dependency.
    """
    dependencies = tomllib.loads(pyproject_content)["project"]["dependencies"]
    return "".join(f"{dependency}\n" for dependency in sorted(dependencies, key=str.casefold))
