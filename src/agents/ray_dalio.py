from typing import Dict, Any
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_financial_metrics, search_line_items
from .base_agent import BaseAgent, AgentSignal

class RayDalioAgent(BaseAgent):
    """Agent that analyzes stocks using Ray Dalio's investment principles."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Ray Dalio's principles", config)
        self.min_roa = config.get("min_roa", 0.10)  # 10% minimum return on assets
        self.min_operating_margin = config.get("min_operating_margin", 0.15)  # 15% minimum operating margin
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes stocks using Ray Dalio's investment principles."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize analysis for each ticker
        dalio_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Dalio's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    dalio_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Initialize scoring
                score = 0
                confidence = 0.8  # High confidence in Dalio's principles
                reasons = []

                # 1. Return on Assets
                if latest_metrics.return_on_assets:
                    if latest_metrics.return_on_assets > self.min_roa:
                        score += 0.3
                        reasons.append(f"Strong return on assets of {latest_metrics.return_on_assets:.1%}")
                    elif latest_metrics.return_on_assets > self.min_roa * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate return on assets of {latest_metrics.return_on_assets:.1%}")
                    elif latest_metrics.return_on_assets < 0:
                        score -= 0.3
                        reasons.append(f"Negative return on assets of {latest_metrics.return_on_assets:.1%}")

                # 2. Operating Margin
                if latest_metrics.operating_margin:
                    if latest_metrics.operating_margin > self.min_operating_margin:
                        score += 0.3
                        reasons.append(f"Strong operating margin of {latest_metrics.operating_margin:.1%}")
                    elif latest_metrics.operating_margin > self.min_operating_margin * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate operating margin of {latest_metrics.operating_margin:.1%}")
                    elif latest_metrics.operating_margin < 0:
                        score -= 0.3
                        reasons.append(f"Negative operating margin of {latest_metrics.operating_margin:.1%}")

                # 3. Debt Management
                if latest_metrics.debt_to_equity is not None:
                    if latest_metrics.debt_to_equity < 0.7:
                        score += 0.2
                        reasons.append(f"Conservative debt level with D/E of {latest_metrics.debt_to_equity:.1f}")
                    elif latest_metrics.debt_to_equity > 1.5:
                        score -= 0.2
                        reasons.append(f"High debt level with D/E of {latest_metrics.debt_to_equity:.1f}")

                # 4. Cash Flow Quality
                if latest_metrics.free_cash_flow and latest_metrics.net_income:
                    fcf_to_net_income = latest_metrics.free_cash_flow / latest_metrics.net_income
                    if fcf_to_net_income > 1.0:
                        score += 0.2
                        reasons.append(f"Strong cash flow quality with FCF/NI of {fcf_to_net_income:.1f}")
                    elif fcf_to_net_income < 0.5:
                        score -= 0.2
                        reasons.append(f"Poor cash flow quality with FCF/NI of {fcf_to_net_income:.1f}")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                dalio_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Dalio analysis",
                    metrics={
                        "score": score,
                        "return_on_assets": latest_metrics.return_on_assets,
                        "operating_margin": latest_metrics.operating_margin,
                        "debt_to_equity": latest_metrics.debt_to_equity,
                        "fcf_to_net_income": fcf_to_net_income if latest_metrics.free_cash_flow and latest_metrics.net_income else None
                    }
                )

            except Exception as e:
                dalio_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Dalio analysis: {str(e)}"
                )

        return dalio_analysis 