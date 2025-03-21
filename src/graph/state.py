from typing_extensions import Annotated, Sequence, TypedDict

import operator
from langchain_core.messages import BaseMessage


import json


def merge_dicts(a: dict[str, any], b: dict[str, any]) -> dict[str, any]:
    return {**a, **b}


# Define agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    data: Annotated[dict[str, any], merge_dicts]
    metadata: Annotated[dict[str, any], merge_dicts]


def show_agent_reasoning(agent_name: str, reasoning: str) -> None:
    """Show agent reasoning if enabled."""
    print(f"{agent_name} reasoning: {reasoning}")

def show_agent_reasoning(agent_name: str, ticker: str, reasoning: str) -> None:
    """Show agent reasoning if enabled."""
    print(f"{agent_name} reasoning for {ticker}: {reasoning}")

class AgentState(dict):
    """State object for agents to share data."""
    pass
