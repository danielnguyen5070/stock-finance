from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.exceptions import InvalidInputError, StockDataError, SymbolNotFoundError
from app.services import get_stock_price, get_symbol

router = APIRouter(prefix="/stocks", tags=["stocks"])


class SymbolResponse(BaseModel):
    company: str
    symbol: str


class StockPriceResponse(BaseModel):
    symbol: str
    timestamp: datetime
    open: float = Field(description="Opening price")
    high: float
    low: float
    close: float
    volume: int


@router.get("/symbol", response_model=SymbolResponse)
def lookup_symbol(
    company: str = Query(..., min_length=1, description="Company name, e.g. Nvidia"),
) -> SymbolResponse:
    """Resolve a company name to a stock ticker."""
    try:
        symbol = get_symbol(company)
    except InvalidInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SymbolNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StockDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SymbolResponse(company=company.strip(), symbol=symbol)


@router.get("/{symbol}/price", response_model=StockPriceResponse)
def lookup_stock_price(symbol: str) -> StockPriceResponse:
    """Return the latest daily OHLCV bar for a ticker."""
    try:
        data = get_stock_price(symbol)
    except InvalidInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except StockDataError as exc:
        # Distinguish unknown symbols from upstream failures when possible.
        status = 404 if "No price data" in str(exc) else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    return StockPriceResponse(**data)
