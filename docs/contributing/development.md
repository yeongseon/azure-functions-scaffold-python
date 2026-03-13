# Development Environment

This guide explains how to set up your local environment for developing azure-functions-scaffold.

## Prerequisites

Ensure you have the following installed on your system:

- Python 3.10 or higher
- Git
- GNU Make
- Hatch (installed automatically via `make install`)

## Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/azure-functions-scaffold.git
   cd azure-functions-scaffold
   ```

2. Initialize the development environment:
   ```bash
   make install
   ```
   This command creates a virtual environment, installs dependencies using Hatch, and sets up pre-commit hooks.

## Project Layout

```text
src/azure_functions_scaffold/
├── templates/          # Jinja2 templates for project generation
├── generator.py        # Logic for adding functions to existing projects
├── scaffolder.py       # Core logic for creating new projects
├── cli.py              # Typer-based command line interface
└── __init__.py         # Package entry and version definition
```

## Makefile Targets

Use these commands to manage your development workflow:

| Target | Description |
| :--- | :--- |
| `make install` | Initial setup (venv, hatch, pre-commit hooks) |
| `make format` | Format code using Ruff and Black |
| `make lint` | Run style checks and type analysis |
| `make test` | Run the full test suite |
| `make cov` | Run tests and generate a coverage report |
| `make security` | Run a Bandit security scan |
| `make check-all` | Run format, lint, test, and security checks |
| `make docs` | Build project documentation |
| `make docs-serve` | Serve documentation locally for preview |
| `make build` | Create distribution packages in `dist/` |
| `make clean` | Remove build artifacts and temporary files |
| `make clean-all` | Full cleanup including virtual environments |

## Code Quality Tools

The project uses several tools to maintain high standards:

| Tool | Version | Purpose |
| :--- | :--- | :--- |
| Ruff | 0.15.5 | Fast linter and formatter (line-length 100) |
| Black | 26.3.0 | Deterministic code formatter (line-length 100) |
| Mypy | 1.19.1 | Static type checker (strict mode) |
| Bandit | 1.9.4 | Security vulnerability scanner |
| Pre-commit | Latest | Runs checks automatically before every commit |

## Working with Templates

Templates are located in `src/azure_functions_scaffold/templates/`. They use Jinja2 syntax to generate Azure Functions project files.

When modifying templates:
1. Identify the template file in the `templates/` directory.
2. Update the Jinja2 variables or structure.
3. Verify the changes by running `make test` to ensure the scaffolder still generates valid projects.
4. Manually inspect generated files if you introduce new complex logic.

## Version Management

The package version is defined in `src/azure_functions_scaffold/__init__.py`. We follow Semantic Versioning (SemVer).

To bump the version and prepare a release, use:
- `make release-patch`: 0.0.x
- `make release-minor`: 0.x.0
- `make release-major`: x.0.0

These commands update the version file and generate a changelog using git-cliff.

## Building and Publishing

To build the package:
```bash
make build
```

To test the distribution on TestPyPI:
```bash
make publish-test
```

To release to the official PyPI:
```bash
make publish-pypi
```
