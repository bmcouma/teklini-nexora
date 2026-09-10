"""Evidence Reviewer agent.

This agent's job is to be skeptical. It looks at what has been
collected so far and decides whether the investigation has enough to
proceed to root cause analysis, or whether it should be sent back for
additional investigation. It never rubber-stamps a finding.
"""

from __future__ import annotations

from nexora.agents.base import BaseAgent
from nexora.models.diagnostic import ReviewFinding
from nexora.models.evidence import EvidenceSource
from nexora.models.state import InvestigationState

_STOP_WORDS = {
    "a", "an", "and", "are", "be", "by", "caused", "due", "for", "from", "in", "is",
    "of", "on", "or", "the", "to", "was", "with", "this", "that", "most", "likely",
}


class EvidenceReviewerAgent(BaseAgent):
    name = "evidence_reviewer"

    def run(self, state: InvestigationState) -> InvestigationState:
        usable_evidence = [e for e in state.evidence if e.source != EvidenceSource.UNAVAILABLE]
        missing_evidence = [
            e.summary for e in state.evidence if e.source == EvidenceSource.UNAVAILABLE
        ]

        unsupported_claims: list[str] = []
        contradictions: list[str] = []
        assumptions: list[str] = []
        evidence_ids = {e.evidence_id for e in state.evidence}
        for finding in state.agent_findings:
            if finding.confidence > 0 and not finding.evidence:
                unsupported_claims.append(f"{finding.agent} reported a finding with no supporting evidence.")
            unknown_ids = [e.evidence_id for e in finding.evidence if e.evidence_id not in evidence_ids]
            if unknown_ids:
                unsupported_claims.append(
                    f"{finding.agent} referenced evidence not present in the investigation: {', '.join(unknown_ids)}."
                )
            if any(term in f"{finding.summary} {finding.notes or ''}".lower() for term in ("assume", "probably", "likely")):
                assumptions.append(f"{finding.agent} uses probabilistic language that requires corroboration.")

        summaries = " ".join(f.summary.lower() for f in state.agent_findings)
        if "healthy" in summaries and ("failed" in summaries or "unavailable" in summaries):
            contradictions.append("Findings contain both healthy and failed or unavailable signals; reconcile the source data.")

        sufficient = len(usable_evidence) > 0 and not unsupported_claims and not contradictions

        if sufficient:
            justification = (
                f"{len(usable_evidence)} usable evidence record(s) collected across "
                f"{len({e.agent for e in usable_evidence})} agent(s), with no unsupported claims or contradictions detected."
            )
            recommendation = "proceed"
        else:
            if not usable_evidence:
                justification = "No usable evidence has been collected yet; all sources reported unavailable."
            else:
                problems = unsupported_claims + contradictions
                justification = "Evidence review found issues: " + " ".join(problems)
            recommendation = "additional_investigation"

        review = ReviewFinding(
            sufficient=sufficient,
            justification=justification,
            missing_evidence=missing_evidence,
            unsupported_claims=unsupported_claims,
            contradictions=contradictions,
            assumptions=assumptions,
            recommendation=recommendation,
        )
        state.review_findings.append(review)
        state.log(f"{self.name}: sufficient={sufficient}. {justification}")
        return state

    def review_conclusion(self, state: InvestigationState) -> InvestigationState:
        """Challenge the proposed root cause after deterministic or Gemini reasoning."""
        root_cause = state.root_cause
        if root_cause is None:
            state.review_findings.append(
                ReviewFinding(
                    sufficient=False,
                    justification="No root-cause conclusion was produced.",
                    missing_evidence=["A structured root-cause conclusion is required."],
                    conclusion_status="needs_more_evidence",
                    recommendation="additional_investigation",
                )
            )
            return state

        evidence_by_id = {item.evidence_id: item for item in state.evidence}
        unsupported: list[str] = []
        assumptions = list(root_cause.uncertainties)
        supporting = root_cause.supporting_evidence
        if root_cause.root_cause.startswith("NEEDS_MORE_EVIDENCE"):
            assumptions.append("The proposed conclusion explicitly reports insufficient evidence.")
        if not supporting and not root_cause.root_cause.startswith("NEEDS_MORE_EVIDENCE"):
            unsupported.append("The proposed root cause has no supporting evidence.")
        if any(item.evidence_id not in evidence_by_id for item in supporting):
            unsupported.append("The proposed root cause references evidence outside the investigation.")

        claim_tokens = self._tokens(root_cause.root_cause)
        evidence_text = " ".join(
            f"{item.summary} {item.detail or ''}" for item in supporting if item.evidence_id in evidence_by_id
        )
        evidence_tokens = self._tokens(evidence_text)
        known_equivalents = {
            "database": {"db", "database", "schema"},
            "dependency": {"connection", "refused", "timeout"},
            "dns": {"dns", "hostname", "nxdomain"},
            "tls": {"tls", "ssl", "certificate"},
            "memory": {"memory", "oom"},
            "disk": {"disk", "space"},
            "authentication": {"authentication", "credentials", "401"},
        }
        related = bool(claim_tokens & evidence_tokens)
        related = related or any(
            claim_term in claim_tokens and equivalents & evidence_tokens
            for claim_term, equivalents in known_equivalents.items()
        )
        if state.reasoning_mode == "gemini_adk" and supporting and not related:
            unsupported.append("Supporting evidence was cited but does not share a recognizable signal with the conclusion.")

        sufficient = not unsupported and bool(supporting)
        if root_cause.root_cause.startswith("NEEDS_MORE_EVIDENCE"):
            sufficient = False
        status = "supported" if sufficient else "needs_more_evidence"
        justification = (
            "The proposed conclusion is supported by cited evidence."
            if sufficient
            else "Conclusion review found: " + " ".join(unsupported)
        )
        state.review_findings.append(
            ReviewFinding(
                sufficient=sufficient,
                justification=justification,
                unsupported_claims=unsupported,
                assumptions=assumptions,
                conclusion_status=status,
                recommendation="proceed" if sufficient else "additional_investigation",
            )
        )
        if not sufficient:
            root_cause.root_cause = "NEEDS_MORE_EVIDENCE: " + root_cause.root_cause
            root_cause.confidence = 0.0
            root_cause.confidence_level = "low"
            root_cause.uncertainties.append("Post-reasoning evidence review did not support the proposed diagnosis.")
        state.log(f"{self.name}: conclusion status={status}.")
        return state

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            token
            for token in value.lower().replace("_", " ").replace("-", " ").split()
            if token not in _STOP_WORDS and len(token) > 2
        }
