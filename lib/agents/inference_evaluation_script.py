# inference evaluation script
# %%
"""
inferential_validity_pipeline.py

End-to-end example:
- LLM segments a paragraph into sentences/statements
- Maps statements into arguments: premises & conclusions
- Produces a SymPy-friendly formalization (restricted DSL)
- Calls a local "tool" that uses sympy to test logical validity
  (valid iff premises ∧ ¬conclusion is unsatisfiable)

Requirements:
  pip install openai sympy pydantic>=2 langchain-core

Env:
  export OPENAI_API_KEY=...
"""

from __future__ import annotations
import time
import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional
import textwrap

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sympy import And, Not, Or, Implies, Equivalent, symbols
from sympy.logic.inference import satisfiable
from sympy.parsing.sympy_parser import parse_expr

from lib.models.llm import OpenAIWrapper

from itertools import zip_longest


def pretty_print_inference(result: InferenceBatchResult) -> None:
    # Index -> Statement mapping for quick lookup
    idx_to_stmt = {s.index: s for s in result.statements}

    print("\n=== PASSAGE SUMMARY ===")
    print(result.passage_summary)

    print("\n=== STATEMENTS ===")
    for s in result.statements:
        print(f"{s.index:>2}. {s.role.upper():<10} {s.text}")

    print("\n=== FORMAL ARGUMENTS + VALIDITY ===")
    for v in result.validated_arguments:
        arg = v.argument
        print(f"\nArgument {arg.argument_id}")

        # Premises with mapping to original sentences
        print("  Premises:")
        for i, (p_idx, formal_p) in enumerate(
            zip_longest(arg.premise_indices, arg.formal_premises, fillvalue=None),
            start=1,
        ):
            stmt = idx_to_stmt.get(p_idx)
            sent_text = stmt.text if stmt else "(missing statement)"
            idx_label = f"[{p_idx}]" if p_idx is not None else "[?]"
            print(f"    P{i}: {idx_label} {sent_text}")
            if formal_p is not None:
                print(f"       Formal: {formal_p}")

        # Conclusion with mapping
        concl_stmt = idx_to_stmt.get(arg.conclusion_index)
        concl_text = concl_stmt.text if concl_stmt else "(missing statement)"
        print("  Conclusion:")
        print(f"    C:  [{arg.conclusion_index}] {concl_text}")
        print(f"       Formal: {arg.formal_conclusion}")

        # Clear validity status
        valid = bool(v.validity_result.get("valid"))
        print(f"  Valid?: {'YES' if valid else 'NO'}")

        # Countermodel (if invalid)
        countermodel = v.validity_result.get("countermodel")
        if not valid and countermodel:
            assigns = ", ".join(
                f"{k}={str(val).lower()}" for k, val in sorted(countermodel.items())
            )
            print(f"  Countermodel: {assigns}")

        if v.notes:
            print(f"  Notes: {v.notes}")


# -----------------------------
# 1) SymPy validity "tool"
# -----------------------------

# %%
# Pre-create a pool of propositional symbols A..Z, P..Z etc. (LLM will reference these)
_SYMBOL_NAMES = (
    [chr(i) for i in range(ord("A"), ord("Z") + 1)]
    + ["P" + str(i) for i in range(1, 51)]
    + ["Q" + str(i) for i in range(1, 51)]
    + ["R" + str(i) for i in range(1, 51)]
    + ["X", "Y", "Z", "C"]
)


_SYMBOLS = symbols(" ".join(sorted(set(_SYMBOL_NAMES))))
_LOCAL_SYMS = {str(s): s for s in _SYMBOLS}
# print(_LOCAL_SYMS)


# from sympy.abc import A, B
# print(satisfiable(A & ~B))

# %%

# Allow only a safe micro-DSL:
#   Atoms: A, B, C, P, Q, R, P1, Q2, ...
#   Connectives (as SymPy functions): And(A,B), Or(A,B), Not(A), Implies(A,B), Equivalent(A,B)
#   Parentheses mandatory; no unicode operators; no lowercase variable names.
# _ALLOWED_FUNCS = {"And": And, "Not": Not}
# Implies/Or/Equivalent are created via parse_expr; add names to locals:
# from sympy import Or, Implies, Equivalent  # noqa: E402

