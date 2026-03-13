# Introduction

Azure Functions Scaffold is a developer-focused CLI tool designed to jumpstart Azure Functions Python v2 projects. It handles the boilerplate of the Blueprint programming model, directory structure, and linting configuration so you can focus on writing business logic.

### Who it's for

*   **Production Teams**: Developers who need a consistent, testable structure across multiple function apps.
*   **Rapid Prototypers**: Users who want to move from an idea to a running HTTP or Timer function in seconds.
*   **Quality Enthusiasts**: Teams that want pre-configured Ruff, MyPy, and Pytest suites without manual setup.

### What you get

*   **Modular Architecture**: Automatic implementation of the Blueprint pattern for clean separation of concerns.
*   **Tooling Presets**: Choose between Minimal, Standard (Ruff + Pytest), or Strict (Ruff + MyPy + Pytest) configurations.
*   **Feature Flags**: Toggle OpenAPI support, Pydantic validation, or health check "doctor" endpoints during generation.
*   **Extensible**: Add new triggers to existing projects with a single command that updates all relevant files.

### Quickstart

Install the CLI, generate a project, and start the local runtime.

```bash
pip install azure-functions-scaffold
afs new my-api --preset standard
cd my-api && func start
```

### What's Next?

*   [Getting Started](getting-started.md): Install prerequisites and create your first project.
*   [Project Structure](project-structure.md): Understand the generated files and layers.
*   [Templates](templates.md): Explore supported triggers like Queue, Blob, and Service Bus.
