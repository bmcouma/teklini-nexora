from nexora.agents.classifier import IncidentClassifierAgent
from nexora.models.incident import Incident, Severity
from nexora.models.state import InvestigationState


def _classify(title: str, description: str, reported_severity=None) -> Severity:
    incident = Incident(title=title, description=description, reported_severity=reported_severity)
    state = InvestigationState(incident=incident)
    return IncidentClassifierAgent().run(state).incident.severity


def test_critical_terms_trigger_critical_severity():
    assert _classify("Production down", "Total outage, all users affected, production down.") == Severity.CRITICAL


def test_5xx_terms_trigger_high_severity():
    assert _classify("Errors", "The API is failing for most users with 502 errors.") == Severity.HIGH


def test_intermittent_terms_trigger_low_severity():
    assert _classify("Minor glitch", "Intermittent, minor, cosmetic issue on one page.") == Severity.LOW


def test_default_is_medium_without_strong_signal():
    assert _classify("Something changed", "A behavior changed recently and needs review.") == Severity.MEDIUM


def test_reported_severity_can_escalate_computed_severity():
    # Computed severity from this description alone would be MEDIUM, but the
    # user reported CRITICAL, so the result must reflect at least CRITICAL.
    result = _classify("Something changed", "A behavior changed recently.", reported_severity=Severity.CRITICAL)
    assert result == Severity.CRITICAL
