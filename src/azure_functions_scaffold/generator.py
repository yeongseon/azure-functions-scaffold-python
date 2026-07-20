from __future__ import annotations

from dataclasses import dataclass
import json
import keyword
import logging
from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.template_registry import list_templates

FUNCTION_IMPORT_MARKER = "# azure-functions-scaffold: function imports"
FUNCTION_REGISTRATION_MARKER = "# azure-functions-scaffold: function registrations"
LEGACY_FUNCTION_IMPORT_MARKER = "# azure-functions-scaffold-python: function imports"
LEGACY_FUNCTION_REGISTRATION_MARKER = "# azure-functions-scaffold-python: function registrations"
SUPPORTED_TRIGGERS = tuple(template.name for template in list_templates())
ADDABLE_TRIGGERS: tuple[str, ...] = (
    "http",
    "timer",
    "queue",
    "blob",
    "servicebus",
    "eventhub",
    "cosmosdb",
    "durable",
    "ai",
)
PARTIALS_ROOT = Path(__file__).parent / "templates" / "partials"
HOST_JSON_TRIGGERS = frozenset({"queue", "blob", "servicebus", "eventhub", "cosmosdb"})
logger = logging.getLogger(__name__)


@dataclass
class _PendingWrite:
    path: Path
    new_content: str
    original_content: str | None
    created_parent: Path | None = None


def _commit_pending_writes(writes: list[_PendingWrite]) -> None:
    written: list[_PendingWrite] = []
    try:
        for write in writes:
            write.path.parent.mkdir(parents=True, exist_ok=True)
            write.path.write_text(write.new_content, encoding="utf-8")
            written.append(write)
    except Exception as exc:
        for write in reversed(written):
            try:
                if write.original_content is None:
                    if write.path.exists():
                        write.path.unlink()
                    if (
                        write.created_parent is not None
                        and write.created_parent.exists()
                        and not any(write.created_parent.iterdir())
                    ):
                        write.created_parent.rmdir()
                else:
                    write.path.write_text(write.original_content, encoding="utf-8")
            except OSError:
                logger.exception("Rollback failed for %s", write.path)
        raise ScaffoldError(
            f"Atomic write failed; rolled back {len(written)} file(s): {exc}"
        ) from exc


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


def _compute_updated_host_json(content: str, trigger: str) -> str | None:
    if trigger not in HOST_JSON_TRIGGERS:
        return None

    try:
        host_config = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ScaffoldError(f"Invalid JSON in host.json: {exc}") from exc
    if not isinstance(host_config, dict):
        raise ScaffoldError("Expected host.json to contain a JSON object.")
    if "extensionBundle" in host_config:
        return None

    host_config["extensionBundle"] = {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.*, 5.0.0)",
    }
    return f"{json.dumps(host_config, indent=2)}\n"


def _compute_updated_local_settings(content: str, trigger: str) -> str | None:
    connection_keys: dict[str, tuple[str, str]] = {
        "servicebus": (
            "ServiceBusConnection",
            "Endpoint=sb://localhost/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=replace-me",
        ),
        "eventhub": (
            "EventHubConnection",
            "Endpoint=sb://localhost/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=replace-me",
        ),
        "cosmosdb": (
            "CosmosDBConnection",
            "AccountEndpoint=https://localhost:8081/;AccountKey=replace-me",
        ),
    }
    if trigger not in connection_keys:
        return None

    try:
        local_settings = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ScaffoldError(f"Invalid JSON in local.settings.json.example: {exc}") from exc
    if not isinstance(local_settings, dict):
        raise ScaffoldError("Expected local.settings.json.example to contain a JSON object.")

    existing_values = local_settings.get("Values")
    if existing_values is None:
        values: dict[str, object] = {}
        local_settings["Values"] = values
    elif isinstance(existing_values, dict):
        values = existing_values
    else:
        raise ScaffoldError("Expected local.settings.json.example Values to be a JSON object.")

    key, default = connection_keys[trigger]
    if key in values:
        return None

    values[key] = default
    return f"{json.dumps(local_settings, indent=2)}\n"


