"""
classifying_receiver.py — ClassifyingReceiver (Python port of PR #425).

Subscriber that applies a three-way decision to every incoming message:
  - ACCEPTED          -> process normally, ack().
  - TRANSIENT failure -> nack(), let Pub/Sub retry with backoff -> dead-letter.
  - FUNCTIONAL REJECT -> ack() + park in quarantine (never bounce).

Patron creacional: Builder — ReceiverBuilder construye el ClassifyingReceiver
con configuracion progresiva antes de sellarlo.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Raised by the handler to signal a recoverable, transient failure."""


class FunctionalRejectError(Exception):
    """Raised by the handler to signal a deterministic, non-recoverable failure."""


@runtime_checkable
class PubSubMessage(Protocol):
    """Structural protocol for google.cloud.pubsub_v1 Message."""

    message_id: str

    def ack(self) -> None: ...
    def nack(self) -> None: ...


class ClassifyingReceiver:
    """
    Wraps a Pub/Sub message handler and classifies processing failures.

    Build via ReceiverBuilder:
        receiver = (
            ReceiverBuilder()
            .with_handler(my_handler)
            .with_quarantine(my_quarantine_fn)
            .build()
        )
    """

    def __init__(
        self,
        handler: Callable[[Any], None],
        quarantine: Callable[[Any, str], None],
    ) -> None:
        self._handler = handler
        self._quarantine = quarantine

    def handle(self, message: PubSubMessage) -> None:
        """Process one Pub/Sub message with three-way classification."""
        try:
            self._handler(message)
            message.ack()
            logger.debug("ACCEPTED: message %s", message.message_id)

        except TransientError as exc:
            logger.warning("TRANSIENT: message %s — %s (nack)", message.message_id, exc)
            message.nack()

        except FunctionalRejectError as exc:
            reason = str(exc)
            logger.error(
                "FUNCTIONAL_REJECT: message %s — %s (ack+quarantine)",
                message.message_id,
                reason,
            )
            try:
                self._quarantine(message, reason)
            except Exception as q_exc:
                logger.error("Quarantine failed for message %s: %s", message.message_id, q_exc)
            message.ack()

        except Exception as exc:
            logger.exception("UNKNOWN: message %s — %s (nack)", message.message_id, exc)
            message.nack()


class ReceiverBuilder:
    """
    Builder pattern for ClassifyingReceiver.

    Allows progressive configuration and enforces required fields at build time.
    """

    def __init__(self) -> None:
        self._handler: Callable[[Any], None] | None = None
        self._quarantine: Callable[[Any, str], None] | None = None

    def with_handler(self, handler: Callable[[Any], None]) -> ReceiverBuilder:
        self._handler = handler
        return self

    def with_quarantine(self, quarantine: Callable[[Any, str], None]) -> ReceiverBuilder:
        self._quarantine = quarantine
        return self

    def build(self) -> ClassifyingReceiver:
        if self._handler is None:
            msg = "handler is required"
            raise ValueError(msg)
        if self._quarantine is None:
            msg = "quarantine function is required"
            raise ValueError(msg)
        return ClassifyingReceiver(self._handler, self._quarantine)
