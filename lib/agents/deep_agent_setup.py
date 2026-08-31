"""Shared construction for the deep agents that review a document directly.

Two agents work on a Word document without a project or a database behind them: the
one answering a comment from the add-in, and the one answering a question from Teams.
They differ in their prompts, their tools and what they return, but they are built
the same way -- same model construction, same rate limiter, same skills mounted into
the same virtual filesystem.

That construction lives here rather than in either agent. It was in ``word_agent``
first and the Teams agent imported it from there, which had the dependency the wrong
way round: answering a question in a chat has nothing to do with Word comments, and
one agent should not be the other's utility library.

``/main.md`` is where the document is mounted, and that is a codebase-wide contract
rather than a local choice: ``FileArtifactsService.get_deepagent_backend_files``, the
workflow agents and ``skills/issues/SKILL.md`` all read it, and the skills' line
numbers are *defined* as line numbers within it.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from deepagents.backends.utils import create_file_data
from langchain.chat_models import BaseChatModel, init_chat_model

from lib.config.env import get_model_api_key
from lib.config.llm_models import LLMModel, gpt_5_6_terra_model
from lib.config.rate_limiter import get_rate_limiter, hash_api_key
from lib.models.agent import ReasoningDict
from lib.skills import strip_interactive_only

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parents[2]
SKILLS_DIR = PROJECT_ROOT / "skills"

DEFAULT_MODEL = gpt_5_6_terra_model
RECURSION_LIMIT = 60
REQUEST_TIMEOUT = 120

# Medium effort because reviewing a document means reading around it and weighing a
# claim against a source, which is more than a lookup. The summary is surfaced in
# Langfuse, so the reasoning behind an answer can be inspected when one looks wrong.
REASONING: ReasoningDict = {"effort": "medium", "summary": "auto"}


def number_paragraphs(paragraphs: list[str]) -> str:
    """The document as the agent sees it, each paragraph prefixed with its index.

    Numbering is what lets an annotation point at a place instead of describing it.
    The indices come from the caller's own paragraph list, so they are an exact
    handle back to the paragraph rather than something to search for. The same idea
    as the sentinels the docx export injects, which exist to avoid fuzzy matching.
    """

    return "\n\n".join(f"[{index}] {text}" for index, text in enumerate(paragraphs))


def build_skill_files() -> dict[str, Any]:
    """Mount the project's skills into the agent's filesystem.

    Separate from the document because skills can only be mounted before the run:
    the skills middleware reads them once and skips thereafter, so an agent that
    opens its document mid-run still needs these up front.
    """

    files: dict[str, Any] = {}
    for path in sorted(SKILLS_DIR.rglob("*")):
        if path.is_file():
            virtual_path = "/" + path.relative_to(PROJECT_ROOT).as_posix()
            # Interactive-only sections (e.g. asking the user for web-search
            # consent) address an agent driven by a user; a backend run has its
            # consent already and nobody to ask.
            files[virtual_path] = create_file_data(
                strip_interactive_only(path.read_text(encoding="utf-8"))
            )
    return files


def build_agent_files(document_text: str) -> dict[str, Any]:
    """Mount the document and the project's skills into the agent's filesystem.

    Mirrors ``FileArtifactsService.get_deepagent_backend_files`` without needing a
    project or a database.
    """

    return {"/main.md": create_file_data(document_text), **build_skill_files()}


def build_llm(model: LLMModel, api_key: Optional[str]) -> BaseChatModel:
    """Same construction LangChainAgent uses, including the shared rate limiter."""

    resolved = api_key
    if resolved is None and model.provider == "openai":
        resolved = get_model_api_key(model.name)

    kwargs: dict[str, Any] = {
        "model": model.model_name,
        "temperature": 0.0,
        "timeout": REQUEST_TIMEOUT,
        "max_retries": 4,
        "rate_limiter": get_rate_limiter(hash_api_key(resolved or "default")),
        "reasoning": REASONING,
    }
    if resolved:
        kwargs["api_key"] = resolved
    return init_chat_model(**kwargs)


def tool_names(messages: list[Any]) -> list[str]:
    """Which tools a run actually called, for the caller's own reporting."""

    used: list[str] = []
    for message in messages:
        for call in getattr(message, "tool_calls", None) or []:
            name = call.get("name") if isinstance(call, dict) else None
            if name:
                used.append(name)
    return sorted(set(used))
