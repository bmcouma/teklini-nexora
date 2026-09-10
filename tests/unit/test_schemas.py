import pytest
from pydantic import ValidationError

from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.incident import Incident, IncidentCreate, Severity
from nexora.models.report import RootCause


def test_incident_gets_default_id_and_timestamps():
    incident = Incident(title="Test incident", description="Something broke.")
    assert incident.incident_id.startswith("INC-")
    assert incident.severity == Severity.INFORMATIONAL
    assert incident.iteration_count == 0


def test_incident_create_allows_demo_mode_without_title():
    payload = IncidentCreate(use_demo_data=True)
    assert payload.title is None
    assert payload.use_demo_data is True


def test_evidence_requires_summary_and_valid_enum_values():
    evidence = Evidence(
        evidence_id="ev-1",
        agent="network_agent",
        source=EvidenceSource.UPLOADED_LOG,
        reliability=EvidenceReliability.HIGH,
        summary="Connection refused detected.",
    )
    assert evidence.source == EvidenceSource.UPLOADED_LOG

    with pytest.raises(ValidationError):
        Evidence(
            evidence_id="ev-2",
            agent="network_agent",
            source="not-a-real-source",
            reliability=EvidenceReliability.HIGH,
            summary="x",
        )


def test_root_cause_confidence_must_be_between_zero_and_one():
    RootCause(root_cause="Example", confidence=0.5)
    with pytest.raises(ValidationError):
        RootCause(root_cause="Example", confidence=1.5)
