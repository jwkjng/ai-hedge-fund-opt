"""
Test script for Polygon.io API implementation.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.api import (
    get_prices,
    get_financial_metrics,
    get_company_news,
    get_insider_trades,
    get_market_cap,
    get_ticker_details,
    search_line_items,
)

def test_api():
    # Test tickers (mix of different sectors and sizes)
    tickers = ["TSLA"]  # Test only Tesla
    
    # Test dates
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print("\n=== Testing Polygon.io API Implementation ===\n")
    
    for ticker in tickers:
        print(f"\nTesting {ticker}:")
        print("-" * 50)
        
        try:
            # 1. Test basic company details
            print("\nFetching company details...")
            details = get_ticker_details(ticker)
            if details:
                print(f"✓ Company Name: {details.name}")
                print(f"✓ Market: {details.market}")
                print(f"✓ Primary Exchange: {details.primary_exchange}")
            
            # 2. Test price data
            print("\nFetching price data...")
            prices = get_prices(ticker, start_date, end_date)
            if prices:
                latest_price = prices[-1]
                print(f"✓ Latest Price ({latest_price.time}):")
                print(f"  Open: ${latest_price.open:.2f}")
                print(f"  Close: ${latest_price.close:.2f}")
                print(f"  Volume: {latest_price.volume:,}")
            
            # 3. Test financial metrics
            print("\nFetching financial metrics...")
            metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
            if metrics:
                latest_metrics = metrics[0]
                print(f"✓ Report Period: {latest_metrics.report_period}")
                print(f"✓ Revenue: ${latest_metrics.revenue:,.2f}" if latest_metrics.revenue else "✓ Revenue: N/A")
                print(f"✓ Net Income: ${latest_metrics.net_income:,.2f}" if latest_metrics.net_income else "✓ Net Income: N/A")
                print(f"✓ PE Ratio: {latest_metrics.pe_ratio:.2f}" if latest_metrics.pe_ratio else "✓ PE Ratio: N/A")
            
            # 4. Test line items search
            print("\nTesting line items search...")
            line_items = search_line_items(
                ticker,
                [
                    "revenue",
                    "net_income",
                    "operating_margin",
                    "free_cash_flow",
                ],
                end_date,
                period="annual",
                limit=1
            )
            if line_items:
                latest_items = line_items[0]
                print("✓ Successfully retrieved line items")
                print(f"  - Revenue: ${latest_items['revenue']:,.2f}" if latest_items.get('revenue') else "  - Revenue: N/A")
                print(f"  - Operating Margin: {latest_items['operating_margin']:.2%}" if latest_items.get('operating_margin') else "  - Operating Margin: N/A")
            
            # 5. Test market cap
            print("\nFetching market cap...")
            market_cap = get_market_cap(ticker, end_date)
            if market_cap:
                print(f"✓ Market Cap: ${market_cap:,.2f}")
            
            # 6. Test news
            print("\nFetching recent news...")
            news = get_company_news(ticker, end_date, start_date, limit=3)
            if news:
                print(f"✓ Found {len(news)} recent news items")
                for item in news[:2]:  # Show first 2 news items
                    print(f"  - {item.date}: {item.title[:100]}...")
            
            # 7. Test insider trades
            print("\nFetching insider trades...")
            trades = get_insider_trades(ticker, end_date, start_date)
            if trades:
                print(f"✓ Found {len(trades)} insider trades")
                for trade in trades[:2]:  # Show first 2 trades
                    print(f"  - {trade.transaction_date}: {trade.insider_name} - {trade.transaction_type}")
            
        except Exception as e:
            print(f"❌ Error testing {ticker}: {str(e)}")
            continue
        
        print("\n✓ All tests completed for", ticker)
        print("-" * 50)

if __name__ == "__main__":
    test_api() 