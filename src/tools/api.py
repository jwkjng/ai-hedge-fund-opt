"""
Financial data API module using Polygon.io as the data provider.
"""

from src.data.models import (
    News,
    NewsResponse,
    MarketData,
    FinancialMetrics,
    LineItem,
    FinancialMetricsResponse,
    LineItemResponse
)

from src.tools.polygon_api import (
    get_prices,
    get_financial_metrics,
    search_line_items,
    get_company_news,
    get_market_data,
    prices_to_df,
    get_price_data,
    get_technical_indicators,
    get_market_status,
    get_market_holidays
)

__all__ = [
    # Models
    'News',
    'NewsResponse',
    'MarketData',
    'FinancialMetrics',
    'LineItem',
    'FinancialMetricsResponse',
    'LineItemResponse',
    
    # Functions
    'get_prices',
    'get_financial_metrics',
    'search_line_items',
    'get_company_news',
    'get_market_data',
    'prices_to_df',
    'get_price_data',
    'get_technical_indicators',
    'get_market_status',
    'get_market_holidays'
]