# Portfolio Readiness

## Project Status

**Portfolio-ready with honest boundaries.** Teklini Nexora is suitable for public GitHub presentation as a hybrid AI/IT operations investigation project. It is not a production-ready enterprise AIOps platform.

## Verified Capabilities

- FastAPI incident API with SQLite local persistence and PostgreSQL configuration support.
- React/TypeScript operations dashboard.
- Deterministic classifier, planner, specialist investigation agents, diagnostic tools, reviewer, root-cause analyzer, remediation advisor, and report generator.
- Optional Google ADK `LlmAgent` and `InMemoryRunner` path for Gemini reasoning.
- Evidence serialization, source/reliability metadata, evidence-ID validation, and post-reasoning review.
- Deterministic fallback when Gemini is unavailable, malformed, or times out.
- Secret redaction before investigation reasoning.
- Prompt-injection-aware treatment of incident data.
- Optional API-key protection for sensitive mutation routes.
- Human approval state for high-risk recommendations.
- No infrastructure mutation or unrestricted shell execution.
- Deterministic demo mode that requires no Gemini credential.

## Architecture

The supported deterministic path is:

```text
Incident -> deterministic orchestration -> specialist agents -> read-only tools
-> structured evidence -> deterministic review -> root cause -> recommendation
-> approval state
```

Gemini mode adds:

```text
structured evidence -> ADK LlmAgent/InMemoryRunner -> Gemini conclusion
-> post-reasoning evidence review -> root cause/recommendation
```

Gemini receives serialized incident data and deterministic evidence only. It does not receive Nexora diagnostic tools or execution capabilities.

## Testing

Verified during the portfolio pass:

- Backend: **50 passed, 2 warnings** via `pytest`
- Deterministic marker suite: **50 passed, 2 warnings** via `pytest -m "not live_gemini"`
- Frontend tests: **2 passed**
- Frontend lint: **passed**
- Frontend build: **passed**
- Changed-file diagnostics: no errors

The standard pytest configuration excludes `tests/live` and forces heuristic provider mode so a local `.env` cannot make normal tests contact Gemini.

## Security

The repository ignores `.env` and `.env.*` except `.env.example`. API keys are backend-only in Gemini mode and are never bundled into the frontend. User-submitted logs are redacted before analysis. Gemini prompts mark incident content and evidence as untrusted data. Diagnostic tools are read-only and bounded. High-risk recommendations require approval state, but no target-system execution exists.

These controls do not provide identity management, role-based authorization, key rotation, rate limiting, TLS, audit logging, or formal security certification.

## AI and ADK Status

Google ADK is implemented in the optional Gemini path through `LlmAgent` and `InMemoryRunner`. Gemini reasoning is implemented behind `LLM_PROVIDER=gemini`. The live Gemini provider smoke test is opt-in and was not successfully verified in the current environment, so this report makes no live-provider success claim.

## Known Limitations

- No infrastructure mutation or autonomous remediation.
- No unrestricted shell execution.
- Limited diagnostic integrations and supplied-evidence coverage.
- Keyword-driven heuristic classification has known evaluation limitations.
- Gemini behavior depends on credential, network, provider, and SDK availability.
- SQLite is for local development; production schema migration and concurrency operations are not established.
- Docker, PostgreSQL, Cloud Run, and browser automation were not fully verified in this pass.
- The API-key boundary is a minimal prototype control, not an identity system.

## GitHub Readiness

**Suitable for public GitHub publication after human review of local/generated files and credential history.** Before publishing, confirm that `.env`, local databases, build outputs, and any previously exposed API key are absent from Git history. No portfolio screenshots were added because no verified screenshot capture was completed in this pass.

## Production Status

**Not production-ready.** The project demonstrates credible engineering decisions, deterministic reproducibility, optional ADK/Gemini reasoning, validation, and safety boundaries. Production deployment would require substantially stronger identity, authorization, observability, data governance, deployment controls, migrations, and provider verification.

## Human Review Before Publication

- Rotate any API key previously pasted into chat or committed anywhere.
- Review `git status` and full Git history for secrets and local artifacts.
- Decide whether to publish Docker/PostgreSQL configuration as supported-but-unverified setup.
- Optionally capture real screenshots from a running local demo.
