# Template Specification

Standard for developing and maintaining templates for `azure-functions-scaffold`.

## Template Locations

All templates are stored within the source package at:
`src/azure_functions_scaffold/templates/<template-name>/`

## Rendering Rules

1. **File Discovery**: The generator recursively discovers all files in the template directory.
2. **Jinja2 Suffix**: Files ending in `.j2` are processed with Jinja2. The `.j2` suffix is removed after rendering.
3. **Placeholder Expansion**: Double underscores denote dynamic path components (e.g., `__project_slug__/function_app.py.j2`).
4. **Binary Files**: Any file without a `.j2` suffix is copied directly without processing.

## Template Context Variables

These variables are available within all Jinja2 templates.

| Variable | Type | Description |
| :--- | :--- | :--- |
| `project_name` | String | User-provided name of the project. |
| `project_slug` | String | URL-friendly, sanitized version of the project name. |
| `python_version` | String | Specified version (e.g., `3.12`). |
| `python_upper_bound` | String | Upper boundary for dependency resolution. |
| `preset_name` | String | Selected preset (`minimal`, `standard`, `strict`). |
| `include_github_actions` | Boolean | Whether to include workflow YAMLs. |
| `initialize_git` | Boolean | Whether to initialize a git repository. |
| `include_ruff` | Boolean | True if preset includes Ruff. |
| `include_mypy` | Boolean | True if preset includes Mypy. |
| `include_pytest` | Boolean | True if preset includes Pytest. |
| `include_openapi` | Boolean | Whether to include Swagger/OpenAPI support. |
| `include_validation` | Boolean | Whether to include Pydantic-based validation. |
| `include_doctor` | Boolean | Whether to include `doctor.py` script. |

## Required Output Files

### Global (All Templates)
- `function_app.py`: The entry point for the Azure Function.
- `requirements.txt` or `pyproject.toml`: Dependency management.
- `.gitignore`: Standard Python and VS Code exclusions.
- `local.settings.json`: Configuration for local runtime.

### HTTP Template Specifics
- Must include a `Blueprint` if following the split-file pattern.
- Must handle route parameters and request body extraction if `include_validation` is true.

### Non-HTTP Template Specifics
- **Queue/Blob/ServiceBus**: Must specify `extensionBundle` version in `host.json`.
- **Timer**: Must include a valid Cron schedule (defaulting to every 5 minutes).
- **Local Dev**: Requires Azurite or a valid Azure storage connection string in `local.settings.json`.

## Quality Contract

All generated projects must pass the following commands immediately after generation:
```bash
make install
make check-all
```

!!! note "Preset Enforcement"
    Templates must conditionally render blocks based on `include_ruff` and `include_mypy` variables to ensure the generated code is compliant with the selected preset's rules.

## Template Authoring Rules

1. Use 4 spaces for indentation in both `.py` and `.py.j2` files.
2. Ensure `function_app.py` uses the `azure.functions.FunctionApp` class.
3. Use docstrings for all functions and classes.
4. Path placeholders must use double underscores: `__variable_name__`.

## Extension Guidelines

To add a new template:
1. Create a directory in `src/azure_functions_scaffold/templates/`.
2. Register the template in `src/azure_functions_scaffold/template_registry.py`.
3. Add a corresponding `TemplateSpec` entry in `models.py`.
4. Update the CLI tests to verify the new template's output.
