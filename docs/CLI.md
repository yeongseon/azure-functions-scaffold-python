# CLI Specification

## Command Surface

Current CLI surface:

```bash
azure-functions-scaffold new <project-name> [--destination <path>]
azure-functions-scaffold templates
azure-functions-scaffold --version
```

## `new`

Creates a new Azure Functions Python v2 project from the default HTTP template.

### Arguments

`project-name`

- required
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

### Behavior

Example:

```bash
azure-functions-scaffold new my-api
```

Result:

- creates `./my-api`
- renders all files from the embedded HTTP template
- prints `Created project at <path>`

### Failure Conditions

The command exits with status `1` when:

- `project-name` is empty after trimming
- `project-name` is `.` or `..`
- `--destination` exists and is not a directory
- target directory already exists

## `templates`

Lists the built-in scaffold templates.

Current output includes:

```text
http: HTTP-trigger Azure Functions Python v2 application.
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

- interactive prompts
- selecting multiple templates
- overwriting existing projects
- dry-run mode
- post-generation dependency installation

## Future CLI Surface

Likely future additions:

- `azure-functions-scaffold new <project-name> --template timer`
- `azure-functions-scaffold add trigger`
- `azure-functions-scaffold doctor`
- `azure-functions-scaffold new --interactive`
