from __future__ import annotations

import json
import logging
from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, select_autoescape

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.template_registry import list_templates

FUNCTION_IMPORT_MARKER = "# azure-functions-scaffold: function imports"
FUNCTION_REGISTRATION_MARKER = "# azure-functions-scaffold: function registrations"
SUPPORTED_TRIGGERS = tuple(template.name for template in list_templates())
PARTIALS_ROOT = Path(__file__).parent / "templates" / "partials"
logger = logging.getLogger(__name__)


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
        FUNCTION_IMPORT_MARKER in content or "configure_logging()" in content
    )
    has_registration_target = (
        FUNCTION_REGISTRATION_MARKER in content
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

    _validate_function_app_updatable(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized_name} import {normalized_name}_blueprint",
        registration_stmt=f"app.register_functions({normalized_name}_blueprint)",
    )

    function_path.parent.mkdir(parents=True, exist_ok=True)
    function_path.write_text(
        _render_function_module(normalized_trigger, normalized_name),
        encoding="utf-8",
    )
    logger.debug("Created function module: %s", function_path)

    if (project_root / "tests").is_dir():
        test_path = project_root / "tests" / f"test_{normalized_name}.py"
        if not test_path.exists():
            test_path.write_text(
                _render_function_test(normalized_trigger, normalized_name),
                encoding="utf-8",
            )
            logger.debug("Created test: %s", test_path)

    _update_function_app(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized_name} import {normalized_name}_blueprint",
        registration_stmt=f"app.register_functions({normalized_name}_blueprint)",
    )
    _ensure_host_extensions(project_root / "host.json", normalized_trigger)
    _ensure_local_settings_values(project_root, normalized_trigger)

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
    if normalized not in SUPPORTED_TRIGGERS:
        supported = ", ".join(SUPPORTED_TRIGGERS)
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


def _update_function_app(
    function_app_path: Path,
    *,
    import_stmt: str,
    registration_stmt: str,
) -> None:
    logger.debug("Updating function_app.py: %s", import_stmt)
    content = function_app_path.read_text(encoding="utf-8")

    if import_stmt in content or registration_stmt in content:
        raise ScaffoldError("Function is already registered in function_app.py.")

    updated = _insert_near_marker(
        content,
        marker=FUNCTION_IMPORT_MARKER,
        line=import_stmt,
        fallback_anchor="configure_logging()",
    )
    updated = _insert_near_marker(
        updated,
        marker=FUNCTION_REGISTRATION_MARKER,
        line=registration_stmt,
        fallback_anchor="app = func.FunctionApp()",
        after_anchor=True,
    )
    function_app_path.write_text(updated, encoding="utf-8")


def _insert_near_marker(
    content: str,
    *,
    marker: str,
    line: str,
    fallback_anchor: str,
    after_anchor: bool = False,
) -> str:
    if marker in content:
        # Insert new import before the blank line that separates imports from
        # the marker comment, keeping all imports in one contiguous block.
        blank_then_marker = f"\n\n{marker}"
        if blank_then_marker in content:
            return content.replace(blank_then_marker, f"\n{line}\n\n{marker}", 1)
        return content.replace(marker, f"{line}\n{marker}", 1)

    if fallback_anchor not in content:
        raise ScaffoldError(
            f"Could not update function_app.py because '{fallback_anchor}' was not found."
        )

    if after_anchor:
        return content.replace(fallback_anchor, f"{fallback_anchor}\n{line}", 1)

    return content.replace(fallback_anchor, f"{line}\n\n{fallback_anchor}", 1)