def add_function(
    *,
    project_root: Path,
    trigger: str,
    function_name: str,
) -> Path:
    logger.info("Adding %s function '%s' to %s", trigger, function_name, project_root)
    normalized_trigger = _normalize_trigger(trigger)
    normalized_name = _normalize_function_name(function_name)

    _validate_project_root(project_root)

    function_path = project_root / "app" / "functions" / f"{normalized_name}.py"
    if function_path.exists():
        raise ScaffoldError(f"Function module already exists: {function_path}")

    import_stmt = f"from app.functions.{normalized_name} import {normalized_name}_blueprint"
    registration_stmt = f"app.register_functions({normalized_name}_blueprint)"
    function_app_path = project_root / "function_app.py"
    _validate_function_app_updatable(
        function_app_path,
        import_stmt=import_stmt,
        registration_stmt=registration_stmt,
    )
    function_app_content = function_app_path.read_text(encoding="utf-8")
    updated_function_app = _compute_updated_function_app(
        function_app_content,
        import_stmt=import_stmt,
        registration_stmt=registration_stmt,
    )

    writes = [
        _PendingWrite(
            path=function_path,
            new_content=_render_function_module(normalized_trigger, normalized_name),
            original_content=None,
        ),
        _PendingWrite(
            path=function_app_path,
            new_content=updated_function_app,
            original_content=function_app_content,
        ),
    ]

    if (project_root / "tests").is_dir():
        test_path = project_root / "tests" / f"test_{normalized_name}.py"
        if not test_path.exists():
            writes.insert(
                1,
                _PendingWrite(
                    path=test_path,
                    new_content=_render_function_test(normalized_trigger, normalized_name),
                    original_content=None,
                ),
            )

    host_json_path = project_root / "host.json"
    if host_json_path.exists() and normalized_trigger in HOST_JSON_TRIGGERS:
        host_content = host_json_path.read_text(encoding="utf-8")
        updated_host = _compute_updated_host_json(host_content, normalized_trigger)
        if updated_host is not None:
            writes.append(
                _PendingWrite(
                    path=host_json_path,
                    new_content=updated_host,
                    original_content=host_content,
                )
            )

    local_settings_path = project_root / "local.settings.json.example"
    if local_settings_path.exists():
        local_settings_content = local_settings_path.read_text(encoding="utf-8")
        updated_local_settings = _compute_updated_local_settings(
            local_settings_content,
            normalized_trigger,
        )
        if updated_local_settings is not None:
            writes.append(
                _PendingWrite(
                    path=local_settings_path,
                    new_content=updated_local_settings,
                    original_content=local_settings_content,
                )
            )

    _commit_pending_writes(writes)

    return function_path


def describe_add_function(
    *,
    project_root: Path,
    trigger: str,
    function_name: str,
) -> list[str]:
    normalized_trigger = _normalize_trigger(trigger)
    normalized_name = _normalize_function_name(function_name)
    _validate_project_root(project_root)

    function_path = project_root / "app" / "functions" / f"{normalized_name}.py"
    if function_path.exists():
        raise ScaffoldError(f"Function module already exists: {function_path}")

    _validate_function_app_updatable(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized_name} import {normalized_name}_blueprint",
        registration_stmt=f"app.register_functions({normalized_name}_blueprint)",
    )

    host_json_path = project_root / "host.json"
    if host_json_path.exists() and normalized_trigger in HOST_JSON_TRIGGERS:
        _compute_updated_host_json(host_json_path.read_text(encoding="utf-8"), normalized_trigger)

    local_settings_path = project_root / "local.settings.json.example"
    if local_settings_path.exists():
        _compute_updated_local_settings(
            local_settings_path.read_text(encoding="utf-8"),
            normalized_trigger,
        )

    lines = [
        f"Dry run: add {normalized_trigger} function '{normalized_name}'",
        f"Project root: {project_root}",
        "Files:",
        f"  - app/functions/{normalized_name}.py",
    ]

    if (project_root / "tests").is_dir():
        lines.append(f"  - tests/test_{normalized_name}.py")

    lines.extend(
        [
            "Updates:",
            "  - function_app.py import registration",
        ]
    )

    if normalized_trigger in {"queue", "blob", "servicebus", "eventhub", "cosmosdb"}:
        lines.append("  - host.json extensionBundle")
    if normalized_trigger == "servicebus":
        lines.append("  - local.settings.json.example ServiceBusConnection")
    if normalized_trigger == "eventhub":
        lines.append("  - local.settings.json.example EventHubConnection")
    if normalized_trigger == "cosmosdb":
        lines.append("  - local.settings.json.example CosmosDBConnection")

    return lines


