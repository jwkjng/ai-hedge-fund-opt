from typing import Dict, Any, List
from datetime import datetime
from .base_agent import BaseAgent, AgentSignal
from graph.state import AgentState
from tools.api import (
    get_financial_metrics,
    get_market_data,
    get_technical_indicators,
    get_company_news,
    get_prices,
    get_market_status,
    get_market_holidays,
)
from utils.progress import progress
import statistics

class StanleyDruckenmillerAgent(BaseAgent):
    """Agent that implements Stanley Druckenmiller's investment strategy"""
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        data = state["data"]
        end_date = data["end_date"]
        start_date = data["start_date"]
        tickers = data["tickers"]
        
        # Get market status for timing
        market_status = get_market_status()
        market_holidays = get_market_holidays()
        
        analysis_results = {}
        
        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing using Druckenmiller's principles")
            
            try:
                # Get financial metrics
                metrics = get_financial_metrics(ticker, end_date, period="ttm", limit=1)
                if not metrics:
                    analysis_results[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No financial metrics available"
                    )
                    continue

                latest_metrics = metrics[0]
                
                # Get technical indicators
                ema_20 = get_technical_indicators(ticker, "ema", 20, end_date)
                ema_50 = get_technical_indicators(ticker, "ema", 50, end_date)
                rsi = get_technical_indicators(ticker, "rsi", 14, end_date)
                macd = get_technical_indicators(ticker, "macd", None, end_date)
                
                # Get price data
                prices = get_prices(ticker, start_date, end_date)
                if not prices:
                    analysis_results[ticker] = AgentSignal(
                        signal="neutral",
                        confidence=0,
                        reasoning="No price data available"
                    )
                    continue
                
                # Get market data
                market_data = get_market_data(ticker, end_date)
                market_cap = market_data.get("market_cap", 0) if market_data else 0
                
                # Get news
                news = get_company_news(ticker, end_date, start_date)
                
                # Calculate quality score
                quality_score = self._analyze_quality(latest_metrics)
                
                # Calculate momentum score
                momentum_score = self._analyze_momentum(prices, ema_20, ema_50, rsi)
                
                # Calculate market environment score
                market_score = self._analyze_market_environment(market_status, market_holidays)
                
                # Calculate corporate activity score
                corporate_score = self._analyze_corporate_activity(news)
                
                # Combine signals
                signal = self._combine_signals(
                    quality=quality_score,
                    momentum=momentum_score,
                    market=market_score,
                    corporate=corporate_score
                )
                
                analysis_results[ticker] = signal
                
            except Exception as e:
                analysis_results[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error in Druckenmiller analysis: {str(e)}"
                )
        
        return analysis_results
    
    def _analyze_quality(self, metrics) -> float:
        """Analyze business quality."""
        score = 0
        
        # Check profitability
        if metrics.operating_margin:
            if metrics.operating_margin > 0.2:  # 20% margin
                score += 0.3
            elif metrics.operating_margin > 0.1:  # 10% margin
                score += 0.1
            elif metrics.operating_margin < 0:
                score -= 0.3
        
        # Check growth
        if metrics.revenue_growth:
            if metrics.revenue_growth > 0.2:  # 20% growth
                score += 0.3
            elif metrics.revenue_growth > 0.1:  # 10% growth
                score += 0.1
            elif metrics.revenue_growth < 0:
                score -= 0.2
        
        # Check balance sheet strength
        if metrics.debt_to_equity:
            if metrics.debt_to_equity < 0.5:
                score += 0.2
            elif metrics.debt_to_equity > 2:
                score -= 0.2
        
        # Normalize to [-1, 1]
        return max(min(score, 1), -1)
    
    def _analyze_momentum(self, prices, ema_20, ema_50, rsi) -> float:
        """Analyze price momentum."""
        score = 0
        
        # Check price trend
        if prices and len(prices) > 1:
            current_price = prices[-1].close
            prev_price = prices[0].close
            price_change = (current_price - prev_price) / prev_price
            
            if price_change > 0.1:  # 10% gain
                score += 0.3
            elif price_change < -0.1:  # 10% loss
                score -= 0.3
        
        # Check EMAs
        if ema_20 and ema_50 and len(ema_20) > 0 and len(ema_50) > 0:
            ema_20_value = ema_20[-1].value
            ema_50_value = ema_50[-1].value
            
            if ema_20_value > ema_50_value:  # Bullish crossover
                score += 0.2
            elif ema_20_value < ema_50_value:  # Bearish crossover
                score -= 0.2
        
        # Check RSI
        if rsi and len(rsi) > 0:
            rsi_value = rsi[-1].value
            
            if rsi_value > 70:  # Overbought
                score -= 0.2
            elif rsi_value < 30:  # Oversold
                score += 0.2
        
        # Normalize to [-1, 1]
        return max(min(score, 1), -1)
    
    def _analyze_market_environment(self, market_status, market_holidays) -> float:
        """Analyze market environment."""
        score = 0
        
        # Check market session
        if market_status.get("market") == "open":
            if market_status.get("session") == "regular":
                score += 0.2
            else:
                score -= 0.1
        
        # Check upcoming holidays
        upcoming_holiday = next(
            (h for h in market_holidays if h["date"] > datetime.now().strftime("%Y-%m-%d")),
            None
        )
        if upcoming_holiday and (datetime.strptime(upcoming_holiday["date"], "%Y-%m-%d") - datetime.now()).days <= 3:
            score -= 0.1
        
        # Normalize to [-1, 1]
        return max(min(score, 1), -1)
    
    def _analyze_corporate_activity(self, news) -> float:
        """Analyze corporate activity."""
        score = 0
        
        if not news:
            return 0
        
        # Count recent news
        recent_news = [
            n for n in news
            if (datetime.now() - datetime.strptime(n.date, "%Y-%m-%d")).days <= 30
        ]
        
        # Simple sentiment based on news volume
        news_volume = len(recent_news)
        if news_volume > 10:
            score += 0.3
        elif news_volume > 5:
            score += 0.1
        elif news_volume == 0:
            score -= 0.1
        
        # Normalize to [-1, 1]
        return max(min(score, 1), -1)
    
    def _combine_signals(
        self, 
        quality: float, 
        momentum: float, 
        market: float,
        corporate: float
    ) -> AgentSignal:
        """Combine different analysis signals into a final trading signal."""
        # Weights for different factors
        weights = {
            "quality": 0.3,
            "momentum": 0.3,
            "market": 0.2,
            "corporate": 0.2
        }
        
        weighted_score = (
            weights["quality"] * quality +
            weights["momentum"] * momentum +
            weights["market"] * market +
            weights["corporate"] * corporate
        )
        
        # Convert score to signal
        if weighted_score > 0.6:
            signal = "bullish"
        elif weighted_score < -0.6:
            signal = "bearish"
        else:
            signal = "neutral"
            
        return AgentSignal(
            signal=signal,
            confidence=abs(weighted_score),
            reasoning={
                "quality_score": quality,
                "momentum_score": momentum,
                "market_score": market,
                "corporate_score": corporate,
                "weighted_score": weighted_score
            }
        )