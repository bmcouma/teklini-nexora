"""Network Agent.

Investigates DNS, connectivity, TLS, and HTTP-layer signals. Prefers
signals extracted from user-provided logs (which reflect what actually
happened) over live checks, since a live check against an arbitrary
user-described host may not be reachable from Nexora's environment at
all in this version.
"""

from __future__ import annotations

from uuid import uuid4

from nexora.agents.base import BaseAgent
from nexora.models.diagnostic import AgentFinding
from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.state import InvestigationState
from nexora.tools.base import ToolResult
from nexora.tools.log_tools import LogAnalysisTool, LogParseInput

_NETWORK_SIGNALS = {"http_5xx", "connection_refused", "connection_reset", "timeout", "dns_failure", "tls_error", "port_conflict"}


class NetworkAgent(BaseAgent):
    name = "network_agent"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        result: ToolResult = LogAnalysisTool().execute(
            LogParseInput(log_text=incident.logs or ""), incident.incident_id
        )

        if result.data.get("unavailable"):
            evidence = Evidence(
                evidence_id=f"ev-{uuid4().hex[:8]}",
                agent=self.name,
                tool="log_analysis",
                source=EvidenceSource.UNAVAILABLE,
                reliability=EvidenceReliability.UNAVAILABLE,
                summary="No log data was available for network-layer analysis.",
            )
            state.evidence.append(evidence)
            state.agent_findings.append(
                AgentFinding(
                    agent=self.name,
                    summary="No network-layer evidence could be collected from the information provided.",
                    evidence=[evidence],
                    confidence=0.0,
                )
            )
            state.log(f"{self.name}: no log data provided; network analysis unavailable.")
            return state

        detected = [s for s in result.data.get("signals_detected", []) if s in _NETWORK_SIGNALS]
        matched_lines = result.data.get("matched_lines", {})

        evidences: list[Evidence] = []
        for signal in detected:
            sample_lines = matched_lines.get(signal, [])
            evidence = Evidence(
                evidence_id=f"ev-{uuid4().hex[:8]}",
                agent=self.name,
                tool="log_analysis",
                source=EvidenceSource.DEMO_FIXTURE if incident.use_demo_data else EvidenceSource.UPLOADED_LOG,
                reliability=EvidenceReliability.HIGH,
                summary=f"Log signal '{signal}' detected {len(sample_lines)} time(s).",
                detail="; ".join(sample_lines) if sample_lines else None,
            )
            evidences.append(evidence)

        state.evidence.extend(evidences)

        if evidences:
            summary = f"Network-layer signals detected: {', '.join(detected)}."
            confidence = min(0.4 + 0.15 * len(detected), 0.9)
        else:
            summary = "No network-layer failure signals were found in the provided logs."
            confidence = 0.5

        state.agent_findings.append(
            AgentFinding(agent=self.name, summary=summary, evidence=evidences, confidence=confidence)
        )
        state.log(f"{self.name}: {summary}")
        return state
