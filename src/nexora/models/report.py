"""Root cause, remediation, and final incident report structures."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field

from nexora.models.evidence import Evidence
from nexora.models.incident import IncidentCategory, Severity


class RootCause(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: str = "low"
    supporting_evidence: list[Evidence] = Field(default_factory=list)
    alternative_causes: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(BaseModel):
    action: str
    risk: RiskLevel
    rationale: str
    requires_approval: bool = False
    approved: bool | None = None


class ApprovalRequest(BaseModel):
    recommendation_index: int
    approved: bool
    approved_by: str | None = None
    note: str | None = None


class IncidentReport(BaseModel):
    incident_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    incident_summary: str
    severity: Severity
    category: IncidentCategory
    affected_system: str | None
    observed_symptoms: list[str]
    known_facts: list[str]
    evidence_collected: list[Evidence]
    investigation_performed: list[str]
    root_cause: RootCause
    recommended_resolution: list[Recommendation]
    verification_steps: list[str]
    security_considerations: list[str]
    remaining_uncertainty: list[str]
    is_demo_data: bool = False
