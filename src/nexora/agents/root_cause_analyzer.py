"""Root Cause Analyzer agent.

Synthesizes collected evidence into a single most-probable root cause,
plausible alternatives, and named uncertainties. Confidence is a
heuristic function of how much corroborating evidence exists; it is
explicitly not a statistical probability.
"""

from __future__ import annotations

from nexora.agents.base import BaseAgent
from nexora.models.evidence import Evidence, EvidenceSource
from nexora.models.report import RootCause
from nexora.models.state import InvestigationState

# Ordered by specificity: the first matching rule wins.
_ROOT_CAUSE_RULES: list[tuple[str, str, float]] = [
    ("service_failed", "The upstream application service failed to start or crashed, causing requests to fail.", 0.85),
    ("config_error", "An application configuration error is preventing the service from starting correctly.", 0.8),
    ("connection_refused", "A downstream dependency refused the connection, most likely because it is not running or not listening on the expected port.", 0.75),
    ("dns_failure", "DNS resolution is failing for a required hostname.", 0.75),
    ("tls_error", "A TLS/SSL certificate problem is preventing secure connections from completing.", 0.75),
    ("db_connection_failure", "The application cannot establish a connection to its database.", 0.75),
    ("disk_full", "The host has exhausted available disk space, which is disrupting normal operation.", 0.8),
    ("oom", "The process was terminated due to memory exhaustion.", 0.8),
    ("auth_failure", "Requests are failing authentication, most likely due to invalid or expired credentials.", 0.7),
    ("port_conflict", "A port conflict is preventing the service from binding to its expected address.", 0.7),
    ("timeout", "A downstream dependency is timing out, suggesting it is overloaded or unreachable.", 0.6),
    ("permission_denied", "A file or resource permission problem is blocking the process from completing an operation.", 0.65),
]


class RootCauseAnalyzerAgent(BaseAgent):
    name = "root_cause_analyzer"

    def run(self, state: InvestigationState) -> InvestigationState:
        usable_evidence = [e for e in state.evidence if e.source != EvidenceSource.UNAVAILABLE]

        matched_cause: str | None = None
        matched_confidence = 0.0
        supporting: list[Evidence] = []

        for signal, cause_text, base_confidence in _ROOT_CAUSE_RULES:
            matches = [e for e in usable_evidence if signal in e.summary.lower()]
            if matches:
                matched_cause = cause_text
                matched_confidence = base_confidence
                supporting = matches
                break

        alternative_causes: list[str] = []
        if matched_cause:
            for signal, cause_text, _ in _ROOT_CAUSE_RULES:
                if cause_text != matched_cause and any(signal in e.summary.lower() for e in usable_evidence):
                    alternative_causes.append(cause_text)

        uncertainties: list[str] = []
        if not usable_evidence:
            matched_cause = (
                "NEEDS_MORE_EVIDENCE: insufficient evidence was available to determine a root cause. "
                "This reflects the limits of the information provided, not a confirmed absence of a cause."
            )
            matched_confidence = 0.0
            uncertainties.append("No usable evidence was collected during this investigation.")
        elif not matched_cause:
            matched_cause = (
                "NEEDS_MORE_EVIDENCE: evidence was collected but did not match a known failure pattern strongly enough "
                "to identify a specific root cause with confidence."
            )
            matched_confidence = 0.2
            uncertainties.append("Available evidence did not clearly indicate a single root cause.")
            supporting = usable_evidence

        if len(supporting) < 2:
            uncertainties.append("Root cause is supported by a single evidence record; corroborating evidence is limited.")

        root_cause = RootCause(
            root_cause=matched_cause,
            confidence=round(matched_confidence, 2),
            confidence_level=("high" if matched_confidence >= 0.8 else "medium" if matched_confidence >= 0.5 else "low"),
            supporting_evidence=supporting,
            alternative_causes=alternative_causes,
            uncertainties=uncertainties,
        )
        state.root_cause = root_cause
        state.log(f"{self.name}: root cause identified with confidence {root_cause.confidence}.")
        return state
