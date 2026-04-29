# API Reference

This page documents the Python API surface for `azure-functions-scaffold`.
Use it when embedding scaffold behavior in tests, custom automation, or other
developer tooling.

!!! note "CLI-first project"
    The primary public interface is the command line (`afs` /
    `azure-functions-scaffold`). Python imports are useful for advanced flows,
    but CLI compatibility is the main stability target.

## Module Overview

Core modules in the package:

- `azure_functions_scaffold.cli`: Typer application and command handlers.
- `azure_functions_scaffold.scaffolder`: project scaffolding orchestration.
- `azure_functions_scaffold.models`: shared dataclasses for options and context.
- `azure_functions_scaffold.generator`: add-function workflow and code updates.
- `azure_functions_scaffold.template_registry`: template and preset discovery.
- `azure_functions_scaffold.errors`: domain-specific exception types.

## Import Patterns

```python
from pathlib import Path

from azure_functions_scaffold.models import ProjectOptions
from azure_functions_scaffold.scaffolder import (
    describe_scaffold_project,
    scaffold_project,
)
from azure_functions_scaffold.template_registry import build_project_options

options = build_project_options(
    preset_name="strict",
    python_version="3.12",
    include_github_actions=True,
    initialize_git=False,
    include_openapi=True,
    include_validation=True,
    include_doctor=True,
)

preview = describe_scaffold_project(
    project_name="my-api",
    destination=Path("."),
    template_name="http",
    options=options,
)

for line in preview:
    print(line)

project_path = scaffold_project(
    project_name="my-api",
    destination=Path("."),
    template_name="http",
    options=options,
)
print(project_path)
```

## Error Handling

Most failures raise `ScaffoldError` with actionable messages.

```python
from pathlib import Path

from azure_functions_scaffold.errors import ScaffoldError
from azure_functions_scaffold.scaffolder import scaffold_project

try:
    scaffold_project(project_name="bad name", destination=Path("."))
except ScaffoldError as exc:
    print(f"Scaffold failed: {exc}")
```

Common failure classes include:

- invalid project names
- unknown templates or presets
- unsupported Python versions
- target directory collisions without overwrite
- invalid `add` project roots

## Stability Notes

Treat the following as stable integration points:

- CLI commands and flags in [CLI Reference](cli.md)
- dataclasses in `azure_functions_scaffold.models`
- high-level orchestration functions in `azure_functions_scaffold.scaffolder`

Treat internals as implementation details:

- private helpers prefixed with `_`
- direct template file internals under `templates/`
- insertion-marker implementation details in generator internals

!!! tip "Programmatic dry-run"
    Use `describe_scaffold_project` and `describe_add_function` to integrate
    preview behavior in automation without touching the filesystem.

## mkdocstrings Reference

The sections below are rendered directly from source using mkdocstrings.

### CLI Module

::: azure_functions_scaffold.cli

### Scaffolder Module

::: azure_functions_scaffold.scaffolder

### Models Module

::: azure_functions_scaffold.models

## Additional Useful Modules

These modules are often imported by advanced users even though they are not the
primary API entry points.

### `azure_functions_scaffold.generator`

Use for adding triggers to existing projects:

- `add_function(...)`
- `describe_add_function(...)`
- `SUPPORTED_TRIGGERS`

### `azure_functions_scaffold.template_registry`

Use for template/preset discovery and input validation:

- `list_templates()`
- `list_presets()`
- `build_project_options(...)`
- `validate_python_version(...)`

### `azure_functions_scaffold.errors`

Domain exception:

- `ScaffoldError`

## Related Pages

- [CLI Reference](cli.md)
- [Template Specification](template-spec.md)
- [Architecture](architecture.md)
- [Configuration Guide](../guide/configuration.md)