_LOCAL_SYMS.update(
    {"And": And, "Or": Or, "Not": Not, "Implies": Implies, "Equivalent": Equivalent}
)


def _parse_formula(expr_str: str):
    """
    Parse a restricted SymPy expression string safely into a SymPy boolean expression.
    Allowed: And(), Or(), Not(), Implies(), Equivalent(); variables from _LOCAL_SYMS only.

    Examples:
        >>> _parse_formula("And(P,Q)")  # Basic conjunction
        And(P, Q)

        >>> _parse_formula("Implies(P,Q)")  # Implication
        Implies(P, Q)

        >>> _parse_formula("And(P,Not(Q))")  # With negation
        And(P, Not(Q))

        >>> _parse_formula("x")  # Invalid symbol
        Traceback (most recent call last):
            ...
        ValueError: Symbol x not allowed.

        >>> _parse_formula("sin(P)")  # Invalid function
        Traceback (most recent call last):
            ...
        ValueError: Could not parse formula: sin(P).
    """
    expr_str = expr_str.strip()
    try:
        expr = parse_expr(expr_str, local_dict=_LOCAL_SYMS, evaluate=True)
    except Exception as e:
        raise ValueError(f"Could not parse formula: {expr_str}. Error: {e}")
    # Basic sanity: must be a boolean expression (has 'free_symbols' subset of locals)
    for sym in expr.free_symbols:
        if str(sym) not in _LOCAL_SYMS:
            raise ValueError(f"Symbol {sym} not allowed.")
    return expr


@tool
def check_validity(
    formal_premises: List[str], formal_conclusion: str
) -> Dict[str, Any]:
    """Test if premises logically entail the conclusion using propositional logic.

    Core validity checker: valid iff And(premises) & Not(conclusion) is unsatisfiable.

    Args:
        formal_premises: List of SymPy-friendly boolean expressions (e.g., "Implies(P,Q)", "P")
        formal_conclusion: SymPy-friendly boolean expression (e.g., "Q")

    Returns:
        Dict with 'valid' (bool) and 'countermodel' ({symbol: True/False} or None)

    Example:
        # Valid argument (modus ponens)
        >>> check_validity(
        ...     formal_premises=["Implies(P,Q)", "P"],
        ...     formal_conclusion="Q"
        ... )
        {'valid': True, 'countermodel': None}

        # Invalid argument
        >>> check_validity(
        ...     formal_premises=["P"],
        ...     formal_conclusion="Q"
        ... )
        {'valid': False, 'countermodel': {'P': True, 'Q': False}}
    """
    premises_exprs = (
        [_parse_formula(s) for s in formal_premises] if formal_premises else []
    )
    conclusion_expr = _parse_formula(formal_conclusion)

    conj = And(*premises_exprs) if len(premises_exprs) > 0 else True
    formula = And(conj, Not(conclusion_expr))
    model = satisfiable(formula, all_models=False)
    if model is False:
        return {"valid": True, "countermodel": None}
    # Normalize countermodel to plain bools
    norm = {}
    for k, v in model.items():
        if hasattr(v, "bool"):
            try:
                v = bool(v)
            except Exception:
                pass
        norm[str(k)] = bool(v)
    return {"valid": False, "countermodel": norm}


# -----------------------------
# 2) Pydantic output contracts
# -----------------------------


class InferenceRole(str, Enum):
    PREMISE = "premise"
    CONCLUSION = "conclusion"
    NEUTRAL = "neutral"  # sentence not used in an argument


class Statement(BaseModel):
    index: int = Field(..., description="1-based order of the statement.")
    text: str
    role: InferenceRole
    linked_argument_id: Optional[str] = Field(
        default=None,
        description="ID of the argument this statement belongs to (if any).",
    )


class FormalArgument(BaseModel):
    argument_id: str = Field(..., description="Stable ID for one argument, e.g., A1.")
    premise_indices: List[int] = Field(
        ..., description="Indices of statements used as premises."
    )
    conclusion_index: int = Field(
        ..., description="Index of statement used as the conclusion."
    )
    # Micro-DSL use: And(), Or(), Not(), Implies(), Equivalent(); Vars: A,B,C,P,Q,R,P1,Q1,R1...
    formal_premises: List[str] = Field(
        ...,
        description="Each as a SymPy-friendly string, e.g., 'Implies(P, Q)', 'P', 'And(P, R)'.",
    )
    formal_conclusion: str = Field(..., description="SymPy-friendly string, e.g., 'Q'.")


