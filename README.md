# azure-functions-scaffold

`azure-functions-scaffold` is an opinionated scaffolding CLI for production-ready Azure Functions Python v2 projects.

It generates a clean Azure Functions app structure with:

- Azure Functions Python v2 programming model
- a default HTTP trigger example
- `pyproject.toml`
- `ruff` configuration
- `pytest` skeleton
- a small service-oriented application layout

## Status

Current MVP scope:

- `azure-functions-scaffold new <project-name>`
- `azure-functions-scaffold templates`
- HTTP project template
- Python 3.10+
- embedded Jinja2 templates

Planned but not implemented yet:

- additional trigger templates
- `add` commands
- interactive setup
- doctor/integration commands

## Installation

```bash
pip install -e .[dev]
```

For package consumers:

```bash
pip install azure-functions-scaffold
```

## Usage

Create a new project in the current directory:

```bash
azure-functions-scaffold new my-api
```

Create a new project in a specific destination:

```bash
azure-functions-scaffold new my-api --destination ./sandbox
```

List available templates:

```bash
azure-functions-scaffold templates
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

## Development

Install dependencies:

```bash
make install
```

Run checks:

```bash
make format
make lint
make test
make check
make build
```

Raw commands are still available when needed:

```bash
pip install -e .[dev]
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m build
```

If you run tests from Windows against a WSL UNC path and coverage locks the SQLite data file, point `COVERAGE_FILE` to a local temp path before running `pytest`.

## Documentation

- [PRD](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\PRD.md)
- [Architecture](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\ARCH.md)
- [Design](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\DESIGN.md)
- [CLI Spec](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\docs\CLI.md)
- [Template Spec](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\docs\TEMPLATE_SPEC.md)
- [Style Guide](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\docs\STYLE_GUIDE.md)
- [Roadmap](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\docs\ROADMAP.md)
- [Contributing](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\CONTRIBUTING.md)
- [Agent Guide](\\wsl.localhost\Ubuntu-24.04\root\Github\azure-functions-scaffold\AGENTS.md)
