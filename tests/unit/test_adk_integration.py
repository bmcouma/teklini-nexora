from nexora.agents.gemini_reasoning import GeminiReasoningAgent
from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.incident import Incident
from nexora.models.state import InvestigationState


def test_adk_module_defines_real_runner_path():
    source = __import__("inspect").getsource(GeminiReasoningAgent._run_adk)
    assert "LlmAgent" in source
    assert "InMemoryRunner" in source
    assert "run_async" in source


def test_gemini_provider_failure_falls_back_without_raising(monkeypatch):
    state = InvestigationState(
        incident=Incident(title="Incident", description="Description"),
        evidence=[
            Evidence(
                evidence_id="ev-1",
                agent="application_agent",
                source=EvidenceSource.TOOL_EXECUTION,
                reliability=EvidenceReliability.HIGH,
                summary="Service failed to start.",
            )
        ],
    )
    agent = GeminiReasoningAgent()
    monkeypatch.setattr(agent, "_run_adk", lambda *_: (_ for _ in ()).throw(TimeoutError("test timeout")))

    result = agent.run(state)

    assert result.reasoning_mode == "gemini_adk"
    assert result.reasoning_status == "fallback_deterministic"
    assert result.reasoning_error
