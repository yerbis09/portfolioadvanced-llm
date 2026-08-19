"""Tests for the MCP wrapper."""

from __future__ import annotations

from types import SimpleNamespace

from vertex_agent import mcp_server


def test_ask_question_uses_injected_agent() -> None:
    class FakeAgent:
        def ask(self, question: str) -> str:
            return f"answer:{question}"

    assert mcp_server.ask_question("How?", agent=FakeAgent()) == "answer:How?"


def test_search_documentation_serializes_chunks() -> None:
    class FakeRetriever:
        def search(self, query: str, top_k: int = 5):
            assert query == "pubsub"
            assert top_k == 3
            return [
                SimpleNamespace(
                    doc_id="doc-1",
                    chunk_text="Pub/Sub overview",
                    source_url="https://cloud.google.com/pubsub",
                )
            ]

    result = mcp_server.search_documentation("pubsub", top_k=3, retriever=FakeRetriever())
    assert result == [
        {
            "doc_id": "doc-1",
            "chunk_text": "Pub/Sub overview",
            "source_url": "https://cloud.google.com/pubsub",
        }
    ]


def test_ingest_document_returns_summary() -> None:
    class FakeIngester:
        def ingest_direct(self, payload: dict):
            assert payload["trace_id"] == "evt-1"
            return [SimpleNamespace(doc_id="evt-1"), SimpleNamespace(doc_id="evt-1")]

    result = mcp_server.ingest_document(
        {"trace_id": "evt-1", "payload": {"content": "x"}},
        ingester=FakeIngester(),
    )
    assert result == {"status": "ok", "chunk_count": 2, "doc_id": "evt-1"}
