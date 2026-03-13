# Template Specification

## Purpose

Templates define the generated project structure and default source files for scaffolded Azure Functions applications.

## Current Template Set

Current built-in templates:

- `http`
- `timer`
- `queue`
- `blob`
- `servicebus`

Location:

```text
src/azure_functions_scaffold/templates/<template-name>/
```

## Rendering Rules

### File Discovery

Every file under the template root is rendered into the destination project.

### File Name Rules

- files ending in `.j2` are emitted without the `.j2` suffix
- path segments may use placeholders such as `__project_name__`

### Content Rules

Template files are rendered with Jinja2.

Current context variables:

- `project_name`
- `project_slug`
- `python_version`
- `python_upper_bound`
- `preset_name`
- `include_github_actions`
- `include_ruff`
- `include_mypy`
- `include_pytest`

`preset_name` may be `custom` when interactive tooling choices diverge from the selected preset defaults.

## HTTP Template Contract

The HTTP template must generate:

- Azure Functions Python v2 `function_app.py`
- at least one Blueprint-backed HTTP trigger module
- one service module
- one schema or model example
- one test file when pytest is enabled
- project-level tooling files

## Required Output Files

Minimum expected files:

```text
function_app.py
host.json
local.settings.json.example
pyproject.toml
.gitignore
.funcignore
README.md
app/functions/http.py
app/services/hello_service.py
app/schemas/request_models.py
app/core/logging.py
tests/test_http.py
```

The `minimal` preset intentionally omits `tests/`.

The template now also supports optional output:

```text
Makefile
.github/workflows/ci.yml
```

These files are rendered only when their corresponding options are enabled.

## Trigger Template Contract

All non-HTTP trigger templates must generate:

- Azure Functions Python v2 `function_app.py`
- one Blueprint-backed trigger module
- one service/helper module
- one test file when pytest is enabled
- project-level tooling files

Additional expectations:

- `timer` must run without external emulators
- `queue` and `blob` must be ready for Azurite-backed local development
- `servicebus` must generate a clear development connection placeholder
- binding-based trigger templates must include `extensionBundle` in `host.json`

## Generated Python Examples by Pattern

### `http-basic` (`function_app.py`)

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!", status_code=200)
```

### `http-openapi` (`function_app.py`)

```python
import azure.functions as func
from azure_functions_openapi import OpenAPI

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
openapi = OpenAPI(title="Sample API", version="1.0.0")


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!", status_code=200)


@app.route(route="openapi.json", methods=["GET"])
def openapi_json(req: func.HttpRequest) -> func.HttpResponse:
    spec = openapi.render_openapi_json()
    return func.HttpResponse(spec, mimetype="application/json", status_code=200)
```

### `http-validation` (`function_app.py`)

```python
import azure.functions as func
from pydantic import BaseModel, Field

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class HelloRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)


class HelloResponse(BaseModel):
    message: str


@app.route(route="hello", methods=["POST"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    payload = HelloRequest.model_validate_json(req.get_body())
    response = HelloResponse(message=f"Hello, {payload.name}!")
    return func.HttpResponse(response.model_dump_json(), mimetype="application/json", status_code=200)
```

### `timer` (`app/functions/cleanup.py`)

```python
import azure.functions as func

bp = func.Blueprint()


@bp.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def cleanup(timer: func.TimerRequest) -> None:
    if timer.past_due:
        return
```

### `queue` (`app/functions/sync_jobs.py`)

```python
import azure.functions as func

bp = func.Blueprint()


@bp.queue_trigger(arg_name="msg", queue_name="jobs", connection="AzureWebJobsStorage")
def sync_jobs(msg: func.QueueMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

### `blob` (`app/functions/ingest_reports.py`)

```python
import azure.functions as func

bp = func.Blueprint()


@bp.blob_trigger(arg_name="blob", path="incoming/{name}", connection="AzureWebJobsStorage")
def ingest_reports(blob: func.InputStream) -> None:
    _ = blob.name
```

### `servicebus` (`app/functions/process_events.py`)

```python
import azure.functions as func

bp = func.Blueprint()


@bp.service_bus_queue_trigger(arg_name="msg", queue_name="events", connection="SERVICEBUS_CONNECTION")
def process_events(msg: func.ServiceBusMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

## Recipes

### REST API with Validation

Build a type-safe REST API with automatic request validation:

```bash
azure-functions-scaffold new my-api --with-openapi --with-validation --preset strict
cd my-api
pip install -e .[dev]
func start
```

This generates an HTTP project with:
- POST `/api/hello` with Pydantic `HelloRequest`/`HelloResponse` models
- GET `/api/openapi.json` and `/api/openapi.yaml` for API specification
- GET `/api/docs` for Swagger UI
- Strict linting with Ruff + mypy
- Pytest test suite

### Scheduled Background Job

Create a timer-triggered function for periodic tasks:

```bash
azure-functions-scaffold new cleanup-job --template timer --preset standard
```

The timer template generates a function that runs every 5 minutes by default. Modify the cron expression in `app/functions/cleanup.py` to change the schedule.

### Message Queue Worker

Process messages from Azure Storage Queue with Azurite for local development:

```bash
azure-functions-scaffold new order-processor --template queue
cd order-processor
pip install -e .
```

Start Azurite for local queue emulation, then run `func start`.

### Blob Storage Processor

React to file uploads in Azure Blob Storage:

```bash
azure-functions-scaffold new file-ingester --template blob
```

The blob template watches the `incoming/` container. Local development uses Azurite.

### Service Bus Event Handler

Process enterprise messages from Azure Service Bus:

```bash
azure-functions-scaffold new event-handler --template servicebus
```

Update the `SERVICEBUS_CONNECTION` in `local.settings.json.example` with your connection string.

### Full-Stack HTTP with All Features

Combine all optional features for a production-ready HTTP API:

```bash
azure-functions-scaffold new production-api \
    --with-openapi \
    --with-validation \
    --with-doctor \
    --preset strict \
    --python-version 3.12 \
    --github-actions \
    --git
```

This generates a project with OpenAPI documentation, request validation, health checks, strict linting, GitHub Actions CI, and git initialization.

### Adding Functions to Existing Projects

Expand a scaffolded project with additional triggers:

```bash
cd my-api
azure-functions-scaffold add http get-user --project-root .
azure-functions-scaffold add timer daily-cleanup --project-root .
azure-functions-scaffold add queue process-orders --project-root .
```

Each `add` command creates a new function module, service, and test file, then registers the Blueprint in `function_app.py`.

## Quality Contract

Generated projects should satisfy the commands implied by their selected preset:

```bash
make install
make check-all
```

Preset expectations:

- `minimal`: no extra quality tooling beyond a valid Azure Functions project structure
- `standard`: Ruff and pytest defaults
- `strict`: Ruff, mypy, and pytest defaults

## Template Authoring Rules

- keep files small and readable
- prefer simple imports and explicit structure
- keep placeholder usage aligned with the actual rendering context
- avoid environment-specific absolute paths
- keep examples realistic but minimal
- keep `function_app.py` update markers stable for post-generation `add` commands

## Extension Guidelines

When adding a new template:

1. create a new template directory under `src/azure_functions_scaffold/templates/`
2. define the required output contract for that template
3. add CLI selection logic
4. add tests that validate rendered output
5. verify preset-specific lint, type, and test behavior in the generated project

