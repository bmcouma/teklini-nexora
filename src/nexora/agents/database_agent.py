"""Database Agent.

Investigates database connectivity and pool-related signals from
provided logs. Never receives credentials and never executes SQL.
"""

from __future__ import annotations

from uuid import uuid4

from nexora.agents.base import BaseAgent
from nexora.models.diagnostic import AgentFinding
from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.state import InvestigationState
from nexora.tools.database_tools import DatabaseLogAnalysisInput, DatabaseLogAnalysisTool


class DatabaseAgent(BaseAgent):
    name = "database_agent"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        result = DatabaseLogAnalysisTool().execute(
            DatabaseLogAnalysisInput(log_text=incident.logs), incident.incident_id
        )

        evidences: list[Evidence] = []
        if result.data.get("unavailable"):
            evidences.append(
                Evidence(
                    evidence_id=f"ev-{uuid4().hex[:8]}",
                    agent=self.name,
                    tool="database_log_analysis",
                    source=EvidenceSource.UNAVAILABLE,
                    reliability=EvidenceReliability.UNAVAILABLE,
                    summary="No database-related log data was available for analysis.",
                )
            )
        else:
            signals = result.data.get("signals_detected", [])
            if signals:
                evidences.append(
                    Evidence(
                        evidence_id=f"ev-{uuid4().hex[:8]}",
                        agent=self.name,
                        tool="database_log_analysis",
                        source=EvidenceSource.UPLOADED_LOG,
                        reliability=EvidenceReliability.HIGH,
                        summary=f"Database failure signal(s) detected: {', '.join(signals)}.",
                    )
                )
            else:
                evidences.append(
                    Evidence(
                        evidence_id=f"ev-{uuid4().hex[:8]}",
                        agent=self.name,
                        tool="database_log_analysis",
                        source=EvidenceSource.UPLOADED_LOG,
                        reliability=EvidenceReliability.MEDIUM,
                        summary="No database failure signals found in the provided logs.",
                    )
                )

        state.evidence.extend(evidences)
        available = [e for e in evidences if e.source != EvidenceSource.UNAVAILABLE]
        summary = "; ".join(e.summary for e in evidences)
        confidence = 0.55 if available else 0.0
        state.agent_findings.append(
            AgentFinding(agent=self.name, summary=summary, evidence=evidences, confidence=confidence)
        )
        state.log(f"{self.name}: {summary}")
        return state
