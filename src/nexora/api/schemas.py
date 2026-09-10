"""API-specific response schemas.

Most responses reuse the domain models directly (InvestigationState,
IncidentReport, Evidence). This module holds the handful of shapes that
exist only for the API surface, such as list views.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class IncidentSummary(BaseModel):
    incident_id: str
    title: str
    category: str
    severity: str
    stage: str
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    app_name: str


class VersionResponse(BaseModel):
    version: str
