from __future__ import annotations

import argparse

from vertex_agent.retraining import RetrainingSignal, RetrainingTrigger


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a retraining signal to Pub/Sub.")
    parser.add_argument("--project", default="portfolioadvanced-llm")
    parser.add_argument("--topic", default="doc-retraining-events")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--score", type=float, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    trigger = RetrainingTrigger(project=args.project, topic=args.topic)
    message_id = trigger.publish(
        RetrainingSignal(reason=args.reason, source=args.source, score=args.score)
    )
    print(f"published_message_id={message_id}")


if __name__ == "__main__":
    main()
