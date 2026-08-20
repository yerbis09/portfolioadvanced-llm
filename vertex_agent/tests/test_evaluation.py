"""Tests for lightweight evaluation helpers."""

from __future__ import annotations

from vertex_agent.evaluation import evaluate_answer


def test_evaluate_answer_scores_keyword_coverage() -> None:
    result = evaluate_answer(
        "How do I create a Pub/Sub subscription?",
        "Create a Pub/Sub subscription and validate the result.",
        ["Pub/Sub", "subscription", "validate"],
    )

    assert result.score == 1.0
    assert result.matched_terms == ("Pub/Sub", "subscription", "validate")
