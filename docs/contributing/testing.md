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
- **Trigger**: Manual only (`workflow_dispatch`)
- **Infrastructure**: Azure Consumption plan, `koreacentral` region (`AZURE_LOCATION` variable)
- **Cleanup**: Resource group deleted immediately after tests (`if: always()`)

### Required Secrets & Variables

The Azure OIDC secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`) are provided as repository-level secrets, matching the sibling `azure-functions-*` repositories. `AZURE_LOCATION` is read from the `vars` context with a fallback to `koreacentral`.

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
repo:yeongseon/azure-functions-scaffold-python:ref:refs/heads/main
```

The subject is composed of `repo:<owner>/<repo>:ref:<git_ref>`, where:

- `<owner>/<repo>` is the GitHub repository slug (`github.repository`). Not the PyPI package name (`azure-functions-scaffold-python`) or the Python import name (`azure_functions_scaffold`).
- `<git_ref>` is the ref the workflow runs against. Because the workflow is dispatch-only and dispatched from `main`, GitHub mints `ref:refs/heads/main`.

The match is **case-sensitive** and exact. Renaming the GitHub owner or repository, or dispatching from a different branch, requires updating the federated credential in Azure to match the new subject; otherwise Azure login fails with `AADSTS700213`.

#### Why a ref-based subject (and no GitHub environment)?

This workflow does not declare a GitHub `environment:`, matching the sibling `azure-functions-*` repositories (`openapi`, `logging`, `doctor`). Since the workflow is dispatch-only and always dispatched from `main`, GitHub mints a single stable ref-based subject (`ref:refs/heads/main`), so exactly one federated credential is required. A GitHub environment would instead mint `environment:<name>` and require a matching environment-scoped credential.

> If you later want approval gating (required reviewers or wait timers) before the destructive Azure run, declare `environment: azure-e2e` on both jobs **and** add an environment-scoped federated credential (`...:environment:azure-e2e`) to the app registration. Do both together, or Azure login will fail with `AADSTS700213`.

Reference:

- Azure docs: [Configure a federated identity credential on an app](https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-create-trust?pivots=identity-wif-apps-methods-azp).

### Troubleshooting Azure E2E

#### `AADSTS700213: No matching federated identity record found`

The OIDC subject GitHub presented does not match any federated credential on the Azure AD app registration behind `AZURE_CLIENT_ID`. Typical causes:

1. The repository was renamed (for example, the toolkit-wide `-python` suffix migration) and the federated credential still references the old subject.
2. A GitHub `environment:` was added to the workflow job, so GitHub now mints an `environment:<name>` subject, but the credential still references the ref-based subject (or vice versa).
3. A different app registration is configured in the repository secrets than the one carrying the federated credential.
4. The workflow was dispatched from a branch other than `main`, minting `ref:refs/heads/<branch>` with no matching credential.

To recover:

1. Confirm which Azure AD app registration is referenced by the repository's `AZURE_CLIENT_ID` value.
2. On that app registration, add or update a federated credential with subject `repo:yeongseon/azure-functions-scaffold-python:ref:refs/heads/main`, issuer `https://token.actions.githubusercontent.com`, and audience `api://AzureADTokenExchange`.
3. Re-run `e2e-azure` via `workflow_dispatch` and confirm the `Azure login (OIDC)` step succeeds.

## Troubleshooting

- **Temporary files:** If a test fails, `tmp_path` is automatically cleaned up. To inspect generated files, you can print the path during a local run.
- **Template rendering:** Use `pytest -s` to see output if you suspect a Jinja2 rendering error.
- **Imports:** Ensure you are running tests via `make test` or `hatch run pytest` to correctly set the Python path for the `src` directory.
