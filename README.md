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
- Diagrams: [docs/architecture.md](docs/architecture.md)
- Public portfolio: [workedtowork](https://yerbis09.github.io/workedtowork/)

## Architecture

See [docs/architecture.md](docs/architecture.md) for a Lucidchart-ready outline.

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
