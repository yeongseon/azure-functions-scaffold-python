# Introduction

`azure-functions-scaffold` is a CLI for creating and evolving Azure Functions
Python v2 projects with consistent architecture and practical defaults.

It generates the wiring you would otherwise repeat manually:

- `function_app.py` entrypoint structure
- function module layout under `app/functions/`
- service and schema boundaries
- optional quality tooling and integrations

## Who This Guide Is For

- **Production teams** that need repeatable structure across multiple apps.
- **Platform engineers** standardizing starter templates and CI behavior.
- **API developers** who want OpenAPI and validation support from day one.

## Core Workflow

1. Generate a project with `afs new`.
2. Add triggers over time with `afs add`.
3. Keep business logic in services, trigger code thin.
4. Use preset-driven quality checks in CI.

```bash
pip install azure-functions-scaffold
afs new my-api --preset standard
cd my-api
pip install -e .[dev]
func start
```

## Built-In Building Blocks

### Templates

- `http`
- `timer`
- `queue`
- `blob`
- `servicebus`

### Presets

- `minimal`: no extra tooling
- `standard`: Ruff + pytest
- `strict`: Ruff + mypy + pytest

### Feature Flags

- `--with-openapi` for HTTP documentation routes
- `--with-validation` for HTTP request/response validation
- `--with-doctor` for diagnostics integration (`make doctor`)

!!! note "Command alias"
    `afs` and `azure-functions-scaffold` are equivalent. Use whichever fits your
    shell scripts and team conventions.

## Recommended Reading Order

1. [Getting Started](getting-started.md)
2. [Configuration](configuration.md)
3. [Templates](templates.md)
4. [Features and Presets](features.md)
5. [Expanding Your Project](expanding.md)

## Example-Driven Learning

If you prefer concrete flows over reference docs, jump to:

- [HTTP API Example](../examples/http_api.md)
- [Timer Job Example](../examples/timer_job.md)
- [Full Stack Example](../examples/full_stack.md)
