"""Report Generator agent.

Assembles the final structured incident report. This agent does not
introduce any new claims; it only organizes what earlier agents already
recorded in the investigation state.
"""

from __future__ import annotations

from nexora.agents.base import BaseAgent
from nexora.models.evidence import EvidenceSource
from nexora.models.report import IncidentReport, RootCause
from nexora.models.state import InvestigationState


class ReportGeneratorAgent(BaseAgent):
    name = "report_generator"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        root_cause = state.root_cause or RootCause(
            root_cause="Investigation did not reach root cause analysis.",
            confidence=0.0,
        )

        observed_symptoms = [incident.description]
        known_facts = state.diagnostic_plan.known_facts if state.diagnostic_plan else [incident.description]
        investigation_performed = [
            f"{finding.agent}: {finding.summary}" for finding in state.agent_findings
        ]

        security_considerations = [
            e.summary for e in state.evidence if e.agent == "security_agent"
        ] or ["No dedicated security findings were generated for this incident."]

        remaining_uncertainty = list(root_cause.uncertainties)
        for review in state.review_findings:
            remaining_uncertainty.extend(review.missing_evidence)

        report = IncidentReport(
            incident_id=incident.incident_id,
            incident_summary=incident.title,
            severity=incident.severity,
            category=incident.category,
            affected_system=incident.affected_service,
            observed_symptoms=observed_symptoms,
            known_facts=known_facts,
            evidence_collected=[e for e in state.evidence if e.source != EvidenceSource.UNAVAILABLE],
            investigation_performed=investigation_performed,
            root_cause=root_cause,
            recommended_resolution=state.recommendations,
            verification_steps=[
                "Re-run the failing request or workflow after applying the recommended fix.",
                "Confirm the previously failing service or endpoint returns a healthy response.",
                "Monitor logs for a short period to confirm the error signal does not recur.",
            ],
            security_considerations=security_considerations,
            remaining_uncertainty=sorted(set(remaining_uncertainty)),
            is_demo_data=incident.use_demo_data,
        )
        state.final_report = report
        state.log(f"{self.name}: incident report generated.")
        return state
