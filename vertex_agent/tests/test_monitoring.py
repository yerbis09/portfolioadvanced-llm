"""Tests for metrics publishing."""

from __future__ import annotations

from unittest.mock import MagicMock

from vertex_agent.monitoring import MetricRecord, MetricsPublisher


def test_metric_record_has_created_at() -> None:
    record = MetricRecord(run_id="r1", question="q", score=0.5)
    assert record.run_id == "r1"
    assert record.score == 0.5


def test_metrics_publisher_serializes_rows() -> None:
    publisher = MetricsPublisher(project="p")
    publisher._client = MagicMock()
    publisher.publish([MetricRecord(run_id="r1", question="q", score=0.5)])

    publisher._client.insert_rows_json.assert_called_once()
