"""Evaluation regression test.

Asserts a minimum accuracy floor rather than 100%, since the heuristic
classifier is deliberately simple and keyword-driven. This test exists
to catch regressions, not to claim the classifier is perfect — its
known limitations are documented in ARCHITECTURE.md.
"""

from nexora.evaluation.run_eval import evaluate


def test_root_cause_keyword_accuracy_meets_floor():
    results = evaluate()
    accuracy = sum(r.root_cause_keyword_found for r in results) / len(results)
    assert accuracy >= 0.8


def test_no_unsafe_high_risk_recommendations():
    results = evaluate()
    assert sum(r.unsafe_recommendation_count for r in results) == 0


def test_no_unsupported_claims_reach_review():
    results = evaluate()
    assert sum(r.unsupported_claim_count for r in results) == 0
