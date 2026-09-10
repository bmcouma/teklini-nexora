"""Security Agent.

Identifies defensive, read-only security signals: authentication
failures and missing recommended HTTP security headers. Performs no
offensive or destructive testing.
"""

from __future__ import annotations

from uuid import uuid4

from nexora.agents.base import BaseAgent
from nexora.models.diagnostic import AgentFinding
from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.state import InvestigationState
from nexora.tools.security_tools import AuthFailureAnalysisInput, AuthFailureAnalysisTool


class SecurityAgent(BaseAgent):
    name = "security_agent"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        result = AuthFailureAnalysisTool().execute(
            AuthFailureAnalysisInput(log_text=incident.logs), incident.incident_id
        )

        evidences: list[Evidence] = []
        if result.data.get("unavailable"):
            evidences.append(
                Evidence(
                    evidence_id=f"ev-{uuid4().hex[:8]}",
                    agent=self.name,
                    tool="auth_failure_analysis",
                    source=EvidenceSource.UNAVAILABLE,
                    reliability=EvidenceReliability.UNAVAILABLE,
                    summary="No log data was available for security analysis.",
                )
            )
        else:
            mentions = result.data.get("auth_failure_mentions", 0)
            evidences.append(
                Evidence(
                    evidence_id=f"ev-{uuid4().hex[:8]}",
                    agent=self.name,
                    tool="auth_failure_analysis",
                    source=EvidenceSource.UPLOADED_LOG,
                    reliability=EvidenceReliability.HIGH,
                    summary=(
                        f"{mentions} authentication failure mention(s) found in provided logs."
                        if mentions
                        else "No authentication failure signals found in the provided logs."
                    ),
                )
            )

        state.evidence.extend(evidences)
        available = [e for e in evidences if e.source != EvidenceSource.UNAVAILABLE]
        summary = "; ".join(e.summary for e in evidences)
        confidence = 0.5 if available else 0.0
        state.agent_findings.append(
            AgentFinding(agent=self.name, summary=summary, evidence=evidences, confidence=confidence)
        )
        state.log(f"{self.name}: {summary}")
        return state
