"""Constants and utilities related to analysts configuration."""

from agents.ben_graham import BenGrahamAgent
from agents.bill_ackman import BillAckmanAgent
from agents.fundamentals import FundamentalsAgent
from agents.sentiment import SentimentAgent
from agents.warren_buffett import WarrenBuffettAgent
from agents.risk_manager import RiskManagerAgent

# Define analyst configuration - single source of truth
ANALYST_CONFIG = {
    "ben_graham": {
        "display_name": "Ben Graham",
        "agent_class": BenGrahamAgent,
        "order": 0,
    },
    "bill_ackman": {
        "display_name": "Bill Ackman",
        "agent_class": BillAckmanAgent,
        "order": 1,
    },
    "warren_buffett": {
        "display_name": "Warren Buffett",
        "agent_class": WarrenBuffettAgent,
        "order": 2,
    },
    "fundamentals": {
        "display_name": "Fundamentals",
        "agent_class": FundamentalsAgent,
        "order": 3,
    },
    "sentiment": {
        "display_name": "Market Sentiment",
        "agent_class": SentimentAgent,
        "order": 4,
    },
    "risk_manager": {
        "display_name": "Risk Management",
        "agent_class": RiskManagerAgent,
        "order": 5,
    },
}

# Create a list of tuples for display order
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]

def get_analyst_class(key: str):
    """Get the agent class for a given analyst key."""
    if key not in ANALYST_CONFIG:
        raise ValueError(f"Unknown analyst key: {key}")
    return ANALYST_CONFIG[key]["agent_class"]

def get_analyst_display_name(key: str) -> str:
    """Get the display name for a given analyst key."""
    if key not in ANALYST_CONFIG:
        raise ValueError(f"Unknown analyst key: {key}")
    return ANALYST_CONFIG[key]["display_name"]
