"""
Inference Validation Agent

Analyzes a full document for logically invalid inferences. Implemented as a
deep agent that spawns three independent sub-agent detection passes over
`/main.md` and then consolidates them into a single, severity-ranked list.
The whole pipeline (detect x3 -> consolidate) lives in the `inference-validation`
skill.

`InferenceAnalysis` / `InferenceResultResponse` are retained as the per-pass
data contract and for backward-compatible deserialization of older workflow
states; the consolidated output uses `ConsolidatedInferenceResultResponse`.
"""

import logging
from typing import Optional

from deepagents import create_deep_agent
from langchain.agents.structured_output import AutoStrategy
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, ConfigDict, Field

from lib.agents.inference_synthesizer import ConsolidatedInferenceResultResponse
from lib.config.llm_models import gpt_5_5_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema

logger = logging.getLogger(__name__)


# =========================
#  Pydantic data contracts
# =========================


class InferenceAnalysis(BaseModel):
    """A single invalid-inference finding from one detection pass."""

    model_config = ConfigDict(extra="forbid")

    key_sentence: str = Field(
        description="The key sentence that contains the incorrect inference, conclusion, or argument. Should be a direct quote from the text."
    )

    inference_validity: bool = Field(
        description="Whether the inference is valid or not."
    )

    short_form_argument_analysis: str = Field(
        description="A concise analysis what is wrong with the inference. In only TWO sentences."
    )

    long_form_argument_analysis: str = Field(
        description="A detailed analysis what is wrong with the inference."
    )

    suggested_action: str = Field(
        description="A suggested action to take to correct the wrong inference. In only TWO sentences."
    )


class InferenceResultResponse(BaseModel):
    """Response containing the result of a single inference check pass."""

    model_config = ConfigDict(extra="forbid")

    results: list[InferenceAnalysis] = Field(
        description="The result of the inference check"
    )


# =========================
#  Agent Implementation
# =========================


class InferenceValidationAgent(LangChainAgent):
    """Deep agent that detects and consolidates inferential errors in a document.

    Spawns three independent sub-agent detection passes over `/main.md` (via the
    deep-agent `task` tool) and consolidates their findings into a single,
    double-checked, severity-ranked list. The orchestration is defined in the
    `inference-validation` skill.
    """

    name = "Inference Validation"
    description = "Detect and consolidate inferential errors in full documents"
    model = gpt_5_5_model
    temperature = 0.2
    reasoning = {"effort": "low", "summary": "auto"}

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> ConsolidatedInferenceResultResponse:
        deep_agent = create_deep_agent(
            model=self.llm,
            context_schema=ContextSchema,
            response_format=AutoStrategy(ConsolidatedInferenceResultResponse),
        )

        result = await deep_agent.ainvoke(
            {
                "files": await self.context.file_artifacts_service.get_deepagent_backend_files(
                    include_skills=False,
                ),
                "messages": [
                    SystemMessage(content=load_skill_prompt("inference-validation")),
                    HumanMessage(
                        content=(
                            "The document under review is available in your filesystem "
                            "at `/main.md`. Validate its inferences following your "
                            "instructions: spawn three independent detection sub-agents "
                            "(tell each to read `/main.md`), then an independent "
                            "adjudicator sub-agent that re-reads `/main.md`, and return "
                            "the consolidated, severity-ranked findings."
                        )
                    ),
                ],
            },
            config={"recursion_limit": 100, **(config or {})},
        )

        return result["structured_response"]
