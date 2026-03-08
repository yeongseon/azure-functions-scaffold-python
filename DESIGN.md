# DESIGN.md

Design Principles for `azure-functions-scaffold`

## Purpose

This document defines the architectural boundaries and design principles of the project.

## Design Goals

- Scaffold Azure Functions Python v2 projects with explicit, maintainable defaults.
- Keep the CLI predictable and easy to understand.
- Generate projects that are immediately testable and lint-clean.
- Stay aligned with the wider Azure Functions Python tooling ecosystem.

## Non-Goals

This project does not aim to:

- Become a full application framework
- Hide Azure Functions runtime concepts
- Generate overly dynamic or highly magical project structures
- Own deployment, infrastructure, or runtime operations

## Design Principles

- The CLI should stay small and obvious.
- Template output should be deterministic.
- Generated code should remain easy to edit by hand.
- Trigger entrypoints and service logic should stay separated.
- Public CLI behavior should evolve conservatively.

## Integration Boundaries

- Runtime validation belongs to `azure-functions-validation`.
- OpenAPI generation belongs to `azure-functions-openapi`.
- Project diagnostics belong to `azure-functions-doctor`.
- This repository owns project generation, template rendering, and scaffold defaults.

## Compatibility Policy

- Minimum supported Python version: `3.10`
- Supported runtime target: Azure Functions Python v2 programming model
- Public APIs and CLI behavior follow semantic versioning expectations

## Change Discipline

- Template behavior changes require tests and docs updates.
- Generated-project quality gates are user-facing behavior.
- Experimental templates or commands must be clearly labeled in code and docs.
