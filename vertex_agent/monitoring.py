"""
monitoring.py — metrics publishing for BigQuery / Looker Studio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from google.cloud import bigquery


@dataclass(frozen=True)
class MetricRecord:
    run_id: str
    question: str
    score: float
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class MetricsPublisher:
    def __init__(
        self,
        project: str,
        dataset: str = "llm_knowledge",
        table: str = "evaluation_metrics",
    ) -> None:
        self._table = f"{project}.{dataset}.{table}"
        self._client = bigquery.Client(project=project)

    def publish(self, records: list[MetricRecord]) -> list[dict]:
        rows = [
            {
                "run_id": record.run_id,
                "question": record.question,
                "score": record.score,
                "created_at": record.created_at,
            }
            for record in records
        ]
        return self._client.insert_rows_json(self._table, rows)
