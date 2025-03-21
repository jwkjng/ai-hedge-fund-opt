from typing import Dict, Any
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import pandas as pd
import numpy as np
from datetime import datetime
import json

from tools.api import (
    get_company_news,
    News
)
from .base_agent import BaseAgent, AgentSignal


class SentimentAgent(BaseAgent):
    """Agent that analyzes market sentiment through various indicators."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Analyzes market sentiment through news and social media", config)
    
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """Analyze market sentiment for multiple tickers."""
        data = state["data"]
        end_date = data["end_date"]
        start_date = data["start_date"]
        tickers = data["tickers"]

        # Initialize sentiment analysis for each ticker
        sentiment_analysis = {}

        for ticker in tickers:
            progress.update_status(self.name, ticker, "Analyzing sentiment")
            
            try:
                # Get company news
                news = get_company_news(ticker, end_date, start_date, test_mode=True)
                
                # Analyze news sentiment
                sentiment_score = self._analyze_news(news)
                
                # Convert score to signal
                signal = "neutral"
                if sentiment_score > 0.3:
                    signal = "bullish"
                elif sentiment_score < -0.3:
                    signal = "bearish"
                
                # Store the analysis results
                sentiment_analysis[ticker] = AgentSignal(
                    signal=signal,
                    confidence=0.7,  # Base confidence
                    reasoning=f"News sentiment score: {sentiment_score:.2f}"
                )

            except Exception as e:
                sentiment_analysis[ticker] = AgentSignal(
                    signal="neutral",
                    confidence=0,
                    reasoning=f"Error analyzing sentiment: {str(e)}"
                )

            # Print the reasoning if the flag is set
            if state["metadata"].get("show_reasoning"):
                show_agent_reasoning(self.name, ticker, sentiment_analysis[ticker].reasoning)

        return sentiment_analysis

    def _analyze_news(self, news: list[News]) -> float:
        """Analyze news sentiment."""
        if not news:
            return 0

        # Simple sentiment based on news volume
        recent_volume = len([
            n for n in news 
            if (datetime.now() - datetime.fromisoformat(n.date)).days <= 7
        ])
        sentiment = (recent_volume - 5) / 10  # Normalize around 5 articles per week
        return max(min(sentiment, 1), -1)  # Normalize to [-1, 1]