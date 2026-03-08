# Contributing

## Scope

This project provides a pragmatic scaffold for Azure Functions Python v2 applications.
Contributions should improve one of these areas:

- CLI usability
- template quality
- generated project quality
- test coverage
- documentation

## Development Setup

```bash
make install
```

## Local Checks

Run these before opening a PR:

```bash
make check-all
make docs
```

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

## Code of Conduct

Be respectful and inclusive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.
