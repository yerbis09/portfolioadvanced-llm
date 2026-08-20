"""
improvements.py — turn evaluation findings into concrete suggestions.
"""

from __future__ import annotations

from dataclasses import dataclass

from vertex_agent.evaluation import EvaluationResult


@dataclass(frozen=True)
class ImprovementSuggestion:
    title: str
    detail: str


def suggest_improvements(
    results: list[EvaluationResult],
    threshold: float = 0.8,
) -> list[ImprovementSuggestion]:
    suggestions: list[ImprovementSuggestion] = []
    for result in results:
        if result.score >= threshold:
            continue
        missing_terms = ", ".join(
            term for term in result.expected_terms if term not in result.matched_terms
        )
        suggestions.append(
            ImprovementSuggestion(
                title=f"Improve answer coverage for: {result.question}",
                detail=f"Missing terms: {missing_terms}",
            )
        )
    return suggestions
