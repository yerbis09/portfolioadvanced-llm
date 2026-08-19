"""
validation_result.py — ValidationResult con Pydantic v2.

Terminal outcome of the archetype gate:
  - ACCEPTED  -> canonical (UTF-8 NFC) payload string, safe to publish.
  - REJECTED  -> list of machine-readable reason codes, never enqueued.

Patrón creacional: Factory Method (accepted / rejected) sobre un modelo Pydantic inmutable.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class Status(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class ValidationResult(BaseModel):
    """Immutable result of the archetype gate. Use factory methods to construct."""

    status: Status
    canonical: Annotated[str | None, Field(default=None)]
    reasons: Annotated[list[str], Field(default_factory=list)]

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _check_consistency(self) -> ValidationResult:
        if self.status == Status.ACCEPTED and self.canonical is None:
            msg = "ACCEPTED result must carry a canonical payload"
            raise ValueError(msg)
        if self.status == Status.REJECTED and not self.reasons:
            msg = "REJECTED result must carry at least one reason"
            raise ValueError(msg)
        return self

    # --- Factory Method pattern ---

    @classmethod
    def accepted(cls, canonical: str) -> ValidationResult:
        """Factory: build an ACCEPTED result with the canonical payload."""
        return cls(status=Status.ACCEPTED, canonical=canonical)

    @classmethod
    def rejected(cls, reasons: list[str]) -> ValidationResult:
        """Factory: build a REJECTED result with machine-readable reason codes."""
        return cls(status=Status.REJECTED, reasons=list(reasons))

    # --- Convenience ---

    @property
    def is_accepted(self) -> bool:
        return self.status == Status.ACCEPTED

    def __str__(self) -> str:
        if self.is_accepted:
            return "ACCEPTED (enqueued)"
        return f"REJECTED — {'; '.join(self.reasons)}"
