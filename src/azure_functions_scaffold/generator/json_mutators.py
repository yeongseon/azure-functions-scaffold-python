"""Idempotent ``host.json`` / ``local.settings.json.example`` mutations."""

from __future__ import annotations

import json

from azure_functions_scaffold.errors import ScaffoldError

HOST_JSON_TRIGGERS = frozenset({"queue", "blob", "servicebus", "eventhub", "cosmosdb"})


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
