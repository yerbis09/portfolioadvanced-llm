from __future__ import annotations

import argparse
import json

from vertex_agent.agent import Agent
from vertex_agent.evaluation import evaluate_answer


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the agent with sample prompts.")
    parser.add_argument("--live", action="store_true", help="Use Vertex AI live generation.")
    parser.add_argument("--model", default=None, help="Optional Vertex AI model override.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    prompts = [
        (
            "How do I create a Pub/Sub subscription?",
            ["Pub/Sub", "subscription"],
        ),
        (
            "What does the validation gate do?",
            ["validate", "reject"],
        ),
    ]
    results = []
    for question, terms in prompts:
        if args.live:
            agent = Agent(model=args.model) if args.model else Agent()
            answer = agent.ask(question)
        else:
            answer = (
                "Pub/Sub subscription guidance: create a subscription, "
                "validate the message, and use the right ack path."
            )
        result = evaluate_answer(question, answer, terms)
        results.append(result)
    print(json.dumps([result.__dict__ for result in results], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
