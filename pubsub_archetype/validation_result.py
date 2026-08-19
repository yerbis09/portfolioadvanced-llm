"""
validation_result.py — Resultado terminal del gate de validación.

Invariante: ``ValidationResult`` es un value object inmutable.
Errores son valores, nunca excepciones — ``validate()`` es una función total.

Patrón: alternate constructors (``accepted`` / ``rejected``) sobre dataclass frozen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Status(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Un error de validación estructural con datos separados del formato."""

    path: str  # JSONPath al campo infractor, e.g. "$.event_type"
    code: str  # Código de error, e.g. "CONTRACT_VIOLATION", "SYNTAX_NOT_JSON"
    message: str  # Descripción legible

    def __str__(self) -> str:
        return f"{self.code}[{self.path}]: {self.message}"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Resultado inmutable del gate. Usa los factory methods para construirlo.

    - ``ACCEPTED``: ``canonical`` contiene el payload UTF-8 NFC listo para publicar.
    - ``REJECTED``: ``errors`` contiene los motivos estructurados; el payload NO se encola.
    """

    status: Status
    canonical: str | None = field(default=None)
    errors: tuple[ValidationError, ...] = field(default_factory=tuple)

    # --- Alternate constructors (Pythonic Factory Method) ---

    @classmethod
    def accepted(cls, canonical: str) -> ValidationResult:
        """Construye un resultado ACCEPTED con el payload canonicalizado."""
        return cls(status=Status.ACCEPTED, canonical=canonical)

    @classmethod
    def rejected(cls, errors: list[ValidationError]) -> ValidationResult:
        """Construye un resultado REJECTED con errores estructurados."""
        return cls(status=Status.REJECTED, errors=tuple(errors))

    @property
    def is_accepted(self) -> bool:
        return self.status == Status.ACCEPTED

    @property
    def reasons(self) -> list[str]:
        """Compatibilidad: lista de strings para logging/serialización."""
        return [str(e) for e in self.errors]

    def __str__(self) -> str:
        if self.is_accepted:
            return "ACCEPTED (enqueued)"
        return f"REJECTED — {'; '.join(str(e) for e in self.errors)}"
