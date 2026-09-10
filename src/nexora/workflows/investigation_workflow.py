"""Investigation workflow entry point.

This module is the boundary between the service/API layer and the
agent orchestration layer. It exists so that callers (the API, tests,
a future CLI) depend on a stable workflow function rather than
reaching into orchestrator internals directly.
"""

from __future__ import annotations

from nexora.agents.orchestrator import NexoraOrchestrator
from nexora.models.incident import Incident
from nexora.models.state import InvestigationState
from nexora.security.redaction import redact_secrets


def run_investigation(incident: Incident) -> InvestigationState:
    """Redact secrets from user-provided logs, then run the full investigation."""
    redacted_pattern_count = 0
    if incident.logs:
        redacted_logs, matched_patterns = redact_secrets(incident.logs)
        incident.logs = redacted_logs
        redacted_pattern_count = len(matched_patterns)

    orchestrator = NexoraOrchestrator()
    state = orchestrator.investigate(incident)

    if redacted_pattern_count:
        # Appended after investigate() so it lands in the activity log without
        # needing to thread redaction details through the orchestrator itself.
        state.activity_log.insert(
            1,
            f"Security: redacted {redacted_pattern_count} potential secret pattern(s) "
            "from submitted logs before analysis.",
        )

    return state
