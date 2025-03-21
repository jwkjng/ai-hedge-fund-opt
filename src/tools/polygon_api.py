import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Union
from pydantic import BaseModel
import time
import threading
import random
import json

from data.cache import get_cache
from data.models import News, MarketData

# Initialize cache and rate limiting variables
_cache = get_cache()
_rate_limit_lock = threading.Lock()
_last_request_time = 0
_retry_count = 0
_min_request_interval = 0.1  # 100ms between requests

# Polygon.io API configuration
POLYGON_BASE_URL = "https://api.polygon.io"
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY")

# Rate limiting configuration
_rate_limit_lock = threading.Lock()
_last_request_time = 0
_min_request_interval = 1.0  # 1 second between requests
_retry_count = 0
_max_retries = 5
_base_backoff = 45.0  # Base backoff time in seconds (45 seconds for first retry)

# Pydantic models for Polygon.io responses
class Price(BaseModel):
    time: str  # ISO format date
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None

class FinancialMetrics(BaseModel):
    report_period: str
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    net_income: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    operating_income: Optional[float] = None
    operating_expense: Optional[float] = None
    free_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    research_and_development: Optional[float] = None
    depreciation_and_amortization: Optional[float] = None
    working_capital: Optional[float] = None
    outstanding_shares: Optional[int] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    return_on_equity: Optional[float] = None
    net_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    book_value_growth: Optional[float] = None
    price_to_earnings_ratio: Optional[float] = None
    price_to_book_ratio: Optional[float] = None
    price_to_sales_ratio: Optional[float] = None
    free_cash_flow_per_share: Optional[float] = None
    earnings_per_share: Optional[float] = None

class CompanyNews(BaseModel):
    date: str
    title: str
    url: str
    source: str
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    tickers: list[str]

class InsiderTrade(BaseModel):
    filing_date: str
    transaction_date: Optional[str] = None
    insider_name: str = ''
    transaction_type: str
    shares: int = 0
    price_per_share: float = 0.0
    total_value: float = 0.0
    shares_owned: Optional[int] = None

