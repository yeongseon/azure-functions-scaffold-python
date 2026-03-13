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
afs new secure-api --preset strict
```

### Feature Flags

Combine flags to add specialized capabilities to your project.

#### --with-openapi

Adds `azure-functions-openapi` to the dependencies and configures HTTP triggers with the necessary decorators for Swagger/OpenAPI documentation.

```bash
afs new swagger-api --with-openapi
```

#### --with-validation

Adds Pydantic to the dependencies and sets up base models in `app/schemas/`. If used with an HTTP trigger, it provides a `POST` endpoint with request body validation.

```bash
afs new validator-api --with-validation
```

#### --with-doctor

Adds a "Doctor" health check endpoint at `/api/doctor`. This endpoint provides a structured JSON response to verify the function app's health.

```bash
afs new healthy-api --with-doctor
```

### Combination Examples

You can mix and match any combination of presets and flags.

```bash
# Production-ready API with all features
afs new commerce-api --preset strict --with-openapi --with-validation --with-doctor

# Minimal timer function with GitHub Actions workflow
afs new nightly-job --template timer --preset minimal --github-actions
```

### Interactive Mode

If you're unsure which flags to use, start the CLI in interactive mode to be guided through the selection process.

```bash
afs new my-api --interactive
```

### What's Next?

Learn how to [Expand Your Project](expanding.md) by adding more triggers to an existing codebase.
