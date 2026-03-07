# Contributing

## Scope

This project aims to provide a pragmatic, production-leaning scaffold for Azure Functions Python v2 applications. Contributions should improve one of these areas:

- CLI usability
- template quality
- generated code quality
- test coverage
- documentation

## Development Setup

```bash
make install
```

## Local Checks

Run these before opening a PR:

```bash
make format
make lint
make test
make build
```

Equivalent raw commands are:

```bash
pip install -e .[dev]
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m build
```

If you run tests from Windows against a WSL UNC path, set `COVERAGE_FILE` to a local temp path before running `pytest`.

## Project Layout

```text
src/azure_functions_scaffold/
|- cli.py
|- scaffolder.py
`- templates/
   `- http/

tests/
docs/
```

## Contribution Guidelines

- Keep changes aligned with the product direction in `PRD.md`.
- Keep changes aligned with the design guardrails in `DESIGN.md`.
- Write all documentation and code comments in English.
- Prefer small, reviewable pull requests.
- Update documentation when behavior or public interfaces change.
- Add or update tests for any CLI or rendering behavior change.
- Keep repository test coverage at or above 90 percent.
- Keep generated output lint-clean and format-clean.

## Template Changes

When changing files under `src/azure_functions_scaffold/templates/`:

- verify the generated project still runs `pytest`
- verify the generated project passes `ruff check .`
- verify the generated project passes `ruff format --check .`
- preserve Azure Functions Python v2 compatibility

## Design Principles

- prefer explicit, boring defaults
- avoid premature template complexity
- keep generated code small but realistic
- separate trigger entrypoints from service logic

## Pull Request Checklist

- behavior is documented
- tests cover the change
- repo checks pass
- generated template checks pass when relevant
