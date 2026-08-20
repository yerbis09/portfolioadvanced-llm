"""Tests for the batch ingestion job."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from scripts import batch_ingest


def test_mime_type_detection() -> None:
    assert batch_ingest._mime_type_for("doc.pdf", None) == "application/pdf"
    assert batch_ingest._mime_type_for("doc.html", None) == "text/html"
    assert batch_ingest._mime_type_for("doc.bin", None) == "application/octet-stream"


@patch("scripts.batch_ingest.storage.Client")
@patch("scripts.batch_ingest.DocumentAiProcessor")
@patch("scripts.batch_ingest.Ingester")
def test_batch_ingest_main(mock_ingester, mock_docai, mock_storage) -> None:
    blob = SimpleNamespace(
        name="docs/file.pdf",
        content_type="application/pdf",
        download_as_bytes=lambda: b"pdf-bytes",
    )
    mock_storage.return_value.list_blobs.return_value = [blob]
    mock_docai.return_value.extract.return_value = SimpleNamespace(
        text="extracted",
        source_name="gs://bucket/docs/file.pdf",
    )
    mock_ingester.return_value.ingest_direct.return_value = []

    with patch("scripts.batch_ingest._parse_args") as parse_args:
        parse_args.return_value = SimpleNamespace(
            project="p",
            bucket="bucket",
            prefix="docs/",
            processor_id="proc",
            location="us",
        )
        batch_ingest.main()

    mock_docai.return_value.extract.assert_called_once()
    mock_ingester.return_value.ingest_direct.assert_called_once()
