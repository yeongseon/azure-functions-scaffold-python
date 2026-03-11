# azure-functions-scaffold

[![PyPI](https://img.shields.io/pypi/v/azure-functions-scaffold.svg)](https://pypi.org/project/azure-functions-scaffold/)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://pypi.org/project/azure-functions-scaffold/)
[![CI](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/ci-test.yml)
[![Security Scans](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml/badge.svg)](https://github.com/yeongseon/azure-functions-scaffold/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-scaffold/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-scaffold)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://img.shields.io/badge/docs-gh--pages-blue)](https://yeongseon.github.io/azure-functions-scaffold/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Scaffolding CLI for production-leaning Azure Functions Python v2 projects.

## Scope

- Azure Functions Python **v2 programming model**
- Decorator-based `func.FunctionApp()` applications
- Opinionated but lightweight project generation
- Interactive bootstrap, presets, and function expansion

This project does **not** support the legacy `function.json`-based Python v1 programming model.

## Features

- `azure-functions-scaffold new <project-name>`
- `azure-functions-scaffold new <project-name> --template http|timer|queue|blob|servicebus`
- `azure-functions-scaffold new --interactive`
- `azure-functions-scaffold new <project-name> --preset minimal|standard|strict`
- `azure-functions-scaffold add http <function-name>`
- `azure-functions-scaffold add timer <function-name>`
- `azure-functions-scaffold add queue <function-name>`
- `azure-functions-scaffold add blob <function-name>`
- `azure-functions-scaffold add servicebus <function-name>`
- Embedded trigger-specific project templates
- Configurable test, lint, and packaging defaults in generated output
- Small service-oriented application layout

## Installation

```bash
pip install azure-functions-scaffold
```

For local development:

```bash
git clone https://github.com/yeongseon/azure-functions-scaffold.git
cd azure-functions-scaffold
make install
```

## Usage

Create a new HTTP project in the current directory:

```bash
azure-functions-scaffold new my-api
```

Create a new timer project:

```bash
azure-functions-scaffold new my-job --template timer
```

Create a queue-trigger project for local Azurite development:

```bash
azure-functions-scaffold new my-worker --template queue
```

Create a blob-trigger project for local Azurite development:

```bash
azure-functions-scaffold new my-blob-worker --template blob
```

Create a Service Bus-trigger project:

```bash
azure-functions-scaffold new my-bus-worker --template servicebus
```

Create a project interactively:

```bash
azure-functions-scaffold new --interactive
```

Create a strict project with GitHub Actions enabled:

```bash
azure-functions-scaffold new my-api --preset strict --python-version 3.12 --github-actions
```

Create a new project in a specific destination:

```bash
azure-functions-scaffold new my-api --destination ./sandbox
```

List available templates:

```bash
azure-functions-scaffold templates
```

List available presets:

```bash
azure-functions-scaffold presets
```

Add a new function to an existing scaffolded project:

```bash
azure-functions-scaffold add http get-user --project-root ./my-api
azure-functions-scaffold add timer cleanup --project-root ./my-api
azure-functions-scaffold add queue sync-jobs --project-root ./my-api
azure-functions-scaffold add blob ingest-reports --project-root ./my-api
azure-functions-scaffold add servicebus process-events --project-root ./my-api
```

## Generated Project

The current HTTP template generates a structure similar to:

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
|  |- core/
|  |  `- logging.py
|  |- functions/
|  |  `- http.py
|  |- schemas/
|  |  `- request_models.py
|  `- services/
|     `- hello_service.py
`- tests/
   `- test_http.py
```

The timer, queue, blob, and service bus templates follow the same top-level layout,
but start with trigger-specific function, service, and test modules. The queue and blob
templates are ready for local Azurite-based development, while the service bus template
starts with a development connection placeholder.

## Development

Use Makefile commands as the canonical entry points:

```bash
make install
make check-all
make docs
make build
```

## Documentation

- Full docs: [yeongseon.github.io/azure-functions-scaffold](https://yeongseon.github.io/azure-functions-scaffold/)
- Root planning docs: `AGENT.md`, `DESIGN.md`, `PRD.md`
- Release history: `CHANGELOG.md`
- CLI guide: `docs/cli.md`
- Template spec: `docs/template_spec.md`
- Style guide: `docs/style_guide.md`
- Roadmap: `docs/roadmap.md`
- Contributing guide: `CONTRIBUTING.md`

## Disclaimer

This project is an independent community project and is not affiliated with,
endorsed by, or maintained by Microsoft.

Azure and Azure Functions are trademarks of Microsoft Corporation.

## License

MIT
