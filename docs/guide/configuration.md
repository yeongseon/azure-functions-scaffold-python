# Configuration

This guide explains how `azure-functions-scaffold` maps CLI options to generated
project behavior. Use it when you need predictable output across environments,
teams, and CI pipelines.

## Configuration Philosophy

The scaffold follows three principles:

1. Deterministic generation: same inputs create the same files.
2. Explicit options: behavior changes only through named flags.
3. Production-first defaults: the default preset (`standard`) includes practical
   quality tooling without being heavy.

!!! note "Single source of truth"
    Project configuration starts at generation time. The CLI encodes choices
    into generated files (`pyproject.toml`, `Makefile`, `function_app.py`), so
    new contributors can understand the setup by reading the project itself.

## Command Surface

You will primarily configure projects through:

- `afs new <name>` for project creation.
- `afs api add <name>` for adding HTTP function modules.
- `afs advanced add <trigger> <name>` for adding non-HTTP function modules.

`afs` is a short alias for `azure-functions-scaffold` and behaves exactly the
same.

## `advanced new` Command Options

For projects that need a non-HTTP template, an explicit preset, or feature
flags, use `afs advanced new` (the power-user variant). The top-level shortcut
`afs new` is an alias for `afs api new` and accepts only `--destination`,
`--python-version`, `--github-actions` / `--no-github-actions`,
`--git` / `--no-git`, `--azd` / `--no-azd`, `--dry-run`, `--overwrite`,
and `--yes`.

```bash
afs advanced new [OPTIONS] PROJECT_NAME
```

### Core Selection Flags

| Flag | Default | Values | Purpose |
| :--- | :--- | :--- | :--- |
| `--destination`, `-d` | `.` | path | Parent directory where project folder is created. |
| `--template`, `-t` | `http` | `http`, `timer`, `queue`, `blob`, `servicebus`, `eventhub`, `cosmosdb`, `durable`, `ai`, `langgraph` | Initial trigger template. |
| `--preset` | `standard` | `minimal`, `standard`, `strict` | Quality tooling baseline. |
| `--python-version` | `3.10` | `3.10`, `3.11`, `3.12`, `3.13`, `3.14 (Preview)` | Python version pin for generated metadata. |

## Python version support

