"""
corpus.py — BigQuery corpus wrapper.

Represents the knowledge base as a queryable corpus rather than a bare
table, which makes the agent and evaluation pipeline easier to compose.
"""

from __future__ import annotations

from dataclasses import dataclass

from google.cloud import bigquery


@dataclass(frozen=True)
class CorpusChunk:
    doc_id: str
    chunk_text: str
    source_url: str


class BigQueryCorpus:
    """Read-only corpus view over the knowledge chunks table."""

    def __init__(self, project: str, dataset: str = "llm_knowledge", table: str = "chunks") -> None:
        self._table = f"{project}.{dataset}.{table}"
        self._client = bigquery.Client(project=project)

    @property
    def table(self) -> str:
        return self._table

    def search(self, query: str, top_k: int = 5) -> list[CorpusChunk]:
        sql = f"""
            SELECT doc_id, chunk_text, source_url
            FROM `{self._table}`
            WHERE SEARCH(chunk_text, @query)
            LIMIT @top_k
        """  # noqa: S608
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("query", "STRING", query),
                bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
            ]
        )
        rows = self._client.query(sql, job_config=job_config).result()
        return [
            CorpusChunk(doc_id=row.doc_id, chunk_text=row.chunk_text, source_url=row.source_url)
            for row in rows
        ]
