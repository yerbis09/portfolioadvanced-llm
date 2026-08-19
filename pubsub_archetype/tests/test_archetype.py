"""
tests/test_archetype.py — Puerto Python de ArchetypeTest.java (PR #425)

Covers: accept, each deterministic reject class, NFD->NFC canonicalization.
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
        # NFD ñ (n + combining tilde) should be accepted after NFC normalization
        nfd_payload = {"event_type": "data_ingest", "payload": {}, "version": "1.0"}
        raw = json.dumps(nfd_payload).encode("utf-8")
        # Manually inject NFD
        nfd_raw = unicodedata.normalize("NFD", raw.decode("utf-8")).encode("utf-8")
        result = gate.validate(nfd_raw)
        assert result.status == Status.ACCEPTED
        # canonical must be NFC
        assert result.canonical == unicodedata.normalize("NFC", result.canonical)


class TestDeterministicRejects:
    def test_not_json(self, gate):
        result = gate.validate(b"not json at all")
        assert result.status == Status.REJECTED
        assert any("SYNTAX_NOT_JSON" in r for r in result.reasons)

    def test_invalid_charset(self, gate):
        result = gate.validate(b"\xff\xfe bad bytes", declared_charset="utf-8")
        assert result.status == Status.REJECTED
        assert any("ENCODING_UNDECODABLE" in r for r in result.reasons)

    def test_bad_enum(self, gate):
        bad = {**VALID, "event_type": "not_a_valid_type"}
        result = gate.validate(_encode(bad))
        assert result.status == Status.REJECTED
        assert any("CONTRACT_VIOLATION" in r for r in result.reasons)

    def test_missing_required_field(self, gate):
        missing = {"event_type": "llm_response", "payload": {}}  # no version
        result = gate.validate(_encode(missing))
        assert result.status == Status.REJECTED
        assert any("CONTRACT_VIOLATION" in r for r in result.reasons)

    def test_additional_property_rejected(self, gate):
        extra = {**VALID, "unexpected_field": "oops"}
        result = gate.validate(_encode(extra))
        assert result.status == Status.REJECTED

    def test_wrong_type_for_version(self, gate):
        bad_type = {**VALID, "version": 1}  # should be string
        result = gate.validate(_encode(bad_type))
        assert result.status == Status.REJECTED

    def test_empty_bytes(self, gate):
        result = gate.validate(b"")
        assert result.status == Status.REJECTED
