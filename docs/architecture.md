# Architecture

`azure-functions-scaffold` has three main concerns:

- command parsing
- template rendering
- embedded project templates

## Runtime Flow

1. The user runs `azure-functions-scaffold new <project-name>`.
2. Typer dispatches the command in `src/azure_functions_scaffold/cli.py`.
3. `scaffold_project()` validates inputs and resolves the destination.
4. The renderer loads the selected embedded template.
5. Jinja2 renders each template file into the target directory.
6. The CLI prints the created project path.

## Module Boundaries

### `cli.py`

- defines the CLI app
- exposes user-facing commands
- translates `ScaffoldError` into user-facing command failures

### `scaffolder.py`

- validates project name and destination
- selects the template root
- iterates through template files
- renders file contents and output paths

### `templates/`

- defines generated Azure Functions projects
- keeps scaffold files as `.j2` templates
- provides the baseline app, tests, and project tooling defaults

## Design Constraints

- keep the runtime small and dependency-light
- keep the scaffold deterministic
- avoid hidden network calls or external template downloads
- package templates inside the distribution artifacts
