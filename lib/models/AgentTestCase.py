from __future__ import annotations

import json
from typing import Any, Dict, Optional, Set, Type, TypeVar

from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from deepdiff import DeepDiff


from lib.models.agent import Agent


TResponse = TypeVar("TResponse", bound=BaseModel)


class EvaluationResult(BaseModel):
    passed: bool = Field(
        description="Whether the expected and received results match, thus passed the evaluation"
    )
    rationale: str = Field(description="Brief reason for the decision")


class AgentTestCase(BaseModel):
    """Generic container for agent test cases with mixed strict/LLM grading.

    - expected_json stores the golden output as a dict matching the agent's response model
    - expected/result are parsed instances of response_model for type-safe access
    - strict_fields are dotted selectors compared exactly (e.g., "reference_index")
    - llm_fields are field names to be graded by an LLM (e.g., "claims")
    - ignore_fields are dotted prefixes to omit from both expected and result prior to checks
    """

    name: str
    agent: Agent
    response_model: Type[TResponse]
    prompt_kwargs: Dict[str, Any]

    # Goldens and results
    expected_json: Dict[str, Any]
    expected: Optional[TResponse] = None
    result: Optional[TResponse] = None

    # Field selectors (same format as pydantic model_dump's include and exclude inputs)
    strict_fields: set | dict = Field(default_factory=set)
    llm_fields: set | dict = Field(default_factory=set)
    ignore_fields: set | dict = Field(default_factory=set)

    # Evaluator model (provider:model). Keep temperature 0 for determinism.
    evaluator_model: str = Field(default="openai:gpt-5")

    def model_post_init(self, __context: Any) -> None:  # type: ignore[override]
        # Parse expected_json into the typed model instance
        if self.expected is None:
            self.expected = self.response_model.model_validate(self.expected_json)  # type: ignore[arg-type]

    async def run(self) -> TResponse:
        """Run the agent and store the typed result."""
        result = await self.agent.apply(self.prompt_kwargs)
        # Ensure result is the expected pydantic type
        self.result = self.response_model.model_validate(result)  # type: ignore[arg-type]
        return self.result  # type: ignore[return-value]

    async def _compare_llm(self) -> EvaluationResult:
        """Use an LLM to semantically compare selected fields."""
        assert (
            self.expected is not None and self.result is not None
        ), "Run the test first"

        expected_llm_json = self.expected.model_dump_json(
            include=self.llm_fields, exclude=self.ignore_fields, indent=2
        )
        result_llm_json = self.result.model_dump_json(
            include=self.llm_fields, exclude=self.ignore_fields, indent=2
        )

        if expected_llm_json == "{}" and result_llm_json == "{}":
            return EvaluationResult(
                passed=True, rationale="No fields require llm comparison"
            )

        evaluator_model_str = str(self.evaluator_model)
        provider, model = evaluator_model_str.split(":", 1)
        grader = init_chat_model(model, model_provider=provider, temperature=0)
        grader = grader.with_structured_output(EvaluationResult)

        prompt = ChatPromptTemplate.from_template(
            """
You are a strict evaluator for agent outputs.

Instructions:
- Compare the EXPECTED and RECEIVED JSON for the selected fields.
- For list-like fields, ignore order.
- For textual fields or rationales, accept minor wording differences if the meaning is equivalent.
- If counts differ in list-like fields or any expected item is missing semantically, return passed=False.

Return a boolean 'passed' (True if the expected and received results match, False otherwise) and a short 'rationale'.

EXPECTED JSON (selected fields):
```json
{expected_llm_json}
```

RECEIVED JSON (selected fields):
```json
{result_llm_json}
```
"""
        )

        messages = prompt.format_messages(
            expected_llm_json=expected_llm_json,
            received_llm_json=result_llm_json,
        )

        return grader.invoke(messages)

    async def _compare_strict(self) -> EvaluationResult:
        expected_strict = self.expected.model_dump(
            include=self.strict_fields, exclude=self.ignore_fields
        )
        result_strict = self.result.model_dump(
            include=self.strict_fields, exclude=self.ignore_fields
        )
        different_fields = DeepDiff(expected_strict, result_strict, ignore_order=True)
        different_fields_str = json.dumps(different_fields, indent=2)

        if len(different_fields) == 0:
            return EvaluationResult(passed=True, rationale="No differences found")
        else:
            return EvaluationResult(
                passed=False,
                rationale=f"Fields with differences with expected: {different_fields_str}",
            )

    async def compare_results(self) -> EvaluationResult:
        strict_eval = await self._compare_strict()
        llm_eval = await self._compare_llm()
        return EvaluationResult(
            passed=strict_eval.passed and llm_eval.passed,
            rationale="\n".join([strict_eval.rationale, llm_eval.rationale]),
        )
