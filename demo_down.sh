#!/usr/bin/env bash
# demo_down.sh — elimina la infra de GCP creada para la demo.
set -uo pipefail
PROJECT=portfolioadvanced-llm
gcloud config set project "$PROJECT" >/dev/null

echo "== Borrando Pub/Sub =="
gcloud pubsub subscriptions delete doc-ingestion-sub 2>/dev/null || echo "  sub no existe"
gcloud pubsub topics delete doc-ingestion-events 2>/dev/null || echo "  topic no existe"

echo "== Borrando BigQuery =="
bq rm -r -f -d "${PROJECT}:llm_knowledge" 2>/dev/null || echo "  dataset no existe"

echo "== DEMO DOWN: infra eliminada =="
