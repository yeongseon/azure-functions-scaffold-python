# Template Specification

## Purpose

Templates define the generated project structure and default source files for scaffolded Azure Functions applications.

## Current Template Set

Current built-in template:

- `http`

Location:

```text
src/azure_functions_scaffold/templates/http/
```

## Rendering Rules

### File Discovery

Every file under the template root is rendered into the destination project.

### File Name Rules

- files ending in `.j2` are emitted without the `.j2` suffix
- path segments may use placeholders such as `__project_name__`

### Content Rules

Template files are rendered with Jinja2.

Current context variables:

- `project_name`

## HTTP Template Contract

The HTTP template must generate:

- Azure Functions Python v2 `function_app.py`
- at least one Blueprint-backed HTTP trigger module
- one service module
- one schema or model example
- one test file
- project-level tooling files

## Required Output Files

Minimum expected files:

```text
function_app.py
host.json
local.settings.json.example
pyproject.toml
.gitignore
.funcignore
README.md
app/functions/http.py
app/services/hello_service.py
app/schemas/request_models.py
app/core/logging.py
tests/test_http.py
```

## Quality Contract

Generated projects must satisfy:

```bash
pytest
ruff check .
ruff format --check .
```

## Template Authoring Rules

- keep files small and readable
- prefer simple imports and explicit structure
- avoid placeholders that are not currently populated
- avoid environment-specific absolute paths
- keep examples realistic but minimal

## Extension Guidelines

When adding a new template:

1. create a new template directory under `src/azure_functions_scaffold/templates/`
2. define the required output contract for that template
3. add CLI selection logic
4. add tests that validate rendered output
5. verify lint, format, and test behavior in the generated project

