# portfolioadvanced-llm

Python companion project for the Pub/Sub gate idea: a clean validation layer,
real GCP smoke tests, a GCP-native ingestion pipeline, and an MCP entrypoint.

## What it shows

- Total validation gate for Pub/Sub payloads
- Document AI → Pub/Sub → BigQuery ingestion path
- Vertex AI RAG agent and MCP server
- OAuth/ADC smoke tests against real GCP

## References

- Upstream Java PR: [GoogleCloudPlatform/pubsub#425](https://github.com/GoogleCloudPlatform/pubsub/pull/425)
- Companion write-up: [PYTHON_COMPANION.md](PYTHON_COMPANION.md)
- Draw.io diagram: [docs/architecture.drawio](docs/architecture.drawio)
- Public portfolio: [workedtowork](https://yerbis09.github.io/workedtowork/)

## Architecture

The architecture is drawn in [docs/architecture.drawio](docs/architecture.drawio)
and shows:

1. GCP docs stored in Cloud Storage
2. Document AI extraction
3. Pub/Sub ingestion events
4. The Python validation gate
5. BigQuery as the knowledge corpus
6. Vertex AI RAG answers
7. MCP exposure for coding agents
8. Metrics and retraining feedback
9. OAuth/ADC smoke tests on real infrastructure

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
