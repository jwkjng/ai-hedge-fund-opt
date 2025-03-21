from typing import Dict, Any
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_financial_metrics, search_line_items
from .base_agent import BaseAgent, AgentSignal

class MichaelBurryAgent(BaseAgent):
    """Agent that analyzes stocks using Michael Burry's investment principles."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Michael Burry's principles", config)
        self.max_debt_to_equity = config.get("max_debt_to_equity", 1.5)  # 150% maximum debt to equity
        self.min_current_ratio = config.get("min_current_ratio", 1.5)  # 1.5x minimum current ratio
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes stocks using Michael Burry's investment principles."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize analysis for each ticker
        burry_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Burry's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    burry_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Initialize scoring
                score = 0
                confidence = 0.8  # High confidence in Burry's principles
                reasons = []

                # 1. Debt to Equity
                if latest_metrics.debt_to_equity is not None:
                    if latest_metrics.debt_to_equity < self.max_debt_to_equity:
                        score += 0.3
                        reasons.append(f"Healthy debt to equity ratio of {latest_metrics.debt_to_equity:.1f}")
                    elif latest_metrics.debt_to_equity > self.max_debt_to_equity * 1.5:
                        score -= 0.3
                        reasons.append(f"High debt to equity ratio of {latest_metrics.debt_to_equity:.1f}")

                # 2. Current Ratio
                if latest_metrics.current_ratio is not None:
                    if latest_metrics.current_ratio > self.min_current_ratio:
                        score += 0.3
                        reasons.append(f"Strong current ratio of {latest_metrics.current_ratio:.1f}")
                    elif latest_metrics.current_ratio < 1.0:
                        score -= 0.3
                        reasons.append(f"Weak current ratio of {latest_metrics.current_ratio:.1f}")

                # 3. Price to Book Value
                if latest_metrics.price_to_book is not None:
                    if latest_metrics.price_to_book < 1.0:
                        score += 0.2
                        reasons.append(f"Trading below book value at P/B of {latest_metrics.price_to_book:.1f}")
                    elif latest_metrics.price_to_book > 3.0:
                        score -= 0.2
                        reasons.append(f"Expensive relative to book value at P/B of {latest_metrics.price_to_book:.1f}")

                # 4. Free Cash Flow
                if latest_metrics.free_cash_flow and latest_metrics.market_cap:
                    fcf_yield = latest_metrics.free_cash_flow / latest_metrics.market_cap
                    if fcf_yield > 0.10:  # 10% FCF yield
                        score += 0.2
                        reasons.append(f"Strong free cash flow yield of {fcf_yield:.1%}")
                    elif fcf_yield < 0:
                        score -= 0.2
                        reasons.append(f"Negative free cash flow yield")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                burry_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Burry analysis",
                    metrics={
                        "score": score,
                        "debt_to_equity": latest_metrics.debt_to_equity,
                        "current_ratio": latest_metrics.current_ratio,
                        "price_to_book": latest_metrics.price_to_book,
                        "fcf_yield": fcf_yield if latest_metrics.free_cash_flow and latest_metrics.market_cap else None
                    }
                )

            except Exception as e:
                burry_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Burry analysis: {str(e)}"
                )

        return burry_analysis 