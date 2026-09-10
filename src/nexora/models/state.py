"""Shared investigation state.

This is the single object that flows through the orchestrator and every
agent. Agents read what they need from it and append their own
contributions; they do not mutate each other's sections. No secrets are
ever stored in this object.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from nexora.models.diagnostic import AgentFinding, ReviewFinding
from nexora.models.evidence import DiagnosticPlan, Evidence
from nexora.models.incident import Incident
from nexora.models.report import IncidentReport, Recommendation, RootCause


class InvestigationState(BaseModel):
    incident: Incident
    diagnostic_plan: DiagnosticPlan | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    agent_findings: list[AgentFinding] = Field(default_factory=list)
    review_findings: list[ReviewFinding] = Field(default_factory=list)
    root_cause: RootCause | None = None
    recommendations: list[Recommendation] = Field(default_factory=list)
    final_report: IncidentReport | None = None
    activity_log: list[str] = Field(default_factory=list)
    reasoning_mode: str = "heuristic"
    reasoning_status: str = "not_used"
    reasoning_error: str | None = None

    def log(self, message: str) -> None:
        self.activity_log.append(message)
