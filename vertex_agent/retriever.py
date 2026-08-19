"""
retriever.py — BigQuery chunk retrieval.

Searches `llm_knowledge.chunks` for the most relevant chunks given a
query string.  Currently uses BM25-style keyword matching via BigQuery
SEARCH (full-text index).  Phase 3 will replace this with vector
similarity once embeddings are populated.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from google.cloud import bigquery

logger = logging.getLogger(__name__)

_PROJECT = "portfolioadvanced-llm"
_BQ_TABLE = f"{_PROJECT}.llm_knowledge.chunks"
_DEFAULT_TOP_K = 5


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    chunk_text: str
    source_url: str


class Retriever:
    """Retrieves the top-k most relevant chunks for a query.

    Usage::

        retriever = Retriever()
        chunks = retriever.search("how to create a Pub/Sub topic", top_k=3)
    """

    def __init__(self, project: str = _PROJECT) -> None:
        self._bq = bigquery.Client(project=project)

    def search(self, query: str, top_k: int = _DEFAULT_TOP_K) -> list[Chunk]:
        """Return up to *top_k* chunks whose text best matches *query*.

        Uses BigQuery full-text search (SEARCH function).  Falls back to
        a LIKE scan if the table has no search index yet.
        """
        sql = f"""
            SELECT doc_id, chunk_text, source_url
            FROM `{_BQ_TABLE}`
            WHERE SEARCH(chunk_text, @query)
            LIMIT @top_k
        """  # noqa: S608
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("query", "STRING", query),
                bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
            ]
        )
        try:
            rows = self._bq.query(sql, job_config=job_config).result()
        except Exception:
            logger.warning("SEARCH index not available, falling back to LIKE scan")
            rows = self._fallback_search(query, top_k)

        return [
            Chunk(doc_id=r.doc_id, chunk_text=r.chunk_text, source_url=r.source_url)
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _fallback_search(self, query: str, top_k: int) -> list:
        words = query.split()[:5]  # use first 5 words to keep query cheap
        conditions = " OR ".join(f"LOWER(chunk_text) LIKE LOWER('%{w}%')" for w in words)
        sql = f"""
            SELECT doc_id, chunk_text, source_url
            FROM `{_BQ_TABLE}`
            WHERE {conditions}
            LIMIT {top_k}
        """  # noqa: S608
        return list(self._bq.query(sql).result())
