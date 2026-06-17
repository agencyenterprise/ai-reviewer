"""Reference extractor v2 agent using document search tool."""

from typing import List, Optional

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.state import RunnableConfig
from pydantic import BaseModel, ConfigDict, Field

from lib.agents.tools.read_main_document import read_document
from lib.agents.tools.search_main_document import search_document
from lib.config.llm_models import gpt_5_4_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema


class ExtractedReferenceWithLines(BaseModel):
    """A single reference with its location in the document."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(description="The complete bibliographic reference text")
    start_line: int = Field(
        description="1-indexed starting line number where this reference begins"
    )
    end_line: int = Field(
        description="1-indexed ending line number where this reference ends"
    )


class ReferenceExtractorV2Output(BaseModel):
    """Output from the reference extractor agent."""

    model_config = ConfigDict(extra="forbid")

    reasoning: str = Field(
        description="Step-by-step reasoning describing how references were found and extracted"
    )
    references: List[ExtractedReferenceWithLines] = Field(
        description="List of extracted bibliographic references with their line locations"
    )


_SYSTEM_PROMPT = load_skill_prompt("reference-extraction")

_USER_MESSAGE = "Please extract all bibliographic references from the document."


class ReferenceExtractorV2Agent(LangChainAgent):
    """Agent that extracts references using document search tool."""

    name = "Reference Extractor v2"
    description = "Extract bibliographic references using intelligent document search"
    model = gpt_5_4_model
    temperature = 0.0
    reasoning = {"effort": "low", "summary": "auto"}

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> tuple[ReferenceExtractorV2Output, list[BaseMessage]]:
        agent = create_agent(
            self.llm,
            [search_document, read_document],
            context_schema=ContextSchema,
            response_format=ReferenceExtractorV2Output,
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=_USER_MESSAGE),
                ]
            },
            config={"recursion_limit": 50, **(config or {})},
            context=self.context,
        )

        return result["structured_response"], result["messages"]
