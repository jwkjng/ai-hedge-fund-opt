from datetime import datetime, timedelta
import argparse
import json
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

from agents.fundamentals import FundamentalsAgent
from agents.warren_buffett import WarrenBuffettAgent
from agents.ben_graham import BenGrahamAgent
from agents.bill_ackman import BillAckmanAgent
from agents.sentiment import SentimentAgent
from agents.risk_manager import RiskManagerAgent
from graph.state import AgentState
from utils.progress import progress
from tools.api import (
    get_market_status,
    get_market_holidays,
    get_company_news
)

# Load environment variables from .env file
load_dotenv()

def get_agent_class(analyst_name: str):
    """Get the agent class for a given analyst name."""
    agent_map = {
        "fundamentals": FundamentalsAgent,
        "warren_buffett": WarrenBuffettAgent,
        "ben_graham": BenGrahamAgent,
        "bill_ackman": BillAckmanAgent,
        "sentiment": SentimentAgent,
        "risk_manager": RiskManagerAgent
    }
    return agent_map.get(analyst_name)

def parse_hedge_fund_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the response from the hedge fund agents."""
    # Convert Pydantic model to dict if needed
    if hasattr(response, "model_dump"):
        response = response.model_dump()

    signal = response.get("signal", "neutral")
    if isinstance(signal, (int, float)):
        # Convert numeric signal to string
        if signal > 0.2:
            signal = "bullish"
        elif signal < -0.2:
            signal = "bearish"
        else:
            signal = "neutral"
    
    return {
        "signal": signal,
        "confidence": response.get("confidence", 0),
        "reasoning": response.get("reasoning", "No reasoning provided")
    }

def run_hedge_fund(
    tickers: list[str],
    start_date: str,
    end_date: str,
    portfolio: dict = None,
    model_name: str = "gpt-4",
    model_provider: str = "OpenAI",
    selected_analysts: list[str] = [],
) -> dict:
    """Run the hedge fund simulation."""
    # Initialize empty dictionaries to store decisions and signals
    decisions = {}
    analyst_signals = {}

    # Get market status
    market_status = get_market_status()
    if market_status["market"] != "open":
        print("\nMarket is currently closed. Skipping analysis.")
        return {"decisions": {}, "analyst_signals": {}}

    # Check for market holidays
    holidays = get_market_holidays()
    if any(holiday["date"] == end_date for holiday in holidays["holidays"]):
        print(f"\nMarket holiday on {end_date}. Skipping analysis.")
        return {"decisions": {}, "analyst_signals": {}}

    print(f"\n{'=' * 80}")
    print(f"ANALYZING STOCKS FOR {end_date}")
    print(f"{'=' * 80}")

    # Create agent state
    state = AgentState({
        "data": {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date
        },
        "metadata": {
            "show_reasoning": True
        },
        "portfolio": portfolio or {
            "cash": 1000000,  # $1M starting cash
            "positions": {}
        }
    })

    # Analyze each ticker
    for ticker in tickers:
        print(f"\n{'-' * 40}")
        print(f"Analyzing {ticker}...")
        print(f"{'-' * 40}")

        # Get company news
        news = get_company_news(ticker, end_date, start_date, test_mode=True)
        if news:
            print(f"\nLatest news for {ticker}:")
            for n in news[:1]:  # Show only the most recent news
                print(f"Date: {n.date}")
                print(f"Title: {n.title}")
                print(f"Source: {n.source}")
                print(f"URL: {n.url}")

        # Run analysis with each selected analyst
        signals = {}
        for analyst in selected_analysts:
            agent_class = get_agent_class(analyst)
            if agent_class:
                agent = agent_class(
                    name=analyst,
                    description=f"{analyst.replace('_', ' ').title()} Analysis",
                    config={}
                )
                signal_dict = agent.analyze(state)
                signal = signal_dict.get(ticker)
                if signal:
                    signal = signal.model_dump()
                else:
                    signal = {
                        "signal": "neutral",
                        "confidence": 0,
                        "reasoning": "Analysis failed"
                    }
                signals[analyst] = signal

                print(f"\n{agent.name} Analysis:")
                print(f"Signal: {signal['signal']}")
                print(f"Confidence: {signal['confidence']:.1f}")
                print(f"Reasoning: {signal['reasoning']}")

        analyst_signals[ticker] = signals

        # Aggregate signals to make trading decisions
        bullish_count = len([s for s in signals.values() if s["signal"].lower() == "bullish"])
        bearish_count = len([s for s in signals.values() if s["signal"].lower() == "bearish"])
        neutral_count = len([s for s in signals.values() if s["signal"].lower() == "neutral"])
        total_signals = len(signals)

        # Default to hold
        action = "hold"
        quantity = 0

        # Simple majority voting system
        if total_signals > 0:
            # Calculate position size based on conviction (% of signals agreeing)
            max_position = 100  # Maximum position size
            
            if bullish_count > bearish_count and bullish_count > neutral_count:
                action = "buy"
                conviction = bullish_count / total_signals
                quantity = int(max_position * conviction)
            elif bearish_count > bullish_count and bearish_count > neutral_count:
                action = "sell"
                conviction = bearish_count / total_signals
                quantity = int(max_position * conviction)

        decisions[ticker] = {"action": action, "quantity": quantity}

    return {
        "decisions": decisions,
        "analyst_signals": analyst_signals
    }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run hedge fund analysis")
    parser.add_argument("--ticker", type=str, required=True, help="Comma-separated list of tickers to analyze")
    parser.add_argument("--end_date", type=str, help="End date for analysis (YYYY-MM-DD)")
    parser.add_argument("--start_date", type=str, help="Start date for analysis (YYYY-MM-DD)")
    parser.add_argument("--show_reasoning", action="store_true", help="Show detailed reasoning")
    return parser.parse_args()

def start():
    """Start the hedge fund analysis."""
    args = parse_args()
    
    # Initialize agents with empty configs
    agents = [
        FundamentalsAgent("fundamentals", config={}),
        WarrenBuffettAgent("warren_buffett", config={}),
        BenGrahamAgent("ben_graham", config={}),
        BillAckmanAgent("bill_ackman", config={}),
        SentimentAgent("sentiment", config={}),
        RiskManagerAgent("risk_manager", config={})
    ]
    
    # Parse tickers
    tickers = args.ticker.split(",")
    
    # Get end date (today)
    end_date = datetime.now()
    
    # Get start date (1 year ago)
    start_date = end_date - timedelta(days=365)
    
    # Format dates as strings
    end_date_str = end_date.strftime("%Y-%m-%d")
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    # Run analysis
    output = run_hedge_fund(
        tickers=tickers,
        start_date=start_date_str,
        end_date=end_date_str,
        selected_analysts=[
            "fundamentals",
            "warren_buffett",
            "ben_graham",
            "bill_ackman",
            "sentiment",
            "risk_manager"
        ]
    )
    
    # Print results using the display formatter
    from utils.display import print_trading_output
    print_trading_output(output)

def main():
    """Main function to run the hedge fund analysis."""
    # Clear the cache
    from data.cache import get_cache
    get_cache().clear()
    
    # Run the analysis
    start()

if __name__ == "__main__":
    main()
