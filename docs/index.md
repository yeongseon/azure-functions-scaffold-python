# Azure Functions Scaffold

Scaffold production-ready Azure Functions Python v2 projects in one command.

`azure-functions-scaffold` gives you a clean, modular starting point with
opinionated defaults, optional feature integrations, and predictable structure.
Use the short alias `afs` or the full command name interchangeably.

## The 5-Second Rule

If you only remember one command, remember this:

```bash
afs new my-api
```

That creates a working HTTP project scaffold with a practical default preset.

## Why Teams Use It

- Start fast without copy-pasting old repos.
- Keep function projects consistent across engineers.
- Separate triggers, services, schemas, and runtime setup from day one.
- Add more triggers later using a safe, repeatable command.

!!! note "Scope"
    This tool scaffolds Azure Functions Python v2 projects. It does not replace
    Azure Functions runtime tools or hosting services.

## Feature Overview

### Commands

- `afs new <name>` creates a new project.
- `afs add <trigger> <name>` adds a function module to an existing project.
- `afs templates` lists built-in templates.
- `afs presets` lists quality/tooling presets.

### Templates

- `http`
- `timer`
- `queue`
- `blob`
- `servicebus`

### Presets

- `minimal`: no extra quality tooling
- `standard`: Ruff + pytest (default)
- `strict`: Ruff + mypy + pytest

### Optional Feature Flags

- `--with-openapi`: OpenAPI routes and Swagger UI for HTTP projects
- `--with-validation`: request/response model validation for HTTP projects
- `--with-doctor`: adds `azure-functions-doctor` integration and command target

## What You Get in a New Project

Typical scaffold layout:

```text
my-api/
|- function_app.py
|- host.json
|- local.settings.json.example
|- pyproject.toml
|- Makefile
|- app/
|  |- core/
|  |- functions/
|  |- services/
|  `- schemas/
`- tests/
```

Design goals of this layout:

- keep trigger wiring in `app/functions/`
- keep business logic in `app/services/`
- keep contracts in `app/schemas/`
- keep runtime utilities in `app/core/`
- keep behavior verifiable in `tests/`

## Quick Start Flow

```bash
pip install azure-functions-scaffold
afs new my-api --preset standard
cd my-api
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
func start
```

Then hit the default route:

```text
http://localhost:7071/api/hello
```

## Common Command Patterns

```bash
# Strict HTTP API with docs and validation
afs new orders-api --preset strict --with-openapi --with-validation

# Timer-based scheduled job
afs new nightly-job --template timer --preset standard

# Add another endpoint to an existing project
afs add http get_user --project-root ./orders-api

# Preview generation without writing files
afs new sandbox-api --dry-run
```

!!! tip "Safe rollout"
    Use `--dry-run` in CI or automation to validate planned output before
    writing files.

## Choose Your Path

- New to the scaffold?
  Start with [Getting Started](guide/getting-started.md).
- Deciding flags and presets?
  Read [Configuration](guide/configuration.md).
- Need end-to-end samples?
  Use [HTTP API](examples/http_api.md), [Timer Job](examples/timer_job.md), and
  [Full Stack](examples/full_stack.md) examples.
- Integrating programmatically?
  See [API Reference](reference/api.md).

## Operational Notes

- Project names must start with an alphanumeric character and can include
  alphanumerics, `_`, and `-`.
- `afs add` must point to a valid scaffold project root.
- Local execution and publish flows use Azure Functions Core Tools (`func`).

## Keep Reading

- [Introduction](guide/index.md)
- [Templates](guide/templates.md)
- [Features and Presets](guide/features.md)
- [Troubleshooting](guide/troubleshooting.md)
- [FAQ](faq.md)
