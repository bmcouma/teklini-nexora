"""Findings produced by specialized diagnostic agents."""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexora.models.evidence import Evidence


class AgentFinding(BaseModel):
    agent: str
    summary: str
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: str = "low"
    notes: str | None = None


class ReviewFinding(BaseModel):
    """Output of the Evidence Reviewer agent."""

    sufficient: bool
    justification: str
    missing_evidence: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    conclusion_status: str = "not_reviewed"
    recommendation: str  # "proceed" | "additional_investigation"
