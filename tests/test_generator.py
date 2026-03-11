from __future__ import annotations

import json
from pathlib import Path

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator import add_function
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_add_function_rejects_unknown_trigger(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    with pytest.raises(ScaffoldError, match="Unsupported trigger"):
        add_function(project_root=project_root, trigger="durable", function_name="sync-data")


def test_add_function_rejects_non_scaffold_project(tmp_path: Path) -> None:
    project_root = tmp_path / "not-a-project"
    project_root.mkdir()

    with pytest.raises(
        ScaffoldError,
        match="does not look like a scaffolded Azure Functions project",
    ):
        add_function(project_root=project_root, trigger="http", function_name="sync-data")


def test_add_function_rejects_missing_project_root(tmp_path: Path) -> None:
    with pytest.raises(ScaffoldError, match="Project root does not exist"):
        add_function(
            project_root=tmp_path / "missing",
            trigger="http",
            function_name="sync-data",
        )


def test_add_function_rejects_file_project_root(tmp_path: Path) -> None:
    project_root = tmp_path / "project.txt"
    project_root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(ScaffoldError, match="Project root must be a directory"):
        add_function(
            project_root=project_root,
            trigger="http",
            function_name="sync-data",
        )


@pytest.mark.parametrize("function_name", ["", "***", "123-sync"])
def test_add_function_rejects_invalid_names(tmp_path: Path, function_name: str) -> None:
    project_root = scaffold_project("sample", tmp_path)

    with pytest.raises(ScaffoldError):
        add_function(project_root=project_root, trigger="http", function_name=function_name)


def test_add_function_rejects_existing_module(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_function(project_root=project_root, trigger="http", function_name="sync-data")

    with pytest.raises(ScaffoldError, match="Function module already exists"):
        add_function(project_root=project_root, trigger="http", function_name="sync-data")


def test_add_function_rejects_uneditable_function_app(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    function_app_path.write_text("import azure.functions as func\n", encoding="utf-8")

    with pytest.raises(ScaffoldError, match="Could not update function_app.py"):
        add_function(project_root=project_root, trigger="http", function_name="sync-data")


def test_add_function_can_skip_test_generation_for_minimal_preset(tmp_path: Path) -> None:
    project_root = scaffold_project(
        "sample",
        tmp_path,
        options=build_project_options(
            preset_name="minimal",
            python_version="3.10",
            include_github_actions=False,
            initialize_git=False,
        ),
    )

    function_path = add_function(
        project_root=project_root,
        trigger="http",
        function_name="sync-data",
    )

    assert function_path == project_root / "app/functions/sync_data.py"
    assert not (project_root / "tests/test_sync_data.py").exists()


@pytest.mark.parametrize(
    ("trigger", "function_name"),
    [
        ("queue", "sync-data"),
        ("blob", "ingest-reports"),
        ("servicebus", "process-events"),
    ],
)
def test_add_function_supports_additional_triggers(
    tmp_path: Path,
    trigger: str,
    function_name: str,
) -> None:
    project_root = scaffold_project("sample", tmp_path)

    function_path = add_function(
        project_root=project_root,
        trigger=trigger,
        function_name=function_name,
    )

    normalized_name = function_name.replace("-", "_")
    assert function_path == project_root / f"app/functions/{normalized_name}.py"
    assert (project_root / f"tests/test_{normalized_name}.py").exists()


@pytest.mark.parametrize("trigger", ["queue", "blob", "servicebus"])
def test_add_function_adds_extension_bundle_for_binding_triggers(
    tmp_path: Path,
    trigger: str,
) -> None:
    project_root = scaffold_project("sample", tmp_path)

    add_function(
        project_root=project_root,
        trigger=trigger,
        function_name=f"{trigger}-handler",
    )

    host_config = json.loads((project_root / "host.json").read_text(encoding="utf-8"))
    assert host_config["extensionBundle"]["id"] == "Microsoft.Azure.Functions.ExtensionBundle"


def test_add_servicebus_function_updates_local_settings_example(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    add_function(
        project_root=project_root,
        trigger="servicebus",
        function_name="process-events",
    )

    local_settings = json.loads(
        (project_root / "local.settings.json.example").read_text(encoding="utf-8")
    )
    assert "ServiceBusConnection" in local_settings["Values"]
