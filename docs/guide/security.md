# Generated application security

New LangGraph apps declare `func.AuthLevel.FUNCTION` on invoke/stream routes.
In Azure, send the function key in `x-functions-key`, not URLs. Core Tools local
`func start` does not enforce function keys: local requests can succeed without
keys even when bindings declare FUNCTION. Local success is not an authentication test.

Only for a deliberately public demo, set `LANGGRAPH_PUBLIC_DEMO=true` in the
generated project's environment/app settings before startup. It selects ANONYMOUS
and logs a WARNING that graph routes are public. Other values retain FUNCTION.
Never enable the demo profile in production. Existing projects are not rewritten.
This new-project deployment compatibility change needs maintainer release review;
it does not change the scaffolder CLI or Python API.

A function key is application-level access control, not user identity or per-user
authorization. Configure identity and consult the
[LangGraph library documentation](https://github.com/yeongseon/azure-functions-langgraph-python)
for `ThreadAuthorizer` guidance. Do not assume a key isolates thread owners.

HTTP health stays anonymous and returns only `{"status": "ok"}`. Optional OpenAPI
and Swagger routes intentionally demonstrate public docs locally; remove or restrict
those routes before production. They describe the API, not its deployment secrets.

Webhooks use FUNCTION plus HMAC-SHA256 in Azure. Missing, malformed, wrong or tampered
signatures fail; comparisons use `hmac.compare_digest`. A 1 MiB application bound
rejects large bodies before HMAC/JSON parsing. Configure host/proxy ingress limits
too, since the handler sees an already-buffered body. Logs and validation errors do
not include payload fields. The example in-memory store is not replay protection.
Use provider-signed timestamps, a freshness window and durable delivery-ID
deduplication; verify that the timestamp is covered by the signature. Define retry,
idempotency and key-rotation procedures with your sender.

AI application logs contain sizes rather than prompt or completion content. Review
provider SDK tracing before enabling DEBUG in production. The partial is an echo
demo and has no backend retries; the standalone service delegates to the SDK.
Apply identity, gateway rate limits/concurrency caps, token limits, per-user quotas,
provider budgets and cost alerts before exposing billable AI/agent routes.

Use a real output directory: scaffolding rejects destinations traversing symlinks.
Replacing a project requires explicit overwrite consent; publishing stages a new
tree and restores the original on publish failure. Do not concurrently mutate the
destination while generation runs; this is not an adversarial multi-user sandbox.

The rendered-output CI check scans all ten templates and three presets plus the AI
partial. No Bicep is currently generated, so Azure provisioning, HTTPS enforcement
and resource TLS configuration require deployment-specific validation. See the root
[security policy](https://github.com/yeongseon/azure-functions-scaffold-python/blob/main/SECURITY.md)
for scan evidence and blocking release dependency policy.
