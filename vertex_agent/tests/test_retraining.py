"""Tests for retraining helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

from vertex_agent.retraining import RetrainingSignal, RetrainingTrigger


def test_retraining_signal_serializes_reason() -> None:
    signal = RetrainingSignal(reason="new docs", source="gs://bucket/doc.pdf", score=0.42)
    assert signal.reason == "new docs"


def test_retraining_trigger_publish_uses_pubsub_topic() -> None:
    trigger = RetrainingTrigger(project="p", topic="signals")
    trigger._publisher = MagicMock()
    trigger._publisher.publish.return_value.result.return_value = "message-1"

    message_id = trigger.publish(
        RetrainingSignal(reason="new docs", source="gs://bucket/doc.pdf", score=0.42)
    )

    assert message_id == "message-1"
    trigger._publisher.publish.assert_called_once()
