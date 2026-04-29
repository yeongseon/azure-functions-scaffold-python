from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator import (
    _derive_resource_names,
    _insert_near_marker,
    _render_function_module,
    _render_function_test,
    _update_function_app,
    add_function,
    add_resource,
    add_route,
    describe_add_function,
    describe_add_resource,
    describe_add_route,
)
from azure_functions_scaffold.scaffolder import scaffold_project
from azure_functions_scaffold.template_registry import build_project_options


def test_add_function_rejects_unknown_trigger(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    with pytest.raises(ScaffoldError, match="Unsupported trigger"):
        add_function(project_root=project_root, trigger="graphql", function_name="sync-data")


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

    with pytest.raises(ScaffoldError, match="Cannot update function_app.py"):
        add_function(project_root=project_root, trigger="http", function_name="sync-data")


def test_add_function_does_not_create_files_when_function_app_uneditable(tmp_path: Path) -> None:
    """Verify no files are left behind when function_app.py cannot be updated."""
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    function_app_path.write_text("import azure.functions as func\n", encoding="utf-8")

    with pytest.raises(ScaffoldError):
        add_function(project_root=project_root, trigger="http", function_name="orphan")

    assert not (project_root / "app/functions/orphan.py").exists()
    assert not (project_root / "tests/test_orphan.py").exists()


def test_add_function_works_with_legacy_marker(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    content = function_app_path.read_text(encoding="utf-8")
    content = content.replace(
        "# azure-functions-scaffold: function imports",
        "# azure-functions-scaffold-python: function imports",
    )
    content = content.replace(
        "# azure-functions-scaffold: function registrations",
        "# azure-functions-scaffold-python: function registrations",
    )
    function_app_path.write_text(content, encoding="utf-8")

    add_function(project_root=project_root, trigger="http", function_name="sync-data")

    updated = function_app_path.read_text(encoding="utf-8")
    assert "from app.functions.sync_data import sync_data_blueprint" in updated
    assert updated.index("from app.functions.sync_data import sync_data_blueprint") < updated.index(
        "# azure-functions-scaffold-python: function imports"
    )
    assert "app.register_functions(sync_data_blueprint)" in updated
def test_add_function_rolls_back_on_host_json_failure(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    original_function_app = function_app_path.read_text(encoding="utf-8")
    (project_root / "host.json").write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ScaffoldError, match="host.json"):
        add_function(project_root=project_root, trigger="queue", function_name="foo")

    assert not (project_root / "app/functions/foo.py").exists()
    assert not (project_root / "tests/test_foo.py").exists()
    assert function_app_path.read_text(encoding="utf-8") == original_function_app


def test_add_function_rolls_back_on_function_app_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    original_write_text = Path.write_text

    def failing_write_text(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
        if self == function_app_path:
            raise PermissionError("blocked")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", failing_write_text)

    with pytest.raises(ScaffoldError, match="Atomic write failed"):
        add_function(project_root=project_root, trigger="http", function_name="bar")

    assert not (project_root / "app/functions/bar.py").exists()
    assert not (project_root / "tests/test_bar.py").exists()


def test_describe_add_function_detects_malformed_host_json(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    (project_root / "host.json").write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ScaffoldError, match="host.json"):
        describe_add_function(project_root=project_root, trigger="queue", function_name="foo")


def test_add_function_succeeds_atomically_for_queue_trigger(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    function_path = add_function(project_root=project_root, trigger="queue", function_name="foo")

    test_path = project_root / "tests/test_foo.py"
    function_app_path = project_root / "function_app.py"
    host_json_path = project_root / "host.json"

    assert function_path == project_root / "app/functions/foo.py"
    assert function_path.exists()
    assert test_path.exists()

    ast.parse(function_path.read_text(encoding="utf-8"))
    ast.parse(test_path.read_text(encoding="utf-8"))
    ast.parse(function_app_path.read_text(encoding="utf-8"))
    json.loads(host_json_path.read_text(encoding="utf-8"))

    function_app_text = function_app_path.read_text(encoding="utf-8")
    assert "from app.functions.foo import foo_blueprint" in function_app_text
    assert "app.register_functions(foo_blueprint)" in function_app_text


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
        ("eventhub", "listen-events"),
        ("cosmosdb", "track-changes"),
        ("durable", "orchestrate-flow"),
        ("ai", "ask-question"),
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


def test_add_timer_function(tmp_path: Path) -> None:
    """Test adding a timer trigger function (tests lines 215, 452 - timer template)."""
    project_root = scaffold_project("sample", tmp_path)

    function_path = add_function(
        project_root=project_root,
        trigger="timer",
        function_name="schedule-task",
    )

    # Verify files were created
    assert function_path == project_root / "app/functions/schedule_task.py"
    assert (project_root / "tests/test_schedule_task.py").exists()

    # Verify function content contains timer-specific code
    func_content = function_path.read_text(encoding="utf-8")
    assert "schedule=" in func_content
    assert "past_due" in func_content

    # Verify test content contains timer-specific code
    test_content = (project_root / "tests/test_schedule_task.py").read_text(encoding="utf-8")
    assert "SimpleNamespace" in test_content
    assert "past_due=False" in test_content


@pytest.mark.parametrize("trigger", ["queue", "blob", "servicebus", "eventhub", "cosmosdb"])
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


def test_add_function_skips_extension_bundle_when_already_exists(tmp_path: Path) -> None:
    """Test that extension bundle is not duplicated when adding multiple functions (line 583)."""
    project_root = scaffold_project("sample", tmp_path)

    # Add first queue function - should add extension bundle
    add_function(project_root=project_root, trigger="queue", function_name="worker-one")
    host_json_path = project_root / "host.json"
    host_config_1 = json.loads(host_json_path.read_text(encoding="utf-8"))
    original_bundle = host_config_1["extensionBundle"].copy()

    # Add second queue function - should not duplicate extension bundle
    add_function(project_root=project_root, trigger="blob", function_name="worker-two")
    host_config_2 = json.loads(host_json_path.read_text(encoding="utf-8"))

    # Extension bundle should be the same
    assert host_config_2["extensionBundle"] == original_bundle


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


def test_describe_add_function_reports_expected_changes(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    lines = describe_add_function(
        project_root=project_root,
        trigger="servicebus",
        function_name="process-events",
    )

    assert lines[0] == "Dry run: add servicebus function 'process_events'"
    assert "  - app/functions/process_events.py" in lines
    assert "  - tests/test_process_events.py" in lines
    assert "  - host.json extensionBundle" in lines
    assert "  - local.settings.json.example ServiceBusConnection" in lines


def test_add_function_skips_test_file_when_already_exists(tmp_path: Path) -> None:
    """Test that add_function doesn't overwrite an existing test file (line 38->44)."""
    project_root = scaffold_project("sample", tmp_path)

    # Add first function to create test infrastructure
    add_function(project_root=project_root, trigger="http", function_name="sync-data")

    # Now delete the function module but keep the test file
    func_path = project_root / "app" / "functions" / "sync_data.py"
    test_path = project_root / "tests" / "test_sync_data.py"
    _original_test_content = test_path.read_text(encoding="utf-8")

    # Modify the test file
    modified_content = "# This test file was manually modified"
    test_path.write_text(modified_content, encoding="utf-8")

    # Delete the function module file
    func_path.unlink()

    # Also need to remove the function from function_app.py to avoid registration conflict
    func_app_path = project_root / "function_app.py"
    content = func_app_path.read_text(encoding="utf-8")
    # Remove the sync_data imports and registrations
    content = content.replace("from app.functions.sync_data import sync_data_blueprint\n", "")
    content = content.replace("app.register_functions(sync_data_blueprint)\n", "")
    func_app_path.write_text(content, encoding="utf-8")

    # Now add the function again - test file should NOT be overwritten
    add_function(project_root=project_root, trigger="http", function_name="sync-data")

    # Verify test file was not overwritten (it should still have our modified content)
    assert test_path.read_text(encoding="utf-8") == modified_content


def test_describe_add_function_rejects_existing_module(tmp_path: Path) -> None:
    """Test that describe_add_function raises error when function module exists."""
    project_root = scaffold_project("sample", tmp_path)
    add_function(project_root=project_root, trigger="http", function_name="sync-data")

    with pytest.raises(ScaffoldError, match="Function module already exists"):
        describe_add_function(
            project_root=project_root,
            trigger="http",
            function_name="sync-data",
        )


def test_describe_add_function_excludes_test_line_when_no_tests_dir(tmp_path: Path) -> None:
    """Test that describe_add_function omits test file line when tests/ dir missing."""
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

    lines = describe_add_function(
        project_root=project_root,
        trigger="http",
        function_name="sync-data",
    )

    # Should NOT contain test file line since tests/ dir doesn't exist
    assert not any("test_sync_data.py" in line for line in lines)


@pytest.mark.parametrize(
    ("trigger", "expected_host_json", "expected_local_settings"),
    [
        ("queue", True, False),
        ("blob", True, False),
        ("servicebus", True, True),
        ("eventhub", True, True),
        ("cosmosdb", True, True),
    ],
)
def test_describe_add_function_trigger_specific_outputs(
    tmp_path: Path,
    trigger: str,
    expected_host_json: bool,
    expected_local_settings: bool,
) -> None:
    """Test that describe_add_function reports correct outputs for each trigger type."""
    project_root = scaffold_project("sample", tmp_path)

    lines = describe_add_function(
        project_root=project_root,
        trigger=trigger,
        function_name="test-func",
    )

    output = "\n".join(lines)

    if expected_host_json:
        assert "host.json extensionBundle" in output
    else:
        assert "host.json extensionBundle" not in output

    if expected_local_settings:
        if trigger == "servicebus":
            assert "ServiceBusConnection" in output
        elif trigger == "eventhub":
            assert "EventHubConnection" in output
        elif trigger == "cosmosdb":
            assert "CosmosDBConnection" in output
    else:
        assert "Connection" not in output


def test_update_function_app_rejects_when_already_registered(tmp_path: Path) -> None:
    """Test that _update_function_app raises error when function is already registered.

    This directly tests the registration check at line 146.
    """
    function_app_path = tmp_path / "function_app.py"
    content = """from azure.functions import FunctionApp, Blueprint

configure_logging()

app = FunctionApp()

app.register_functions(sync_data_blueprint)
"""
    function_app_path.write_text(content, encoding="utf-8")

    # Try to register the same function again - should raise error
    with pytest.raises(ScaffoldError, match="Function is already registered"):
        _update_function_app(
            function_app_path,
            import_stmt="from app.functions.sync_data import sync_data_blueprint",
            registration_stmt="app.register_functions(sync_data_blueprint)",
        )


def test_insert_near_marker_raises_when_fallback_anchor_missing(tmp_path: Path) -> None:
    """Test that _insert_near_marker raises error when fallback anchor not found."""
    content = "some content without any anchor"

    with pytest.raises(
        ScaffoldError,
        match="Could not update function_app.py because 'missing_anchor' was not found",
    ):
        _insert_near_marker(
            content,
            marker="# some marker",
            line="new line",
            fallback_anchor="missing_anchor",
        )


def test_insert_near_marker_inserts_before_anchor_when_not_specified() -> None:
    """Test that _insert_near_marker inserts before anchor when after_anchor=False (line 188)."""
    content = """configure_logging()

app = FunctionApp()"""

    result = _insert_near_marker(
        content,
        marker="# marker",
        line="import my_module",
        fallback_anchor="configure_logging()",
        after_anchor=False,
    )

    assert "import my_module\n\nconfigure_logging()" in result


def test_insert_near_marker_inserts_after_anchor_when_specified() -> None:
    """Test that _insert_near_marker inserts after anchor when after_anchor=True (line 186)."""
    content = """app = FunctionApp()

app.register_functions(my_blueprint)"""

    result = _insert_near_marker(
        content,
        marker="# marker",
        line="new_line_here",
        fallback_anchor="app = FunctionApp()",
        after_anchor=True,
    )

    assert "app = FunctionApp()\nnew_line_here" in result


def test_render_function_module_raises_for_unknown_trigger() -> None:
    """Test that _render_function_module raises error for unknown trigger."""
    with pytest.raises(ScaffoldError, match="No function module template for trigger"):
        _render_function_module(trigger="unknown", function_name="test_func")


def test_render_function_test_raises_for_unknown_trigger() -> None:
    """Test that _render_function_test raises error for unknown trigger."""
    with pytest.raises(ScaffoldError, match="No function test template for trigger"):
        _render_function_test(trigger="unknown", function_name="test_func")


def test_add_function_with_http_trigger_skips_host_extensions(tmp_path: Path) -> None:
    """Test that http trigger does not update host.json (line 583 branch)."""
    project_root = scaffold_project("sample", tmp_path)
    original_host = (project_root / "host.json").read_text(encoding="utf-8")

    add_function(project_root=project_root, trigger="http", function_name="web-api")

    # host.json should not be modified for http trigger
    assert (project_root / "host.json").read_text(encoding="utf-8") == original_host


def test_add_function_skips_local_settings_when_example_missing(tmp_path: Path) -> None:
    """Test _ensure_local_settings_values returns early when example file missing (line 613)."""
    project_root = scaffold_project("sample", tmp_path)

    # Remove the local.settings.json.example file
    local_settings_path = project_root / "local.settings.json.example"
    if local_settings_path.exists():
        local_settings_path.unlink()

    # This should not raise an error even though the file is missing
    add_function(
        project_root=project_root,
        trigger="servicebus",
        function_name="event-handler",
    )

    # Verify the function was still created
    assert (project_root / "app" / "functions" / "event_handler.py").exists()


# ---------------------------------------------------------------------------
# _derive_resource_names
# ---------------------------------------------------------------------------


class TestDeriveResourceNames:
    def test_basic_plural_name(self) -> None:
        result = _derive_resource_names("products")
        assert result == {
            "resource_name": "products",
            "resource_singular": "product",
            "resource_class": "Product",
            "route_name": "products",
            "store_class": "ProductsStore",
        }

    def test_underscore_name(self) -> None:
        result = _derive_resource_names("line_items")
        assert result == {
            "resource_name": "line_items",
            "resource_singular": "line_item",
            "resource_class": "LineItem",
            "route_name": "line-items",
            "store_class": "LineItemsStore",
        }

    def test_short_name_not_stripped(self) -> None:
        """Names with 3 or fewer characters should not have trailing 's' stripped."""
        result = _derive_resource_names("bus")
        assert result["resource_singular"] == "bus"
        assert result["resource_class"] == "Bus"

    def test_non_plural_name(self) -> None:
        result = _derive_resource_names("health")
        assert result["resource_singular"] == "health"
        assert result["resource_class"] == "Health"
        assert result["route_name"] == "health"
        assert result["store_class"] == "HealthStore"

    def test_single_word(self) -> None:
        result = _derive_resource_names("users")
        assert result["resource_singular"] == "user"
        assert result["resource_class"] == "User"
        assert result["store_class"] == "UsersStore"

    def test_no_strip_status(self) -> None:
        """Names in the no-strip list should keep their trailing 's'."""
        result = _derive_resource_names("status")
        assert result["resource_singular"] == "status"
        assert result["resource_class"] == "Status"

    def test_no_strip_news(self) -> None:
        result = _derive_resource_names("news")
        assert result["resource_singular"] == "news"
        assert result["resource_class"] == "News"

    def test_no_strip_address(self) -> None:
        result = _derive_resource_names("address")
        assert result["resource_singular"] == "address"
        assert result["resource_class"] == "Address"

    def test_no_strip_compound_with_status(self) -> None:
        """Compound name whose last segment is in the no-strip list."""
        result = _derive_resource_names("order_status")
        assert result["resource_singular"] == "order_status"
        assert result["resource_class"] == "OrderStatus"


# ---------------------------------------------------------------------------
# add_resource
# ---------------------------------------------------------------------------


def test_add_resource_creates_all_files(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    created = add_resource(project_root=project_root, resource_name="products")

    assert (project_root / "app/functions/products.py").exists()
    assert (project_root / "app/services/products_service.py").exists()
    assert (project_root / "app/schemas/products.py").exists()
    assert (project_root / "tests/test_products.py").exists()
    assert len(created) == 4


def test_add_resource_blueprint_content_is_valid_python(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    blueprint_text = (project_root / "app/functions/products.py").read_text(encoding="utf-8")
    # Verify it compiles (valid Python syntax)
    compile(blueprint_text, "products.py", "exec")
    # Verify key content
    assert "products_blueprint" in blueprint_text
    assert "list_products" in blueprint_text
    assert "get_product" in blueprint_text
    assert "create_product" in blueprint_text
    assert "update_product" in blueprint_text
    assert "delete_product" in blueprint_text
    assert "from app.services.products_service import products_store" in blueprint_text


def test_add_resource_blueprint_guards_non_dict_json(tmp_path: Path) -> None:
    """Verify generated blueprint includes isinstance(body, dict) guard."""
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    blueprint_text = (project_root / "app/functions/products.py").read_text(encoding="utf-8")
    assert "isinstance(body, dict)" in blueprint_text
    assert "Request body must be a JSON object" in blueprint_text


def test_add_resource_service_content_is_valid_python(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    service_text = (project_root / "app/services/products_service.py").read_text(encoding="utf-8")
    compile(service_text, "products_service.py", "exec")
    assert "ProductsStore" in service_text
    assert "products_store" in service_text
    assert "def create" in service_text
    assert "def delete" in service_text


def test_add_resource_schema_content_is_valid_python(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    schema_text = (project_root / "app/schemas/products.py").read_text(encoding="utf-8")
    compile(schema_text, "products.py", "exec")
    assert "CreateProductRequest" in schema_text
    assert "UpdateProductRequest" in schema_text
    assert "ProductResponse" in schema_text


def test_add_resource_test_content_is_valid_python(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    test_text = (project_root / "tests/test_products.py").read_text(encoding="utf-8")
    compile(test_text, "test_products.py", "exec")
    assert "TestListProduct" in test_text
    assert "TestCreateProduct" in test_text
    assert "TestDeleteProduct" in test_text


def test_add_resource_registers_blueprint(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    function_app_text = (project_root / "function_app.py").read_text(encoding="utf-8")
    assert "from app.functions.products import products_blueprint" in function_app_text
    assert "app.register_functions(products_blueprint)" in function_app_text


def test_add_resource_rejects_existing_blueprint(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    with pytest.raises(ScaffoldError, match="File already exists"):
        add_resource(project_root=project_root, resource_name="products")


def test_add_resource_rejects_non_scaffold_project(tmp_path: Path) -> None:
    project_root = tmp_path / "not-a-project"
    project_root.mkdir()

    with pytest.raises(
        ScaffoldError,
        match="does not look like a scaffolded Azure Functions project",
    ):
        add_resource(project_root=project_root, resource_name="products")


def test_add_resource_rejects_missing_project_root(tmp_path: Path) -> None:
    with pytest.raises(ScaffoldError, match="Project root does not exist"):
        add_resource(project_root=tmp_path / "missing", resource_name="products")


@pytest.mark.parametrize("resource_name", ["", "***", "123-sync"])
def test_add_resource_rejects_invalid_names(tmp_path: Path, resource_name: str) -> None:
    project_root = scaffold_project("sample", tmp_path)

    with pytest.raises(ScaffoldError):
        add_resource(project_root=project_root, resource_name=resource_name)


def test_add_resource_does_not_create_files_when_function_app_uneditable(tmp_path: Path) -> None:
    """Verify no files are left behind when function_app.py cannot be updated."""
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    function_app_path.write_text("import azure.functions as func\n", encoding="utf-8")

    with pytest.raises(ScaffoldError):
        add_resource(project_root=project_root, resource_name="orphans")

    assert not (project_root / "app/functions/orphans.py").exists()
    assert not (project_root / "app/services/orphans_service.py").exists()
    assert not (project_root / "app/schemas/orphans.py").exists()
    assert not (project_root / "tests/test_orphans.py").exists()


def test_add_resource_rolls_back_on_partial_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    original_function_app = function_app_path.read_text(encoding="utf-8")
    original_write_text = Path.write_text

    def failing_write_text(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
        if self == function_app_path:
            raise PermissionError("blocked")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", failing_write_text)

    with pytest.raises(ScaffoldError, match="Atomic write failed"):
        add_resource(project_root=project_root, resource_name="products")

    assert not (project_root / "app/functions/products.py").exists()
    assert not (project_root / "app/services/products_service.py").exists()
    assert not (project_root / "app/schemas/products.py").exists()
    assert not (project_root / "tests/test_products.py").exists()
    assert function_app_path.read_text(encoding="utf-8") == original_function_app


def test_add_resource_skips_test_when_no_tests_dir(tmp_path: Path) -> None:
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

    created = add_resource(project_root=project_root, resource_name="products")

    # Blueprint + service + schema = 3 files, no test
    assert len(created) == 3
    assert not (project_root / "tests/test_products.py").exists()


def test_add_resource_with_hyphenated_name(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="line-items")

    assert (project_root / "app/functions/line_items.py").exists()
    assert (project_root / "app/services/line_items_service.py").exists()
    assert (project_root / "app/schemas/line_items.py").exists()
    blueprint_text = (project_root / "app/functions/line_items.py").read_text(encoding="utf-8")
    assert "line_items_blueprint" in blueprint_text
    assert "LineItem" in blueprint_text  # resource_class from singular


def test_add_multiple_resources(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")
    add_resource(project_root=project_root, resource_name="orders")

    function_app_text = (project_root / "function_app.py").read_text(encoding="utf-8")
    assert "products_blueprint" in function_app_text
    assert "orders_blueprint" in function_app_text


# ---------------------------------------------------------------------------
# describe_add_resource
# ---------------------------------------------------------------------------


def test_describe_add_resource_reports_expected_changes(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    lines = describe_add_resource(project_root=project_root, resource_name="products")

    assert lines[0] == "Dry run: add resource 'products'"
    assert "  - app/functions/products.py" in lines
    assert "  - app/services/products_service.py" in lines
    assert "  - app/schemas/products.py" in lines
    assert "  - tests/test_products.py" in lines
    assert "  - function_app.py import registration" in lines


def test_describe_add_resource_rejects_existing_files(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_resource(project_root=project_root, resource_name="products")

    with pytest.raises(ScaffoldError, match="File already exists"):
        describe_add_resource(project_root=project_root, resource_name="products")


def test_describe_add_resource_excludes_test_when_no_tests_dir(tmp_path: Path) -> None:
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

    lines = describe_add_resource(project_root=project_root, resource_name="products")

    assert not any("test_products.py" in line for line in lines)


# ---------------------------------------------------------------------------
# add_route
# ---------------------------------------------------------------------------


def test_add_route_creates_blueprint_and_test(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    route_path = add_route(project_root=project_root, route_name="status")

    assert route_path == project_root / "app/functions/status.py"
    assert (project_root / "tests/test_status.py").exists()


def test_add_route_blueprint_content_is_valid_python(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_route(project_root=project_root, route_name="status")

    blueprint_text = (project_root / "app/functions/status.py").read_text(encoding="utf-8")
    compile(blueprint_text, "status.py", "exec")
    assert "status_blueprint" in blueprint_text
    assert 'route="status"' in blueprint_text
    assert 'body="TODO: implement status"' in blueprint_text


def test_add_route_test_content_is_valid_python(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_route(project_root=project_root, route_name="status")

    test_text = (project_root / "tests/test_status.py").read_text(encoding="utf-8")
    compile(test_text, "test_status.py", "exec")
    assert "test_status_returns_placeholder_response" in test_text


def test_add_route_registers_blueprint(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_route(project_root=project_root, route_name="status")

    function_app_text = (project_root / "function_app.py").read_text(encoding="utf-8")
    assert "from app.functions.status import status_blueprint" in function_app_text
    assert "app.register_functions(status_blueprint)" in function_app_text


def test_add_route_rejects_existing_module(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_route(project_root=project_root, route_name="status")

    with pytest.raises(ScaffoldError, match="Function module already exists"):
        add_route(project_root=project_root, route_name="status")


def test_add_route_rejects_non_scaffold_project(tmp_path: Path) -> None:
    project_root = tmp_path / "not-a-project"
    project_root.mkdir()

    with pytest.raises(
        ScaffoldError,
        match="does not look like a scaffolded Azure Functions project",
    ):
        add_route(project_root=project_root, route_name="status")


def test_add_route_does_not_create_files_when_function_app_uneditable(tmp_path: Path) -> None:
    """Verify no files are left behind when function_app.py cannot be updated."""
    project_root = scaffold_project("sample", tmp_path)
    function_app_path = project_root / "function_app.py"
    function_app_path.write_text("import azure.functions as func\n", encoding="utf-8")

    with pytest.raises(ScaffoldError):
        add_route(project_root=project_root, route_name="orphan")

    assert not (project_root / "app/functions/orphan.py").exists()
    assert not (project_root / "tests/test_orphan.py").exists()


def test_add_route_with_hyphenated_name(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    route_path = add_route(project_root=project_root, route_name="health-check")

    assert route_path == project_root / "app/functions/health_check.py"
    blueprint_text = (project_root / "app/functions/health_check.py").read_text(encoding="utf-8")
    assert "health_check_blueprint" in blueprint_text
    assert 'route="health-check"' in blueprint_text


def test_add_route_skips_test_when_no_tests_dir(tmp_path: Path) -> None:
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

    add_route(project_root=project_root, route_name="status")

    assert (project_root / "app/functions/status.py").exists()
    assert not (project_root / "tests/test_status.py").exists()


def test_add_route_and_resource_coexist(tmp_path: Path) -> None:
    """Verify a route and a resource can be added to the same project."""
    project_root = scaffold_project("sample", tmp_path)
    add_route(project_root=project_root, route_name="status")
    add_resource(project_root=project_root, resource_name="products")

    function_app_text = (project_root / "function_app.py").read_text(encoding="utf-8")
    assert "status_blueprint" in function_app_text
    assert "products_blueprint" in function_app_text


# ---------------------------------------------------------------------------
# describe_add_route
# ---------------------------------------------------------------------------


def test_describe_add_route_reports_expected_changes(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)

    lines = describe_add_route(project_root=project_root, route_name="status")

    assert lines[0] == "Dry run: add route 'status'"
    assert "  - app/functions/status.py" in lines
    assert "  - tests/test_status.py" in lines
    assert "  - function_app.py import registration" in lines


def test_describe_add_route_rejects_existing_module(tmp_path: Path) -> None:
    project_root = scaffold_project("sample", tmp_path)
    add_route(project_root=project_root, route_name="status")

    with pytest.raises(ScaffoldError, match="Function module already exists"):
        describe_add_route(project_root=project_root, route_name="status")


def test_describe_add_route_excludes_test_when_no_tests_dir(tmp_path: Path) -> None:
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

    lines = describe_add_route(project_root=project_root, route_name="status")

    assert not any("test_status.py" in line for line in lines)
