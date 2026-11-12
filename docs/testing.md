# Testing

This guide describes the test suite for `azure-functions-scaffold`, including how to run tests, the structure of the test suite, and guidelines for contributing new tests.

## Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make cov
```

## Test Structure

Tests live in `tests/`. This map lists the test *levels*, the representative files for each level,
the command that runs it, and what it does **not** prove. Every path below is checked against the
working tree by `tests/test_docs_test_paths.py`, so a renamed or deleted file cannot stay in this guide.

| Level | Representative files | Run with | Proves | Does not prove |
| :--- | :--- | :--- | :--- | :--- |
| CLI behavior | `tests/test_cli.py`, `tests/test_cli_intents.py`, `tests/test_docs_cli_examples.py` | `make test` | Command routing, options, exit codes, error messages, and that documented CLI examples match the current command surface. | Anything about the files a command writes beyond the checked output. |
| Scaffolding and template rendering | `tests/test_scaffolder.py`, `tests/test_generator.py`, `tests/test_rendered_security.py` | `make test` | Project and function generation, `afs ... add` expansion, rollback and containment, and that rendered Jinja templates contain the expected content. Runs in-process with temporary directories, offline. | That the generated project installs or runs. |
| Generated-project contract | `tests/test_generated_projects.py`, `tests/test_template_smoke.py`, `tests/test_generated_http_indexing.py`, `tests/test_generated_http_option_matrix.py`, `tests/test_generated_security_defaults.py` | `make test`; one template: `pytest --no-cov "tests/test_generated_projects.py::test_generated_project_passes_in_isolated_venv[http]"` | A generated project installs into its own virtual environment and passes its own `make check-all` (Ruff, mypy, pytest), plus its documented option and security defaults. | Behavior on a running Functions host. |
| Local Functions host | `tests/test_generated_langgraph_host_security.py` (opt-in) and the `generated-host-smoke` job in `.github/workflows/ci-test.yml` | `make security-host` (sets `RUN_LOCAL_HOST_SECURITY=true`); the CI job starts `func start` against Azurite | A generated project starts on a real local Functions host and answers its health route. | Azure hosting, platform authentication or networking. |
| Real Azure E2E | `tests/e2e/test_scaffold_e2e.py` | `make e2e-azure` (needs `E2E_BASE_URL` and `E2E_SCAFFOLDED_DIR`) | A generated project deployed to a real Function App responds over HTTP. | Anything when the inputs are missing: the run fails instead of skipping. |

Offline generator checks (the first three rows) never start a Functions host or touch Azure. A local
host run is not Azure evidence, and a passing unit or template test is not evidence that the
generated project runs. Treat each level as a separate claim.

The generated-project tests are marked `slow` (they spawn subprocesses and create virtual
environments); the default `pytest` configuration deselects only `e2e`.

## CI Test Matrix

Tests run automatically on every pull request and push to `main`. The CI matrix covers:

| Python Version | Status |
| -------------- | ------ |
| 3.11 | Tested |
| 3.12 | Tested |
| 3.13 | Tested |
| 3.14 | Tested |

All tests must pass across the entire matrix before a pull request can be merged.

## Real Azure E2E Tests

The project includes a real Azure end-to-end test workflow that deploys an actual Function App to Azure and validates HTTP endpoints.

### Workflow

- **File**: `.github/workflows/e2e-azure.yml`
- **Trigger**: Manual (`workflow_dispatch`) or weekly schedule (Mondays 02:00 UTC)
- **Infrastructure**: Azure Consumption plan, `koreacentral` region
- **Cleanup**: Resource group deleted immediately after tests (`if: always()`)

### Running E2E Tests

```bash
gh workflow run e2e-azure.yml --ref main
```

### Required Secrets & Variables

| Name | Type | Description |
| --- | --- | --- |
| `AZURE_CLIENT_ID` | Secret | App Registration Client ID (OIDC) |
| `AZURE_TENANT_ID` | Secret | Azure Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Secret | Azure Subscription ID |
| `AZURE_LOCATION` | Variable | Azure region (default: `koreacentral`) |

### Test Report

HTML test report is uploaded as a GitHub Actions artifact (retained 30 days).
