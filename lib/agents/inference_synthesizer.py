"""
Inference data contracts (consolidated results).

The consolidated inference schema produced by the inference-validation pipeline.
The detection + consolidation logic now lives in a single deep agent
(`InferenceValidationAgent`) driven by the `inference-validation` skill; this
module retains the consolidated data contracts, which are also used for
backward-compatible deserialization of older workflow states.
"""

from pydantic import BaseModel, ConfigDict, Field

from lib.workflows.models import SeverityEnum


class ConsolidatedInferenceAnalysis(BaseModel):
    """The consolidated result of the inference check."""

    model_config = ConfigDict(extra="forbid")

    key_sentence: str = Field(
        description="The key sentence that contains the incorrect inference, conclusion, or argument. Should be a direct quote from the text."
    )

    severity: SeverityEnum = Field(
        description="The severity level of the inference analysis. HIGH if the inference problem leads the conclusion to be completely invalid. MEDIUM if the inference problem weakens the justification for the conclusion. LOW if the inference problem is a minor/tangential issue that does not significantly weaken the justification for the conclusion. NONE if the inference is valid and correct."
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


class ConsolidatedInferenceResultResponse(BaseModel):
    """Response containing the consolidated result of the inference check."""

    model_config = ConfigDict(extra="forbid")

    results: list[ConsolidatedInferenceAnalysis] = Field(
        description="The result of the inference check"
    )
