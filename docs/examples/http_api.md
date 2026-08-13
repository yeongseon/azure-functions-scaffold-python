# HTTP API Example

This walkthrough builds an HTTP-focused Azure Functions project, customizes the
generated code, adds a second endpoint, and runs everything locally.

## What You Will Build

By the end, you will have:

- a scaffolded HTTP project
- optional OpenAPI and validation support
- two HTTP function modules (`health` and `webhooks`)
- local run and curl verification flow

## 1) Generate the Project

Create a strict project with OpenAPI and validation enabled:

```bash
afs advanced new \
  --template http \
  --preset strict \
  --with-openapi \
  --with-validation \
  my-http-api
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

The `http` template generates two endpoints:

- `GET /api/health` — anonymous auth, returns `{"status": "ok"}`.
- `POST /api/webhooks/inbound` — FUNCTION auth, verifies an HMAC-SHA256 signature from the `X-Signature` header against the `WEBHOOK_SECRET` environment variable. Returns 503 when the secret is not configured, 401 on signature mismatch, and 202 on success.

!!! note "Default route mode"
    The health endpoint uses anonymous auth so it can be polled by infrastructure without credentials. The webhook endpoint uses FUNCTION auth and signature verification to authenticate external callers.

The `function_app.py` entrypoint also includes OpenAPI routes when
`--with-openapi` is enabled:

- `GET /api/docs`
- `GET /api/openapi.json`
- `GET /api/openapi.yaml`

## 3) Run the Function App Locally

```bash
func start
```

In a second terminal, test the health endpoint:

```bash
curl "http://localhost:7071/api/health"
```

Expected response:

```json
{"status": "ok"}
```

Open Swagger UI:

```text
http://localhost:7071/api/docs
```

## 4) Add a New HTTP Endpoint Module

Use `afs api add` to add a second endpoint scaffold:

```bash
afs api add users --project-root .
```

This command:

1. Creates `app/functions/users.py`.
2. Creates `tests/test_users.py` (if `tests/` exists).
3. Updates `function_app.py` import and registration markers.

Preview before writing if needed:

```bash
afs api add users --project-root . --dry-run
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

!!! warning "Webhook secret not set"
    With `WEBHOOK_SECRET` unset, `POST /api/webhooks/inbound` returns 503. Set it in `local.settings.json` before testing the webhook endpoint locally.

## Next Steps

- Follow [Full Stack Example](full_stack.md) for a complete strict setup.
- See [Configuration](../guide/configuration.md) for option combinations.
- Use [Troubleshooting](../guide/troubleshooting.md) for runtime issues.