class ValidatedArgument(BaseModel):
    argument: FormalArgument
    validity_result: Dict[str, Any] = Field(
        ...,
        description="Return from the tool: {'valid': bool, 'countermodel': {...}|None}",
    )
    notes: str = Field(
        default="",
        description="Brief note about mapping or caveats (e.g., assumptions, scope).",
    )


class InferenceBatchResult(BaseModel):
    passage_summary: str
    statements: List[Statement]
    formal_arguments: List[FormalArgument]
    validated_arguments: List[ValidatedArgument]


# -----------------------------
# 3) LLM orchestration
# -----------------------------

SYSTEM_INSTRUCTIONS = """\
You are an expert in argument analysis and formal logic.

Task: Given a paragraph, you will:
  (1) segment it into sentences,
  (2) label each as PREMISE, CONCLUSION, or NEUTRAL (if not part of an argument),
  (3) group PREMISE(s) + CONCLUSION into one or more arguments,
  (4) produce a SymPy-friendly formalization for each argument using ONLY:
      - variables: A..Z, P..R, or indexed like P1, Q2
      - connectives: And(X,Y), Or(X,Y), Not(X), Implies(X,Y), Equivalent(X,Y)

Rules:
- Keep each sentence text EXACT in the output.
- If a conclusion relies on multiple premises, list them all.
- If a sentence is not used in any argument, mark it NEUTRAL.
- Choose variables consistently within each argument (e.g., P, Q, R).
- No unicode or alternate spellings; only the allowed connectives exactly as written.
- DO NOT invent citations or facts; map structure only.
- Prefer simple canonical forms (e.g., Implies(P, Q) rather than Or(Not(P), Q)).

You have access to a tool 'check_validity' to evaluate whether each formalized argument is valid.
Validity definition (propositional): The argument is valid iff (premises AND NOT conclusion) is UNSATISFIABLE.

Process:
1) Segment and label each sentence
2) Build FormalArgument objects
3) For EACH FormalArgument, call 'check_validity' with formal_premises and formal_conclusion
4) Return the complete InferenceBatchResult with all validated arguments

Output must be a single JSON object matching the InferenceBatchResult schema exactly.
"""

USER_TEMPLATE = """\
PARAGRAPH:
\"\"\"{paragraph}\"\"\"

Segment the paragraph, identify arguments, formalize them, and validate using the check_validity tool.
Return a complete InferenceBatchResult JSON with all fields populated.
"""


async def run_inference_validity_pipeline(
    paragraph: str,
    model: str = "gpt-5",
    api_key: Optional[str] = None,
) -> InferenceBatchResult:
    """
    Orchestrates an LLM to analyze argument validity using a two-phase approach:

    Phase 1: Parse paragraph into statements and arguments (no tools)
    Phase 2: Validate formalized arguments using tool calls

    This approach separates parsing from validation, avoiding the infinite loop issue.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY or pass api_key")

    from langfuse.openai import AsyncOpenAI
    import json

    client = AsyncOpenAI(api_key=api_key)

    # Phase 1: Parse paragraph into statements and arguments (no tools)
    parsing_result = await _parse_paragraph_into_arguments(client, paragraph, model)

    # print the statement to symbolic mapping
    # Print statement to symbolic mapping for debugging
    print("\n=== STATEMENT TO SYMBOLIC MAPPING ===")
    for arg in parsing_result.formal_arguments:
        print(f"\nArgument {arg.argument_id}:")

        # Map premises to their symbolic forms
        for idx, formal in zip(arg.premise_indices, arg.formal_premises):
            stmt = next((s for s in parsing_result.statements if s.index == idx), None)
            if stmt:
                print(f"  P{idx}: {stmt.text}")
                print(f"     → {formal}")

        # Map conclusion to symbolic form
        concl_stmt = next(
            (s for s in parsing_result.statements if s.index == arg.conclusion_index),
            None,
        )
        if concl_stmt:
            print(f"  C{arg.conclusion_index}: {concl_stmt.text}")
            print(f"     → {arg.formal_conclusion}")

    # Phase 2: Validate each formalized argument using tool calls
    validated_arguments = await _validate_arguments_with_tools(
        client, parsing_result.formal_arguments, model
    )

    # Combine results
    return InferenceBatchResult(
        passage_summary=parsing_result.passage_summary,
        statements=parsing_result.statements,
        formal_arguments=parsing_result.formal_arguments,
        validated_arguments=validated_arguments,
    )


async def _parse_paragraph_into_arguments(
    client, paragraph: str, model: str
) -> "ParsingResult":
    """Phase 1: Parse paragraph into statements and arguments without tools."""

    # Separate parsing instructions (no tools)
    parsing_instructions = """\
