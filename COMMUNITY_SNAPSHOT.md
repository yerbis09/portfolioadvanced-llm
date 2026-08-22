# portfolioadvanced-llm — Live GCP demo (Pub/Sub → gate → BigQuery + Vertex AI RAG over MCP)

Project: portfolioadvanced-llm
Generated: 2026-08-22 11:24 UTC

## Enabled Google Cloud APIs
- aiplatform.googleapis.com
- bigquery.googleapis.com
- bigqueryconnection.googleapis.com
- bigquerydatapolicy.googleapis.com
- bigquerydatatransfer.googleapis.com
- bigquerymigration.googleapis.com
- bigqueryreservation.googleapis.com
- bigquerystorage.googleapis.com
- documentai.googleapis.com
- pubsub.googleapis.com
- storage-api.googleapis.com
- storage-component.googleapis.com
- storage.googleapis.com

## Pub/Sub
Topics:
- doc-ingestion-events
Subscriptions:
- doc-ingestion-sub

## BigQuery datasets and tables
- dataset: llm_knowledge
    - table: chunks

## BigQuery table schema (llm_knowledge.chunks)
    - doc_id: STRING
    - chunk_text: STRING
    - source_url: STRING
    - ingested_at: TIMESTAMP
    - embedding: STRING

## MCP server tools (stdio)
- ask_gcp: answer a GCP question via the Vertex AI RAG agent
- search_gcp_docs: search the BigQuery-backed knowledge base
- ingest_gcp_doc: validate + store a document (Pub/Sub -> BigQuery)

## Repository structure (top level)
- .
- ./docs
- ./pubsub_archetype
- ./pubsub_archetype/schemas
- ./pubsub_archetype/tests
- ./scripts
- ./src
- ./src/portfolioadvanced_llm
- ./vertex_agent
- ./vertex_agent/tests

## End-to-end validation
Smoke test: scripts.gcp_smoke -> publish -> pull/ack roundtrip -> BigQuery insert+query -> smoke=ok
