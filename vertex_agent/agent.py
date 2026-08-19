"""
agent.py — Vertex AI Gemini agent with RAG.

Retrieves relevant chunks from BigQuery, builds a grounded prompt, and
calls Vertex AI (Gemini Pro) to produce a final answer.

Why Gemini via Vertex AI:
  - Same GCP project, same ADC credentials — zero extra auth setup.
  - `vertexai` Python SDK is idiomatic and async-friendly.
  - Free quota on gemini-1.0-pro-001 covers development workloads.
"""

from __future__ import annotations

import logging
import textwrap

import vertexai
from vertexai.generative_models import GenerativeModel

from vertex_agent.retriever import Retriever

logger = logging.getLogger(__name__)

_PROJECT = "portfolioadvanced-llm"
_LOCATION = "us-central1"
_MODEL = "gemini-1.0-pro-001"

_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a GCP documentation assistant.
    Answer questions using ONLY the context chunks provided.
    If the answer is not in the context, say "I don't have enough information."
    Always cite the source_url of the chunks you use.
""")


class Agent:
    """RAG agent backed by BigQuery chunks and Vertex AI Gemini.

    Usage::

        agent = Agent()
        answer = agent.ask("How do I create a Pub/Sub subscription with ordering?")
        print(answer)
    """

    def __init__(
        self,
        project: str = _PROJECT,
        location: str = _LOCATION,
        model: str = _MODEL,
        top_k: int = 5,
    ) -> None:
        vertexai.init(project=project, location=location)
        self._model = GenerativeModel(model, system_instruction=_SYSTEM_PROMPT)
        self._retriever = Retriever(project=project)
        self._top_k = top_k

    def ask(self, question: str) -> str:
        """Answer *question* using retrieved chunks as context."""
        chunks = self._retriever.search(question, top_k=self._top_k)
        if not chunks:
            return "I don't have enough information — no relevant chunks found."

        context = "\n\n".join(
            f"[{c.source_url}]\n{c.chunk_text}" for c in chunks
        )
        prompt = f"Context:\n{context}\n\nQuestion: {question}"
        logger.debug("Prompt length: %d chars", len(prompt))

        response = self._model.generate_content(prompt)
        return response.text
