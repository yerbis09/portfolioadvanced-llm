"""
gateway.py — Puerto Python de ArchetypeValidationGateway.java (PR #425)

Entry point. With no arguments runs an offline demo of the gate
over representative payloads (same spirit as the Java demo).

Usage:
    python -m pubsub_archetype.gateway
    python -m pubsub_archetype.gateway --archetype path/to/schema.json --charset utf-8
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .archetype import Archetype

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_SCHEMA = Path(__file__).parent / "schemas" / "archetype.schema.json"

# Representative payloads for the offline demo
DEMO_PAYLOADS = [
    # ✅ Conformant
    {
        "label": "conformant",
        "data": json.dumps(
            {"event_type": "llm_request", "payload": {"prompt": "Hello world"}, "version": "1.0"}
        ).encode("utf-8"),
    },
    # ✅ NFD → NFC canonicalization (false reject prevention)
    {
        "label": "NFD-normalized (ñ as n+combining)",
        "data": json.dumps(
            {
                "event_type": "data_ingest",
                "payload": {"text": "nin\u0303o"},  # NFD ñ
                "version": "1.0",
            }
        ).encode("utf-8"),
    },
    # ❌ Wrong enum value
    {
        "label": "bad enum (event_type)",
        "data": json.dumps({"event_type": "unknown_event", "payload": {}, "version": "1.0"}).encode(
            "utf-8"
        ),
    },
    # ❌ Missing required field
    {
        "label": "missing required field (version)",
        "data": json.dumps({"event_type": "llm_response", "payload": {}}).encode("utf-8"),
    },
    # ❌ Not JSON
    {
        "label": "not JSON",
        "data": b"this is not json at all",
    },
    # ❌ Bad charset
    {
        "label": "invalid charset bytes",
        "data": b"\xff\xfe invalid utf-8 sequence",
    },
    # ❌ Additional property (schema forbids it)
    {
        "label": "extra field not in schema",
        "data": json.dumps(
            {
                "event_type": "eval_result",
                "payload": {"score": 0.95},
                "version": "2.1",
                "unknown_field": "oops",
            }
        ).encode("utf-8"),
    },
]


def run_demo(schema_path: Path, charset: str) -> None:
    gate = Archetype(schema_path)
    sep = "-" * 60
    print(f"\n{sep}")
    print("  Archetype Validation Gate -- offline demo")
    print(f"  Schema  : {schema_path}")
    print(f"  Charset : {charset}")
    print(f"{sep}\n")

    for sample in DEMO_PAYLOADS:
        result = gate.validate(sample["data"], charset)
        icon = "[OK]" if result.is_accepted else "[FAIL]"
        print(f"{icon}  [{sample['label']}]")
        print(f"     -> {result}\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Archetype Validation Gate demo")
    parser.add_argument(
        "--archetype", default=str(DEFAULT_SCHEMA), help="Path to JSON Schema archetype file"
    )
    parser.add_argument("--charset", default="utf-8", help="Declared charset of incoming payloads")
    args = parser.parse_args(argv)
    run_demo(Path(args.archetype), args.charset)


if __name__ == "__main__":
    main(sys.argv[1:])
