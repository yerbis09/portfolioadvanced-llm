"""
retraining.py — retraining trigger helper.

Publishes a lightweight signal when fresh documentation arrives or when
evaluation scores drop below a threshold.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from google.cloud import pubsub_v1


@dataclass(frozen=True)
class RetrainingSignal:
    reason: str
    source: str
    score: float | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class RetrainingTrigger:
    """Publishes retraining signals to Pub/Sub."""

    def __init__(self, project: str, topic: str = "doc-retraining-events") -> None:
        self._topic = f"projects/{project}/topics/{topic}"
        self._publisher = pubsub_v1.PublisherClient()

    def publish(self, signal: RetrainingSignal) -> str:
        message_id = self._publisher.publish(
            self._topic,
            json.dumps(signal.__dict__, ensure_ascii=True).encode("utf-8"),
        ).result(timeout=60)
        return message_id
