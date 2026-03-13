# Azure Functions Scaffold

Production-ready Azure Functions Python v2 projects in seconds.

`azure-functions-scaffold` generates an opinionated baseline for teams that want
to ship Azure Functions projects with clear boundaries, reliable tests, and
standardized tooling from day one.

## Get Started

```bash
pip install azure-functions-scaffold
azure-functions-scaffold new my-api
cd my-api
func start
```

## Why Azure Functions Scaffold

- Opinionated project structure with clear separation between triggers,
  services, schemas, and infrastructure concerns.
- Type-safe defaults with optional request/response validation for predictable
  contracts.
- Integrated ecosystem support for OpenAPI, structured logging, and health
  diagnostics.
- Fast local-first workflow designed to run offline with Azure Functions Core
  Tools and Azurite-ready templates.

## Generated Code Preview

When you run `azure-functions-scaffold new my-api --template http`, the
generated `function_app.py` starts as executable Azure Functions Python v2 code:

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!", status_code=200)
```

## Documentation

Start with these core pages:

- [`quickstart.md`](quickstart.md): Create, run, test, and deploy your first project.
- [`why.md`](why.md): Rationale behind the generated folder and code structure.
- [`installation.md`](installation.md): Environment setup and installation details.
- [`cli.md`](cli.md): Full command and option reference.

Reference guides:

- [`template_spec.md`](template_spec.md): Template behavior and generated files.
- [`architecture.md`](architecture.md): Internal design of the scaffold engine.
- [`style_guide.md`](style_guide.md): Conventions used across generated code.
- [`development.md`](development.md): Contributor workflow and local dev tasks.
- [`testing.md`](testing.md): Testing strategy and execution commands.

Project health and governance:

- [`troubleshooting.md`](troubleshooting.md): Common issues and fixes.
- [`roadmap.md`](roadmap.md): Planned capabilities and milestones.
- [`security.md`](security.md): Security policy and reporting process.
- [`changelog.md`](changelog.md): Release history.
- [`contributing.md`](contributing.md): Contribution guidelines.

## Ecosystem

- Validation: [azure-functions-validation](https://github.com/yeongseon/azure-functions-validation)
- OpenAPI: [azure-functions-openapi](https://github.com/yeongseon/azure-functions-openapi)
- Doctor: [azure-functions-doctor](https://github.com/yeongseon/azure-functions-doctor)
- Logging: [azure-functions-logging](https://github.com/yeongseon/azure-functions-logging)
- Cookbook: [azure-functions-cookbook](https://github.com/yeongseon/azure-functions-cookbook)

Use the Quick Start page to scaffold your first project, then move to the CLI
reference and template spec when you need custom generation flows.
