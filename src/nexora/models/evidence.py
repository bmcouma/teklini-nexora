"""Evidence and diagnostic task structures.

Evidence is the currency of the investigation. Every claim made later
in the workflow (root cause, recommendations) must be traceable back
to one or more Evidence records collected here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class EvidenceSource(str, Enum):
    USER_PROVIDED = "user_provided"
    UPLOADED_LOG = "uploaded_log"
    DEMO_FIXTURE = "demo_fixture"
    TOOL_EXECUTION = "tool_execution"
    UNAVAILABLE = "unavailable"


class EvidenceReliability(str, Enum):
    """How much weight this evidence should carry in reasoning."""

    HIGH = "high"       # directly observed via a tool or explicit user log
    MEDIUM = "medium"    # inferred from partial or indirect data
    LOW = "low"          # user-asserted but unverified
    UNAVAILABLE = "unavailable"


class Evidence(BaseModel):
    evidence_id: str
    agent: str
    tool: str | None = None
    source: EvidenceSource
    reliability: EvidenceReliability
    summary: str
    detail: str | None = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DiagnosticTask(BaseModel):
    task_id: str
    objective: str
    assigned_agent: str
    required_tools: list[str] = Field(default_factory=list)
    validation_criteria: str
    status: str = "pending"  # pending | in_progress | completed | skipped


class DiagnosticPlan(BaseModel):
    objective: str
    known_facts: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    tasks: list[DiagnosticTask] = Field(default_factory=list)
    stopping_conditions: list[str] = Field(default_factory=list)
