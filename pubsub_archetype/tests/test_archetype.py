"""
tests/test_archetype.py — Tests del gate de validacion Archetype.

Cubre: accept, cada clase de rechazo determinista, canonicalizacion NFD->NFC.
Los errores se comprueban como datos estructurados (ValidationError), no strings.
"""

import json
import sys
import unicodedata
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from pubsub_archetype.archetype import Archetype
from pubsub_archetype.validation_result import Status

SCHEMA = Path(__file__).parent.parent / "schemas" / "archetype.schema.json"


@pytest.fixture(scope="module")
def gate():
    return Archetype.from_path(SCHEMA)


def _encode(obj: dict) -> bytes:
    return json.dumps(obj).encode("utf-8")


VALID = {"event_type": "llm_request", "payload": {"prompt": "hi"}, "version": "1.0"}


class TestAccept:
    def test_conformant_payload_is_accepted(self, gate):
        result = gate.validate(_encode(VALID))
        assert result.status == Status.ACCEPTED
        assert result.canonical is not None

    def test_nfd_normalized_to_nfc(self, gate):
        payload = {"event_type": "data_ingest", "payload": {}, "version": "1.0"}
        raw = json.dumps(payload).encode("utf-8")
        nfd_raw = unicodedata.normalize("NFD", raw.decode("utf-8")).encode("utf-8")
        result = gate.validate(nfd_raw)
        assert result.status == Status.ACCEPTED
        assert result.canonical == unicodedata.normalize("NFC", result.canonical)


class TestDeterministicRejects:
    def test_not_json(self, gate):
        result = gate.validate(b"not json at all")
        assert result.status == Status.REJECTED
        assert any(e.code == "SYNTAX_NOT_JSON" for e in result.errors)

    def test_invalid_charset(self, gate):
        result = gate.validate(b"\xff\xfe bad bytes", declared_charset="utf-8")
        assert result.status == Status.REJECTED
        assert any(e.code == "ENCODING_UNDECODABLE" for e in result.errors)

    def test_bad_enum(self, gate):
        bad = {**VALID, "event_type": "not_a_valid_type"}
        result = gate.validate(_encode(bad))
        assert result.status == Status.REJECTED
        assert any(e.code == "CONTRACT_VIOLATION" for e in result.errors)

    def test_missing_required_field(self, gate):
        missing = {"event_type": "llm_response", "payload": {}}
        result = gate.validate(_encode(missing))
        assert result.status == Status.REJECTED
        assert any(e.code == "CONTRACT_VIOLATION" for e in result.errors)

    def test_additional_property_rejected(self, gate):
        extra = {**VALID, "unexpected_field": "oops"}
        result = gate.validate(_encode(extra))
        assert result.status == Status.REJECTED

    def test_wrong_type_for_version(self, gate):
        bad_type = {**VALID, "version": 1}
        result = gate.validate(_encode(bad_type))
        assert result.status == Status.REJECTED

    def test_empty_bytes(self, gate):
        result = gate.validate(b"")
        assert result.status == Status.REJECTED

    def test_errors_are_structured_data(self, gate):
        """Los errores son ValidationError con path/code/message, no strings ad-hoc."""
        bad = {**VALID, "event_type": "bad_enum"}
        result = gate.validate(_encode(bad))
        for err in result.errors:
            assert hasattr(err, "path")
            assert hasattr(err, "code")
            assert hasattr(err, "message")
            assert err.path.startswith("$")

    def test_reasons_compat_property(self, gate):
        """reasons sigue disponible para logging/serialización."""
        result = gate.validate(b"not json")
        assert isinstance(result.reasons, list)
        assert len(result.reasons) > 0
