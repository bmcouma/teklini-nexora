import pytest

from nexora.config.settings import get_settings
from nexora.models.incident import Incident
from nexora.workflows.investigation_workflow import run_investigation

pytestmark = pytest.mark.live_gemini


def test_live_gemini_adk_smoke(monkeypatch):
    """Opt-in provider smoke test; never collected by the standard suite."""
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.google_api_key:
        pytest.skip("GOOGLE_API_KEY is not configured in the local environment")

    assert settings.gemini_timeout_seconds > 0
    assert settings.gemini_timeout_seconds <= 60

    state = run_investigation(
        Incident(
            title="Live Gemini smoke test",
            description="Verify the configured ADK/Gemini provider with deterministic demo evidence.",
            use_demo_data=True,
        )
    )

    if state.reasoning_status != "completed":
        pytest.fail(
            "Gemini/ADK provider failed: "
            f"status={state.reasoning_status}; error={state.reasoning_error or 'unknown provider failure'}"
        )
    assert state.reasoning_mode == "gemini_adk"
    assert state.root_cause is not None
