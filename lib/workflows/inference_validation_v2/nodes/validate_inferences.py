import logging
from typing import List

from langgraph.runtime import Runtime

from lib.agents.inference_synthesizer import ConsolidatedInferenceResultResponse
from lib.agents.inference_validator_v2 import InferenceValidationAgent
from lib.services.chunk_line_matcher import find_chunks_by_fuzzy_match
from lib.workflows.context import ContextSchema
from lib.workflows.decorators import register_node
from lib.workflows.inference_validation_v2.state import (
    ExtractedInferenceResult,
    ExtractedInferenceResultResponse,
    InferenceValidationV2State,
)

logger = logging.getLogger(__name__)


@register_node("Validate inferences")
async def validate_inferences(
    state: InferenceValidationV2State, runtime: Runtime[ContextSchema]
) -> dict[str, ExtractedInferenceResultResponse]:
    """Run the inference-validation deep agent and write consolidated results.

    The agent reads `/main.md`, runs three independent detection passes via
    sub-agents, and consolidates them. We then attach chunk indices (by fuzzy
    line match) to each finding for downstream issue rendering.
    """
    agent = InferenceValidationAgent(runtime.context)
    try:
        consolidated = await agent.ainvoke({})
    except Exception as e:
        logger.error(
            "validate_inferences: inference validation agent failed: %s",
            e,
            exc_info=True,
        )
        consolidated = ConsolidatedInferenceResultResponse(results=[])

    chunks = await runtime.context.file_artifacts_service.get_chunks()
    extracted_inference_results: List[ExtractedInferenceResult] = []
    for result in consolidated.results:
        chunk_indices: List[int] = []
        if chunks:
            chunk_indices = find_chunks_by_fuzzy_match(chunks, result.key_sentence)

        extracted_inference_results.append(
            ExtractedInferenceResult(
                key_sentence=result.key_sentence,
                severity=result.severity,
                inference_validity=result.inference_validity,
                short_form_argument_analysis=result.short_form_argument_analysis,
                long_form_argument_analysis=result.long_form_argument_analysis,
                suggested_action=result.suggested_action,
                chunk_indices=chunk_indices,
            )
        )

    return {
        "inference_results": ExtractedInferenceResultResponse(
            results=extracted_inference_results
        )
    }
