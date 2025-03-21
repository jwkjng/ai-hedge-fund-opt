from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentSignal
from graph.state import AgentState, show_agent_reasoning
from tools.api import get_financial_metrics, get_market_data, search_line_items
from utils.llm import call_llm
from utils.progress import progress
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
import json

class BillAckmanAgent(BaseAgent):
    """Agent that analyzes stocks using Bill Ackman's investment principles."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Bill Ackman's principles", config)
        self.min_fcf_yield = config.get("min_fcf_yield", 0.05)  # 5% minimum free cash flow yield
        self.min_revenue_growth = config.get("min_revenue_growth", 0.10)  # 10% minimum revenue growth
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyzes stocks using Bill Ackman's investment principles."""
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]

        # Initialize analysis for each ticker
        ackman_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Ackman's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    ackman_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Initialize scoring
                score = 0
                confidence = 0.8  # High confidence in Ackman's principles
                reasons = []

                # 1. Free Cash Flow Yield
                if latest_metrics.free_cash_flow and latest_metrics.market_cap:
                    fcf_yield = latest_metrics.free_cash_flow / latest_metrics.market_cap
                    if fcf_yield > self.min_fcf_yield:
                        score += 0.3
                        reasons.append(f"Strong free cash flow yield of {fcf_yield:.1%}")
                    elif fcf_yield > self.min_fcf_yield * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate free cash flow yield of {fcf_yield:.1%}")
                    elif fcf_yield < 0:
                        score -= 0.3
                        reasons.append(f"Negative free cash flow yield")

                # 2. Revenue Growth
                if latest_metrics.revenue_growth:
                    if latest_metrics.revenue_growth > self.min_revenue_growth:
                        score += 0.3
                        reasons.append(f"Strong revenue growth of {latest_metrics.revenue_growth:.1%}")
                    elif latest_metrics.revenue_growth > self.min_revenue_growth * 0.5:
                        score += 0.1
                        reasons.append(f"Moderate revenue growth of {latest_metrics.revenue_growth:.1%}")
                    elif latest_metrics.revenue_growth < 0:
                        score -= 0.2
                        reasons.append(f"Negative revenue growth of {latest_metrics.revenue_growth:.1%}")

                # 3. Operating Margins
                if latest_metrics.operating_margin:
                    if latest_metrics.operating_margin > 0.20:  # 20% operating margin
                        score += 0.2
                        reasons.append(f"Strong operating margin of {latest_metrics.operating_margin:.1%}")
                    elif latest_metrics.operating_margin < 0:
                        score -= 0.2
                        reasons.append(f"Negative operating margin of {latest_metrics.operating_margin:.1%}")

                # 4. Market Position
                if latest_metrics.market_cap:
                    if latest_metrics.market_cap > 10e9:  # $10B market cap
                        score += 0.2
                        reasons.append(f"Strong market position with ${latest_metrics.market_cap/1e9:.1f}B market cap")
                    elif latest_metrics.market_cap < 1e9:  # $1B market cap
                        score -= 0.1
                        reasons.append(f"Small market position with ${latest_metrics.market_cap/1e9:.1f}B market cap")

                # 5. Capital Allocation
                if latest_metrics.return_on_equity:
                    if latest_metrics.return_on_equity > 0.15:  # 15% ROE
                        score += 0.2
                        reasons.append(f"Strong capital allocation with {latest_metrics.return_on_equity:.1%} ROE")
                    elif latest_metrics.return_on_equity < 0:
                        score -= 0.2
                        reasons.append(f"Poor capital allocation with {latest_metrics.return_on_equity:.1%} ROE")

                # Convert score to signal
                signal = "neutral"
                if score > 0.3:
                    signal = "bullish"
                elif score < -0.3:
                    signal = "bearish"

                # Store the analysis results
                ackman_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Ackman analysis",
                    metrics={
                        "score": score,
                        "fcf_yield": fcf_yield if latest_metrics.free_cash_flow and latest_metrics.market_cap else None,
                        "revenue_growth": latest_metrics.revenue_growth,
                        "operating_margin": latest_metrics.operating_margin,
                        "market_cap": latest_metrics.market_cap,
                        "return_on_equity": latest_metrics.return_on_equity
                    }
                )

            except Exception as e:
                ackman_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Ackman analysis: {str(e)}"
                )

        return ackman_analysis
    
    def _generate_signal(self, total_score: float, max_possible_score: float) -> tuple[str, float]:
        """Generate signal and confidence based on Ackman's criteria"""
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
                """You are a Bill Ackman AI agent. Analyze the investment based on:
                - Business Quality and Growth
                - Financial Discipline and Capital Structure
                - Valuation and Margin of Safety
                - Activist Potential (if applicable)
                
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
    
    def _analyze_business_quality(self, metrics: list, financial_line_items: list) -> dict:
        """Analyze business quality using Ackman's criteria"""
        # Keep existing implementation
        pass
    
    def _analyze_financial_discipline(self, metrics: list, financial_line_items: list) -> dict:
        """Analyze financial discipline using Ackman's criteria"""
        # Keep existing implementation
        pass
    
    def _analyze_valuation(self, financial_line_items: list, market_cap: float) -> dict:
        """Calculate valuation using Ackman's approach"""
        # Keep existing implementation
        pass

# For backward compatibility
def bill_ackman_agent(state: AgentState) -> dict:
    """Legacy wrapper for backward compatibility"""
    agent = BillAckmanAgent(
        name="bill_ackman_agent",
        description="Analyzes stocks using Bill Ackman's investment principles"
    )
    return agent.execute(state)