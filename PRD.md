# PRD - azure-functions-scaffold

## Overview

`azure-functions-scaffold` is a scaffolding CLI for creating production-leaning Azure Functions
Python v2 projects.

It generates a clean project structure with testing, linting, and packaging defaults that are
better suited to real Python teams than the minimal starter templates from Azure Functions Core Tools.

## Problem Statement

The default Azure Functions initialization flow is useful for learning, but often leaves teams to
fill in the same missing pieces repeatedly:

- project structure conventions
- linting and formatting configuration
- test setup
- application layer separation
- maintainable `pyproject.toml` defaults

Without a scaffold, each team reinvents these decisions and quality drifts across repositories.

## Goals

- Generate Azure Functions Python v2 projects with clear, maintainable defaults.
- Align scaffolded output with modern Python packaging and quality tooling.
- Keep the CLI small and explicit.
- Produce generated projects that are easy to extend by hand.
- Support interactive bootstrap for first-time project creation.
- Support opinionated presets that reduce repeated CLI decisions.
- Support adding new function modules after initial project creation.

## Non-Goals

- Replacing Azure Functions runtime concepts
- Building a general-purpose application framework
- Supporting the legacy `function.json`-based Python v1 model
- Managing deployment or infrastructure

## Primary Users

- Python developers bootstrapping Azure Functions services
- Teams that want repeatable repository structure
- Maintainers building consistent Azure Functions project foundations

## Core Use Cases

- Create a new HTTP-trigger Azure Functions project from a single command
- Create queue-, blob-, and Service Bus-trigger projects for local-first development
- Create a new project interactively without memorizing flags
- Choose between `minimal`, `standard`, and `strict` presets
- Generate project files that already include tests and linting defaults
- Add new HTTP, timer, queue, blob, and Service Bus functions to an existing scaffolded codebase
- Standardize project layout across repositories

## Success Criteria

- Generated projects pass their own lint and test checks
- Representative scaffold output remains smoke-tested in CI
- The CLI stays simple enough to understand without external scaffolding systems
