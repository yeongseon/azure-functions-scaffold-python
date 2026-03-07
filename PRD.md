# Product Requirements Document

## 1. Overview

**azure-functions-scaffold** is an opinionated scaffolding CLI for creating production-ready Azure Functions Python v2 projects.

While Azure Functions Core Tools (`func init`, `func new`) provide basic project and function templates, they are intentionally minimal and not optimized for modern Python development workflows.

This tool generates **lint-clean, test-ready, and Pythonic Azure Functions Python v2 projects** aligned with the official programming model while improving developer experience.

The project belongs to a broader Azure Functions Python tooling ecosystem alongside:

- `azure-functions-doctor`
- `azure-functions-openapi`
- `azure-functions-validation`

## 2. Problem Statement

### 2.1 Minimal Official Templates

The official workflow:

```bash
func init
func new
```

creates learning-oriented examples, not production-oriented foundations.

Common issues:

- no lint configuration
- no typing-oriented structure
- no testing setup
- no service layer separation
- example code that often needs cleanup before team use

### 2.2 Poor Python Developer Experience

Python developers expect project generators comparable to:

- `django-admin startproject`
- `poetry new`
- `uv init`
- `cookiecutter`

Azure Functions lacks a small, opinionated generator focused on Python teams.

### 2.3 Inconsistent Project Structures

Without a scaffold, each team invents its own conventions for:

- trigger modules
- business logic
- configuration boundaries
- tests

This increases maintenance cost and reduces consistency across projects.

## 3. Goals

### 3.1 Opinionated Project Generator

Generate Azure Functions Python v2 projects with a clean default structure.

### 3.2 Pythonic Developer Experience

Align with modern Python conventions:

- `pyproject.toml`
- `ruff`
- `pytest`
- modular application layout

### 3.3 Official Programming Model Alignment

Generated projects must follow the Azure Functions Python v2 programming model:

- decorator-based triggers
- `function_app.py`
- optional Blueprint modularization

### 3.4 High-Quality Default Code

Generated code must:

- pass lint checks
- be format-clean
- include basic tests
- model maintainable separation of concerns

## 4. Non-Goals

Initial release excludes:

- metrics frameworks
- distributed tracing
- telemetry abstractions
- observability platforms
- middleware ecosystems
- deep Azure SDK integration

## 5. Target Users

### 5.1 Python Developers

Developers building APIs or background workloads with Azure Functions.

### 5.2 Azure Functions Teams

Teams seeking a repeatable and maintainable Python project structure.

### 5.3 Open Source Contributors

Contributors who want a solid base for serverless Python community tooling.

## 6. Core Features

### 6.1 CLI Project Generator

```bash
azure-functions-scaffold new my-api
```

### 6.2 Interactive Setup

Not in MVP. May be added later for guided project selection and configuration.

### 6.3 Project Templates

MVP includes:

- HTTP trigger project

Planned future templates:

- Timer trigger
- Queue trigger
- Durable Functions

## 7. Generated Project Structure

```text
my-api/
|- function_app.py
|- host.json
|- local.settings.json.example
|- pyproject.toml
|- .gitignore
|- .funcignore
|- README.md
|- app/
|  |- functions/
|  |  `- http.py
|  |- services/
|  |  `- hello_service.py
|  |- schemas/
|  |  `- request_models.py
|  `- core/
|     `- logging.py
`- tests/
   `- test_http.py
```

## 8. Quality Standards

Generated code must satisfy:

```bash
ruff check .
ruff format --check .
pytest
```

## 9. Technical Design

Recommended stack:

- Python 3.10+
- Typer
- Jinja2

## 10. CLI UX

Current command:

```bash
azure-functions-scaffold new <project-name>
```

Potential future commands:

```bash
azure-functions-scaffold add trigger
azure-functions-scaffold doctor
```

## 11. MVP Definition

Phase 1 is complete when the CLI can generate an HTTP-trigger Azure Functions project that:

- is created from a single command
- contains a realistic app layout
- passes lint and format checks
- includes a working example test

## 12. Success Metrics

The project is successful if:

- developers use it to bootstrap Azure Functions Python apps
- contributors expand template coverage
- the project becomes a recognized Azure Functions Python developer tool
