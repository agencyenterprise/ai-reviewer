import asyncio
import logging
from lib.agents.document_summarizer import (
    DocumentSummary,
    DocumentSummarizerResponse,
    document_summarizer_agent,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
)

logger = logging.getLogger(__name__)


async def summarize_supporting_documents(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info("summarize_supporting_documents: summarizing supporting documents")

    agents_to_run = state.config.agents_to_run
    if agents_to_run and "summarize_supporting_documents" not in agents_to_run:
        logger.info("summarize_supporting_documents: Skipping (not in agents_to_run)")
        return {}

    supporting_files = state.supporting_files
    if not supporting_files:
        logger.info("summarize_supporting_documents: No supporting files to summarize")
        return {}

    logger.info(
        "summarize_supporting_documents: Summarizing %d files in parallel",
        len(supporting_files),
    )

    async def summarize_file(index: int, file):
        logger.info("summarize_supporting_documents: Summarizing %s", file.file_name)
        response: DocumentSummarizerResponse = await document_summarizer_agent.apply(
            {
                "document": file.markdown,
            }
        )
        return index, response.summary

    # Run all summarizations in parallel
    results = await asyncio.gather(
        *[summarize_file(i, file) for i, file in enumerate(supporting_files)]
    )

    # Build dictionary from results
    summaries = {index: summary for index, summary in results}

    return {"supporting_documents_summaries": summaries}
