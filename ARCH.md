# Architecture

## Overview

`azure-functions-scaffold` is a small CLI package with three main concerns:

- command parsing
- template rendering
- embedded project templates

## Current Runtime Flow

1. The user runs `azure-functions-scaffold new <project-name>`.
2. Typer dispatches the `new` command in `src/azure_functions_scaffold/cli.py`.
3. `scaffold_project()` in `src/azure_functions_scaffold/scaffolder.py` validates inputs.
4. The renderer loads the `http` template directory.
5. Jinja2 renders each template file into the target project directory.
6. The CLI prints the created project path.

## Module Structure

### `cli.py`

Responsibilities:

- define the CLI app
- expose the `new` command
- translate `ScaffoldError` into user-facing command failures

### `scaffolder.py`

Responsibilities:

- validate project name and destination
- select the template root
- iterate files inside the template tree
- render file contents and output paths

### `templates/http/`

Responsibilities:

- define the generated Azure Functions HTTP project
- hold all scaffolded files as `.j2` templates
- provide the baseline app, tests, and tool configuration

## Rendering Model

The current renderer is file-based:

- every file under `templates/http/` is considered part of the output
- `.j2` suffixes are removed from generated file names
- template contents are rendered through Jinja2
- path placeholders are reserved for future expansion through `__project_name__`

Current template context:

- `project_name`

## Design Constraints

- keep the runtime small and dependency-light
- keep the scaffold deterministic
- avoid hidden network calls or external template downloads
- package templates inside the wheel/sdist

## Error Handling

The scaffolder raises `ScaffoldError` for invalid user input, including:

- empty project name
- invalid path-like project names such as `.` and `..`
- non-directory destinations
- pre-existing target directories

The CLI catches these and exits with code `1`.

## Testing Strategy

The repository tests focus on:

- CLI success path
- collision handling when the target already exists

The generated project should also be verified separately for:

- `pytest`
- `ruff check .`
- `ruff format --check .`

## Future Architectural Extensions

Likely next additions:

- template registry instead of hard-coded `http`
- richer context model
- template variants by trigger type
- optional interactive prompting layer
- post-generation hooks for optional setup tasks

