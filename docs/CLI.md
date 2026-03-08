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

Creates a new Azure Functions Python v2 project from the default HTTP template.

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
- when enabled, prompts for project name, template, preset, Python version, GitHub Actions, and git initialization

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

Result:

- creates `./my-api`
- renders all files from the embedded HTTP template
- optionally omits tests for the `minimal` preset
- optionally includes `.github/workflows/ci.yml`
- optionally initializes a git repository
- prints `Created project at <path>`

## `add`

Adds a new function module to an existing scaffolded project.

### Arguments

`trigger`

- required
- supported values: `http`, `timer`

`function-name`

- required
- normalized into a Python module name

### Options

`--project-root`

- optional
- default: current directory
- points to an existing scaffolded Azure Functions project

### Behavior

HTTP example:

```bash
azure-functions-scaffold add http get-user --project-root ./my-api
```

Timer example:

```bash
azure-functions-scaffold add timer cleanup --project-root ./my-api
```

Result:

- creates `app/functions/<name>.py`
- updates `function_app.py` to import and register the new Blueprint
- creates `tests/test_<name>.py` when the project includes a `tests/` directory

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
- dry-run mode
- post-generation dependency installation
- queue, Service Bus, or blob function generation

## Future CLI Surface

Likely future additions:

- `azure-functions-scaffold new <project-name> --template timer`
- `azure-functions-scaffold add queue <function-name>`
- richer interactive tooling selection beyond preset choice
- additional deployment-oriented templates
