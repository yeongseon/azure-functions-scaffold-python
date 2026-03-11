# CLI Specification

## Command Surface

Current CLI surface:

```bash
azure-functions-scaffold new [<project-name>] [--destination <path>]
azure-functions-scaffold add <trigger> <function-name> [--project-root <path>]
azure-functions-scaffold presets
azure-functions-scaffold templates
azure-functions-scaffold --version
```

## `new`

Creates a new Azure Functions Python v2 project from one of the built-in simple templates.

### Arguments

`project-name`

- optional when `--interactive` is used
- used as the output directory name
- also injected into template rendering context as `project_name`

### Options

`--destination`, `-d`

- optional
- default: current directory
- interpreted as the parent directory where the project folder will be created

`--template`, `-t`

- optional
- default: `http`
- supported values: `http`, `timer`, `queue`, `blob`, `servicebus`
- selects the scaffold template to render

`--preset`

- optional
- default: `standard`
- supported values: `minimal`, `standard`, `strict`
- controls generated quality tooling defaults

`--python-version`

- optional
- default: `3.10`
- supported values: `3.10`, `3.11`, `3.12`, `3.13`, `3.14`
- controls the generated `requires-python` range and tool target version

`--github-actions`, `--no-github-actions`

- optional
- default: `--no-github-actions`
- controls whether `.github/workflows/ci.yml` is generated

`--git`, `--no-git`

- optional
- default: `--no-git`
- controls whether the generated project runs `git init`

`--interactive`, `-i`

- optional
- when enabled, prompts for project name, template, preset, Python version, GitHub Actions, git initialization, and individual tooling selection

`--dry-run`

- optional
- previews the generated project without writing files

### Behavior

Example:

```bash
azure-functions-scaffold new my-api
```

Interactive example:

```bash
azure-functions-scaffold new --interactive
```

Preset example:

```bash
azure-functions-scaffold new my-api --preset strict --python-version 3.12 --github-actions
```

Timer template example:

```bash
azure-functions-scaffold new my-job --template timer
```

Queue template example:

```bash
azure-functions-scaffold new my-worker --template queue
```

Blob template example:

```bash
azure-functions-scaffold new my-blob-worker --template blob
```

Service Bus template example:

```bash
azure-functions-scaffold new my-bus-worker --template servicebus
```

Dry-run example:

```bash
azure-functions-scaffold new my-api --template queue --preset strict --dry-run
```

Result:

- creates `./my-api`
- renders all files from the embedded HTTP template
- uses the chosen preset as a starting point, then applies interactive tooling overrides
- optionally omits tests for the `minimal` preset
- optionally includes `.github/workflows/ci.yml`
- optionally initializes a git repository
- supports dry-run previews of the target directory and rendered file set
- prints `Created project at <path>`

## `add`

Adds a new function module to an existing scaffolded project.

### Arguments

`trigger`

- required
- supported values: `http`, `timer`, `queue`, `blob`, `servicebus`

`function-name`

- required
- normalized into a Python module name

### Options

`--project-root`

- optional
- default: current directory
- points to an existing scaffolded Azure Functions project

`--dry-run`

- optional
- previews the files and project updates without modifying the project

### Behavior

HTTP example:

```bash
azure-functions-scaffold add http get-user --project-root ./my-api
```

Timer example:

```bash
azure-functions-scaffold add timer cleanup --project-root ./my-api
```

Queue example:

```bash
azure-functions-scaffold add queue sync-jobs --project-root ./my-api
```

Blob example:

```bash
azure-functions-scaffold add blob ingest-reports --project-root ./my-api
```

Service Bus example:

```bash
azure-functions-scaffold add servicebus process-events --project-root ./my-api
```

Dry-run example:

```bash
azure-functions-scaffold add servicebus process-events --project-root ./my-api --dry-run
```

Result:

- creates `app/functions/<name>.py`
- updates `function_app.py` to import and register the new Blueprint
- creates `tests/test_<name>.py` when the project includes a `tests/` directory
- updates `host.json` for binding-based triggers
- updates `local.settings.json.example` for Service Bus additions when needed

### Failure Conditions

The command exits with status `1` when:

- `project-name` is missing outside interactive mode
- `project-name` is empty after trimming
- `project-name` is `.` or `..`
- `--destination` exists and is not a directory
- unsupported preset or Python version is requested
- target directory already exists
- git initialization is requested but `git` is unavailable

For `add`, the command exits with status `1` when:

- the trigger is unsupported
- the project root does not look like a scaffolded project
- the generated function module already exists
- the function name is invalid
- `function_app.py` cannot be updated safely

## `templates`

Lists the built-in scaffold templates.

Current output includes:

```text
http: HTTP-trigger Azure Functions Python v2 application.
timer: Timer-trigger Azure Functions Python v2 application.
queue: Queue-trigger Azure Functions Python v2 application.
blob: Blob-trigger Azure Functions Python v2 application.
servicebus: Service Bus-trigger Azure Functions Python v2 application.
```

## `presets`

Lists the built-in project presets.

Current output includes:

```text
minimal: Minimal HTTP function with no additional quality tooling. [tooling: none]
standard: HTTP function with Ruff and pytest defaults. [tooling: ruff, pytest]
strict: HTTP function with Ruff, mypy, and pytest defaults. [tooling: ruff, mypy, pytest]
```

## `--version`

Prints the installed package version and exits.

## Output Contract

On success:

- exit code `0`
- created directory is ready for dependency installation and local checks

On failure:

- exit code `1` for scaffold validation errors
- human-readable error message is printed to stdout

## Non-Goals for Current CLI

Not currently supported:

- selecting multiple templates in one command
- overwriting existing projects
- post-generation dependency installation
- durable orchestrations and activities

## Future CLI Surface

Likely future additions:

- richer interactive tooling selection beyond preset choice
- additional deployment-oriented templates
