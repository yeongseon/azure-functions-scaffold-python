# Generated Output

This page shows **exactly what each template scaffolds** — the generated project tree plus the
`function_app.py` entrypoint and `host.json` runtime config. Use it to preview a template before
you run the CLI.

The HTTP project layout (with a `schemas/` layer) is documented separately in
[Project Structure](project-structure.md). The samples below cover the non-HTTP templates:
timer, queue, blob, servicebus, eventhub, cosmosdb, durable, ai, and langgraph.

!!! note "Generated from real scaffold output"
    Every tree and snippet on this page is captured verbatim from `afs` output so it stays
    faithful to what the CLI produces. See [Templates](templates.md) for the command and use case
    behind each template, and the [CLI Reference](../reference/cli.md) for full command options.

## Blueprint worker & advanced templates

The eight trigger-based templates — **timer, queue, blob, servicebus, eventhub, cosmosdb,
durable, ai** — all follow the same Blueprint layout. Only the two generated names differ per
template: `app/functions/<trigger>.py` and `app/services/<trigger>_service.py` (plus the matching
`tests/test_<trigger>.py`).

### Project tree

Shown for the timer template (`afs worker timer nightly-job`). Every other template in this family
is identical apart from the trigger-named files highlighted below.

```text
nightly-job/
├── function_app.py               # Azure Functions v2 entrypoint — registers the Blueprint
├── host.json                     # Runtime configuration
├── local.settings.json.example   # Local environment template
├── pyproject.toml                # Dependencies and tooling config
├── Makefile                      # Common dev tasks (install, test, lint)
├── .funcignore
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── logging.py            # Structured JSON logging configuration
│   ├── functions/
│   │   ├── __init__.py
│   │   └── timer.py              # Trigger handler (Blueprint)  ← per-template name
│   └── services/
│       ├── __init__.py
│       └── maintenance_service.py  # Pure Python business logic  ← per-template name
└── tests/
    └── test_timer.py             # Pytest test suite  ← per-template name
```

### Per-template generated files

| Template | CLI Command | Trigger handler | Service | Test |
| :--- | :--- | :--- | :--- | :--- |
| **Timer** | `afs worker timer <name>` | `app/functions/timer.py` | `app/services/maintenance_service.py` | `tests/test_timer.py` |
| **Queue** | `afs worker queue <name>` | `app/functions/queue.py` | `app/services/queue_service.py` | `tests/test_queue.py` |
| **Blob** | `afs worker blob <name>` | `app/functions/blob.py` | `app/services/blob_service.py` | `tests/test_blob.py` |
| **Service Bus** | `afs worker servicebus <name>` | `app/functions/servicebus.py` | `app/services/servicebus_service.py` | `tests/test_servicebus.py` |
| **Event Hub** | `afs worker eventhub <name>` | `app/functions/eventhub.py` | `app/services/eventhub_service.py` | `tests/test_eventhub.py` |
| **CosmosDB** | `afs advanced new --template cosmosdb --preset standard <name>` | `app/functions/cosmosdb.py` | `app/services/cosmosdb_service.py` | `tests/test_cosmosdb.py` |
| **Durable** | `afs advanced new --template durable --preset standard <name>` | `app/functions/durable.py` | `app/services/durable_service.py` | `tests/test_durable.py` |
| **AI** | `afs advanced new --template ai --preset standard <name>` | `app/functions/ai.py` | `app/services/ai_service.py` | `tests/test_ai.py` |

### `function_app.py`

All eight templates register their Blueprint the same way — only the imported module and
blueprint name change. For the timer template:

```python
from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.timer import timer_blueprint

# azure-functions-scaffold: function imports

configure_logging()

app = func.FunctionApp()
# azure-functions-scaffold: function registrations
app.register_functions(timer_blueprint)
```

For any other template, swap `timer` for the trigger name (e.g. `from app.functions.queue import
queue_blueprint` / `app.register_functions(queue_blueprint)`).

### `host.json`

Two variants are produced in this family:

**Timer and AI** ship the minimal runtime config:

```json
{
  "version": "2.0"
}
```

**Queue, blob, servicebus, eventhub, cosmosdb, and durable** add the extension bundle required by
their bindings:

```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

## LangGraph template

The LangGraph template (`afs ai agent my-agent`) uses a different structure built around
`LangGraphApp` instead of the Blueprint layout — graphs live under `app/graphs/` and there is no
`core/`, `functions/`, or `services/` split.

### Project tree

```text
my-agent/
├── function_app.py               # LangGraphApp entrypoint
├── host.json                     # Runtime configuration
├── local.settings.json.example   # Local environment template
├── pyproject.toml                # Dependencies and tooling config
├── Makefile                      # Common dev tasks (install, test, lint)
├── .funcignore
├── .gitignore
├── app/
│   ├── __init__.py
│   └── graphs/
│       ├── __init__.py
│       └── echo_agent.py         # Example LangGraph agent
└── tests/
    └── test_echo_agent.py        # Pytest test suite
```

### `function_app.py`

```python
from __future__ import annotations

import azure.functions as func
from azure_functions_langgraph import LangGraphApp  # type: ignore[import-not-found]

from app.graphs.echo_agent import graph

# Create LangGraph app with Azure Functions
lg_app = LangGraphApp(auth_level=func.AuthLevel.ANONYMOUS)
lg_app.register(graph=graph, name="echo_agent")

# Azure Functions entrypoint
func_app = lg_app.function_app
```

### `host.json`

```json
{
  "version": "2.0"
}
```

## What's Next?

- Browse the [Templates](templates.md) guide for the use case behind each template.
- See the full [CLI Reference](../reference/cli.md) for every command and flag.
- Review [Features & Presets](features.md) to layer OpenAPI, validation, and more onto a project.
