# Troubleshooting

Use this page to diagnose common CLI and runtime issues for
`azure-functions-scaffold` projects.

## CLI Installation and Execution

### `afs` command not found

**Symptoms**

- `afs: command not found`
- command works in one shell but not another

**Likely causes**

- package install location is not on `PATH`
- virtual environment is not activated

**Fix**

```bash
pipx install azure-functions-scaffold
afs --version
```

If using `pip`, verify installation path and environment activation.

### Wrong Python interpreter

**Symptoms**

- unexpected dependency errors
- `afs --version` differs between terminals

**Fix**

- run with explicit interpreter: `python -m azure_functions_scaffold.cli`
- standardize on `pipx` or one active venv workflow per project

## Project Generation Failures

### Unknown template or preset

**Symptoms**

- `Unknown template ...`
- `Unknown preset ...`

**Fix**

List valid options first:

```bash
afs templates
afs presets
```

Supported templates are `http`, `timer`, `queue`, `blob`, `servicebus`.
Supported presets are `minimal`, `standard`, `strict`.

### Target directory already exists

**Symptoms**

- generation fails with target directory exists message

**Fix**

- choose a different name, or
- pass `--overwrite` when replacing that directory is intentional

!!! warning "Overwrite behavior"
    `--overwrite` removes the existing target directory before generation.

### Permission denied while writing files

**Symptoms**

- `PermissionError`
- project directory partially created

**Likely causes**

- writing into protected paths
- files owned by another user

**Fix**

- generate under a user-writable path (for example your home/workspace)
- check ownership/permissions on destination parent directory
- rerun generation after fixing ownership

## Feature Flag Surprises

### OpenAPI routes not present

**Symptoms**

- `/api/docs` returns 404
- no `openapi.json` route

**Fix**

- generate HTTP project with `--with-openapi`
- verify `function_app.py` includes openapi route handlers

### Validation behavior differs from expectation

**Symptoms**

- `GET /api/hello` no longer works
- body validation errors on hello route

**Explanation**

With `--with-validation`, generated hello endpoint uses POST body validation.

**Fix**

- send JSON body matching request model, or
- adjust generated endpoint method/signature to fit your API contract

### Doctor command unavailable

**Symptoms**

- `make doctor` fails or target missing

**Fix**

- ensure project was generated with `--with-doctor`
- reinstall dependencies in active environment

## `afs add` Problems

### `add` cannot find scaffold project root

**Symptoms**

- error says project root does not look scaffolded

**Likely causes**

- running command outside project root
- missing required files like `function_app.py` or `app/functions/`

**Fix**

```bash
afs add http users --project-root ./my-api
```

Use `--project-root` explicitly in scripts and CI.

### Function already exists

**Symptoms**

- add command fails due to existing module

**Fix**

- choose a different function name, or
- remove/rename the existing module before running `afs add` again

## Core Tools Runtime Issues

### `func` command not found

Install Azure Functions Core Tools v4 and verify:

```bash
func --version
```

### "No job functions found" during `func start`

**Likely causes**

- blueprint not registered in `function_app.py`
- broken import in function modules

**Fix checklist**

1. Confirm each module import exists in `function_app.py`.
2. Confirm each module has `app.register_functions(<blueprint>)`.
3. Run `pip install -e .` from project root.

### Local storage errors (`UseDevelopmentStorage=true`)

For timer/queue/blob/servicebus local workflows, ensure Azurite is running and
`local.settings.json` exists (copied from the example file).

## Project Structure and Imports

### Import errors for `app.services` modules

**Fix**

- run from project root
- install package editable: `pip install -e .`
- keep imports absolute (`from app.services...`) per generated layout

### Missing tests after adding a function

`afs add` creates test files only when `tests/` directory exists. If your
project removed tests, recreate the folder or add tests manually.

## Diagnostic Workflow

When in doubt, run this order:

```bash
afs --version
python --version
afs templates
afs presets
afs new scratch --dry-run
```

Then inside a project:

```bash
pip install -e .[dev]
make check-all
func start
```

## Still Stuck?

- Check [FAQ](../faq.md)
- Revisit [Configuration](configuration.md)
- Compare with [HTTP API Example](../examples/http_api.md)
