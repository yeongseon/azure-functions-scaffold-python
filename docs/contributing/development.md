# Development Environment

This guide explains how to set up your local environment for developing azure-functions-scaffold-python.

## Prerequisites

Ensure you have the following installed on your system:

- Python 3.11 or newer (the project supports `>=3.11,<3.15`)
- Git
- GNU Make
- Hatch (install once in an isolated tool environment)

## Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/<your-github-username>/azure-functions-scaffold-python.git
   cd azure-functions-scaffold-python
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
| `make install` | Idempotent Hatch environment and pre-commit hooks |
| `make install-ci` | Install into the selected CI interpreter, not Hatch's default |
| `make doctor` | Read-only prerequisites; required missing tools return nonzero |
| `make format` | Format code using Ruff |
| `make lint` | Run style checks and type analysis |
| `make test` | Offline generator/unit/structure tests, coverage >=95% |
| `make cov` | Run tests and generate a coverage report |
| `make security` | Run a Bandit security scan |
| `make check` | Non-mutating format/lint/types once/security/workflow checks |
| `make integration` | Ten isolated generated suites and run-owned HTTP host/Azurite |
| `make verify` / `make check-all` | Full local verification / exact alias |
| `make e2e-azure` | Explicit existing deployed candidate, separate from local verification |
| `make report` | Read saved evidence without running tests |
| `make docs` | Build project documentation |
| `make docs-serve` | Serve documentation locally for preview |
| `make build` | Create distribution packages in `dist/` |
| `make clean` | Remove build artifacts and temporary files |
| `make clean-all` | Full cleanup including virtual environments |

Focused targets are PARTIAL. Required generated suites must collect and execute
positive cases; exit 5, unexpected skips and missing results never PASS. See the
[root contributing guide](https://github.com/yeongseon/azure-functions-scaffold-python/blob/main/CONTRIBUTING.md#generated-projects-and-diagnostics-policy)
for Doctor's required-rule/advisory policy and redacted evidence schema.
Integration requires `func` and `azurite`, uses unique loopback ports and owned
process groups, and never stops shared services. Check/test need neither tool.
Local execution uses Hatch Python 3.11; CI preserves Python 3.11–3.14 and the
minimum-dependency constraints on the matrix interpreter.

## Generated Artifacts

Several development tools produce files that must **never** be committed to source control. They bloat the repository, create noisy diffs across machines, and can leak environment-specific data.

The repository's `.gitignore` already blocks the common offenders, but contributors should still verify before staging:

| Path / Pattern | Produced By | How To Clean |
| :--- | :--- | :--- |
| `.venv/`, `venv/`, `env/` | Virtual environment creation (`make install`, `hatch env create`) | `make clean-all` |
| `.coverage`, `.coverage.*` | `pytest --cov` (the `.coverage.*` files are per-process data emitted by `coverage run --parallel`) | `make clean` |
| `coverage.xml`, `htmlcov/` | `make cov` and CI coverage steps | `make clean` |
| `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | `pytest`, `mypy`, `ruff` | `make clean` |
| `build/`, `dist/`, `*.egg-info/` | `make build`, `hatch build` | `make clean` |
| `site/` | `make docs` (MkDocs output) | `make clean` |
| `test-results/` | Lane JUnit, coverage, logs, summaries and provenance | `make clean` |
| `__pycache__/`, `*.py[cod]` | Python interpreter bytecode | `make clean` |
| `.DS_Store` | macOS Finder metadata | `make clean-all` |

### Verify before committing

Always run `git status` before `git add`, and avoid bulk-staging from the repository root:

```bash
git status
git add <specific file>      # preferred over `git add .` or `git add -A`
```

If a generated artifact appears in `git status`, prefer fixing `.gitignore` (and submitting that fix as part of your change) over committing the artifact.

### If something was committed by mistake

Generated artifacts that slip into history should be removed in a dedicated cleanup commit:

```bash
git rm -r --cached <path>    # untrack without deleting from disk
git commit -m "chore: stop tracking <path>"
```

Then confirm `.gitignore` blocks the path so it cannot be reintroduced.

## Code Quality Tools

The project uses several tools to maintain high standards:

| Tool | Version | Purpose |
| :--- | :--- | :--- |
| Ruff | see `pyproject.toml` | Fast linter and formatter (line-length 100); replaces Black |
| Mypy | see `pyproject.toml` | Static type checker (strict mode) |
| Bandit | see `pyproject.toml` | Security vulnerability scanner |
| Pre-commit | see `.pre-commit-config.yaml` | Runs checks automatically before every commit |

Exact pinned versions live in the `[tool.hatch.envs.default]` dependency list in `pyproject.toml` and in
`.pre-commit-config.yaml`. Black is not used: `ruff format` is the only formatter.

## Working with Templates

Templates are located in `src/azure_functions_scaffold/templates/`. They use Jinja2 syntax to generate Azure Functions project files.

When modifying templates:
1. Identify the template file in the `templates/` directory.
2. Update the Jinja2 variables or structure.
3. Verify the changes by running `make test` to ensure the scaffolder still generates valid projects.
4. Manually inspect generated files if you introduce new complex logic.

## Version Management

The package version is defined in `src/azure_functions_scaffold/__init__.py`. We follow Semantic Versioning (SemVer).

Do not bump the version by hand. Release Please derives it from Conventional Commit messages and
updates the version file and `CHANGELOG.md` in its Release PR. See [Release Process](../release_process.md).

## Building and Publishing

To build the package:
```bash
make build
```

To test the distribution on TestPyPI:
```bash
make publish-test
```

PyPI releases are published only by the gated `publish-pypi.yml` workflow, started by the release tag.
