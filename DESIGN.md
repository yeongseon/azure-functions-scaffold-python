# DESIGN.md

## Purpose

This document defines the design philosophy of `azure-functions-scaffold`.

It exists to:

- keep the CLI predictable
- prevent accidental template bloat
- keep generated projects easy to understand and maintain
- provide guardrails for AI-assisted development

## Goals

- provide a small, reliable CLI for bootstrapping Azure Functions Python projects
- favor explicit scaffolding over hidden automation
- generate code that is easy to edit by hand after scaffolding
- keep the initial template close to normal Python application structure

## Anti-Goals

This project does not aim to:

- become a full application framework
- hide Azure Functions runtime concepts
- generate highly dynamic or "magic" project structures
- force large opinion bundles into every generated app

## CLI Design Principles

- commands stay small and obvious
- output paths and side effects must be explicit
- error messages should be short and actionable
- existing CLI behavior should remain stable unless there is a strong reason to change it

## Template Design Principles

- generated files must be readable without extra tooling
- trigger code and business logic should be separated
- project defaults should be production-leaning, not tutorial-only
- generated code must pass Ruff and tests

## Compatibility Policy

- minimum supported Python version: 3.10
- development may use newer Python versions
- generated runtime code must stay compatible with Python 3.10+

## Change Discipline

- prefer additive changes over breaking changes
- keep templates deterministic
- if a template behavior changes, update tests and docs in the same change

