"""Application Agent.

Investigates framework signals, configuration errors, and environment
variable problems surfaced in application logs.
"""

from __future__ import annotations

from uuid import uuid4

from nexora.agents.base import BaseAgent
from nexora.models.diagnostic import AgentFinding
from nexora.models.evidence import Evidence, EvidenceReliability, EvidenceSource
from nexora.models.state import InvestigationState
from nexora.services.demo_data import get_demo_context
from nexora.tools.application_tools import (
    EnvironmentVariableCheckInput,
    EnvironmentVariableCheckTool,
    FrameworkDetectionInput,
    FrameworkDetectionTool,
)
from nexora.tools.log_tools import LogAnalysisTool, LogParseInput

_APPLICATION_SIGNALS = {"config_error", "service_failed", "http_5xx"}


class ApplicationAgent(BaseAgent):
    name = "application_agent"

    def run(self, state: InvestigationState) -> InvestigationState:
        incident = state.incident
        evidences: list[Evidence] = []
        log_text = incident.logs or (get_demo_context()["log_text"] if incident.use_demo_data else "")

        framework_result = FrameworkDetectionTool().execute(
            FrameworkDetectionInput(log_text=log_text), incident.incident_id
        )
        if not framework_result.data.get("unavailable"):
            frameworks = framework_result.data.get("frameworks_detected", [])
            if frameworks:
                evidences.append(
                    Evidence(
                        evidence_id=f"ev-{uuid4().hex[:8]}",
                        agent=self.name,
                        tool="framework_detection",
                        source=EvidenceSource.DEMO_FIXTURE if incident.use_demo_data else EvidenceSource.UPLOADED_LOG,
                        reliability=EvidenceReliability.MEDIUM,
                        summary=f"Framework signature(s) detected: {', '.join(frameworks)}.",
                    )
                )

        log_result = LogAnalysisTool().execute(LogParseInput(log_text=log_text), incident.incident_id)
        if not log_result.data.get("unavailable"):
            detected = [s for s in log_result.data.get("signals_detected", []) if s in _APPLICATION_SIGNALS]
            matched_lines = log_result.data.get("matched_lines", {})
            for signal in detected:
                evidences.append(
                    Evidence(
                        evidence_id=f"ev-{uuid4().hex[:8]}",
                        agent=self.name,
                        tool="log_analysis",
                        source=EvidenceSource.DEMO_FIXTURE if incident.use_demo_data else EvidenceSource.UPLOADED_LOG,
                        reliability=EvidenceReliability.HIGH,
                        summary=f"Application-level log signal '{signal}' detected.",
                        detail="; ".join(matched_lines.get(signal, [])) or None,
                    )
                )

        if incident.use_demo_data:
            demo = get_demo_context()
            env_result = EnvironmentVariableCheckTool().execute(
                EnvironmentVariableCheckInput(
                    required_vars=demo["required_env_vars"], provided_vars=demo["env_vars"]
                ),
                incident.incident_id,
            )
            if not env_result.data.get("unavailable"):
                empty = env_result.data.get("empty_vars", [])
                missing = env_result.data.get("missing_vars", [])
                if empty or missing:
                    evidences.append(
                        Evidence(
                            evidence_id=f"ev-{uuid4().hex[:8]}",
                            agent=self.name,
                            tool="environment_variable_check",
                            source=EvidenceSource.DEMO_FIXTURE,
                            reliability=EvidenceReliability.HIGH,
                            summary=(
                                f"Empty environment variable(s): {', '.join(empty)}."
                                if empty
                                else f"Missing environment variable(s): {', '.join(missing)}."
                            ),
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
                    summary="No application-layer evidence could be collected from the information provided.",
                )
            )

        state.evidence.extend(evidences)
        available = [e for e in evidences if e.source != EvidenceSource.UNAVAILABLE]
        summary = (
            "; ".join(e.summary for e in available)
            if available
            else "No application-level evidence could be collected."
        )
        confidence = 0.65 if available else 0.0
        state.agent_findings.append(
            AgentFinding(agent=self.name, summary=summary, evidence=evidences, confidence=confidence)
        )
        state.log(f"{self.name}: {summary}")
        return state
