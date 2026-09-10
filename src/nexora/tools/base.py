"""Base classes for deterministic diagnostic tools.

Tools are intentionally separate from agent reasoning. An agent decides
*when* to call a tool; the tool itself is deterministic, has a fixed
input/output schema, and never depends on an LLM to run. This keeps
diagnostic evidence reproducible and auditable.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

logger = logging.getLogger("nexora.tools")

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT")

DEFAULT_TIMEOUT_SECONDS = 5.0


class ToolExecutionError(Exception):
    """Raised when a tool fails validation, times out, or errors during execution."""


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    duration_ms: float
    data: dict[str, Any] = {}
    error: str | None = None
    unavailable: bool = False
    unavailable_reason: str | None = None


class BaseTool(ABC, Generic[InputT, OutputT]):
    """Every diagnostic tool implements this interface.

    Subclasses must define `name`, `description`, and `run`. The base
    class handles timing, error containment, and structured logging so
    that individual tools stay focused on their diagnostic logic.
    """

    name: str = "unnamed_tool"
    description: str = ""
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    @abstractmethod
    def run(self, payload: InputT) -> dict[str, Any]:
        """Execute the tool. Must return a JSON-serializable dict.

        Implementations should never raise for expected "no data available"
        situations. Instead, return a dict with an explicit unavailable marker
        so callers can distinguish "checked and found nothing wrong" from
        "could not check."
        """
        raise NotImplementedError

    def execute(self, payload: InputT, incident_id: str) -> ToolResult:
        start = time.monotonic()
        try:
            data = self.run(payload)
            duration_ms = (time.monotonic() - start) * 1000
            logger.info(
                "tool_execution",
                extra={
                    "incident_id": incident_id,
                    "tool": self.name,
                    "status": "success",
                    "duration_ms": round(duration_ms, 2),
                },
            )
            unavailable = bool(data.get("unavailable"))
            return ToolResult(
                tool_name=self.name,
                success=True,
                duration_ms=duration_ms,
                data=data,
                unavailable=unavailable,
                unavailable_reason=data.get("unavailable_reason"),
            )
        except Exception as exc:  # noqa: BLE001 - deliberately broad, tool boundary
            duration_ms = (time.monotonic() - start) * 1000
            logger.warning(
                "tool_execution",
                extra={
                    "incident_id": incident_id,
                    "tool": self.name,
                    "status": "error",
                    "duration_ms": round(duration_ms, 2),
                    "error": str(exc),
                },
            )
            return ToolResult(
                tool_name=self.name,
                success=False,
                duration_ms=duration_ms,
                error=str(exc),
            )