def _rate_limited_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make a rate-limited HTTP request with retries."""
    global _last_request_time, _retry_count
    
    # Add API key to params if not already present
    if "params" not in kwargs:
        kwargs["params"] = {}
    if "apiKey" not in kwargs["params"]:
        kwargs["params"]["apiKey"] = os.getenv("POLYGON_API_KEY")
    
    with _rate_limit_lock:
        current_time = time.time()
        time_since_last_request = current_time - _last_request_time
        if time_since_last_request < _min_request_interval:
            time.sleep(_min_request_interval - time_since_last_request)
        
        response = requests.request(method, url, **kwargs)
        _last_request_time = time.time()
        
        # Only retry on rate limit errors (429)
        if response.status_code == 429:
            while _retry_count < _max_retries:
                # Exponential backoff with jitter, starting at 45 seconds
                sleep_time = _base_backoff * (2 ** _retry_count) + random.uniform(0, 1)
                print(f"Rate limit hit, waiting {sleep_time:.2f} seconds before retry {_retry_count + 1}/{_max_retries}")
                time.sleep(sleep_time)
                response = requests.request(method, url, **kwargs)
                _retry_count += 1
                _last_request_time = time.time()
                
                # If we get a non-429 response after retry, return it
                if response.status_code != 429:
                    _retry_count = 0
                    return response
            
            # If we've exhausted all retries, raise an exception
            _retry_count = 0
            raise requests.exceptions.TooManyRequests("Max retries exceeded for rate limit")
        elif not response.ok:
            # For any other error status code, raise an exception immediately
            raise requests.exceptions.RequestException(f"Request failed with status code {response.status_code}: {response.text}")
        
        _retry_count = 0  # Reset retry count for successful requests
        return response

def _get_headers() -> dict[str, str]:
    """Get headers for Polygon.io API requests."""
    return {
        "Authorization": f"Bearer {os.getenv('POLYGON_API_KEY')}",
        "Content-Type": "application/json"
    }

def get_prices(ticker: str, start_date: str, end_date: str) -> list[Price]:
    """Fetch price data from cache or Polygon.io API."""
    # Check cache first
    if cached_data := _cache.get_prices(ticker):
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # Fetch from Polygon.io API
    url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    response = _rate_limited_request("GET", url, headers=_get_headers())
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

    data = response.json()
    if not data.get("results"):
        return []

    # Convert Polygon.io format to our Price model
    prices = []
    for result in data["results"]:
        price = Price(
            time=datetime.fromtimestamp(result["t"] / 1000).strftime("%Y-%m-%d"),
            open=result["o"],
            high=result["h"],
            low=result["l"],
            close=result["c"],
            volume=result["v"],
            vwap=result.get("vw"),
            transactions=result.get("n")
        )
        prices.append(price)

    # Cache the results
    _cache.set_prices(ticker, [p.model_dump() for p in prices])
    return prices

def get_financial_metrics(
    ticker: str,
    end_date: str,
    period: str = "ttm",
    limit: int = 10,
) -> list[FinancialMetrics]:
    """Fetch financial metrics from cache or Polygon.io API."""
    # Check cache first
    if cached_data := _cache.get_financial_metrics(ticker):
        filtered_data = [FinancialMetrics(**metric) for metric in cached_data if metric["report_period"] <= end_date]
        filtered_data.sort(key=lambda x: x.report_period, reverse=True)
        if filtered_data:
            return filtered_data[:limit]

    # Fetch from Polygon.io API
    url = f"{POLYGON_BASE_URL}/vX/reference/financials"
    params = {
        "ticker": ticker,
        "filing_date.lte": end_date,
        "limit": limit,
        "timeframe": period,  # ttm, annual, or quarterly
        "include_sources": True,  # Get detailed breakdowns
        "order": "desc",  # Get most recent first
        "sort": "filing_date"
    }
    
    response = _rate_limited_request("GET", url, headers=_get_headers(), params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

    data = response.json()
    if not data.get("results"):
        return []

    metrics = []
    for result in data["results"]:
        financials = result.get("financials", {})
        balance_sheet = financials.get("balance_sheet", {})
        income_statement = financials.get("income_statement", {})
        cash_flow_statement = financials.get("cash_flow_statement", {})
        
        # Extract basic metrics
        total_assets = _get_value(balance_sheet.get("assets"))
        total_liabilities = _get_value(balance_sheet.get("liabilities"))
        shareholders_equity = _get_value(balance_sheet.get("equity"))
        current_assets = _get_value(balance_sheet.get("current_assets"))
        current_liabilities = _get_value(balance_sheet.get("current_liabilities"))
        net_income = _get_value(income_statement.get("net_income_loss"))
        revenue = _get_value(income_statement.get("revenues"))
        operating_income = _get_value(income_statement.get("operating_income_loss"))
        operating_expense = _get_value(income_statement.get("operating_expenses"))
        
        # Calculate ratios and derived metrics
        debt_to_equity = total_liabilities / shareholders_equity if shareholders_equity and total_liabilities else None
        current_ratio = current_assets / current_liabilities if current_assets and current_liabilities else None
        return_on_equity = net_income / shareholders_equity if shareholders_equity and net_income else None
        net_margin = net_income / revenue if revenue and net_income else None
        operating_margin = operating_income / revenue if revenue and operating_income else None
        
        # Get market data for price ratios
        market_cap = result.get("market_cap")
        shares_outstanding = _get_value(balance_sheet.get("shares_outstanding"))
        if market_cap and shares_outstanding:
            stock_price = market_cap / shares_outstanding
            pe_ratio = stock_price / (net_income / shares_outstanding) if net_income else None
            pb_ratio = stock_price / (shareholders_equity / shares_outstanding) if shareholders_equity else None
            ps_ratio = stock_price / (revenue / shares_outstanding) if revenue else None
        else:
            pe_ratio = pb_ratio = ps_ratio = None
        
        # Calculate growth rates if previous period data is available
        if len(metrics) > 0:
            prev = metrics[-1]
            revenue_growth = (revenue - prev.revenue) / abs(prev.revenue) if revenue and prev.revenue else None
            earnings_growth = (net_income - prev.net_income) / abs(prev.net_income) if net_income and prev.net_income else None
            book_value_growth = ((shareholders_equity - prev.total_assets + prev.total_liabilities) / 
                               abs(prev.total_assets - prev.total_liabilities)) if shareholders_equity and prev.total_assets and prev.total_liabilities else None
        else:
            revenue_growth = earnings_growth = book_value_growth = None
        
        metric = FinancialMetrics(
            report_period=result.get("end_date", result.get("filing_date")),
            market_cap=market_cap,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            ps_ratio=ps_ratio,
            revenue=revenue,
            gross_profit=_get_value(income_statement.get("gross_profit")),
            net_income=net_income,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            current_assets=current_assets,
            current_liabilities=current_liabilities,
            operating_income=operating_income,
            operating_expense=operating_expense,
            free_cash_flow=_get_value(cash_flow_statement.get("free_cash_flow")),
            capital_expenditure=_get_value(cash_flow_statement.get("capital_expenditure")),
            research_and_development=_get_value(income_statement.get("research_and_development")),
            depreciation_and_amortization=_get_value(income_statement.get("depreciation_and_amortization")),
            working_capital=current_assets - current_liabilities if current_assets and current_liabilities else None,
            outstanding_shares=shares_outstanding,
            debt_to_equity=debt_to_equity,
            current_ratio=current_ratio,
            return_on_equity=return_on_equity,
            net_margin=net_margin,
            operating_margin=operating_margin,
            revenue_growth=revenue_growth,
            earnings_growth=earnings_growth,
            book_value_growth=book_value_growth,
            price_to_earnings_ratio=pe_ratio,
            price_to_book_ratio=pb_ratio,
            price_to_sales_ratio=ps_ratio,
            free_cash_flow_per_share=_get_value(cash_flow_statement.get("free_cash_flow")) / shares_outstanding if shares_outstanding else None,
            earnings_per_share=net_income / shares_outstanding if shares_outstanding else None
        )
        metrics.append(metric)

    # Cache the results
    _cache.set_financial_metrics(ticker, [m.model_dump() for m in metrics])
    return metrics

def _get_value(data: dict | None) -> float | None:
    """Helper function to extract value from financial data point."""
    if not data or not isinstance(data, dict):
        return None
    return data.get("value")

def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str,
    period: str = "annual",
    limit: int = 5,
) -> list[dict]:
    """Search for specific financial line items using Polygon.io's financials endpoint."""
    # Get financial metrics which already contain all the line items we need
    metrics = get_financial_metrics(ticker, end_date, period, limit)
    
    # Convert metrics to dictionaries
    return [m.model_dump() for m in metrics]

