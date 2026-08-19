"""
tests/test_gateway.py — Tests for the offline demo gateway.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from pubsub_archetype.gateway import main, run_demo

SCHEMA = Path(__file__).parent.parent / "schemas" / "archetype.schema.json"


class TestGatewayDemo:
    def test_run_demo_no_exceptions(self, capsys):
        run_demo(SCHEMA, "utf-8")
        out = capsys.readouterr().out
        assert "ACCEPTED" in out
        assert "REJECTED" in out

    def test_main_no_args_runs_demo(self, capsys):
        main([])
        out = capsys.readouterr().out
        assert "Archetype Validation Gate" in out

    def test_main_custom_schema(self, capsys):
        main(["--archetype", str(SCHEMA), "--charset", "utf-8"])
        out = capsys.readouterr().out
        assert "ACCEPTED" in out