You are an expert in argument analysis and formal logic. You take a paragraph and segment it into sentences, convert the sentences into statements, and then label each statement as PREMISE, CONCLUSION, or NEUTRAL (if not part of an argument), and group PREMISE(s) + CONCLUSION into one or more arguments. You then produce a SymPy-friendly formalization for each argument using ONLY:

Task: Given a paragraph, you will:
  (1) segment it into sentences,
  (2) convert the sentences into statements. These statements need NOT be exact replicas of the sentences, and can be inferred from the sentences.
  (3) label each statement as PREMISE, CONCLUSION, or NEUTRAL (if not part of an argument),
  (4) group PREMISE(s) + CONCLUSION into one or more arguments,
  (5) produce a SymPy-friendly formalization for each argument using ONLY:
      - variables: A..Z, P..R, or indexed like P1, Q2
      - connectives: And(X,Y), Or(X,Y), Not(X), Implies(X,Y), Equivalent(X,Y)

Rules:
- If a conclusion relies on multiple premises, list them all.
- If a sentence is not used in any argument, mark it NEUTRAL.
- Choose variables consistently within each argument (e.g., P, Q, R).
- No unicode or alternate spellings; only the allowed connectives exactly as written.
- DO NOT invent citations or facts; map structure only.
- Prefer simple canonical forms (e.g., Implies(P, Q) rather than Or(Not(P), Q)).

Guidelines 
- Only include statements that are not in the original paragraph if they are absolutely TRUE independent of the truth of the sentences in the paragraph. 
- A clear indicator of an "Implies" statement is when the statement is like "X leads to Y" or "X <verb implying action> Y". These statements imply that if X is true, then "<verb implying action> Y" is true.

Output must be a single JSON object matching this schema:
{
  "passage_summary": "Brief summary of the passage",
  "statements": [
    {
      "index": 1,
      "text": "inferred statement text",
      "role": "premise|conclusion|neutral",
      "linked_argument_id": "A1" // null if neutral
    }
  ],
  "formal_arguments": [
    {
      "argument_id": "A1",
      "premise_indices": [1, 2],
      "conclusion_index": 3,
      "formal_premises": ["Implies(P,Q)", "P"],
      "formal_conclusion": "Q"
    }
  ]
}
"""

    parsing_template = """\
PARAGRAPH:
\"\"\"{paragraph}\"\"\"

Segment the paragraph, identify arguments, and formalize them.
Return a complete JSON object with the structure above.
"""

    messages = [
        {"role": "system", "content": parsing_instructions},
        {
            "role": "user",
            "content": parsing_template.format(paragraph=paragraph.strip()),
        },
    ]

    print(f"\n=== Phase 1: Parsing paragraph ===")
    response = await client.responses.create(
        model=model,
        input=messages,
    )

    # Parse the response
    output_text = (
        response.output_text
        if hasattr(response, "output_text")
        else str(response.output)
    )

    if not output_text or not output_text.strip():
        raise ValueError("Empty response from parsing phase")

    # Clean markdown code blocks if present
    output_text = output_text.strip()
    if output_text.startswith("```"):
        lines = output_text.split("\n")
        output_text = "\n".join(lines[1:-1]) if len(lines) > 2 else output_text

    try:
        parsing_data = json.loads(output_text)
        return ParsingResult.model_validate(parsing_data)
    except Exception as e:
        raise ValueError(
            f"Failed to parse parsing result: {e}\nOutput: {output_text[:500]}"
        )


async def _validate_arguments_with_tools(
    client, formal_arguments: List[FormalArgument], model: str
) -> List[ValidatedArgument]:
    """Phase 2: Validate formalized arguments using tool calls."""

    validated_arguments = []

    for arg in formal_arguments:
        print(f"\n=== Validating argument {arg.argument_id} ===")

        # Create a simple validation request
        validation_instructions = f"""\
