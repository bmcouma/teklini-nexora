"""Planner agent.

Builds a diagnostic plan mapping the classified incident to a bounded
set of tasks for specialized agents. The planner deliberately keeps the
plan small: only agents relevant to the classified category (plus
application and systems, which are broadly useful for most incidents)
are engaged.
"""

from __future__ import annotations

from nexora.agents.base import BaseAgent
from nexora.models.evidence import DiagnosticPlan, DiagnosticTask
from nexora.models.incident import IncidentCategory
from nexora.models.state import InvestigationState

_AGENT_BY_CATEGORY: dict[IncidentCategory, list[str]] = {
    IncidentCategory.NETWORK: ["network_agent", "application_agent"],
    IncidentCategory.DATABASE: ["database_agent", "application_agent"],
    IncidentCategory.AUTHENTICATION: ["security_agent", "application_agent"],
    IncidentCategory.SECURITY: ["security_agent"],
    IncidentCategory.DEPLOYMENT: ["application_agent", "systems_agent"],
    IncidentCategory.API: ["network_agent", "application_agent"],
    IncidentCategory.PERFORMANCE: ["systems_agent", "application_agent"],
    IncidentCategory.INFRASTRUCTURE: ["systems_agent"],
    IncidentCategory.APPLICATION: ["application_agent", "systems_agent"],
    IncidentCategory.UNKNOWN: ["application_agent", "systems_agent", "network_agent"],
}

_TASK_OBJECTIVES: dict[str, str] = {
    "network_agent": "Determine whether DNS, TCP connectivity, TLS, or HTTP responses show signs of failure.",
    "systems_agent": "Determine whether host-level services or resource exhaustion contributed to the incident.",
    "application_agent": "Determine whether the application framework, configuration, or dependencies are implicated.",
    "database_agent": "Determine whether database connectivity, authentication, or pool exhaustion is implicated.",
    "security_agent": "Determine whether an authentication, credential, or configuration weakness is implicated.",
}


class PlannerAgent(BaseAgent):
    name = "planner"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        agent_names = _AGENT_BY_CATEGORY.get(incident.category, ["application_agent", "systems_agent"])

        tasks = [
            DiagnosticTask(
                task_id=f"task-{idx + 1}",
                objective=_TASK_OBJECTIVES[agent_name],
                assigned_agent=agent_name,
                required_tools=[],
                validation_criteria="At least one piece of evidence, or an explicit unavailable marker, is recorded.",
            )
            for idx, agent_name in enumerate(agent_names)
        ]

        plan = DiagnosticPlan(
            objective=f"Investigate: {incident.title}",
            known_facts=[incident.description],
            unknowns=["Root cause has not yet been established."],
            hypotheses=[],
            tasks=tasks,
            stopping_conditions=[
                "Evidence Reviewer confirms sufficient evidence has been collected.",
                "Maximum diagnostic iterations reached.",
            ],
        )
        state.diagnostic_plan = plan
        state.log(f"Planner: diagnostic plan created with {len(tasks)} task(s): {', '.join(agent_names)}.")
        return state
