from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class Cache:
    """In-memory cache for API responses."""

    def __init__(self):
        """Initialize empty caches."""
        self._price_cache: dict[str, list[dict[str, any]]] = {}
        self._news_cache: dict[str, list[dict[str, any]]] = {}
        self._financials_cache: dict[str, list[dict[str, any]]] = {}
        self._market_cache: dict[str, list[dict[str, any]]] = {}

    def clear(self):
        """Clear all caches."""
        self._price_cache.clear()
        self._news_cache.clear()
        self._financials_cache.clear()
        self._market_cache.clear()

    def _merge_data(self, existing: list[dict] | None, new_data: list[dict], key_field: str) -> list[dict]:
        """Merge existing and new data, avoiding duplicates based on a key field."""
        if not existing:
            return sorted(new_data, key=lambda x: x[key_field], reverse=True)
        
        # Create a dictionary of existing items for O(1) lookup and update
        merged_dict = {item[key_field]: item for item in existing}
        
        # Update with new items
        for item in new_data:
            key = item[key_field]
            if key not in merged_dict:
                merged_dict[key] = item
        
        # Convert back to list and sort by key field
        merged = list(merged_dict.values())
        return sorted(merged, key=lambda x: x[key_field], reverse=True)

    def _convert_to_model(self, data: list[dict], model_cls: Type[T]) -> list[T]:
        """Convert a list of dictionaries to a list of Pydantic models."""
        return [model_cls(**item) for item in data]

    def get_prices(self, ticker: str) -> list[dict[str, any]] | None:
        """Get cached price data if available."""
        return self._price_cache.get(ticker)

    def set_prices(self, ticker: str, data: list[dict[str, any]]):
        """Append new price data to cache."""
        self._price_cache[ticker] = self._merge_data(
            self._price_cache.get(ticker),
            data,
            key_field="time"
        )

    def get_financial_metrics(self, ticker: str) -> list[dict[str, any]]:
        """Get cached financial metrics if available."""
        return self._financials_cache.get(ticker)

    def set_financial_metrics(self, ticker: str, data: list[dict[str, any]]):
        """Append new financial metrics to cache."""
        self._financials_cache[ticker] = self._merge_data(
            self._financials_cache.get(ticker),
            data,
            key_field="report_period"
        )

    def get_line_items(self, ticker: str) -> list[dict[str, any]] | None:
        """Get cached line items if available."""
        return self._financials_cache.get(ticker)

    def set_line_items(self, ticker: str, data: list[dict[str, any]]):
        """Append new line items to cache."""
        self._financials_cache[ticker] = self._merge_data(
            self._financials_cache.get(ticker),
            data,
            key_field="report_period"
        )

    def get_company_news(self, ticker: str, model_cls: Type[T] = None) -> list[dict[str, any]] | list[T] | None:
        """Get cached company news if available."""
        data = self._news_cache.get(ticker)
        if data and model_cls:
            return self._convert_to_model(data, model_cls)
        return data

    def set_company_news(self, ticker: str, data: list[dict[str, any]]):
        """Append new company news to cache."""
        self._news_cache[ticker] = self._merge_data(
            self._news_cache.get(ticker),
            data,
            key_field="date"
        )

    def get_market_data(self, ticker: str) -> list[dict[str, any]] | None:
        """Get cached market data if available."""
        return self._market_cache.get(ticker)

    def set_market_data(self, ticker: str, data: list[dict[str, any]]):
        """Append new market data to cache."""
        self._market_cache[ticker] = self._merge_data(
            self._market_cache.get(ticker),
            data
        )


# Global cache instance
_cache = Cache()


def get_cache() -> Cache:
    """Get the global cache instance."""
    return _cache
