# Testing

## Verification contract

`make check` is non-mutating quality; `make test` is offline with >=95% coverage.
`make integration` runs ten isolated generated suites plus an owned HTTP
Functions host and Azurite. `make verify` adds quality, wheel smoke, build and
strict docs; `make check-all` is an exact alias. `make doctor` reports prerequisites,
`make report` reads saved results, and `make clean` removes only generated artifacts.
Focused commands are PARTIAL, not Azure certification.

Required generated tests must execute positive cases: exit 5, zero execution,
all-skipped and unexpected skips block. Doctor JSON is classified into required
findings, advisory recommendations, CLI errors and crashes; only advisories pass.
Missing required diagnostic identities block. The sole manifest exemption is
generated LangGraph with Doctor 0.23.1's exact adapter-detection short circuit
([Doctor #590](https://github.com/yeongseon/azure-functions-doctor-python/issues/590)),
owned by `yeongseon` and expiring 2026-11-23 UTC. Diagnostics remain **INCOMPLETE**
in a separate summary and the template's `diagnostics_status`; only this diagnostic
requirement is temporarily optional. Structure, compile/lint/types, positive pytest
and a real SDK FunctionApp export with registered functions still block the matrix job.
No other template, report shape or Doctor version is exempt; expiry fails closed.
See the [contributing guide](https://github.com/yeongseon/azure-functions-scaffold-python/blob/main/CONTRIBUTING.md)
for the stable rule policy, isolated wheel provenance, prerequisites and evidence.

`test-results/` contains separate generator, generated-project, installed-wheel,
host, full-local and Azure generation/remote summaries. PASS/FAIL/INCOMPLETE/
NOT_APPLICABLE results include counts and redacted environment metadata. Missing
required proofs never PASS. Explicit Azure validation requires a generated project,
deployed HTTPS URL, expected scaffold version and candidate wheel before tests.

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
