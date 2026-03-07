# AGENTS.md

## Purpose

This repository is intended to be worked on with agentic coding workflows.

## Canonical Documents

Read these first, in this order:

1. `README.md`
2. `PRD.md`
3. `ARCH.md`
4. `docs/CLI.md`
5. `docs/TEMPLATE_SPEC.md`
6. `docs/STYLE_GUIDE.md`
7. `docs/ROADMAP.md`
8. `CONTRIBUTING.md`

## Working Rules

- Treat `PRD.md` as the product source of truth.
- Treat `ARCH.md` as the implementation and structure source of truth.
- Treat `DESIGN.md` as the design guardrail document.
- Do not claim support for features that are not implemented.
- Write all documentation and code comments in English.
- Keep generated scaffold output lint-clean, format-clean, and testable.
- Keep repository coverage at or above 90 percent.
- When changing CLI behavior, update tests and user-facing docs.
- When changing templates, validate both repo checks and generated-project checks.

## Architecture Rules

- The CLI must be implemented with Typer.
- Templates must be rendered with Jinja2.
- All generated code must pass Ruff.
- The Python version target is 3.10+.

## Code Modification Rules

- Never break existing CLI commands.
- Always update tests when modifying code.
- Use `Makefile` commands as the primary entry point for local development workflows.

## Golden Commands

- `make install`
- `make format`
- `make lint`
- `make test`
- `make check`
- `make check-all`
- `make build`

## Current Product Scope

Implemented:

- `azure-functions-scaffold new <project-name>`
- default HTTP scaffold
- Jinja2-based embedded templates

Not yet implemented:

- multiple scaffold templates
- interactive setup
- `add trigger`
- `doctor`

## Verification

Repository checks:

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

If local pytest plugins interfere:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest
```

For template changes, also validate a generated project with the same checks.
