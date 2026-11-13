# Templates

The CLI supports the most common Azure Functions triggers. Each trigger-based template follows the Blueprint pattern, automatically generating the trigger, a corresponding service, and a test file. The LangGraph template uses a different structure based on `LangGraphApp`. To preview the exact files each template produces, see [Generated Output](generated-output.md).

### Template Overview

| Template | CLI Command | Primary Use Case |
| :--- | :--- | :--- |
| **HTTP** | `afs new <name>` | APIs, webhooks, synchronous requests. |
| **Timer** | `afs worker timer <name>` | Scheduled tasks, clean-up jobs, reports. |
| **Queue** | `afs worker queue <name>` | Async message processing from Azure Storage. |
| **Blob** | `afs worker blob <name>` | File processing, image resizing, data ingestion. |
| **Service Bus** | `afs worker servicebus <name>` | Enterprise messaging with topics or queues. |
| **Event Hub** | `afs worker eventhub <name>` | High-throughput event stream ingestion. |
| **CosmosDB** | `afs advanced new --template cosmosdb --preset standard <name>` | Change feed processing from Cosmos DB containers. |
| **Durable** | `afs advanced new --template durable --preset standard <name>` | Orchestrated workflows with activities and fan-out. |
| **AI** | `afs advanced new --template ai --preset standard <name>` | Azure OpenAI chat completion endpoints. |
| **LangGraph** | `afs ai agent <name>` | LangGraph agent deployment on Azure Functions. |

### HTTP Template

The default template for building RESTful APIs.

```bash
afs new my-api
```

*   **Generates**: `app/functions/health.py`, `app/functions/webhooks.py`, `app/services/health_service.py`, `app/services/webhook_service.py`, `tests/test_health.py`, `tests/test_webhooks.py`.
*   **Key points**: Includes a `GET /api/health` endpoint (anonymous auth) and a `POST /api/webhooks/inbound` endpoint (FUNCTION auth, HMAC-SHA256 signature verification).

#### Choosing an HTTP starter

`afs new` (identical to `afs api new`) is the **opinionated production API scaffold**, not a minimal
one. It enables the `strict` preset plus OpenAPI, request validation and Doctor. When you want less
generated code, choose a different command rather than a different template:

| Command | Files | Runtime dependencies | Dev extras | Notes |
| :--- | ---: | :--- | :--- | :--- |
| `afs new <name>` / `afs api new <name>` | 25 | `azure-functions`, `azure-functions-logging`, `orjson`, `azure-functions-openapi`, `azure-functions-validation`, `pydantic`, `azure-functions-doctor` | `pytest`, `ruff`, `mypy` | Production-oriented: OpenAPI docs, validation, Doctor, strict tooling. |
| `afs advanced new <name>` (preset `standard`) | 25 | `azure-functions`, `azure-functions-logging`, `orjson` | `pytest`, `ruff` | Same layered layout and tests, no OpenAPI/validation/Doctor. |
| `afs advanced new --preset minimal <name>` | 23 | `azure-functions`, `azure-functions-logging`, `orjson` | none | Smallest generated project from this tool: same layered layout, no generated `tests/`, no dev tooling. |
| `func init` + `func new` | n/a | `azure-functions` | n/a | Official Core Tools; smallest possible start, no layered structure. |

The `minimal` preset changes **tooling only**: it removes the generated tests and dev extras but keeps
the layered `app/` structure (`core`, `dependencies`, `functions`, `schemas`, `services`), the health
and webhook functions, structured logging and `orjson`. It is a lighter project, not a single-file one.
`tests/test_simple_http_starter_contract.py` pins these file lists and dependency sets, so this table
cannot drift unnoticed. None of the commands above changed.

### Timer Template

Triggers functions on a schedule using CRON expressions.

```bash
afs worker timer nightly-job
```

*   **Generates**: `app/functions/timer.py`, `app/services/maintenance_service.py`, `tests/test_timer.py`.
*   **Key points**: Default schedule is set to `0 */5 * * * *` (every 5 minutes) in `host.json` or the trigger decorator.

### Queue Template

Reacts to messages added to an Azure Storage Queue.

```bash
afs worker queue my-queue-processor
```

*   **Generates**: `app/functions/queue.py`, `app/services/queue_service.py`, `tests/test_queue.py`.
*   **Key points**: Requires `AzureWebJobsStorage` connection string.

**Try it offline with a synthetic message**

