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
from vertex_agent.ingester import Ingester
from vertex_agent.retriever import Retriever

__all__ = ["Agent", "Ingester", "Retriever"]
