# Contribution Guidelines

Thank you for your interest in contributing to azure-functions-scaffold! This document outlines our process for receiving and managing contributions.

## Project Scope

We welcome contributions that improve the core functionality, add new Azure Functions triggers, enhance documentation, or fix bugs.

Our goal is to provide a fast, reliable, and clean scaffolding tool for Azure Functions in Python.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally.
3. Set up the development environment with `make install`.
4. Run `make check-all` to verify your initial setup passes all checks.

## Development Workflow

We follow a standard Git-based development workflow:

1. **Feature branch:** Create a new branch for your change (e.g., `git checkout -b feat/add-service-bus-trigger`).
2. **Implementation:** Write your code, following the project's style and quality standards.
3. **Tests:** Add or update tests to cover your changes. Run `make test` and `make cov` to verify.
4. **Quality gate:** Run `make check-all` before committing to ensure formatting, linting, and type checking pass.
5. **Commit:** Commit your changes using the Conventional Commits format (see below).
6. **Push and PR:** Push your branch to your fork and open a Pull Request against the `main` branch.

## Commit Message Conventions

We use Conventional Commits to automatically generate our changelog.

| Type | Description | Example |
| :--- | :--- | :--- |
| `feat` | A new feature | `feat: add cosmos-db trigger support` |
| `fix` | A bug fix | `fix: correct host.json path in scaffolder` |
| `docs` | Documentation changes | `docs: update contributing guide` |
| `style` | Formatting, missing semi-colons, etc. | `style: fix ruff formatting issues` |
| `refactor` | Code change that neither fixes a bug nor adds a feature | `refactor: simplify template resolution` |
| `test` | Adding missing tests or correcting existing tests | `test: increase coverage for generator.py` |
| `chore` | Changes to the build process or auxiliary tools | `chore: update bandit version` |

## Code Quality Standards

Maintain high quality by following these rules:

- **Style:** Code must pass `make lint` and `make format`.
- **Types:** All public functions and complex logic must have type hints that pass `make lint` (mypy strict mode).
- **Security:** Avoid insecure patterns. `make security` must pass.
- **Coverage:** New code must maintain or improve the overall test coverage. A minimum of **90% coverage** is required.
- **Language:** All code, comments, and documentation must be written in English.

## Template Change Guidelines

If you are modifying templates in `src/azure_functions_scaffold/templates/`, follow these verification steps:

1. Confirm the Jinja2 syntax is correct and follows our patterns.
2. Verify that the changes generate the expected file structure for a new project.
3. Run `make test` to ensure existing project generation tests still pass.
4. Manually generate a project with the new/updated template.
5. Verify the generated project can be initialized (e.g., `pip install -r requirements.txt`).
6. Confirm the generated code is valid Python and follows Azure Functions best practices.

## Pull Request Process

- Provide a clear title and description of the change in your PR.
- Reference any related issues (e.g., `fixes #123`).
- Ensure all CI checks (GitHub Actions) pass.
- A project maintainer will review your code. Address any requested changes.
- Once approved, the PR will be merged into the `main` branch.

## Code of Conduct

All contributors are expected to follow the project's Code of Conduct and treat others with respect and professionalism.
