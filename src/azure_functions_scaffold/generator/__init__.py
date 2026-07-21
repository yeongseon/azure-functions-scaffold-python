"""Add functions, routes, and CRUD resources to an existing scaffolded project.

This package is split into focused modules:

* :mod:`~azure_functions_scaffold.generator.writer` — the atomic multi-file
  write path with rollback.
* :mod:`~azure_functions_scaffold.generator.function_app` — marker-based
  ``function_app.py`` registration updates.
* :mod:`~azure_functions_scaffold.generator.json_mutators` — idempotent
  ``host.json`` / ``local.settings.json.example`` mutations.

The public ``add_*`` / ``describe_*`` orchestration, name normalization, and
Jinja rendering live in this module and compose the helpers above.
"""

from __future__ import annotations

import keyword
import logging
from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.generator.function_app import (
    FUNCTION_IMPORT_MARKER,
    FUNCTION_REGISTRATION_MARKER,
    _compute_updated_function_app,
    _insert_near_marker,
    _sort_app_functions_imports,
    _validate_function_app_updatable,
)
from azure_functions_scaffold.generator.json_mutators import (
    HOST_JSON_TRIGGERS,
    _compute_updated_host_json,
    _compute_updated_local_settings,
)
from azure_functions_scaffold.generator.writer import (
    _commit_pending_writes,
    _PendingWrite,
)
from azure_functions_scaffold.template_registry import list_templates

__all__ = [
    "ADDABLE_TRIGGERS",
    "FUNCTION_IMPORT_MARKER",
    "FUNCTION_REGISTRATION_MARKER",
    "HOST_JSON_TRIGGERS",
    "SUPPORTED_TRIGGERS",
    "_compute_updated_function_app",
    "_compute_updated_host_json",
    "_compute_updated_local_settings",
    "_insert_near_marker",
    "_sort_app_functions_imports",
    "add_function",
    "add_resource",
    "add_route",
    "describe_add_function",
    "describe_add_resource",
    "describe_add_route",
]

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
PARTIALS_ROOT = Path(__file__).parent.parent / "templates" / "partials"
logger = logging.getLogger(__name__)


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
