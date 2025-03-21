from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentSignal
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_financial_metrics, get_market_data, search_line_items
from utils.llm import call_llm
from utils.progress import progress
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
import json

class CathieWoodAgent(BaseAgent):
    """Agent that analyzes stocks using Cathie Wood's investment principles."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Cathie Wood's principles", config)
        self.min_revenue_growth = config.get("min_revenue_growth", 0.20)  # 20% minimum revenue growth
        self.min_rd_to_revenue = config.get("min_rd_to_revenue", 0.10)  # 10% minimum R&D to revenue
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes stocks using Cathie Wood's investment principles."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize analysis for each ticker
        wood_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Wood's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    wood_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Initialize scoring
                score = 0
                confidence = 0.8  # High confidence in Wood's principles
                reasons = []

                # 1. Revenue Growth
                if latest_metrics.revenue_growth:
                    if latest_metrics.revenue_growth > self.min_revenue_growth:
                        score += 0.4
                        reasons.append(f"Strong revenue growth of {latest_metrics.revenue_growth:.1%}")
                    elif latest_metrics.revenue_growth > self.min_revenue_growth * 0.5:
                        score += 0.2
                        reasons.append(f"Moderate revenue growth of {latest_metrics.revenue_growth:.1%}")
                    elif latest_metrics.revenue_growth < 0:
                        score -= 0.3
                        reasons.append(f"Negative revenue growth of {latest_metrics.revenue_growth:.1%}")

                # 2. R&D Investment
                if latest_metrics.research_and_development and latest_metrics.revenue:
                    rd_to_revenue = latest_metrics.research_and_development / latest_metrics.revenue
                    if rd_to_revenue > self.min_rd_to_revenue:
                        score += 0.3
                        reasons.append(f"Strong R&D investment at {rd_to_revenue:.1%} of revenue")
                    elif rd_to_revenue > self.min_rd_to_revenue * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate R&D investment at {rd_to_revenue:.1%} of revenue")

                # 3. Market Position in Innovation
                if latest_metrics.market_cap:
                    if latest_metrics.market_cap > 5e9:  # $5B market cap
                        score += 0.2
                        reasons.append(f"Significant market presence with ${latest_metrics.market_cap/1e9:.1f}B market cap")
                    elif latest_metrics.market_cap < 1e9:  # $1B market cap
                        score -= 0.1
                        reasons.append(f"Small market presence with ${latest_metrics.market_cap/1e9:.1f}B market cap")

                # 4. Gross Margins (indicating technological advantage)
                if latest_metrics.gross_margin:
                    if latest_metrics.gross_margin > 0.50:  # 50% gross margin
                        score += 0.2
                        reasons.append(f"Strong gross margins of {latest_metrics.gross_margin:.1%}")
                    elif latest_metrics.gross_margin < 0.30:  # 30% gross margin
                        score -= 0.2
                        reasons.append(f"Low gross margins of {latest_metrics.gross_margin:.1%}")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                wood_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Wood analysis",
                    metrics={
                        "score": score,
                        "revenue_growth": latest_metrics.revenue_growth,
                        "rd_to_revenue": rd_to_revenue if latest_metrics.research_and_development and latest_metrics.revenue else None,
                        "market_cap": latest_metrics.market_cap,
                        "gross_margin": latest_metrics.gross_margin
                    }
                )

            except Exception as e:
                wood_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Wood analysis: {str(e)}"
                )

        return wood_analysis
    
    def _generate_signal(self, total_score: float, max_possible_score: float) -> tuple[str, float]:
        """Generate signal and confidence based on Wood's criteria"""
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
                """You are a Cathie Wood AI agent. Analyze the investment based on:
                - Disruptive Technology/Innovation
                - Exponential Growth Potential
                - Market Leadership Position
                - Innovation-Driven Growth
                - Long-term Value Creation
                
                Focus on breakthrough technologies in:
                - Artificial Intelligence
                - Robotics
                - Genomics
                - Fintech
                - Blockchain/Crypto
                - Energy Innovation
                
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
    
    def _analyze_disruptive_potential(self, metrics: list, financial_line_items: list) -> dict:
        """Analyze disruptive potential using Wood's criteria"""
        # Keep existing implementation
        pass
    
    def _analyze_innovation_growth(self, metrics: list, financial_line_items: list) -> dict:
        """Analyze innovation-driven growth using Wood's criteria"""
        # Keep existing implementation
        pass
    
    def _analyze_cathie_wood_valuation(self, financial_line_items: list, market_cap: float) -> dict:
        """Calculate valuation using Wood's approach"""
        # Keep existing implementation
        pass

# For backward compatibility
def cathie_wood_agent(state: AgentState) -> dict:
    """Legacy wrapper for backward compatibility"""
    agent = CathieWoodAgent(
        name="cathie_wood_agent",
        description="Analyzes stocks using Cathie Wood's disruptive innovation principles"
    )
    return agent.execute(state)