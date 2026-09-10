"""Application-layer diagnostic tools.

Framework-aware analysis of user-provided application logs and
environment configuration. Extending support to another framework means
adding a new entry to `_FRAMEWORK_SIGNATURES` rather than modifying
agent logic.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from nexora.tools.base import BaseTool

_FRAMEWORK_SIGNATURES: dict[str, re.Pattern[str]] = {
    "django": re.compile(r"(?i)django|wsgi|manage\.py"),
    "flask": re.compile(r"(?i)flask|werkzeug"),
    "fastapi": re.compile(r"(?i)fastapi|uvicorn"),
    "express": re.compile(r"(?i)express|node_modules"),
    "gunicorn": re.compile(r"(?i)gunicorn"),
}


class FrameworkDetectionInput(BaseModel):
    log_text: str | None = None


class FrameworkDetectionTool(BaseTool[FrameworkDetectionInput, dict]):
    name = "framework_detection"
    description = "Detects which application framework(s) are referenced in provided logs."

    def run(self, payload: FrameworkDetectionInput) -> dict[str, Any]:
        if not payload.log_text:
            return {"unavailable": True, "unavailable_reason": "No log text was provided."}
        detected = [name for name, pattern in _FRAMEWORK_SIGNATURES.items() if pattern.search(payload.log_text)]
        return {"unavailable": False, "frameworks_detected": detected}


class EnvironmentVariableCheckInput(BaseModel):
    required_vars: list[str]
    provided_vars: dict[str, str] | None = None


class EnvironmentVariableCheckTool(BaseTool[EnvironmentVariableCheckInput, dict]):
    name = "environment_variable_check"
    description = "Checks a set of required environment variables against what was explicitly provided."

    def run(self, payload: EnvironmentVariableCheckInput) -> dict[str, Any]:
        if payload.provided_vars is None:
            return {
                "unavailable": True,
                "unavailable_reason": "No environment configuration was provided to check.",
            }
        missing = [v for v in payload.required_vars if v not in payload.provided_vars]
        empty = [v for v in payload.required_vars if payload.provided_vars.get(v) == ""]
        return {
            "unavailable": False,
            "missing_vars": missing,
            "empty_vars": empty,
        }
