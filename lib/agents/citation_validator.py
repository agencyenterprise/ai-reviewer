"""Citation validator agent that reads document sections and validates citations."""

from enum import StrEnum
from typing import List, Optional

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.state import RunnableConfig
from pydantic import BaseModel, Field

from lib.agents.claim_verifier import ClaimEvidenceSource
from lib.agents.tools.read_document import read_document
from lib.agents.tools.search_document import search_document
from lib.agents.tools.vector_search import vector_search
from lib.config.llm_models import gpt_5_5_model
from lib.models.agent import LangChainAgent
from lib.skills import load_skill_prompt
from lib.workflows.context import ContextSchema


class TruthfulnessLabel(StrEnum):
    """Truthfulness taxonomy adapted from the RAND policy benchmark
    (RAND_RRA4269-1, Table 2), plus an `unverifiable` value for citations
    whose supporting file is missing or inaccessible.

    RAND's `divergent_positions` category is intentionally omitted: the agent
    never reaches it reliably and the benchmark has too few examples to measure
    it, so claims that present mixed evidence are routed to `partially_true`."""

    TRUE_EXPLICIT = "true_explicit"
    TRUE_INFERRED = "true_inferred"
    PARTIALLY_TRUE = "partially_true"
    FALSE_CONTRADICTED = "false_contradicted"
    FALSE_NOT_IN_TEXT = "false_not_in_text"
    UNVERIFIABLE = "unverifiable"


class CitationAssessment(BaseModel):
    """The agent's output for a single assessed citation — exactly what the LLM
    must return, and nothing more (no persistence/legacy fields). The
    validate_section node converts this into the workflow's persisted
    `CitationIssueItem`, which keeps deprecated fields for retro-compatibility."""

    quoted_text: str = Field(
        description="The exact sentence or passage from the main document that contains the citation marker."
    )
    line_start: int = Field(
        description="1-indexed line number where quoted_text starts."
    )
    line_end: int = Field(description="1-indexed line number where quoted_text ends.")
    addresses_specific_claim: bool = Field(
        description=(
            "Gate question, answered independently of the label below. Setting "
            "the general topic aside, does the source actually state the claim's "
            "SPECIFIC assertion — its particular numbers, entities, scope, or the "
            "relationship it asserts? The source merely discussing the broader "
            "subject WITHOUT stating the claim's specific content does NOT count "
            "— answer false then. If false, the citation is `false_not_in_text` "
            "regardless of the label below."
        )
    )
    truthfulness_label: Optional[TruthfulnessLabel] = Field(
        default=None,
        description=(
            "Truthfulness category of the cited claim. Possible values: "
            f"{[e.value for e in TruthfulnessLabel]}."
        ),
    )
    rationale: str = Field(
        description="Brief explanation of why the citation is or is not supported."
    )
    feedback: str = Field(
        description="Actionable suggestion for the author. Return 'No changes needed' if the citation is correct."
    )
    evidence_sources: List[ClaimEvidenceSource] = Field(
        description="All reference files that were checked when validating this citation.",
        default_factory=list,
    )
    citation_to_file_mapping: Optional[str] = Field(
        default=None,
        description=(
            "Display-friendly summary of which bibliography entry was matched to "
            "which supporting file when checking this citation, e.g. "
            "'Smith (2020) → smith_2020.pdf'. Do not include file_id UUIDs in this "
            "string; the file_id belongs in each entry of evidence_sources."
        ),
    )


class SectionValidationResult(BaseModel):
    """The citation-validator agent's output for one document section."""

    issues: List[CitationAssessment] = Field(
        description="All citations identified in this section, with their validation results.",
        default_factory=list,
    )


def _apply_addresses_gate(item: CitationAssessment) -> None:
    """One-way override: if the source does not state the claim's specific
    assertion (`addresses_specific_claim` is False), force `false_not_in_text`.

    This is the only structured intervention on the model's directly-chosen
    label. It targets the dominant failure mode (the source discusses the topic
    but not the claim → over-credited to `partially_true`) without disturbing
    the model's strong native judgments on the supported/contradicted side.
    `unverifiable` (source missing) is respected, not overridden.
    """
    if item.truthfulness_label == TruthfulnessLabel.UNVERIFIABLE:
        return
    if not item.addresses_specific_claim:
        item.truthfulness_label = TruthfulnessLabel.FALSE_NOT_IN_TEXT


