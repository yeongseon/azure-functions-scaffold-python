# FAQ

Answers to common questions about `azure-functions-scaffold` and generated
projects.

## What templates are available?

Five templates are built in:

- `http`
- `timer`
- `queue`
- `blob`
- `servicebus`

You can list them at any time:

```bash
afs templates
```

See [Templates](guide/templates.md) for behavior and use cases.

## How do I add custom templates?

The CLI ships with bundled templates and does not currently provide a runtime
plugin command for external template packs.

If you need custom templates today:

1. Fork or clone the project source.
2. Add a new folder under `src/azure_functions_scaffold/templates/`.
3. Register it in `src/azure_functions_scaffold/template_registry.py`.
4. Add tests for generation and `afs add` behavior.

See [Template Specification](reference/template-spec.md) for format rules.

!!! tip "Team strategy"
    If your organization needs opinionated internal templates, maintain a pinned
    internal fork and version it like any other developer platform tool.

## What is the difference between presets?

Presets control quality tooling in generated project configuration.

| Preset | Tooling | Best for |
| :--- | :--- | :--- |
| `minimal` | none | Prototypes, very small scripts |
| `standard` | `ruff`, `pytest` | Most projects (default) |
| `strict` | `ruff`, `mypy`, `pytest` | Type-safe, team-scale APIs |

List presets from CLI:

```bash
afs presets
```

## Can I use it without Azure Functions Core Tools?

Yes for scaffolding, no for local runtime and deployment.

- You can generate files with `afs new` and `afs add` without Core Tools.
- You need Core Tools (`func`) to run `func start` locally.
- You typically need Core Tools for `func azure functionapp publish ...`.

## How do I add features after project creation?

Feature flags are generation-time options. There is no separate command like
`afs features enable ...` today.

Practical options:

1. Regenerate with desired flags and port business code.
2. Manually add equivalent dependencies and code wiring.

Examples:

- OpenAPI requires route handlers in `function_app.py` and OpenAPI decorators.
- Validation requires `azure-functions-validation`, request/response models, and
  validated endpoint signatures.
- Doctor requires dependency plus command invocation (for example `make doctor`).

See [Configuration](guide/configuration.md) for flag behavior.

## What are the project naming rules?

Project names must:

- be non-empty
- start with a letter or number
- contain only letters, numbers, hyphens, or underscores

Valid examples:

- `my-api`
- `orders_v2`
- `api2026`

Invalid examples:

- `my api`
- `_api`
- `api!`

## Does it create tests?

Yes when pytest tooling is enabled.

- `standard` and `strict` presets include pytest and generate tests.
- `minimal` preset does not include pytest by default.

When adding functions with `afs add`, test files are created if a `tests/`
directory exists in the project.

## Does `afs` differ from `azure-functions-scaffold`?

No. `afs` is a short alias and a drop-in replacement.

These are equivalent:

```bash
afs new my-api
azure-functions-scaffold new my-api
```

## Can I preview changes before writing files?

Yes. Use `--dry-run` on both project creation and add flows.

```bash
afs new my-api --preset strict --dry-run
afs add queue process_orders --project-root ./my-api --dry-run
```

## Where should I start next?

- [Getting Started](guide/getting-started.md)
- [Configuration](guide/configuration.md)
- [HTTP API Example](examples/http_api.md)
- [Troubleshooting](guide/troubleshooting.md)

## Why is `orjson` included in generated projects?

All scaffolded projects include [`orjson`](https://github.com/ijl/orjson) as a
default dependency. The Azure Functions Python worker
[automatically detects orjson](https://techcommunity.microsoft.com/blog/appsonazureblog/scaling-azure-functions-python-with-orjson/4445780)
when it is installed and uses it for JSON serialization and deserialization —
no code changes required.

Benchmarks from Microsoft show up to **40% lower HTTP response times** and
significantly higher throughput for Service Bus and Event Hub triggers. Since
`orjson` provides pre-built wheels for all platforms Azure Functions supports,
it adds negligible install overhead for a meaningful performance gain.
