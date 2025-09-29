from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults


class WebSearchArgs(BaseModel):
    query: str = Field(description="Web search query string")
    max_results: int = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )


def _web_search(query: str, max_results: int) -> Dict[str, Any]:
    # Use LangChain's DuckDuckGoSearchResults tool (no API key required)
    tool = DuckDuckGoSearchResults(output_format="list")
    results = tool.invoke(query)
    # results is a list of dicts with keys: title, link, snippet
    items: List[Dict[str, Any]] = []
    for r in (results or [])[:max_results]:
        items.append(
            {
                "title": r.get("title"),
                "url": r.get("link"),
                "content": r.get("snippet"),
                "score": 0.0,
            }
        )
    return {"results": items, "provider": "duckduckgo"}


def build_all_tools():
    tools = {}

    def _web_search_tool(query: str, max_results: int = 5) -> Dict[str, Any]:
        return _web_search(query=query, max_results=max_results)

    search_tool = StructuredTool.from_function(
        name="web_search",
        description="""Search the web using DuckDuckGo Instant Answer API.
Use this to check on current facts, latest news, etc., whenever it is helpful for performing the task with high quality.""",
        args_schema=WebSearchArgs,
        func=_web_search_tool,
        return_direct=False,
    )

    openai_web_search_tool = {"type": "web_search_preview"}

    openai_code_interpreter_tool = {
        "type": "code_interpreter",
        "container": {"type": "auto"},
    }

    tools["web_search"] = search_tool
    tools["openai_web_search"] = openai_web_search_tool
    tools["openai_code_interpreter"] = openai_code_interpreter_tool
    return tools


def prepare_tools(tool_names: list[str]) -> List[StructuredTool]:
    """Build default tools available to all agents."""
    all_tools = build_all_tools()
    return [all_tools[tool_name] for tool_name in tool_names]
