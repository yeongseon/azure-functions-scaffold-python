# Tutorials

This guide provides end-to-end walkthroughs for each function template available in the CLI. You will learn how to generate, test, and customize projects for different Azure Functions scenarios.

## HTTP API

The default template generates a RESTful API endpoint with a clean separation between trigger logic and business services.

### Generate the Project

Run the following command to create a new project using the `azure-functions-scaffold` CLI (aliased as `afs`):

```bash
afs new my-api
cd my-api
make install
```

### Explore the Generated Code

The generator creates a modular structure where the function entry point is separated from the business logic.

```python
# app/functions/http.py
from __future__ import annotations

import azure.functions as func

from app.services.hello_service import build_greeting

http_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@http_blueprint.route(
    route="hello",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "world")
    message = build_greeting(name)
    return func.HttpResponse(message, status_code=200)
```

The business logic resides in a dedicated service file:

```python
# app/services/hello_service.py
from __future__ import annotations


def build_greeting(name: str) -> str:
    clean_name = name.strip() or "world"
    return f"Hello, {clean_name}!"
```

The `function_app.py` file registers the blueprint:

```python
# function_app.py
from __future__ import annotations

import azure.functions as func

from app.core.logging import configure_logging
from app.functions.http import http_blueprint

# azure-functions-scaffold: function imports

configure_logging()

app = func.FunctionApp()
# azure-functions-scaffold: function registrations
app.register_functions(http_blueprint)
```

### Customize the Logic

To return a JSON response with a timestamp, update the service first:

```python
# app/services/hello_service.py
from __future__ import annotations
from datetime import datetime


def build_greeting(name: str) -> dict[str, str]:
    clean_name = name.strip() or "world"
    return {
        "message": f"Hello, {clean_name}!",
        "timestamp": datetime.utcnow().isoformat()
    }
```

Then update the function to return a JSON response:

```python
# app/functions/http.py
from __future__ import annotations

import json

import azure.functions as func

from app.services.hello_service import build_greeting

http_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@http_blueprint.route(
    route="hello",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "world")
    data = build_greeting(name)
    return func.HttpResponse(
        body=json.dumps(data),
        mimetype="application/json",
        status_code=200,
    )
```

### Run the Tests

Verify your changes using the included test suite.

```bash
make test
```

The standard preset includes a unit test for the HTTP trigger:

```python
# tests/test_http.py
from __future__ import annotations

import azure.functions as func

from app.functions.http import hello


def test_hello_returns_named_greeting() -> None:
    request = func.HttpRequest(
        method="GET",
        url="http://localhost/api/hello",
        params={"name": "Azure"},
        body=b"",
    )

    response = hello(request)

    assert response.status_code == 200
    assert response.get_body() == b"Hello, Azure!"
```

### Run Locally

Start the local Azure Functions runtime:

```bash
func start
```

In a separate terminal, send a request:

```bash
curl "http://localhost:7071/api/hello?name=Azure"
```

Expected output:

```text
Hello, Azure!
```

### Expand with `add`

Use the `add` command to append new functions to an existing project. The CLI generates the function file, a test, and registers the blueprint in `function_app.py` automatically.

```bash
afs add http users --project-root .
```

The CLI generates a skeleton for the new endpoint:

```python
# app/functions/users.py
from __future__ import annotations

import azure.functions as func

users_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@users_blueprint.route(
    route="users",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def users(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body="TODO: implement users",
        status_code=200,
    )
```

From here, create a service in `app/services/users_service.py`, wire it into the function, and add assertions to the generated test file. See [Expanding Your Project](expanding.md) for the full workflow.

## Scheduled Job (Timer)

Timer triggers are ideal for maintenance tasks, database cleanups, or periodic reporting.

### Generate the Project

```bash
afs new maintenance-jobs --template timer
cd maintenance-jobs
make install
```

### Explore the Generated Code

The timer trigger is configured with a cron expression.

```python
# app/functions/timer.py
from __future__ import annotations

import logging

import azure.functions as func

from app.services.maintenance_service import build_tick_message

timer_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@timer_blueprint.timer_trigger(
    arg_name="timer",
    schedule="0 */5 * * * *",
    run_on_startup=False,
    use_monitor=True,
)
def cleanup(timer: func.TimerRequest) -> None:
    if timer.past_due:
        logging.warning("Timer trigger 'cleanup' is running late.")

    logging.info(build_tick_message())
```

```python
# app/services/maintenance_service.py
from __future__ import annotations


def build_tick_message() -> str:
    return "Timer trigger executed."
```

### Customize the Logic

Modify the service to perform a concrete task, such as purging expired cache entries.

```python
# app/services/maintenance_service.py
from __future__ import annotations

def purge_expired_entries(max_age_hours: int = 24) -> str:
    # Logic to connect to storage/database and delete old records
    count = 42 
    return f"Purged {count} expired entries older than {max_age_hours} hours."
```

Update the function entry point:

```python
# app/functions/timer.py
def cleanup(timer: func.TimerRequest) -> None:
    summary = purge_expired_entries()
    logging.info(summary)
```

### Run the Tests

The timer test uses `SimpleNamespace` to mock the `TimerRequest` object. Run the suite with:

```bash
make test
```

The generated test verifies the function runs without raising exceptions:
```python
# tests/test_timer.py
from __future__ import annotations

from types import SimpleNamespace

from app.functions.timer import cleanup


def test_cleanup_runs_without_error() -> None:
    timer = SimpleNamespace(past_due=False)

    cleanup(timer)
```

## Queue Worker

Queue triggers allow you to process messages from Azure Queue Storage asynchronously.

