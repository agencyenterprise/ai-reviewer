import asyncio
from pydantic import BaseModel, Field
from lib.services.file import File
from lib.agents.reference_extractor import (
    ReferenceExtractorResponse,
    reference_extractor_agent,
)
from lib.agents.reference_matcher import (
    ReferenceMatch,
    format_supporting_documents_prompt_section,
    reference_matcher_agent,
)


class ReferenceProcessorResult(BaseModel):
    references: list[str] = Field(description="A list of references found in the text")
    matches: list[ReferenceMatch] = Field(
        description="A list of reference matches found in the supporting documents"
    )


class ReferenceProcessor:
    def __init__(
        self,
        main_document: File,
        supporting_documents: list[File],
    ):
        self.main_document = main_document
        self.supporting_documents = supporting_documents

    async def process(self) -> ReferenceProcessorResult:
        full_document = await self.main_document.get_markdown()

        references_result: ReferenceExtractorResponse = (
            await reference_extractor_agent.apply(
                prompt_kwargs={
                    "full_document": full_document,
                }
            )
        )

        matches: list[ReferenceMatch] = []

        # Create tasks for parallel execution
        async def process_supporting_document(
            supporting_document: File,
        ) -> ReferenceMatch:
            return await reference_matcher_agent.apply(
                prompt_kwargs={
                    "references": "\n\n".join(references_result.references),
                    "supporting_document": await format_supporting_documents_prompt_section(
                        supporting_document
                    ),
                }
            )

        # Run all reference matching tasks in parallel
        match_tasks = [
            process_supporting_document(doc) for doc in self.supporting_documents
        ]
        matches = await asyncio.gather(*match_tasks)

        return ReferenceProcessorResult(
            references=references_result.references,
            matches=matches,
        )