def get_company_news(ticker: str, end_date: Union[str, datetime], start_date: Optional[Union[str, datetime]] = None, test_mode: bool = False) -> List[News]:
    """Get company news for a ticker."""
    # Test response for development/testing
    test_response = {
        "status": "OK",
        "count": 2,
        "results": [
            {
                "published_utc": "2024-03-15T14:30:00Z",
                "title": "Test Company Reports Strong Q4 Results",
                "article_url": "https://example.com/article1",
                "publisher": {"name": "Test News"},
                "description": "The company reported better than expected earnings.",
                "keywords": ["earnings", "growth"],
                "tickers": [ticker]
            },
            {
                "published_utc": "2024-03-14T09:15:00Z",
                "title": "Test Company Announces New Product",
                "article_url": "https://example.com/article2",
                "publisher": {"name": "Test News"},
                "description": "The company unveiled its latest innovation.",
                "keywords": ["product", "innovation"],
                "tickers": [ticker]
            }
        ]
    }

    # Check cache first
    if cached_data := _cache.get_company_news(ticker, News):
        filtered_data = [
            news for news in cached_data
            if (start_date is None or news.date >= start_date) and news.date <= end_date
        ]
        filtered_data.sort(key=lambda x: x.date, reverse=True)
        if filtered_data:
            return filtered_data

    # If in test mode, use test response
    if test_mode:
        data = test_response
    else:
        # Fetch from Polygon.io API
        url = f"{POLYGON_BASE_URL}/v2/reference/news"
        params = {
            "ticker": ticker,
            "published_utc.lte": end_date,
            "limit": 100
        }
        if start_date:
            params["published_utc.gte"] = start_date

        response = _rate_limited_request("GET", url, headers=_get_headers(), params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")

        data = response.json()

    if not data.get("results"):
        return []

    news_items = []
    for result in data["results"]:
        try:
            news = News(
                ticker=ticker,
                date=result["published_utc"].split("T")[0],
                title=result["title"],
                url=result["article_url"],
                source=result["publisher"]["name"],
                description=result.get("description", ""),
                author=result.get("author", ""),
                sentiment=None
            )
            news_items.append(news)
        except (KeyError, TypeError) as e:
            continue

    # Cache the results as dictionaries but return News objects
    _cache.set_company_news(ticker, [n.model_dump() for n in news_items])
    return news_items

def get_market_status() -> dict:
    """Get current market status."""
    # Test response for development/testing
    test_response = {
        "market": "open",
        "session": "regular",
        "exchanges": {
            "nyse": "open",
            "nasdaq": "open",
            "otc": "open"
        },
        "currencies": {
            "fx": "open",
            "crypto": "open"
        }
    }
    return test_response

def get_technical_indicators(ticker: str, indicator_type: str, window: Optional[int] = None, end_date: Optional[Union[str, datetime]] = None) -> List[dict]:
    """Get technical indicators for a ticker."""
    # Test response for development/testing
    test_response = {
        "status": "OK",
        "results": [
            {
                "timestamp": "2024-03-15T14:30:00Z",
                "value": 50.0
            },
            {
                "timestamp": "2024-03-14T14:30:00Z",
                "value": 48.5
            }
        ]
    }

    # For now, return test data
    return [
        {
            "date": result["timestamp"].split("T")[0],
            "value": result["value"]
        }
        for result in test_response["results"]
    ]

def get_market_data(ticker: str, end_date: Union[str, datetime], start_date: Optional[Union[str, datetime]] = None, test_mode: bool = False) -> List[MarketData]:
    """Get market data for a ticker."""
    # ... existing code ...

def get_market_cap(ticker: str, end_date: str) -> float | None:
    """Get market cap for a ticker at a specific date."""
    metrics = get_financial_metrics(ticker, end_date, limit=1)
    return metrics[0].market_cap if metrics else None

def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert a list of Price objects to a pandas DataFrame."""
    return pd.DataFrame([p.model_dump() for p in prices])

def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Get price data as a pandas DataFrame."""
    prices = get_prices(ticker, start_date, end_date)
    return prices_to_df(prices)

def get_market_holidays():
    """Get market holidays for the current year."""
    # Test response with some common US market holidays
    return {
        "status": "OK",
        "holidays": [
            {
                "date": "2024-01-01",
                "name": "New Year's Day",
                "status": "closed",
                "exchange": "NYSE"
            },
            {
                "date": "2024-01-15", 
                "name": "Martin Luther King Jr. Day",
                "status": "closed",
                "exchange": "NYSE"
            },
            {
                "date": "2024-02-19",
                "name": "Presidents' Day",
                "status": "closed", 
                "exchange": "NYSE"
            },
            {
                "date": "2024-03-29",
                "name": "Good Friday",
                "status": "closed",
                "exchange": "NYSE"
            },
            {
                "date": "2024-05-27",
                "name": "Memorial Day",
                "status": "closed",
                "exchange": "NYSE"
            }
        ]
    }