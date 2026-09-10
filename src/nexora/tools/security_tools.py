"""Defensive security diagnostic tools.

These tools identify obvious misconfiguration signals from data the user
has provided. They perform no offensive testing, no exploitation, and no
destructive checks of any kind.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from nexora.tools.base import BaseTool

_RECOMMENDED_HEADERS = [
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "content-security-policy",
]


class HttpHeaderAuditInput(BaseModel):
    headers: dict[str, str] | None = None


class HttpHeaderAuditTool(BaseTool[HttpHeaderAuditInput, dict]):
    name = "http_security_header_audit"
    description = "Checks a set of HTTP response headers against common security header recommendations."

    def run(self, payload: HttpHeaderAuditInput) -> dict[str, Any]:
        if not payload.headers:
            return {"unavailable": True, "unavailable_reason": "No HTTP headers were provided to audit."}
        lower_headers = {k.lower() for k in payload.headers}
        missing = [h for h in _RECOMMENDED_HEADERS if h not in lower_headers]
        return {"unavailable": False, "missing_recommended_headers": missing}


class AuthFailureAnalysisInput(BaseModel):
    log_text: str | None = None


class AuthFailureAnalysisTool(BaseTool[AuthFailureAnalysisInput, dict]):
    name = "auth_failure_analysis"
    description = "Counts and characterizes authentication-failure signals in provided logs."

    def run(self, payload: AuthFailureAnalysisInput) -> dict[str, Any]:
        if not payload.log_text:
            return {"unavailable": True, "unavailable_reason": "No log text was provided."}
        lowered = payload.log_text.lower()
        failure_count = lowered.count("authentication failed") + lowered.count("401 unauthorized")
        return {
            "unavailable": False,
            "auth_failure_mentions": failure_count,
            "possible_credential_issue": failure_count > 0,
        }
