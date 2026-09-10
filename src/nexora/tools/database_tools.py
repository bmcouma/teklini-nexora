"""Database diagnostic tools.

These tools never execute SQL against a target database and never
receive or expose credentials. They reason only over connection
metadata and log signals explicitly supplied by the user.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from nexora.tools.base import BaseTool

_DB_ERROR_PATTERNS: dict[str, re.Pattern[str]] = {
    "connection_refused": re.compile(r"(?i)connection refused"),
    "authentication_failed": re.compile(r"(?i)password authentication failed|access denied for user"),
    "too_many_connections": re.compile(r"(?i)too many connections|remaining connection slots"),
    "unknown_database": re.compile(r"(?i)database .* does not exist|unknown database"),
    "migration_pending": re.compile(r"(?i)you have \d+ unapplied migration|pending migration"),
}


class DatabaseLogAnalysisInput(BaseModel):
    log_text: str | None = None


class DatabaseLogAnalysisTool(BaseTool[DatabaseLogAnalysisInput, dict]):
    name = "database_log_analysis"
    description = "Scans provided database or application logs for known database failure signatures."

    def run(self, payload: DatabaseLogAnalysisInput) -> dict[str, Any]:
        if not payload.log_text:
            return {"unavailable": True, "unavailable_reason": "No database-related log text was provided."}
        matches = {
            name: True for name, pattern in _DB_ERROR_PATTERNS.items() if pattern.search(payload.log_text)
        }
        return {"unavailable": False, "signals_detected": sorted(matches.keys())}


class ConnectionPoolInput(BaseModel):
    max_connections: int | None = None
    active_connections: int | None = None


class ConnectionPoolTool(BaseTool[ConnectionPoolInput, dict]):
    name = "connection_pool_inspection"
    description = "Evaluates connection pool utilization from explicitly supplied metrics."

    WARN_THRESHOLD = 0.9

    def run(self, payload: ConnectionPoolInput) -> dict[str, Any]:
        if payload.max_connections is None or payload.active_connections is None:
            return {"unavailable": True, "unavailable_reason": "Connection pool metrics were not provided."}
        utilization = payload.active_connections / payload.max_connections if payload.max_connections else 0
        return {
            "unavailable": False,
            "utilization": round(utilization, 2),
            "near_exhaustion": utilization >= self.WARN_THRESHOLD,
        }
