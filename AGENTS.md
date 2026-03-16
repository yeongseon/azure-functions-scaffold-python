# AGENTS.md

## Purpose
`azure-functions-scaffold` is a CLI and library for scaffolding production-ready Azure Functions Python v2 projects.

## Read First
- `README.md`
- `CONTRIBUTING.md`
- `AGENT.md`
- `docs/agent-playbook.md`

## Working Rules
- Treat `AGENT.md` as the existing repository contract and keep this file aligned with it.
- Runtime code must remain compatible with Python 3.10+.
- Public APIs must be fully typed.
- When changing CLI behaviour or generated template output, update docs, examples, and tests in the same change.
- Keep repository structure aligned with sibling azure-functions-* repositories.
- `make check-all` is the minimum merge gate.

## Validation
- `make test`
- `make lint`
- `make typecheck`
- `make build`
