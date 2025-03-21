import math
import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime

from .base_agent import BaseAgent, AgentSignal
from graph.state import AgentState
from tools.api import (
    get_prices,
    prices_to_df,
    get_technical_indicators,
    get_market_status,
    get_market_holidays
)
from utils.progress import progress

class TechnicalAnalysisAgent(BaseAgent):
    """Agent that implements multi-strategy technical analysis"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description, config)
        self.strategy_weights = config.get("weights", {
            "trend": 0.25,
            "mean_reversion": 0.20,
            "momentum": 0.25,
            "volatility": 0.15,
            "stat_arb": 0.15,
        })
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        data = state["data"]
        start_date = data["start_date"]
        end_date = data["end_date"]
        tickers = data["tickers"]
        
        # Get market status for trading hours
        market_status = get_market_status()
        market_holidays = get_market_holidays()
        
        analysis_results = {}
        
        for ticker in tickers:
            progress.update_status(self.name, ticker, "Fetching price data")
            prices = get_prices(ticker, start_date, end_date)
            if not prices:
                continue
                
            df = prices_to_df(prices)
            
            # Get technical indicators from Polygon.io
            progress.update_status(self.name, ticker, "Calculating technical indicators")
            
            # Get RSI
            rsi_data = get_technical_indicators(ticker, "rsi", {
                "timespan": "day",
                "window": 14,
                "series_type": "close"
            })
            
            # Get MACD
            macd_data = get_technical_indicators(ticker, "macd", {
                "timespan": "day",
                "short_window": 12,
                "long_window": 26,
                "signal_window": 9,
                "series_type": "close"
            })
            
            # Get EMAs
            ema_20 = get_technical_indicators(ticker, "ema", {
                "timespan": "day",
                "window": 20,
                "series_type": "close"
            })
            
            ema_50 = get_technical_indicators(ticker, "ema", {
                "timespan": "day",
                "window": 50,
                "series_type": "close"
            })
            
            # Analyze signals
            trend_signal = self._analyze_trend(df, ema_20, ema_50)
            momentum_signal = self._analyze_momentum(df, rsi_data)
            mean_reversion_signal = self._analyze_mean_reversion(df)
            volatility_signal = self._analyze_volatility(df)
            stat_arb_signal = self._analyze_stat_arb(df, macd_data)
            
            # Adjust signals based on market conditions
            market_adjustment = self._get_market_adjustment(market_status, market_holidays)
            
            # Combine signals using weights
            weighted_signal = (
                self.strategy_weights["trend"] * trend_signal +
                self.strategy_weights["momentum"] * momentum_signal +
                self.strategy_weights["mean_reversion"] * mean_reversion_signal +
                self.strategy_weights["volatility"] * volatility_signal +
                self.strategy_weights["stat_arb"] * stat_arb_signal
            ) * market_adjustment
            
            analysis_results[ticker] = AgentSignal(
                signal="bullish" if weighted_signal > 0.5 else "bearish" if weighted_signal < -0.5 else "neutral",
                confidence=abs(weighted_signal),
                reasoning={
                    "trend": trend_signal,
                    "momentum": momentum_signal,
                    "mean_reversion": mean_reversion_signal,
                    "volatility": volatility_signal,
                    "stat_arb": stat_arb_signal,
                    "market_adjustment": market_adjustment,
                    "weighted_signal": weighted_signal
                }
            )
            
        return analysis_results

    def _get_market_adjustment(self, market_status: dict, market_holidays: list) -> float:
        """Calculate market condition adjustment factor."""
        adjustment = 1.0
        
        # Reduce signal strength during non-regular hours
        if market_status.get("market") == "open":
            if market_status.get("session") != "regular":
                adjustment *= 0.8
        
        # Reduce signal strength near holidays
        upcoming_holiday = next(
            (h for h in market_holidays if h["date"] > datetime.now().strftime("%Y-%m-%d")),
            None
        )
        if upcoming_holiday and (datetime.strptime(upcoming_holiday["date"], "%Y-%m-%d") - datetime.now()).days <= 3:
            adjustment *= 0.9
            
        return adjustment
    
    def _analyze_trend(self, df: pd.DataFrame, ema_20: dict, ema_50: dict) -> float:
        """Analyze trend using EMAs"""
        if not ema_20.get("results") or not ema_50.get("results"):
            return 0.0
            
        ema_20_value = ema_20["results"][-1]["value"]
        ema_50_value = ema_50["results"][-1]["value"]
        current_price = df["close"].iloc[-1]
        
        # Strong uptrend if price > EMA20 > EMA50
        if current_price > ema_20_value > ema_50_value:
            return 1.0
        # Strong downtrend if price < EMA20 < EMA50
        elif current_price < ema_20_value < ema_50_value:
            return -1.0
        # Weak trend or consolidation
        else:
            return 0.0
    
    def _analyze_momentum(self, df: pd.DataFrame, rsi_data: dict) -> float:
        """Analyze momentum using RSI"""
        if not rsi_data.get("results"):
            return 0.0
            
        rsi = rsi_data["results"][-1]["value"]
        
        # Oversold
        if rsi < 30:
            return 1.0
        # Overbought
        elif rsi > 70:
            return -1.0
        # Neutral
        else:
            return 0.0
    
    def _analyze_mean_reversion(self, df: pd.DataFrame) -> float:
        """Analyze mean reversion potential"""
        if len(df) < 20:
            return 0.0
            
        current_price = df["close"].iloc[-1]
        sma_20 = df["close"].rolling(window=20).mean().iloc[-1]
        std_20 = df["close"].rolling(window=20).std().iloc[-1]
        
        z_score = (current_price - sma_20) / std_20
        
        # Strong mean reversion signal if price is more than 2 std dev away from mean
        if z_score > 2:
            return -1.0
        elif z_score < -2:
            return 1.0
        else:
            return 0.0
    
    def _analyze_volatility(self, df: pd.DataFrame) -> float:
        """Analyze volatility trends"""
        if len(df) < 20:
            return 0.0
            
        # Calculate historical volatility
        returns = df["close"].pct_change()
        current_vol = returns.rolling(window=20).std().iloc[-1]
        avg_vol = returns.rolling(window=60).std().iloc[-1]
        
        # Signal based on volatility regime
        if current_vol > avg_vol * 1.5:
            return -0.5  # Higher risk, reduce exposure
        elif current_vol < avg_vol * 0.5:
            return 0.5   # Lower risk, increase exposure
        else:
            return 0.0
    
    def _analyze_stat_arb(self, df: pd.DataFrame, macd_data: dict) -> float:
        """Analyze statistical arbitrage opportunities using MACD"""
        if not macd_data.get("results"):
            return 0.0
            
        macd = macd_data["results"][-1]
        macd_line = macd["value"]
        signal_line = macd["signal"]
        
        # MACD crossover signals
        if macd_line > signal_line:
            return 1.0
        elif macd_line < signal_line:
            return -1.0
        else:
            return 0.0