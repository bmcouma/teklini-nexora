"""Core incident data structures."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class IncidentCategory(str, Enum):
    NETWORK = "network"
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    DATABASE = "database"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    AUTHENTICATION = "authentication"
    API = "api"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InvestigationStage(str, Enum):
    SUBMITTED = "submitted"
    CLASSIFYING = "classifying"
    PLANNING = "planning"
    INVESTIGATING = "investigating"
    REVIEWING = "reviewing"
    ADDITIONAL_INVESTIGATION = "additional_investigation"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    REMEDIATION = "remediation"
    AWAITING_APPROVAL = "awaiting_approval"
    REPORT_READY = "report_ready"
    FAILED = "failed"


def _now() -> datetime:
    return datetime.now(UTC)


class IncidentCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    affected_service: str | None = None
    environment: str | None = Field(default=None, description="e.g. production, staging")
    reported_severity: Severity | None = None
    logs: str | None = Field(
        default=None, description="Raw user-provided log content, treated as untrusted data."
    )
    use_demo_data: bool = False


class Incident(BaseModel):
    incident_id: str = Field(default_factory=lambda: f"INC-{uuid4().hex[:8].upper()}")
    title: str
    description: str
    affected_service: str | None = None
    environment: str | None = None
    reported_severity: Severity | None = None
    logs: str | None = None
    use_demo_data: bool = False
    category: IncidentCategory = IncidentCategory.UNKNOWN
    severity: Severity = Severity.INFORMATIONAL
    stage: InvestigationStage = InvestigationStage.SUBMITTED
    iteration_count: int = 0
    review_iteration_count: int = 0
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
