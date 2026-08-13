# CosmosDB Change Feed Example

This walkthrough creates a CosmosDB change feed processor that reacts to
document changes, then runs and tests it locally with the CosmosDB emulator.

## What You Will Build

You will create a change feed processor that:

- triggers on document inserts and updates in a CosmosDB container
- processes batches of changed documents
- uses a lease container to track processing state
- is testable with pytest

## 1) Generate the Project

```bash
afs advanced new --template cosmosdb --preset standard my-change-processor
```

Set up environment and dependencies:

```bash
cd my-change-processor
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Run quality checks:

```bash
make check-all
```

## 2) Understand CosmosDB Trigger Defaults

The generated trigger function:

```python
@cosmosdb_blueprint.cosmos_db_trigger_v3(
    arg_name="documents",
    collection_name="my-container",
    database_name="my-database",
    connection_string_setting="CosmosDBConnection",
    lease_collection_name="leases",
    create_lease_collection_if_not_exists=True,
)
def process_cosmos_changes(documents: func.DocumentList) -> None:
    count = describe_documents(documents)
    logging.info("Processed %s Cosmos DB change(s).", count)
```

!!! note "Lease container"
    The lease container tracks which changes have been processed. It enables
    multiple instances to share the change feed without duplicating work. The
    `create_lease_collection_if_not_exists=True` flag creates it automatically.

## 3) Generated Layout

```text
my-change-processor/
├── function_app.py
├── app/
│   ├── functions/cosmosdb.py
│   └── services/cosmosdb_service.py
├── tests/test_cosmosdb.py
├── local.settings.json.example
└── pyproject.toml
```

- `app/functions/cosmosdb.py` — trigger handler that receives document batches.
- `app/services/cosmosdb_service.py` — service function (`describe_documents` returns document count).
- `tests/test_cosmosdb.py` — smoke test passing a plain list as the document batch.

## 4) Local Prerequisites

CosmosDB triggers require the CosmosDB emulator for local development.

Using Docker (Linux):

```bash
docker run --rm -p 8081:8081 -p 10250-10255:10250-10255 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
```

!!! note "Windows"
    On Windows, use the native CosmosDB Emulator installer from the Azure
    documentation.

Create active local settings file and configure the connection:

```bash
cp local.settings.json.example local.settings.json
```

The template includes a placeholder connection string:

```json
{
  "CosmosDBConnection": "AccountEndpoint=https://localhost:8081/;AccountKey=replace-me"
}
```

Replace `replace-me` with the emulator's default account key.

Create the database (`my-database`) and container (`my-container`) in the
emulator before starting the function app.

## 5) Run and Test Locally

```bash
func start
```

Insert or update a document in the `my-container` container using the
emulator's Data Explorer or a small SDK script. Watch the terminal for log output:

```text
Processed 1 Cosmos DB change(s).
```

## 6) Customize the Change Processor

Replace `describe_documents` with actual business logic. Each document in the
batch is a dictionary:

```python
def process_documents(documents: func.DocumentList) -> None:
    for doc in documents:
        doc_id = doc.get("id", "unknown")
        # Route to domain-specific processing
        handle_update(doc_id, doc)
```

Update the trigger handler to call the new service function:

```python
def process_cosmos_changes(documents: func.DocumentList) -> None:
    process_documents(documents)
    logging.info("Processed %s Cosmos DB change(s).", len(documents))
```

!!! tip "Keep trigger modules thin"
    Move document parsing and side effects into `app/services/`. The trigger
    handler should only decode, delegate, and log.

## 7) Key Configuration Parameters

| Parameter | Description |
| :--- | :--- |
| `collection_name` | Source container to watch for changes. |
| `database_name` | Database containing the source container. |
| `connection_string_setting` | App setting name for the CosmosDB connection string. |
| `lease_collection_name` | Container used to store change feed leases. |
| `create_lease_collection_if_not_exists` | Auto-create lease container on first run. |
| `feed_poll_delay` | Delay in milliseconds between feed polls (optional). |

## 8) Testing Strategy

The generated test passes a plain list to the trigger function:

```python
def test_process_cosmos_changes_runs_without_error() -> None:
    documents = [{"id": "1", "data": "hello"}]
    process_cosmos_changes(documents)
```

Run tests:

```bash
pytest
```

This approach works because `func.DocumentList` is compatible with a plain
Python list in the test context. For richer tests, add assertions in the
service layer.

## Troubleshooting Notes

!!! warning "No trigger fires"
    Confirm the CosmosDB emulator is running, the connection string is valid,
    and the database and container exist. The trigger only fires on new changes
    after it starts monitoring.

!!! warning "Lease conflicts"
    Multiple local instances sharing the same lease container can cause
    processing conflicts. Use a unique `lease_collection_name` per instance
    during development.

!!! warning "Emulator SSL errors"
    The CosmosDB emulator uses a self-signed certificate. If connections
    fail, import the emulator certificate into your Python environment's
    trust store or pass `verify=False` to the SDK client during local
    development only.

## Next Steps

- See [Worker Triggers](worker_triggers.md) for queue, blob, and messaging
  patterns.
- See [Durable Workflow](durable_workflow.md) for orchestration workflows.
- See [Templates](../guide/templates.md) for the full template list.
- See [Troubleshooting](../guide/troubleshooting.md) for runtime diagnostics.
