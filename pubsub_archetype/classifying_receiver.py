"""
classifying_receiver.py — Subscriber con clasificacion de fallos para Pub/Sub.

Aplica una decision de tres vias a cada mensaje:
  - ACCEPTED          -> handler OK, ack().
  - TRANSIENT failure -> nack(), deja que Pub/Sub reintente con backoff -> dead-letter.
  - FUNCTIONAL REJECT -> ack() + quarantine. Nunca rebota.

Solo los fallos transitorios usan la maquinaria de redelivery.

Por qué dataclass en vez de Builder
-------------------------------------
Java necesita el patron Builder porque carece de keyword arguments y defaults.
Python los tiene nativos: ClassifyingReceiver(handler=h, quarantine=q) ES el builder,
es inmutable con frozen=True y autodocumentado. Cero metodos encadenados, cero .build().
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class TransientError(Exception):
    """Señala un fallo recuperable (timeout, 5xx, red). Pub/Sub reintentara."""


class FunctionalRejectError(Exception):
    """Señala un fallo determinista (id desconocido, duplicado, regla de negocio).
    El mensaje se acepta (ack) y se aparca en cuarentena; nunca rebota."""


@runtime_checkable
class PubSubMessage(Protocol):
    """
    Protocolo estructural para google.cloud.pubsub_v1 Message.

    Usar Protocol desacopla del SDK sin adapters — imposible en Java sin
    interfaces + wrappers. El duck typing con contrato es suficiente.

    Note: message_id se expone como atributo read-only en el SDK real.
    @runtime_checkable verifica presencia pero no firma; no usar isinstance
    como sustituto de tipado estricto.
    """

    message_id: str  # read-only en el SDK

    def ack(self) -> None: ...
    def nack(self) -> None: ...


Handler = Callable[[Any], None]
Quarantine = Callable[[Any, str], None]


@dataclass(frozen=True)
class ClassifyingReceiver:
    """
    Receptor clasificador. Construye directamente con keyword args:

        receiver = ClassifyingReceiver(handler=my_fn, quarantine=my_q)

    Inmutable por frozen=True; igualdad estructural gratis.
    """

    handler: Handler
    quarantine: Quarantine

    def handle(self, message: PubSubMessage) -> None:
        """Procesa un mensaje Pub/Sub con decision de tres vias."""
        try:
            self.handler(message)
            message.ack()
            logger.debug("ACCEPTED: message %s", message.message_id)

        except TransientError as exc:
            logger.warning("TRANSIENT: message %s — %s (nack)", message.message_id, exc)
            message.nack()

        except FunctionalRejectError as exc:
            reason = str(exc)
            logger.error(
                "FUNCTIONAL_REJECT: message %s — %s (ack+quarantine)", message.message_id, reason
            )
            try:
                self.quarantine(message, reason)
            except Exception as q_exc:
                logger.error("Quarantine failed for message %s: %s", message.message_id, q_exc)
            message.ack()

        except Exception as exc:
            logger.exception("UNKNOWN: message %s — %s (nack)", message.message_id, exc)
            message.nack()
