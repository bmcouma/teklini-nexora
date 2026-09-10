from nexora.models.incident import Incident, IncidentCategory, InvestigationStage
from nexora.workflows.investigation_workflow import run_investigation


def test_demo_incident_reaches_report_ready_with_correct_root_cause():
    incident = Incident(
        title="Django application returns 502 Bad Gateway",
        description="Users report 502 errors. Nginx is reachable but upstream requests fail.",
        use_demo_data=True,
        logs=(
            "nginx: [error] connect() failed (111: Connection refused) while connecting to upstream\n"
            "gunicorn[3341]: ModuleNotFoundError: No module named 'config.settings'\n"
            "gunicorn[3341]: Worker failed to start.\n"
            "systemd: gunicorn.service: Failed with result 'exit-code'.\n"
        ),
    )
    state = run_investigation(incident)

    assert state.incident.stage == InvestigationStage.REPORT_READY
    assert state.incident.category in (IncidentCategory.NETWORK, IncidentCategory.APPLICATION)
    assert state.root_cause is not None
    assert "failed to start" in state.root_cause.root_cause.lower()
    assert state.final_report is not None
    assert state.final_report.is_demo_data is True
    assert len(state.recommendations) > 0


def test_investigation_with_no_evidence_still_completes_and_flags_uncertainty():
    incident = Incident(title="Vague report", description="Something feels off but no details are available.")
    state = run_investigation(incident)

    assert state.incident.stage == InvestigationStage.REPORT_READY
    assert state.root_cause is not None
    assert state.root_cause.confidence <= 0.2
    assert len(state.root_cause.uncertainties) > 0


def test_review_loop_respects_iteration_limits():
    incident = Incident(title="Unclear problem", description="No further detail is available for this incident.")
    run_investigation(incident)

    assert incident.iteration_count <= 3
    assert incident.review_iteration_count <= 2


def test_secrets_in_logs_are_redacted_before_reasoning():
    incident = Incident(
        title="Auth failure",
        description="Login attempts are failing.",
        logs="authentication failed\npassword=SuperSecretValue123\n",
    )
    state = run_investigation(incident)

    assert "SuperSecretValue123" not in (incident.logs or "")
    assert any("redacted" in line.lower() for line in state.activity_log)


def test_high_risk_recommendation_requires_approval_before_report_ready():
    incident = Incident(
        title="Repeated authentication failures",
        description="Many users are failing authentication and credentials may be compromised.",
        logs="authentication failed\nauthentication failed\nauthentication failed\n",
    )
    state = run_investigation(incident)

    high_risk = [r for r in state.recommendations if r.risk.value == "high"]
    if high_risk:
        assert incident.stage == InvestigationStage.AWAITING_APPROVAL
