# Durable Workflow Example

This walkthrough creates a Durable Functions project with an orchestrator,
activities, and an HTTP starter endpoint, then runs everything locally.

## What You Will Build

You will create a durable workflow that:

- starts an orchestration via an HTTP POST
- calls multiple activity functions sequentially
- collects results and returns them through a status endpoint
- runs locally with Azurite and Core Tools

## 1) Generate the Project

```bash
afs advanced new --template durable --preset standard my-workflow
```

Set up environment and dependencies:

```bash
cd my-workflow
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Run quality checks:

```bash
make check-all
```

## 2) Understand the Durable Pattern

The generated project contains three function types in a single module:

**HTTP Starter** — receives a POST request and starts a new orchestration
instance:

```python
@durable_blueprint.route(
    route="orchestrators/{functionName}",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
@durable_blueprint.durable_client_input(client_name="client")
async def http_start(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    instance_id = await client.start_new(req.route_params["functionName"])
    logging.info("Started orchestration with ID '%s'.", instance_id)
    return client.create_check_status_response(req, instance_id)
```

**Orchestrator** — coordinates activity calls using generator-style `yield`:

```python
@durable_blueprint.orchestration_trigger(context_name="context")
def hello_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, list[str]]:
    results: list[str] = []
    results.append((yield context.call_activity("say_hello", "Tokyo")))
    results.append((yield context.call_activity("say_hello", "Seattle")))
    results.append((yield context.call_activity("say_hello", "London")))
    return results
```

**Activity** — performs a single unit of work:

```python
@durable_blueprint.activity_trigger(input_name="city")
def say_hello(city: str) -> str:
    return build_greeting(city)
```

!!! note "Durable Functions imports"
    Durable uses `azure.durable_functions` (imported as `df`)
    alongside the standard `azure.functions` package.

## 3) Generated Layout

```text
my-workflow/
├── function_app.py
├── app/
│   ├── functions/durable.py
│   └── services/durable_service.py
├── tests/test_durable.py
├── local.settings.json.example
└── pyproject.toml
```

- `app/functions/durable.py` — all three function types (starter, orchestrator, activity).
- `app/services/durable_service.py` — business logic called by activities.
- `tests/test_durable.py` — tests service functions directly.

## 4) Azurite Setup

Durable Functions require `AzureWebJobsStorage` for orchestration state
management. Start Azurite before running locally.

Using npm:

```bash
npm install -g azurite
azurite --silent --location .azurite --debug .azurite/debug.log
```

Using Docker:

```bash
docker run --rm -p 10000:10000 -p 10001:10001 -p 10002:10002 \
  mcr.microsoft.com/azure-storage/azurite
```

Create active local settings file:

```bash
cp local.settings.json.example local.settings.json
```

## 5) Run and Test Locally

```bash
func start
```

Start the orchestration by sending a POST to the starter endpoint:

```bash
curl -X POST "http://localhost:7071/api/orchestrators/hello_orchestrator"
```

The response includes a `statusQueryGetUri` field — use that URL directly
to poll orchestration progress:

```bash
# Copy the statusQueryGetUri value from the POST response
curl "<statusQueryGetUri from response>"
```

Expected completed output:

```json
{
  "runtimeStatus": "Completed",
  "output": ["Hello, Tokyo!", "Hello, Seattle!", "Hello, London!"]
}
```

## 6) Customize the Workflow

Add a new activity and wire it into the orchestrator.

Add a formatting function to `app/services/durable_service.py`:

```python
def format_greeting(greeting: str) -> str:
    return greeting.upper()
```

Add the activity in `app/functions/durable.py`:

```python
@durable_blueprint.activity_trigger(input_name="greeting")
def format_result(greeting: str) -> str:
    return format_greeting(greeting)
```

Update the orchestrator to call the new activity after each greeting:

```python
results.append((yield context.call_activity("say_hello", "Tokyo")))
results.append((yield context.call_activity("format_result", results[-1])))
```

## 7) Testing Strategy

The generated test validates the service layer directly:

```python
def test_build_greeting_returns_city_greeting() -> None:
    result = build_greeting("Tokyo")
    assert result == "Hello, Tokyo!"
```

Run tests:

```bash
pytest
```

Durable orchestrations are best tested through their service functions rather
than the orchestration framework. Keep activity logic in `app/services/` and
write unit tests against those functions.

!!! tip "Keep activities thin"
    Treat activity functions as adapters: extract inputs, call a service
    function, return the result. Test the service function.

## Troubleshooting Notes

!!! warning "Orchestration not starting"
    Verify Azurite is running and `local.settings.json` has
    `AzureWebJobsStorage` configured.

!!! warning "Status URL returns 404"
    The `{functionName}` in the route must match the decorated orchestrator
    function name exactly (`hello_orchestrator`).

!!! warning "Orchestrator yield syntax"
    Orchestrators use Python generators with `yield`, not `async/await`.
    Each `yield context.call_activity(...)` suspends until the activity
    completes.

## Next Steps

- See [Worker Triggers](worker_triggers.md) for queue, blob, and messaging
  patterns.
- See [Templates](../guide/templates.md) for the full template list.
- See [Troubleshooting](../guide/troubleshooting.md) for runtime diagnostics.
