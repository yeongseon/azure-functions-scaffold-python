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

Tests are located in the `tests/` directory:

```
tests/
  test_new.py        # scaffold new command and template generation
  test_cli.py        # CLI option parsing and dry-run mode
  test_templates.py  # Jinja2 template rendering for all function types
```

## CI Test Matrix

Tests run automatically on every pull request and push to `main`. The CI matrix covers:

| Python Version | Status |
| -------------- | ------ |
| 3.10 | Tested |
| 3.11 | Tested |
| 3.12 | Tested |
| 3.13 | Tested |
| 3.14 | Preview - allowed to fail |

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
