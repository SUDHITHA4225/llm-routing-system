"""Simple interactive CLI for the LLM prompt router."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from app.llm_client import LLMClient, build_llm_client
from app.router import handle_message


def _build_client() -> LLMClient:
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    demo_mode = os.getenv("ROUTER_DEMO_MODE", "false").lower() == "true"
    return build_llm_client(api_key=api_key, model=model, demo_mode=demo_mode)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="LLM Prompt Router CLI")
    parser.add_argument(
        "--message",
        type=str,
        default="",
        help="Single message mode. If omitted, starts interactive mode.",
    )
    args = parser.parse_args()

    threshold = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD", "0.7"))
    log_path = Path(os.getenv("ROUTE_LOG_PATH", "route_log.jsonl"))
    client = _build_client()

    if args.message:
        result = handle_message(
            message=args.message,
            llm_client=client,
            log_path=log_path,
            confidence_threshold=threshold,
        )
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return

    print("LLM Prompt Router CLI")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("\nYou> ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Bye.")
            break
        if not user_input:
            continue

        result = handle_message(
            message=user_input,
            llm_client=client,
            log_path=log_path,
            confidence_threshold=threshold,
        )

        print(f"Intent: {result['intent']} (confidence={result['confidence']:.2f})")
        print(f"Assistant> {result['response']}")


if __name__ == "__main__":
    main()
