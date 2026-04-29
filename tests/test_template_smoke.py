from __future__ import annotations

import ast
import importlib
import json
import os
from pathlib import Path
import subprocess
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


@pytest.mark.slow
def test_rendered_strict_http_project_tests_pass(tmp_path: Path) -> None:
    """Scaffold a strict HTTP project and run its generated tests."""
    options = build_project_options(
        preset_name="strict",
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
        include_openapi=True,
        include_validation=True,
        include_doctor=True,
    )
    project_root = scaffold_project(
        project_name="smoke-strict",
        destination=tmp_path,
        template_name="http",
        options=options,
    )

    # Run the generated project's own tests using the current interpreter.
    # All runtime deps (azure-functions, pydantic, etc.) are already installed.
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q", str(project_root / "tests")],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "WEBHOOK_SECRET": "test-secret-key",
            "PYTHONPATH": os.pathsep.join(
                filter(None, [str(project_root), os.environ.get("PYTHONPATH", "")])
            ),
        },
    )
    assert result.returncode == 0, (
        f"Generated project tests failed (rc={result.returncode}):\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


@pytest.mark.slow
def test_rendered_standard_http_project_tests_pass(tmp_path: Path) -> None:
    """Scaffold a standard HTTP project (no openapi/validation) and run its generated tests."""
    options = build_project_options(
        preset_name="standard",
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
        include_openapi=False,
        include_validation=False,
        include_doctor=False,
    )
    project_root = scaffold_project(
        project_name="smoke-standard",
        destination=tmp_path,
        template_name="http",
        options=options,
    )

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q", str(project_root / "tests")],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "WEBHOOK_SECRET": "test-secret-key",
            "PYTHONPATH": os.pathsep.join(
                filter(None, [str(project_root), os.environ.get("PYTHONPATH", "")])
            ),
        },
    )
    assert result.returncode == 0, (
        f"Generated project tests failed (rc={result.returncode}):\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_rendered_http_webhook_returns_503_when_secret_missing(tmp_path: Path) -> None:
    options = build_project_options(
        preset_name="standard",
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
        include_openapi=False,
        include_validation=False,
        include_doctor=False,
    )
    project_root = scaffold_project(
        project_name="webhook-secret-missing",
        destination=tmp_path,
        template_name="http",
        options=options,
    )

    sys.path.insert(0, str(project_root))
    try:
        from app.functions.webhooks import receive_webhook
        import azure.functions as func

        request = func.HttpRequest(
            method="POST",
            url="http://localhost/api/webhooks/inbound",
            params={},
            body=json.dumps({"event_type": "ping", "source": "test"}).encode(),
            route_params={},
            headers={"Content-Type": "application/json"},
        )

        original_secret = os.environ.pop("WEBHOOK_SECRET", None)
        try:
            response = receive_webhook(request)
        finally:
            if original_secret is not None:
                os.environ["WEBHOOK_SECRET"] = original_secret
    finally:
        sys.path.pop(0)
        for module_name in list(sys.modules):
            if module_name == "app" or module_name.startswith("app."):
                del sys.modules[module_name]

    assert response.status_code == 503
    assert json.loads(response.get_body()) == {"error": "Webhook signing secret not configured"}


def test_rendered_http_webhook_returns_401_for_unsigned_payload_when_secret_set(
    tmp_path: Path,
) -> None:
    options = build_project_options(
        preset_name="standard",
        python_version="3.10",
        include_github_actions=False,
        initialize_git=False,
        include_openapi=False,
        include_validation=False,
        include_doctor=False,
    )
    project_root = scaffold_project(
        project_name="webhook-secret-set",
        destination=tmp_path,
        template_name="http",
        options=options,
    )

    sys.path.insert(0, str(project_root))
    try:
        from app.functions.webhooks import receive_webhook
        import azure.functions as func

        payload = json.dumps({"event_type": "ping", "source": "test"}).encode()
        request = func.HttpRequest(
            method="POST",
            url="http://localhost/api/webhooks/inbound",
            params={},
            body=payload,
            route_params={},
            headers={"Content-Type": "application/json", "X-Signature": ""},
        )

        original_secret = os.environ.get("WEBHOOK_SECRET")
        os.environ["WEBHOOK_SECRET"] = "test-secret-key"
        try:
            response = receive_webhook(request)
        finally:
            if original_secret is None:
                del os.environ["WEBHOOK_SECRET"]
            else:
                os.environ["WEBHOOK_SECRET"] = original_secret
    finally:
        sys.path.pop(0)
        for module_name in list(sys.modules):
            if module_name == "app" or module_name.startswith("app."):
                del sys.modules[module_name]

    assert response.status_code == 401
