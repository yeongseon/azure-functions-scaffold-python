# Templates

The CLI supports the most common Azure Functions triggers. Each template follows the Blueprint pattern, automatically generating the trigger, a corresponding service, and a test file.

### Template Overview

| Template | CLI Command | Primary Use Case |
| :--- | :--- | :--- |
| **HTTP** | `http` | APIs, webhooks, synchronous requests. |
| **Timer** | `timer` | Scheduled tasks, clean-up jobs, reports. |
| **Queue** | `queue` | Async message processing from Azure Storage. |
| **Blob** | `blob` | File processing, image resizing, data ingestion. |
| **Service Bus** | `servicebus` | Enterprise messaging with topics or queues. |

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
afs new queue-processor --template queue
```

*   **Generates**: `app/functions/queue.py`, `app/services/queue_service.py`, `tests/test_queue.py`.
*   **Key points**: Requires `AzureWebJobsStorage` connection string.

!!! tip "Local Development"
    Use [Azurite](https://github.com/Azure/Azurite) to simulate Azure Storage Queues locally.

### Blob Template

Triggers when a blob is uploaded or updated in a storage container.

```bash
afs new image-resizer --template blob
```

*   **Generates**: `app/functions/blob.py`, `app/services/blob_service.py`, `tests/test_blob.py`.
*   **Key points**: Default container path is `samples-workitems/{name}`.

### Service Bus Template

Handles high-throughput enterprise messages from Service Bus queues or topics.

```bash
afs new bus-listener --template servicebus
```

*   **Generates**: `app/functions/servicebus.py`, `app/services/servicebus_service.py`, `tests/test_servicebus.py`.
*   **Key points**: Uses a `SERVICEBUS_CONNECTION` placeholder in your settings.

### What's Next?

Enhance your project with [Features and Presets](features.md) like OpenAPI or Pydantic validation.
