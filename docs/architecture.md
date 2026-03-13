# Architecture
## Overview
azure-functions-scaffold is a Typer + Jinja2 CLI that generates Azure Functions Python v2 projects from embedded templates.
The architecture separates command handling, option validation, and template rendering to keep output deterministic and offline-capable.
It supports both full project creation (`new`) and incremental trigger generation (`add`).
## Runtime Flow
### new command
1. The user runs `azure-functions-scaffold new <project-name>` or starts interactive mode.
2. Typer routes the command to `cli.py` for argument and mode handling.
3. Interactive mode prompts for template, preset, Python version, tooling, and feature flags.
4. `_resolve_new_project_inputs()` collects validated inputs into `ProjectOptions`.
5. `build_project_options()` in `template_registry.py` validates preset and tooling compatibility.
6. `scaffold_project()` in `scaffolder.py` validates the project name and resolves destination paths.
7. The scaffolder builds `TemplateContext` values consumed by templates.
8. Jinja2 renders `.j2` files from the selected template root.
9. Rendered files are written to disk and git is initialized when requested.
### add command
1. The user runs `azure-functions-scaffold add <trigger> <function-name>` in an existing project.
2. `add_function()` in `generator.py` validates that the current directory is a scaffolded project.
3. The generator validates the trigger type against supported templates.
4. Function, service, and test modules are rendered from the trigger template.
5. The new Blueprint registration is appended to `function_app.py` without overwriting existing entries.
## Rendered Pipeline Examples
### Stage 1: Generated app entrypoint (`function_app.py`)
```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!", status_code=200)
```
### Stage 2: Generated trigger module (`app/functions/http.py`)
```python
import azure.functions as func

from app.services.hello_service import build_hello_message

bp = func.Blueprint()


@bp.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    message = build_hello_message(name)
    return func.HttpResponse(message, status_code=200)
```
### Stage 3: Generated test module (`tests/test_http.py`)
```python
from app.services.hello_service import build_hello_message


def test_build_hello_message_defaults_to_world() -> None:
    assert build_hello_message("World") == "Hello, World!"
```
## Module Boundaries
- **cli.py**: Defines commands, parses input, and maps expected errors to CLI output.
- **scaffolder.py**: Creates new projects by validating names, preparing context, and rendering files.
- **generator.py**: Adds trigger modules to existing projects and updates `function_app.py` registrations.
- **template_registry.py**: Defines available templates and presets and builds validated `ProjectOptions`.
- **models.py**: Defines frozen dataclasses (`TemplateContext`, `TemplateSpec`, `PresetSpec`, `ProjectOptions`).
- **errors.py**: Defines `ScaffoldError` for expected operational failures.
- **templates/**: Stores embedded Jinja2 templates grouped by trigger type.
## Data Model
- **TemplateContext**: Render-time values passed into Jinja2 templates.
- **ProjectOptions**: Validated user selections from CLI flags or interactive prompts.
- **TemplateSpec**: Template metadata (name, description, package path).
- **PresetSpec**: Preset metadata and tooling tuple (for example Ruff, mypy, pytest).
- **ScaffoldError**: Shared exception type for recoverable validation and filesystem errors.
## Template System
- Templates are bundled with the package, so rendering works offline.
- Each trigger has a dedicated template directory under `templates/`.
- Jinja2 conditionals adapt output to presets, Python version, and enabled features.
- Rendering is deterministic for a given input set.
## Design Constraints
- Keep runtime dependencies minimal (`typer`, `jinja2`, stdlib).
- Do not require network access during `new` or `add` operations.
- Keep generated output deterministic and editable by hand.
- Package templates in the distribution artifact, not remote storage.
- Keep generated projects aligned with selected quality tooling.
- Ensure each interactive choice has a non-interactive CLI flag.
## Dependency Graph
- `cli.py` depends on `scaffolder.py`, `generator.py`, `template_registry.py`, and `models.py`.
- `scaffolder.py` and `generator.py` depend on `template_registry.py` and `models.py`.
- `template_registry.py` depends on `models.py`.
- Modules use `errors.py` for consistent error signaling.
