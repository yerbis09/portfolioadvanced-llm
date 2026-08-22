#!/usr/bin/env bash
# demo_up.sh — recrea la infra (si falta), valida el pipeline y prueba el MCP.
set -euo pipefail
PROJECT=portfolioadvanced-llm
cd "$(dirname "$0")"

echo "== 1. Proyecto =="
gcloud config set project "$PROJECT" >/dev/null

echo "== 2. Pub/Sub (crea si no existe) =="
gcloud pubsub topics create doc-ingestion-events 2>/dev/null || echo "  topic ya existe"
gcloud pubsub subscriptions create doc-ingestion-sub --topic=doc-ingestion-events 2>/dev/null || echo "  sub ya existe"

echo "== 3. BigQuery (crea si no existe) =="
bq --location=US mk --dataset "${PROJECT}:llm_knowledge" 2>/dev/null || echo "  dataset ya existe"
bq mk --table "${PROJECT}:llm_knowledge.chunks" \
  doc_id:STRING,chunk_text:STRING,source_url:STRING,ingested_at:TIMESTAMP,embedding:STRING 2>/dev/null || echo "  tabla ya existe"

echo "== 4. Smoke test end-to-end =="
uv run python -m scripts.gcp_smoke

echo "== 5. Servidor MCP: handshake + tools =="
uv run python -c "
import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
    p = StdioServerParameters(command='uv', args=['run','python','-m','vertex_agent.mcp_server'])
    async with stdio_client(p) as (r,w):
        async with ClientSession(r,w) as s:
            await s.initialize()
            t = await s.list_tools()
            print('HERRAMIENTAS MCP:', [x.name for x in t.tools])
anyio.run(main)
"
echo "== DEMO OK: infra levantada, smoke=ok, MCP responde =="
