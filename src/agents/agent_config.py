from pydantic import BaseModel
from typing import Dict, Any, Optional

class AgentConfig(BaseModel):
    """Configuration settings for agents"""
    name: str
    description: str
    weights: Optional[Dict[str, float]] = None  # For weighted strategies
    parameters: Dict[str, Any] = {}  # Agent-specific parameters
    
    class Config:
        arbitrary_types_allowed = True
        
    @classmethod
    def create_default(cls, name: str, description: str = "") -> "AgentConfig":
        """Create a default configuration for an agent"""
        return cls(
            name=name,
            description=description,
            parameters={}
        )