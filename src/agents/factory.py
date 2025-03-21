from typing import Dict, Any
from .base_agent import BaseAgent
from .agent_config import AgentConfig
from .registry import AgentRegistry

class AgentFactory:
    """Factory for creating agent instances"""
    
    @staticmethod
    def create_agent(agent_type: str, **kwargs: Any) -> BaseAgent:
        """
        Create an agent instance with the given configuration.
        
        Args:
            agent_type: The type/name of the agent to create
            **kwargs: Additional configuration parameters
        
        Returns:
            An instance of the requested agent
        """
        return AgentRegistry.get_agent(agent_type, **kwargs)
    
    @staticmethod
    def list_available_agents() -> Dict[str, str]:
        """List all available agents and their descriptions"""
        return AgentRegistry.list_agents()
    
    @staticmethod
    def register_agent(agent_class: type, config: AgentConfig) -> None:
        """Register a new agent type"""
        AgentRegistry.register(agent_class, config)