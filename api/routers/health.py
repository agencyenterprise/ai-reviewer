"""
Health check and system metadata endpoints
"""

from fastapi import APIRouter

from lib.agents.registry import agent_registry

router = APIRouter(tags=["health"])


@router.get("/api/health")
def read_health():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.get("/api/supported-agents")
async def get_supported_agents():
    """
    Get list of supported agent types for chunk re-evaluation.

    Returns:
        List of supported agent type strings with descriptions
    """
    return {
        "supported_agents": agent_registry.get_supported_types(),
        "agent_descriptions": agent_registry.get_agent_descriptions(),
    }
