"""REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from nexora import PACKAGE_VERSION
from nexora.api.db import get_db
from nexora.api.schemas import HealthResponse, IncidentSummary, VersionResponse
from nexora.config.settings import get_settings
from nexora.models.incident import Incident, IncidentCreate
from nexora.models.report import ApprovalRequest, IncidentReport
from nexora.models.state import InvestigationState
from nexora.services import incident_service

router = APIRouter()


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> None:
    settings = get_settings()
    if not settings.auth_required:
        return

    provided = x_api_key
    if not provided and authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer":
            provided = token

    if provided == settings.api_key and settings.api_key:
        return

    raise HTTPException(status_code=401, detail="API key required")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", app_name=settings.app_name)


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    return VersionResponse(version=PACKAGE_VERSION)


@router.post("/incidents", response_model=InvestigationState)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    _authenticated: None = Depends(require_api_key),
) -> InvestigationState:
    if not payload.use_demo_data and not payload.title:
        raise HTTPException(status_code=422, detail="title is required unless use_demo_data is set")
    if not payload.use_demo_data and not payload.description:
        raise HTTPException(
            status_code=422, detail="description is required unless use_demo_data is set"
        )
    return incident_service.create_and_investigate(db, payload)


@router.get("/incidents", response_model=list[IncidentSummary])
def list_incidents(db: Session = Depends(get_db)) -> list[IncidentSummary]:
    records = incident_service.list_incidents(db)
    return [
        IncidentSummary(
            incident_id=r.incident_id,
            title=r.title,
            category=r.category,
            severity=r.severity,
            stage=r.stage,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.get("/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: str, db: Session = Depends(get_db)) -> Incident:
    try:
        state = incident_service.get_state(db, incident_id)
    except incident_service.IncidentNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found") from None
    return state.incident


@router.get("/incidents/{incident_id}/status", response_model=InvestigationState)
def get_incident_status(incident_id: str, db: Session = Depends(get_db)) -> InvestigationState:
    try:
        return incident_service.get_state(db, incident_id)
    except incident_service.IncidentNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found") from None


@router.get("/incidents/{incident_id}/evidence")
def get_incident_evidence(incident_id: str, db: Session = Depends(get_db)) -> list[dict]:
    try:
        state = incident_service.get_state(db, incident_id)
    except incident_service.IncidentNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found") from None
    return [e.model_dump(mode="json") for e in state.evidence]


@router.get("/incidents/{incident_id}/report", response_model=IncidentReport)
def get_incident_report(incident_id: str, db: Session = Depends(get_db)) -> IncidentReport:
    try:
        state = incident_service.get_state(db, incident_id)
    except incident_service.IncidentNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found") from None
    if state.final_report is None:
        raise HTTPException(status_code=409, detail="Report has not been generated yet")
    return state.final_report


@router.post("/incidents/{incident_id}/investigate", response_model=InvestigationState)
def reinvestigate(
    incident_id: str,
    db: Session = Depends(get_db),
    _authenticated: None = Depends(require_api_key),
) -> InvestigationState:
    """Re-run the investigation workflow for an existing incident's stored input."""
    try:
        return incident_service.reinvestigate(db, incident_id)
    except incident_service.IncidentNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found") from None


@router.post("/incidents/{incident_id}/approve", response_model=InvestigationState)
def approve_recommendation(
    incident_id: str,
    approval: ApprovalRequest,
    db: Session = Depends(get_db),
    _authenticated: None = Depends(require_api_key),
) -> InvestigationState:
    try:
        return incident_service.approve_recommendation(db, incident_id, approval)
    except incident_service.IncidentNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
