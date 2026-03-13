# Azure Functions Scaffold

Scaffolding CLI for production-ready Azure Functions Python v2 projects.

Azure Functions Scaffold generates modular, testable project structures using the
Blueprint programming model. It handles directory layout, linting configuration,
and tooling presets so you can focus on business logic.

## Who it's for

*   **Production Teams**: Developers who need a consistent, testable structure across multiple function apps.
*   **Rapid Prototypers**: Users who want to move from an idea to a running HTTP or Timer function in seconds.
*   **Quality Enthusiasts**: Teams that want pre-configured Ruff, MyPy, and Pytest suites without manual setup.

## Quick Start

```bash
pip install azure-functions-scaffold
afs new my-api --preset standard
cd my-api && func start
```

Open `http://localhost:7071/api/hello` in your browser to see your first function in action.

## What you get

*   **Modular Architecture**: Automatic implementation of the Blueprint pattern for clean separation of concerns.
*   **Tooling Presets**: Choose between Minimal, Standard (Ruff + Pytest), or Strict (Ruff + MyPy + Pytest) configurations.
*   **Feature Flags**: Toggle OpenAPI support, Pydantic validation, or health check "doctor" endpoints during generation.
*   **Extensible**: Add new triggers to existing projects with a single command that updates all relevant files.

## Next Steps

*   [Getting Started](guide/getting-started.md): Install prerequisites and create your first project.
*   [Project Structure](guide/project-structure.md): Understand the generated files and layers.
*   [Templates](guide/templates.md): Explore supported triggers like Queue, Blob, and Service Bus.
*   [CLI Reference](reference/cli.md): Full list of commands, flags, and defaults.
