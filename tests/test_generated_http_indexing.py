from __future__ import annotations

import inspect
from pathlib import Path
import sys
import typing

import azure.functions as func

from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_generated_http_functions_expose_resolvable_worker_type_hints(tmp_path: Path) -> None:
    # Given: a strict HTTP project generated with every default integration.
    project_root = scaffold_project(
        project_name="worker-indexing",
        destination=tmp_path,
        template_name="http",
        options=build_project_options(
            preset_name="strict",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
            include_openapi=True,
            include_validation=True,
            include_doctor=True,
        ),
    )
    sys.path.insert(0, str(project_root))
    try:
        import function_app

        functions = function_app.app.get_functions()

        # When: the worker resolves every indexed handler's annotations.
        hints = [typing.get_type_hints(function.get_user_function()) for function in functions]
    finally:
        sys.path.pop(0)
        for module_name in list(sys.modules):
            if (
                module_name == "app"
                or module_name.startswith("app.")
                or module_name == "function_app"
            ):
                del sys.modules[module_name]

    # Then: all five handlers produce serialized input and return metadata.
    assert len(hints) == 5
    assert all("return" in function_hints for function_hints in hints)
    assert all(
        function_hints.get("context") is not func.Context
        or inspect.signature(function.get_user_function()).parameters["context"].default
        is inspect.Parameter.empty
        for function, function_hints in zip(functions, hints, strict=True)
    )
