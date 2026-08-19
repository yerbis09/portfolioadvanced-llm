"""
tests/test_classifying_receiver.py — Tests de ClassifyingReceiver.

Construccion directa con kwargs (no Builder) segun el patron Pythonic.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from pubsub_archetype.classifying_receiver import (
    ClassifyingReceiver,
    FunctionalRejectError,
    TransientError,
)


def _mock_message(message_id: str = "msg-001") -> MagicMock:
    msg = MagicMock()
    msg.message_id = message_id
    return msg


def _build(handler, quarantine=None):
    return ClassifyingReceiver(
        handler=handler,
        quarantine=quarantine or (lambda m, r: None),
    )


class TestClassifyingReceiverConstruction:
    def test_direct_construction_with_kwargs(self):
        r = ClassifyingReceiver(handler=lambda m: None, quarantine=lambda m, r: None)
        assert isinstance(r, ClassifyingReceiver)

    def test_frozen_immutable(self):
        r = ClassifyingReceiver(handler=lambda m: None, quarantine=lambda m, r: None)
        with pytest.raises((AttributeError, TypeError)):
            r.handler = lambda m: None  # type: ignore[misc]


class TestClassifyingReceiverHandle:
    def test_success_acks_message(self):
        msg = _mock_message()
        _build(lambda m: None).handle(msg)
        msg.ack.assert_called_once()
        msg.nack.assert_not_called()

    def test_transient_error_nacks_message(self):
        msg = _mock_message()
        _build(lambda m: (_ for _ in ()).throw(TransientError("timeout"))).handle(msg)
        msg.nack.assert_called_once()
        msg.ack.assert_not_called()

    def test_functional_reject_acks_and_quarantines(self):
        msg = _mock_message()
        quarantined = []
        _build(
            lambda m: (_ for _ in ()).throw(FunctionalRejectError("unknown_id")),
            quarantine=lambda m, r: quarantined.append(r),
        ).handle(msg)
        msg.ack.assert_called_once()
        assert quarantined == ["unknown_id"]

    def test_unknown_exception_nacks(self):
        msg = _mock_message()
        _build(lambda m: (_ for _ in ()).throw(RuntimeError("boom"))).handle(msg)
        msg.nack.assert_called_once()

    def test_quarantine_failure_still_acks(self):
        msg = _mock_message()
        _build(
            lambda m: (_ for _ in ()).throw(FunctionalRejectError("bad")),
            quarantine=lambda m, r: (_ for _ in ()).throw(RuntimeError("q down")),
        ).handle(msg)
        msg.ack.assert_called_once()
