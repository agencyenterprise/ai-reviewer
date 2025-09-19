"""
Agent Registry System

Provides a centralized way to register, discover, and access agents dynamically.
This eliminates hardcoded agent types throughout the system.
"""

import logging
from typing import Dict, List

from lib.models.agent import Agent

logger = logging.getLogger(__name__)


class AgentInfo:
    """Information about a registered agent"""
    def __init__(self, agent_type: str, agent: Agent, description: str):
        self.agent_type = agent_type
        self.agent = agent
        self.description = description
    
    def __repr__(self):
        return f"AgentInfo(type='{self.agent_type}', agent='{self.agent.name}')"


class AgentRegistry:
    """
    Central registry for all agents in the system.
    
    Provides dynamic agent discovery and eliminates hardcoded agent types.
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
    
    def register(self, agent_type: str, agent: Agent, description: str) -> None:
        """
        Register an agent with the registry
        
        Args:
            agent_type: String identifier for the agent (e.g., "claims", "citations")
            agent: The Agent instance
            description: Human-readable description
        """
        if agent_type in self._agents:
            logger.warning(f"Overriding existing agent registration for '{agent_type}'")
        
        agent_info = AgentInfo(
            agent_type=agent_type,
            agent=agent,
            description=description
        )
        
        self._agents[agent_type] = agent_info
        logger.info(f"Registered agent: {agent_type} -> {agent.name}")
    
    def get_agent(self, agent_type: str) -> Agent:
        """Get an agent by type"""
        if agent_type not in self._agents:
            raise ValueError(f"Unknown agent type: '{agent_type}'. Available: {list(self._agents.keys())}")
        return self._agents[agent_type].agent
    
    def has_agent(self, agent_type: str) -> bool:
        """Check if agent type is registered"""
        return agent_type in self._agents
    
    def get_supported_types(self) -> List[str]:
        """Get list of all registered agent types"""
        return list(self._agents.keys())
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get mapping of agent types to descriptions"""
        return {
            agent_type: info.description 
            for agent_type, info in self._agents.items()
        }
    
    def validate_agents(self, agent_types: List[str]) -> None:
        """Validate that all requested agent types are available"""
        if not agent_types:
            raise ValueError("agent_types cannot be empty")
        
        unsupported = [agent_type for agent_type in agent_types if not self.has_agent(agent_type)]
        if unsupported:
            supported_list = ", ".join(self._agents.keys())
            raise ValueError(
                f"Unsupported agent types: {unsupported}. "
                f"Supported: {supported_list}"
            )


# Global registry instance
agent_registry = AgentRegistry()


def initialize_default_agents():
    """Initialize the registry with default agents"""

    from lib.agents.claim_detector import claim_detector_agent
    from lib.agents.citation_detector import citation_detector_agent
    from lib.agents.claim_substantiator import claim_substantiator_agent
    
    agent_registry.register(
        agent_type="claims",
        agent=claim_detector_agent,
        description="Detect and extract claims from text chunks"
    )
    
    agent_registry.register(
        agent_type="citations", 
        agent=citation_detector_agent,
        description="Detect and extract citations from text chunks"
    )
    
    agent_registry.register(
        agent_type="substantiation",
        agent=claim_substantiator_agent,
        description="Substantiate claims against supporting documents"
    )
    
    logger.info("Initialized default agent registry")


initialize_default_agents()
