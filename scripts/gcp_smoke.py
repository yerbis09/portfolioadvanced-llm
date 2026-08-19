from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import UTC, datetime

from google.cloud import bigquery, pubsub_v1

from vertex_agent.ingester import Ingester


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Real GCP smoke test for Pub/Sub + BigQuery + the ingestion gate."
    )
    parser.add_argument("--project", default="portfolioadvanced-llm")
    parser.add_argument("--topic", default="doc-ingestion-events")
    parser.add_argument("--subscription", default="doc-ingestion-sub")
    parser.add_argument("--dataset", default="llm_knowledge")
    parser.add_argument("--table", default="chunks")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    project = args.project
    topic = f"projects/{project}/topics/{args.topic}"
    subscription = f"projects/{project}/subscriptions/{args.subscription}"
    table = f"{project}.{args.dataset}.{args.table}"
    trace_id = f"smoke-{uuid.uuid4().hex[:12]}"
    payload = {
        "trace_id": trace_id,
        "event_type": "data_ingest",
        "version": "1.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": {
            "content": "Google Cloud Pub/Sub routes messages reliably. " * 20,
            "source_url": "https://cloud.google.com/pubsub/docs/overview",
        },
    }
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")

    publisher = pubsub_v1.PublisherClient()
    message_id = publisher.publish(topic, body).result(timeout=60)
    print(f"published_message_id={message_id}")

    subscriber = pubsub_v1.SubscriberClient()
    received = None
    ack_ids: list[str] = []
    for _ in range(12):
        response = subscriber.pull(
            request={"subscription": subscription, "max_messages": 5},
            timeout=10,
        )
        for msg in response.received_messages:
            candidate = json.loads(msg.message.data.decode("utf-8"))
            if candidate.get("trace_id") == trace_id:
                received = candidate
                ack_ids.append(msg.ack_id)
                break
        if received:
            break
        time.sleep(1)

    if not received:
        raise RuntimeError("smoke pull failed: trace_id not observed on subscription")

    subscriber.acknowledge(
        request={"subscription": subscription, "ack_ids": ack_ids}
    )
    print(f"pubsub_roundtrip=ok trace_id={received['trace_id']}")

    ingester = Ingester(project=project)
    records = ingester.ingest_direct(payload)
    print(f"bq_insert_rows={len(records)}")

    bq = bigquery.Client(project=project)
    rows = list(
        bq.query(
            f"""
            SELECT doc_id, COUNT(*) AS chunk_count
            FROM `{table}`
            WHERE doc_id = @doc_id
            GROUP BY doc_id
            """,  # noqa: S608
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("doc_id", "STRING", trace_id)
                ]
            ),
        ).result()
    )
    if not rows:
        raise RuntimeError("smoke query failed: no BigQuery rows for trace_id")
    print(f"bq_query_rows={rows[0].chunk_count} doc_id={rows[0].doc_id}")
    print("smoke=ok")


if __name__ == "__main__":
    main()
