# Teklini Nexora QA Remediation Plan

## Overview

This document tracks the remediation work required to move the project from a credible portfolio prototype to a technically hardened, more maintainable implementation without changing its core purpose.

## Severity Priorities

### Critical

| Issue | Severity | Affected files | Proposed solution | Implementation status |
|---|---|---|---|---|
| Broken or brittle local developer setup | Critical | README.md, SETUP.md, pyproject.toml, .env.example, .gitignore | Standardize a clean venv flow, document supported Python, add startup scripts, remove dependence on pre-existing local environments | Completed for documented local workflows; Linux not executed here |
| Unsafe default secret behavior | Critical | src/nexora/config/settings.py, .env.example | Require secret configuration through environment variables and fail clearly in production, without embedding a default secret in code | Completed |
| Unauthenticated sensitive operations | Critical | src/nexora/api/routes.py, src/nexora/api/main.py, frontend/src/lib/api.ts | Add optional environment-based API authentication for privileged routes and document demo/dev vs production posture | Completed for API and frontend prototype boundary |

### High

| Issue | Severity | Affected files | Proposed solution | Implementation status |
|---|---|---|---|---|
| Product positioning overstates production readiness | High | README.md, SECURITY.md, docs, app copy | Reframe the project as a portfolio-grade prototype and document limitations honestly | Completed |
| Architecture needs clearer deterministic-vs-agentic boundaries | High | src/nexora/agents/*, src/nexora/tools/*, docs/ARCHITECTURE.md | Separate tool-based observation layer from reasoning layer and clarify evidence/hypothesis boundaries | Completed; ADK Runner path implemented, live provider execution unverified |
| Demo mode and external-service assumptions are not clearly isolated | High | src/nexora/services/demo_data.py, README.md, SETUP.md | Keep demo mode deterministic and clearly label it as demo-only data | Completed |

### Medium

| Issue | Severity | Affected files | Proposed solution | Implementation status |
|---|---|---|---|---|
| Database initialization is too simple for real schema evolution | Medium | src/nexora/api/db.py | Keep SQLite compatibility for dev while documenting migration expectations for PostgreSQL | Planned |
| Frontend error/loading states need stronger QA polish | Medium | frontend/src/pages/*.tsx, frontend/src/lib/api.ts | Improve state handling for backend failures, empty data, and investigation lifecycle stages | Completed for current portfolio scope |
| Dependency drift and warnings | Medium | pyproject.toml, frontend/package.json | Review deprecations and upgrade only where low-risk | Planned |

### Low

| Issue | Severity | Affected files | Proposed solution | Implementation status |
|---|---|---|---|---|
| UI text and wording should stay professional | Low | frontend/src/*.tsx, README.md | Remove AI-marketing filler and keep wording technical and precise | Completed for current portfolio scope |
| Single-command developer workflow is missing | Low | README.md, SETUP.md | Add scripts and documented commands for backend/frontend startup | Planned |

## Implementation Notes

- This plan prioritizes high-confidence fixes that improve credibility without destabilizing the working demo flow.
- No major rewrite is planned; the focus is on hardening, documentation, and environment control.
- Any change that affects the current demo must preserve reproducible behavior and maintain testability.

## Progress Summary

- QA review completed against the current repository.
- Issue triage completed with priority labels.
- Remediation begins with environment reliability and secret handling.
