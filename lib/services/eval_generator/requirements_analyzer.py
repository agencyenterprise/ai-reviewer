"""Analyzer for determining file requirements based on selected agents."""

from typing import List, Dict, Any, Union
from pydantic import BaseModel


class RequirementsAnalyzer:
    """Analyzes requirements for different agent combinations."""
    
    
    @classmethod
    def has_valid_items(cls, data: Union[BaseModel, Dict[str, Any], list, None], key: str) -> bool:
        """Check if data has valid items for the specified key."""
        if not data:
            return False
        
        # Handle direct list data (for substantiation and references)
        if isinstance(data, list):
            return len(data) > 0
            
        if isinstance(data, BaseModel):
            attr_value = getattr(data, key, None)
            return bool(attr_value and (
                (isinstance(attr_value, list) and len(attr_value) > 0) or
                (not isinstance(attr_value, list) and attr_value)
            ))
        
        if isinstance(data, dict):
            return bool(data.get(key))
            
        return False
    
    @classmethod
    def should_generate_agent_tests(cls, agent_id: str, selected_agents: List[str], data: Union[BaseModel, Dict[str, Any], list, None]) -> bool:
        """Determine if tests should be generated for a specific agent."""
        if agent_id not in selected_agents:
            return False
        
        # For all agent types, use the unified has_valid_items method
        # Note: for substantiation and references, data is passed as direct list
        # For citations and claims, data contains the key
        return cls.has_valid_items(data, agent_id)
