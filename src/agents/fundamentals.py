from typing import Dict, Any
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_financial_metrics
from .base_agent import BaseAgent, AgentSignal

class FundamentalsAgent(BaseAgent):
    """Agent that analyzes fundamental data and generates trading signals."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes fundamental data and generates trading signals", config)
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes fundamental data and generates trading signals for multiple tickers."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize fundamental analysis for each ticker
        fundamental_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Fetching financial metrics")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    fundamental_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Calculate fundamental score based on key metrics
                score = 0
                confidence = 0.7  # Base confidence
                reasons = []

                # Analyze profitability
                if latest_metrics.net_margin:
                    if latest_metrics.net_margin > 0.2:
                        score += 0.3
                        reasons.append(f"Strong net margin of {latest_metrics.net_margin:.1%}")
                    elif latest_metrics.net_margin > 0.1:
                        score += 0.1
                        reasons.append(f"Decent net margin of {latest_metrics.net_margin:.1%}")
                    elif latest_metrics.net_margin < 0:
                        score -= 0.3
                        reasons.append(f"Negative net margin of {latest_metrics.net_margin:.1%}")

                # Analyze growth
                if latest_metrics.revenue_growth:
                    if latest_metrics.revenue_growth > 0.2:
                        score += 0.3
                        reasons.append(f"Strong revenue growth of {latest_metrics.revenue_growth:.1%}")
                    elif latest_metrics.revenue_growth > 0.1:
                        score += 0.1
                        reasons.append(f"Decent revenue growth of {latest_metrics.revenue_growth:.1%}")
                    elif latest_metrics.revenue_growth < 0:
                        score -= 0.2
                        reasons.append(f"Negative revenue growth of {latest_metrics.revenue_growth:.1%}")

                # Analyze valuation
                if latest_metrics.pe_ratio:
                    if latest_metrics.pe_ratio < 15:
                        score += 0.2
                        reasons.append(f"Attractive P/E ratio of {latest_metrics.pe_ratio:.1f}")
                    elif latest_metrics.pe_ratio > 30:
                        score -= 0.2
                        reasons.append(f"High P/E ratio of {latest_metrics.pe_ratio:.1f}")

                # Analyze financial health
                if latest_metrics.current_ratio:
                    if latest_metrics.current_ratio > 2:
                        score += 0.2
                        reasons.append(f"Strong current ratio of {latest_metrics.current_ratio:.1f}")
                    elif latest_metrics.current_ratio < 1:
                        score -= 0.3
                        reasons.append(f"Weak current ratio of {latest_metrics.current_ratio:.1f}")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                fundamental_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for detailed analysis",
                    metrics={
                        "score": score,
                        "net_margin": latest_metrics.net_margin,
                        "revenue_growth": latest_metrics.revenue_growth,
                        "pe_ratio": latest_metrics.pe_ratio,
                        "current_ratio": latest_metrics.current_ratio
                    }
                )

            except Exception as e:
                fundamental_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error analyzing fundamentals: {str(e)}"
                )

        return fundamental_analysis
