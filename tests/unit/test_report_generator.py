from nexora.agents.report_generator import ReportGeneratorAgent
from nexora.models.diagnostic import AgentFinding
from nexora.models.evidence import DiagnosticPlan, Evidence, EvidenceReliability, EvidenceSource
from nexora.models.incident import Incident
from nexora.models.report import Recommendation, RiskLevel, RootCause
from nexora.models.state import InvestigationState


def _base_state() -> InvestigationState:
    incident = Incident(title="Service down", description="The service is returning errors.")
    state = InvestigationState(incident=incident)
    state.diagnostic_plan = DiagnosticPlan(objective="Investigate", known_facts=[incident.description])
    evidence = Evidence(
        evidence_id="ev-1",
        agent="network_agent",
        source=EvidenceSource.UPLOADED_LOG,
        reliability=EvidenceReliability.HIGH,
        summary="Connection refused detected.",
    )
    state.evidence.append(evidence)
    state.agent_findings.append(
        AgentFinding(agent="network_agent", summary="Connection refused detected.", evidence=[evidence], confidence=0.7)
    )
    state.root_cause = RootCause(root_cause="A downstream dependency refused the connection.", confidence=0.75, supporting_evidence=[evidence])
    state.recommendations = [
        Recommendation(action="Check the dependency's status.", risk=RiskLevel.LOW, rationale="Read-only step."),
    ]
    return state


def test_report_includes_root_cause_and_evidence():
    state = _base_state()
    result = ReportGeneratorAgent().run(state)
    report = result.final_report
    assert report is not None
    assert report.root_cause.root_cause == "A downstream dependency refused the connection."
    assert len(report.evidence_collected) == 1
    assert report.evidence_collected[0].evidence_id == "ev-1"


def test_report_excludes_unavailable_evidence_from_evidence_collected():
    state = _base_state()
    state.evidence.append(
        Evidence(
            evidence_id="ev-2",
            agent="database_agent",
            source=EvidenceSource.UNAVAILABLE,
            reliability=EvidenceReliability.UNAVAILABLE,
            summary="No database data available.",
        )
    )
    result = ReportGeneratorAgent().run(state)
    ids = [e.evidence_id for e in result.final_report.evidence_collected]
    assert "ev-2" not in ids
    assert "ev-1" in ids


def test_report_marks_demo_data_flag():
    state = _base_state()
    state.incident.use_demo_data = True
    result = ReportGeneratorAgent().run(state)
    assert result.final_report.is_demo_data is True


def test_report_handles_missing_root_cause_gracefully():
    incident = Incident(title="Unclear issue", description="Investigation was inconclusive.")
    state = InvestigationState(incident=incident)
    result = ReportGeneratorAgent().run(state)
    assert result.final_report is not None
    assert result.final_report.root_cause.confidence == 0.0