def _normalize_trigger(trigger: str) -> str:
    normalized = trigger.strip().lower()
    if normalized not in ADDABLE_TRIGGERS:
        supported = ", ".join(ADDABLE_TRIGGERS)
        raise ScaffoldError(f"Unsupported trigger '{trigger}'. Supported triggers: {supported}")
    return normalized


def _normalize_function_name(function_name: str) -> str:
    normalized = function_name.strip()
    if not normalized:
        raise ScaffoldError("Function name must not be empty.")

    module_name = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    if not module_name:
        raise ScaffoldError("Function name must contain letters or numbers.")

    if module_name[0].isdigit():
        raise ScaffoldError("Function name must not start with a digit.")

    if not module_name.isidentifier():
        raise ScaffoldError(
            f"Function name '{function_name}' does not produce a valid Python "
            f"identifier (got '{module_name}'). Use letters, numbers, hyphens, "
            f"or underscores."
        )

    soft_keywords = set(getattr(keyword, "softkwlist", ())) | {"_", "case", "match", "type"}
    if keyword.iskeyword(module_name) or module_name in soft_keywords:
        raise ScaffoldError(
            f"Function name '{function_name}' resolves to a reserved Python "
            f"keyword ('{module_name}'). Choose a different name."
        )

    return module_name


def _validate_project_root(project_root: Path) -> None:
    if not project_root.exists():
        raise ScaffoldError(f"Project root does not exist: {project_root}")

    if not project_root.is_dir():
        raise ScaffoldError(f"Project root must be a directory: {project_root}")

    required_paths = [
        project_root / "function_app.py",
        project_root / "app" / "functions",
    ]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        raise ScaffoldError("Project root does not look like a scaffolded Azure Functions project.")


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


_FUNCTION_MODULE_TEMPLATES: dict[str, str] = {
    "http": "functions/http_module.py.j2",
    "timer": "functions/timer_module.py.j2",
    "queue": "functions/queue_module.py.j2",
    "blob": "functions/blob_module.py.j2",
    "servicebus": "functions/servicebus_module.py.j2",
    "eventhub": "functions/eventhub_module.py.j2",
    "cosmosdb": "functions/cosmosdb_module.py.j2",
    "durable": "functions/durable_module.py.j2",
    "ai": "functions/ai_module.py.j2",
}

_FUNCTION_TEST_TEMPLATES: dict[str, str] = {
    "http": "functions/http_test.py.j2",
    "timer": "functions/timer_test.py.j2",
    "queue": "functions/queue_test.py.j2",
    "blob": "functions/blob_test.py.j2",
    "servicebus": "functions/servicebus_test.py.j2",
    "eventhub": "functions/eventhub_test.py.j2",
    "cosmosdb": "functions/cosmosdb_test.py.j2",
    "durable": "functions/durable_test.py.j2",
    "ai": "functions/ai_test.py.j2",
}


def _render_function_module(trigger: str, function_name: str) -> str:
    template_name = _FUNCTION_MODULE_TEMPLATES.get(trigger)
    if template_name is None:
        raise ScaffoldError(f"No function module template for trigger '{trigger}'.")
    return _render_partial(
        template_name,
        {
            "function_name": function_name,
            "route_name": function_name.replace("_", "-"),
        },
    )


def _render_function_test(trigger: str, function_name: str) -> str:
    template_name = _FUNCTION_TEST_TEMPLATES.get(trigger)
    if template_name is None:
        raise ScaffoldError(f"No function test template for trigger '{trigger}'.")
    return _render_partial(
        template_name,
        {
            "function_name": function_name,
            "route_name": function_name.replace("_", "-"),
        },
    )


# ---------------------------------------------------------------------------
# Resource generation (Jinja partials)
# ---------------------------------------------------------------------------


