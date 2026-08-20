# portfolioadvanced-llm

Python companion project for the Pub/Sub gate idea: a clean validation layer,
a real GCP ingestion pipeline, an MCP entrypoint, and smoke tests against live
infrastructure.

## What it shows

- A total validation gate for Pub/Sub payloads
- A Document AI → Pub/Sub → BigQuery ingestion path
- A Vertex AI RAG agent and MCP server
- OAuth/ADC smoke tests against real GCP

## References

- Upstream Java PR: [GoogleCloudPlatform/pubsub#425](https://github.com/GoogleCloudPlatform/pubsub/pull/425)
- Companion write-up: [PYTHON_COMPANION.md](PYTHON_COMPANION.md)
- Linked diagrams: [docs/architecture.md](docs/architecture.md)
- Public portfolio: [workedtowork](https://yerbis09.github.io/workedtowork/)

## Architecture

See [docs/architecture.md](docs/architecture.md). It explains the flow in
English and keeps the diagram source linked from the README.

The process is:

1. Official GCP docs are stored in Cloud Storage.
2. Document AI extracts text and structure from each document.
3. Pub/Sub carries ingestion events into the Python validation gate.
4. The gate rejects invalid payloads before they are published downstream.
5. BigQuery stores the extracted chunks as the knowledge corpus.
6. Vertex AI answers questions with grounded context from that corpus.
7. The MCP server exposes the capability to coding agents.
8. Metrics and retraining signals close the feedback loop.
9. OAuth/ADC smoke tests prove the pipeline on real infrastructure.

## Run

```bash
uv sync --group dev
uv run pytest
uv run python -m scripts.gcp_smoke
uv run portfolioadvanced-llm-mcp
```

For real GCP smoke tests:

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project portfolioadvanced-llm
```

## Notes

- No service account keys are stored in the repo.
- The smoke test is intended to be run by each developer with their own OAuth/ADC.
- The detailed companion and integration notes live in `PYTHON_COMPANION.md`.
