from __future__ import annotations

import argparse
import json

from vertex_agent.monitoring import MetricRecord, MetricsPublisher


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish evaluation metrics to BigQuery.")
    parser.add_argument("--project", default="portfolioadvanced-llm")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--score", type=float, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    publisher = MetricsPublisher(project=args.project)
    errors = publisher.publish(
        [MetricRecord(run_id=args.run_id, question=args.question, score=args.score)]
    )
    print(json.dumps({"errors": errors}, indent=2))


if __name__ == "__main__":
    main()