def _derive_resource_names(resource_name: str) -> dict[str, str]:
    """Derive all template variable names from a normalized resource name.

    For example, ``products`` yields::

        resource_name   = "products"
        resource_singular = "product"
        resource_class  = "Product"
        route_name      = "products"
        store_class     = "ProductsStore"
    """
    # Simple English singular: strip trailing 's' when safe.
    # Guard against false positives where stripping 's' produces nonsense.
    _NO_STRIP = frozenset(
        {
            "status",
            "bus",
            "news",
            "address",
            "class",
            "process",
            "access",
            "success",
            "progress",
            "focus",
            "canvas",
            "analysis",
            "basis",
            "crisis",
            "diagnosis",
            "thesis",
        }
    )
    singular = resource_name
    # Check the last segment (after final underscore) for the no-strip list.
    last_segment = resource_name.rsplit("_", maxsplit=1)[-1]
    if last_segment not in _NO_STRIP and singular.endswith("s") and len(singular) > 3:
        singular = singular[:-1]

    # PascalCase: split on underscore, capitalise each part.
    class_name = "".join(part.capitalize() for part in singular.split("_"))
    store_class = "".join(part.capitalize() for part in resource_name.split("_")) + "Store"
    route_name = resource_name.replace("_", "-")

    result = {
        "resource_name": resource_name,
        "resource_singular": singular,
        "resource_class": class_name,
        "route_name": route_name,
        "store_class": store_class,
    }
    logger.debug("Derived resource names for '%s': %s", resource_name, result)
    return result


def _render_partial(template_name: str, context: dict[str, str]) -> str:
    """Render a Jinja partial template with the given context."""
    logger.debug("Rendering partial template: %s", template_name)
    env = Environment(
        loader=FileSystemLoader(str(PARTIALS_ROOT)),
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml"),
            default_for_string=False,
            default=False,
        ),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)
    return template.render(**context)


def add_resource(
    *,
    project_root: Path,
    resource_name: str,
) -> list[Path]:
    """Add a full CRUD resource to an existing scaffolded project.

    Creates four files:
        - ``app/functions/{name}.py`` — CRUD blueprint
        - ``app/services/{name}_service.py`` — in-memory store
        - ``app/schemas/{name}.py`` — request/response dataclasses
        - ``tests/test_{name}.py`` — test suite (if ``tests/`` exists)

    Also registers the new blueprint in ``function_app.py`` via markers.

    Returns the list of created file paths.
    """
    logger.info("Adding resource '%s' to %s", resource_name, project_root)
    normalized = _normalize_function_name(resource_name)
    _validate_project_root(project_root)
    names = _derive_resource_names(normalized)

    # Check for existing files before writing anything.
    blueprint_path = project_root / "app" / "functions" / f"{normalized}.py"
    service_path = project_root / "app" / "services" / f"{normalized}_service.py"
    schema_path = project_root / "app" / "schemas" / f"{normalized}.py"

    for path in (blueprint_path, service_path, schema_path):
        if path.exists():
            raise ScaffoldError(f"File already exists: {path}")

    import_stmt = f"from app.functions.{normalized} import {normalized}_blueprint"
    registration_stmt = f"app.register_functions({normalized}_blueprint)"
    function_app_path = project_root / "function_app.py"
    _validate_function_app_updatable(
        function_app_path,
        import_stmt=import_stmt,
        registration_stmt=registration_stmt,
    )
    function_app_content = function_app_path.read_text(encoding="utf-8")
    updated_function_app = _compute_updated_function_app(
        function_app_content,
        import_stmt=import_stmt,
        registration_stmt=registration_stmt,
    )

    writes = [
        _PendingWrite(
            path=blueprint_path,
            new_content=_render_partial("resource_blueprint.py.j2", names),
            original_content=None,
        ),
        _PendingWrite(
            path=service_path,
            new_content=_render_partial("resource_service.py.j2", names),
            original_content=None,
        ),
        _PendingWrite(
            path=schema_path,
            new_content=_render_partial("resource_schema.py.j2", names),
            original_content=None,
        ),
    ]

    created = [blueprint_path, service_path, schema_path]

    if (project_root / "tests").is_dir():
        test_path = project_root / "tests" / f"test_{normalized}.py"
        if not test_path.exists():
            writes.append(
                _PendingWrite(
                    path=test_path,
                    new_content=_render_partial("resource_test.py.j2", names),
                    original_content=None,
                )
            )
            created.append(test_path)

    writes.append(
        _PendingWrite(
            path=function_app_path,
            new_content=updated_function_app,
            original_content=function_app_content,
        )
    )

    _commit_pending_writes(writes)

    return created


