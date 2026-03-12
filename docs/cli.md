# CLI Specification

## Command Surface

Current CLI surface:

```bash
azure-functions-scaffold new [<project-name>] [--destination <path>]
azure-functions-scaffold add <trigger> <function-name> [--project-root <path>]
azure-functions-scaffold presets
azure-functions-scaffold templates
azure-functions-scaffold --version
```

## `new`

Creates a new Azure Functions Python v2 project from one of the built-in simple templates.

### Arguments

`project-name`

- optional when `--interactive` is used
- used as the output directory name
- also injected into template rendering context as `project_name`
- must start with an alphanumeric character
- may contain only letters, numbers, hyphens, and underscores

### Options

`--destination`, `-d`

- optional
- default: current directory
- interpreted as the parent directory where the project folder will be created

`--template`, `-t`

- optional
- default: `http`
- supported values: `http`, `timer`, `queue`, `blob`, `servicebus`
- selects the scaffold template to render

`--preset`

- optional
- default: `standard`
- supported values: `minimal`, `standard`, `strict`
- controls generated quality tooling defaults

`--python-version`

- optional
- default: `3.10`
- supported values: `3.10`, `3.11`, `3.12`, `3.13`, `3.14`
- controls the generated `requires-python` range and tool target version

`--github-actions`, `--no-github-actions`

- optional
- default: `--no-github-actions`
- controls whether `.github/workflows/ci.yml` is generated

`--git`, `--no-git`

- optional
- default: `--no-git`
- controls whether the generated project runs `git init`

`--with-openapi`, `--no-openapi`

- optional
- default: `--no-openapi`
- includes OpenAPI documentation support in the generated project (HTTP template only)
- adds `/api/openapi.json`, `/api/openapi.yaml`, and `/api/docs` endpoints
- requires `azure-functions-openapi>=0.13.0`

`--with-validation`, `--no-validation`

- optional
- default: `--no-validation`
- includes request/response validation in the generated project (HTTP template only)
- switches the hello endpoint from GET to POST with Pydantic body parsing
- requires `azure-functions-validation>=0.5.0` and `pydantic>=2.0.0`

`--interactive`, `-i`

- optional
- when enabled, prompts for project name, template, preset, Python version, GitHub Actions, git initialization, individual tooling selection, OpenAPI documentation, and request validation
- invalid project names, templates, presets, and Python versions are rejected at the prompt and re-requested immediately

`--dry-run`

- optional
- previews the generated project without writing files

`--overwrite`

- optional
- removes an existing target directory before rendering the new project

### Behavior

Example:

```bash
azure-functions-scaffold new my-api
```

Generated Output (`function_app.py`):

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!", status_code=200)
```

Interactive example:

```bash
azure-functions-scaffold new --interactive
```

Generated Output (default interactive HTTP selection):

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("Hello, World!", status_code=200)
```

Preset example:

```bash
azure-functions-scaffold new my-api --preset strict --python-version 3.12 --github-actions
```

Generated Output (`tests/test_http.py` included by strict preset):

```python
from app.services.hello_service import build_hello_message


def test_build_hello_message() -> None:
    assert build_hello_message("Azure") == "Hello, Azure!"
```

Timer template example:

```bash
azure-functions-scaffold new my-job --template timer
```

Generated Output (`function_app.py` for timer template):

```python
import azure.functions as func

app = func.FunctionApp()


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def cleanup(timer: func.TimerRequest) -> None:
    if timer.past_due:
        return
```

Queue template example:

```bash
azure-functions-scaffold new my-worker --template queue
```

Generated Output (`function_app.py` for queue template):

```python
import azure.functions as func

app = func.FunctionApp()


@app.queue_trigger(arg_name="msg", queue_name="jobs", connection="AzureWebJobsStorage")
def sync_jobs(msg: func.QueueMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

Blob template example:

```bash
azure-functions-scaffold new my-blob-worker --template blob
```

Generated Output (`function_app.py` for blob template):

```python
import azure.functions as func

app = func.FunctionApp()


