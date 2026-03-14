# HTTP API Example

This walkthrough builds an HTTP-focused Azure Functions project, customizes the
generated code, adds a second endpoint, and runs everything locally.

## What You Will Build

By the end, you will have:

- a scaffolded HTTP project
- optional OpenAPI and validation support
- two HTTP function modules (`hello` and `users`)
- local run and curl verification flow

## 1) Generate the Project

Create a strict project with OpenAPI and validation enabled:

```bash
afs new my-http-api \
  --template http \
  --preset strict \
  --with-openapi \
  --with-validation
```

Move into the project and install dependencies:

```bash
cd my-http-api
python -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

Run baseline checks:

```bash
make check-all
```

## 2) Understand Generated HTTP Behavior

With `--with-validation` enabled, the default `hello` route is generated as a
`POST` endpoint that validates body models.

!!! note "Default route mode changes"
    Without validation, the default route is `GET /api/hello` and reads query
    params. With validation enabled, it becomes `POST /api/hello` and expects a
    JSON body.

The `function_app.py` entrypoint also includes OpenAPI routes when
`--with-openapi` is enabled:

- `GET /api/docs`
- `GET /api/openapi.json`
- `GET /api/openapi.yaml`

## 3) Run the Function App Locally

```bash
func start
```

In a second terminal, test the validated hello route:

```bash
curl -X POST "http://localhost:7071/api/hello" \
  -H "Content-Type: application/json" \
  -d '{"name":"Azure"}'
```

Expected response shape:

```json
{"message":"Hello, Azure!"}
```

Open Swagger UI:

```text
http://localhost:7071/api/docs
```

## 4) Add a New HTTP Endpoint Module

Use `afs add` to add a second endpoint scaffold:

```bash
afs add http users --project-root .
```

This command:

1. Creates `app/functions/users.py`.
2. Creates `tests/test_users.py` (if `tests/` exists).
3. Updates `function_app.py` import and registration markers.

Preview before writing if needed:

```bash
afs add http users --project-root . --dry-run
```

## 5) Customize the New Endpoint

Edit `app/functions/users.py` so the route returns user list data:

```python
from __future__ import annotations

import json

import azure.functions as func

users_blueprint = func.Blueprint()  # type: ignore[no-untyped-call]


@users_blueprint.route(
    route="users",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def users(req: func.HttpRequest) -> func.HttpResponse:
    payload = {
        "items": [
            {"id": 1, "name": "Ada"},
            {"id": 2, "name": "Grace"},
        ]
    }
    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=200,
        mimetype="application/json",
    )
```

!!! tip "Keep business logic separated"
    For larger endpoints, move data access and business rules into
    `app/services/` and keep trigger modules thin.

## 6) Test the New Endpoint

Run checks and tests:

```bash
make check-all
```

Run locally again:

```bash
func start
```

Call the new route:

```bash
curl "http://localhost:7071/api/users"
```

Example response:

```json
{"items":[{"id":1,"name":"Ada"},{"id":2,"name":"Grace"}]}
```

## 7) Common HTTP Customization Patterns

- Add request/response models in `app/schemas/`.
- Add OpenAPI annotations for each route when docs are enabled.
- Keep trigger code in `app/functions/`, service logic in `app/services/`.
- Use pytest tests in `tests/` for endpoint behavior.

## Troubleshooting Notes

!!! warning "OpenAPI routes missing"
    Regenerate with `--with-openapi`, or verify your project was created with
    that flag. OpenAPI routes are generated at creation time.

!!! warning "Validation errors on hello"
    With validation enabled, `hello` expects JSON body fields that match
    `app/schemas/request_models.py`.

## Next Steps

- Follow [Full Stack Example](full_stack.md) for a complete strict setup.
- See [Configuration](../guide/configuration.md) for option combinations.
- Use [Troubleshooting](../guide/troubleshooting.md) for runtime issues.