def describe_add_resource(
    *,
    project_root: Path,
    resource_name: str,
) -> list[str]:
    """Return a dry-run description of what ``add_resource`` would do."""
    normalized = _normalize_function_name(resource_name)
    _validate_project_root(project_root)

    blueprint_path = project_root / "app" / "functions" / f"{normalized}.py"
    service_path = project_root / "app" / "services" / f"{normalized}_service.py"
    schema_path = project_root / "app" / "schemas" / f"{normalized}.py"

    for path in (blueprint_path, service_path, schema_path):
        if path.exists():
            raise ScaffoldError(f"File already exists: {path}")

    _validate_function_app_updatable(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized} import {normalized}_blueprint",
        registration_stmt=f"app.register_functions({normalized}_blueprint)",
    )

    lines = [
        f"Dry run: add resource '{normalized}'",
        f"Project root: {project_root}",
        "Files:",
        f"  - app/functions/{normalized}.py",
        f"  - app/services/{normalized}_service.py",
        f"  - app/schemas/{normalized}.py",
    ]

    if (project_root / "tests").is_dir():
        lines.append(f"  - tests/test_{normalized}.py")

    lines.extend(
        [
            "Updates:",
            "  - function_app.py import registration",
        ]
    )

    return lines


# ---------------------------------------------------------------------------
# Route generation (Jinja partials)
# ---------------------------------------------------------------------------


def add_route(
    *,
    project_root: Path,
    route_name: str,
) -> Path:
    """Add a simple HTTP route blueprint to an existing scaffolded project.

    Creates:
        - ``app/functions/{name}.py`` — route blueprint
        - ``tests/test_{name}.py`` — test (if ``tests/`` exists)

    Also registers the new blueprint in ``function_app.py`` via markers.

    Returns the path to the created blueprint file.
    """
    logger.info("Adding route '%s' to %s", route_name, project_root)
    normalized = _normalize_function_name(route_name)
    _validate_project_root(project_root)

    blueprint_path = project_root / "app" / "functions" / f"{normalized}.py"
    if blueprint_path.exists():
        raise ScaffoldError(f"Function module already exists: {blueprint_path}")

    import_stmt = f"from app.functions.{normalized} import {normalized}_blueprint"
    registration_stmt = f"app.register_functions({normalized}_blueprint)"
    function_app_path = project_root / "function_app.py"
    _validate_function_app_updatable(
        function_app_path,
        import_stmt=import_stmt,
        registration_stmt=registration_stmt,
    )
    function_app_content = function_app_path.read_text(encoding="utf-8")
    updated_function_app = _compute_updated_function_app(
        function_app_content,
        import_stmt=import_stmt,
        registration_stmt=registration_stmt,
    )

    names = {
        "resource_name": normalized,
        "route_name": normalized.replace("_", "-"),
    }

    writes = [
        _PendingWrite(
            path=blueprint_path,
            new_content=_render_partial("route_blueprint.py.j2", names),
            original_content=None,
        )
    ]

    if (project_root / "tests").is_dir():
        test_path = project_root / "tests" / f"test_{normalized}.py"
        if not test_path.exists():
            writes.append(
                _PendingWrite(
                    path=test_path,
                    new_content=_render_partial("route_test.py.j2", names),
                    original_content=None,
                )
            )

    writes.append(
        _PendingWrite(
            path=function_app_path,
            new_content=updated_function_app,
            original_content=function_app_content,
        )
    )

    _commit_pending_writes(writes)

    return blueprint_path


def describe_add_route(
    *,
    project_root: Path,
    route_name: str,
) -> list[str]:
    """Return a dry-run description of what ``add_route`` would do."""
    normalized = _normalize_function_name(route_name)
    _validate_project_root(project_root)

    blueprint_path = project_root / "app" / "functions" / f"{normalized}.py"
    if blueprint_path.exists():
        raise ScaffoldError(f"Function module already exists: {blueprint_path}")

    _validate_function_app_updatable(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized} import {normalized}_blueprint",
        registration_stmt=f"app.register_functions({normalized}_blueprint)",
    )

    lines = [
        f"Dry run: add route '{normalized}'",
        f"Project root: {project_root}",
        "Files:",
        f"  - app/functions/{normalized}.py",
    ]

    if (project_root / "tests").is_dir():
        lines.append(f"  - tests/test_{normalized}.py")

    lines.extend(
        [
            "Updates:",
            "  - function_app.py import registration",
        ]
    )

    return lines
