# %%
import logging

from lib.agents.claim_categorizer import (
    claim_categorizer_agent,
    ClaimCategorizationResponse,
)
from lib.agents.formatting_utils import (
    format_audience_context,
    format_domain_context,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.claim_substantiation.state import SubstantiationWorkflowConfig
from lib.workflows.chunk_iterator import iterate_chunks

import asyncio
import argparse
from datetime import datetime
from lib.services.file import FileDocument
from lib.agents.claim_extractor import Claim, ClaimResponse
from rich.console import Console
from rich.panel import Panel
import nest_asyncio

logger = logging.getLogger(__name__)


# @requires_agent("categorize_claims")
async def categorize_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info(f"categorize_claims ({state.config.session_id}): starting")

    results = await iterate_chunks(
        state, _categorize_chunk_claims, "Categorizing claims"
    )
    logger.info(f"categorize_claims ({state.config.session_id}): done")
    return results


async def _categorize_chunk_claims(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    if chunk.claims is None or not chunk.claims.claims:
        logger.debug(
            f"categorize_claims: Chunk {chunk.chunk_index} has no claims to categorize"
        )
        return chunk

    updated_claims = []
    for claim_index, claim in enumerate(chunk.claims.claims):
        try:
            result: ClaimCategorizationResponse = await claim_categorizer_agent.apply(
                {
                    "full_document": state.file.markdown,
                    "paragraph": state.get_paragraph(chunk.paragraph_index),
                    "chunk": chunk.content,
                    "claim": claim.claim,
                    "domain_context": format_domain_context(state.config.domain),
                    "audience_context": format_audience_context(
                        state.config.target_audience
                    ),
                }
            )
            updated_claims.append(
                claim.model_copy(
                    update={
                        "claim_category": result.claim_category,
                        "categorization_rationale": result.rationale,
                        "needs_external_verification": result.needs_external_verification,
                    }
                )
            )
        except Exception:
            logger.exception(
                f"categorize_claims: Error categorizing claim {claim_index} in chunk {chunk.chunk_index}"
            )
            updated_claims.append(claim)

    # preserve existing ClaimResponse.rationale; only replace its claims list
    return chunk.model_copy(
        update={
            "claims": chunk.claims.model_copy(update={"claims": updated_claims}),
        }
    )


if __name__ == "__main__":

    nest_asyncio.apply()

    console = Console()

    async def test_claim_categorization():
        # Create a test document chunk
        test_chunk = DocumentChunk(
            chunk_index=0,
            paragraph_index=0,
            content="Machine learning models have shown superior performance on image classification tasks compared to traditional computer vision approaches.",
            claims=ClaimResponse(
                claims=[
                    Claim(
                        text="Machine learning models have shown superior performance on image classification tasks",
                        claim="Machine learning models outperform traditional computer vision approaches on image classification",
                        rationale="The text directly states the comparative performance advantage",
                    )
                ],
                rationale="Extracted a comparative claim about ML performance",
            ),
        )

        # Create test state
        test_state = ClaimSubstantiatorState(
            file=FileDocument(
                file_name="test.md",
                file_path="/tmp/test.md",
                file_type="text/markdown",
                markdown="# Test Document\n\nMachine learning models have shown superior performance on image classification tasks compared to traditional computer vision approaches.",
            ),
            config=SubstantiationWorkflowConfig(
                session_id="test-session",
                domain="machine learning",
                target_audience="technical",
                document_publication_date=datetime(2023, 1, 1).date(),
                agents_to_run=["categorize_claims"],
            ),
            chunks=[test_chunk],
        )

        console.print("\n[bold cyan]Running Claim Categorization Test[/bold cyan]")
        console.print("\n[yellow]Input State:[/yellow]")
        console.print(Panel(test_state.model_dump_json(indent=2), title="Test State"))

        console.print("\n[yellow]Input Chunk:[/yellow]")
        console.print(Panel(test_chunk.model_dump_json(indent=2), title="Test Chunk"))

        try:
            # Test the claim categorization
            result = await _categorize_chunk_claims(test_state, test_chunk)

            console.print("\n[green]Categorization Results:[/green]")
            console.print(
                Panel(
                    result.claims.model_dump_json(indent=2),
                    title="Categorized Claims",
                )
            )

        except Exception as e:
            console.print(f"\n[red]Error during categorization:[/red]")
            console.print(Panel(str(e), title="Error", style="red"))

    parser = argparse.ArgumentParser(description="Test Claim Categorization")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args, _ = parser.parse_known_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    console.print("\n[bold]Starting Claim Categorization Test[/bold]")
    console.print("[dim]Run with --debug flag for detailed logging[/dim]")

    asyncio.run(test_claim_categorization())
