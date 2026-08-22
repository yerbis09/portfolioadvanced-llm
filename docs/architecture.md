# Architecture diagram notes

Use this page as the linked source for the presentation diagram.

## Main flow

```text
Cloud Storage docs
   ↓
Document AI
   ↓
Pub/Sub ingestion events
   ↓
Python validation gate
   ↓
BigQuery knowledge corpus
   ↓
Vertex AI RAG agent
   ↓
MCP server
```

## Feedback loop

```text
Vertex AI RAG agent
   ├─→ Metrics / evaluation
   └─→ Retraining signals

OAuth / ADC smoke tests
   ├─→ Pub/Sub round-trip
   └─→ BigQuery insert/query
```

## How the process works

1. Docs are ingested from Cloud Storage.
2. Document AI extracts usable text.
3. Pub/Sub transports ingestion events.
4. The Python gate rejects invalid payloads before publish.
5. BigQuery becomes the knowledge base.
6. Vertex AI uses the corpus to answer questions.
7. The MCP server exposes the capability to tools and agents.
8. Smoke tests prove the full path against real infrastructure.

## Live infrastructure (validated, smoke=ok)

~~~mermaid
flowchart LR
    C[["MCP client (Copilot / Claude)"]]
    MCP["vertex_agent.mcp_server (stdio)"]
    GATE{{"pubsub_archetype gate"}}
    PS["Pub/Sub: doc-ingestion-events / -sub"]
    ING["Ingester (chunk + overlap)"]
    BQ[("BigQuery: llm_knowledge.chunks")]
    VTX["Vertex AI RAG agent"]
    C -->|stdio JSON-RPC| MCP
    MCP -->|ingest_gcp_doc| GATE
    GATE -->|valid| PS
    PS --> ING
    ING --> BQ
    MCP -->|search_gcp_docs| BQ
    MCP -->|ask_gcp| VTX
    VTX -->|grounding| BQ
~~~

| Resource | Name | Type |
| --- | --- | --- |
| Pub/Sub topic | doc-ingestion-events | messaging |
| Pub/Sub subscription | doc-ingestion-sub | messaging |
| BigQuery dataset | llm_knowledge | analytics |
| BigQuery table | chunks | analytics |
