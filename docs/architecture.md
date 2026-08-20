# Architecture outline for Lucidchart

## Boxes

- Official GCP docs
- Document AI processor
- Pub/Sub topic: `doc-ingestion-events`
- Python validation gate
- BigQuery dataset: `llm_knowledge`
- Vertex AI RAG agent
- MCP server
- Metrics and retraining signals

## Arrows

- Official GCP docs → Document AI processor
- Document AI processor → Pub/Sub topic: `doc-ingestion-events`
- Pub/Sub topic: `doc-ingestion-events` → Python validation gate
- Python validation gate → BigQuery dataset: `llm_knowledge`
- BigQuery dataset: `llm_knowledge` → Vertex AI RAG agent
- Vertex AI RAG agent → MCP server
- Vertex AI RAG agent → Metrics and retraining signals

## Smoke test flow

- Developer authenticates with OAuth / ADC
- Developer publishes a valid payload to Pub/Sub
- Subscriber round-trip is verified
- BigQuery insert/query is verified
- Smoke test reports `smoke=ok`
