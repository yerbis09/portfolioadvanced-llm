"""pubsub_archetype -- Gate de validacion de payloads para Cloud Pub/Sub.

Invariante: Archetype.validate es total -- nunca lanza, errores son valores.
"""

from .archetype import Archetype
from .classifying_receiver import ClassifyingReceiver, FunctionalRejectError, TransientError
from .validation_result import Status, ValidationError, ValidationResult

__all__ = [
    "Archetype",
    "ClassifyingReceiver",
    "FunctionalRejectError",
    "Status",
    "TransientError",
    "ValidationError",
    "ValidationResult",
]
