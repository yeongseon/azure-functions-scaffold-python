# Template Specification

## Purpose

Templates define the generated project structure and default source files for scaffolded Azure Functions applications.

## Current Template Set

Current built-in templates:

- `http`
- `timer`
- `queue`
- `blob`
- `servicebus`

Location:

```text
src/azure_functions_scaffold/templates/<template-name>/
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
- `project_slug`
- `python_version`
- `python_upper_bound`
- `preset_name`
- `include_github_actions`
- `include_ruff`
- `include_mypy`
- `include_pytest`

`preset_name` may be `custom` when interactive tooling choices diverge from the selected preset defaults.

## HTTP Template Contract

The HTTP template must generate:

- Azure Functions Python v2 `function_app.py`
- at least one Blueprint-backed HTTP trigger module
- one service module
- one schema or model example
- one test file when pytest is enabled
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

The `minimal` preset intentionally omits `tests/`.

The template now also supports optional output:

```text
Makefile
.github/workflows/ci.yml
```

These files are rendered only when their corresponding options are enabled.

## Trigger Template Contract

All non-HTTP trigger templates must generate:

- Azure Functions Python v2 `function_app.py`
- one Blueprint-backed trigger module
- one service/helper module
- one test file when pytest is enabled
- project-level tooling files

Additional expectations:

- `timer` must run without external emulators
- `queue` and `blob` must be ready for Azurite-backed local development
- `servicebus` must generate a clear development connection placeholder
- binding-based trigger templates must include `extensionBundle` in `host.json`

## Quality Contract

Generated projects should satisfy the commands implied by their selected preset:

```bash
make install
make check-all
```

Preset expectations:

- `minimal`: no extra quality tooling beyond a valid Azure Functions project structure
- `standard`: Ruff and pytest defaults
- `strict`: Ruff, mypy, and pytest defaults

## Template Authoring Rules

- keep files small and readable
- prefer simple imports and explicit structure
- keep placeholder usage aligned with the actual rendering context
- avoid environment-specific absolute paths
- keep examples realistic but minimal
- keep `function_app.py` update markers stable for post-generation `add` commands

## Extension Guidelines

When adding a new template:

1. create a new template directory under `src/azure_functions_scaffold/templates/`
2. define the required output contract for that template
3. add CLI selection logic
4. add tests that validate rendered output
5. verify preset-specific lint, type, and test behavior in the generated project

