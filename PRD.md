# PRD - azure-functions-scaffold-python

## Overview

`azure-functions-scaffold` is a scaffolding CLI for creating production-leaning Azure Functions
Python v2 projects.

It generates a clean project structure with testing, linting, and packaging defaults that are
better suited to real Python teams than the minimal starter templates from Azure Functions Core Tools.

## Problem Statement

The default Azure Functions initialization flow is useful for learning, but often leaves teams to
fill in the same missing pieces repeatedly:

- project structure conventions
- linting and formatting configuration
- test setup
- application layer separation
- maintainable `pyproject.toml` defaults

Without a scaffold, each team reinvents these decisions and quality drifts across repositories.

## Goals

- Generate Azure Functions Python v2 projects with clear, maintainable defaults.
- Align scaffolded output with modern Python packaging and quality tooling.
- Keep the CLI small and explicit.
- Produce generated projects that are easy to extend by hand.
- Support interactive bootstrap for first-time project creation.
- Support opinionated presets that reduce repeated CLI decisions.
- Support adding new function modules after initial project creation.

## Non-Goals

- Replacing Azure Functions runtime concepts
- Building a general-purpose application framework
- Supporting the legacy `function.json`-based Python v1 model
- Managing deployment or infrastructure

## Primary Users

- Python developers bootstrapping Azure Functions services
- Teams that want repeatable repository structure
- Maintainers building consistent Azure Functions project foundations

## Core Use Cases

- Create a new HTTP-trigger Azure Functions project from a single command
- Create queue-, blob-, and Service Bus-trigger projects for local-first development
- Create a new project interactively without memorizing flags
- Choose between `minimal`, `standard`, and `strict` presets
- Generate project files that already include tests and linting defaults
- Add new HTTP, timer, queue, blob, and Service Bus functions to an existing scaffolded codebase
- Standardize project layout across repositories

## Success Criteria

- Generated projects pass their own lint and test checks
- Representative scaffold output remains smoke-tested in CI
- The CLI stays simple enough to understand without external scaffolding systems

## Example-First Design

### Philosophy

A scaffolding CLI is only as good as the projects it generates. `azure-functions-scaffold`
treats every generated project as a runnable example — if a developer cannot go from
`pip install` to `func start` with a working endpoint in under two minutes, the scaffold
has failed its purpose.

### Quick Start (Hello World)

The shortest path from zero to a running Azure Function:

```bash
pip install azure-functions-scaffold
azure-functions-scaffold new my-api
cd my-api
pip install -e .
func start
```

Open `http://localhost:7071/api/hello` and get:

```text
Hello, World!
```

Every template (HTTP, timer, queue, blob, Service Bus) produces a project that runs
out of the box with zero manual configuration.

### Why Examples Matter

1. **Lower entry barrier.** The generated project IS the example. A developer evaluates the
   scaffold by running the output, not by reading documentation.
2. **AI agent discoverability.** Tools like GitHub Copilot, Cursor, and Claude Code recommend
   libraries based on README, PRD, and example content. Clear CLI usage patterns and
generated output help AI agents suggest `azure-functions-scaffold` for project setup prompts.
3. **Cookbook role.** For niche ecosystems, generated project templates serve as the primary
   reference architecture. Each template teaches real project structure, not toy examples.
4. **Proven approach.** FastAPI, LangChain, SQLAlchemy, and Pandas all achieved early adoption
   through extensive, copy-paste-friendly examples. Scaffold takes this further — the entire
   output is a production-leaning example.

### Template Inventory

| Template | Command | Use Case |
|---|---|---|
| HTTP | `scaffold new my-api` | REST APIs, webhooks |
| Timer | `scaffold new my-job --template timer` | Scheduled tasks, cron |
| Queue | `scaffold new my-worker --template queue` | Message processing (Azurite) |
| Blob | `scaffold new my-blob --template blob` | File processing (Azurite) |
| Service Bus | `scaffold new my-bus --template servicebus` | Enterprise messaging |

All generated projects pass their own lint and test checks in CI. New templates must
produce output that works out of the box without manual intervention.
