from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from .polygon_api import _get_headers, POLYGON_BASE_URL
import requests

class TickerDetails(BaseModel):
    """Detailed information about a ticker."""
    ticker: str
    name: str
    market: str
    locale: str
    primary_exchange: str
    type: str
    active: bool
    currency_name: str
    cik: Optional[str] = None
    composite_figi: Optional[str] = None
    share_class_figi: Optional[str] = None
    market_cap: Optional[float] = None
    phone_number: Optional[str] = None
    address: Optional[dict] = None
    description: Optional[str] = None
    sic_code: Optional[str] = None
    sic_description: Optional[str] = None
    ticker_root: Optional[str] = None
    homepage_url: Optional[str] = None
    total_employees: Optional[int] = None
    list_date: Optional[str] = None
    share_class_shares_outstanding: Optional[int] = None
    weighted_shares_outstanding: Optional[int] = None

class DividendEvent(BaseModel):
    """Dividend event information."""
    cash_amount: float
    declaration_date: Optional[str]
    dividend_type: str
    ex_dividend_date: str
    frequency: int
    pay_date: str
    record_date: str

class StockSplit(BaseModel):
    """Stock split information."""
    execution_date: str
    split_from: float
    split_to: float

def get_ticker_details(ticker: str) -> Optional[TickerDetails]:
    """Get detailed information about a ticker."""
    url = f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker}"
    response = requests.get(url, headers=_get_headers())
    
    if response.status_code != 200:
        return None

    data = response.json()
    if not data.get("results"):
        return None

    return TickerDetails(**data["results"])

def get_dividends(ticker: str, start_date: str, end_date: str) -> List[DividendEvent]:
    """Get dividend events for a ticker."""
    url = f"{POLYGON_BASE_URL}/v3/reference/dividends"
    params = {
        "ticker": ticker,
        "ex_dividend_date.gte": start_date,
        "ex_dividend_date.lte": end_date
    }
    
    response = requests.get(url, headers=_get_headers(), params=params)
    if response.status_code != 200:
        return []

    data = response.json()
    if not data.get("results"):
        return []

    return [DividendEvent(**event) for event in data["results"]]

def get_stock_splits(ticker: str, start_date: str, end_date: str) -> List[StockSplit]:
    """Get stock split events for a ticker."""
    url = f"{POLYGON_BASE_URL}/v3/reference/splits"
    params = {
        "ticker": ticker,
        "execution_date.gte": start_date,
        "execution_date.lte": end_date
    }
    
    response = requests.get(url, headers=_get_headers(), params=params)
    if response.status_code != 200:
        return []

    data = response.json()
    if not data.get("results"):
        return []

    return [StockSplit(**split) for split in data["results"]]

def get_market_status() -> dict:
    """Get current market status and upcoming market holidays."""
    url = f"{POLYGON_BASE_URL}/v1/marketstatus/now"
    response = requests.get(url, headers=_get_headers())
    
    if response.status_code != 200:
        return {}

    return response.json()

def get_market_holidays() -> List[dict]:
    """Get list of market holidays."""
    url = f"{POLYGON_BASE_URL}/v1/marketstatus/upcoming"
    response = requests.get(url, headers=_get_headers())
    
    if response.status_code != 200:
        return []

    return response.json()

def get_technical_indicators(ticker: str, indicator: str, params: dict) -> dict:
    """Get technical indicators for a ticker.
    
    Available indicators: sma, ema, rsi, macd
    """
    url = f"{POLYGON_BASE_URL}/v1/indicators/{indicator}/{ticker}"
    response = requests.get(url, headers=_get_headers(), params=params)
    
    if response.status_code != 200:
        return {}

    return response.json()