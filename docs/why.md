# Why This Structure

Azure Functions Scaffold generates an opinionated project layout. This page explains the reasoning behind each design decision.

## The Generated Layout

```text
my-api/
|- function_app.py          # Entrypoint: Azure Functions runtime reads this
|- app/
|  |- functions/            # Trigger handlers (thin layer)
|  |  `- http.py
|  |- services/             # Business logic (testable without Azure SDK)
|  |  `- hello_service.py
|  |- schemas/              # Request/response models
|  |  `- request_models.py
|  `- core/                 # Cross-cutting: logging, config
|     `- logging.py
`- tests/
   `- test_http.py
```

This layout separates runtime integration from application logic.
The Azure-facing files stay small, while domain logic remains framework-agnostic.

## function_app.py vs Blueprint

Azure Functions Python v2 expects a single `function_app.py` as the runtime entrypoint.
The runtime imports this module and discovers function registrations from it.

Individual function modules use `Blueprint` so each trigger can live in its own file.
`function_app.py` only creates `FunctionApp` and registers blueprints.
Business logic does not live in `function_app.py`.

This mirrors Flask's app factory pattern: one composition root, many feature modules.
The composition root wires components together without owning domain behavior.

## functions/ - Trigger Layer

`app/functions/` is the trigger adapter layer.

- Each file handles one trigger type (`http`, `timer`, `queue`, `blob`, `servicebus`).
- Handler functions stay thin: parse input, call a service, return a response.
- Azure-specific request/response types stay in this layer.
- New handlers can be added with `azure-functions-scaffold add http get-user`.

Keeping triggers thin reduces coupling to Azure SDK details.
If trigger contracts change, updates stay localized to this layer.

## services/ - Business Logic

`app/services/` contains pure Python business behavior.
Services should avoid Azure SDK imports.

This keeps behavior easy to test with plain pytest.
Most unit tests can run without function host startup or Azure mocks.

```python
# app/services/hello_service.py
def build_hello_message(name: str) -> str:
    return f"Hello, {name}!"
```

```python
# tests/test_http.py
from app.services.hello_service import build_hello_message


def test_build_hello_message() -> None:
    assert build_hello_message("Azure") == "Hello, Azure!"
```

This design supports fast feedback loops for core logic.
Integration tests can then focus only on trigger wiring and bindings.

## schemas/ - Data Models

`app/schemas/` holds request and response model definitions.
These are optional and generated when `--with-validation` is enabled.

- Validation rules are explicit and centralized.
- Trigger handlers avoid inline schema definitions.
- Response shapes remain consistent across handlers.

Keeping models separate makes API contracts easier to review and evolve.

## core/ - Cross-Cutting Concerns

`app/core/` is for shared infrastructure code.

- Logging setup lives here, including structured JSON output through `azure-functions-logging`.
- Shared configuration helpers can be added here.
- Future middleware-style utilities can be added here.

Centralizing cross-cutting behavior prevents copy-paste setup in every function module.

## How This Scales

As the project grows, the same boundaries continue to work:

- New endpoints mainly add files under `app/functions/` and `app/services/`.
- Shared policies (logging, config, retry helpers) stay centralized in `app/core/`.
- API contract changes are isolated to `app/schemas/` when validation is enabled.
- `function_app.py` remains a small registry file instead of a monolith.

This keeps code review scope smaller and lowers merge conflicts across teams.

## Presets

Presets control tooling defaults without changing the runtime architecture.

- `minimal`: No extra tooling; useful for prototyping.
- `standard`: Ruff + pytest; recommended default for most projects.
- `strict`: Ruff + mypy + pytest; suited for production-focused teams.

You can still override options with flags.
Presets provide a consistent starting baseline.

## Design Principles

- Separation of concerns: trigger wiring, business logic, and models are isolated.
- Testability: services are pure Python and easy to unit test.
- Consistency: all templates follow the same structural conventions.
- Progressive enhancement: start minimal and add capabilities via flags.
