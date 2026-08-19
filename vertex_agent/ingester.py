"""
ingester.py — Pub/Sub → BigQuery chunk pipeline.

Subscribes to `doc-ingestion-events`, validates each message through
the archetype gate, splits the document text into overlapping chunks,
and writes them to `llm_knowledge.chunks` in BigQuery.

Why Python over Java here:
  - `google-cloud-bigquery` + `google-cloud-pubsub` are first-class
    Python libraries with idiomatic context managers.
  - The archetype gate (`pubsub_archetype`) is already Python — zero
    FFI or subprocess overhead.
  - Chunk/overlap logic is three lines with standard slicing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from google.cloud import bigquery, pubsub_v1

from pubsub_archetype import Archetype, ClassifyingReceiver, FunctionalRejectError, TransientError

logger = logging.getLogger(__name__)

_SCHEMA_PATH = "pubsub_archetype/schemas/archetype.schema.json"
_PROJECT = "portfolioadvanced-llm"
_SUBSCRIPTION = f"projects/{_PROJECT}/subscriptions/doc-ingestion-sub"
_BQ_TABLE = f"{_PROJECT}.llm_knowledge.chunks"

_CHUNK_SIZE = 512   # characters
_CHUNK_OVERLAP = 64


@dataclass(frozen=True)
class ChunkRecord:
    doc_id: str
    chunk_text: str
    source_url: str
    ingested_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    embedding: str = "{}"  # placeholder until Phase 3 adds embeddings


def _split_chunks(text: str, size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split *text* into overlapping windows of *size* chars."""
    step = size - overlap
    return [text[i : i + size] for i in range(0, max(1, len(text) - overlap), step)]


class Ingester:
    """Pulls Pub/Sub messages, validates them, and stores chunks in BigQuery.

    Usage::

        ingester = Ingester()
        ingester.run()          # blocking pull loop
    """

    def __init__(self, project: str = _PROJECT) -> None:
        self._project = project
        self._gate = Archetype.from_path(_SCHEMA_PATH)
        self._bq = bigquery.Client(project=project)
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscription = f"projects/{project}/subscriptions/doc-ingestion-sub"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Block and process messages until KeyboardInterrupt."""
        receiver = ClassifyingReceiver(
            handler=self._on_message,
            quarantine=self._on_quarantine,
        )
        logger.info("Ingester listening on %s", self._subscription)
        streaming_pull = self._subscriber.subscribe(self._subscription, receiver)
        try:
            streaming_pull.result()
        except KeyboardInterrupt:
            streaming_pull.cancel()

    def ingest_direct(self, payload: dict) -> list[ChunkRecord]:
        """Validate *payload* and write chunks — useful for unit tests."""
        result = self._gate.validate(json.dumps(payload).encode())
        if not result.is_accepted:
            raise FunctionalRejectError(result)
        return self._write_chunks(payload)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_message(self, message: pubsub_v1.types.PubsubMessage) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            result = self._gate.validate(message.data)
            if result.is_accepted:
                self._write_chunks(payload)
                message.ack()
            else:
                logger.warning("Schema invalid — nacking: %s", result.errors)
                message.nack()
        except Exception:
            logger.exception("Transient error processing message")
            message.nack()

    def _on_quarantine(self, message: pubsub_v1.types.PubsubMessage, exc: Exception) -> None:
        logger.error("Quarantine: %s — %s", exc, message.message_id)

    def _write_chunks(self, payload: dict) -> list[ChunkRecord]:
        doc_id = payload.get("trace_id", payload.get("event_type", "unknown"))
        text = payload.get("payload", {}).get("content", "")
        source_url = payload.get("payload", {}).get("source_url", "")
        chunks = [
            ChunkRecord(doc_id=doc_id, chunk_text=c, source_url=source_url)
            for c in _split_chunks(text)
        ]
        rows = [
            {
                "doc_id": c.doc_id,
                "chunk_text": c.chunk_text,
                "source_url": c.source_url,
                "ingested_at": c.ingested_at,
                "embedding": c.embedding,
            }
            for c in chunks
        ]
        errors = self._bq.insert_rows_json(_BQ_TABLE, rows)
        if errors:
            raise TransientError(f"BigQuery insert errors: {errors}")
        logger.info("Stored %d chunks for doc %s", len(chunks), doc_id)
        return chunks
