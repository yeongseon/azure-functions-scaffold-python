# Troubleshooting

Common issues and solutions for the Azure Functions Scaffold CLI and its generated projects.

### Installation

**Problem**: `afs` command not found.
*   **Cause**: The installation directory is not in your system's `PATH`.
*   **Solution**: Run `pip show azure-functions-scaffold` to find the installation path and add the `bin` directory to your `PATH`. Alternatively, use `pipx install azure-functions-scaffold`.

### Project Creation

**Problem**: "Directory not empty" error when creating a project.
*   **Cause**: The CLI prevents overwriting existing files by default.
*   **Solution**: Use the `--overwrite` flag if you want to force project creation in an existing directory.

### Feature Flags

**Problem**: OpenAPI documentation is not showing up.
*   **Cause**: Missing `--with-openapi` flag during project generation.
*   **Solution**: Re-generate the project with the flag or manually install `azure-functions-openapi` and add the required decorators to your trigger.

### Function Addition

**Problem**: `add` command fails to find `function_app.py`.
*   **Cause**: The command is not being run from the project root.
*   **Solution**: Run the command from the root directory of your generated project or provide the `--project-root` flag pointing to it.

### Generated Project

**Problem**: "No job functions found" when running `func start`.
*   **Cause**: Blueprints are not correctly registered in `function_app.py`.
*   **Solution**: Open `function_app.py` and verify that `app.register_functions(blueprint)` is called for each function module.

**Problem**: `ImportError` when importing services.
*   **Cause**: The project root is not in the Python path or dependencies aren't installed.
*   **Solution**: Ensure you are in a virtual environment, run `pip install -e .`, and make sure you're importing from `app.services.your_service`.

### Interactive Mode

**Problem**: CLI gets stuck or behaves unexpectedly in a shell.
*   **Cause**: Some shells (like Git Bash on Windows) handle interactive TTYs poorly.
*   **Solution**: Prefix the command with `winpty` (e.g., `winpty afs new my-api --interactive`) or use a standard terminal like PowerShell or CMD.

### Development

**Problem**: Linting errors with Ruff after project generation.
*   **Cause**: Your editor may be using a different version of Ruff than the one in your environment.
*   **Solution**: Run `ruff check .` from the command line to verify the project's actual status.
