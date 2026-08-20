"""Tests for suggestion generation."""

from __future__ import annotations

from vertex_agent.evaluation import EvaluationResult
from vertex_agent.improvements import suggest_improvements


def test_suggest_improvements_returns_missing_term_hints() -> None:
    result = EvaluationResult(
        question="How do I create a subscription?",
        answer="Use Pub/Sub.",
        expected_terms=("Pub/Sub", "subscription", "ack"),
        matched_terms=("Pub/Sub",),
        score=1 / 3,
    )
    suggestions = suggest_improvements([result], threshold=0.8)

    assert suggestions[0].title.startswith("Improve answer coverage")
    assert "subscription" in suggestions[0].detail
