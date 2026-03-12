# Architecture

## Overview

azure-functions-scaffold is a CLI tool built on Typer and Jinja2 that generates Azure Functions Python v2 projects from embedded templates. The project is designed around three main concerns: command parsing, template rendering, and embedded project templates. By keeping templates inside the package distribution, the tool ensures fast, reliable, and deterministic project generation without requiring network access during the scaffolding process. The goal is to provide a standardized starting point for Azure Functions development that follows best practices for Python v2 programming models.

The system handles both full project initialization and incremental function additions. This dual approach allows developers to start from a clean slate or grow their applications over time. All generated code is designed to be readable, lint-clean, and easy to modify, ensuring that the scaffolded project serves as a helpful foundation rather than a restrictive framework. The project is built to be a robust, high-performance tool for developers who want to avoid the boilerplate often associated with serverless applications.

The design emphasizes simplicity and speed, making it an ideal choice for both rapid prototyping and enterprise-grade application development. By providing a solid structure from the very beginning, azure-functions-scaffold helps teams maintain consistency across their serverless portfolios. This approach minimizes the technical debt often introduced during the early stages of a project's lifecycle, as every generated component follows a uniform and well-tested pattern. The tool's internal design is modular, allowing for easy updates to the underlying templates as the Azure Functions runtime evolves.

Furthermore, the architecture is built to be accessible to developers of all skill levels. For those new to Azure Functions, the tool provides a clear path forward by generating high-quality code that can be used for learning. For experienced users, the highly customizable templates and presets offer the flexibility needed to meet specific project requirements without sacrificing the benefits of automation. This inclusivity ensures that the tool remains a valuable resource across a diverse range of development environments and use cases, from small personal projects to large-scale industrial solutions. This versatility is a core strength, as it allows the tool to serve as both a pedagogical aid and a production-ready engineering tool.

By choosing azure-functions-scaffold, developers gain more than just a code generator. They gain a methodology for building serverless applications that are scalable, maintainable, and aligned with industry standards. The tool acts as a bridge between the complex requirements of cloud-native development and the need for a simple, streamlined workflow.

## Runtime Flow

### new command

The `new` command is the primary entry point for creating complete projects. It orchestrates the entire process from user input to the final file structure on disk.

1. The user runs `azure-functions-scaffold new <project-name>` or uses the `--interactive` flag to start a guided setup. This initial interaction defines the entire project's structure and characteristics.
2. Typer dispatches the request to `cli.py`, which handles initial argument parsing and determines whether to enter an interactive mode.
3. If the interactive flag is present, the CLI prompts the user for the project name, template type, preset, Python version, tooling, and optional feature flags. These prompts are designed to be intuitive while still providing deep customization.
4. `cli.py` calls `_resolve_new_project_inputs()` to gather all validated inputs into a `ProjectOptions` object, which acts as a single source of truth for the session.
5. `build_project_options()` in `template_registry.py` validates the selected preset, Python version, and tooling compatibility to ensure the requested configuration is supported.
6. `scaffold_project()` in `scaffolder.py` validates the project name against filesystem constraints and resolves the absolute destination path on the user's machine.
7. `scaffolder.py` builds a `TemplateContext` from the provided options, mapping user choices to the variables expected by the Jinja2 templates.
8. Jinja2 renders each `.j2` template found in the template root. The rendering process handles file names, directory structures, and file contents dynamically based on the provided context.
9. The resulting rendered files are written to the destination directory. Finally, a git repository is initialized if the user has requested it through flags or interactive prompts.

### add command

The `add` command allows users to extend existing projects with new functions, maintaining the same structure and coding style as the initial scaffold.

1. The user runs `azure-functions-scaffold add <trigger> <function-name>` to add a new function to their project. This command is designed to be non-destructive.
2. `add_function()` in `generator.py` validates the current directory as a valid project root by checking for key files and directory structures.
3. The generator checks the requested trigger type against the available templates, which include http, timer, queue, blob, and servicebus.
4. The system renders function, service, and test modules from the specific trigger templates, ensuring that each new function comes with its own isolated logic and tests.
5. The system appends the new function registration to the existing `function_app.py` file, integrating it into the project's runtime without overwriting existing registrations.

## Rendered Pipeline Examples

The rendering pipeline produces plain Python modules that are ready to run. The examples below show generated output artifacts at each stage.

### Stage 1: Generated app entrypoint (`function_app.py`)

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    return func.HttpResponse(f"Hello, {name}!", status_code=200)
```

### Stage 2: Generated trigger module (`app/functions/http.py`)

```python
import azure.functions as func

from app.services.hello_service import build_hello_message

bp = func.Blueprint()


@bp.route(route="hello", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "World")
    message = build_hello_message(name)
    return func.HttpResponse(message, status_code=200)
```

### Stage 3: Generated test module (`tests/test_http.py`)

```python
from app.services.hello_service import build_hello_message


def test_build_hello_message_defaults_to_world() -> None:
    assert build_hello_message("World") == "Hello, World!"
