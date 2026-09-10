"""Nexora Orchestrator.

Coordinates the full investigation lifecycle. The orchestrator itself
performs no diagnostic reasoning; it routes work to the classifier,
planner, specialized agents, evidence reviewer, root cause analyzer,
remediation advisor, and report generator, and enforces the iteration
limits that prevent runaway loops.
"""

from __future__ import annotations

import logging

from nexora.agents.application_agent import ApplicationAgent
from nexora.agents.base import BaseAgent
from nexora.agents.classifier import IncidentClassifierAgent
from nexora.agents.database_agent import DatabaseAgent
from nexora.agents.evidence_reviewer import EvidenceReviewerAgent
from nexora.agents.gemini_reasoning import GeminiReasoningAgent
from nexora.agents.network_agent import NetworkAgent
from nexora.agents.planner import PlannerAgent
from nexora.agents.remediation_advisor import RemediationAdvisorAgent
from nexora.agents.report_generator import ReportGeneratorAgent
from nexora.agents.root_cause_analyzer import RootCauseAnalyzerAgent
from nexora.agents.security_agent import SecurityAgent
from nexora.agents.systems_agent import SystemsAgent
from nexora.config.settings import get_settings
from nexora.models.incident import Incident, InvestigationStage
from nexora.models.state import InvestigationState

logger = logging.getLogger("nexora.orchestrator")

_SPECIALIST_REGISTRY: dict[str, type[BaseAgent]] = {
    "network_agent": NetworkAgent,
    "systems_agent": SystemsAgent,
    "application_agent": ApplicationAgent,
    "database_agent": DatabaseAgent,
    "security_agent": SecurityAgent,
}


class NexoraOrchestrator:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._classifier = IncidentClassifierAgent()
        self._planner = PlannerAgent()
        self._reviewer = EvidenceReviewerAgent()
        self._root_cause_analyzer = RootCauseAnalyzerAgent()
        self._gemini_reasoning = GeminiReasoningAgent()
        self._remediation_advisor = RemediationAdvisorAgent()
        self._report_generator = ReportGeneratorAgent()

    def investigate(self, incident: Incident) -> InvestigationState:
        state = InvestigationState(incident=incident)
        state.reasoning_mode = "gemini_adk" if self._settings.llm_provider.lower() == "gemini" else "heuristic"
        state.log(f"Orchestrator: investigation started for {incident.incident_id}.")

        incident.stage = InvestigationStage.CLASSIFYING
        state = self._classifier.run(state)

        incident.stage = InvestigationStage.PLANNING
        state = self._planner.run(state)

        incident.stage = InvestigationStage.INVESTIGATING
        state = self._run_diagnostic_agents(state)

        state = self._review_loop(state)

        incident.stage = InvestigationStage.ROOT_CAUSE_ANALYSIS
        state = self._root_cause_analyzer.run(state)
        if self._settings.llm_provider.lower() == "gemini":
            state = self._gemini_reasoning.run(state)
        state = self._reviewer.review_conclusion(state)

        incident.stage = InvestigationStage.REMEDIATION
        state = self._remediation_advisor.run(state)

        requires_approval = any(r.requires_approval for r in state.recommendations)
        incident.stage = (
            InvestigationStage.AWAITING_APPROVAL if requires_approval else InvestigationStage.REPORT_READY
        )

        state = self._report_generator.run(state)
        if incident.stage != InvestigationStage.AWAITING_APPROVAL:
            incident.stage = InvestigationStage.REPORT_READY

        state.log("Orchestrator: investigation complete.")
        return state

    def _run_diagnostic_agents(self, state: InvestigationState) -> InvestigationState:
        if not state.diagnostic_plan:
            return state
        for task in state.diagnostic_plan.tasks:
            agent_cls = _SPECIALIST_REGISTRY.get(task.assigned_agent)
            if not agent_cls:
                task.status = "skipped"
                state.log(f"Orchestrator: no agent registered for '{task.assigned_agent}'; task skipped.")
                continue
            task.status = "in_progress"
            state = agent_cls().run(state)
            task.status = "completed"
        return state

    def _review_loop(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        max_review = self._settings.max_review_iterations
        max_diagnostic = self._settings.max_diagnostic_iterations

        incident.stage = InvestigationStage.REVIEWING
        state = self._reviewer.run(state)

        while (
            state.review_findings
            and not state.review_findings[-1].sufficient
            and incident.review_iteration_count < max_review
            and incident.iteration_count < max_diagnostic
        ):
            incident.review_iteration_count += 1
            incident.iteration_count += 1
            incident.stage = InvestigationStage.ADDITIONAL_INVESTIGATION
            state.log(
                f"Orchestrator: evidence insufficient, running additional investigation "
                f"(iteration {incident.iteration_count}/{max_diagnostic})."
            )
            state = self._run_diagnostic_agents(state)
            incident.stage = InvestigationStage.REVIEWING
            state = self._reviewer.run(state)

        if state.review_findings and not state.review_findings[-1].sufficient:
            state.log(
                "Orchestrator: proceeding to root cause analysis with available evidence after "
                "reaching the maximum investigation iterations."
            )

        return state