def _render_function_module(trigger: str, function_name: str) -> str:
    route_name = function_name.replace("_", "-")

    if trigger == "http":
        return f"""from __future__ import annotations

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.route(
    route="{route_name}",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def {function_name}(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body="TODO: implement {route_name}",
        status_code=200,
    )
"""

    if trigger == "timer":
        return f"""from __future__ import annotations

import logging

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.timer_trigger(
    arg_name="timer",
    schedule="0 */5 * * * *",
    run_on_startup=False,
    use_monitor=True,
)
def {function_name}(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.warning("Timer trigger '{function_name}' is running late.")

    logging.info("Timer trigger '{function_name}' executed.")
"""

    if trigger == "queue":
        return f"""from __future__ import annotations

import logging

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.queue_trigger(
    arg_name="message",
    queue_name="work-items",
    connection="AzureWebJobsStorage",
)
def {function_name}(message: func.QueueMessage) -> None:
    payload = message.get_body().decode("utf-8")
    logging.info("Queue trigger '{function_name}' processed: %s", payload)
"""

    if trigger == "blob":
        return f"""from __future__ import annotations

import logging

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.blob_trigger(
    arg_name="blob",
    path="samples-workitems/{{name}}",
    connection="AzureWebJobsStorage",
)
def {function_name}(blob: func.InputStream) -> None:
    logging.info(
        "Blob trigger '{function_name}' processed %s (%s bytes).",
        blob.name,
        blob.length,
    )
"""

    if trigger == "servicebus":
        return f"""from __future__ import annotations

import logging

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.service_bus_queue_trigger(
    arg_name="message",
    queue_name="work-items",
    connection="ServiceBusConnection",
)
def {function_name}(message: func.ServiceBusMessage) -> None:
    body = message.get_body().decode("utf-8")
    logging.info("Service Bus trigger '{function_name}' processed: %s", body)
"""

    if trigger == "eventhub":
        return f"""from __future__ import annotations

import logging

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.event_hub_message_trigger(
    arg_name="event",
    event_hub_name="my-event-hub",
    connection="EventHubConnection",
)
def {function_name}(event: func.EventHubEvent) -> None:
    payload = event.get_body().decode("utf-8")
    logging.info("EventHub trigger '{function_name}' processed: %s", payload)
"""

    if trigger == "cosmosdb":
        return f"""from __future__ import annotations

import logging

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.cosmos_db_trigger_v3(
    arg_name="documents",
    container_name="my-container",
    database_name="my-database",
    connection="CosmosDBConnection",
    lease_container_name="leases",
    create_lease_container_if_not_exists=True,
)
def {function_name}(documents: func.DocumentList) -> None:
    logging.info("CosmosDB trigger '{function_name}' processed %s document(s).", len(documents))
"""

    if trigger == "durable":
        return f"""from __future__ import annotations

import logging

import azure.functions as func
import azure.functions.durable_functions as df

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.route(
    route="orchestrators/{{functionName}}",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
@{function_name}_blueprint.durable_client_input(client_name="client")
async def {function_name}_http_start(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    instance_id = await client.start_new(req.route_params["functionName"])
    logging.info("Started orchestration with ID '%s'.", instance_id)
    return client.create_check_status_response(req, instance_id)


@{function_name}_blueprint.orchestration_trigger(context_name="context")
def {function_name}_orchestrator(context: df.DurableOrchestrationContext) -> list[str]:
    results: list[str] = []
    results.append(yield context.call_activity("{function_name}_activity", "Tokyo"))
    results.append(yield context.call_activity("{function_name}_activity", "Seattle"))
    results.append(yield context.call_activity("{function_name}_activity", "London"))
    return results


@{function_name}_blueprint.activity_trigger(input_name="city")
def {function_name}_activity(city: str) -> str:
    return f"Hello, {{city}}!"
"""

    if trigger == "ai":
        return f"""from __future__ import annotations

import json
import logging
import os

import azure.functions as func

{function_name}_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@{function_name}_blueprint.route(
    route="chat",
    methods=["POST"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
async def {function_name}(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        prompt = body.get("prompt", "")
    except ValueError:
        return func.HttpResponse(
            body=json.dumps({{"error": "Invalid JSON body."}}),
            status_code=400,
            mimetype="application/json",
        )

    if not prompt:
        return func.HttpResponse(
            body=json.dumps({{"error": "Missing 'prompt' field."}}),
            status_code=400,
            mimetype="application/json",
        )

    logging.info("AI function '{function_name}' received prompt: %s", prompt[:50])
    return func.HttpResponse(
        body=json.dumps({{"response": f"Echo: {{prompt}}"}}),
        status_code=200,
        mimetype="application/json",
    )
"""

    raise ScaffoldError(f"No function module template for trigger '{trigger}'.")


def _render_function_test(trigger: str, function_name: str) -> str:
    if trigger == "http":
        route_name = function_name.replace("_", "-")
        return f"""from __future__ import annotations

import azure.functions as func

from app.functions.{function_name} import {function_name}


def test_{function_name}_returns_placeholder_response() -> None:
    request = func.HttpRequest(
        method="GET",
        url="http://localhost/api/{route_name}",
        params={{}},
        body=b"",
    )

    response = {function_name}(request)

    assert response.status_code == 200
    assert response.get_body() == b"TODO: implement {route_name}"
"""

    if trigger == "timer":
        return f"""from __future__ import annotations

from types import SimpleNamespace

from app.functions.{function_name} import {function_name}


def test_{function_name}_runs_without_error() -> None:
    timer = SimpleNamespace(past_due=False)

    {function_name}(timer)
"""

    if trigger == "queue":
        return f"""from __future__ import annotations

from types import SimpleNamespace

from app.functions.{function_name} import {function_name}


def test_{function_name}_runs_without_error() -> None:
    message = SimpleNamespace(get_body=lambda: b"hello")

    {function_name}(message)
"""

    if trigger == "blob":
        return f"""from __future__ import annotations

from types import SimpleNamespace

from app.functions.{function_name} import {function_name}


def test_{function_name}_runs_without_error() -> None:
    blob = SimpleNamespace(name="samples-workitems/input.txt", length=12)

    {function_name}(blob)
"""

    if trigger == "servicebus":
        return f"""from __future__ import annotations

from types import SimpleNamespace

from app.functions.{function_name} import {function_name}


def test_{function_name}_runs_without_error() -> None:
    message = SimpleNamespace(get_body=lambda: b"hello")

    {function_name}(message)
"""

    if trigger == "eventhub":
        return f"""from __future__ import annotations

from types import SimpleNamespace

from app.functions.{function_name} import {function_name}


def test_{function_name}_runs_without_error() -> None:
    event = SimpleNamespace(get_body=lambda: b"hello")

    {function_name}(event)
"""

    if trigger == "cosmosdb":
        return f"""from __future__ import annotations

from app.functions.{function_name} import {function_name}


def test_{function_name}_runs_without_error() -> None:
    documents = [{{"id": "1", "data": "hello"}}]

    {function_name}(documents)
"""

    if trigger == "durable":
        return f"""from __future__ import annotations

from app.functions.{function_name} import {function_name}_activity


def test_{function_name}_activity_returns_greeting() -> None:
    result = {function_name}_activity("Tokyo")

    assert result == "Hello, Tokyo!"
"""

    if trigger == "ai":
        return f"""from __future__ import annotations

import json

import azure.functions as func

from app.functions.{function_name} import {function_name}


def test_{function_name}_rejects_missing_prompt() -> None:
    request = func.HttpRequest(
        method="POST",
        url="http://localhost/api/chat",
        params={{}},
        body=json.dumps({{"prompt": ""}}).encode(),
        headers={{"Content-Type": "application/json"}},
    )

    import asyncio

    response = asyncio.run({function_name}(request))

    assert response.status_code == 400
"""

    raise ScaffoldError(f"No function test template for trigger '{trigger}'.")


