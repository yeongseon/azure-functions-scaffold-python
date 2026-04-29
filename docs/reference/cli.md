# CLI Reference

Technical specification for the `azure-functions-scaffold-python` (alias: `afs`) command-line interface.

## Commands

### `new`

Generates a new Azure Functions Python v2 project from scratch.

- **Synopsis**: `azure-functions-scaffold-python new [PROJECT_NAME] [OPTIONS]`

#### Arguments

| Argument | Required | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | No | Name of the project directory. If omitted, the tool enters interactive mode. |

#### Options

| Flag | Default | Values | Description |
| :--- | :--- | :--- | :--- |
| `--destination`, `-d` | `.` | Path | Target parent directory for the project. |
| `--template`, `-t` | `http` | `http`, `timer`, `queue`, `blob`, `servicebus` | Initial trigger template to include. |
| `--preset` | `standard` | `minimal`, `standard`, `strict` | Tooling configuration (linting, types, tests). |
| `--python-version` | `3.10` | `3.10`, `3.11`, `3.12`, `3.13`, `3.14` | Target Python version for the project. |
| `--github-actions` / `--no-github-actions` | `--no-github-actions` | Boolean | Include GitHub Actions CI/CD workflows. |
| `--git` / `--no-git` | `--no-git` | Boolean | Initialize a git repository. |
| `--with-openapi` / `--no-openapi` | `--no-openapi` | Boolean | Include OpenAPI/Swagger documentation support. |
| `--with-validation` / `--no-validation` | `--no-validation` | Boolean | Include Pydantic-based request validation. |
| `--with-doctor` / `--no-doctor` | `--no-doctor` | Boolean | Include a `doctor.py` script for environment checks. |
| `--interactive`, `-i` | False | Boolean | Force interactive wizard. |
| `--dry-run` | False | Boolean | Show planned files without writing to disk. |
| `--overwrite` | False | Boolean | Overwrite files if the destination directory exists. |
| `--yes`, `-y` | False | Boolean | Skip overwrite confirmation prompts when deletion is intentional. |

When `--overwrite` is used in an interactive TTY, the CLI prompts before deleting the target directory and defaults to No. In non-interactive sessions, `--overwrite` is refused unless `--yes` is also passed. As an extra safety guard, any target directory containing `.git/` also requires `--yes` before it can be deleted.

### `add`

Adds a new function to an existing project.

- **Synopsis**: `azure-functions-scaffold-python add TRIGGER FUNCTION_NAME [OPTIONS]`

#### Arguments

| Argument | Required | Description |
| :--- | :--- | :--- |
| `TRIGGER` | Yes | Trigger type (e.g., `http`, `timer`, `queue`). |
| `FUNCTION_NAME` | Yes | Name of the new function. |

#### Options

| Flag | Default | Values | Description |
| :--- | :--- | :--- | :--- |
| `--project-root` | `.` | Path | Path to the root of the existing project. |
| `--dry-run` | False | Boolean | Show planned changes without writing to disk. |

### `templates`

Lists all available function templates.

- **Synopsis**: `azure-functions-scaffold-python templates`

### `presets`

Lists all available project presets and their included tools.

- **Synopsis**: `azure-functions-scaffold-python presets`

### `--version`

Shows the current version of the CLI tool.

- **Synopsis**: `azure-functions-scaffold-python --version`

## Exit Codes

| Code | Meaning |
| :--- | :--- |
| `0` | Success |
| `1` | Validation error or runtime failure |

## Error Conditions

The CLI returns exit code `1` under the following conditions:

- **Directory Conflict**: Destination directory is not empty and `--overwrite` is not set.
- **Invalid Template**: Specified trigger template does not exist in the registry.
- **Invalid Preset**: Specified preset name is not recognized.
- **Python Version Mismatch**: Host Python version is lower than required by the tool.
- **Missing Project Root**: `add` command executed outside a valid scaffolded project.
- **Validation Failure**: Project name contains illegal characters for Azure resources.
