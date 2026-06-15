"""Reviewer 2 agent — rigorous peer review using deep agent with file tools."""

from typing import Optional

from deepagents import create_deep_agent
from langchain.agents.structured_output import AutoStrategy
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from lib.config.llm_models import gpt_5_4_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema


class Reviewer2Output(BaseModel):
    peer_review_markdown: str = Field(
        description="The peer review document in markdown (Sections 1-4)"
    )
    rebuttal_markdown: str = Field(description="The rebuttal document in markdown")


class Reviewer2Agent(LangChainAgent):
    name = "Reviewer 2"
    description = "Produce a rigorous peer review and rebuttal of a research document"
    model = gpt_5_4_model
    temperature = 0.3
    reasoning = {"effort": "medium", "summary": "auto"}

    async def ainvoke(
        self, prompt_kwargs: dict, config: Optional[RunnableConfig] = None
    ) -> Reviewer2Output:
        document_markdown = prompt_kwargs["document_markdown"]

        deep_agent = create_deep_agent(
            model=self.llm,
            context_schema=ContextSchema,
            response_format=AutoStrategy(Reviewer2Output),
        )

        result = await deep_agent.ainvoke(
            {
                "messages": [
                    SystemMessage(content=load_skill_prompt("reviewer-2")),
                    HumanMessage(
                        content=(
                            "Here is the document to review:\n\n" f"{document_markdown}"
                        )
                    ),
                ],
            },
            config={"recursion_limit": 100, **(config or {})},
        )

        return result["structured_response"]
