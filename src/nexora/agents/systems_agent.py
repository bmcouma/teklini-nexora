"""Systems Agent.

Investigates host-level service state and resource exhaustion. Nexora
does not run an agent on customer infrastructure in this version, so
structured service/resource data is only available in demo mode or when
a future upload endpoint supplies it. Outside of that, this agent
extracts what it can from log text and otherwise records evidence as
explicitly unavailable rather than guessing.
"""

from __future__ import annotations

from uuid import uuid4

from nexora.agents.base import BaseAgent
from nexora.models.diagnostic import AgentFinding
from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.state import InvestigationState
from nexora.services.demo_data import get_demo_context
from nexora.tools.log_tools import LogAnalysisTool, LogParseInput
from nexora.tools.system_tools import (
    ResourceInspectionTool,
    ResourceMetricsInput,
    ServiceStatusInput,
    ServiceStatusTool,
)

_SYSTEM_SIGNALS = {"disk_full", "oom", "service_failed", "permission_denied"}


class SystemsAgent(BaseAgent):
    name = "systems_agent"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        evidences: list[Evidence] = []

        if incident.use_demo_data:
            demo = get_demo_context()

            service_result = ServiceStatusTool().execute(
                ServiceStatusInput(services=demo["services"]), incident.incident_id
            )
            if not service_result.data.get("unavailable"):
                failed = service_result.data.get("failed_services", [])
                evidences.append(
                    Evidence(
                        evidence_id=f"ev-{uuid4().hex[:8]}",
                        agent=self.name,
                        tool="service_status_inspection",
                        source=EvidenceSource.DEMO_FIXTURE,
                        reliability=EvidenceReliability.HIGH,
                        summary=(
                            f"Failed service(s) detected: {', '.join(failed)}."
                            if failed
                            else "All checked services report running."
                        ),
                        detail=str(service_result.data.get("services")),
                    )
                )

            resource_result = ResourceInspectionTool().execute(
                ResourceMetricsInput(**demo["resources"]), incident.incident_id
            )
            if not resource_result.data.get("unavailable"):
                warnings = resource_result.data.get("warnings", [])
                evidences.append(
                    Evidence(
                        evidence_id=f"ev-{uuid4().hex[:8]}",
                        agent=self.name,
                        tool="resource_inspection",
                        source=EvidenceSource.DEMO_FIXTURE,
                        reliability=EvidenceReliability.HIGH,
                        summary=(
                            "; ".join(warnings)
                            if warnings
                            else "Resource utilization is within normal thresholds."
                        ),
                    )
                )

        log_result = LogAnalysisTool().execute(
            LogParseInput(log_text=incident.logs or ""), incident.incident_id
        )
        if not log_result.data.get("unavailable"):
            detected = [s for s in log_result.data.get("signals_detected", []) if s in _SYSTEM_SIGNALS]
            matched_lines = log_result.data.get("matched_lines", {})
            for signal in detected:
                evidences.append(
                    Evidence(
                        evidence_id=f"ev-{uuid4().hex[:8]}",
                        agent=self.name,
                        tool="log_analysis",
                        source=EvidenceSource.UPLOADED_LOG,
                        reliability=EvidenceReliability.HIGH,
                        summary=f"System-level log signal '{signal}' detected.",
                        detail="; ".join(matched_lines.get(signal, [])) or None,
                    )
                )

        if not evidences:
            evidences.append(
                Evidence(
                    evidence_id=f"ev-{uuid4().hex[:8]}",
                    agent=self.name,
                    tool=None,
                    source=EvidenceSource.UNAVAILABLE,
                    reliability=EvidenceReliability.UNAVAILABLE,
                    summary=(
                        "No host-level service or resource data is available. Nexora has no live "
                        "agent installed on this host in this version."
                    ),
                )
            )

        state.evidence.extend(evidences)
        available = [e for e in evidences if e.source != EvidenceSource.UNAVAILABLE]
        summary = (
            "; ".join(e.summary for e in available)
            if available
            else "No system-level evidence could be collected."
        )
        confidence = 0.6 if available else 0.0
        state.agent_findings.append(
            AgentFinding(agent=self.name, summary=summary, evidence=evidences, confidence=confidence)
        )
        state.log(f"{self.name}: {summary}")
        return state
