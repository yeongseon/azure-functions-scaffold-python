# Security Policy

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability, please report it
responsibly and avoid public disclosure until a fix is available.

### Preferred: GitHub Security Advisory

1. Go to the [Security Advisories page](https://github.com/yeongseon/azure-functions-scaffold-python/security/advisories/new)
2. Click "Report a vulnerability"
3. Submit the details in the private advisory

### Alternative: Email

If you prefer email, contact: yeongseon.choe@gmail.com

### What to Include

* A clear description of the issue
* Steps to reproduce
* Impact assessment
* Suggested mitigation or fix, if available

### Response Timeline

* Initial response: within 48 hours
* Status update: within 7 days

## Supported Versions

| Version | Supported |
| ------- | --------- |
| Latest release | :white_check_mark: |
| Older releases | :x: |

## Scan paths and gates

Pull-request/main security jobs retain Bandit and the SHA-pinned Semgrep action.
Bandit evidence inventories Python in `src/`, `tools/`, `docs_hooks/`, and `ci/`,
including exact reviewed inline suppressions. The rendered-security job generates
all ten templates across all three presets, including optional supported features,
and the AI partial; Bandit scans the actual generated application Python.
Generated test files are excluded from Bandit (pytest assertions are intentional),
but remain exercised by generated-project pytest. Workflow permissions and action
pins are checked separately. No Bicep is emitted by the current templates; zero
Bicep is explicitly reported, not claimed as infrastructure certification.
CodeQL and SPDX SBOM generation remain separate unchanged workflows.

The release `runtime-dependency-audit` job downloads the exact `build` wheel,
installs it in an isolated environment on Python 3.11–3.14, and uses pip-audit
2.10.1. There are no runtime extras (`dev` and `docs` are not runtime closures).
All known runtime advisories block, including unknown/low severity, unless a
current exact exception applies. `publish` needs this job as well as the existing
verification and real-Azure certification jobs; OIDC and artifact reuse are unchanged.
Scheduled/manual dependency audits are reporting-only, with separate runtime and
development results. A reporting-only job is not release authorization.

## Evidence and exceptions

`security-results/**` contains allow-listed IDs, relative paths, lines, severities,
counts, tool versions and outcomes. Raw source, scanner messages, request input,
credentials, environment values, connection strings and advisory descriptions are
discarded. Job Summaries and uploads run even after failures. Semgrep evidence
records the action outcome only; its finding count is unknown.

`FAIL` means a policy violation/finding; `TOOL_ERROR` means execution or evidence
cannot be trusted; `INCOMPLETE` means scope/outputs are missing or skipped. All
three block release/static gates; empty Python scans never pass. Recovery after a
transient tool failure is `gh workflow run publish-pypi.yml --ref vX.Y.Z` on the
same unchanged tag. Code corrections require a new release, never a moved tag.

Exceptions in `security/*.json` require a maintainer-reviewed exact advisory/package
or rule/file/line, kind, reason, owner, added date and expiry at most 90 days later.
Expired exceptions fail. Blanket suppressions and unreviewed generated suppressions
are rejected. Re-review exceptions when tools or source locations change; do not
renew automatically. No runtime advisory exceptions are installed by default.

## Generated application threat model

Untrusted HTTP callers, webhook senders, model inputs, filesystem destinations and
dependency registries are trust boundaries. The scaffolder is not a runtime security
gateway: operators must configure identity, quotas, secret storage and deployment
network policies. New LangGraph projects use FUNCTION authentication; only the
generated-project setting `LANGGRAPH_PUBLIC_DEMO=true` opts into public execution
with a startup WARNING. Core Tools local mode does not enforce function keys.
Keys are application access control, not user identity or thread authorization;
consult the runtime library's `ThreadAuthorizer` documentation separately.

HTTP liveness is intentionally anonymous and minimal. Optional OpenAPI/docs routes
are intentionally public local/demo examples: disable or restrict them in production.
Webhooks require a function key in Azure plus HMAC-SHA256, constant-time comparison,
and a 1 MiB application body limit before verification/parsing. The host/proxy must
also bound bodies before buffering. HMAC alone does not stop replay: implement
provider-signed timestamps, freshness windows and durable delivery-ID deduplication.
The in-memory store is local demonstration storage, not durable replay prevention.
AI endpoint logs contain sizes only, not prompts/completions; SDK debug tracing
must be reviewed separately. Configure API/model quotas, concurrency and token
limits, rate limiting, budgets and cost alerts before exposing billable endpoints.

These output changes affect newly generated projects only. We consider changing
anonymous graph execution to FUNCTION a deployment compatibility change warranting
explicit release review; the maintainer decides versioning. No CLI/API change or
automatic migration of existing projects is introduced.
