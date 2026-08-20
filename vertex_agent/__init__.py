"""
vertex_agent — Phase 2: GCP-native LLM agent.

Ingests official GCP documentation into BigQuery, then answers
questions by retrieving relevant chunks and calling Vertex AI
(Gemini) to synthesise a response.

Architecture:
  [GCP Docs] → Pub/Sub (doc-ingestion-events)
             → ingester.py  (chunk + store in BQ)
             → retriever.py (BQ similarity search)
             → agent.py     (Vertex AI Gemini)
             → MCP server   (Phase 3)
"""

from vertex_agent.agent import Agent
from vertex_agent.corpus import BigQueryCorpus
from vertex_agent.document_ai import DocumentAiProcessor
from vertex_agent.evaluation import EvaluationResult, evaluate_answer
from vertex_agent.improvements import ImprovementSuggestion, suggest_improvements
from vertex_agent.ingester import Ingester
from vertex_agent.mcp_server import main as mcp_main
from vertex_agent.monitoring import MetricRecord, MetricsPublisher
from vertex_agent.retraining import RetrainingSignal, RetrainingTrigger
from vertex_agent.retriever import Retriever

__all__ = [
    "Agent",
    "BigQueryCorpus",
    "DocumentAiProcessor",
    "EvaluationResult",
    "ImprovementSuggestion",
    "Ingester",
    "MetricRecord",
    "MetricsPublisher",
    "RetrainingSignal",
    "RetrainingTrigger",
    "Retriever",
    "evaluate_answer",
    "mcp_main",
    "suggest_improvements",
]
