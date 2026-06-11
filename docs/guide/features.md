# Features and Presets

Presets define the development tooling included in your project, while feature flags add specific functionality like API documentation or data validation.

### Tooling Presets

Presets configure `pyproject.toml` with linting, formatting, and testing tools.

| Preset | Included Tools | Recommended For |
| :--- | :--- | :--- |
| **minimal** | None | Quick experiments, simple scripts. |
| **standard** | Ruff, Pytest | Most production apps (Default). |
| **strict** | Ruff, MyPy, Pytest | Large teams, mission-critical systems. |

#### Example: Strict Preset

Use the strict preset to enforce type safety and strict linting.

```bash
afs advanced new --preset strict secure-api
```

### Feature Flags

Combine flags to add specialized capabilities to your project.

#### Structured Logging (Built-in)

Every scaffold template includes `azure-functions-logging` as a default dependency.
Structured JSON logging is configured in `app/core/logging.py` and activated at startup
in `function_app.py` — no flag required.

```python
# app/core/logging.py (generated)
from azure_functions_logging import get_logger, setup_logging


def configure_logging() -> None:
    setup_logging(format="json")


logger = get_logger("my-api")
```

To use structured logging anywhere in your app:

```python
from app.core.logging import logger

logger.info("request received", route="/api/hello")
```

See [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging-python) for the full API.

#### --with-openapi

Adds `azure-functions-openapi` to the dependencies and configures HTTP triggers with the necessary decorators for Swagger/OpenAPI documentation.

```bash
afs advanced new --with-openapi swagger-api
```

#### --with-validation

Adds Pydantic to the dependencies and sets up base models in `app/schemas/`. If used with an HTTP trigger, it provides a `POST` endpoint with request body validation.

```bash
afs advanced new --with-validation validator-api
```

#### --with-doctor

Adds a "Doctor" health check endpoint at `/api/doctor`. This endpoint provides a structured JSON response to verify the function app's health.

```bash
afs advanced new --with-doctor healthy-api
```

### Combination Examples

You can mix and match any combination of presets and flags.

```bash
# Production-ready API with all features
afs advanced new --preset strict --with-openapi --with-validation --with-doctor commerce-api

# Minimal timer function with GitHub Actions workflow
afs advanced new --template timer --preset minimal --github-actions nightly-job
```

### What's Next?

Learn how to [Expand Your Project](expanding.md) by adding more triggers to an existing codebase.
