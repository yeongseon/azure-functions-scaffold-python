# Roadmap

## Phase 1: MVP

Status: implemented

Delivered:

- `new` command
- embedded HTTP scaffold
- Jinja2-based rendering
- repository tests for CLI behavior
- generated project quality baseline with `pytest` and `ruff`

## Phase 2: Guided Scaffolding

Status: implemented

Delivered:

- interactive project setup
- `minimal`, `standard`, and `strict` presets
- richer template context for Python version and tooling choices
- optional generated GitHub Actions CI workflow
- optional git initialization

## Phase 3: Post-Generation Expansion

Status: partially implemented

Delivered:

- `add http <function-name>`
- `add timer <function-name>`
- automatic `function_app.py` registration updates

Planned:

- queue trigger generation
- Service Bus trigger generation
- blob trigger generation

## Phase 4: Template Expansion

Planned:

- timer-focused project template
- queue-focused project template
- richer project structure variants

## Phase 5: CLI Expansion

Planned:

- dry-run mode
- overwrite protections with clearer UX
- finer interactive tooling selection beyond presets

## Phase 6: Product Expansion

Potential:

- CI/CD starter files
- OpenAPI-ready HTTP variants
- validation-oriented project variants

## Out of Scope for Near Term

- telemetry frameworks
- tracing abstractions
- runtime middleware ecosystems
- large Azure SDK opinion bundles

