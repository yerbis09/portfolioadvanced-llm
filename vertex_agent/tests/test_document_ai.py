"""Tests for Document AI helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from vertex_agent.document_ai import DocumentAiProcessor


def test_document_ai_extract_uses_processor_name() -> None:
    client = MagicMock()
    client.processor_path.return_value = "projects/p/locations/l/processors/proc"
    client.process_document.return_value = SimpleNamespace(
        document=SimpleNamespace(text="Extracted text")
    )

    processor = DocumentAiProcessor(project="p", location="l", processor_id="proc", client=client)
    result = processor.extract(b"data", "application/pdf", "gs://bucket/doc.pdf")

    assert result.text == "Extracted text"
    assert result.mime_type == "application/pdf"
    assert result.source_name == "gs://bucket/doc.pdf"
    client.process_document.assert_called_once()
