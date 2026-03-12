# Style Guide

## Repository Code Style

### Python

- target Python `3.10+`
- keep functions small and explicit
- prefer standard library types and `pathlib.Path`
- use type hints for public and internal code paths when reasonable

### Tooling

- lint with `ruff`
- format with `ruff format`
- test with `pytest`

### Imports

- keep imports sorted
- avoid unnecessary indirection
- avoid wildcard imports

### Error Handling

- raise specific, readable exceptions for user-facing validation failures
- keep CLI errors actionable and short

## Template Style

Generated template code should:

- be easy to read without project-specific context
- represent a maintainable baseline, not a toy snippet
- separate Azure trigger code from business logic
- stay lint-clean and format-clean

## Documentation Style

- prefer short sections with concrete examples
- document current behavior separately from future ideas
- avoid claiming support for features that are not implemented
- write all documentation in English

## Comment Style

- write all code comments in English
- keep comments short and explain intent, not obvious syntax

## Naming Conventions

### Repository

- package name: `azure_functions_scaffold`
- CLI command: `azure-functions-scaffold`

### Generated Project

- `function_app.py` is the Azure Functions app entrypoint
- `app/functions/` contains trigger-facing modules
- `app/services/` contains business logic
- `app/schemas/` contains simple request/response models
- `app/core/` contains cross-cutting concerns
- `Makefile` is the generated local entry point for project checks when enabled

### CLI Terms

- use `preset` for bundled tooling defaults
- use `template` for the overall project scaffold type
- use `add` for post-generation function creation

## Generated Code Patterns

### Good Pattern: Typed, deterministic HTTP handler

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!", status_code=200)
```

### Good Pattern: Trigger logic separated from service logic

```python
from app.services.hello_service import build_hello_message


def run(name: str) -> str:
    return build_hello_message(name)
```

### Bad Pattern: Untyped and side-effect heavy handler

```python
import azure.functions as func

app = func.FunctionApp()


@app.route(route="hello")
def hello(req):
    print(req.params)
    name = req.params.get("name")
    return func.HttpResponse("hello " + str(name))
```

### Bad Pattern: Business logic embedded in trigger module

```python
import azure.functions as func

bp = func.Blueprint()


@bp.route(route="orders", methods=["POST"])
def create_order(req: func.HttpRequest) -> func.HttpResponse:
    data = req.get_json()
    total = 0
    for item in data["items"]:
        total += item["price"] * item["qty"]
    return func.HttpResponse(str(total), status_code=200)
```

## Change Discipline

When behavior changes:

- update tests
- update public docs
- validate the generated scaffold
