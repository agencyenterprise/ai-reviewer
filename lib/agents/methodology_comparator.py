from typing import List, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from lib.agents.literature_review import ReferenceType
from lib.agents.methodology_extractor import ReproducibilityCategoryResponse
from lib.config.llm_models import gpt_5_4_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema


class SummaryAndOutput(BaseModel):
    summary: str = Field(
        description="A one to two sentence summary of the related section."
    )
    markdown_output: str = Field(
        description="Markdown formatted output of the full context of the related section."
    )


class ReferenceMinimal(BaseModel):
    title: str = Field(
        description="Canonical title for the reference exactly as it should appear in the article's bibliography"
    )
    type: ReferenceType = Field(
        description=f"Format classification for the reference. Possible values: {[e.value for e in ReferenceType]}"
    )
    link: str = Field(
        description="Stable URL or DOI that lets the author retrieve the reference quickly"
    )
    bibliography_info: str = Field(
        description="Bibliography entry formatted in the article's style; reuse the existing entry when the source is already in the bibliography"
    )


class MethodologyComparisonResponse(BaseModel):
    reproducibility: ReproducibilityCategoryResponse = Field(
        description="The class of reproducibility of the methodology."
    )
    extracted_methodology: SummaryAndOutput = Field(
        description="The extracted methodology of the paper."
    )
    field_methods_overview: SummaryAndOutput = Field(
        description="The overview of the field methods."
    )
    alignment_with_field_practice: SummaryAndOutput = Field(
        description="The alignment of the paper's methodology with the field methods."
    )
    methodological_rigor_and_risks: SummaryAndOutput = Field(
        description="The rigor and risks of the paper's methodology."
    )
    suggestions_for_improvements: SummaryAndOutput = Field(
        description="The suggestions for improvements to the paper's methodology."
    )
    references: List[ReferenceMinimal] = Field(
        default=[], description="List of sources cited from web search"
    )


class MethodologyComparisonAgent(LangChainAgent):
    name = "Methodology Comparison Agent"
    description = (
        "Compare an extracted paper methodology to typical methods used in the broader field, "
        "using web search to find field methods context, and return a structured text comparison."
    )
    model = gpt_5_4_model
    temperature = 0.3
    timeout = 600
    reasoning = {"effort": "low", "summary": "auto"}

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> MethodologyComparisonResponse:
        """
        Expected prompt_kwargs:
            {
                "extracted_methodology": str,  # output of MethodologyExtractorAgent
            }
        """
        content = (
            load_skill_prompt("methodology-comparison")
            + "\n\n## Inputs for this run\n\n"
            + "### Paper methodology (extracted per the methodology-extraction skill)\n\n"
            + prompt_kwargs["extracted_methodology"]
        )

        agent = create_agent(
            self.llm,
            [{"type": "web_search"}],
            context_schema=ContextSchema,
            response_format=MethodologyComparisonResponse,
        )

        result = await agent.ainvoke(  # type: ignore[call-overload]
            {"messages": [HumanMessage(content=content)]},
            config=config,
            context=self.context,
        )

        return result["structured_response"]
