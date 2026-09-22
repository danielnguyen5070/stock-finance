#!/usr/bin/env python3
"""Local smoke test for the DeepSeek OpenAI-compatible client.

Usage (from ``backend/`` with venv active and ``DEEPSEEK_API_KEY`` set):

    python scripts/test_llm.py
    python scripts/test_llm.py --prompt "Say hello in one word"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ai import get_completion
from app.ai.openai_client import get_openai_client
from app.config import get_settings
from app.exceptions import LLMError


def main() -> int:
    parser = argparse.ArgumentParser(description="Test DeepSeek get_completion.")
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: ok",
        help="User prompt to send",
    )
    args = parser.parse_args()

    get_settings.cache_clear()
    get_openai_client.cache_clear()
    settings = get_settings()

    print(f"model={settings.deepseek_model}", flush=True)
    print(f"base_url={settings.deepseek_base_url}", flush=True)

    try:
        completion = get_completion(
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": args.prompt},
            ]
        )
    except LLMError as exc:
        print(f"Error: {exc}", file=sys.stderr, flush=True)
        return 1

    message = completion.choices[0].message
    print(f"finish_reason={completion.choices[0].finish_reason}", flush=True)
    print(f"content={message.content!r}", flush=True)
    if message.tool_calls:
        print(f"tool_calls={message.tool_calls}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
