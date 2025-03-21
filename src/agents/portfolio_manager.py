import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from typing_extensions import Literal
from utils.progress import progress
from utils.llm import call_llm
from .base_agent import BaseAgent


class PortfolioDecision(BaseModel):
    action: Literal["buy", "sell", "short", "cover", "hold"]
    quantity: int = Field(description="Number of shares to trade")
    confidence: float = Field(description="Confidence in the decision, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the decision")


class PortfolioManagerOutput(BaseModel):
    decisions: dict[str, PortfolioDecision] = Field(description="Dictionary of ticker to trading decisions")


class PortfolioManagerAgent(BaseAgent):
    """Agent that makes final trading decisions based on all analyst signals."""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        super().__init__(name, description or "Makes final trading decisions based on all analyst signals", config)
    
    def analyze(self, state: AgentState) -> Dict[str, PortfolioDecision]:
        """Makes trading decisions based on all analyst signals."""
        data = state["data"]
        metadata = state["metadata"]
        
        # Get all signals from analysts
        signals_by_ticker = {}
        for ticker in data["tickers"]:
            signals_by_ticker[ticker] = {}
            for analyst, signals in data["analyst_signals"].items():
                if ticker in signals:
                    signals_by_ticker[ticker][analyst] = signals[ticker]

        # Get current prices and portfolio
        current_prices = data.get("current_prices", {})
        portfolio = data.get("portfolio", {})
        max_shares = data.get("max_shares", {})

        # Generate trading decisions
        output = self._generate_trading_decision(
            tickers=data["tickers"],
            signals_by_ticker=signals_by_ticker,
            current_prices=current_prices,
            max_shares=max_shares,
            portfolio=portfolio,
            model_name=metadata.get("model_name", "gpt-4"),
            model_provider=metadata.get("model_provider", "OpenAI")
        )

        # Print the reasoning if the flag is set
        if metadata.get("show_reasoning"):
            show_agent_reasoning(output.decisions, "Portfolio Manager")

        return output.decisions

    def _generate_trading_decision(
        self,
        tickers: list[str],
        signals_by_ticker: dict[str, dict],
        current_prices: dict[str, float],
        max_shares: dict[str, int],
        portfolio: dict[str, float],
        model_name: str,
        model_provider: str,
    ) -> PortfolioManagerOutput:
        """Generate trading decisions based on analyst signals."""
        try:
            # Create the prompt for the LLM
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a portfolio manager making trading decisions based on analyst signals.
                Your goal is to maximize returns while managing risk.
                For each ticker, decide whether to buy, sell, short, cover, or hold based on the analyst signals.
                Consider the current portfolio positions and price levels.
                Provide clear reasoning for each decision."""),
                ("human", """Here are the details:

                Tickers: {tickers}
                Analyst Signals: {signals}
                Current Prices: {prices}
                Max Shares: {max_shares}
                Current Portfolio: {portfolio}

                For each ticker, provide a trading decision in the following format:
                {{
                    "decisions": {{
                        "TICKER": {{
                            "action": "buy|sell|short|cover|hold",
                            "quantity": number_of_shares,
                            "confidence": confidence_level,
                            "reasoning": "detailed reasoning"
                        }},
                        ...
                    }}
                }}""")
            ])

            # Format the prompt variables
            formatted_signals = json.dumps(signals_by_ticker, indent=2)
            formatted_prices = json.dumps(current_prices, indent=2)
            formatted_max_shares = json.dumps(max_shares, indent=2)
            formatted_portfolio = json.dumps(portfolio, indent=2)

            # Call the LLM
            response = call_llm(
                prompt=prompt,
                model_name=model_name,
                model_provider=model_provider,
                tickers=tickers,
                signals=formatted_signals,
                prices=formatted_prices,
                max_shares=formatted_max_shares,
                portfolio=formatted_portfolio
            )

            # Parse the response
            try:
                output = PortfolioManagerOutput.model_validate_json(response.content)
                return output
            except Exception as e:
                print(f"Error parsing LLM response: {e}")
                return self._create_default_portfolio_output(tickers)

        except Exception as e:
            print(f"Error generating trading decisions: {e}")
            return self._create_default_portfolio_output(tickers)

    def _create_default_portfolio_output(self, tickers: list[str]) -> PortfolioManagerOutput:
        """Create a default portfolio output with hold decisions."""
        decisions = {}
        for ticker in tickers:
            decisions[ticker] = PortfolioDecision(
                action="hold",
                quantity=0,
                confidence=0.0,
                reasoning="Error occurred, defaulting to hold"
            )
        return PortfolioManagerOutput(decisions=decisions)
