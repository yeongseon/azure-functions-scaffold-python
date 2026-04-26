# AGENTS.md

## Purpose
`azure-functions-scaffold-python` is a CLI and library for scaffolding production-ready Azure Functions Python v2 projects.

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

## Issue Conventions

Follow these conventions when opening issues so the backlog stays consistent with sibling DX Toolkit repositories.

### Title

- Use Conventional Commit prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `ci:`, `build:`, `perf:`.
- Add a scope qualifier when it narrows the area: `feat(template):`, `docs(cli):`, `refactor(generator):`.
- Keep the title imperative, under ~80 characters, no trailing period.
- Do **not** put `[P0]` / `[P1]` / `[P2]` (or any priority marker) in the title — priority lives in the body.

### Body

Use the following sections, in order, omitting any that do not apply:

```
## Priority: P0 | P1 | P2 (target vX.Y.Z, optional)

## Context
What problem this issue addresses and why now.

## Acceptance Checklist
- [ ] Concrete, verifiable items.

## Out of scope
- Items intentionally excluded, with links to the issues that track them.

## References
- PRs, ADRs, sibling issues, external docs.
```

### Labels

- Apply at least one of `bug`, `enhancement`, `documentation`, `chore`.
- Add `area:*` labels when they exist in the repository.
- Use `blocker` only when the issue blocks a release.

### Umbrella issues

When splitting a large piece of work into focused issues, keep the umbrella open as a tracker that links each child issue with a checkbox; close it once every child is closed or explicitly deferred.

## Validation
- `make test`
- `make lint`
- `make typecheck`
- `make build`
