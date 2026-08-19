"""Unit tests for vertex_agent — all GCP clients are mocked."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from vertex_agent.ingester import Ingester, _split_chunks
from vertex_agent.retriever import Chunk, Retriever


# ---------------------------------------------------------------------------
# _split_chunks
# ---------------------------------------------------------------------------

def test_split_chunks_basic():
    text = "A" * 600
    chunks = _split_chunks(text, size=512, overlap=64)
    assert len(chunks) == 2
    assert len(chunks[0]) == 512
    assert chunks[0][-64:] == chunks[1][:64]  # overlap preserved


def test_split_chunks_short_text():
    chunks = _split_chunks("hello", size=512, overlap=64)
    assert chunks == ["hello"]


def test_split_chunks_exact_size():
    chunks = _split_chunks("X" * 512, size=512, overlap=64)
    assert len(chunks) == 1


# ---------------------------------------------------------------------------
# Ingester.ingest_direct (mocked BQ + gate)
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_payload():
    return {
        "trace_id": "evt-001",
        "event_type": "data_ingest",
        "version": "1.0",
        "payload": {
            "content": "Google Cloud Pub/Sub is a messaging service. " * 20,
            "source_url": "https://cloud.google.com/pubsub/docs/overview",
        },
    }


@patch("vertex_agent.ingester.bigquery.Client")
@patch("vertex_agent.ingester.pubsub_v1.SubscriberClient")
def test_ingest_direct_valid(mock_sub, mock_bq, valid_payload):
    mock_bq.return_value.insert_rows_json.return_value = []  # no errors
    ingester = Ingester()
    records = ingester.ingest_direct(valid_payload)
    assert len(records) >= 1
    assert all(r.doc_id == "evt-001" for r in records)
    mock_bq.return_value.insert_rows_json.assert_called_once()


@patch("vertex_agent.ingester.bigquery.Client")
@patch("vertex_agent.ingester.pubsub_v1.SubscriberClient")
def test_ingest_direct_invalid_schema(mock_sub, mock_bq):
    from pubsub_archetype import FunctionalRejectError
    ingester = Ingester()
    with pytest.raises(FunctionalRejectError):
        ingester.ingest_direct({"bad": "payload"})


# ---------------------------------------------------------------------------
# Retriever.search (mocked BQ)
# ---------------------------------------------------------------------------

@patch("vertex_agent.retriever.bigquery.Client")
def test_retriever_search_returns_chunks(mock_bq):
    row = MagicMock()
    row.doc_id = "doc-1"
    row.chunk_text = "Pub/Sub ordering keys allow message ordering."
    row.source_url = "https://cloud.google.com/pubsub"
    mock_bq.return_value.query.return_value.result.return_value = [row]

    retriever = Retriever()
    chunks = retriever.search("ordering keys")
    assert len(chunks) == 1
    assert isinstance(chunks[0], Chunk)
    assert "ordering" in chunks[0].chunk_text


@patch("vertex_agent.retriever.bigquery.Client")
def test_retriever_fallback_on_error(mock_bq):
    mock_bq.return_value.query.side_effect = [
        Exception("no search index"),  # first call (SEARCH) fails
        MagicMock(result=MagicMock(return_value=[])),  # fallback LIKE scan
    ]
    retriever = Retriever()
    chunks = retriever.search("pub sub topic")
    assert chunks == []
