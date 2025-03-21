from typing import Dict, Type, Any
from .base_agent import BaseAgent
from .agent_config import AgentConfig

class AgentRegistry:
    """Registry for managing all available agents"""
    
    _agents: Dict[str, Type[BaseAgent]] = {}
    _configs: Dict[str, AgentConfig] = {}
    
    @classmethod
    def register(cls, agent_class: Type[BaseAgent], config: AgentConfig) -> None:
        """Register a new agent with its configuration"""
        cls._agents[config.name] = agent_class
        cls._configs[config.name] = config
    
    @classmethod
    def get_agent(cls, name: str, **kwargs: Any) -> BaseAgent:
        """Get an instance of an agent by name with optional config overrides"""
        if name not in cls._agents:
            raise KeyError(f"Agent '{name}' not found in registry")
        
        agent_class = cls._agents[name]
        config = cls._configs[name]
        
        # Override config with kwargs if provided
        if kwargs:
            config = AgentConfig(**{**config.dict(), **kwargs})
            
        return agent_class(name=config.name, description=config.description, config=config.parameters)
    
    @classmethod
    def list_agents(cls) -> Dict[str, str]:
        """List all registered agents and their descriptions"""
        return {name: cls._configs[name].description 
                for name in cls._agents.keys()}
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered agents"""
        cls._agents.clear()
        cls._configs.clear()