#!/usr/bin/env python3
"""Local smoke test for run_agent_stream (SSE event payloads).

Usage:

    python scripts/test_agent_stream.py
    python scripts/test_agent_stream.py --question "What is Apple's price?"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.agent import run_agent_stream
from app.ai.openai_client import get_openai_client
from app.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Test run_agent_stream events.")
    parser.add_argument(
        "--question",
        default="Giá cổ phiếu hiện tại của Nvidia là bao nhiêu?",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s %(name)s: %(message)s",
        )

    get_settings.cache_clear()
    get_openai_client.cache_clear()

    print(f"question={args.question!r}", flush=True)
    tokens: list[str] = []

    for event in run_agent_stream(args.question):
        if event.get("type") == "token":
            tokens.append(event.get("content") or "")
            print(event["content"], end="", flush=True)
        else:
            if tokens:
                print(flush=True)
                tokens.clear()
            print(json.dumps(event, ensure_ascii=False, default=str), flush=True)
            if event.get("type") in {"done", "error"}:
                return 0 if event.get("type") == "done" else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