### Generate the Project

```bash
afs new worker-service --template queue
cd worker-service
make install
```

### Explore the Generated Code

The generator includes a `local.settings.json.example` file configured for [Azurite](https://github.com/Azure/Azurite), the local Azure Storage emulator.

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
```

!!! tip "Local Storage Emulation"
    Queue and Blob templates use `UseDevelopmentStorage=true`, which requires [Azurite](https://github.com/Azure/Azurite) to be running locally. Install it with `npm install -g azurite` and start it with `azurite --silent`.

```python
# app/functions/queue.py
from __future__ import annotations

import logging

import azure.functions as func

from app.services.queue_service import decode_queue_message

queue_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@queue_blueprint.queue_trigger(
    arg_name="message",
    queue_name="work-items",
    connection="AzureWebJobsStorage",
)
def process_queue_message(message: func.QueueMessage) -> None:
    payload = decode_queue_message(message)
    logging.info("Processed queue message: %s", payload)
```

### Customize the Logic

Update the service to parse JSON payloads for structured processing.

```python
# app/services/queue_service.py
from __future__ import annotations
import json
import azure.functions as func

def decode_queue_message(message: func.QueueMessage) -> dict:
    raw_body = message.get_body().decode("utf-8")
    return json.loads(raw_body)
```

Example usage in the function:

```python
# app/functions/queue.py
def process_queue_message(message: func.QueueMessage) -> None:
    data = decode_queue_message(message)
    order_id = data.get("order_id")
    action = data.get("action")
    logging.info("Processing order %s with action %s", order_id, action)
```

### Run the Tests

```bash
make test
```

The generated test uses `SimpleNamespace` to simulate the queue message:
```python
# tests/test_queue.py
from __future__ import annotations

from types import SimpleNamespace

from app.functions.queue import process_queue_message


def test_process_queue_message_runs_without_error() -> None:
    message = SimpleNamespace(get_body=lambda: b"hello from queue")

    process_queue_message(message)
```

## Blob Processor

Blob triggers respond to new or updated files in Azure Blob Storage.

### Generate the Project

```bash
afs new image-processor --template blob
cd image-processor
make install
```

### Explore the Generated Code

```python
# app/functions/blob.py
from __future__ import annotations

import logging

import azure.functions as func

from app.services.blob_service import describe_blob

blob_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@blob_blueprint.blob_trigger(
    arg_name="blob",
    path="samples-workitems/{name}",
    connection="AzureWebJobsStorage",
)
def process_blob(blob: func.InputStream) -> None:
    logging.info(describe_blob(blob))
```

```python
# app/services/blob_service.py
from __future__ import annotations

import azure.functions as func


def describe_blob(blob: func.InputStream) -> str:
    return f"Processed blob {blob.name} ({blob.length} bytes)"
```

### Customize the Logic

Modify the service to read the blob content, such as calculating a checksum or parsing CSV rows.

```python
# app/services/blob_service.py
import hashlib

def describe_blob(blob: func.InputStream) -> str:
    content = blob.read()
    checksum = hashlib.md5(content).hexdigest()
    return f"Blob: {blob.name}, MD5: {checksum}"
```

### Run the Tests

```bash
make test
```
```python
# tests/test_blob.py
from __future__ import annotations

from types import SimpleNamespace

from app.functions.blob import process_blob


def test_process_blob_runs_without_error() -> None:
    blob = SimpleNamespace(name="samples-workitems/input.txt", length=16)

    process_blob(blob)
```

## Service Bus Consumer

The Service Bus template is designed for high-throughput enterprise messaging.

### Generate the Project

```bash
afs new messaging-node --template servicebus
cd messaging-node
make install
```

### Explore the Generated Code

The local configuration requires a Service Bus connection string.

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ServiceBusConnection": "Endpoint=sb://localhost/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=replace-me"
  }
}
```

!!! note "Service Bus Emulation"
    Unlike Storage Queues, Azure Service Bus does not have a local emulator. For local development, use an actual Service Bus namespace or a test namespace in Azure.

```python
# app/functions/servicebus.py
from __future__ import annotations

import logging

import azure.functions as func

from app.services.servicebus_service import decode_servicebus_message

servicebus_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@servicebus_blueprint.service_bus_queue_trigger(
    arg_name="message",
    queue_name="work-items",
    connection="ServiceBusConnection",
)
def process_servicebus_message(message: func.ServiceBusMessage) -> None:
    payload = decode_servicebus_message(message)
    logging.info("Processed Service Bus message: %s", payload)
```

### Customize the Logic

Implement event validation to ensure incoming messages meet your schema requirements.

```python
# app/services/servicebus_service.py
from __future__ import annotations
import json
import azure.functions as func

def decode_servicebus_message(message: func.ServiceBusMessage) -> dict:
    raw_body = message.get_body().decode("utf-8")
    data = json.loads(raw_body)
    
    if "event_type" not in data:
        raise ValueError("Missing event_type in message")
        
    return data
```

### Run the Tests

```bash
make test
```
```python
# tests/test_servicebus.py
from __future__ import annotations

from types import SimpleNamespace

from app.functions.servicebus import process_servicebus_message


def test_process_servicebus_message_runs_without_error() -> None:
    message = SimpleNamespace(get_body=lambda: b"hello from service bus")

    process_servicebus_message(message)
```

## Next Steps

Now that you have explored the primary templates, check out the advanced configurations:

- [Project Structure](project-structure.md): Understand the role of each directory.
- [Templates](templates.md): Learn about preset variations and configuration options.
- [Expanding](expanding.md): Detailed guide on using the `add` command.
