# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.3.2] - 2026-03-21

### Added

- Real Azure end-to-end test workflow (`e2e-azure.yml`) deploying to Consumption plan (`koreacentral`)
- `docs/testing.md` — Real Azure E2E Tests section
- EventHub, CosmosDB, Durable, and AI scaffold templates
- Mermaid diagrams to architecture and README
- Generator coverage tests

### Changed

- GitHub Actions versions upgraded to Node.js 24 compatible versions
- Repository consistency fixes (LICENSE, .gitignore standardization)

### Fixed

- Generate `requirements.txt` from `pyproject.toml` before `func publish`, add startup probe
- Fix scaffold e2e warmup route, pyproject.toml check, cleanup resilience
- Fix e2e workflow to use correct scaffold CLI `new` command

## [0.3.1] - 2026-03-14

### Added

- Unified tooling: Ruff (lint + format), pre-commit hooks, standardized Makefile
- Comprehensive documentation overhaul (MkDocs site with standardized nav)
- Translated README files (Korean, Japanese, Chinese)
- Standardized documentation quality across ecosystem

## [0.3.0] - 2026-03-12

### Added

- `--with-doctor` / `--no-doctor` flag for `new` command to include `azure-functions-doctor` health checks
- Interactive prompt for doctor inclusion
- Conditional `make doctor` target in generated Makefile when doctor is enabled
- `azure-functions-logging>=0.2.0` as default dependency across all templates
- Structured JSON logging via `setup_logging(format="json")` and `get_logger()` in generated `logging.py`
- Non-HTTP function templates now use `logging.info()` instead of `print()`
- Dry-run output reports "Doctor: enabled" when `--with-doctor` is set
- New test coverage for doctor flag, dry-run, and logging dependency

### Changed

- Generated `logging.py` replaced `basicConfig` stub with `azure-functions-logging` integration
- Queue, blob, and Service Bus function templates use lazy `%s` format strings for logging
## [0.2.0] - 2026-03-12

### Added

- `--with-openapi` / `--no-openapi` flag for `new` command (HTTP template only)
- `--with-validation` / `--no-validation` flag for `new` command (HTTP template only)
- Interactive prompts for OpenAPI and validation inclusion
- Conditional Jinja2 templates for openapi endpoints, validation decorators, and Pydantic models
- Dry-run output reports "OpenAPI: enabled" and "Validation: enabled" when flags are set
- New test coverage for all openapi/validation flag combinations

## [0.1.0] - 2026-03-08

### Added

- Interactive `new` command for Azure Functions Python v2 projects
- Presets for `minimal`, `standard`, and `strict` project layouts
- Optional tooling selection for Ruff, mypy, and pytest during interactive setup
- `add http`, `add timer`, `add queue`, `add blob`, and `add servicebus` commands for generating new functions
- Queue, blob, and Service Bus trigger templates for project scaffolding
- Template-driven project generation for `pyproject.toml`, `Makefile`, CI, and README files
- Project documentation, release notes, and template specification guidance
