# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
