"""Incident service.

Bridges the API layer, persistence, and the investigation workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from nexora.api.db import IncidentRecord
from nexora.models.incident import Incident, IncidentCreate
from nexora.models.report import ApprovalRequest
from nexora.models.state import InvestigationState
from nexora.services.demo_data import DEMO_INCIDENT_DESCRIPTION, DEMO_INCIDENT_TITLE, DEMO_LOG_TEXT
from nexora.workflows.investigation_workflow import run_investigation


class IncidentNotFoundError(Exception):
    pass


def _to_incident(payload: IncidentCreate) -> Incident:
    if payload.use_demo_data:
        return Incident(
            title=payload.title or DEMO_INCIDENT_TITLE,
            description=payload.description or DEMO_INCIDENT_DESCRIPTION,
            affected_service=payload.affected_service or "django-app",
            environment=payload.environment or "production",
            reported_severity=payload.reported_severity,
            logs=payload.logs or DEMO_LOG_TEXT,
            use_demo_data=True,
        )
    if payload.title is None or payload.description is None:
        raise ValueError("title and description are required unless use_demo_data is set")
    return Incident(
        title=payload.title,
        description=payload.description,
        affected_service=payload.affected_service,
        environment=payload.environment,
        reported_severity=payload.reported_severity,
        logs=payload.logs,
        use_demo_data=False,
    )


def _persist(db: Session, state: InvestigationState) -> IncidentRecord:
    incident = state.incident
    record = db.get(IncidentRecord, incident.incident_id)
    state_json = state.model_dump(mode="json")

    if record is None:
        record = IncidentRecord(
            incident_id=incident.incident_id,
            title=incident.title,
            category=incident.category.value,
            severity=incident.severity.value,
            stage=incident.stage.value,
            state_json=state_json,
        )
        db.add(record)
    else:
        record.title = incident.title
        record.category = incident.category.value
        record.severity = incident.severity.value
        record.stage = incident.stage.value
        record.state_json = state_json
        record.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(record)
    return record


def create_and_investigate(db: Session, payload: IncidentCreate) -> InvestigationState:
    incident = _to_incident(payload)
    state = run_investigation(incident)
    _persist(db, state)
    return state


def reinvestigate(db: Session, incident_id: str) -> InvestigationState:
    """Re-run the investigation workflow for an existing incident, preserving its ID."""
    existing = get_state(db, incident_id)
    incident = existing.incident.model_copy(
        update={
            "iteration_count": 0,
            "review_iteration_count": 0,
        }
    )
    state = run_investigation(incident)
    _persist(db, state)
    return state


def get_state(db: Session, incident_id: str) -> InvestigationState:
    record = db.get(IncidentRecord, incident_id)
    if record is None:
        raise IncidentNotFoundError(incident_id)
    return InvestigationState.model_validate(record.state_json)


def list_incidents(db: Session) -> list[IncidentRecord]:
    return list(db.query(IncidentRecord).order_by(IncidentRecord.created_at.desc()).all())


def approve_recommendation(db: Session, incident_id: str, approval: ApprovalRequest) -> InvestigationState:
    state = get_state(db, incident_id)
    if not (0 <= approval.recommendation_index < len(state.recommendations)):
        raise ValueError("recommendation_index out of range")

    state.recommendations[approval.recommendation_index].approved = approval.approved
    note = "approved" if approval.approved else "declined"
    state.log(
        f"Human approval recorded: recommendation #{approval.recommendation_index} {note}"
        + (f" by {approval.approved_by}" if approval.approved_by else "")
        + ("" if not approval.note else f" ({approval.note})")
    )

    if all(
        (not r.requires_approval) or (r.approved is not None) for r in state.recommendations
    ):
        from nexora.models.incident import InvestigationStage

        state.incident.stage = InvestigationStage.REPORT_READY

    _persist(db, state)
    return state
