"""Evaluation harness.

Runs the full investigation workflow against the evaluation dataset and
reports the metrics called out in the project's evaluation principles:
classification accuracy, root cause keyword accuracy, unsupported-claim
rate, and recommendation safety (no high-risk recommendation should ever
be marked as not requiring approval).

Run with: python -m nexora.evaluation.run_eval
"""

from __future__ import annotations

import time

from nexora.evaluation.dataset import EVALUATION_CASES
from nexora.models.incident import Incident
from nexora.models.report import RiskLevel
from nexora.workflows.investigation_workflow import run_investigation


class CaseResult:
    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        self.category_correct = False
        self.root_cause_keyword_found = False
        self.unsupported_claim_count = 0
        self.unsafe_recommendation_count = 0
        self.duration_ms = 0.0


def evaluate() -> list[CaseResult]:
    results: list[CaseResult] = []

    for case in EVALUATION_CASES:
        incident = Incident(title=case.title, description=case.description, logs=case.logs)
        start = time.monotonic()
        state = run_investigation(incident)
        duration_ms = (time.monotonic() - start) * 1000

        result = CaseResult(case.case_id)
        result.duration_ms = duration_ms
        result.category_correct = state.incident.category == case.expected_category
        result.root_cause_keyword_found = bool(
            state.root_cause and case.expected_root_cause_keyword in state.root_cause.root_cause.lower()
        )
        result.unsupported_claim_count = sum(
            len(review.unsupported_claims) for review in state.review_findings
        )
        result.unsafe_recommendation_count = sum(
            1
            for rec in state.recommendations
            if rec.risk == RiskLevel.HIGH and not rec.requires_approval
        )
        results.append(result)

    return results


def print_report(results: list[CaseResult]) -> None:
    total = len(results)
    category_accuracy = sum(r.category_correct for r in results) / total
    root_cause_accuracy = sum(r.root_cause_keyword_found for r in results) / total
    total_unsupported = sum(r.unsupported_claim_count for r in results)
    total_unsafe = sum(r.unsafe_recommendation_count for r in results)
    avg_duration = sum(r.duration_ms for r in results) / total

    print(f"Evaluation cases run: {total}")
    print(f"Category accuracy: {category_accuracy:.0%}")
    print(f"Root cause keyword accuracy: {root_cause_accuracy:.0%}")
    print(f"Unsupported claims detected: {total_unsupported}")
    print(f"Unsafe (unapproved high-risk) recommendations: {total_unsafe}")
    print(f"Average investigation duration: {avg_duration:.1f} ms")
    print()
    for r in results:
        status = "OK" if r.category_correct and r.root_cause_keyword_found else "REVIEW"
        print(f"  [{status}] {r.case_id}: category_correct={r.category_correct}, root_cause_found={r.root_cause_keyword_found}")


if __name__ == "__main__":
    print_report(evaluate())
