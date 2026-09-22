"""Stock market data services (Yahoo Finance).

Designed so a sibling ``crypto.py`` module can mirror the same patterns later.
"""

from __future__ import annotations

import logging
from typing import Any

import yfinance as yf

from app.config import Settings, get_settings
from app.exceptions import InvalidInputError, StockDataError, SymbolNotFoundError
from app.models.stock import StockPriceData

logger = logging.getLogger(__name__)

# Prefer equity quotes when searching by company name.
_PREFERRED_QUOTE_TYPES = ("EQUITY",)


def get_symbol(company: str, *, settings: Settings | None = None) -> str:
    """Resolve a company name to a stock ticker via Yahoo Finance search.

    Uses Yahoo's ``/v1/finance/search`` endpoint under the hood.

    Args:
        company: Company name or partial name (e.g. ``"Nvidia"``).

    Returns:
        Ticker symbol string (e.g. ``"NVDA"``).

    Raises:
        InvalidInputError: If ``company`` is empty.
        SymbolNotFoundError: If Yahoo returns no usable equity quote.
        StockDataError: If the search request fails.
    """
    query = company.strip()
    if not query:
        raise InvalidInputError("Company name must not be empty.")

    cfg = settings or get_settings()
    timeout = int(cfg.request_timeout_seconds)

    try:
        search = yf.Search(
            query,
            max_results=8,
            news_count=0,
            enable_fuzzy_query=True,
            timeout=timeout,
        )
        quotes: list[dict[str, Any]] = list(search.quotes or [])
    except Exception as exc:
        raise StockDataError(
            f"Yahoo Finance search failed for '{query}': {exc}"
        ) from exc

    symbol = _pick_equity_symbol(quotes)
    if not symbol:
        raise SymbolNotFoundError(
            f"No stock symbol found for company '{query}'."
        )

    logger.info("Resolved company '%s' → %s", query, symbol)
    return symbol


def get_stock_price(symbol: str, *, settings: Settings | None = None) -> StockPriceData:
    """Fetch the latest daily OHLCV bar for a ticker via ``yfinance``.

    Args:
        symbol: Stock ticker symbol (e.g. ``"NVDA"``).

    Returns:
        Dict with ``symbol``, ``timestamp``, ``open``, ``high``, ``low``,
        ``close``, and ``volume``.

    Raises:
        InvalidInputError: If ``symbol`` is empty.
        StockDataError: If price history is missing or yfinance fails.
    """
    _ = settings  # reserved for future provider config
    ticker = symbol.strip().upper()
    if not ticker:
        raise InvalidInputError("Symbol must not be empty.")

    try:
        history = yf.Ticker(ticker).history(period="5d", interval="1d")
    except Exception as exc:  # yfinance raises varied exception types
        raise StockDataError(
            f"Failed to fetch price data for '{ticker}': {exc}"
        ) from exc

    if history is None or history.empty:
        raise StockDataError(
            f"No price data available for symbol '{ticker}'."
        )

    row = history.iloc[-1]
    try:
        timestamp = row.name.to_pydatetime()
        result: StockPriceData = {
            "symbol": ticker,
            "timestamp": timestamp,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]),
        }
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise StockDataError(
            f"Malformed price data for symbol '{ticker}'."
        ) from exc

    logger.info(
        "Fetched %s close=%.4f volume=%s",
        ticker,
        result["close"],
        result["volume"],
    )
    return result


def _pick_equity_symbol(quotes: list[dict[str, Any]]) -> str | None:
    """Pick the best equity ticker from Yahoo search quotes."""
    equities = [
        quote
        for quote in quotes
        if isinstance(quote, dict)
        and quote.get("symbol")
        and str(quote.get("quoteType", "")).upper() in _PREFERRED_QUOTE_TYPES
    ]
    candidates = equities or [
        quote
        for quote in quotes
        if isinstance(quote, dict) and quote.get("symbol")
    ]
    if not candidates:
        return None
    return str(candidates[0]["symbol"]).upper()
