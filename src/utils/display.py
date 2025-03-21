from colorama import Fore, Style
from tabulate import tabulate
from .analysts import ANALYST_ORDER
import os
from typing import List, Dict, Any


def sort_analyst_signals(signals):
    """Sort analyst signals in a consistent order."""
    # Create order mapping from ANALYST_ORDER
    analyst_order = {display: idx for idx, (display, _) in enumerate(ANALYST_ORDER)}
    analyst_order["Risk Management"] = len(ANALYST_ORDER)  # Add Risk Management at the end

    return sorted(signals, key=lambda x: analyst_order.get(x[0], 999))


def print_trading_output(output: dict) -> None:
    """Print trading analysis output in a nicely formatted way."""
    decisions = output.get("decisions", {})
    analyst_signals = output.get("analyst_signals", {})

    print("\nTRADING DECISIONS")
    print("=" * 80)
    print(f"{'Ticker':8} {'Action':8} {'Quantity':>10}")
    print("-" * 80)
    
    for ticker, decision in decisions.items():
        print(f"{ticker:8} {decision['action']:8} {decision['quantity']:>10}")
    
    print("\nANALYST SIGNALS")
    print("=" * 80)
    
    for ticker, signals in analyst_signals.items():
        print(f"\n{ticker} Analysis:")
        print("-" * 40)
        
        bullish = len([s for s in signals.values() if s["signal"].lower() == "bullish"])
        bearish = len([s for s in signals.values() if s["signal"].lower() == "bearish"])
        neutral = len([s for s in signals.values() if s["signal"].lower() == "neutral"])
        
        print(f"Signal Summary: {bullish} Bullish, {neutral} Neutral, {bearish} Bearish")
        
        for analyst, signal in signals.items():
            print(f"\n{analyst}:")
            print(f"  Signal: {signal['signal']}")
            print(f"  Confidence: {signal['confidence']:.1f}")
            print(f"  Reasoning: {signal['reasoning']}")
    
    print("\n" + "=" * 80)


def print_backtest_results(table_rows: List[Dict[str, Any]]) -> None:
    """Print backtest results in a nicely formatted table."""
    # Clear the screen
    print("\033[2J\033[H")
    
    # Print header
    print("\n" + "=" * 100)
    print(f"{'Date':12} {'Ticker':8} {'Action':8} {'Qty':>8} {'Price':>10} {'Value':>12} {'Signal':>10}")
    print("-" * 100)
    
    # Print rows
    for row in table_rows:
        if row.get("is_summary"):
            print("-" * 100)
            print(f"{row['date']:12} {'SUMMARY':8} {' ':8} {' ':8} {' ':10}", end=" ")
            print(f"${row['total_value']:>11,.2f} {' ':10}")
            print(f"{'':12} {'':8} {'Cash:':8} {' ':8} {' ':10}", end=" ")
            print(f"${row['cash_balance']:>11,.2f} {' ':10}")
            print(f"{'':12} {'':8} {'Return:':8} {' ':8} {' ':10}", end=" ")
            print(f"{row['return_pct']:>11.2f}% {' ':10}")
            if row.get('sharpe_ratio'):
                print(f"{'':12} {'':8} {'Sharpe:':8} {' ':8} {' ':10}", end=" ")
                print(f"{row['sharpe_ratio']:>11.2f} {' ':10}")
            print("=" * 100)
        else:
            signal = f"{row['bullish_count']}/{row['neutral_count']}/{row['bearish_count']}"
            print(f"{row['date']:12} {row['ticker']:8} {row['action']:8}", end=" ")
            print(f"{row['quantity']:>8} ${row['price']:>9,.2f}", end=" ")
            print(f"${row['position_value']:>11,.2f} {signal:>10}")
    
    print()


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    shares_owned: float,
    position_value: float,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
    is_summary: bool = False,
    total_value: float = None,
    return_pct: float = None,
    cash_balance: float = None,
    total_position_value: float = None,
    sharpe_ratio: float = None,
    sortino_ratio: float = None,
    max_drawdown: float = None,
) -> list[any]:
    """Format a row for the backtest results table"""
    # Color the action
    action_color = {
        "BUY": Fore.GREEN,
        "COVER": Fore.GREEN,
        "SELL": Fore.RED,
        "SHORT": Fore.RED,
        "HOLD": Fore.YELLOW,
    }.get(action.upper(), Fore.WHITE)

    if is_summary:
        return_color = Fore.GREEN if return_pct >= 0 else Fore.RED
        return [
            date,
            f"{Fore.WHITE}{Style.BRIGHT}PORTFOLIO SUMMARY{Style.RESET_ALL}",
            "",  # Action
            "",  # Quantity
            "",  # Price
            "",  # Shares
            f"{Fore.YELLOW}${total_position_value:,.2f}{Style.RESET_ALL}",  # Total Position Value
            f"{Fore.CYAN}${cash_balance:,.2f}{Style.RESET_ALL}",  # Cash Balance
            f"{Fore.WHITE}${total_value:,.2f}{Style.RESET_ALL}",  # Total Value
            f"{return_color}{return_pct:+.2f}%{Style.RESET_ALL}",  # Return
            f"{Fore.YELLOW}{sharpe_ratio:.2f}{Style.RESET_ALL}" if sharpe_ratio is not None else "",  # Sharpe Ratio
            f"{Fore.YELLOW}{sortino_ratio:.2f}{Style.RESET_ALL}" if sortino_ratio is not None else "",  # Sortino Ratio
            f"{Fore.RED}{max_drawdown:.2f}%{Style.RESET_ALL}" if max_drawdown is not None else "",  # Max Drawdown
        ]
    else:
        return [
            date,
            f"{Fore.CYAN}{ticker}{Style.RESET_ALL}",
            f"{action_color}{action.upper()}{Style.RESET_ALL}",
            f"{action_color}{quantity:,.0f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{price:,.2f}{Style.RESET_ALL}",
            f"{Fore.WHITE}{shares_owned:,.0f}{Style.RESET_ALL}",
            f"{Fore.YELLOW}{position_value:,.2f}{Style.RESET_ALL}",
            f"{Fore.GREEN}{bullish_count}{Style.RESET_ALL}",
            f"{Fore.RED}{bearish_count}{Style.RESET_ALL}",
            f"{Fore.BLUE}{neutral_count}{Style.RESET_ALL}",
        ]