| Version | Status on Azure Functions |
|---------|--------------------------|
| 3.10    | GA                        |
| 3.11    | GA                        |
| 3.12    | GA (recommended default)  |
| 3.13    | GA                        |
| 3.14    | **Preview** - limited regional and plan support; Flex Consumption remote build may be unavailable. Verify against the [Microsoft support matrix](https://learn.microsoft.com/azure/azure-functions/supported-languages) before production use. |

The scaffolder accepts all listed versions. Choose 3.12 for the broadest compatibility, or 3.14 if you have explicitly verified Preview support for your region and plan.

### Optional Workflow Flags

| Flag | Default | Purpose |
| :--- | :--- | :--- |
| `--github-actions` / `--no-github-actions` | `--no-github-actions` | Include a starter CI workflow under `.github/workflows/`. |
| `--git` / `--no-git` | `--no-git` | Run `git init` in the generated project. |
| `--azd` / `--no-azd` | `--no-azd` | Include Azure Developer CLI (`azd`) support files. |
| `--overwrite` | `False` | Replace an existing target directory. |

### Built-in Features

The following are included in every generated project regardless of flags.

| Feature | Dependency | Location |
| :--- | :--- | :--- |
| Structured logging | `azure-functions-logging` | `app/core/logging.py` |

Structured JSON logging is pre-configured via `configure_logging()` in `app/core/logging.py`
and called at startup in `function_app.py`. No additional flag is required.

```python
# app/core/logging.py (generated)
from azure_functions_logging import get_logger, setup_logging


def configure_logging() -> None:
    setup_logging(format="json")


logger = get_logger("my-api")
```

### Optional Feature Flags

| Flag | Default | Effect |
| :--- | :--- | :--- |
| `--with-openapi` / `--no-openapi` | `--no-openapi` | Adds OpenAPI routes (`/api/docs`, `/api/openapi.json`, `/api/openapi.yaml`) for HTTP projects. |
| `--with-validation` / `--no-validation` | `--no-validation` | Adds `azure-functions-validation` and Pydantic request/response model validation for HTTP projects. |
| `--with-doctor` / `--no-doctor` | `--no-doctor` | Adds `azure-functions-doctor` dependency and a `make doctor` target. |

!!! warning "HTTP-only behavior"
    `--with-openapi` and `--with-validation` are intended for the HTTP template.
    If you pass them to non-HTTP templates, there is no HTTP route to apply
    those integrations.

### Preview and Safety Flags

| Flag | Default | Purpose |
| :--- | :--- | :--- |
| `--dry-run` | `False` | Prints what would be generated without writing files. |
| `--yes`, `-y` | `False` | Skips confirmation prompts (required when `--overwrite` runs in a non-TTY session or against a directory containing `.git`). |

## Presets in Detail

Presets define quality tooling included in the generated project.

| Preset | Included tooling | Typical use |
| :--- | :--- | :--- |
| `minimal` | none | Quick experiments or ultra-light projects. |
| `standard` | `ruff`, `pytest` | Balanced default for most teams. |
| `strict` | `ruff`, `mypy`, `pytest` | Type-heavy projects and larger teams. |

### Examples

```bash
# Smallest possible scaffold
afs advanced new --preset minimal scratch-api

# Good default for API work
afs advanced new --preset standard customer-api

# Strict CI gate from day one
afs advanced new --preset strict payments-api
```

## Feature Combinations

Feature flags compose with templates and presets.

```bash
# HTTP API with docs and validation, strict checks
afs advanced new --preset strict --with-openapi --with-validation orders-api

# Timer job with lightweight tooling and doctor checks
afs advanced new --template timer --preset minimal --with-doctor nightly-cleanup

# Service Bus worker plus CI workflow bootstrap
afs worker servicebus bus-worker --github-actions
```

!!! tip "Recommended baseline"
    For production HTTP APIs, start with:

    - `--preset strict`
    - `--with-openapi`
    - `--with-validation`
    - `--with-doctor`

## Dry Run Workflows

Use dry runs in scripts and CI to verify intent before changing the filesystem.

```bash
afs advanced new --preset strict --with-openapi --dry-run my-api
```

For project expansion:

```bash
afs advanced add timer cleanup --project-root ./my-api --dry-run
```

Dry-run output includes:

- target location
- selected template/preset
- enabled features
- file list and planned updates

## `add` Command Configuration

```bash
afs api add <function-name> --project-root <path>
afs advanced add <trigger> <function-name> --project-root <path>
```

Supported triggers:

- `http`
- `timer`
- `queue`
- `blob`
- `servicebus`

Options:

| Flag | Default | Purpose |
| :--- | :--- | :--- |
| `--project-root` | `.` | Existing scaffolded project directory. |
| `--dry-run` | `False` | Preview files and updates without writing. |

When successful, these commands update `function_app.py` markers and may update
`host.json` or `local.settings.json.example` depending on trigger type.

## Naming and Validation Rules

Project names must:

- start with a letter or number
- contain only letters, numbers, hyphens, or underscores
- be non-empty after trimming

Examples:

- valid: `my-api`, `worker_v2`, `orders2026`
- invalid: `my api`, `-api`, `api!`

Function names added through `afs api add` or `afs advanced add` are normalized to Python module names.
For example, `Process Orders` becomes `process_orders`.

## Related Guides

- [Getting Started](getting-started.md)
- [Features and Presets](features.md)
- [Templates](templates.md)
- [Expanding Your Project](expanding.md)
- [Troubleshooting](troubleshooting.md)