@app.blob_trigger(arg_name="blob", path="incoming/{name}", connection="AzureWebJobsStorage")
def ingest_reports(blob: func.InputStream) -> None:
    _ = blob.name
```

Service Bus template example:

```bash
azure-functions-scaffold new my-bus-worker --template servicebus
```

Generated Output (`function_app.py` for service bus template):

```python
import azure.functions as func

app = func.FunctionApp()


@app.service_bus_queue_trigger(arg_name="msg", queue_name="events", connection="SERVICEBUS_CONNECTION")
def process_events(msg: func.ServiceBusMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

Dry-run example:

```bash
azure-functions-scaffold new my-api --template queue --preset strict --dry-run
```

Generated Output (previewed, not written):

```python
import azure.functions as func

app = func.FunctionApp()


@app.queue_trigger(arg_name="msg", queue_name="jobs", connection="AzureWebJobsStorage")
def sync_jobs(msg: func.QueueMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

Overwrite example:

```bash
azure-functions-scaffold new my-api --overwrite
```

Generated Output (same baseline HTTP app after replacement):

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("Hello, World!", status_code=200)
```

OpenAPI example:

```bash
azure-functions-scaffold new my-api --with-openapi
```

Generated Output (`function_app.py` with OpenAPI endpoints):

```python
import azure.functions as func
from azure_functions_openapi import OpenAPI

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
openapi = OpenAPI(title="My API", version="1.0.0")


@app.route(route="openapi.json", methods=["GET"])
def openapi_json(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(openapi.render_openapi_json(), mimetype="application/json", status_code=200)
```

Validation example:

```bash
azure-functions-scaffold new my-api --with-validation
```

Generated Output (`function_app.py` with request validation):

```python
import azure.functions as func
from pydantic import BaseModel

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


class HelloRequest(BaseModel):
    name: str


@app.route(route="hello", methods=["POST"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    payload = HelloRequest.model_validate_json(req.get_body())
    return func.HttpResponse(f"Hello, {payload.name}!", status_code=200)
```

OpenAPI + validation example:

```bash
azure-functions-scaffold new my-api --with-openapi --with-validation
```

Generated Output (`function_app.py` with both features):

```python
import azure.functions as func
from azure_functions_openapi import OpenAPI
from pydantic import BaseModel

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
openapi = OpenAPI(title="My API", version="1.0.0")


class HelloRequest(BaseModel):
    name: str


@app.route(route="hello", methods=["POST"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    payload = HelloRequest.model_validate_json(req.get_body())
    return func.HttpResponse(f"Hello, {payload.name}!", status_code=200)
```

Result:

- creates `./my-api`
- renders all files from the embedded HTTP template
- uses the chosen preset as a starting point, then applies interactive tooling overrides
- optionally omits tests for the `minimal` preset
- optionally includes `.github/workflows/ci.yml`
- optionally initializes a git repository
- supports dry-run previews of the target directory and rendered file set
- only replaces an existing target directory when `--overwrite` is provided
- prints `Created project at <path>`
- includes OpenAPI endpoints when `--with-openapi` is provided (HTTP template)
- includes request validation when `--with-validation` is provided (HTTP template)

## `add`

Adds a new function module to an existing scaffolded project.

### Arguments

`trigger`

- required
- supported values: `http`, `timer`, `queue`, `blob`, `servicebus`

`function-name`

- required
- normalized into a Python module name

### Options

`--project-root`

- optional
- default: current directory
- points to an existing scaffolded Azure Functions project

`--dry-run`

- optional
- previews the files and project updates without modifying the project

### Behavior

HTTP example:

```bash
azure-functions-scaffold add http get-user --project-root ./my-api
```

Generated Output (`app/functions/get_user.py`):

```python
import azure.functions as func

bp = func.Blueprint()


@bp.route(route="get-user", methods=["GET"])
def get_user(req: func.HttpRequest) -> func.HttpResponse:
    user_id = req.params.get("id", "unknown")
    return func.HttpResponse(f"user={user_id}", status_code=200)
```

Timer example:

```bash
azure-functions-scaffold add timer cleanup --project-root ./my-api
```

Generated Output (`app/functions/cleanup.py`):

```python
import azure.functions as func

bp = func.Blueprint()


@bp.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def cleanup(timer: func.TimerRequest) -> None:
    if timer.past_due:
        return
```

Queue example:

```bash
azure-functions-scaffold add queue sync-jobs --project-root ./my-api
```

Generated Output (`app/functions/sync_jobs.py`):

```python
import azure.functions as func

bp = func.Blueprint()


@bp.queue_trigger(arg_name="msg", queue_name="jobs", connection="AzureWebJobsStorage")
def sync_jobs(msg: func.QueueMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

Blob example:

```bash
azure-functions-scaffold add blob ingest-reports --project-root ./my-api
```

Generated Output (`app/functions/ingest_reports.py`):

```python
import azure.functions as func

bp = func.Blueprint()


@bp.blob_trigger(arg_name="blob", path="incoming/{name}", connection="AzureWebJobsStorage")
def ingest_reports(blob: func.InputStream) -> None:
    _ = blob.name
```

Service Bus example:

```bash
azure-functions-scaffold add servicebus process-events --project-root ./my-api
```

Generated Output (`app/functions/process_events.py`):

```python
import azure.functions as func

bp = func.Blueprint()


@bp.service_bus_queue_trigger(arg_name="msg", queue_name="events", connection="SERVICEBUS_CONNECTION")
def process_events(msg: func.ServiceBusMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

Dry-run example:

```bash
azure-functions-scaffold add servicebus process-events --project-root ./my-api --dry-run
```

Generated Output (previewed function module):

```python
import azure.functions as func

bp = func.Blueprint()


@bp.service_bus_queue_trigger(arg_name="msg", queue_name="events", connection="SERVICEBUS_CONNECTION")
def process_events(msg: func.ServiceBusMessage) -> None:
    _ = msg.get_body().decode("utf-8")
```

Result:

- creates `app/functions/<name>.py`
- updates `function_app.py` to import and register the new Blueprint
- creates `tests/test_<name>.py` when the project includes a `tests/` directory
- updates `host.json` for binding-based triggers
- updates `local.settings.json.example` for Service Bus additions when needed

### Failure Conditions

The command exits with status `1` when:

- `project-name` is missing outside interactive mode
- `project-name` is empty after trimming
- `project-name` is `.` or `..`
- `--destination` exists and is not a directory
- unsupported preset or Python version is requested
- target directory already exists
- git initialization is requested but `git` is unavailable

For `add`, the command exits with status `1` when:

- the trigger is unsupported
- the project root does not look like a scaffolded project
- the generated function module already exists
- the function name is invalid
- `function_app.py` cannot be updated safely

## `templates`

Lists the built-in scaffold templates.

Current output includes:

```text
http: HTTP-trigger Azure Functions Python v2 application.
timer: Timer-trigger Azure Functions Python v2 application.
queue: Queue-trigger Azure Functions Python v2 application.
blob: Blob-trigger Azure Functions Python v2 application.
servicebus: Service Bus-trigger Azure Functions Python v2 application.
```

## `presets`

Lists the built-in project presets.

Current output includes:

```text
minimal: Minimal HTTP function with no additional quality tooling. [tooling: none]
standard: HTTP function with Ruff and pytest defaults. [tooling: ruff, pytest]
strict: HTTP function with Ruff, mypy, and pytest defaults. [tooling: ruff, mypy, pytest]
```

## `--version`

Prints the installed package version and exits.

## Output Contract

On success:

- exit code `0`
- created directory is ready for dependency installation and local checks

On failure:

- exit code `1` for scaffold validation errors
- human-readable error message is printed to stdout

## Non-Goals for Current CLI

Not currently supported:

- selecting multiple templates in one command
- overwriting existing projects
- post-generation dependency installation
- durable orchestrations and activities

## Future CLI Surface

Likely future additions:

- richer interactive tooling selection beyond preset choice
- additional deployment-oriented templates
