# Azure Functions Scaffold

[![PyPI](https://img.shields.io/pypi/v/azure-functions-scaffold.svg)](https://pypi.org/project/azure-functions-scaffold/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/azure-functions-scaffold/)
[![CI](https://github.com/yeongseon/azure-functions-scaffold-python/actions/workflows/ci-test.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold-python/actions/workflows/ci-test.yml)
[![Release](https://github.com/yeongseon/azure-functions-scaffold-python/actions/workflows/release.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold-python/actions/workflows/release.yml)
[![Security Scans](https://github.com/yeongseon/azure-functions-scaffold-python/actions/workflows/security.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold-python/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-scaffold-python/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-scaffold-python)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://yeongseon.github.io/azure-functions-scaffold-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Read this in: [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

Scaffolding CLI for production-ready Azure Functions Python v2 projects.

Python version support: 3.10-3.13 are GA on Azure Functions; 3.14 is accepted as **Preview**. See [Python version support](docs/guide/configuration.md#python-version-support).

## Why `afs new` instead of `func init`?

`afs new` is **not** a replacement for [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local). It complements them. Use whichever fits your situation.

| Concern | `func init` + `func new` (official) | `afs new` (this project) |
|---|---|---|
| Maintained by | Microsoft | Community |
| Scope | Minimal Functions skeleton | Opinionated, production-leaning starter |
| Project layout | Bare `function_app.py` + `host.json` | Layered: `api/`, `domain/`, `infra/`, tests, CI |
| Auth defaults | `AuthLevel.ANONYMOUS` | `AuthLevel.ANONYMOUS` (pre-wired for HMAC verification in webhooks) |
| Logging | `logging` stdlib | `azure-functions-logging` structured JSON, pre-wired |
| Observability | None pre-wired | Optional `azure-functions-doctor` health checks |
| OpenAPI | None | Optional `azure-functions-openapi` Swagger UI |
| Validation | None | Optional `azure-functions-validation` (Pydantic) |
| Test scaffolding | None | `pytest` setup + sample tests |
| CI | None | GitHub Actions workflow generated |
| Templates | Per-trigger blank function | Trigger + business-pattern templates (HTTP CRUD, webhook, queue worker, etc.) |
| Re-entry | One-shot | `afs api add`, `afs advanced add`, `afs api add-route` extend the same project |
| Lock-in | None | Generates code; no runtime dependency on `afs` after scaffolding |

**Pick `func init`** when you want the smallest possible starting point, are following Microsoft's official tutorials, or need to match the exact layout used in Azure Functions documentation.

**Pick `afs new`** when you want a project that already has structured logging, sane auth defaults, an opinionated layered structure, and CI in place from the first commit - and you can extend it later with `afs api add` / `afs advanced add`.

You can also start with `func init` and migrate manually; `afs new` does not lock you in. The generated project is plain Azure Functions Python code - no runtime dependency on this CLI.

## Why Use It

Starting a new Azure Functions project means setting up boilerplate: `host.json`, `function_app.py`, directory structure, tooling config, and tests. `azure-functions-scaffold` generates a production-ready project layout in one command, so you can focus on business logic from the start.

```mermaid
flowchart LR
    Dev(["Developer"])
    CLI["afs new my-api"]
    T["Templates"]
    P["Generated Project"]
    VAL["azure-functions-validation"]

    Dev --> CLI
    CLI --> T
    T --> P
    CLI --> VAL
    VAL --> P
```
## Scope

- Azure Functions Python **v2 programming model**
- Decorator-based `func.FunctionApp()` applications
- CLI-driven project generation and expansion
- Templates for HTTP, Timer, Queue, Blob, Service Bus triggers, and LangGraph agents

This tool generates project scaffolds. It does **not** provide runtime libraries.

## What this package does not do

This package does not own:

- **Runtime behavior** — intent commands choose optional package wiring during generation, but runtime logic belongs to those packages
- **API documentation** — use [`azure-functions-openapi`](https://github.com/yeongseon/azure-functions-openapi-python) for API documentation and spec generation
- **Request validation** — use [`azure-functions-validation`](https://github.com/yeongseon/azure-functions-validation-python) for request/response validation and serialization
- **Database bindings** — use [`azure-functions-db`](https://github.com/yeongseon/azure-functions-db-python) for database input/output bindings

## Features

- Top-level shortcut: `afs new` creates an API project with production defaults
- Intent-based command groups: `afs api`, `afs worker`, `afs ai`, and `afs advanced`
- API project commands: `afs api new`, `afs api add`, `afs api add-route`, and `afs api add-resource`
- Worker project commands: `afs worker timer|queue|blob|servicebus|eventhub`
- AI project command: `afs ai agent` for LangGraph scaffolds
- Advanced power-user commands: `afs advanced new`, `afs advanced add`, `afs advanced add-route`, and `afs advanced add-resource`
- Optional feature flags (`--with-openapi`, `--with-validation`, `--with-doctor`) and `--preset minimal|standard|strict` available via `afs advanced new`
- Discovery commands: `afs templates` and `afs presets`
- Short alias: `afs` is the primary CLI entry point for `azure-functions-scaffold`

## Installation

```bash
pip install azure-functions-scaffold
```

## Quick Start

Use this 4-step flow to create and run a local HTTP function:

1. Install the CLI.
2. Generate a new project.
3. Install project dependencies.
4. Start the local Functions runtime.

```bash
afs new my-api
cd my-api
pip install -e .
func start
```

Open `http://localhost:7071/api/health` in your browser.

Expected response:

```json
{"status": "ok"}
```

Project names must start with an alphanumeric character and use only letters,
numbers, hyphens, or underscores.

## What You Get

The generated layout separates trigger bindings, business logic, shared runtime
concerns, and tests so teams can scale endpoints without coupling everything to
`function_app.py`.

```text
my-api/
|- function_app.py          # Azure Functions v2 entrypoint
|- host.json                # Runtime configuration
|- local.settings.json.example
|- pyproject.toml           # Dependencies and tooling config
|- app/
|  |- core/
|  |  |- config.py          # Application settings
|  |  `- logging.py         # Structured JSON logging
|  |- dependencies/
|  |  `- __init__.py        # Shared dependencies
|  |- functions/
|  |  |- health.py          # Health check (Blueprint)
|  |  `- webhooks.py        # Webhook receiver (Blueprint)
|  |- schemas/
|  |  `- webhooks.py        # Webhook request/response models
|  `- services/
|     |- health_service.py   # Health check logic
|     `- webhook_service.py  # Webhook processing logic
`- tests/
   |- test_health.py        # Health endpoint tests
   `- test_webhooks.py      # Webhook endpoint tests
```

Why this layout works:

- Keep trigger-specific code in `app/functions`.
- Keep reusable business rules in `app/services`.
- Keep model contracts in `app/schemas`.
- Keep observability and runtime helpers in `app/core`.
- Keep integration checks in `tests`.

## Templates

| Template | Command | Use Case |
| --- | --- | --- |
| http | `afs new my-api` | REST APIs, webhooks |
| timer | `afs worker timer my-job` | Scheduled tasks, cron |
| queue | `afs worker queue my-worker` | Message processing (Azurite) |
| blob | `afs worker blob my-blob` | File processing (Azurite) |
| servicebus | `afs worker servicebus my-bus` | Enterprise messaging |
| langgraph | `afs ai agent my-agent` | LangGraph AI agent deployment |

Note: `afs` is short for `azure-functions-scaffold`. Both work.

Template defaults:

- `http`: health endpoint and webhook receiver with HMAC signature verification.
- `timer`: scheduled trigger using NCRONTAB expression settings.
- `queue`: Storage Queue trigger ready for local Azurite development.
- `blob`: Blob trigger scaffold for file-ingestion pipelines.
- `servicebus`: Service Bus trigger scaffold with development placeholders.

## Optional Features

Intent commands pre-select optional features based on project intent:

- `afs api new <name>` (or `afs new <name>`) includes OpenAPI, validation, and doctor integration
- `afs worker <trigger> <name>` and `afs ai agent <name>` apply trigger-specific defaults

Use `afs advanced new <name>` when you need direct control over feature flags:

- `--with-openapi` - Swagger UI + OpenAPI spec endpoints
- `--with-validation` - Pydantic request/response validation
- `--with-doctor` - Health check diagnostics
- `--with-db` - Database bindings (SQLAlchemy) *(planned — not yet available in CLI)*
- `--preset minimal|standard|strict` - Tooling level

## Expand Your Project

### Add a route

Add a lightweight HTTP endpoint (blueprint + test):

```bash
afs api add-route status --project-root ./my-api
```

### Add a resource

Add a full CRUD resource with blueprint, service, schema, and test:

```bash
afs api add-resource products --project-root ./my-api
```

### Add a function

Add a single HTTP function module:

```bash
afs api add get-user --project-root ./my-api
```

### Add non-HTTP triggers

```bash
afs advanced add timer cleanup --project-root ./my-api
afs advanced add queue sync-jobs --project-root ./my-api
afs advanced add blob ingest-reports --project-root ./my-api
afs advanced add servicebus process-events --project-root ./my-api
```

Preview additions before writing files:

```bash
afs api add-resource products --project-root ./my-api --dry-run
```

Common expansion flow:

1. Add API endpoints with `afs api add-route <name>` for simple routes or `afs api add-resource <name>` for full CRUD.
2. Add non-HTTP triggers with `afs advanced add <trigger> <name>`.
3. Implement business logic under `app/services`.
4. Update contracts in `app/schemas` if needed.
5. Add or update tests in `tests`.

## Deploy

```bash
func azure functionapp publish <APP_NAME>
```

Before publishing:

- Set required app settings for production connections.
- Review `host.json` and function auth levels.
- Run your project checks (`pytest`, lint, and formatting).
- Verify startup locally with `func start`.

## Documentation

- Full docs: [yeongseon.github.io/azure-functions-scaffold-python](https://yeongseon.github.io/azure-functions-scaffold-python/)
- Python version support: [`docs/guide/configuration.md#python-version-support`](docs/guide/configuration.md#python-version-support)
- Getting Started: [`docs/guide/getting-started.md`](docs/guide/getting-started.md)
- CLI Reference: [`docs/reference/cli.md`](docs/reference/cli.md)
- Project Structure: [`docs/guide/project-structure.md`](docs/guide/project-structure.md)
- Templates: [`docs/guide/templates.md`](docs/guide/templates.md)
- Troubleshooting: [`docs/guide/troubleshooting.md`](docs/guide/troubleshooting.md)

## Development

Use Makefile commands as the canonical entry points:

```bash
make install
make check-all
make docs
make build
```

## Ecosystem

This package is part of the **Azure Functions Python DX Toolkit**.

**Design principle:** `azure-functions-scaffold` owns project generation and template expansion. It does not provide runtime libraries — runtime behavior belongs to [`azure-functions-openapi`](https://github.com/yeongseon/azure-functions-openapi-python) (API documentation and spec generation), [`azure-functions-validation`](https://github.com/yeongseon/azure-functions-validation-python) (request/response validation), and [`azure-functions-langgraph`](https://github.com/yeongseon/azure-functions-langgraph-python) (LangGraph runtime exposure).

| Package | Role |
|---------|------|
| [azure-functions-openapi](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI spec generation and Swagger UI |
| [azure-functions-validation](https://github.com/yeongseon/azure-functions-validation-python) | Request/response validation and serialization |
| [azure-functions-db](https://github.com/yeongseon/azure-functions-db-python) | Database bindings for SQL, PostgreSQL, MySQL, SQLite, and Cosmos DB |
| [azure-functions-langgraph](https://github.com/yeongseon/azure-functions-langgraph-python) | LangGraph deployment adapter for Azure Functions |
| **azure-functions-scaffold** | Project scaffolding CLI |
| [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging-python) | Structured logging and observability |
| [azure-functions-doctor](https://github.com/yeongseon/azure-functions-doctor-python) | Pre-deploy diagnostic CLI |
| [azure-functions-durable-graph](https://github.com/yeongseon/azure-functions-durable-graph-python) | Manifest-first graph runtime with Durable Functions *(experimental)* |
| [azure-functions-knowledge-python](https://github.com/yeongseon/azure-functions-knowledge-python) | Knowledge retrieval (RAG) decorators |
| [azure-functions-cookbook-python](https://github.com/yeongseon/azure-functions-cookbook-python) | Dogfood examples — runnable recipes that exercise the full toolkit |

## For AI Coding Assistants

This package includes `llms.txt` and `llms-full.txt` files in the repository root designed specifically for LLM-assisted development:

- **`llms.txt`** — Concise overview of the CLI, commands, templates, and quick start
- **`llms-full.txt`** — Complete CLI reference with all options, patterns, and workflows

Use these files to provide context to AI coding assistants when working with Azure Functions scaffolding.

Reference:
- Repository: https://github.com/yeongseon/azure-functions-scaffold-python
- Issue: [#40](https://github.com/yeongseon/azure-functions-scaffold-python/issues/40)

## Disclaimer

This project is an independent community project and is not affiliated with,
endorsed by, or maintained by Microsoft.

Azure and Azure Functions are trademarks of Microsoft Corporation.

## License

MIT
