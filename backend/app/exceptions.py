"""Shared exception types for market data and LLM services."""


class MarketServiceError(Exception):
    """Base error for market data lookups."""


class InvalidInputError(MarketServiceError):
    """Raised when a caller passes an empty or invalid argument."""


class SymbolNotFoundError(MarketServiceError):
    """Raised when no stock symbol matches the company name."""


class StockDataError(MarketServiceError):
    """Raised when stock price data cannot be retrieved."""


class LLMError(Exception):
    """Base error for LLM client failures."""


class LLMConfigError(LLMError):
    """Raised when LLM credentials or settings are missing/invalid."""


class LLMRequestError(LLMError):
    """Raised when the LLM API request fails."""
