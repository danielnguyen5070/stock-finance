from datetime import datetime
from typing import TypedDict


class StockPriceData(TypedDict):
    """Latest OHLCV bar for a stock symbol."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
