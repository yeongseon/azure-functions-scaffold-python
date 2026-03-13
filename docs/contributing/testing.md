# Testing Guide

All changes to azure-functions-scaffold must include tests. We aim for high reliability and 90% or greater test coverage.

## Running Tests

To execute the full test suite:
```bash
make test
```

To run tests with a detailed coverage report:
```bash
make cov
```

To run a specific test file or function:
```bash
hatch run pytest tests/test_cli.py
hatch run pytest tests/test_cli.py::test_init_success
```

## Test Structure

| File | Lines | Description |
| :--- | :--- | :--- |
| `test_cli.py` | ~558 | CLI command tests using Typer `CliRunner` |
| `test_scaffolder.py` | ~437 | Project generation logic with the `tmp_path` fixture |
| `test_generator.py` | ~171 | Logic for adding new functions to existing projects |

## Test Patterns

### CLI Tests

We use `typer.testing.CliRunner` to test the command-line interface.

- **Success paths:** Verify the command exits with code 0 and provides the expected output message.
- **Error paths:** Verify the command exits with code 1 or 2 for invalid arguments or execution errors.
- **Interactive mode:** Use the `input` parameter in `runner.invoke` to simulate user responses for CLI prompts.

```python
from typer.testing import CliRunner
from azure_functions_scaffold.cli import app

runner = CliRunner()

    def test_new_command_creates_project(tmp_path):
    result = runner.invoke(app, ["new", "my-api", "--destination", str(tmp_path)])
    assert result.exit_code == 0
```

### Scaffolder Tests

These tests focus on the core project creation logic. Use the `tmp_path` fixture to create a temporary directory for each test run.

- **Trigger types:** Verify that all supported triggers (HTTP, Timer, Queue, etc.) generate correct file structures.
- **Naming validation:** Ensure the scaffolder rejects invalid project names or function names.
- **Presets:** Test the resolution of project presets to ensure they include the correct dependencies.

### Generator Tests

These tests ensure new functions can be added to existing projects without breaking them.

- **Function addition:** Verify that adding a second or third function correctly updates the project's file structure.
- **Validation:** Test that adding a duplicate function name fails gracefully.
- **Error handling:** Test the behavior when the target project directory is missing or invalid.

## Coverage Configuration

The project is configured to track:
- All source files in `src/azure_functions_scaffold/`.
- Branch coverage for conditional logic.
- Exclusions for boilerplate code that does not require testing.

A minimum coverage of **90%** is required. PRs that drop the coverage below this threshold will fail CI checks.

## Writing New Tests

- Place tests in the `tests/` directory.
- Follow the `test_<module>.py` naming convention.
- Include both success and error paths (edge cases).
- Use descriptive function names like `test_scaffolder_fails_on_duplicate_name`.

## CI Matrix

Each pull request is tested against a matrix of environments to ensure broad compatibility:

- **OS:** `ubuntu-latest`
- **Python versions:** 3.10, 3.11, 3.12, 3.13, 3.14

## Troubleshooting

- **Temporary files:** If a test fails, `tmp_path` is automatically cleaned up. To inspect generated files, you can print the path during a local run.
- **Template rendering:** Use `pytest -s` to see output if you suspect a Jinja2 rendering error.
- **Imports:** Ensure you are running tests via `make test` or `hatch run pytest` to correctly set the Python path for the `src` directory.
