from typing import Dict, Any
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from tools.api import get_prices
from .base_agent import BaseAgent, AgentSignal

class RiskManagerAgent(BaseAgent):
    """Agent that manages portfolio risk and position sizing."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Manages portfolio risk and position sizing", config)
        self.max_position_size = config.get("max_position_size", 100000)  # Default $100k per position
        self.max_portfolio_risk = config.get("max_portfolio_risk", 0.20)  # Default 20% max risk
        self.stop_loss = config.get("stop_loss", 0.15)  # Default 15% stop loss
        self.position_sizing_method = config.get("position_sizing_method", "equal_weight")
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes risk factors and sets position limits for multiple tickers."""
        data = state["data"]
        end_date = data["end_date"]
        start_date = data["start_date"]
        tickers = data["tickers"]
        portfolio = state["portfolio"]

        # Initialize risk analysis for each ticker
        risk_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing risk factors")
            
            try:
                # Get price data for volatility calculation
                prices = get_prices(ticker, start_date, end_date)
                if not prices:
                    risk_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No price data available for risk analysis"
                    )
                    continue

                # Calculate volatility
                returns = [(p.close - prices[i-1].close) / prices[i-1].close for i, p in enumerate(prices) if i > 0]
                volatility = (sum(r * r for r in returns) / len(returns)) ** 0.5 * (252 ** 0.5)  # Annualized

                # Calculate position size based on risk
                position_size = min(
                    self.max_position_size,
                    portfolio["cash"] * (1 / len(tickers))  # Equal weight
                )

                # Adjust position size based on volatility
                if volatility > 0.4:  # High volatility
                    position_size *= 0.5
                    risk_level = "high"
                elif volatility > 0.2:  # Medium volatility
                    position_size *= 0.75
                    risk_level = "medium"
                else:  # Low volatility
                    risk_level = "low"

                # Set stop loss based on volatility
                stop_loss = max(self.stop_loss, volatility)

                # Generate signal based on risk assessment
                signal = "neutral"
                if risk_level == "low" and position_size >= self.max_position_size * 0.8:
                    signal = "bullish"
                elif risk_level == "high" and position_size <= self.max_position_size * 0.5:
                    signal = "bearish"

                # Store the analysis results
                risk_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=0.8,  # High confidence in risk assessment
                    reasoning=f"Risk Level: {risk_level.upper()}\n" +
                            f"Annual Volatility: {volatility:.1%}\n" +
                            f"Recommended Position Size: ${position_size:,.0f}\n" +
                            f"Stop Loss Level: {stop_loss:.1%}",
                    metrics={
                        "volatility": volatility,
                        "position_size": position_size,
                        "stop_loss": stop_loss,
                        "risk_level": risk_level
                    }
                )

            except Exception as e:
                risk_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in risk analysis: {str(e)}"
                )

        return risk_analysis
