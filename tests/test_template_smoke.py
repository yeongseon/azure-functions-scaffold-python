from __future__ import annotations

import ast
import importlib
from pathlib import Path
import sys
from typing import Callable, cast

import pytest

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def _load_pyproject(project_root: Path) -> dict[str, object]:
    parsed = _toml_loads((project_root / "pyproject.toml").read_text(encoding="utf-8"))
    return _as_string_key_dict(parsed)


def _toml_loads(content: str) -> object:
    version_info = sys.version_info
    module_name = "tomllib" if version_info >= (3, 11) else "tomli"
    module = importlib.import_module(module_name)
    loads = cast(Callable[[str], object], getattr(module, "loads"))
    return loads(content)


def _as_string_key_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    typed_value = cast(dict[object, object], value)
    result: dict[str, object] = {}
    for key, item in typed_value.items():
        assert isinstance(key, str)
        result[key] = item
    return result


def _as_string_list(value: object) -> list[str]:
    assert isinstance(value, list)
    typed_value = cast(list[object], value)
    result: list[str] = []
    for item in typed_value:
        assert isinstance(item, str)
        result.append(item)
    return result


def _get_sdist_includes(pyproject_data: dict[str, object]) -> list[str]:
    tool = _as_string_key_dict(pyproject_data["tool"])
    hatch = _as_string_key_dict(tool["hatch"])
    build = _as_string_key_dict(hatch["build"])
    targets = _as_string_key_dict(build["targets"])
    sdist = _as_string_key_dict(targets["sdist"])
    return _as_string_list(sdist["include"])


@pytest.mark.parametrize(
    (
        "template_name",
        "preset_name",
        "include_openapi",
        "include_validation",
        "include_doctor",
    ),
    [
        ("http", "strict", True, True, True),
        ("http", "standard", False, False, False),
        ("timer", "standard", False, False, False),
    ],
)
def test_scaffolded_templates_produce_parseable_python_and_toml(
    tmp_path: Path,
    template_name: str,
    preset_name: str,
    include_openapi: bool,
    include_validation: bool,
    include_doctor: bool,
) -> None:
    project_name = (
        f"{template_name}-{preset_name}-"
        f"openapi-{int(include_openapi)}-"
        f"validation-{int(include_validation)}-"
        f"doctor-{int(include_doctor)}"
    )
    options = build_project_options(
        preset_name=preset_name,
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
        include_openapi=include_openapi,
        include_validation=include_validation,
        include_doctor=include_doctor,
    )
    project_root = scaffold_project(
        project_name=project_name,
        destination=tmp_path,
        template_name=template_name,
        options=options,
    )

    python_files = sorted(project_root.rglob("*.py"))
    assert python_files
    for python_file in python_files:
        _ = ast.parse(python_file.read_text(encoding="utf-8"), filename=str(python_file))

    pyproject_data = _load_pyproject(project_root)
    assert isinstance(pyproject_data, dict)


@pytest.mark.parametrize(
    (
        "template_name",
        "preset_name",
        "include_openapi",
        "include_validation",
        "include_doctor",
    ),
    [
        ("http", "strict", True, True, True),
        ("timer", "standard", False, False, False),
    ],
)
def test_scaffolded_pyproject_sdist_includes_do_not_use_leading_slashes(
    tmp_path: Path,
    template_name: str,
    preset_name: str,
    include_openapi: bool,
    include_validation: bool,
    include_doctor: bool,
) -> None:
    project_name = (
        f"sdist-{template_name}-{preset_name}-"
        f"openapi-{int(include_openapi)}-"
        f"validation-{int(include_validation)}-"
        f"doctor-{int(include_doctor)}"
    )
    options = build_project_options(
        preset_name=preset_name,
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
        include_openapi=include_openapi,
        include_validation=include_validation,
        include_doctor=include_doctor,
    )
    project_root = scaffold_project(
        project_name=project_name,
        destination=tmp_path,
        template_name=template_name,
        options=options,
    )

    pyproject_data = _load_pyproject(project_root)
    sdist_includes = _get_sdist_includes(pyproject_data)
    assert all(not path.startswith("/") for path in sdist_includes)
