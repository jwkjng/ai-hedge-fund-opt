from typing import Dict, Any
from datetime import datetime
from .base_agent import BaseAgent, AgentSignal
from graph.state import AgentState
from tools.api import (
    get_financial_metrics,
    get_market_data,
    get_company_news,
    search_line_items
)
from utils.progress import progress

class CharlieMungerAgent(BaseAgent):
    """Agent that implements Charlie Munger's investment strategy"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes stocks using Charlie Munger's principles", config)
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        data = state["data"]
        end_date = data["end_date"]
        tickers = data["tickers"]
        
        # Initialize analysis for each ticker
        munger_analysis = {}
        
        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Munger's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    munger_analysis[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Get additional financial line items
                financial_line_items = search_line_items(
                    ticker,
                    [
                        "gross_margin",
                        "operating_margin",
                        "net_margin",
                        "return_on_equity",
                        "debt_to_equity",
                        "current_ratio",
                        "quick_ratio",
                        "inventory_turnover",
                        "receivables_turnover"
                    ],
                    end_date
                )
                
                market_data = get_market_data(ticker, end_date)
                market_cap = market_data.get("market_cap", 0) if market_data else 0
                
                progress.update_status(self.name, ticker, "Fetching company news")
                # Munger avoids businesses with frequent negative press
                company_news = get_company_news(
                    ticker,
                    end_date,
                    # Look back 1 year for news
                    start_date=None,
                    limit=100
                )
                
                # Perform analysis
                moat_analysis = self._analyze_moat_strength(metrics, financial_line_items)
                management_analysis = self._analyze_management_quality(financial_line_items)
                predictability_analysis = self._analyze_predictability(financial_line_items)
                valuation_analysis = self._calculate_munger_valuation(financial_line_items, market_cap)
                
                # Combine scores with Munger's weighting preferences
                total_score = (
                    moat_analysis["score"] * 0.35 +
                    management_analysis["score"] * 0.25 +
                    predictability_analysis["score"] * 0.25 +
                    valuation_analysis["score"] * 0.15
                )
                
                max_possible_score = 10  # Scale to 0-10
                
                # Generate signal and confidence
                signal, confidence = self._generate_signal(total_score)
                
                # Generate reasoning
                reasons = []
                if moat_analysis["reasoning"]:
                    reasons.append(f"Moat Analysis: {moat_analysis['reasoning']}")
                if management_analysis["reasoning"]:
                    reasons.append(f"Management Analysis: {management_analysis['reasoning']}")
                if predictability_analysis["reasoning"]:
                    reasons.append(f"Predictability Analysis: {predictability_analysis['reasoning']}")
                if valuation_analysis["reasoning"]:
                    reasons.append(f"Valuation Analysis: {valuation_analysis['reasoning']}")
                
                munger_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=confidence,
                    reasoning="\n".join(reasons) or "Insufficient data for Munger analysis",
                    metrics={
                        "moat_score": moat_analysis["score"],
                        "management_score": management_analysis["score"],
                        "predictability_score": predictability_analysis["score"],
                        "valuation_score": valuation_analysis["score"],
                        "total_score": total_score
                    }
                )
                
            except Exception as e:
                munger_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Munger analysis: {str(e)}"
                )
        
        return munger_analysis
    
    def _analyze_moat_strength(self, metrics, financial_line_items) -> dict:
        """Analyze the company's economic moat."""
        score = 0
        reasons = []
        
        # Check gross margins
        if metrics[0].gross_margin:
            if metrics[0].gross_margin > 0.4:  # 40% gross margin
                score += 3
                reasons.append("Strong gross margins indicating pricing power")
            elif metrics[0].gross_margin > 0.2:  # 20% gross margin
                score += 1
                reasons.append("Moderate gross margins")
        
        # Check operating margins
        if metrics[0].operating_margin:
            if metrics[0].operating_margin > 0.2:  # 20% operating margin
                score += 3
                reasons.append("Strong operating margins indicating operational efficiency")
            elif metrics[0].operating_margin > 0.1:  # 10% operating margin
                score += 1
                reasons.append("Moderate operating margins")
        
        # Check return on equity
        if metrics[0].return_on_equity:
            if metrics[0].return_on_equity > 0.2:  # 20% ROE
                score += 4
                reasons.append("High returns on equity indicating competitive advantage")
            elif metrics[0].return_on_equity > 0.15:  # 15% ROE
                score += 2
                reasons.append("Good returns on equity")
        
        return {
            "score": score / 10,  # Normalize to 0-1
            "reasoning": "; ".join(reasons)
        }
    
    def _analyze_management_quality(self, financial_line_items) -> dict:
        """Analyze management quality based on financial metrics."""
        score = 0
        reasons = []
        
        # Check capital allocation through ROE trends
        if financial_line_items and len(financial_line_items) > 1:
            latest_roe = financial_line_items[0].get("return_on_equity")
            prev_roe = financial_line_items[1].get("return_on_equity")
            if latest_roe and prev_roe:
                if latest_roe > prev_roe:
                    score += 3
                    reasons.append("Improving returns on equity")
                elif latest_roe > 0.15:  # Still good even if not improving
                    score += 1
                    reasons.append("Maintaining good returns on equity")
        
        # Check debt management
        if financial_line_items and financial_line_items[0].get("debt_to_equity"):
            debt_to_equity = financial_line_items[0]["debt_to_equity"]
            if debt_to_equity < 0.5:
                score += 4
                reasons.append("Conservative debt management")
            elif debt_to_equity < 1.0:
                score += 2
                reasons.append("Reasonable debt levels")
        
        # Check working capital management
        if financial_line_items:
            current_ratio = financial_line_items[0].get("current_ratio")
            if current_ratio and current_ratio > 2:
                score += 3
                reasons.append("Strong working capital management")
            elif current_ratio and current_ratio > 1.5:
                score += 1
                reasons.append("Adequate working capital management")
        
        return {
            "score": score / 10,  # Normalize to 0-1
            "reasoning": "; ".join(reasons)
        }
    
    def _analyze_predictability(self, financial_line_items) -> dict:
        """Analyze business predictability."""
        score = 0
        reasons = []
        
        if financial_line_items and len(financial_line_items) > 1:
            # Check revenue stability
            revenues = [item.get("revenue") for item in financial_line_items if item.get("revenue")]
            if len(revenues) > 1:
                revenue_growth_rates = [(revenues[i] - revenues[i+1]) / revenues[i+1] for i in range(len(revenues)-1)]
                avg_growth = sum(revenue_growth_rates) / len(revenue_growth_rates)
                growth_volatility = sum((r - avg_growth) ** 2 for r in revenue_growth_rates) / len(revenue_growth_rates)
                
                if growth_volatility < 0.1:  # Low volatility
                    score += 5
                    reasons.append("Highly stable revenue growth")
                elif growth_volatility < 0.2:
                    score += 3
                    reasons.append("Moderately stable revenue growth")
            
            # Check margin stability
            margins = [item.get("operating_margin") for item in financial_line_items if item.get("operating_margin")]
            if len(margins) > 1:
                margin_volatility = sum((margins[i] - margins[i+1]) ** 2 for i in range(len(margins)-1)) / len(margins)
                
                if margin_volatility < 0.05:  # Low volatility
                    score += 5
                    reasons.append("Highly stable operating margins")
                elif margin_volatility < 0.1:
                    score += 3
                    reasons.append("Moderately stable operating margins")
        
        return {
            "score": score / 10,  # Normalize to 0-1
            "reasoning": "; ".join(reasons)
        }
    
    def _calculate_munger_valuation(self, financial_line_items, market_cap) -> dict:
        """Calculate valuation using Munger's principles."""
        score = 0
        reasons = []
        
        if not market_cap or not financial_line_items:
            return {"score": 0, "reasoning": "Insufficient data for valuation analysis"}
        
        # Calculate owner earnings (Munger's preferred metric)
        if (financial_line_items[0].get("net_income") and 
            financial_line_items[0].get("depreciation_and_amortization") and 
            financial_line_items[0].get("capital_expenditure")):
            
            owner_earnings = (
                financial_line_items[0]["net_income"] +
                financial_line_items[0]["depreciation_and_amortization"] -
                financial_line_items[0]["capital_expenditure"]
            )
            
            # Calculate owner earnings yield
            owner_earnings_yield = owner_earnings / market_cap
            
            if owner_earnings_yield > 0.1:  # 10% yield
                score += 5
                reasons.append("Attractive owner earnings yield")
            elif owner_earnings_yield > 0.06:  # 6% yield
                score += 3
                reasons.append("Reasonable owner earnings yield")
        
        # Check price to book ratio
        if financial_line_items[0].get("price_to_book_ratio"):
            pb_ratio = financial_line_items[0]["price_to_book_ratio"]
            if pb_ratio < 3:
                score += 3
                reasons.append("Reasonable price to book ratio")
            elif pb_ratio < 5:
                score += 1
                reasons.append("Acceptable price to book ratio")
        
        # Check debt adjusted valuation
        if financial_line_items[0].get("enterprise_value") and financial_line_items[0].get("ebitda"):
            ev_ebitda = financial_line_items[0]["enterprise_value"] / financial_line_items[0]["ebitda"]
            if ev_ebitda < 10:
                score += 2
                reasons.append("Attractive EV/EBITDA ratio")
            elif ev_ebitda < 15:
                score += 1
                reasons.append("Reasonable EV/EBITDA ratio")
        
        return {
            "score": score / 10,  # Normalize to 0-1
            "reasoning": "; ".join(reasons)
        }
    
    def _generate_signal(self, total_score: float) -> tuple[str, float]:
        """Generate signal and confidence based on Munger's criteria"""
        if total_score > 0.7:
            return "bullish", 0.8
        elif total_score < 0.3:
            return "bearish", 0.8
        else:
            return "neutral", 0.6

# For backward compatibility
def charlie_munger_agent(state: AgentState) -> dict:
    """Legacy wrapper for backward compatibility"""
    agent = CharlieMungerAgent(
        name="charlie_munger_agent",
        description="Analyzes stocks using Charlie Munger's investment principles"
    )
    return agent.execute(state)