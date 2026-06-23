# %%
from enum import Enum
from typing import List, Optional, cast

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from lib.agents.models import ReproducibilityCategory
from lib.config.llm_models import gpt_5_mini_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt


class ResultType(Enum):
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    TEXT = "text"
    ALGORITHM = "algorithm"
    OTHER = "other"


class ResultSection(BaseModel):

    title: str = Field(
        description="A chosen title for the section. Can be extracted from the text if it is present, but it should be no more than five words."
    )
    description: str = Field(description="The description of the result section.")
    result_type: ResultType = Field(description="The type of the result section.")
    location: str = Field(
        description="Description of the location of the result section in the document. This should be a description of the page number, figure number, table number, equation number, etc."
    )
    reproducibility: ReproducibilityCategory = Field(
        description="The class of reproducibility of the result section."
    )
    reproducibility_rationale: str = Field(
        description="The rationale for why you think the result section is reproducible or not. Describe what is needed to make this particular section reproducible."
    )


class ResultsListResponse(BaseModel):
    result_sections: List[ResultSection] = Field(
        description="The list of result sections."
    )


class ResultsExtractorAgent(LangChainAgent):
    name = "Results Extractor"
    description = "Read a research document and extract a detailed list of the results"
    model = gpt_5_mini_model
    temperature = 0.2
    output_schema = ResultsListResponse

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> ResultsListResponse:
        content = (
            load_skill_prompt("reproducibility-check")
            + "\n\n## The document to analyze\n\n"
            + prompt_kwargs["document"]
        )
        return cast(
            ResultsListResponse,
            await self.llm.ainvoke([HumanMessage(content=content)], config=config),
        )
