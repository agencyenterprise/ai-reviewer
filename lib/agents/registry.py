"""
Agent Registry System

Provides a centralized way to register, discover, and access agents dynamically.
This eliminates hardcoded agent types throughout the system.
"""

import logging
from typing import Dict, List, Optional, Type, Any, Callable
from abc import ABC, abstractmethod

from lib.models.agent import Agent
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState

logger = logging.getLogger(__name__)


class AgentInfo:
    """Information about a registered agent"""
    def __init__(
        self,
        agent_type: str,
        agent: Agent,
        description: str,
        dependencies: List[str] = None,
        node_function: Optional[Callable] = None
    ):
        self.agent_type = agent_type
        self.agent = agent
        self.description = description
        self.dependencies = dependencies or []
        self.node_function = node_function
    
    def __repr__(self):
        return f"AgentInfo(type='{self.agent_type}', agent='{self.agent.name}')"


class AgentRegistry:
    """
    Central registry for all agents in the system.
    
    Provides dynamic agent discovery and eliminates hardcoded agent types.
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._initialized = False
    
    def register(
        self,
        agent_type: str,
        agent: Agent,
        description: str,
        dependencies: List[str] = None,
        node_function: Optional[Callable] = None
    ) -> None:
        """
        Register an agent with the registry
        
        Args:
            agent_type: String identifier for the agent (e.g., "claims", "citations")
            agent: The Agent instance
            description: Human-readable description
            dependencies: List of agent types this agent depends on
            node_function: Optional custom node function for LangGraph workflow
        """
        if agent_type in self._agents:
            logger.warning(f"Overriding existing agent registration for '{agent_type}'")
        
        agent_info = AgentInfo(
            agent_type=agent_type,
            agent=agent,
            description=description,
            dependencies=dependencies,
            node_function=node_function
        )
        
        self._agents[agent_type] = agent_info
        logger.info(f"Registered agent: {agent_type} -> {agent.name}")
    
    def get_agent(self, agent_type: str) -> Agent:
        """Get an agent by type"""
        if agent_type not in self._agents:
            raise ValueError(f"Unknown agent type: '{agent_type}'. Available: {list(self._agents.keys())}")
        return self._agents[agent_type].agent
    
    def get_agent_info(self, agent_type: str) -> AgentInfo:
        """Get full agent info by type"""
        if agent_type not in self._agents:
            raise ValueError(f"Unknown agent type: '{agent_type}'. Available: {list(self._agents.keys())}")
        return self._agents[agent_type]
    
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
        
        unsupported = set(agent_types) - set(self._agents.keys())
        if unsupported:
            supported_list = ", ".join(self._agents.keys())
            raise ValueError(
                f"Unsupported agent types: {unsupported}. "
                f"Supported: {supported_list}"
            )
    
    def get_execution_order(self, agent_types: List[str]) -> List[str]:
        """
        Get agent types in dependency-respecting execution order
        
        Returns agent types sorted so dependencies execute before dependents.
        """
        self.validate_agents(agent_types)
        
        # Simple topological sort for dependencies
        ordered = []
        remaining = set(agent_types)
        
        while remaining:
            # Find agents with no unresolved dependencies in the remaining set
            ready = []
            for agent_type in remaining:
                info = self._agents[agent_type]
                unmet_deps = set(info.dependencies) & remaining
                if not unmet_deps:
                    ready.append(agent_type)
            
            if not ready:
                # Circular dependency or invalid state
                logger.warning(f"Circular dependency detected among: {remaining}")
                # Add remaining in arbitrary order
                ready = list(remaining)
            
            # Add ready agents to order and remove from remaining
            for agent_type in ready:
                ordered.append(agent_type)
                remaining.remove(agent_type)
        
        return ordered
    
    def create_node_function(self, agent_type: str) -> Callable:
        """
        Create a LangGraph node function for the given agent type
        
        Returns a function that can be used as a node in LangGraph workflows.
        """
        # Force refresh to pick up any updated agent definitions
        if agent_type == "substantiation":
            # Check if we have the updated substantiation agent with correct input_variables
            from lib.agents.claim_substantiator import claim_substantiator_agent
            current_agent = self._agents.get("substantiation")
            if current_agent and current_agent.agent != claim_substantiator_agent:
                # Re-register with updated agent
                self.register(
                    agent_type="substantiation",
                    agent=claim_substantiator_agent,
                    description="Substantiate claims against supporting documents",
                    dependencies=["claims"]
                )
        
        agent_info = self.get_agent_info(agent_type)
        
        # Use custom node function if provided
        if agent_info.node_function:
            return agent_info.node_function
        
        # Create generic node function
        async def generic_node(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
            from lib.services.document_processor import DocumentProcessor
            
            logger.info(f"{agent_type}_node: processing chunk {state['chunk_index']}")
            
            # Apply the agent to the chunk
            processor = DocumentProcessor(state["file"])
            
            # Prepare prompt kwargs based on agent type and available state
            prompt_kwargs = self._prepare_prompt_kwargs(agent_type, state)
            
            try:
                result_data = await processor.apply_agent_to_chunk(
                    agent=agent_info.agent,
                    chunk=state["chunk"],
                    prompt_kwargs=prompt_kwargs
                )
                
                # Store result in appropriate field
                result = state["result"]
                if agent_type == "claims":
                    result.claims = result_data
                elif agent_type == "citations":
                    result.citations = result_data
                elif agent_type == "substantiation":
                    # Handle substantiation specially as it processes individual claims
                    # Early exit if no claims exist at all
                    if not result.claims:
                        logger.info(f"No claims object found for substantiation in chunk {state['chunk_index']}")
                        result.substantiations = []
                    elif not hasattr(result.claims, 'claims'):
                        logger.info(f"Claims object has no 'claims' attribute in chunk {state['chunk_index']}")
                        result.substantiations = []
                    elif not result.claims.claims:
                        logger.info(f"Empty claims list found for substantiation in chunk {state['chunk_index']}")
                        result.substantiations = []
                    else:
                        substantiations = []
                        
                        # Filter claims that need substantiation
                        claims_to_substantiate = []
                        for claim in result.claims.claims:
                            # Check if claim needs substantiation - handle both camelCase and snake_case
                            needs_substantiation = (
                                getattr(claim, 'needs_substantiation', False) or 
                                getattr(claim, 'needsSubstantiation', False)
                            )
                            print(f"REGISTRY CLAIM DEBUG: Claim has needs_substantiation={getattr(claim, 'needs_substantiation', 'NOT_SET')}")
                            print(f"REGISTRY CLAIM DEBUG: Claim has needsSubstantiation={getattr(claim, 'needsSubstantiation', 'NOT_SET')}")
                            print(f"REGISTRY CLAIM DEBUG: Final needs_substantiation={needs_substantiation}")
                            if needs_substantiation:
                                claims_to_substantiate.append(claim)
                        
                        if not claims_to_substantiate:
                            logger.info(f"No claims need substantiation in chunk {state['chunk_index']}")
                            result.substantiations = []
                        else:
                            logger.info(f"Substantiating {len(claims_to_substantiate)} claims in chunk {state['chunk_index']}")
                            
                            for claim_index, claim in enumerate(claims_to_substantiate):
                                # Extract claim text outside try block for error logging
                                if hasattr(claim, 'claim'):
                                    claim_text = claim.claim
                                elif hasattr(claim, 'text'):
                                    claim_text = claim.text  
                                else:
                                    claim_text = str(claim)
                                
                                print(f"REGISTRY DEBUG: Processing claim {claim_index}: '{claim_text[:50]}...'")
                                print(f"REGISTRY DEBUG: Initial prompt_kwargs: {prompt_kwargs}")
                                
                                try:
                                    claim_kwargs = prompt_kwargs.copy()
                                    claim_kwargs.update({
                                        "claim": claim_text,
                                        "claim_index": claim_index
                                    })
                                    
                                    # Explicit debug to see what we're passing
                                    print(f"REGISTRY FINAL DEBUG: About to call processor.apply_agent_to_chunk")
                                    print(f"REGISTRY FINAL DEBUG: claim_kwargs = {claim_kwargs}")
                                    print(f"REGISTRY FINAL DEBUG: claim_kwargs keys = {list(claim_kwargs.keys())}")
                                    
                                    substantiation = await processor.apply_agent_to_chunk(
                                        agent=agent_info.agent,
                                        chunk=state["chunk"],
                                        prompt_kwargs=claim_kwargs
                                    )
                                    
                                    if substantiation:
                                        # Convert ClaimSubstantiationResult to ClaimSubstantiationResultWithClaimIndex
                                        from lib.agents.claim_substantiator import ClaimSubstantiationResultWithClaimIndex
                                        
                                        if isinstance(substantiation, list):
                                            for sub in substantiation:
                                                substantiation_with_index = ClaimSubstantiationResultWithClaimIndex(
                                                    **sub.model_dump(),
                                                    chunk_index=state["chunk_index"],
                                                    claim_index=claim_index
                                                )
                                                substantiations.append(substantiation_with_index)
                                        else:
                                            substantiation_with_index = ClaimSubstantiationResultWithClaimIndex(
                                                **substantiation.model_dump(),
                                                chunk_index=state["chunk_index"],
                                                claim_index=claim_index
                                            )
                                            substantiations.append(substantiation_with_index)
                                            
                                except Exception as e:
                                    logger.error(f"Failed to substantiate claim {claim_index} '{claim_text[:50]}': {e}")
                                    import traceback
                                    logger.error(f"Substantiation error traceback: {traceback.format_exc()}")
                                    continue
                            
                            result.substantiations = substantiations
                    
                else:
                    # For other agent types, store in a generic way
                    setattr(result, agent_type, result_data)
                
                count = self._get_result_count(agent_type, result_data)
                logger.info(f"Agent '{agent_type}' found {count} items in chunk {state['chunk_index']}")
                
                return {"result": result}
                
            except Exception as e:
                logger.error(f"Agent '{agent_type}' failed on chunk {state['chunk_index']}: {e}")
                raise
        
        return generic_node
    
    def _prepare_prompt_kwargs(self, agent_type: str, state: ClaimSubstantiatorState) -> Dict[str, Any]:
        """Prepare prompt kwargs based on agent type and state"""
        prompt_kwargs = {}
        
        if agent_type == "citations":
            # Citations need bibliography context
            bibliography_text = ""
            references = state.get("references", [])
            if references:
                bibliography_text = "\n".join([
                    f"{i+1}. {ref.text if hasattr(ref, 'text') else str(ref)}" 
                    for i, ref in enumerate(references)
                ])
            else:
                bibliography_text = "No bibliography entries found."
            prompt_kwargs["bibliography"] = bibliography_text
            
        elif agent_type == "substantiation":
            # Substantiation needs cited_references context
            supporting_files = state.get("supporting_files", [])
            if supporting_files:
                cited_references = "\n\n---\n\n".join([
                    f"## Supporting Document: {doc.file_name}\n{doc.markdown}"
                    for doc in supporting_files
                ])
            else:
                cited_references = "No supporting documents provided for substantiation."
            prompt_kwargs["cited_references"] = cited_references
            
            # CRITICAL FIX: Always add a claim parameter for substantiation
            # This handles the case where individual claim processing isn't working
            result = state.get("result")
            if result and result.claims and hasattr(result.claims, 'claims') and result.claims.claims:
                # Find first claim that needs substantiation
                first_claim = None
                for claim in result.claims.claims:
                    needs_substantiation = (
                        getattr(claim, 'needs_substantiation', False) or 
                        getattr(claim, 'needsSubstantiation', False)
                    )
                    if needs_substantiation:
                        if hasattr(claim, 'claim'):
                            first_claim = claim.claim
                        elif hasattr(claim, 'text'):
                            first_claim = claim.text
                        else:
                            first_claim = str(claim)
                        break
                
                if first_claim:
                    prompt_kwargs["claim"] = first_claim
                    print(f"REGISTRY FIX: Added claim parameter: '{first_claim[:50]}...'")
                else:
                    prompt_kwargs["claim"] = "No claims found that need substantiation"
                    print(f"REGISTRY FIX: No claims need substantiation, using default")
            else:
                prompt_kwargs["claim"] = "No claims available for substantiation"
                print(f"REGISTRY FIX: No claims found, using default")
        
        return prompt_kwargs
    
    def _get_result_count(self, agent_type: str, result_data: Any) -> int:
        """Get count of results for logging"""
        if hasattr(result_data, 'claims'):
            return len(result_data.claims)
        elif hasattr(result_data, 'citations'):
            return len(result_data.citations)
        elif isinstance(result_data, list):
            return len(result_data)
        else:
            return 1 if result_data else 0


# Global registry instance
agent_registry = AgentRegistry()


def initialize_default_agents():
    """Initialize the registry with default agents"""
    if agent_registry._initialized:
        return
        
    # Import agents
    from lib.agents.claim_detector import claim_detector_agent
    from lib.agents.toulmin_claim_detector import toulmin_claim_detector_agent  
    from lib.agents.citation_detector import citation_detector_agent
    from lib.agents.claim_substantiator import claim_substantiator_agent
    
    # Register agents with dependencies
    agent_registry.register(
        agent_type="claims",
        agent=claim_detector_agent,
        description="Detect and extract claims from text chunks",
        dependencies=[]
    )
    
    agent_registry.register(
        agent_type="citations", 
        agent=citation_detector_agent,
        description="Detect and extract citations from text chunks",
        dependencies=[]
    )
    
    agent_registry.register(
        agent_type="substantiation",
        agent=claim_substantiator_agent,
        description="Substantiate claims against supporting documents",
        dependencies=["claims"]  # Substantiation depends on having claims
    )
    
    agent_registry._initialized = True
    logger.info("Initialized default agent registry")


# Initialize on import
initialize_default_agents()

# Force re-initialization to pick up any agent changes
def force_reinitialize_agents():
    """Force re-initialization of agents (useful after agent updates)"""
    global agent_registry
    agent_registry._initialized = False
    agent_registry._agents.clear()
    initialize_default_agents()

# Force re-initialization to pick up the updated agent definitions
force_reinitialize_agents()
