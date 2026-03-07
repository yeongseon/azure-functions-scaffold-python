# Style Guide

## Repository Code Style

### Python

- target Python `3.10+`
- keep functions small and explicit
- prefer standard library types and `pathlib.Path`
- use type hints for public and internal code paths when reasonable

### Tooling

- lint with `ruff`
- format with `ruff format`
- test with `pytest`

### Imports

- keep imports sorted
- avoid unnecessary indirection
- avoid wildcard imports

### Error Handling

- raise specific, readable exceptions for user-facing validation failures
- keep CLI errors actionable and short

## Template Style

Generated template code should:

- be easy to read without project-specific context
- represent a maintainable baseline, not a toy snippet
- separate Azure trigger code from business logic
- stay lint-clean and format-clean

## Documentation Style

- prefer short sections with concrete examples
- document current behavior separately from future ideas
- avoid claiming support for features that are not implemented
- write all documentation in English

## Comment Style

- write all code comments in English
- keep comments short and explain intent, not obvious syntax

## Naming Conventions

### Repository

- package name: `azure_functions_scaffold`
- CLI command: `azure-functions-scaffold`

### Generated Project

- `function_app.py` is the Azure Functions app entrypoint
- `app/functions/` contains trigger-facing modules
- `app/services/` contains business logic
- `app/schemas/` contains simple request/response models
- `app/core/` contains cross-cutting concerns

## Change Discipline

When behavior changes:

- update tests
- update public docs
- validate the generated scaffold
