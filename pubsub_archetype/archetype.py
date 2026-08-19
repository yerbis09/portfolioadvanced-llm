"""
archetype.py — Gate de validación de payloads para Cloud Pub/Sub.

Invariante: ``Archetype.validate`` es una función **total** — nunca lanza sobre
input malformado. Siempre devuelve un ``ValidationResult``; los errores son
valores, no excepciones.

Por qué Python en vez de Java
---------------------------------
El port Java original (PR #425, GoogleCloudPlatform/pubsub) requiere:
  - Java 8 + Maven + 5 dependencias transitivas (Jackson, json-schema-validator...)
  - ~800 líneas con patrones GoF (Factory, Singleton, Builder) necesarios porque
    Java carece de funciones de primera clase, keyword args y módulos-singleton.

Esta implementación Python consigue lo mismo con:
  - functools.cache      -> el registry de schemas en una línea, thread-safe.
  - unicodedata.normalize en stdlib -> canonicalización NFC sin dependencias extra.
  - json en stdlib       -> parseo sin ObjectMapper ni checked exceptions.
  - jsonschema           -> validación con errores iterables como datos.
  - Alternate constructors -> from_path / from_stream como datetime.fromisoformat.
  - Errores como valores -> ValidationResult con ValidationError estructurado,
                            no strings de formato ni excepciones de control de flujo.

Orden del gate (cheapest-first):
  1. Canonicalización  -- decode charset + NFC. Elimina falsos rechazos por NFD.
  2. Sintáctico        -- es JSON válido?
  3. Estructural       -- satisface el schema archetype?
"""

from __future__ import annotations

import functools
import json
import unicodedata
from pathlib import Path
from typing import IO

from jsonschema import Draft7Validator

from .validation_result import ValidationError, ValidationResult


@functools.cache
def _compile_validator(schema_json: str) -> Draft7Validator:
    """
    Compila y cachea un Draft7Validator por contenido de schema.

    Reemplaza el Singleton _SchemaRegistry del port Java: functools.cache
    es thread-safe, introspectable y no requiere ninguna clase auxiliar.
    """
    schema = json.loads(schema_json)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


class Archetype:
    """
    El gate de validación. Thread-safe tras la construcción.

    Usa los alternate constructors en vez del __init__ directo:
        gate = Archetype.from_path("schemas/archetype.schema.json")
        gate = Archetype.from_stream(file_obj)
    """

    def __init__(self, validator: Draft7Validator) -> None:
        self._validator = validator

    @classmethod
    def from_path(cls, schema_path: str | Path) -> Archetype:
        """Carga y compila el schema desde un fichero. Cachea por contenido."""
        schema_json = Path(schema_path).read_text(encoding="utf-8")
        return cls(_compile_validator(schema_json))

    @classmethod
    def from_stream(cls, stream: IO[str]) -> Archetype:
        """Carga y compila el schema desde un stream abierto."""
        return cls(_compile_validator(stream.read()))

    def validate(self, raw_bytes: bytes, declared_charset: str = "utf-8") -> ValidationResult:
        """
        Valida y canonicaliza un payload en el gate.

        Esta funcion es total: nunca lanza para input invalido.
        Cualquier error (encoding, JSON, schema) es un ValidationResult.rejected.

        Args:
            raw_bytes:        payload tal como llega por el wire.
            declared_charset: charset que el emisor declara haber usado.

        Returns:
            ValidationResult.accepted(canonical) si el payload es conforme.
            ValidationResult.rejected(errors) con errores estructurados si no.
        """
        # 1. Canonicalizacion: decode + NFC. Elimina falsos rechazos NFD vs NFC.
        try:
            decoded = raw_bytes.decode(declared_charset)
            canonical = unicodedata.normalize("NFC", decoded)
        except (UnicodeDecodeError, LookupError) as exc:
            return ValidationResult.rejected(
                [
                    ValidationError(
                        path="$",
                        code="ENCODING_UNDECODABLE",
                        message=f"payload is not valid {declared_charset}: {exc}",
                    )
                ]
            )

        # 2. Sintactico: es JSON parseable?
        try:
            node = json.loads(canonical)
        except json.JSONDecodeError as exc:
            return ValidationResult.rejected(
                [ValidationError(path="$", code="SYNTAX_NOT_JSON", message=str(exc))]
            )

        if node is None:
            return ValidationResult.rejected(
                [
                    ValidationError(
                        path="$", code="SYNTAX_EMPTY", message="payload contained no JSON value"
                    )
                ]
            )

        # 3. Estructural: satisface el schema archetype?
        schema_errors = sorted(self._validator.iter_errors(node), key=lambda e: tuple(e.path))
        if schema_errors:
            return ValidationResult.rejected(
                [
                    ValidationError(
                        path="$." + ".".join(str(p) for p in e.absolute_path)
                        if e.absolute_path
                        else "$",
                        code="CONTRACT_VIOLATION",
                        message=e.message,
                    )
                    for e in schema_errors
                ]
            )

        return ValidationResult.accepted(canonical)
