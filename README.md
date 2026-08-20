# portfolioadvanced-llm

A **total validation gate** for Cloud Pub/Sub payloads, implemented in idiomatic Python.
`Archetype.validate()` never raises on malformed input — errors are values, not exceptions.
Built to feed a GCP-native LLM agent that continuously improves Google Cloud services.

---

## Why Python over Java

The upstream reference implementation ([GoogleCloudPlatform/pubsub PR #425](https://github.com/GoogleCloudPlatform/pubsub/pull/425)) is Java 8 + Maven.
This port makes the same guarantees with a fraction of the ceremony:

| Concern | Java (PR #425) | Python (this repo) |
|---|---|---|
| Schema cache | 30-line `_SchemaRegistry` Singleton + `Lock` | `@functools.cache` — 1 line, thread-safe |
| Immutable config object | Builder pattern (`.withX().build()`) | `dataclass(frozen=True)` + keyword args |
| Value object | Jackson `record` / Lombok boilerplate | `dataclass(frozen=True, slots=True)` |
| Structured errors | Pre-formatted strings | `ValidationError(path, code, message)` |
| SDK decoupling | Interface + Adapter | `Protocol` — structural typing, no wrappers |
| Unicode canonicalization | 3rd-party lib | `unicodedata.normalize("NFC", ...)` in stdlib |
| Total lines | ~800 | ~250 |
| Build tool | Maven + 5 transitive deps | `uv` + 2 deps (`jsonschema`, stdlib only) |

---

## Architecture

```
                          raw bytes
                              |
                    ┌─────────▼──────────┐
                    │     Archetype      │  total function — never raises
                    │  .from_path(...)   │
                    │  .from_stream(...) │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       1. Canonicalize   2. Syntactic    3. Structural
       decode + NFC      json.loads()    Draft7Validator
              │               │               │
              └───────────────┴───────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
   ValidationResult.accepted(canonical)  ValidationResult.rejected(errors)
              │                               │
         publish to topic             [ValidationError(path, code, message), ...]
                                       never enqueued


   Subscriber side:
   ┌────────────────────────────────────────────────────────┐
   │  ClassifyingReceiver(handler=fn, quarantine=fn)        │
   │                                                        │
   │  handler OK          → ack()                           │
   │  TransientError      → nack() → Pub/Sub retry backoff  │
   │  FunctionalRejectError → ack() + quarantine()          │
   └────────────────────────────────────────────────────────┘
```

---

## Getting started

**Requirements**: Python 3.13+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/yerbis09/portfolioadvanced-llm.git
cd portfolioadvanced-llm
uv sync --group dev

# Offline demo — runs the gate over representative payloads
uv run python -m pubsub_archetype.gateway

# Tests
uv run pytest -v

# MCP server (stdio)
uv run portfolioadvanced-llm-mcp

# Lint + format
uv run ruff check pubsub_archetype/
uv run ruff format --check pubsub_archetype/
```

**WSL users**: everything is pre-configured in WSL. `bash push.sh` to push using your token from `local.settings`.

### OAuth / ADC for real GCP smoke tests

This repo does **not** store service account keys. For real GCP integration tests,
each user authenticates with their own Google account and ADC:

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project portfolioadvanced-llm
```

Then run the smoke test:

```bash
uv run python -m scripts.gcp_smoke
```

The smoke script uses:
- Pub/Sub publish/pull
- the validation gate in `vertex_agent.ingester`
- BigQuery inserts/queries

If you use another project, pass `--project`, `--topic`, `--subscription`,
`--dataset`, and `--table` explicitly.

---

## Quality gates

Every commit and PR must pass all four gates in order:

```
1. detect-secrets scan   — no credentials in source
2. ruff check + format   — zero lint errors, canonical format
3. pytest --cov ≥ 70%    — currently 98.92%
4. sonar analyze DEEP    — zero issues (SonarQube Cloud, org: yerbis09)
```

GitHub Actions enforces this automatically:
- [`ci.yml`](.github/workflows/ci.yml) — runs on every push
- [`pr-gate.yml`](.github/workflows/pr-gate.yml) — blocks merge until all gates pass

CI requires `SONAR_TOKEN` secret set in the repository settings.

---

## Core API

```python
from pubsub_archetype import Archetype, ClassifyingReceiver, TransientError, FunctionalRejectError

# Build the gate once (schema is cached by functools.cache)
gate = Archetype.from_path("pubsub_archetype/schemas/archetype.schema.json")

# Validate before publishing
result = gate.validate(raw_bytes, declared_charset="utf-8")
if result.is_accepted:
    publisher.publish(topic, result.canonical.encode())
else:
    for err in result.errors:
        log.warning("%s [%s]: %s", err.code, err.path, err.message)

# Subscriber with three-way classification
receiver = ClassifyingReceiver(
    handler=process_message,
    quarantine=send_to_dead_letter,
)
streaming_pull_future = subscriber.subscribe(subscription, receiver.handle)
```

---

## Adapting the schema

Replace [`pubsub_archetype/schemas/archetype.schema.json`](pubsub_archetype/schemas/archetype.schema.json)
with your own JSON Schema (Draft 7). The gate validates any payload against it at the ingestion point.

The bundled schema enforces:

```json
{
  "required": ["event_type", "payload", "version"],
  "properties": {
    "event_type": { "enum": ["llm_request", "llm_response", "eval_result", "data_ingest"] },
    "version":    { "pattern": "^\\d+\\.\\d+$" }
  },
  "additionalProperties": false
}
```

---

## Upstream contribution

The design is contributed back to the GoogleCloudPlatform ecosystem via
**[GoogleCloudPlatform/pubsub PR #425](https://github.com/GoogleCloudPlatform/pubsub/pull/425)**
(Java reference implementation, open for review).

> **Note**: PR #425 requires signing the [Google CLA](https://cla.developers.google.com/) before it can be merged.

---

## Roadmap

### Phase 1 — Validation gate ✅ (current)
- [x] `Archetype` gate with total `validate()` function
- [x] `ClassifyingReceiver` with three-way subscriber decision
- [x] `ValidationError` as structured data (path, code, message)
- [x] 98.92% test coverage, ruff clean, SonarQube 0 issues
- [x] CI/CD with secrets scanning, lint, tests, Sonar gates
- [x] GCP project `portfolioadvanced-llm` provisioned (Vertex AI, BigQuery, Pub/Sub, Storage, Document AI)

### Phase 2 — GCP documentation ingestion pipeline
- [ ] Cloud Storage bucket for official GCP documentation (PDFs, HTML)
- [ ] Document AI processor to extract structured text from docs
- [ ] Pub/Sub topic + archetype schema for document ingestion events
- [ ] BigQuery dataset to store extracted knowledge chunks
- [ ] Cloud Run job for batch ingestion pipeline

### Phase 3 — Vertex AI LLM agent
- [ ] Vertex AI corpus from BigQuery knowledge base
- [ ] Gemini fine-tuning / grounding with GCP official docs
- [ ] Agent that answers questions about GCP service configuration
- [ ] Evaluation pipeline (ROUGE, human eval) via Vertex AI Model Evaluation
- [ ] Continuous retraining trigger on new documentation ingestion

### Phase 4 — MCP server + continuous improvement loop
- [x] MCP (Model Context Protocol) server exposing GCP knowledge to AI coding agents
- [ ] Copilot / Claude integration via `.mcp.json` (already wired in this repo)
- [ ] Agent-driven GCP service improvement suggestions with PR generation
- [ ] Monitoring dashboard in BigQuery + Looker Studio
- [ ] Feedback loop: agent suggestions → human review → knowledge base update

## Project structure

```
portfolioadvanced-llm/
├── pubsub_archetype/
│   ├── archetype.py              # The gate — Archetype.validate() total function
│   ├── validation_result.py      # ValidationResult + ValidationError value objects
│   ├── classifying_receiver.py   # ClassifyingReceiver + TransientError/FunctionalRejectError
│   ├── gateway.py                # Entry point + offline demo
│   ├── schemas/
│   │   └── archetype.schema.json # Canonical contract (replace with your own)
│   └── tests/
│       ├── test_archetype.py
│       ├── test_classifying_receiver.py
│       └── test_gateway.py
├── vertex_agent/
│   ├── ingester.py                # Pub/Sub -> BigQuery chunk pipeline
│   ├── retriever.py               # BigQuery retrieval layer
│   ├── agent.py                   # Vertex AI Gemini RAG agent
│   ├── mcp_server.py              # MCP stdio server wrapping the agent
│   └── tests/
│       ├── test_vertex_agent.py
│       └── test_mcp_server.py
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                # Push CI: secrets → lint → tests → sonar
│   │   └── pr-gate.yml           # PR blocker: all gates must pass
│   └── instructions/
│       └── sonarqube.instructions.md
├── sonar-project.properties
├── pyproject.toml                # uv project, ruff config, pytest config
└── push.sh                       # WSL push helper (reads token from local.settings)
```

---

## License

Apache 2.0 — consistent with the upstream GoogleCloudPlatform/pubsub repository.
