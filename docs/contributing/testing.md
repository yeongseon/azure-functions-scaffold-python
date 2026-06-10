# Testing Guide

All changes to azure-functions-scaffold-python must include tests. We aim for high reliability and 90% or greater test coverage.

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
- **Python versions:** 3.10, 3.11, 3.12, 3.13, 3.14 (Preview - allowed to fail)

## Generated-project smoke tests

The `templates-smoke.yml` workflow scaffolds every template on every push that touches `src/azure_functions_scaffold/templates/**` or related code, then runs `compileall`, `ruff`, `mypy`, and `pytest` against each generated project. This catches template-level breakage that unit tests cannot - for example, a marker-string drift between `generator.py` constants and template comments.

Local equivalent:

```bash
tmpdir=$(mktemp -d)
cd "$tmpdir"
afs new smoke --python-version 3.12
cd smoke
python -m compileall -q .
ruff check . && mypy . && pytest -q
```

## Azure End-to-End Tests

The `.github/workflows/e2e-azure.yml` workflow generates a scaffolded project, deploys it to Azure, and validates HTTP endpoints against a real Function App.

### Workflow

- **File**: `.github/workflows/e2e-azure.yml`
- **Trigger**: Tag push (`v*`) or manual (`workflow_dispatch`)
- **Infrastructure**: Azure Consumption plan, `koreacentral` region (`AZURE_LOCATION` variable)
- **Cleanup**: Resource group deleted immediately after tests (`if: always()`)

### Required Secrets & Variables

Both `deploy_and_test` and `cleanup` jobs declare `environment: azure-e2e`. The Azure OIDC secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`) may be provided either as environment secrets on `azure-e2e` or as repository-level secrets with the same names. `AZURE_LOCATION` is read from the `vars` context with a fallback to `koreacentral`.

If `azure-e2e` later enables required reviewers or wait timers, both `deploy_and_test` and `cleanup` will pause for approval before Azure access because both jobs declare that environment.

| Name | Type | Description |
| --- | --- | --- |
| `AZURE_CLIENT_ID` | Secret | App Registration Client ID (OIDC) |
| `AZURE_TENANT_ID` | Secret | Azure Tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Secret | Azure Subscription ID |
| `AZURE_LOCATION` | Variable | Azure region (default: `koreacentral`) |

### Federated Credential (OIDC) Setup

Azure login uses [GitHub OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect) to exchange a short-lived token with the Azure AD app registration referenced by `AZURE_CLIENT_ID`. The app registration must have a federated credential whose **subject claim matches exactly** the value GitHub presents.

For this workflow, the expected subject is:

```text
repo:yeongseon/azure-functions-scaffold-python:environment:azure-e2e
```

The subject is composed of `repo:<owner>/<repo>:environment:<environment_name>`, where:

- `<owner>/<repo>` is the GitHub repository slug (`github.repository`). Not the PyPI package name (`azure-functions-scaffold-python`) or the Python import name (`azure_functions_scaffold`).
- `<environment_name>` is the GitHub Environment declared on the workflow jobs (`environment: azure-e2e`).

The match is **case-sensitive** and exact. Renaming the GitHub owner, repository, or environment requires updating the federated credential in Azure to match the new subject; otherwise Azure login fails with `AADSTS700213`.

#### Why one environment-based subject (and not branch / tag subjects)?

The workflow runs from both `workflow_dispatch` (typically against `main`) and `push` of `v*` tags. Without an environment, GitHub mints ref-based OIDC subjects such as:

- `repo:yeongseon/azure-functions-scaffold-python:ref:refs/heads/main` (for dispatches against `main`)
- `repo:yeongseon/azure-functions-scaffold-python:ref:refs/tags/v0.6.1` (for tag pushes)

Maintaining ref-based credentials is brittle: you need one for `refs/heads/main` and, for tag runs, either flexible tag matching in Entra or separate credentials for concrete tag refs. Using a GitHub environment avoids that drift and keeps one stable subject, which only changes if the owner/repo/environment is renamed.

Reference:

- Workflow declares `environment: azure-e2e` on both `deploy_and_test` and `cleanup` jobs in `.github/workflows/e2e-azure.yml`.
- Azure docs: [Configure a federated identity credential on an app](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust?pivots=identity-wif-apps-methods-azp).

### Troubleshooting Azure E2E

#### `AADSTS700213: No matching federated identity record found`

The OIDC subject GitHub presented does not match any federated credential on the Azure AD app registration behind `AZURE_CLIENT_ID`. Typical causes:

1. The repository was renamed (for example, the toolkit-wide `-python` suffix migration) and the federated credential still references the old subject.
2. The `environment:` value on the workflow job changed and the federated credential references the old environment name.
3. A different app registration is configured in the `azure-e2e` environment secrets than the one carrying the federated credential.
4. The federated credential still references a ref-based subject (`refs/heads/main` or a concrete `refs/tags/<tag>`) from a version of the workflow that did not declare `environment:`.

To recover:

1. Confirm which Azure AD app registration is referenced by the `AZURE_CLIENT_ID` value used by the `azure-e2e` GitHub Environment (or the repository).
2. On that app registration, add or update a federated credential with subject `repo:yeongseon/azure-functions-scaffold-python:environment:azure-e2e`, issuer `https://token.actions.githubusercontent.com`, and audience `api://AzureADTokenExchange`.
3. Re-run `e2e-azure` (tag push or `workflow_dispatch`) and confirm the `Azure login (OIDC)` step succeeds.

## Troubleshooting

- **Temporary files:** If a test fails, `tmp_path` is automatically cleaned up. To inspect generated files, you can print the path during a local run.
- **Template rendering:** Use `pytest -s` to see output if you suspect a Jinja2 rendering error.
- **Imports:** Ensure you are running tests via `make test` or `hatch run pytest` to correctly set the Python path for the `src` directory.
