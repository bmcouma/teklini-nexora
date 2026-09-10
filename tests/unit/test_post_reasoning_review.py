from nexora.agents.evidence_reviewer import EvidenceReviewerAgent
from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.incident import Incident
from nexora.models.report import RootCause
from nexora.models.state import InvestigationState


def _state() -> InvestigationState:
    evidence = Evidence(
        evidence_id="ev-1",
        agent="application_agent",
        source=EvidenceSource.TOOL_EXECUTION,
        reliability=EvidenceReliability.HIGH,
        summary="Connection refused detected.",
    )
    return InvestigationState(
        incident=Incident(title="Service down", description="Requests fail."),
        evidence=[evidence],
        root_cause=RootCause(
            root_cause="The database schema is corrupted.",
            confidence=0.8,
            confidence_level="high",
            supporting_evidence=[evidence],
        ),
        reasoning_mode="gemini_adk",
    )


def test_post_reasoning_review_downgrades_unrelated_gemini_claim():
    state = _state()
    result = EvidenceReviewerAgent().review_conclusion(state)

    assert result.review_findings[-1].sufficient is False
    assert result.review_findings[-1].conclusion_status == "needs_more_evidence"
    assert result.root_cause is not None
    assert result.root_cause.root_cause.startswith("NEEDS_MORE_EVIDENCE")
    assert result.root_cause.confidence_level == "low"
