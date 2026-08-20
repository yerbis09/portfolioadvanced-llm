"""
evaluation.py — lightweight evaluation helpers for the RAG agent.

This is intentionally simple and deterministic so it can be used in CI
without depending on external evaluation services.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationResult:
    question: str
    answer: str
    expected_terms: tuple[str, ...]
    matched_terms: tuple[str, ...]
    score: float


def evaluate_answer(question: str, answer: str, expected_terms: list[str]) -> EvaluationResult:
    normalized_answer = answer.lower()
    matched = tuple(term for term in expected_terms if term.lower() in normalized_answer)
    score = len(matched) / len(expected_terms) if expected_terms else 1.0
    return EvaluationResult(
        question=question,
        answer=answer,
        expected_terms=tuple(expected_terms),
        matched_terms=matched,
        score=score,
    )
