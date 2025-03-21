from typing import Dict, Any
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_financial_metrics, search_line_items
from .base_agent import BaseAgent, AgentSignal

class WarrenBuffettAgent(BaseAgent):
    """Agent that analyzes stocks using Warren Buffett's investment principles."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Warren Buffett's investment principles", config)
        self.min_roe = config.get("min_roe", 0.15)  # 15% minimum ROE
        self.min_operating_margin = config.get("min_operating_margin", 0.20)  # 20% minimum operating margin
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes stocks using Warren Buffett's investment principles."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize analysis for each ticker
        buffett_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Buffett's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    buffett_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Initialize scoring
                score = 0
                confidence = 0.8  # High confidence in Buffett's principles
                reasons = []

                # 1. Strong Return on Equity (ROE)
                if latest_metrics.return_on_equity:
                    if latest_metrics.return_on_equity > self.min_roe:
                        score += 0.3
                        reasons.append(f"Strong ROE of {latest_metrics.return_on_equity:.1%}")
                    elif latest_metrics.return_on_equity > self.min_roe * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate ROE of {latest_metrics.return_on_equity:.1%}")
                    else:
                        score -= 0.2
                        reasons.append(f"Weak ROE of {latest_metrics.return_on_equity:.1%}")

                # 2. High Operating Margins
                if latest_metrics.operating_margin:
                    if latest_metrics.operating_margin > self.min_operating_margin:
                        score += 0.3
                        reasons.append(f"Strong operating margin of {latest_metrics.operating_margin:.1%}")
                    elif latest_metrics.operating_margin > self.min_operating_margin * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate operating margin of {latest_metrics.operating_margin:.1%}")
                    else:
                        score -= 0.2
                        reasons.append(f"Weak operating margin of {latest_metrics.operating_margin:.1%}")

                # 3. Low Debt to Equity
                if latest_metrics.debt_to_equity:
                    if latest_metrics.debt_to_equity < 0.5:
                        score += 0.2
                        reasons.append(f"Low debt-to-equity ratio of {latest_metrics.debt_to_equity:.1f}")
                    elif latest_metrics.debt_to_equity > 1.5:
                        score -= 0.3
                        reasons.append(f"High debt-to-equity ratio of {latest_metrics.debt_to_equity:.1f}")

                # 4. Consistent Earnings Growth
                if latest_metrics.earnings_growth:
                    if latest_metrics.earnings_growth > 0.15:
                        score += 0.2
                        reasons.append(f"Strong earnings growth of {latest_metrics.earnings_growth:.1%}")
                    elif latest_metrics.earnings_growth < 0:
                        score -= 0.3
                        reasons.append(f"Negative earnings growth of {latest_metrics.earnings_growth:.1%}")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                buffett_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Buffett analysis",
                    metrics={
                        "score": score,
                        "roe": latest_metrics.return_on_equity,
                        "operating_margin": latest_metrics.operating_margin,
                        "debt_to_equity": latest_metrics.debt_to_equity,
                        "earnings_growth": latest_metrics.earnings_growth
                    }
                )

            except Exception as e:
                buffett_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Buffett analysis: {str(e)}"
                )

        return buffett_analysis

# For backward compatibility
def warren_buffett_agent(state: AgentState) -> dict:
    """Legacy wrapper for backward compatibility"""
    agent = WarrenBuffettAgent(
        name="warren_buffett_agent",
        description="Analyzes stocks using Warren Buffett's investment principles"
    )
    return agent.execute(state)