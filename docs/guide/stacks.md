# Recommended Stacks

Pre-tested package combinations for common Azure Functions project types.

Each stack lists the toolkit packages to install, what they provide together,
and the scaffold command to generate a matching project.

## API Stack

**Best for:** REST APIs, webhooks, and public-facing HTTP services.

| Package | Role |
|---------|------|
| `azure-functions-openapi` | Swagger UI + OpenAPI 3.1 spec |
| `azure-functions-validation` | Pydantic request/response validation |
| `azure-functions-logging` | Structured JSON logging |

```bash
afs new my-api --profile api
```

```text
# requirements.txt
azure-functions
azure-functions-openapi
azure-functions-validation
azure-functions-logging
```

**What you get:** validated HTTP endpoints with auto-generated API docs,
structured logs, and request correlation IDs.

---

## DB API Stack

**Best for:** CRUD APIs backed by PostgreSQL, MySQL, or SQL Server.

| Package | Role |
|---------|------|
| `azure-functions-openapi` | Swagger UI + OpenAPI 3.1 spec |
| `azure-functions-validation` | Pydantic request/response validation |
| `azure-functions-db` | Declarative database input/output bindings |
| `azure-functions-logging` | Structured JSON logging |

```bash
afs new my-api --profile db-api
```

```text
# requirements.txt
azure-functions
azure-functions-openapi
azure-functions-validation
azure-functions-db[postgres]
azure-functions-logging
```

**What you get:** everything in the API Stack plus declarative database
read/write bindings via `@db.input()` and `@db.output()`.

---

## AI Agent Stack

**Best for:** LangGraph-based conversational agents and AI workflows.

| Package | Role |
|---------|------|
| `azure-functions-langgraph` | LangGraph HTTP deployment adapter |
| `azure-functions-openapi` | Swagger UI for agent endpoints |
| `azure-functions-logging` | Structured JSON logging |

```bash
afs new my-agent --template langgraph
```

```text
# requirements.txt
azure-functions
langgraph
azure-functions-langgraph
azure-functions-openapi
azure-functions-logging
```

**What you get:** invoke, stream, and health endpoints for LangGraph graphs,
plus API documentation and structured logging.

---

## Full Stack

**Best for:** production applications that need everything — validated APIs,
database access, health diagnostics, and observability.

| Package | Role |
|---------|------|
| `azure-functions-openapi` | Swagger UI + OpenAPI 3.1 spec |
| `azure-functions-validation` | Pydantic request/response validation |
| `azure-functions-db` | Declarative database bindings |
| `azure-functions-logging` | Structured JSON logging |
| `azure-functions-doctor` | Pre-deploy diagnostic checks |

```bash
afs new my-api --profile db-api --with-doctor
```

```text
# requirements.txt
azure-functions
azure-functions-openapi
azure-functions-validation
azure-functions-db[postgres]
azure-functions-logging
azure-functions-doctor
```

**What you get:** a fully instrumented API with validation, database access,
API docs, structured logging, and pre-deploy health diagnostics.

---

## Choosing a Stack

| Stack | Scaffold Command | Packages | Use Case |
|-------|-----------------|----------|----------|
| API | `afs new my-api --profile api` | 3 | REST APIs, webhooks |
| DB API | `afs new my-api --profile db-api` | 4 | CRUD with database |
| AI Agent | `afs new my-agent --template langgraph` | 3 | LangGraph agents |
| Full | `afs new my-api --profile db-api --with-doctor` | 5 | Production services |

Start with the smallest stack that covers your needs.
Add packages incrementally — the toolkit is designed for zero coupling between packages.
