# Contributing Guide

We welcome contributions to the `azure-functions-scaffold` project.

## Local development quickstart

Local development requires Python 3.11 through 3.14, matching the
`requires-python = ">=3.11,<3.15"` range in `pyproject.toml`. No Azure account,
Azure Functions Core Tools, Azurite, or Docker is required for the standard
repository checks.

Install Hatch once in an isolated tool environment. From a clone, create the
Hatch development environment:

```bash
make install
```

The `install` target creates the Hatch environment and installs the pre-commit
hook; routine targets never upgrade pip or reinstall Hatch. Then run the
standard verification commands:

```bash
make test
make lint
make typecheck
make build
```

## Branch Strategy

Use GitHub Flow and branch from `main`.

Recommended branch prefixes:

- `feat/` for new features
- `fix/` for bug fixes
- `docs/` for documentation-only changes
- `chore/` for tooling and maintenance
- `ci/` for workflow updates

## Development Workflow

1. Create a branch from `main`.
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feat/your-feature-name
   ```
2. Write code and tests.
3. Run the local quality gate.
   ```bash
   make check-all
   ```
4. Push and create a pull request.
   ```bash
   git push origin feat/your-feature-name
   ```

## Project Commands

| Command | Contract |
| --- | --- |
| `make install` | Idempotent Hatch development environment and hooks |
| `make install-ci` | Install dev/docs extras into CI's selected interpreter |
| `make doctor` | Read-only prerequisite check; nonzero for missing required tools |
| `make format` / `make format-check` | Explicit formatting mutation / read-only check |
| `make lint` / `make typecheck` / `make security` | Style plus strict types / strict types / Bandit |
| `make check` | Non-mutating formatting, lint, types once, security and workflow policy |
| `make test` | Offline generator/unit/structure suite; coverage >=95% |
| `make integration` | Ten isolated generated-project suites plus real generated HTTP host |
| `make verify` | Check, test, integration, installed-wheel smoke, build, strict docs |
| `make e2e-azure` | Explicit existing generated input and deployed HTTPS endpoint; no provisioning |
| `make report` | Display saved evidence only; never run tests |
| `make clean` | Remove generated artifacts; preserve environments and shared/cloud resources |

`make check-all` is an exact alias of `make verify`. `make clean-all` retains
historical deep cleanup, including `.venv` and bytecode. `cov`, `generated-project`,
`host-smoke`, `wheel-smoke`, `build`, `docs` and individual quality targets are
focused **PARTIAL** evidence, not full verification. `e2e-local` runs host smoke,
not Azure certification. Local commands use Hatch's Python 3.11; CI uses the
selected matrix interpreter directly (`CI=1`, optionally `PYTHON=/path/to/python`).

### Generated projects and diagnostics policy

`tools/verification_manifest.py` declares the ten templates and test families.
Every strict template must collect and execute at least one generated pytest case.
There are **no no-tests exceptions**: pytest exit 5 is a failure. Zero execution,
all-skipped or unexpected skips never PASS. The offline suite allows only the two
existing historical-migration documentation skips, by test identity and reason.

The runner builds a scaffold wheel (or uses explicit `VERIFICATION_WHEEL`), installs
it into an isolated venv outside the checkout, checks imported package/version
identity, and generates through that installed CLI. Each generated project gets
its own isolated venv, SDK resolution, compile/lint/type/test and diagnostics run.
No scaffolder source-tree imports are added to these environments.

Doctor uses `doctor --format json` directly, never GNU Make's remapped exit status
or human summary text. The stable required-rule allowlist is
`check_python_version` (environment), `check_requirements_txt` and
`check_azure_functions_library` (dependencies), and `check_host_json` and
`check_host_json_version` (structure). Failed/skipped required conditions block;
normal warnings and non-required recommendations are ADVISORY, including subjective
configuration recommendations. Exit 2 is CLI_ERROR; other abnormal exits or
missing/malformed JSON are CRASH. Both block. Required findings block regardless
of a changed display severity. New required categories need an explicit policy update.

Every required rule identity must appear; an incomplete report never becomes diagnostic
PASS. One temporary **diagnostics-only** exemption is declared in the manifest:
generated `langgraph`, owner `yeongseon`, expires **2026-11-23 (UTC, exclusive)**,
[Doctor #590](https://github.com/yeongseon/azure-functions-doctor-python/issues/590).
Released Doctor **0.23.1** short-circuits on `func_app = lg_app.function_app` even
though this exports a real SDK FunctionApp. Only exit 1 with the exact single
`check_programming_model_v2` error and `programming_model=unknown` matches.
The runner still executes Doctor and records a separate `diagnostics/summary.json`
as **INCOMPLETE**, `required=false`, preserving its exit 1, owner, reason, expiry,
version and issue link. The generated-project summary carries
`diagnostics_status=INCOMPLETE`; its PASS refers only to the remaining required
checks, not complete diagnostic certification. Structure, compile, lint, types,
positive generated pytest, and an imported SDK FunctionApp export with registered
functions remain blocking. Other templates, malformed reports, other tool versions,
new failures and expiry receive no exemption. A complete report is classified normally.
Remove this entry after a released Doctor fixes detection; never renew automatically.

`func` and `azurite` are required for integration/verify, not check/test. Doctor
reports these prerequisites without installing anything. Host smoke uses unique
loopback ports, temporary emulator storage and run-owned process groups; teardown
terminates only its own children on success, failure, timeout or interruption.
The generated HTTP health route must index, return 200 and contain `status=ok`.

### Saved evidence and Azure

Gitignored `test-results/` stores offline `test/{junit.xml,coverage.xml,summary.json}`,
per-template integration JUnit/logs, separate host and wheel evidence,
`verify/{summary.json,environment.json,lanes.json}`, and separate Azure generation
and remote phase reports. Schema-versioned summaries include command/lane,
required flag, scope, selected/passed/failed/skipped counts, exit status and artifact
paths. Per-template evidence records generated Python, SDK, scaffold version,
wheel SHA-256 and generated file digest. Environment evidence records Python,
package versions and source commit. Secrets/connection strings are redacted from
logs, JUnit, JSON, console and Actions Job Summary; CI uploads evidence with
`if: always()` on failure as well as success.

Statuses are PASS, FAIL, INCOMPLETE and NOT_APPLICABLE. Missing prerequisites or
unexecuted required checks are INCOMPLETE/nonzero, never NOT_APPLICABLE; failed
processes/tests are FAIL. NOT_APPLICABLE is reserved for explicitly unsupported
lanes. Generator success does not prove a host or a deployed Azure app.

Azure preflight requires `E2E_SCAFFOLDED_DIR`, `E2E_BASE_URL` (HTTPS),
`E2E_EXPECTED_VERSION` and `VERIFICATION_WHEEL`. Missing inputs fail **before tests**.
Both generated-input and remote-HTTP phases must execute positive, no-skip suites.
There is no deployed package-version endpoint: `deployed_artifact_identity` remains
INCOMPLETE and the release workflow owns deployment provenance. Local host smoke
does not certify Azure. The existing OIDC deployment/release chain is unchanged.

Before opening a PR, run `ruff format --check <changed-python-files>` (or
`ruff format <changed-python-files>` to fix them). `make format-check` checks
`src` and `tests` without changing files. CI checks those same trees and also
reports formatting failures on changed Python files in a dedicated step.

## GitHub Actions Pinning

All external `uses:` references in `.github/workflows/` MUST pin to a
full 40-character commit SHA with a trailing comment documenting the
released version or channel. Example:

```yaml
- uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6
```

This applies to first-party (`actions/*`, `github/*`, `azure/*`) and
third-party Actions alike.

**Rationale.** Mutable tags (including immutable-looking version tags
like `@v6.0.1`) can be retroactively moved by an attacker who gains
write access to the upstream repository. The
[`tj-actions/changed-files` compromise (CVE-2025-30066, March 2025)](https://github.com/advisories/GHSA-mrrh-fwg8-r2c3)
demonstrated this exact failure mode: ~23,000 repositories had their CI
secrets exfiltrated, and only workflows that pinned to a commit SHA were
safe. GitHub's own guidance now identifies SHA pinning as
[the only way to use an Action as an immutable release](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#using-third-party-actions),
and OpenSSF Scorecard's
[`Pinned-Dependencies` check](https://github.com/ossf/scorecard/blob/main/docs/checks.md#pinned-dependencies)
flags anything weaker as Medium-risk.

Dependabot updates SHA-pinned references on the configured schedule and
keeps the trailing version comment in sync, so the human-readable
context never drifts from the pinned commit.

**Approved exceptions.** The following mutable refs are the only ones
permitted in this repository and are flagged with an inline comment at
the call site:

- Local composite actions (`uses: ./...`) — versioned with the repo.

When adding a new external Action, resolve the SHA with
`git ls-remote <repo-url> 'refs/tags/<tag>^{}'`. The trailing `^{}`
**dereferences** the ref to its target commit; without it, an
*annotated* tag returns the tag-object SHA instead of the commit SHA,
and the tag-object SHA is **not** a valid `uses:` target.

```bash
# Annotated tag — the two forms return *different* SHAs:
git ls-remote https://github.com/Azure/login 'refs/tags/v3.0.0' 'refs/tags/v3.0.0^{}'
# 93381592...   refs/tags/v3.0.0       <- tag object, do NOT pin to this
# 532459ea...   refs/tags/v3.0.0^{}    <- commit, pin to this one

# Lightweight tag — only the non-deref form returns a row, and it is
# already the commit SHA. Always include the `^{}` form anyway so the
# same command works for both tag types:
git ls-remote https://github.com/actions/setup-python 'refs/tags/v6' 'refs/tags/v6^{}'
```

Single-quote the `refs/...^{}` argument so the `{}` and `^` are not
interpreted by your shell (notably zsh with `EXTENDED_GLOB`).

## Example Coverage Policy

Examples are part of the supported API experience and should stay verified.

- Keep one representative example for the minimal scaffolding workflow.
- Keep one complex example for custom templates and multi-project generation.
- Add or update smoke tests whenever an example changes.
- Prefer lightweight smoke coverage over infrastructure-heavy end-to-end tests.

## Issue Scope

When opening or editing an issue, follow the
[Issue Conventions in AGENTS.md](AGENTS.md#issue-conventions), including the
repository-scope checks. Describe this repository's problem and acceptance
criteria, and explain why any external repository reference is relevant.

## Title Convention

This section is the single source of truth for issue, pull request, and commit titles in this repository. `AGENTS.md`, the pull request template, the issue forms, and the documentation site point here instead of restating the rules.

Issues, pull requests, and the final squash commit on the default branch all use:

```text
type: description
type(scope): description
```

- Write titles in English.
- `type` and `scope` are lowercase. Put exactly one space after the colon.
- `scope` is optional. Add it only when it narrows the area; do not add one just for uniformity.
- `description` states what changes and why, concisely. Start with a lowercase word, but keep the spelling of API names, acronyms, error codes, and proper nouns.
- No trailing period.
- No priority, size, status, or owner markers, and no bracket prefixes such as `[Bug]`, `[Feature]`, or `[WIP]`. Use labels and Draft pull requests instead.
- An issue title may describe the problem; the pull request title describes the change that resolves it. Keep them aligned when they cover the same work, without forcing identical wording when the scope differs.
- Do not put issue numbers in pull request titles. Link issues in the pull request body with `Closes #123` or `Refs #123`.

| type | use for |
|---|---|
| `feat` | a user-facing feature or capability |
| `fix` | a bug fix in product behavior |
| `docs` | documentation only |
| `test` | adding or changing tests |
| `perf` | a performance improvement |
| `refactor` | internal restructuring that keeps external behavior |
| `ci` | CI and automation workflows |
| `build` | build, packaging, and dependency changes |
| `chore` | maintenance that fits none of the above |
| `style` | formatting only, no behavior change |
| `revert` | reverting an earlier change |

A breaking change adds `!` before the colon: `type!: description` or `type(scope)!: description`. Whether a change is breaking, and how it is released, is decided by the Release Process in [AGENTS.md](AGENTS.md), not by the title alone. Release Please reads these titles from the squash commits on `main`: `fix` and `feat` drive the version bump, and the other types only shape the changelog.

Examples:

```text
fix: reject an existing output directory
feat(cli): add a JSON output option
docs(readme): clarify the local setup steps
refactor!: rename the public configuration keys
```

Not accepted: `[Bug] crash on save` (bracket prefix, no type), `Fix: crash on save` (uppercase type), `feature: add export` (type not in the table), `fix: crash on save.` (trailing period), `fix: reject an existing output directory (#503)` (the pull request number belongs in the body).

Pull requests are squash-merged and the pull request title becomes the final commit title. GitHub appends the pull request number by itself, so `fix: reject an existing output directory` lands on `main` as `fix: reject an existing output directory (#503)`. Do not write that number into the title yourself — the check rejects a title ending in `(#123)`, because it would be doubled. Link the issue from the pull request body instead, for example `Closes #503`. The **PR title** check validates the format whenever a pull request is opened, edited, reopened, or updated. Individual commits on a branch are not checked.

Issue titles are not enforced. Anyone can open an issue without knowing this convention; maintainers adjust the title during triage.

## Releases

Merging to `main` does not publish a release.

Release Please keeps an open **Release PR** showing what the next version would
be; merging that PR is what cuts the release, and it is what creates the `v*`
tag that starts the publish workflow. Publishing happens only after the release
verification requirements have been satisfied. Contributors never need to bump a
version or tag anything in an ordinary pull request.


See `AGENTS.md` for the maintainer-only release procedure.

## Code of Conduct

Be respectful and inclusive. See our [Code of Conduct](CODE_OF_CONDUCT.md) for details.
