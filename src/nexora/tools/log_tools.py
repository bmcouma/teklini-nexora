"""Deterministic log parsing.

This tool never invents log content. It only extracts and classifies
lines that are actually present in the text handed to it (user-provided
logs or demo fixtures).
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from nexora.tools.base import BaseTool

_SIGNAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "http_5xx": re.compile(r"\b(50[0-9])\b"),
    "connection_refused": re.compile(r"(?i)connection refused"),
    "connection_reset": re.compile(r"(?i)connection reset"),
    "timeout": re.compile(r"(?i)\btimed? ?out\b|timeout"),
    "dns_failure": re.compile(r"(?i)name or service not known|dns.*(fail|error)|nxdomain"),
    "tls_error": re.compile(r"(?i)certificate (has expired|verify failed)|ssl.*error"),
    "permission_denied": re.compile(r"(?i)permission denied|eacces"),
    "disk_full": re.compile(r"(?i)no space left on device|disk full"),
    "oom": re.compile(r"(?i)out of memory|oom.?killer|memoryerror"),
    "auth_failure": re.compile(r"(?i)authentication failed|invalid credentials|401 unauthorized"),
    "db_connection_failure": re.compile(r"(?i)could not connect to (server|database)|connection to database.*failed"),
    "config_error": re.compile(r"(?i)config(uration)? error|invalid configuration|missing environment variable"),
    "service_failed": re.compile(r"(?i)failed to start|service (failed|crashed)|exited with code [1-9]"),
    "port_conflict": re.compile(r"(?i)address already in use|port .*(in use|unavailable)"),
}


class LogParseInput(BaseModel):
    log_text: str


class LogAnalysisTool(BaseTool[LogParseInput, dict]):
    name = "log_analysis"
    description = "Scans provided log text for known error signal patterns. Read-only, no external calls."

    def run(self, payload: LogParseInput) -> dict[str, Any]:
        if not payload.log_text or not payload.log_text.strip():
            return {"unavailable": True, "unavailable_reason": "No log text was provided."}

        lines = payload.log_text.splitlines()
        matches: dict[str, list[str]] = {}

        for line in lines:
            for signal, pattern in _SIGNAL_PATTERNS.items():
                if pattern.search(line):
                    matches.setdefault(signal, [])
                    if len(matches[signal]) < 5:
                        matches[signal].append(line.strip()[:300])

        return {
            "unavailable": False,
            "lines_scanned": len(lines),
            "signals_detected": sorted(matches.keys()),
            "matched_lines": matches,
        }
