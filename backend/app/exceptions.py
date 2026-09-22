"""Shared exception types for market data services."""


class MarketServiceError(Exception):
    """Base error for market data lookups."""


class InvalidInputError(MarketServiceError):
    """Raised when a caller passes an empty or invalid argument."""


class SymbolNotFoundError(MarketServiceError):
    """Raised when no stock symbol matches the company name."""


class StockDataError(MarketServiceError):
    """Raised when stock price data cannot be retrieved."""
