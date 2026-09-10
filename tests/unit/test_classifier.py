from nexora.agents.classifier import IncidentClassifierAgent
from nexora.models.incident import Incident, IncidentCategory, Severity
from nexora.models.state import InvestigationState


def _state_for(title: str, description: str, logs: str | None = None, reported_severity: Severity | None = None) -> InvestigationState:
    incident = Incident(title=title, description=description, logs=logs, reported_severity=reported_severity)
    return InvestigationState(incident=incident)


def test_classifies_network_category_from_dns_keywords():
    state = _state_for("Site unreachable", "Users report DNS resolution timeout errors on checkout.")
    result = IncidentClassifierAgent().run(state)
    assert result.incident.category == IncidentCategory.NETWORK


def test_classifies_database_category_from_keywords():
    state = _state_for("App errors", "The application cannot reach the postgres database, connection pool exhausted.")
    result = IncidentClassifierAgent().run(state)
    assert result.incident.category == IncidentCategory.DATABASE


def test_unknown_category_when_no_keywords_match():
    state = _state_for("Something odd", "Users say the page looks a little different today.")
    result = IncidentClassifierAgent().run(state)
    assert result.incident.category == IncidentCategory.UNKNOWN


def test_user_reported_severity_is_never_downgraded():
    state = _state_for("Minor issue", "Intermittent minor cosmetic glitch.", reported_severity=Severity.CRITICAL)
    result = IncidentClassifierAgent().run(state)
    assert result.incident.severity == Severity.CRITICAL
