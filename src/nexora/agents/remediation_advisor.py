"""Remediation Advisor agent.

Translates the identified root cause into concrete, risk-tiered
recommendations. High-risk actions are always flagged as requiring
explicit human approval; Nexora never executes them automatically.
"""

from __future__ import annotations

from nexora.agents.base import BaseAgent
from nexora.models.report import Recommendation, RiskLevel
from nexora.models.state import InvestigationState

_REMEDIATION_MAP: list[tuple[str, list[Recommendation]]] = [
    ("failed to start", [
        Recommendation(action="Inspect the application service's startup logs for the specific error.", risk=RiskLevel.LOW, rationale="Read-only investigation step."),
        Recommendation(action="Verify the application's configuration module and environment variables are correct.", risk=RiskLevel.LOW, rationale="Configuration errors are a common cause of startup failure."),
        Recommendation(action="Restart the failed service once the underlying configuration issue is fixed.", risk=RiskLevel.MEDIUM, rationale="Restarting before fixing the root cause will likely reproduce the failure."),
    ]),
    ("configuration error", [
        Recommendation(action="Compare the current environment configuration against a known-good deployment.", risk=RiskLevel.LOW, rationale="Read-only comparison."),
        Recommendation(action="Correct the identified missing or invalid configuration value.", risk=RiskLevel.MEDIUM, rationale="Requires a configuration change to the running environment."),
    ]),
    ("disk space", [
        Recommendation(action="Check available disk space on the affected host.", risk=RiskLevel.LOW, rationale="Read-only investigation step."),
        Recommendation(action="Clear unnecessary log files, temp files, or old build artifacts.", risk=RiskLevel.MEDIUM, rationale="Deletes data; verify nothing required is removed."),
    ]),
    ("memory exhaustion", [
        Recommendation(action="Review recent memory usage trends for the affected process.", risk=RiskLevel.LOW, rationale="Read-only investigation step."),
        Recommendation(action="Increase available memory or adjust process memory limits.", risk=RiskLevel.MEDIUM, rationale="Requires an infrastructure or configuration change."),
    ]),
    ("database", [
        Recommendation(action="Verify database connectivity and credentials from the application host.", risk=RiskLevel.LOW, rationale="Read-only investigation step."),
        Recommendation(action="Increase the database connection pool size if utilization is near exhaustion.", risk=RiskLevel.MEDIUM, rationale="Requires a configuration change."),
        Recommendation(action="Modify database schema, users, or firewall rules.", risk=RiskLevel.HIGH, rationale="Directly affects a shared, stateful system.", requires_approval=True),
    ]),
    ("dns", [
        Recommendation(action="Verify the DNS record for the affected hostname resolves correctly.", risk=RiskLevel.LOW, rationale="Read-only investigation step."),
        Recommendation(action="Update the DNS record or resolver configuration.", risk=RiskLevel.MEDIUM, rationale="Requires a DNS configuration change."),
    ]),
    ("tls", [
        Recommendation(action="Confirm the certificate expiry date and issuing authority.", risk=RiskLevel.LOW, rationale="Read-only investigation step."),
        Recommendation(action="Renew or replace the expired or invalid TLS certificate.", risk=RiskLevel.MEDIUM, rationale="Requires a certificate change on the affected service."),
    ]),
    ("authentication", [
        Recommendation(action="Confirm whether credentials in use are current and correctly scoped.", risk=RiskLevel.LOW, rationale="Read-only investigation step."),
        Recommendation(action="Rotate the affected credentials.", risk=RiskLevel.HIGH, rationale="Credential rotation can affect other systems depending on the same credential.", requires_approval=True),
    ]),
]

_DEFAULT_RECOMMENDATIONS = [
    Recommendation(
        action="Gather additional diagnostic information (logs, metrics, or configuration) for the affected system.",
        risk=RiskLevel.LOW,
        rationale="Read-only investigation step; current evidence is insufficient to recommend a specific fix.",
    ),
]


class RemediationAdvisorAgent(BaseAgent):
    name = "remediation_advisor"

    def run(self, state: InvestigationState) -> InvestigationState:
        root_cause_text = (state.root_cause.root_cause if state.root_cause else "").lower()

        recommendations: list[Recommendation] = []
        for keyword, actions in _REMEDIATION_MAP:
            if keyword in root_cause_text:
                recommendations = actions
                break

        if not recommendations:
            recommendations = _DEFAULT_RECOMMENDATIONS

        state.recommendations = recommendations
        high_risk = [r for r in recommendations if r.risk == RiskLevel.HIGH]
        state.log(
            f"{self.name}: {len(recommendations)} recommendation(s) generated"
            + (f", {len(high_risk)} requiring approval." if high_risk else ".")
        )
        return state
