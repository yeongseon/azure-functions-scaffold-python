# Full Stack Example

This scenario uses the full recommended option set:

- strict quality preset
- OpenAPI documentation
- request/response validation
- doctor checks

Use this as a production baseline for HTTP APIs.

## 1) Generate the Project

```bash
afs new commerce-api \
  --template http \
  --preset strict \
  --with-openapi \
  --with-validation \
  --with-doctor \
  --github-actions
```

This combines template, quality tooling, API docs, validation, diagnostics,
and CI bootstrap in one command.

## 2) Bootstrap Local Development

```bash
cd commerce-api
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
cp local.settings.json.example local.settings.json
```

Run all checks:

```bash
make check-all
```

Run doctor diagnostics (enabled by `--with-doctor`):

```bash
make doctor
```

!!! note "What doctor adds"
    `--with-doctor` adds `azure-functions-doctor` dependency and Makefile target.
    It does not auto-create an HTTP endpoint.

## 3) Verify Generated Feature Set

You should see:

- OpenAPI routes in `function_app.py`
- validation decorators and Pydantic models in HTTP module/schemas
- strict tools (`ruff`, `mypy`, `pytest`) in `pyproject.toml`
- `doctor` target in `Makefile`
- optional workflow under `.github/workflows/` with `--github-actions`

## 4) Run Locally and Validate Endpoints

Start runtime:

```bash
func start
```

Test validated hello endpoint:

```bash
curl -X POST "http://localhost:7071/api/hello" \
  -H "Content-Type: application/json" \
  -d '{"name":"Commerce"}'
```

Open docs:

```text
http://localhost:7071/api/docs
```

Fetch OpenAPI JSON:

```bash
curl "http://localhost:7071/api/openapi.json"
```

## 5) Extend API with Additional Endpoints

Add a product list endpoint:

```bash
afs add http list_products --project-root .
```

Add an order status endpoint:

```bash
afs add http get_order_status --project-root .
```

Use dry-run before either change if needed:

```bash
afs add http get_order_status --project-root . --dry-run
```

## 6) Add Service Layer and Contracts

Example service module (`app/services/product_service.py`):

```python
from __future__ import annotations


def list_products() -> list[dict[str, object]]:
    return [
        {"sku": "SKU-001", "name": "Notebook", "price": 12.5},
        {"sku": "SKU-002", "name": "Pen", "price": 1.9},
    ]
```

Example schema additions (`app/schemas/request_models.py`):

```python
from pydantic import BaseModel


class OrderStatusRequest(BaseModel):
    order_id: str


class OrderStatusResponse(BaseModel):
    order_id: str
    status: str
```

!!! tip "Keep trigger modules thin"
    Treat `app/functions/*.py` as adapter layers: validation, auth, and
    transport mapping. Keep business logic in `app/services/`.

## 7) Production-Like Quality Gate

Run local quality pipeline before merge/deploy:

```bash
ruff check .
ruff format --check .
mypy .
pytest
make doctor
```

You can also rely on:

```bash
make check-all
```

## 8) Suggested CI Pipeline Stages

1. Install dependencies (`pip install -e .[dev]`)
2. Lint (`ruff check .`)
3. Type check (`mypy .`)
4. Test (`pytest`)
5. Doctor checks (`python -m azure_functions_doctor check .`)

This order gives fast feedback while keeping release gates strict.

## 9) Deployment Handoff

Before deploying to Azure:

- verify app settings and connection strings
- confirm auth level choices for routes
- validate OpenAPI endpoint behavior
- run full quality and doctor checks

Publish with Core Tools:

```bash
func azure functionapp publish <APP_NAME>
```

## Troubleshooting Notes

!!! warning "Validation route method mismatch"
    With validation enabled, generated hello endpoint is `POST`, not `GET`.

!!! warning "Doctor command missing"
    Confirm project was created with `--with-doctor` and re-run dependency
    installation so the package is available.

!!! warning "OpenAPI docs unavailable"
    Confirm generation included `--with-openapi` and runtime is started from the
    correct project root.

## Next Steps

- Follow [API Reference](../reference/api.md) for programmatic integration.
- Use [Configuration](../guide/configuration.md) to standardize team defaults.
- Review [FAQ](../faq.md) for common setup decisions.
