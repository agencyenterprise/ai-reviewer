# %%
import logging

from lib.agents.claim_categorizer import (
    claim_categorizer_agent,
    ClaimCategorizationResponse,
    ClaimCategorizationResponseWithClaimIndex,
)
from lib.agents.formatting_utils import (
    format_audience_context,
    format_domain_context,
)
from lib.workflows.claim_substantiation.state import (
    ClaimSubstantiatorState,
    DocumentChunk,
)
from lib.workflows.chunk_iterator import iterate_chunks
from lib.workflows.decorators import handle_chunk_errors

logger = logging.getLogger(__name__)


async def categorize_claims(
    state: ClaimSubstantiatorState,
) -> ClaimSubstantiatorState:
    logger.info(f"categorize_claims ({state.config.session_id}): starting")

    results = await iterate_chunks(
        state, _categorize_chunk_claims, "Categorizing claims"
    )
    logger.info(f"categorize_claims ({state.config.session_id}): done")
    return results


@handle_chunk_errors("Claim categorization")
async def _categorize_chunk_claims(
    state: ClaimSubstantiatorState, chunk: DocumentChunk
) -> DocumentChunk:
    # Skip if chunk has no claims
    if chunk.claims is None or not chunk.claims.claims:
        logger.debug(
            "Skipping claim categorization for chunk %s: no claims detected",
            chunk.chunk_index,
        )
        return chunk

    categorization_results = []
    for claim_index, claim in enumerate(chunk.claims.claims):
        result = await claim_categorizer_agent.ainvoke(
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
        categorization_results.append(
            ClaimCategorizationResponseWithClaimIndex(
                chunk_index=chunk.chunk_index,
                claim_index=claim_index,
                **result.model_dump(),
            )
        )

    return chunk.model_copy(update={"claim_categories": categorization_results})


if __name__ == "__main__":
    import asyncio
    import argparse
    from datetime import datetime
    from lib.services.file import FileDocument
    from lib.agents.claim_extractor import Claim, ClaimResponse
    from lib.workflows.claim_substantiation.state import SubstantiationWorkflowConfig
    from rich.console import Console
    from rich.panel import Panel
    import nest_asyncio
    import json

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
            ),
            chunks=[test_chunk],
        )

        console.print("\n[bold cyan]Running Claim Categorization Test[/bold cyan]")
        console.print("\n[yellow]Input Chunk:[/yellow]")
        console.print(Panel(test_chunk.model_dump_json(indent=2), title="Test Chunk"))

        try:
            # Test the claim categorization
            result = await _categorize_chunk_claims(test_state, test_chunk)

            console.print("\n[green]Categorization Results:[/green]")
            if result.claim_categories:
                for cat_result in result.claim_categories:
                    console.print(
                        Panel(
                            json.dumps(
                                cat_result.model_dump(),
                                indent=2,
                                default=str,
                                ensure_ascii=False,
                            ),
                            title=f"Claim {cat_result.claim_index} - {cat_result.claim_category.value}",
                        )
                    )
            else:
                console.print("[yellow]No categorization results[/yellow]")

        except Exception as e:
            console.print(f"\n[red]Error during categorization:[/red]")
            console.print(Panel(str(e), title="Error", style="red"))
            import traceback

            traceback.print_exc()

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
