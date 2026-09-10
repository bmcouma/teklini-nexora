# QA Phase 2 Final Report

## Scope

Phase 2 remediation addressed frontend authentication, clean-environment setup guidance, architecture accuracy, evidence review, prompt-injection handling, and safe tool boundaries. Existing deterministic demo functionality was preserved.

## Changes Implemented

- Added session-scoped frontend API-key handling using a user-entered key only.
- Added typed frontend handling for `401 Unauthorized` and `403 Forbidden` responses.
- Added UI states for missing or rejected authentication on incident creation and approval.
- Added frontend authentication tests and a `vitest` test command.
- Removed hard-coded production secret behavior and added fail-closed production configuration validation.
- Added optional API-key enforcement for incident creation, reinvestigation, and recommendation approval.
- Added clean-clone setup commands for Linux/macOS and Windows PowerShell.
- Documented demo mode, authenticated mode, tests, frontend setup, backend setup, and verified portability limits.
- Added explicit component classification in `ARCHITECTURE.md`.
- Added a real optional Google ADK reasoning stage using `LlmAgent` and `InMemoryRunner`. The default heuristic workflow remains deterministic.
- Gemini prompts mark incident content and evidence as untrusted data, require JSON output, and reject citations to unknown evidence IDs.
- Strengthened review findings with unsupported claims, contradictions, assumptions, and missing evidence.
- Added explicit `NEEDS_MORE_EVIDENCE` conclusions for insufficient deterministic evidence.
- Added qualitative confidence levels: `high`, `medium`, and `low`.
- Added regression tests for prompt-injection text, fabricated evidence IDs, and authentication behavior.
- Isolated the standard pytest suite from local `.env` provider settings; live Gemini coverage is
  excluded from normal discovery and marked `live_gemini` for explicit opt-in execution.

## Tests Executed

- Backend: `pytest`
  - Result: **50 passed, 2 warnings**
- Backend deterministic marker suite: `pytest -m "not live_gemini"`
  - Result: **50 passed, 2 warnings**
- Frontend: `npm test`
  - Result: **1 test file passed, 2 tests passed**
- Frontend lint: `npm run lint`
  - Result: **passed**
- Frontend production build: `npm run build`
  - Result: **passed**
- Python environment check:
  - Active interpreter: **Python 3.14.7**
  - Project requirement: **Python >=3.11**
- Environment template check:
  - `.env.example` contains placeholders and no real credentials were added.

The backend suite continues to emit two dependency deprecation warnings from the installed FastAPI/Starlette test client stack. They are not caused by the remediation changes.

## Security Verification

- No production API key is bundled into React or TypeScript source.
- Frontend keys are user-provided and kept in browser session storage; this is suitable only for the prototype's minimal API boundary.
- Production startup rejects an empty `SECRET_KEY`.
- Enabling `NEXORA_AUTH_REQUIRED=true` without `NEXORA_API_KEY` fails configuration validation.
- Protected mutation routes reject missing or invalid API keys.
- Logs remain redacted before workflow reasoning.
- Diagnostic tools remain read-only and no unrestricted shell execution was added.
- No execution capability exists. Recommendations remain subject to human approval and are not executed automatically.
- Prompt-injection regression tests verify that hostile incident text remains data and that fabricated evidence references are rejected.

## Agent Architecture Verification

Current implementation classification:

- Deterministic tools: `src/nexora/tools/*`
- Deterministic workflow logic: classifier, planner, specialist agents, deterministic root-cause analyzer
- Validation/reviewer logic: evidence reviewer and structured Gemini response validation
- Gemini-powered reasoning: optional `GeminiReasoningAgent`, enabled only with `LLM_PROVIDER=gemini`
- ADK agent: `GeminiReasoningAgent` constructs a root `LlmAgent`, specialist ADK sub-agents, and executes them through `InMemoryRunner` when Gemini mode is enabled
- API/application infrastructure: FastAPI routes, services, persistence, models, configuration, and frontend

The deterministic demo path is the supported reproducible path. Gemini receives supplied incident data and deterministic evidence only. It cannot execute tools or create observations.

## Known Limitations

- The API-key mechanism is a minimal prototype boundary, not identity management.
- There is no user identity, role model, key rotation workflow, rate limiting, audit event store, or TLS termination in this repository.
- The frontend cannot prove backend authentication mode until it makes a request; it presents session-key controls for protected deployments.
- The live Gemini smoke test is opt-in and was not run in the final deterministic verification; live provider success is not claimed.
- Docker, PostgreSQL, Cloud Run, and external infrastructure integrations were not verified in this phase.
- Browser automation/E2E was not run because no configured browser test suite is present.
- The setup documentation is verified against the current Windows environment and repository configuration. A fresh Linux clone was not executed in this environment, so broad cross-platform support is documented as practical guidance, not as fully verified behavior.
- The existing SQLite initialization is suitable for local development, not concurrent production workloads or schema migration operations.

## Remaining Risks

- Sensitive incident data may be persisted in the application database after redaction; deployment operators still need retention, access control, encryption, and backup policies.
- Qualitative confidence levels are explanatory labels, not statistically calibrated probabilities.
- The heuristic classifier and deterministic rules have known evaluation limitations.
- Gemini output quality and availability depend on provider configuration and are not covered by local deterministic tests.
- Dependency deprecation warnings should be resolved during a future dependency maintenance pass.

## Portfolio Suitability

**Suitable for GitHub portfolio publication after reviewing repository secrets and generated local files.** It now accurately presents a portfolio-grade hybrid AI/IT operations investigation platform with a reproducible deterministic mode and an optional evidence-grounded Gemini path.

## Production Readiness

**Not production-ready.** Passing tests demonstrate functional behavior in the verified local environment, not operational readiness. Production deployment still requires a real identity and authorization model, secure secret management, TLS and network controls, rate limiting, audit logging, observability, data-retention policy, migration strategy, provider testing, and deployment-specific verification.
