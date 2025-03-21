from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentSignal
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_financial_metrics, get_market_data, search_line_items
from utils.llm import call_llm
from utils.progress import progress
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
import math
import json

class BenGrahamAgent(BaseAgent):
    """Agent that analyzes stocks using Benjamin Graham's investment principles."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Benjamin Graham's principles", config)
        self.margin_of_safety = config.get("margin_of_safety", 0.25)  # 25% margin of safety
        self.min_current_ratio = config.get("min_current_ratio", 2.0)  # Minimum current ratio
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes stocks using Benjamin Graham's investment principles."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize analysis for each ticker
        graham_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Graham's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    graham_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Initialize scoring
                score = 0
                confidence = 0.8  # High confidence in Graham's principles
                reasons = []

                # 1. Adequate Size
                if latest_metrics.market_cap:
                    if latest_metrics.market_cap > 2e9:  # $2B market cap
                        score += 0.2
                        reasons.append(f"Large market cap of ${latest_metrics.market_cap/1e9:.1f}B")
                    elif latest_metrics.market_cap < 100e6:  # $100M market cap
                        score -= 0.2
                        reasons.append(f"Small market cap of ${latest_metrics.market_cap/1e6:.1f}M")

                # 2. Strong Financial Condition
                if latest_metrics.current_ratio:
                    if latest_metrics.current_ratio > self.min_current_ratio:
                        score += 0.3
                        reasons.append(f"Strong current ratio of {latest_metrics.current_ratio:.1f}")
                    elif latest_metrics.current_ratio < 1.5:
                        score -= 0.3
                        reasons.append(f"Weak current ratio of {latest_metrics.current_ratio:.1f}")

                # 3. Earnings Stability
                if latest_metrics.earnings_growth:
                    if latest_metrics.earnings_growth > 0.07:  # 7% growth
                        score += 0.2
                        reasons.append(f"Stable earnings growth of {latest_metrics.earnings_growth:.1%}")
                    elif latest_metrics.earnings_growth < 0:
                        score -= 0.2
                        reasons.append(f"Negative earnings growth of {latest_metrics.earnings_growth:.1%}")

                # 4. Dividend Record
                if latest_metrics.free_cash_flow and latest_metrics.market_cap:
                    fcf_yield = latest_metrics.free_cash_flow / latest_metrics.market_cap
                    if fcf_yield > 0.06:  # 6% FCF yield
                        score += 0.2
                        reasons.append(f"Strong free cash flow yield of {fcf_yield:.1%}")
                    elif fcf_yield < 0:
                        score -= 0.2
                        reasons.append(f"Negative free cash flow yield")

                # 5. Price-Earnings Ratio
                if latest_metrics.pe_ratio:
                    if latest_metrics.pe_ratio < 15:
                        score += 0.2
                        reasons.append(f"Low P/E ratio of {latest_metrics.pe_ratio:.1f}")
                    elif latest_metrics.pe_ratio > 25:
                        score -= 0.2
                        reasons.append(f"High P/E ratio of {latest_metrics.pe_ratio:.1f}")

                # 6. Price-to-Book Ratio
                if latest_metrics.pb_ratio:
                    if latest_metrics.pb_ratio < 1.5:
                        score += 0.2
                        reasons.append(f"Low P/B ratio of {latest_metrics.pb_ratio:.1f}")
                    elif latest_metrics.pb_ratio > 3:
                        score -= 0.2
                        reasons.append(f"High P/B ratio of {latest_metrics.pb_ratio:.1f}")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                graham_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Graham analysis",
                    metrics={
                        "score": score,
                        "market_cap": latest_metrics.market_cap,
                        "current_ratio": latest_metrics.current_ratio,
                        "earnings_growth": latest_metrics.earnings_growth,
                        "pe_ratio": latest_metrics.pe_ratio,
                        "pb_ratio": latest_metrics.pb_ratio
                    }
                )

            except Exception as e:
                graham_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Graham analysis: {str(e)}"
                )

        return graham_analysis
    
    def _generate_signal(self, total_score: float, max_possible_score: float) -> tuple[str, float]:
        """Generate signal and confidence based on Graham's criteria"""
        score_ratio = total_score / max_possible_score
        
        if score_ratio >= 0.7:
            return "bullish", min(score_ratio * 100, 100)
        elif score_ratio <= 0.3:
            return "bearish", min((1 - score_ratio) * 100, 100)
        else:
            return "neutral", 50
    
    def _generate_reasoning(self, ticker: str, analysis_data: dict, model_name: str, model_provider: str) -> str:
        """Generate detailed reasoning using LLM"""
        template = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a Benjamin Graham AI agent. Analyze the investment based on:
                - Earnings Stability
                - Financial Strength
                - Valuation (Net-Net and Graham Number)
                - Margin of Safety
                
                Provide clear, concise reasoning for the investment decision.
                """
            ),
            (
                "human",
                """Based on the following analysis for {ticker}, explain the investment decision:
                {analysis_data}
                
                Provide a clear, concise explanation of the reasoning behind the signal.
                """
            )
        ])
        
        prompt = template.invoke({
            "ticker": ticker,
            "analysis_data": analysis_data
        })
        
        response = call_llm(
            prompt=prompt,
            model_name=model_name,
            model_provider=model_provider,
            temperature=0.7
        )
        
        return str(response)
    
    def _analyze_earnings_stability(self, metrics: list, financial_line_items: list) -> dict:
        """Analyze earnings stability using Graham's criteria"""
        # Keep existing implementation
        pass
    
    def _analyze_financial_strength(self, financial_line_items: list) -> dict:
        """Analyze financial strength using Graham's criteria"""
        # Keep existing implementation
        pass
    
    def _analyze_valuation_graham(self, financial_line_items: list, market_cap: float) -> dict:
        """Calculate valuation using Graham's methods"""
        # Keep existing implementation
        pass

# For backward compatibility
def ben_graham_agent(state: AgentState) -> dict:
    """Legacy wrapper for backward compatibility"""
    agent = BenGrahamAgent(
        name="ben_graham_agent",
        description="Analyzes stocks using Benjamin Graham's value investing principles"
    )
    return agent.execute(state)