# Templates

The CLI supports the most common Azure Functions triggers. Each trigger-based template follows the Blueprint pattern, automatically generating the trigger, a corresponding service, and a test file. The LangGraph template uses a different structure based on `LangGraphApp`.

### Template Overview

| Template | CLI Command | Primary Use Case |
| :--- | :--- | :--- |
| **HTTP** | `afs new <name> --template http` | APIs, webhooks, synchronous requests. |
| **Timer** | `afs new <name> --template timer` | Scheduled tasks, clean-up jobs, reports. |
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
afs new my-api --template http
```

*   **Generates**: `app/functions/http.py`, `app/services/hello_service.py`, `tests/test_http.py`.
*   **Key points**: Configured with a default `hello` route and JSON response handling.

### Timer Template

Triggers functions on a schedule using CRON expressions.

```bash
afs new nightly-job --template timer
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

!!! tip "Local Development"
    Use [Azurite](https://github.com/Azure/Azurite) to simulate Azure Storage Queues locally.

### Blob Template

Triggers when a blob is uploaded or updated in a storage container.

```bash
afs worker blob my-image-resizer
```

*   **Generates**: `app/functions/blob.py`, `app/services/blob_service.py`, `tests/test_blob.py`.
*   **Key points**: Default container path is `samples-workitems/{name}`.

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
*   **Key points**: Uses `azure.functions.durable_functions`. Requires Azurite for state management.

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
