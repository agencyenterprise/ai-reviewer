# %%
from enum import Enum
from typing import Optional, cast

from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel, Field

from lib.config.env import config
from lib.config.llm_models import gpt_5_mini_model
from lib.agents.models import ReproducibilityCategory
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema


class ReproducibilityCategoryResponse(BaseModel):
    class_value: ReproducibilityCategory = Field(
        description=f"The class of reproducibility of the methodology. Possible values: {[e.value for e in ReproducibilityCategory]}"
    )
    rationale: str = Field(
        description="The rationale for why you think the methodology is reproducible or not."
    )


class MethodologyExtractionResponse(BaseModel):
    reproducibility: ReproducibilityCategoryResponse = Field(
        description="The class of reproducibility of the methodology."
    )
    methodology: str = Field(
        description=(
            "A concise but detailed markdown formatted description of the methodology used in the document to obtain its results. This should be comprehensive enough that a technically "
            "literate researcher could reproduce the work. Include step-by-step procedures, "
            "exact parameters, software versions, data preprocessing details, and all "
            "implementation choices that materially affect results. Focus on procedures, "
            "data, models, experimental setups, and analysis workflows, avoiding background "
            "or interpretation."
        )
    )


class MethodologyExtractorAgent(LangChainAgent):
    name = "Methodology Extractor"
    description = (
        "Read a research document and extract a detailed, reproducible description of "
        "the methodology used to obtain the results, with sufficient detail for external "
        "researchers to reproduce the work."
    )
    model = gpt_5_mini_model
    temperature = 0.2
    output_schema = MethodologyExtractionResponse

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> MethodologyExtractionResponse:
        content = (
            load_skill_prompt("methodology-extraction")
            + "\n\n## The document to analyze\n\n"
            + prompt_kwargs["document"]
        )
        return cast(
            MethodologyExtractionResponse,
            await self.llm.ainvoke([HumanMessage(content=content)], config=config),
        )


# Test script - can be run directly or imported
if __name__ == "__main__":
    import asyncio
    import os
    import sys
    from pathlib import Path

    from lib.services.converters.base import convert_to_markdown

    # Set the file path here, or pass it as a command line argument
    FILE_PATH = "tests/data/RAND_RRA3307-1.pdf"  # e.g., "tests/data/sample_document.md"
    # FILE_PATH = "tests/data/case_1/main_document.md"
    FILE_PATH = "rand-personal/sample_papers_rand/RAND_RRA3034-1.pdf"
    FILE_PATH = "rand-personal/Smaldino_McElreath_(2016).pdf"

    async def test_methodology_extractor(file_path: str):
        """Test the methodology extractor agent with a given file."""
        # Resolve the file path (handle relative paths from project root)
        if not os.path.isabs(file_path):
            # Assume relative to project root
            project_root = Path(__file__).parent.parent.parent
            file_path = str(project_root / file_path)

        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return

        print(f"Reading file: {file_path}")
        print("-" * 80)

        # Convert file to markdown
        markdown_content = await convert_to_markdown(file_path)

        print(f"Document length: {len(markdown_content)} characters")
        print("Running methodology extractor agent...")
        print("-" * 80)

        # Initialize context
        from lib.services.file_artifacts_service.mock import MockFileArtifactsService

        context = ContextSchema(
            openai_api_key=config.OPENAI_API_KEY,
            vector_store=None,
            project_id="dev",
            file_artifacts_service=MockFileArtifactsService(),
        )

        # Run the agent
        methodology_extractor_agent = MethodologyExtractorAgent(context)
        response = await methodology_extractor_agent.ainvoke(
            {"document": markdown_content}
        )

        # Print the reproducibility results
        print("\n" + "=" * 80)
        print("REPRODUCIBILITY ASSESSMENT")
        print("=" * 80)
        print(f"Category: {response.reproducibility.class_value.value}")
        print(f"\nRationale:\n{response.reproducibility.rationale}")
        print("\n" + "=" * 80)

        # Print the methodology results
        print("\n" + "=" * 80)
        print("EXTRACTED METHODOLOGY")
        print("=" * 80)
        print(response.methodology)
        print("\n" + "=" * 80)

    # Get file path from command line or use the FILE_PATH variable
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    elif FILE_PATH:
        file_path = FILE_PATH
    else:
        print("Usage: python methodology_extractor_agent.py <file_path>")
        print("   or: Set FILE_PATH variable in the script")
        sys.exit(1)

    # Run the test
    asyncio.run(test_methodology_extractor(file_path))
