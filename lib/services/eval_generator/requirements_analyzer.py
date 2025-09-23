"""Analyzer for determining file requirements based on selected agents."""

from typing import List, Set, Dict, Any, Union
from pydantic import BaseModel


class RequirementsAnalyzer:
    """Analyzes requirements for different agent combinations."""
    
    # Agent file requirements mapping
    AGENT_REQUIREMENTS = {
        "claims": {"main_document"},
        "citations": {"main_document", "bibliography"},
        "references": {"main_document", "supporting_documents"},
        "substantiation": {"main_document", "supporting_documents", "cited_references"}
    }
    
    @classmethod
    def determine_required_files(cls, selected_agents: List[str]) -> Set[str]:
        """Determine which files are needed based on selected agents."""
        required = {"main_document"}  # Always need main document
        
        # Agent requirements:
        # - claims: main_document + chunk
        # - citations: main_document + bibliography + chunk  
        # - references: main_document + supporting_documents
        # - substantiation: main_document + chunk + cited_references (from supporting docs)
        
        if any(agent in selected_agents for agent in ["references", "substantiation"]):
            required.add("supporting_documents")
        
        return required
    
    @classmethod
    def has_valid_items(cls, data: Union[BaseModel, Dict[str, Any], None], key: str) -> bool:
        """Check if data has valid items for the specified key."""
        if not data:
            return False
            
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
    def should_generate_agent_tests(cls, agent_id: str, selected_agents: List[str], data: Union[BaseModel, Dict[str, Any], None]) -> bool:
        """Determine if tests should be generated for a specific agent."""
        if agent_id not in selected_agents:
            return False
        
        # Check if the data contains relevant information for this agent
        if agent_id == "citations":
            return cls.has_valid_items(data, "citations")
        elif agent_id == "claims":
            return cls.has_valid_items(data, "claims")
        elif agent_id == "references":
            return cls.has_valid_items(data, "references")
        elif agent_id == "substantiation":
            if isinstance(data, BaseModel):
                substantiations = getattr(data, "substantiations", None)
                return bool(substantiations and len(substantiations) > 0)
            elif isinstance(data, dict):
                return bool(data.get("substantiations"))
        
        return False
