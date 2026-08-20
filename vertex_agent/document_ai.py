"""
document_ai.py — Document AI extraction helper.

Processes PDFs and HTML documents into plain text that can then be split
into chunks and stored in BigQuery.
"""

from __future__ import annotations

from dataclasses import dataclass

from google.cloud import documentai_v1 as documentai


@dataclass(frozen=True)
class DocumentExtraction:
    text: str
    mime_type: str
    source_name: str


class DocumentAiProcessor:
    """Thin wrapper over Document AI's ProcessDocument API."""

    def __init__(
        self,
        project: str,
        location: str,
        processor_id: str,
        client: documentai.DocumentProcessorServiceClient | None = None,
    ) -> None:
        self._project = project
        self._location = location
        self._processor_id = processor_id
        self._client = client or documentai.DocumentProcessorServiceClient()

    @property
    def processor_name(self) -> str:
        return self._client.processor_path(
            self._project,
            self._location,
            self._processor_id,
        )

    def extract(self, content: bytes, mime_type: str, source_name: str) -> DocumentExtraction:
        raw_document = documentai.RawDocument(content=content, mime_type=mime_type)
        request = documentai.ProcessRequest(
            name=self.processor_name,
            raw_document=raw_document,
        )
        response = self._client.process_document(request=request)
        return DocumentExtraction(
            text=response.document.text,
            mime_type=mime_type,
            source_name=source_name,
        )
