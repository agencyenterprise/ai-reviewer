from __future__ import annotations

from typing import Any, List, Sequence

from langchain.agents import AgentExecutor, create_react_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_core.messages import BaseMessage, SystemMessage
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel


# We keep a single Langfuse handler consistent with the rest of the codebase
langfuse_handler = CallbackHandler()


def _format_default_tools_preamble(
    mandatory_tools: Sequence[str], available_tools: Sequence[str]
) -> str:
    tool_list = ", ".join(sorted(available_tools)) if available_tools else "(none)"
    pre = f"""You can use tools to reason step-by-step before answering.
Available tools: {tool_list}.
"""
    if mandatory_tools:
        pre += f"""You MUST use each of the following tools at least once before producing the final answer: {', '.join(sorted(mandatory_tools))}."""
    return pre


def _build_prompt_with_tools_preamble(
    base_messages: Any, mandatory_tools: Sequence[str], available_tools: Sequence[str]
) -> List[Any]:
    preamble = _format_default_tools_preamble(mandatory_tools, available_tools)
    return [HumanMessage(content=preamble), *base_messages]


def _collect_tool_use_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Extract tool use messages from a list of messages"""
    tool_use_messages = [
        message for message in messages if "function_call" in message.additional_kwargs
    ]
    return tool_use_messages


def _build_retry_messages(
    base_messages: Any, missing_tools: Sequence[str]
) -> List[Any]:
    retry = HumanMessage(
        content=f"""You did not use the mandatory tool(s): {', '.join(sorted(missing_tools))}. Use them now."""
    )
    return [*base_messages, retry]


def _filter_tools(
    default_tools: Sequence[StructuredTool], disallowed: Sequence[str]
) -> List[StructuredTool]:
    disallowed_set = set(disallowed or [])
    return [t for t in default_tools if t.name not in disallowed_set]


def _ensure_structured_output(output: Any, schema: type[BaseModel]) -> BaseModel:
    """Validate or coerce the output into the expected Pydantic model.

    If the output is already a dict, validate directly. If it's a string, let the
    schema try to parse JSON. As a last resort, raise and let caller decide fallback.
    """
    if isinstance(output, dict):
        return schema.model_validate(output)
    if isinstance(output, str):
        return schema.model_validate_json(output)
    # Let caller decide fallback (e.g., call structured LLM directly)
    raise ValueError("Agent did not return a structured result.")


async def run_agent(
    *,
    executor: AgentExecutor,
    messages: Any,
    mandatory_tools: Sequence[str] | None,
) -> Any:
    result = await executor.ainvoke({"messages": messages})

    used_tool_names = set(
        [
            message.additional_kwargs.get("function_call").get("name")
            for message in _collect_tool_use_messages(result.get("messages"))
        ]
    )
    missing = set(mandatory_tools or []) - used_tool_names

    if missing:
        retry_messages = _build_retry_messages(messages, sorted(missing))
        result = await executor.ainvoke({"messages": retry_messages})

    return result.get("messages", [])


def run_agent_sync(
    *,
    executor: AgentExecutor,
    messages: Any,
    mandatory_tools: Sequence[str] | None,
) -> Any:
    result = executor.invoke({"messages": messages})

    used_tool_names = set(
        [
            message.additional_kwargs.get("function_call").get("name")
            for message in _collect_tool_use_messages(result.get("messages"))
        ]
    )
    missing = set(mandatory_tools or []) - used_tool_names

    if missing:
        retry_messages = _build_retry_messages(result.get("messages"), sorted(missing))
        result = executor.invoke({"messages": retry_messages})

    return result.get("messages", [])
