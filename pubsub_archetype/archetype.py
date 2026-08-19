"""
archetype.py — Archetype validation gate (Python port of PR #425).

The ingestion gate. Validates and canonicalizes every payload BEFORE it is
published to a Pub/Sub topic. Cheapest check first:

  1. Canonicalization  — decode declared charset + normalize to Unicode NFC.
  2. Syntactic         — is it valid JSON?
  3. Structural        — does it satisfy the JSON Schema archetype?

Patrones creacionales:
  - Factory Method : Archetype.from_path / Archetype.from_stream
  - Singleton      : _SchemaRegistry — cada path de schema se carga una sola vez.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from threading import Lock
from typing import IO

from jsonschema import Draft7Validator

from .validation_result import ValidationResult


class _SchemaRegistry:
    """Singleton registry: each schema path is compiled exactly once."""

    _instance: _SchemaRegistry | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> _SchemaRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._cache: dict[str, Draft7Validator] = {}
                    inst._cache_lock = Lock()
                    cls._instance = inst
        return cls._instance

    def get_or_compile(self, key: str, schema: dict) -> Draft7Validator:  # type: ignore[type-arg]
        with self._cache_lock:
            if key not in self._cache:
                Draft7Validator.check_schema(schema)
                self._cache[key] = Draft7Validator(schema)
            return self._cache[key]


class Archetype:
    """
    The validation gate. Thread-safe after construction.

    Use factory methods instead of the constructor directly:
        gate = Archetype.from_path("schemas/archetype.schema.json")
        gate = Archetype.from_stream(file_obj, key="my-schema")
    """

    def __init__(self, validator: Draft7Validator) -> None:
        self._validator = validator

    # --- Factory Method pattern ---

    @classmethod
    def from_path(cls, schema_path: str | Path) -> Archetype:
        """Factory: load and compile a JSON Schema from a file path."""
        schema_path = Path(schema_path)
        with schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        registry = _SchemaRegistry()
        validator = registry.get_or_compile(str(schema_path.resolve()), schema)
        return cls(validator)

    @classmethod
    def from_stream(cls, stream: IO[str], *, key: str) -> Archetype:
        """Factory: load and compile a JSON Schema from an open stream."""
        schema = json.load(stream)
        registry = _SchemaRegistry()
        validator = registry.get_or_compile(key, schema)
        return cls(validator)

    # --- Gate ---

    def validate(self, raw_bytes: bytes, declared_charset: str = "utf-8") -> ValidationResult:
        """
        Validate and canonicalize a raw payload at the gate.

        Args:
            raw_bytes:        payload exactly as received on the wire.
            declared_charset: charset the emitter claims to have used.

        Returns:
            ValidationResult.accepted(canonical) or ValidationResult.rejected([reasons]).
            Never raises for invalid input.
        """
        # 1. Canonicalization: decode + NFC. Kills false rejects (NFD vs NFC).
        try:
            decoded = raw_bytes.decode(declared_charset, errors="strict")
            canonical = unicodedata.normalize("NFC", decoded)
        except (UnicodeDecodeError, LookupError) as exc:
            return ValidationResult.rejected(
                [f"ENCODING_UNDECODABLE: payload is not valid {declared_charset}: {exc}"]
            )

        # 2. Syntactic: is it parseable JSON?
        try:
            node = json.loads(canonical)
        except json.JSONDecodeError as exc:
            return ValidationResult.rejected([f"SYNTAX_NOT_JSON: {exc}"])

        if node is None:
            return ValidationResult.rejected(["SYNTAX_EMPTY: payload contained no JSON value"])

        # 3. Structural: does it satisfy the archetype schema?
        errors = sorted(self._validator.iter_errors(node), key=lambda e: list(e.path))
        if errors:
            reasons = [
                "CONTRACT_VIOLATION[$."
                f"{'.'.join(str(p) for p in e.absolute_path) or '<root>'}]: {e.message}"
                for e in errors
            ]
            return ValidationResult.rejected(reasons)

        return ValidationResult.accepted(canonical)
