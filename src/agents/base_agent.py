from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning

class AgentSignal(BaseModel):
    """Standard signal format for all agents"""
    signal: str  # bullish, bearish, or neutral
    confidence: float  # 0 to 100
    reasoning: str
    metrics: Dict[str, Any] = {}  # Additional metrics specific to each agent

class BaseAgent(ABC):
    """Base class for all trading agents"""
    
    def __init__(self, name: str, description: str = "", config: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.config = config or {}
    
    @abstractmethod
    def analyze(self, state: AgentState) -> Dict[str, AgentSignal]:
        """
        Main analysis method that each agent must implement.
        Returns a dictionary mapping ticker symbols to their signals.
        """
        pass

    def execute(self, state: AgentState) -> dict:
        """
        Common execution flow for all agents.
        1. Performs analysis
        2. Creates message
        3. Updates state
        4. Shows reasoning if needed
        """
        analysis_results = self.analyze(state)
        
        # Create the message
        message = HumanMessage(
            content=str(analysis_results),
            name=self.name
        )

        # Show reasoning if requested
        if state["metadata"].get("show_reasoning", False):
            show_agent_reasoning(analysis_results, self.name)

        # Update state with signals
        state["data"]["analyst_signals"][self.name] = analysis_results

        return {
            "messages": [message],
            "data": state["data"]
        }

    def show_reasoning(self, analysis: Dict[str, AgentSignal]) -> None:
        """Show agent reasoning in a standardized format"""
        show_agent_reasoning(analysis, self.name)