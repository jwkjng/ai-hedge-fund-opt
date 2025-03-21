from typing import Dict, Any
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_financial_metrics, search_line_items
from .base_agent import BaseAgent, AgentSignal

class PeterLynchAgent(BaseAgent):
    """Agent that analyzes stocks using Peter Lynch's investment principles."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Peter Lynch's principles", config)
        self.min_earnings_growth = config.get("min_earnings_growth", 0.15)  # 15% minimum earnings growth
        self.max_peg_ratio = config.get("max_peg_ratio", 1.0)  # Maximum PEG ratio of 1.0
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes stocks using Peter Lynch's investment principles."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize analysis for each ticker
        lynch_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Lynch's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    lynch_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Initialize scoring
                score = 0
                confidence = 0.8  # High confidence in Lynch's principles
                reasons = []

                # 1. Earnings Growth
                if latest_metrics.earnings_growth:
                    if latest_metrics.earnings_growth > self.min_earnings_growth:
                        score += 0.3
                        reasons.append(f"Strong earnings growth of {latest_metrics.earnings_growth:.1%}")
                    elif latest_metrics.earnings_growth > self.min_earnings_growth * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate earnings growth of {latest_metrics.earnings_growth:.1%}")
                    elif latest_metrics.earnings_growth < 0:
                        score -= 0.3
                        reasons.append(f"Negative earnings growth of {latest_metrics.earnings_growth:.1%}")

                # 2. PEG Ratio
                if latest_metrics.pe_ratio and latest_metrics.earnings_growth:
                    peg_ratio = latest_metrics.pe_ratio / (latest_metrics.earnings_growth * 100)
                    if peg_ratio < self.max_peg_ratio:
                        score += 0.3
                        reasons.append(f"Attractive PEG ratio of {peg_ratio:.1f}")
                    elif peg_ratio > self.max_peg_ratio * 2:
                        score -= 0.3
                        reasons.append(f"High PEG ratio of {peg_ratio:.1f}")

                # 3. Debt Level
                if latest_metrics.debt_to_equity is not None:
                    if latest_metrics.debt_to_equity < 0.5:
                        score += 0.2
                        reasons.append(f"Low debt to equity ratio of {latest_metrics.debt_to_equity:.1f}")
                    elif latest_metrics.debt_to_equity > 1.0:
                        score -= 0.2
                        reasons.append(f"High debt to equity ratio of {latest_metrics.debt_to_equity:.1f}")

                # 4. Dividend Growth (if applicable)
                if latest_metrics.dividend_growth:
                    if latest_metrics.dividend_growth > 0.10:  # 10% dividend growth
                        score += 0.2
                        reasons.append(f"Strong dividend growth of {latest_metrics.dividend_growth:.1%}")
                    elif latest_metrics.dividend_growth < 0:
                        score -= 0.1
                        reasons.append(f"Declining dividends of {latest_metrics.dividend_growth:.1%}")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                lynch_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Lynch analysis",
                    metrics={
                        "score": score,
                        "earnings_growth": latest_metrics.earnings_growth,
                        "peg_ratio": peg_ratio if latest_metrics.pe_ratio and latest_metrics.earnings_growth else None,
                        "debt_to_equity": latest_metrics.debt_to_equity,
                        "dividend_growth": latest_metrics.dividend_growth
                    }
                )

            except Exception as e:
                lynch_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Lynch analysis: {str(e)}"
                )

        return lynch_analysis 