From a checkout of this repository, `pytest tests/test_worker_smoke_queue.py --no-cov` generates this
worker into a temporary directory, calls `process_queue_message` with a synthetic
`azure.functions.QueueMessage`, and checks the logged payload and the declared trigger. It does not
require Azure, Azurite, credentials, network access or a Functions host. Only a real host and Storage
Queue can verify polling, visibility timeouts, dequeue counts and poison-queue handling. Inside a
generated project, `make test` runs the project's own `tests/test_queue.py` the same way.

!!! tip "Local Development"
    Use [Azurite](https://github.com/Azure/Azurite) to simulate Azure Storage Queues locally.

### Blob Template

Triggers when a blob is uploaded or updated in a storage container.

```bash
afs worker blob my-image-resizer
```

*   **Generates**: `app/functions/blob.py`, `app/services/blob_service.py`, `tests/test_blob.py`.
*   **Key points**: Default container path is `samples-workitems/{name}`.

**Try it offline with a fake `InputStream`**

From a checkout of this repository, `pytest tests/test_worker_smoke_blob.py --no-cov` generates this
worker into a temporary directory, calls `process_blob` with an in-memory `azure.functions.InputStream`
test double, and checks the logged description and the declared trigger. It does not require Azure,
Azurite, credentials, network access or a Functions host. What it does not prove: blob event delivery,
polling latency, blob receipts and poison-blob handling, or the behavior of the real stream object the
host supplies; those need separate integration certification against a real host and Storage account.
Inside a generated project, `make test` runs the project's own `tests/test_blob.py` the same way.

### Service Bus Template

Handles high-throughput enterprise messages from Service Bus queues or topics.

```bash
afs worker servicebus my-bus-listener
```

*   **Generates**: `app/functions/servicebus.py`, `app/services/servicebus_service.py`, `tests/test_servicebus.py`.
*   **Key points**: Uses a `ServiceBusConnection` placeholder in your settings.

### Event Hub Template

Ingests high-throughput event streams from Azure Event Hubs.

```bash
afs worker eventhub my-event-processor
```

*   **Generates**: `app/functions/eventhub.py`, `app/services/eventhub_service.py`, `tests/test_eventhub.py`.
*   **Key points**: Uses an `EventHubConnection` placeholder. Default event hub name is `my-event-hub`.

**Try it offline with a synthetic message**

From a checkout of this repository, `pytest tests/test_worker_smoke_eventhub.py --no-cov` generates
this worker into a temporary directory, calls `process_event` with a synthetic
`azure.functions.EventHubEvent`, and checks the logged payload and the declared trigger. It does not
require Azure, credentials, network access or a Functions host. A real host and Event Hubs are still
needed to verify listener startup, partition ownership, checkpointing and batching. Inside a generated
project, `make test` runs the project's own `tests/test_eventhub.py` the same way.

### CosmosDB Template

Reacts to document changes via the Cosmos DB change feed.

```bash
afs advanced new --template cosmosdb --preset standard my-processor
```

*   **Generates**: `app/functions/cosmosdb.py`, `app/services/cosmosdb_service.py`, `tests/test_cosmosdb.py`.
*   **Key points**: Uses `cosmos_db_trigger_v3` binding. Requires `CosmosDBConnection` and a lease container for tracking.

!!! tip "Local Development"
    Use the [CosmosDB Emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/emulator) for local change feed testing.

### Durable Template

Builds orchestrated workflows with an HTTP starter, orchestrator, and activity functions.

```bash
afs advanced new --template durable --preset standard my-workflow
```

*   **Generates**: `app/functions/durable.py`, `app/services/durable_service.py`, `tests/test_durable.py`.
*   **Key points**: Uses `azure.durable_functions`. Requires Azurite for state management.

### AI Template

Creates an HTTP endpoint backed by Azure OpenAI for chat completions.

```bash
afs advanced new --template ai --preset standard my-ai-api
```

*   **Generates**: `app/functions/ai.py`, `app/services/ai_service.py`, `tests/test_ai.py`.
*   **Key points**: Requires `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT` settings.

### LangGraph Template

Deploys a LangGraph agent as an Azure Functions app using `azure-functions-langgraph`.

```bash
afs ai agent my-agent
```

*   **Generates**: `app/graphs/echo_agent.py`, `function_app.py`, `tests/test_echo_agent.py`.
*   **Key points**: Uses `LangGraphApp` to register graphs. Default scaffold includes an echo agent.

### What's Next?

Enhance your project with [Features and Presets](features.md) like OpenAPI or Pydantic validation.

Want to see exactly what each template produces? Check the [Generated Output](generated-output.md) reference for per-template project trees and `function_app.py` / `host.json` snippets.
