# Project Structure

The CLI generates a clean, multi-layered directory structure based on the Azure Functions v2 Blueprint pattern. This approach separates framework concerns from your business logic, making the code testable and easy to maintain as it grows.

### Tree View

Here's the layout of a generated project with an HTTP trigger:

```text
my-api/
├── function_app.py          # Azure Functions v2 entrypoint — registers Blueprints
├── host.json                # Runtime configuration
├── local.settings.json.example  # Local environment template
├── pyproject.toml           # Dependencies and tooling config
├── app/
│   ├── core/
│   │   └── logging.py       # Structured JSON logging configuration
│   ├── functions/
│   │   ├── health.py        # Health check HTTP trigger (Blueprint)
│   │   └── webhooks.py      # Webhook HTTP trigger (Blueprint)
│   ├── schemas/
│   │   ├── health.py        # Health response model
│   │   └── webhooks.py      # Webhook request/response models
│   └── services/
│       ├── health_service.py   # Health check business logic
│       └── webhook_service.py  # Webhook business logic
└── tests/
    ├── test_health.py       # Pytest suite for health endpoint
    └── test_webhooks.py     # Pytest suite for webhooks endpoint
```

### Layer Responsibilities

*   **Trigger (Functions)**: Thin entry points that handle input parsing and output formatting.
*   **Service (Business Logic)**: Pure Python functions or classes independent of Azure's SDK.
*   **Schema (Data Models)**: Pydantic or basic Python models defining the API contract.
*   **Core (Cross-cutting)**: Shared configurations like structured logging or custom exception handlers.

### Why this structure?

Traditional Azure Functions often mix trigger logic with business rules. By using this scaffold:

1.  **Testability**: You can test services without mocking the complex `HttpRequest` or `HttpResponse` objects.
2.  **Scalability**: Adding a new endpoint doesn't clutter `function_app.py`. Instead, you create a new Blueprint in `app/functions/` and register it once.
3.  **Consistency**: Every project in your organization follows the same predictable pattern.

### Separation in Action

The trigger receives the request, calls a service, and returns the response. This pattern keeps the function logic minimal.

```python
# app/functions/health.py (simplified)
from __future__ import annotations

import json
import logging

import azure.functions as func

from app.services.health_service import check_health

health_blueprint = func.Blueprint()

@health_blueprint.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    result = check_health()
    return func.HttpResponse(
        body=json.dumps(result),
        mimetype="application/json",
        status_code=200,
    )
```

### Blueprint Registration

The main `function_app.py` acts as a coordinator. It imports and registers Blueprints from the `app/functions/` directory.

```python
# function_app.py (simplified)
import azure.functions as func

from app.core.logging import configure_logging
from app.functions.health import health_blueprint
from app.functions.webhooks import webhooks_blueprint

configure_logging()

app = func.FunctionApp()
app.register_functions(health_blueprint)
app.register_functions(webhooks_blueprint)
```

### What's Next?

Learn about the available [Templates](templates.md) for various trigger types.