```

## Module Boundaries

The codebase is organized into specialized modules with clear responsibilities and minimal overlap:

- **cli.py** (384 lines): This is the main entry point for the application. It defines the Typer application structure, handles complex argument parsing, manages the interactive prompt logic, and translates internal `ScaffoldError` exceptions into user-friendly messages. It is responsible for the overall user experience and CLI behavior.
- **scaffolder.py**: This module handles the core logic for project creation. It manages project name validation, destination resolution, Jinja2 template rendering, directory creation, and git initialization. It is the engine that drives the `new` command and ensures the project is set up correctly.
- **generator.py**: This module focuses on the incremental addition of functions to existing projects. It handles trigger validation and the safe, non-destructive modification of existing project files like `function_app.py`. It ensures that new code fits perfectly into the existing project structure.
- **template_registry.py** (131 lines): This serves as the central authority for all available templates and presets. It validates Python versions, tooling choices, and constructs the `ProjectOptions` used by the rest of the system. It is the definitive source for what the tool can generate.
- **models.py** (46 lines): Defines the frozen dataclasses used for type-safe data passing throughout the application. These include `TemplateContext`, `TemplateSpec`, `PresetSpec`, and `ProjectOptions`, ensuring that data cannot be modified unexpectedly during the runtime flow.
- **errors.py** (5 lines): Contains the `ScaffoldError` exception class, which is the base for all expected errors in the application. This allows the CLI to catch and report specific failures gracefully, providing a better experience for the user.
- **templates/**: A directory containing the actual Jinja2 `.j2` template files. These are organized by trigger type (http, timer, queue, blob, and servicebus) and provide the blueprint for the generated projects and functions.

## Data Model

The application uses frozen dataclasses to ensure data integrity and clear communication between modules:

- **TemplateContext**: A frozen dataclass containing all variables required for rendering templates, such as project name, Python version, and specific feature flags. This object is passed directly to the Jinja2 environment for processing.
- **ProjectOptions**: A frozen dataclass that encapsulates the choices made by the user, whether they were provided via CLI flags or interactive prompts. This is the primary input for the scaffolding process.
- **TemplateSpec**: A frozen dataclass that defines a template's metadata, including its name, description, and its root path within the package. This is used by the registry to track available triggers.
- **PresetSpec**: A frozen dataclass that defines a preset's name, description, and the specific tooling tuple (like ruff, mypy, or pytest) it includes. This helps define the "standard," "minimal," and "strict" configurations.
- **ScaffoldError**: A single, custom exception type used to signal issues like validation failures or filesystem errors, which are then caught and displayed by the CLI layer.

## Template System

The template system is designed to be self-contained and highly flexible:

- All templates are embedded directly inside the package distribution. This guarantees that the tool works offline and that the generated code is always consistent with the installed version of the CLI.
- Each trigger type (http, timer, queue, blob, and servicebus) has its own dedicated directory under the `templates/` path, allowing for clear separation of concerns and easy extension in the future.
- The system uses Jinja2 with extensive conditional blocks. This allows the same template to adapt to different presets (minimal, standard, and strict) and Python versions, ensuring the output is always optimized for the user's choices.
- The output is entirely deterministic. Given the same inputs, the tool will always produce the exact same file structure and content, which is essential for testing, reliability, and automated workflows.
- The templates are kept simple and readable, making them easy to maintain and update as the underlying Azure Functions programming model changes over time.

## Design Constraints

The architecture is guided by several strict principles to ensure a high-quality developer experience:

- The system maintains minimal dependencies, relying primarily on `jinja2` for rendering and `typer` for the CLI interface to keep the installation footprint small and manageable.
- No network calls are permitted during the scaffolding or generation process to ensure speed, security, and reliability in all environments, including air-gapped systems.
- All output must be deterministic and predictable across different environments, ensuring that users can rely on the tool for consistent project setups.
- Templates are always packaged inside the distribution artifacts rather than being downloaded on demand, avoiding versioning issues and network dependencies.
- Generated code is required to be lint-clean and format-clean according to modern Python standards (e.g., Ruff), providing a professional starting point for any new project.
- The resulting code must remain easy for developers to edit by hand, avoiding overly complex abstractions in the generated output that would hinder modification or maintenance.
- Every interactive flow must have a corresponding non-interactive CLI flag, enabling the tool to be used in CI/CD pipelines, automated scripts, and other devops scenarios.

## Dependency Graph

The flow of information and dependencies follows a clear, directed hierarchy that minimizes circular dependencies and promotes modularity:

- `cli.py` acts as the orchestrator, depending on `scaffolder.py`, `generator.py`, `template_registry.py`, and `models.py`.
- `scaffolder.py` and `generator.py` perform the core work, both depending on `template_registry.py` and `models.py`.
- `template_registry.py` defines the available options and depends on `models.py` for its data structures.
- Every module in the system depends on `errors.py` for consistent error handling and reporting across the entire application.

This structured approach ensures that concerns are clearly separated, making the codebase easier to maintain, test, and extend as new Azure Functions features or Python versions are released. By focusing on a clean dependency graph, the tool remains robust even as the number of supported triggers and presets grows over time. This architectural clarity allows developers to quickly understand how the tool works and contribute to its ongoing development, ensuring that the scaffold remains relevant in an ever-changing technical landscape. The result is a tool that is not only powerful but also remarkably easy to maintain and evolve as the serverless ecosystem continues to mature and expand. Each module is documented to ensure that future contributors can pick up the project with ease, maintaining the high standards of quality and performance that have been established from the beginning. This level of detail in the design ensures that azure-functions-scaffold remains a leader in the space for years to come.