You have access to a tool 'check_validity' to test logical validity.

Call the check_validity tool with:
- formal_premises: {arg.formal_premises}
- formal_conclusion: {arg.formal_conclusion}

Then return the result.
"""

        messages = [
            {"role": "system", "content": validation_instructions},
            {"role": "user", "content": f"Validate this argument: {arg.argument_id}"},
        ]

        # Convert LangChain tool to OpenAI format
        tool_schema = {
            "type": "function",
            "name": check_validity.name,
            "description": check_validity.description,
            "parameters": check_validity.args_schema.model_json_schema(),
        }

        response = await client.responses.create(
            model=model,
            input=messages,
            tools=[tool_schema],
        )

        # Execute tool calls
        tool_calls = []
        if hasattr(response, "output") and isinstance(response.output, list):
            for item in response.output:
                if hasattr(item, "type") and item.type == "function_call":
                    tool_calls.append(item)

        if tool_calls:
            for tool_call in tool_calls:
                tool_name = getattr(tool_call, "name", None)
                tool_args = getattr(tool_call, "arguments", {})

                if tool_name == check_validity.name:
                    # Parse args if they're a string
                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError as e:
                            print(f"JSON decode error: {e}")
                            continue

                    try:
                        print(f"Executing check_validity with: {tool_args}")
                        validity_result = check_validity.func(**tool_args)
                        print(f"Result: {validity_result}")

                        validated_argument = ValidatedArgument(
                            argument=arg,
                            validity_result=validity_result,
                            notes="Validated using tool call",
                        )
                        validated_arguments.append(validated_argument)

                    except Exception as e:
                        print(f"Execution error: {e}")
                        # Create error result
                        validated_argument = ValidatedArgument(
                            argument=arg,
                            validity_result={"valid": False, "countermodel": None},
                            notes=f"Validation error: {str(e)}",
                        )
                        validated_arguments.append(validated_argument)
        else:
            # No tool calls made, create error result
            print(f"No tool calls made for argument {arg.argument_id}")
            validated_argument = ValidatedArgument(
                argument=arg,
                validity_result={"valid": False, "countermodel": None},
                notes="No tool calls executed",
            )
            validated_arguments.append(validated_argument)

    return validated_arguments


# Helper class for parsing results
class ParsingResult(BaseModel):
    passage_summary: str
    statements: List[Statement]
    formal_arguments: List[FormalArgument]


# -----------------------------
# 4) Quick demo (CLI)
# -----------------------------

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    start_time = time.time()

    nest_asyncio.apply()

    print("Running inference validity pipeline...")

    DEMO_LIST = [
        "If the questionnaire response rate exceeds 80%, then sampling bias is unlikely. In our pilot, the response rate exceeded 85%. Therefore, sampling bias is unlikely. Separately, since prior work shows large models generalize better, our larger model will generalize best.",
    ]

    RESEARCH_INFERENCE_EXAMPLES = [
        {
            "id": "1_valid_causal",
            "text": (
                "Because increasing the sample size reduces variance, "
                "and our sample was doubled in this round, we expect the confidence intervals to narrow accordingly."
            ),
            "inference_type": "deductive (causal / modus ponens)",
            "validity": "valid",
            "comment": "Valid reasoning—if premises hold, conclusion follows.",
        },
        {
            "id": "2_invalid_affirm_consequent",
            "text": (
                "Our model achieved human-level performance on the benchmark, "
                "which suggests it must have learned to reason like a human."
            ),
            "inference_type": "deductive (affirming the consequent)",
            "validity": "invalid",
            "comment": "Invalid—performance does not entail human-like reasoning.",
        },
        {
            "id": "3_valid_modus_tollens",
            "text": (
                "If the catalyst had been active, we would have observed a sharp drop in activation energy. "
                "No such drop occurred, implying the catalyst was inactive under these conditions."
            ),
            "inference_type": "deductive (modus tollens)",
            "validity": "valid",
            "comment": "Valid deductive inference; negation of consequence implies negation of cause.",
        },
        {
            "id": "4_inductive_generalization",
            "text": (
                "Across the three datasets we tested, the scaling law held consistently, "
                "suggesting this trend likely generalizes to similar domains."
            ),
            "inference_type": "inductive generalization",
            "validity": "plausible",
            "comment": "Inductive inference—reasonable but not logically certain.",
        },
        {
            "id": "5_false_cause",
            "text": (
                "Model accuracy decreased after we added differential privacy, "
                "so the privacy constraint appears to be the main reason for the drop."
            ),
            "inference_type": "causal (post hoc fallacy)",
            "validity": "invalid",
            "comment": "Invalid—temporal sequence does not prove causation.",
        },
        {
            "id": "6_valid_controlled_causal",
            "text": (
                "Even after controlling for dataset size and architecture, introducing differential privacy reduced accuracy by 3–5%, "
                "indicating that the privacy constraint itself has a measurable cost."
            ),
            "inference_type": "causal (controlled experiment)",
            "validity": "valid",
            "comment": "Valid conditional causal inference—confounders addressed.",
        },
        {
            "id": "7_abductive_best_explanation",
            "text": (
                "The only parameter that differed between the two experiments was pH, "
                "so the change in yield is most likely attributable to pH effects."
            ),
            "inference_type": "abductive (best explanation)",
            "validity": "plausible",
            "comment": "Reasonable best-explanation inference, not deductively guaranteed.",
        },
        {
            "id": "8_appeal_to_authority",
            "text": (
                "Prior reviews by leading AI ethicists argue that interpretability guarantees fairness; "
                "our results therefore confirm that interpretable models are fairer."
            ),
            "inference_type": "rhetorical (appeal to authority)",
            "validity": "invalid",
            "comment": "Invalid—expert opinion is not direct evidence.",
        },
        {
            "id": "9_weak_analogy",
            "text": (
                "Since convolutional networks capture hierarchical structure effectively, "
                "transformers should exhibit similar advantages on image tasks."
            ),
            "inference_type": "analogical reasoning",
            "validity": "invalid",
            "comment": "Invalid analogy—architectural similarity does not guarantee shared inductive bias.",
        },
        {
            "id": "10_valid_chain",
            "text": (
                "If limited data reduces model accuracy, and lower accuracy undermines reliability, "
                "then limited data ultimately reduces reliability."
            ),
            "inference_type": "deductive (hypothetical syllogism)",
            "validity": "valid",
            "comment": "Valid reasoning chain connecting antecedent to final consequence.",
        },
    ]

    for i, item in enumerate(RESEARCH_INFERENCE_EXAMPLES):

        DEMO = item["text"]
        print(
            f"--RUNNING {i+1} OF {len(RESEARCH_INFERENCE_EXAMPLES)} RESEARCH INFERENCE EXAMPLES--"
        )
        print(
            textwrap.fill(
                f"""INPUT TEXT: {DEMO}
        """,
                width=100,
            )
        )
        result = asyncio.run(run_inference_validity_pipeline(DEMO))
        end_time = time.time()
        print(f"Time taken: {end_time - start_time} seconds")
        print()
        print("\n=== PASSAGE SUMMARY ===")
        print(result.passage_summary)
        print("\n=== STATEMENTS ===")
        for s in result.statements:
            print(f"{s.index:>2}. {s.role.upper():<10} {s.text}")

        print("\n=== FORMAL ARGUMENTS + VALIDITY ===")
        for v in result.validated_arguments:
            print(f"\nArgument {v.argument.argument_id}")
            print("  Premises:", v.argument.formal_premises)
            print("  Conclusion:", v.argument.formal_conclusion)
            print("  Valid?:", v.validity_result.get("valid"))
            print("  Countermodel:", v.validity_result.get("countermodel"))
            if v.notes:
                print("  Notes:", v.notes)
        print()
        print("---------VALIDITY CHECK----------------")
        print(f"Comment: {item['comment']}")
        print(f"Inference Type: {item['inference_type']}")
        print(f"Validity: {item['validity']}")
        print("----------------------------------------")
        print()
    print("All research inference examples completed")
