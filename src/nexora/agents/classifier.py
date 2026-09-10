"""Incident Classifier agent.

Determines category, severity, and which specialized agents should be
engaged. Classification is evidence-driven: it looks at the incident
description, affected service, and any log text the user provided,
rather than guessing from the title alone.
"""

from __future__ import annotations

import re

from nexora.agents.base import BaseAgent
from nexora.models.incident import IncidentCategory, Severity
from nexora.models.state import InvestigationState

_CATEGORY_KEYWORDS: dict[IncidentCategory, list[str]] = {
    IncidentCategory.NETWORK: ["dns", "timeout", "connection refused", "tls", "ssl", "certificate", "502", "504", "gateway"],
    IncidentCategory.DATABASE: ["database", "postgres", "mysql", "connection pool", "migration", "sql"],
    IncidentCategory.AUTHENTICATION: ["authentication", "login", "401", "unauthorized", "credentials", "token expired"],
    IncidentCategory.SECURITY: ["security", "vulnerability", "exposed", "breach", "unauthorized access"],
    IncidentCategory.DEPLOYMENT: ["deploy", "ci/cd", "pipeline", "build failed", "release"],
    IncidentCategory.API: ["api", "endpoint", "rate limit", "422", "400 bad request"],
    IncidentCategory.PERFORMANCE: ["slow", "latency", "high cpu", "high memory", "performance"],
    IncidentCategory.INFRASTRUCTURE: ["disk", "docker", "container", "kubernetes", "service failed", "systemd"],
    IncidentCategory.APPLICATION: ["500", "internal server error", "exception", "traceback", "crash"],
}

_CRITICAL_TERMS = ["outage", "down", "critical", "all users", "production down", "data loss"]
_HIGH_TERMS = ["502", "503", "504", "500", "failing for", "most users"]
_LOW_TERMS = ["intermittent", "occasional", "minor", "cosmetic"]


class IncidentClassifierAgent(BaseAgent):
    name = "incident_classifier"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        corpus = " ".join(
            filter(
                None,
                [incident.title.lower(), incident.description.lower(), (incident.logs or "").lower()],
            )
        )

        category, category_score = self._classify_category(corpus)
        severity = self._classify_severity(corpus, incident.reported_severity)

        state.incident.category = category
        state.incident.severity = severity

        confidence_note = (
            f"Category '{category.value}' selected on {category_score} matched keyword(s)."
            if category_score
            else "No strong category signal found in the incident description; defaulting to 'unknown'."
        )
        state.log(
            f"Incident Classifier: category={category.value}, severity={severity.value}. {confidence_note}"
        )
        return state

    def _classify_category(self, corpus: str) -> tuple[IncidentCategory, int]:
        best_category = IncidentCategory.UNKNOWN
        best_score = 0
        for category, keywords in _CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in corpus)
            if score > best_score:
                best_score = score
                best_category = category
        return best_category, best_score

    def _classify_severity(self, corpus: str, reported: Severity | None) -> Severity:
        if any(re.search(rf"\b{re.escape(term)}\b", corpus) for term in _CRITICAL_TERMS):
            computed = Severity.CRITICAL
        elif any(term in corpus for term in _HIGH_TERMS):
            computed = Severity.HIGH
        elif any(term in corpus for term in _LOW_TERMS):
            computed = Severity.LOW
        else:
            computed = Severity.MEDIUM

        # A user-reported severity is evidence too. Never silently downgrade
        # a user's critical report; only ever escalate or match it.
        if reported is not None:
            order = [
                Severity.INFORMATIONAL,
                Severity.LOW,
                Severity.MEDIUM,
                Severity.HIGH,
                Severity.CRITICAL,
            ]
            return order[max(order.index(reported), order.index(computed))]
        return computed
