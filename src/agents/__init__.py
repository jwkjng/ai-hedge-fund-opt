from .base_agent import BaseAgent, AgentSignal
from .agent_config import AgentConfig
from .registry import AgentRegistry
from .factory import AgentFactory

# Import all agents
from .warren_buffett import WarrenBuffettAgent
from .technicals import TechnicalAnalysisAgent
from .charlie_munger import CharlieMungerAgent
from .ben_graham import BenGrahamAgent
from .bill_ackman import BillAckmanAgent
from .cathie_wood import CathieWoodAgent
from .stanley_druckenmiller import StanleyDruckenmillerAgent

# Register agents with their configurations
AgentFactory.register_agent(
    WarrenBuffettAgent,
    AgentConfig(
        name="warren_buffett_agent",
        description="Analyzes stocks using Warren Buffett's investment principles"
    )
)

AgentFactory.register_agent(
    TechnicalAnalysisAgent,
    AgentConfig(
        name="technical_analyst_agent",
        description="Multi-strategy technical analysis system",
        weights={
            "trend": 0.25,
            "mean_reversion": 0.20,
            "momentum": 0.25,
            "volatility": 0.15,
            "stat_arb": 0.15,
        }
    )
)

AgentFactory.register_agent(
    CharlieMungerAgent,
    AgentConfig(
        name="charlie_munger_agent",
        description="Analyzes stocks using Charlie Munger's investment principles",
        parameters={
            "moat_weight": 0.35,
            "management_weight": 0.25,
            "predictability_weight": 0.25,
            "valuation_weight": 0.15,
            "bullish_threshold": 7.5,  # Munger has very high standards
            "bearish_threshold": 4.5
        }
    )
)

AgentFactory.register_agent(
    BenGrahamAgent,
    AgentConfig(
        name="ben_graham_agent",
        description="Analyzes stocks using Benjamin Graham's value investing principles",
        parameters={
            "earnings_weight": 0.33,
            "strength_weight": 0.33,
            "valuation_weight": 0.34,
            "bullish_threshold": 0.7,  # 70% of max score
            "bearish_threshold": 0.3,  # 30% of max score
            "current_ratio_min": 2.0,  # Graham's conservative criteria
            "debt_ratio_max": 0.5
        }
    )
)

AgentFactory.register_agent(
    BillAckmanAgent,
    AgentConfig(
        name="bill_ackman_agent",
        description="Analyzes stocks using Bill Ackman's investment principles",
        parameters={
            "quality_weight": 0.35,
            "balance_sheet_weight": 0.35,
            "valuation_weight": 0.30,
            "bullish_threshold": 0.7,
            "bearish_threshold": 0.3
        }
    )
)

AgentFactory.register_agent(
    CathieWoodAgent,
    AgentConfig(
        name="cathie_wood_agent",
        description="Analyzes stocks using Cathie Wood's disruptive innovation principles",
        parameters={
            "disruptive_weight": 0.35,
            "innovation_weight": 0.35,
            "valuation_weight": 0.30,
            "bullish_threshold": 0.7,
            "bearish_threshold": 0.3,
            "rd_intensity_threshold": 0.15  # High R&D spending threshold
        }
    )
)

AgentFactory.register_agent(
    StanleyDruckenmillerAgent,
    AgentConfig(
        name="stanley_druckenmiller_agent",
        description="Analyzes stocks using Stanley Druckenmiller's investment principles",
        parameters={
            "growth_momentum_weight": 0.35,
            "risk_reward_weight": 0.20,
            "valuation_weight": 0.20,
            "sentiment_weight": 0.15,
            "bullish_threshold": 7.5,  # High conviction threshold
            "bearish_threshold": 4.5   # Risk management threshold
        }
    )
)

# Export commonly used classes and functions
__all__ = [
    'BaseAgent',
    'AgentSignal',
    'AgentConfig',
    'AgentRegistry',
    'AgentFactory',
    'WarrenBuffettAgent',
    'TechnicalAnalysisAgent',
    'CharlieMungerAgent',
    'BenGrahamAgent',
    'BillAckmanAgent',
    'CathieWoodAgent',
    'StanleyDruckenmillerAgent'
]