def _ensure_host_extensions(host_json_path: Path, trigger: str) -> None:
    if (
        trigger not in {"queue", "blob", "servicebus", "eventhub", "cosmosdb"}
        or not host_json_path.exists()
    ):
        return

    host_config = json.loads(host_json_path.read_text(encoding="utf-8"))
    if "extensionBundle" in host_config:
        return

    host_config["extensionBundle"] = {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.*, 5.0.0)",
    }
    logger.debug("Adding extensionBundle to host.json")
    host_json_path.write_text(f"{json.dumps(host_config, indent=2)}\n", encoding="utf-8")


def _ensure_local_settings_values(project_root: Path, trigger: str) -> None:
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
        return

    local_settings_path = project_root / "local.settings.json.example"
    if not local_settings_path.exists():
        return

    local_settings = json.loads(local_settings_path.read_text(encoding="utf-8"))
    values = local_settings.setdefault("Values", {})
    key, default = connection_keys[trigger]
    values.setdefault(key, default)
    logger.debug("Adding %s to local.settings.json.example", key)
    local_settings_path.write_text(
        f"{json.dumps(local_settings, indent=2)}\n",
        encoding="utf-8",
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
    _NO_STRIP = frozenset({
        "status", "bus", "news", "address", "class", "process",
        "access", "success", "progress", "focus", "canvas",
        "analysis", "basis", "crisis", "diagnosis", "thesis",
    })
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

    # Pre-validate function_app.py can be updated before writing files.
    _validate_function_app_updatable(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized} import {normalized}_blueprint",
        registration_stmt=f"app.register_functions({normalized}_blueprint)",
    )

    # Render and write files.
    created: list[Path] = []

    blueprint_path.parent.mkdir(parents=True, exist_ok=True)
    blueprint_path.write_text(_render_partial("resource_blueprint.py.j2", names), encoding="utf-8")
    created.append(blueprint_path)
    logger.debug("Created %s", blueprint_path)

    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(_render_partial("resource_service.py.j2", names), encoding="utf-8")
    created.append(service_path)
    logger.debug("Created %s", service_path)

    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(_render_partial("resource_schema.py.j2", names), encoding="utf-8")
    created.append(schema_path)
    logger.debug("Created %s", schema_path)

    if (project_root / "tests").is_dir():
        test_path = project_root / "tests" / f"test_{normalized}.py"
        if not test_path.exists():
            test_path.write_text(_render_partial("resource_test.py.j2", names), encoding="utf-8")
            created.append(test_path)
            logger.debug("Created %s", test_path)

    _update_function_app(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized} import {normalized}_blueprint",
        registration_stmt=f"app.register_functions({normalized}_blueprint)",
    )

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

    _validate_function_app_updatable(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized} import {normalized}_blueprint",
        registration_stmt=f"app.register_functions({normalized}_blueprint)",
    )

    names = {
        "resource_name": normalized,
        "route_name": normalized.replace("_", "-"),
    }

    blueprint_path.parent.mkdir(parents=True, exist_ok=True)
    blueprint_path.write_text(_render_partial("route_blueprint.py.j2", names), encoding="utf-8")
    logger.debug("Created %s", blueprint_path)

    if (project_root / "tests").is_dir():
        test_path = project_root / "tests" / f"test_{normalized}.py"
        if not test_path.exists():
            test_path.write_text(_render_partial("route_test.py.j2", names), encoding="utf-8")
            logger.debug("Created %s", test_path)

    _update_function_app(
        project_root / "function_app.py",
        import_stmt=f"from app.functions.{normalized} import {normalized}_blueprint",
        registration_stmt=f"app.register_functions({normalized}_blueprint)",
    )

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
