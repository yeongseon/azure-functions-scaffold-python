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
all ten templates across all three presets with optional features both enabled and disabled
(60 projects), including dataclass/Pydantic schemas and both webhook handlers,
and the AI partial; Bandit scans the actual generated application Python.
Generated test files are excluded from Bandit (pytest assertions are intentional),
but remain exercised by generated-project pytest. Workflow permissions and action
pins are checked separately. No Bicep is emitted by the current templates; zero
Bicep is explicitly reported, not claimed as infrastructure certification.
CodeQL and SPDX SBOM generation remain separate unchanged workflows.

The release `runtime-dependency-audit` job downloads the exact `build` wheel,
installs it in an isolated environment on Python 3.11–3.14, and uses pip-audit
2.10.1. It verifies the installed candidate name/version against the wheel metadata,
then audits the exact installed third-party inventory using a temporary pinned requirements
file (`--no-deps --disable-pip`). Only that verified candidate is excluded, allowing
first publication without weakening third-party skip/advisory checks. Empty or mismatched
inventories block. There are no runtime extras (`dev` and `docs` are not runtime closures).
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
records `INCOMPLETE` with "action outcome only"; its analysed inventory and finding
count are unknown. Exactly exit 3 is tolerated by the evidence target, while the pinned
Semgrep action remains the blocking gate and its failure is never overridden.

`FAIL` means a policy violation/finding; `TOOL_ERROR` means execution or evidence
cannot be trusted; `INCOMPLETE` means scope/outputs are missing or skipped. All
three block release/static gates; empty Python scans never pass. Recovery after a
transient tool failure is `gh workflow run publish-pypi.yml --ref vX.Y.Z` on the
same unchanged tag. Code corrections require a new release, never a moved tag.

Local/CI entry points: `make security` includes repository Bandit and rendered scans;
`make security-bandit`, `make security-rendered`, `make security-semgrep`,
`make security-audit` (blocking), `make security-audit-report` (reporting-only),
`make security-contracts`, and opt-in `make security-host` are shared targets.
Audit targets take `AUDIT_SITE_PACKAGES`, `CANDIDATE_NAME`, `CANDIDATE_VERSION`
(from candidate wheel metadata), and `SECURITY_OUTPUT`; Semgrep takes `SEMGREP_OUTCOME`.

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
only when the value is exactly lowercase `true` (no case folding or whitespace
trimming). `True`, `TRUE`, `1`, `yes`, empty and whitespace/newline variants keep
FUNCTION. A template-owned Python `UserWarning` during indexing is visible in
local Core Tools host output; real-host tests assert it in public mode and its
absence in default mode. This is not a claim about every cloud log configuration.
Core Tools local mode does not enforce function keys.
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

## Filesystem publication boundary

The selected destination is a directory root alias: existing symlinked ancestors
and a valid symlink selected as the destination are followed once to a canonical
root, preserving the previous CLI contract. Dangling destination links are rejected.
The project directory immediately below that canonical root cannot itself be a
symlink. Before publication, any existing link along a generated output path that
resolves outside the canonical project root is rejected without changing outside
data. Other unrelated existing links are never followed by the staged whole-tree
replacement or cleanup. Rendering uses a fresh sibling staging tree; overwrite
and rollback rename whole directories and preserve original data on publish failure.
Do not let an untrusted concurrent process mutate the selected directory during
generation: this is a local filesystem boundary, not a hostile concurrent-filesystem sandbox.

Expansion (`advanced add`, `api add-route`, `api add-resource`) uses the same
canonical-root boundary. Before any write it preflights function, test, schema,
service, registration and configuration paths, then the complete planned atomic
write set. Existing in-root links remain supported; escaping, dangling and looping
paths fail with `ScaffoldError` before staging or registration changes. Expansion
does not write README/docs/workflows; any future such writes must enter the same
preflighted write set. Refused operations leave project and outside inventories
unchanged. Checks are pathname-based, not directory-handle anchored: a concurrent
untrusted rename/symlink swap between preflight and use remains a TOCTOU risk.