# The citation-substantiation *method* lives in the portable `citation-support`
# skill (the single source of truth). This backend-only addendum carries the
# Draft-Detective specifics the skill omits: the assigned section, the concrete
# document-access tools, the bibliography→file mapping, and the structured-output
# field mapping. It is a `str.format` template — only this addendum is formatted,
# never the skill body (so the skill's literal braces are safe).
_ENV_GUIDANCE = """\


---

## Your assigned section

You are assigned a single section of the document; validate only citations whose
markers fall within it (this avoids duplicates from adjacent sections).

- **Main document file_id**: `{main_file_id}`
- **Section line range**: lines {start_line}–{end_line}
- **Section headings**: {section_headings}

## Tools in this environment

1. **read_document(file_id, start_line, end_line)**: Read a line range from any document (max 300 lines). Use the main document file_id to read your assigned section (or adjacent lines for boundary context), and a reference file_id to read source material.
2. **search_document(file_id, pattern)**: Search a document for lines matching a case-insensitive regex — use for specific terms, numbers, statistics, names, or exact phrases. To resolve a footnote marker, search the main document for the footnote entry (e.g. `^\\s*2\\.` or `\\[\\^2\\]`), read it, and match it to the bibliography-to-file mapping below.
3. **vector_search(file_id, query, top_k)**: Semantic search in a **supporting file** (not the main document) — use for conceptual or thematic claims where wording differs. Recommended top_k: 10.

Start by reading your assigned section with `read_document(main_file_id, {start_line}, {end_line})`, extending to adjacent lines if the boundaries fall mid-sentence or mid-block.

## Bibliography-to-file mapping

This table maps each bibliography entry to its supporting file. Use the file_id when calling the tools; a citation whose entry has no supporting file is `unverifiable`.

```
{reference_file_map}
```

## Output

Return `issues` — one `CitationAssessment` per citation you validate — each with:
- `quoted_text`: the exact sentence/passage containing the citation marker;
- `line_start` / `line_end`: its 1-indexed line range in the main document;
- `addresses_specific_claim`: the specific-claim gate (boolean). If false, the citation is treated as `false_not_in_text` regardless of the label, so keep the two consistent;
- `truthfulness_label`: one of `true_explicit`, `true_inferred`, `partially_true`, `false_contradicted`, `false_not_in_text`, `unverifiable`;
- `rationale`: a brief explanation of the judgment;
- `feedback`: an actionable suggestion for the author (`"No changes needed"` if the citation is correct);
- `evidence_sources`: every reference file you checked for this citation (with a quote, location, and file_id each);
- `citation_to_file_mapping`: a display-friendly summary of which bibliography entry matched which file (e.g. `"Smith (2020) → smith_2020.pdf"`; no file_id UUIDs here).

{domain_context}

{audience_context}
"""


_USER_MESSAGE = "Please validate all citations in your assigned section."


class CitationValidatorAgent(LangChainAgent):
    name = "Citation Validator"
    description = "Validate citations in a document section against reference files"
    model = gpt_5_5_model
    temperature = 0.0
    reasoning = {"effort": "medium", "summary": "auto"}

    async def ainvoke(
        self,
        prompt_kwargs: dict,
        config: Optional[RunnableConfig] = None,
    ) -> tuple[SectionValidationResult, List[BaseMessage]]:
        agent = create_agent(
            self.llm,
            [vector_search, search_document, read_document],
            context_schema=ContextSchema,
            response_format=SectionValidationResult,
        )

        result = await agent.ainvoke(
            {
                "messages": [
                    SystemMessage(
                        content=load_skill_prompt("citation-support")
                        + _ENV_GUIDANCE.format(**prompt_kwargs)
                    ),
                    HumanMessage(content=_USER_MESSAGE),
                ]
            },
            config={"recursion_limit": 80, **(config or {})},
            context=self.context,
        )

        structured: SectionValidationResult = result["structured_response"]
        for issue in structured.issues:
            _apply_addresses_gate(issue)

        return structured, result["messages"]
