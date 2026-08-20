from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime

from google.cloud import storage

from vertex_agent.document_ai import DocumentAiProcessor
from vertex_agent.ingester import Ingester


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch ingest docs from a GCS bucket.")
    parser.add_argument(
        "--project",
        default=os.environ.get("GOOGLE_CLOUD_PROJECT", "portfolioadvanced-llm"),
    )
    parser.add_argument(
        "--bucket",
        default=os.environ.get("DOCS_BUCKET", "portfolioadvanced-llm-docs"),
    )
    parser.add_argument("--prefix", default=os.environ.get("DOCS_PREFIX", ""))
    parser.add_argument(
        "--processor-id",
        default=os.environ.get("DOCUMENTAI_PROCESSOR_ID", ""),
    )
    parser.add_argument("--location", default=os.environ.get("DOCUMENTAI_LOCATION", "us"))
    return parser.parse_args()


def _mime_type_for(name: str, content_type: str | None) -> str:
    if content_type:
        return content_type
    if name.lower().endswith(".pdf"):
        return "application/pdf"
    if name.lower().endswith(".html") or name.lower().endswith(".htm"):
        return "text/html"
    return "application/octet-stream"


def main() -> None:
    args = _parse_args()
    if not args.processor_id:
        raise SystemExit("DOCUMENTAI_PROCESSOR_ID is required (or pass --processor-id)")

    storage_client = storage.Client(project=args.project)
    processor = DocumentAiProcessor(
        project=args.project,
        location=args.location,
        processor_id=args.processor_id,
    )
    ingester = Ingester(project=args.project)

    bucket = storage_client.bucket(args.bucket)
    count = 0
    for blob in storage_client.list_blobs(bucket, prefix=args.prefix):
        if blob.name.endswith("/"):
            continue
        content = blob.download_as_bytes()
        extraction = processor.extract(
            content=content,
            mime_type=_mime_type_for(blob.name, blob.content_type),
            source_name=f"gs://{args.bucket}/{blob.name}",
        )
        payload = {
            "trace_id": blob.name,
            "event_type": "data_ingest",
            "version": "1.0",
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": {
                "content": extraction.text,
                "source_url": extraction.source_name,
            },
        }
        ingester.ingest_direct(payload)
        count += 1

    print(f"batch_ingested_documents={count}")


if __name__ == "__main__":
    main()
