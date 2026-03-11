from __future__ import annotations

import json
from pathlib import Path
import re

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.template_registry import list_templates

FUNCTION_IMPORT_MARKER = "# azure-functions-scaffold: function imports"
FUNCTION_REGISTRATION_MARKER = "# azure-functions-scaffold: function registrations"
SUPPORTED_TRIGGERS = tuple(template.name for template in list_templates())


def add_function(
    *,
    project_root: Path,
    trigger: str,
    function_name: str,
) -> Path:
    normalized_trigger = _normalize_trigger(trigger)
    normalized_name = _normalize_function_name(function_name)

    _validate_project_root(project_root)

    function_path = project_root / "app" / "functions" / f"{normalized_name}.py"
    if function_path.exists():
        raise ScaffoldError(f"Function module already exists: {function_path}")

    function_path.parent.mkdir(parents=True, exist_ok=True)
    function_path.write_text(
        _render_function_module(normalized_trigger, normalized_name),
        encoding="utf-8",
    )

    if (project_root / "tests").is_dir():
        test_path = project_root / "tests" / f"test_{normalized_name}.py"
        if not test_path.exists():
            test_path.write_text(
                _render_function_test(normalized_trigger, normalized_name),
                encoding="utf-8",
            )

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

    if normalized_trigger in {"queue", "blob", "servicebus"}:
        lines.append("  - host.json extensionBundle")
    if normalized_trigger == "servicebus":
        lines.append("  - local.settings.json.example ServiceBusConnection")

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

    return f"""from __future__ import annotations

from types import SimpleNamespace

from app.functions.{function_name} import {function_name}


def test_{function_name}_runs_without_error() -> None:
    message = SimpleNamespace(get_body=lambda: b"hello")

    {function_name}(message)
"""


def _ensure_host_extensions(host_json_path: Path, trigger: str) -> None:
    if trigger not in {"queue", "blob", "servicebus"} or not host_json_path.exists():
        return

    host_config = json.loads(host_json_path.read_text(encoding="utf-8"))
    if "extensionBundle" in host_config:
        return

    host_config["extensionBundle"] = {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.*, 5.0.0)",
    }
    host_json_path.write_text(f"{json.dumps(host_config, indent=2)}\n", encoding="utf-8")


def _ensure_local_settings_values(project_root: Path, trigger: str) -> None:
    if trigger != "servicebus":
        return

    local_settings_path = project_root / "local.settings.json.example"
    if not local_settings_path.exists():
        return

    local_settings = json.loads(local_settings_path.read_text(encoding="utf-8"))
    values = local_settings.setdefault("Values", {})
    values.setdefault(
        "ServiceBusConnection",
        "Endpoint=sb://localhost/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=replace-me",
    )
    local_settings_path.write_text(
        f"{json.dumps(local_settings, indent=2)}\n",
        encoding="utf-8",
    )
