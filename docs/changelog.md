# Changelog

All notable changes to the `azure-functions-scaffold` project are documented on this page. This project adheres to Semantic Versioning and maintains a structured history of updates, features, and bug fixes.

## Versioning Scheme

This project follows [Semantic Versioning (SemVer)](https://semver.org/). Version numbers are assigned using the `MAJOR.MINOR.PATCH` format:

- **MAJOR**: Breaking changes that require user intervention or migration.
- **MINOR**: New features or significant enhancements that are backwards compatible.
- **PATCH**: Backwards compatible bug fixes and maintenance updates.

The changelog is generated from [Conventional Commits](https://www.conventionalcommits.org/) using `git-cliff`. Breaking changes are explicitly highlighted in the release notes.

## Full Version History

### v0.3.1 (2026-03-14)

This release captures the tooling unification and documentation overhaul applied across the ecosystem.

#### Added
- Unified tooling: Ruff (lint + format), pre-commit hooks, standardized Makefile
- Comprehensive documentation overhaul (MkDocs site with standardized nav)
- Translated README files (Korean, Japanese, Chinese)
- Standardized documentation quality across ecosystem

### v0.3.0 (2026-03-12)

This release introduces health check integration and enhanced structured logging capabilities across all project templates.

#### Added
- Introduced `--with-doctor` and `--no-doctor` flags for the `new` command to include `azure-functions-doctor` health checks in scaffolded projects.
- Added an interactive prompt to choose whether to include the doctor health check tool during project setup.
- Implemented a conditional `make doctor` target in the generated `Makefile` when the doctor flag is enabled.
- Set `azure-functions-logging>=0.2.0` as a default dependency for all generated project templates.
- Added structured JSON logging support via `setup_logging(format="json")` and `get_logger()` in the generated `logging.py` file.
- Updated non-HTTP function templates to use `logging.info()` instead of `print()` for better production readiness.
- Added a dry-run report status for the doctor tool, showing "Doctor: enabled" when requested.
- Expanded test coverage to include the doctor flag, dry-run output verification, and logging dependency management.

#### Changed
- Refactored the generated `logging.py` to replace the basic `basicConfig` stub with full `azure-functions-logging` integration.
- Updated Queue, Blob, and Service Bus function templates to use lazy `%s` format strings for more efficient logging.

### v0.2.0 (2026-03-12)

This update focuses on the HTTP template, adding optional support for OpenAPI documentation and automated request/target validation.

#### Added
- Added `--with-openapi` and `--no-openapi` flags for the `new` command, specifically for HTTP project templates.
- Added `--with-validation` and `--no-validation` flags for the `new` command to enable request and response validation.
- Included interactive prompts for both OpenAPI and validation features during the `new` command execution.
- Implemented conditional Jinja2 templates to generate OpenAPI endpoints, validation decorators, and Pydantic models only when requested.
- Updated dry-run output to report "OpenAPI: enabled" and "Validation: enabled" based on the provided flags.
- Added comprehensive test coverage for all combinations of OpenAPI and validation flags.

### v0.1.0 (2026-03-08)

The initial release of the `azure-functions-scaffold` CLI, providing a robust foundation for building Azure Functions Python v2 projects.

#### Added
- Launched the interactive `new` command for bootstrapping Azure Functions Python v2 projects with ease.
- Introduced project presets (`minimal`, `standard`, and `strict`) to cater to different project complexity needs.
- Added optional tooling selection for `Ruff`, `mypy`, and `pytest` during the interactive setup process.
- Implemented the `add` command with support for `http`, `timer`, `queue`, `blob`, and `servicebus` triggers.
- Provided specialized trigger templates for Queue, Blob, and Service Bus functions.
- Enabled template-driven generation for core project files, including `pyproject.toml`, `Makefile`, CI configurations, and `README.md`.
- Established initial project documentation, release notes structure, and template specification guidance.
