# Azure Functions Scaffold

[![PyPI](https://img.shields.io/pypi/v/azure-functions-scaffold.svg)](https://pypi.org/project/azure-functions-scaffold/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/azure-functions-scaffold/)
[![CI](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml)
[![Release](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/release.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/release.yml)
[![Security Scans](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-scaffold/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-scaffold)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://yeongseon.github.io/azure-functions-scaffold/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Read this in: [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

Scaffolding CLI for production-ready Azure Functions Python v2 projects.

## Why Use It

Starting a new Azure Functions project means setting up boilerplate: `host.json`, `function_app.py`, directory structure, tooling config, and tests. `azure-functions-scaffold` generates a production-ready project layout in one command, so you can focus on business logic from the start.

## Scope

- Azure Functions Python **v2 programming model**
- Decorator-based `func.FunctionApp()` applications
- CLI-driven project generation and expansion
- Templates for HTTP, Timer, Queue, Blob, and Service Bus triggers

This tool generates project scaffolds. It does **not** provide runtime libraries.

## Features

- `azure-functions-scaffold new` command for project generation
- Five built-in templates: HTTP, Timer, Queue, Blob, Service Bus
- `azure-functions-scaffold add` command for expanding existing projects
- Optional integrations: `--with-openapi`, `--with-validation`, `--with-doctor`
- Preset tooling levels: `--preset minimal|standard|strict`
- Interactive guided setup via `--interactive`
- Short alias: `afs` works as a drop-in for `azure-functions-scaffold`

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
azure-functions-scaffold new my-api
cd my-api
pip install -e .
func start
```

Open `http://localhost:7071/api/hello` in your browser.

Expected response:

```text
Hello, World!
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
|  |  `- logging.py         # Structured JSON logging
|  |- functions/
|  |  `- http.py            # HTTP trigger (Blueprint)
|  |- schemas/
|  |  `- request_models.py  # Request/response models
|  `- services/
|     `- hello_service.py   # Business logic
`- tests/
   `- test_http.py          # Pytest tests
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
| http | `azure-functions-scaffold new my-api` | REST APIs, webhooks |
| timer | `azure-functions-scaffold new my-job --template timer` | Scheduled tasks, cron |
| queue | `azure-functions-scaffold new my-worker --template queue` | Message processing (Azurite) |
| blob | `azure-functions-scaffold new my-blob --template blob` | File processing (Azurite) |
| servicebus | `azure-functions-scaffold new my-bus --template servicebus` | Enterprise messaging |

Note: `afs` is short for `azure-functions-scaffold`. Both work.

Template defaults:

- `http`: public HTTP endpoint and service module.
- `timer`: scheduled trigger using NCRONTAB expression settings.
- `queue`: Storage Queue trigger ready for local Azurite development.
- `blob`: Blob trigger scaffold for file-ingestion pipelines.
- `servicebus`: Service Bus trigger scaffold with development placeholders.

## Optional Features

- `--with-openapi` - Swagger UI + OpenAPI spec endpoints
- `--with-validation` - Pydantic request/response validation
- `--with-doctor` - Health check diagnostics
- `--preset minimal|standard|strict` - Tooling level
- `--interactive` - Guided project setup

Example combinations:

```bash
azure-functions-scaffold new my-api --preset strict --with-validation
azure-functions-scaffold new my-api --with-openapi --with-validation
azure-functions-scaffold new my-api --template timer --preset minimal
```

## Expand Your Project

Add functions to an existing scaffolded project:

```bash
azure-functions-scaffold add http get-user --project-root ./my-api
azure-functions-scaffold add timer cleanup --project-root ./my-api
azure-functions-scaffold add queue sync-jobs --project-root ./my-api
azure-functions-scaffold add blob ingest-reports --project-root ./my-api
azure-functions-scaffold add servicebus process-events --project-root ./my-api
```

Preview additions before writing files:

```bash
azure-functions-scaffold add servicebus process-events --project-root ./my-api --dry-run
```

Common expansion flow:

1. Add a trigger with `azure-functions-scaffold add <trigger> <name>`.
2. Implement business logic under `app/services`.
3. Update contracts in `app/schemas` if needed.
4. Add or update tests in `tests`.

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

- Full docs: [yeongseon.github.io/azure-functions-scaffold](https://yeongseon.github.io/azure-functions-scaffold/)
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

- [azure-functions-validation](https://github.com/yeongseon/azure-functions-validation) — Request and response validation
- [azure-functions-openapi](https://github.com/yeongseon/azure-functions-openapi) — OpenAPI and Swagger UI
- [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging) — Structured logging
- [azure-functions-doctor](https://github.com/yeongseon/azure-functions-doctor) — Diagnostic CLI
- [azure-functions-python-cookbook](https://github.com/yeongseon/azure-functions-python-cookbook) — Recipes and examples

## Disclaimer

This project is an independent community project and is not affiliated with,
endorsed by, or maintained by Microsoft.

Azure and Azure Functions are trademarks of Microsoft Corporation.

## License

MIT
