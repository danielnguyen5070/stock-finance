#!/usr/bin/env python3
"""Local smoke test for stock service functions.

Usage (from ``backend/`` with the venv active):

    python scripts/test_stock.py
    python scripts/test_stock.py --company "Apple" --symbol AAPL
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Allow running as ``python scripts/test_stock.py`` from backend/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.exceptions import MarketServiceError
from app.services import get_stock_price, get_symbol


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")


def main() -> int:
    parser = argparse.ArgumentParser(description="Test stock service helpers.")
    parser.add_argument(
        "--company",
        default="Nvidia",
        help="Company name for get_symbol (default: Nvidia)",
    )
    parser.add_argument(
        "--symbol",
        default=None,
        help="Optional ticker for get_stock_price (default: result of get_symbol)",
    )
    args = parser.parse_args()

    try:
        print(f"get_symbol({args.company!r}) …", flush=True)
        symbol = get_symbol(args.company)
        print(f"  → {symbol}\n", flush=True)

        ticker = args.symbol or symbol
        print(f"get_stock_price({ticker!r}) …", flush=True)
        price = get_stock_price(ticker)
        print(json.dumps(price, indent=2, default=_json_default), flush=True)
    except MarketServiceError as exc:
        print(f"Error: {exc}", file=sys.stderr, flush=True)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
