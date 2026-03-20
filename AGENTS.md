# AGENTS.md

## Purpose
`azure-functions-scaffold` is a CLI and library for scaffolding production-ready Azure Functions Python v2 projects.

## Read First
- `README.md`
- `CONTRIBUTING.md`

## Working Rules
- Keep repository-level engineering and planning docs at the repository root (`AGENTS.md`, `DESIGN.md`, `PRD.md`).
- Keep `docs/` for user-facing documentation only.
- Use Makefile entry points for contributor guidance and CI (`make install`, `make format`, `make lint`, `make typecheck`, `make test`, `make cov`, `make check-all`, `make docs`, `make build`).
- Runtime code must remain compatible with Python 3.10+.
- Public APIs must be fully typed.
- Avoid silent behavior changes; document and discuss breaking changes before release.
- When changing CLI behaviour or generated template output, update docs, examples, and tests in the same change.
- Keep repository structure aligned with sibling azure-functions-* repositories.
- `make check-all` is the minimum merge gate.
- Use Conventional Commits with allowed types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`.

## Validation
- `make test`
- `make lint`
- `make typecheck`
- `make build`
