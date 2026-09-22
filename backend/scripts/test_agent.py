#!/usr/bin/env python3
"""Local smoke test for the stock tool-calling agent.

Usage (from ``backend/`` with venv active and ``DEEPSEEK_API_KEY`` set):

    python scripts/test_agent.py
    python scripts/test_agent.py --question "What is the price of Apple stock?"
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai.agent import run_agent
from app.ai.openai_client import get_openai_client
from app.config import get_settings
from app.exceptions import LLMError


def main() -> int:
    parser = argparse.ArgumentParser(description="Test run_agent tool-calling loop.")
    parser.add_argument(
        "--question",
        default="Giá cổ phiếu hiện tại của Nvidia là bao nhiêu?",
        help="User question for the agent",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print agent / tool logs",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    get_settings.cache_clear()
    get_openai_client.cache_clear()
    settings = get_settings()

    print(f"model={settings.deepseek_model}", flush=True)
    print(f"question={args.question!r}", flush=True)

    try:
        answer = run_agent(args.question)
    except LLMError as exc:
        print(f"Error: {exc}", file=sys.stderr, flush=True)
        return 1

    print("\n--- final answer ---", flush=True)
    print(answer, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
