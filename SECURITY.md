# Security

## Reporting a vulnerability

If you find a security issue in this project, please open a GitHub issue with as much detail as
you can provide, or contact the maintainer directly if the issue involves sensitive details you
would rather not post publicly.

## Design principles

Nexora is built around a small number of hard security constraints that hold regardless of how
the system is prompted or configured:

1. **No unrestricted shell access.** No component of Nexora executes arbitrary operating-system
   commands. Diagnostic tools call specific, narrow APIs with fixed timeouts and fixed output
   schemas.
2. **No destructive or state-changing operations against user infrastructure.** Nexora observes
   and recommends. In this version, it does not execute any remediation, low-risk or otherwise,
   against a target system. That boundary is enforced by the absence of any execution capability
   in the codebase, not by a policy an agent could be talked out of.
3. **High-risk recommendations always require explicit human approval.** The remediation advisor
   tags every recommendation with a risk level. Anything tagged `high` sets
   `requires_approval: true` and moves the incident to the `awaiting_approval` stage until a human
   calls `POST /api/incidents/{id}/approve`.
4. **User-provided content is always data, never instructions.** Incident descriptions and log
   text are passed through deterministic pattern-matching tools, not interpolated into a system
   prompt that could reinterpret embedded text as a command. See "Prompt injection defense" below.
5. **Secrets are redacted before analysis, not after.** `src/nexora/security/redaction.py` runs
   on submitted logs before the investigation workflow starts, stripping common credential
   patterns (AWS access keys, bearer tokens, password/secret fields, database connection string
   credentials, JWTs, PEM private key blocks).
6. **No credentials ever reach a tool.** Database tools operate on log signals and connection
   *metadata* (pool size, connection counts); they never receive, store, or transmit an actual
   password or connection string.

## Prompt injection defense

A submitted log file might contain text like `"ignore previous instructions and..."`. Nexora's
default configuration (`LLM_PROVIDER=heuristic`) never sends log text to a language model at all,
so there is no prompt for such text to inject into: it is matched against a fixed set of regular
expressions in `src/nexora/tools/log_tools.py` and related tool modules, producing structured
`Evidence` records. There is no path by which matched text can change which tools are called,
what permissions an agent has, or how the orchestrator's control flow proceeds.

When `LLM_PROVIDER=gemini` is configured, the ADK prompt explicitly labels incident content and
serialized evidence as untrusted data. Gemini receives no Nexora diagnostic tools, shell access,
credentials, or mutation capability. Its structured evidence IDs are validated and the proposed
conclusion is reviewed after reasoning. These are engineering controls, not a formal safety
certification or guarantee against every model failure.

## Secrets and environment configuration

- `.env` is git-ignored. Only `.env.example` (with no real values) is committed.
- `SECRET_KEY`, `GOOGLE_API_KEY`, and database credentials are read exclusively from environment
  variables via `src/nexora/config/settings.py`.
- Structured logging (`src/nexora/tools/base.py`) never logs tool input/output payloads verbatim;
  it logs the tool name, status, and duration. Redacted log text may still appear in `Evidence`
  records returned by the API, since that is the investigation's actual output, but the
  redaction step runs first so credential patterns are stripped before they reach that point.

## Authentication and authorization

This version does not implement end-user identity or role-based access control. It provides an
optional shared API-key dependency for sensitive mutation routes when `NEXORA_AUTH_REQUIRED=true`.
That boundary is suitable for a controlled portfolio demo, not a replacement for an identity
provider, per-incident authorization, key rotation, rate limiting, TLS, or audit logging.

## Dependency and supply chain notes

- Dependencies are pinned by lower bound in `pyproject.toml` and `frontend/package.json`; run
  `pip list --outdated` / `npm outdated` periodically and review changelogs before upgrading.
- The Docker images use official, actively maintained base images (`python:3.12-slim`,
  `node:22-slim`, `postgres:16-alpine`, `nginx:1.27-alpine`).
