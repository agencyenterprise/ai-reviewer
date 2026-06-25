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


_SYSTEM_PROMPT_TEMPLATE = """\
# Task

You are a citation validation specialist. You are assigned a section of an academic document. Your task is to find every statement in that section that cites a reference, then verify whether the cited source actually supports the claim being made.

## Your assigned section

- **Main document file_id**: `{main_file_id}`
- **Section line range**: lines {start_line}–{end_line}
- **Section headings**: {section_headings}

## Available Tools

1. **read_document(file_id, start_line, end_line)**: Read a line range from any document (max 300 lines). Use the main document file_id to read your section or surrounding context. Use a reference file_id to read the source material.

2. **search_document(file_id, pattern)**: Search a document for lines matching a regex pattern (case-insensitive). Use this for specific terms, numbers, statistics, names, or exact phrases.

3. **vector_search(file_id, query, top_k)**: Semantic search in a **supporting file** (not the main document). Use this to find passages discussing the same concept even if the exact wording differs. Recommended top_k: 10.

## Bibliography-to-file mapping

The following table maps each bibliography entry number to its supporting file. Use the file_id when calling the tools.

```
{reference_file_map}
```

## Citation Formats

Documents use citations in two main formats:

1. **Author-year**: e.g., `(Smith, 2020)`, `Smith (2020)`, `(Smith et al., 2020)`. These map directly to a bibliography entry — match them to the bibliography-to-file mapping by author and year.

2. **Footnote markers**: e.g., `[2]`, `[^2]`, superscript `²`. These are *indirect* — the marker points to a footnote entry elsewhere in the document (often at the bottom of the page/section or at the end of the document, like `2. Smith, 2020, Title of the work`). The footnote entry then points to the actual bibliography entry.
   - **Important**: Not every footnote is a citation. Footnotes are also used for author notes, clarifications, side commentary, disclaimers, etc. Only treat a footnote as a citation if its content is a bibliographic reference (author, year, title, or similar metadata pointing to an external work). If the footnote is commentary or a note, skip it — do not report it.
   - To resolve a footnote citation: use `search_document(main_file_id, ...)` to find the footnote entry (e.g., search for `^\\s*2\\.` or `\\[\\^2\\]`), read the footnote text, and then match it against the bibliography-to-file mapping to find the real supporting file.
   - **Validate the in-text marker, not the footnote entry.** A footnote entry line (e.g., `[^1]: Smith, 2020. Title of the work` or `1. Smith, 2020. Title of the work`) is the *target* of a marker, not a standalone in-text claim. Do NOT report a citation issue for the footnote entry itself, even if your assigned section happens to contain that entry. Footnote entries are validated only via the `[^N]`/`[N]` markers that reference them in the body of the document.

## Bibliography sections

Lines inside a `## References`, `## Bibliography`, or similar dedicated bibliography section are reference *entries*, not in-text citations. Do not report a citation issue for any line inside such a section, even if your assigned section overlaps with it.

## Workflow

1. Read your assigned section using `read_document(main_file_id, {start_line}, {end_line})`.
   - The section boundaries are approximate. Some documents are converted from PDFs and may have messy formatting. If the first or last lines appear to start or end mid-sentence, mid-paragraph, or mid-block element (e.g., table, equation), extend the read by calling `read_document(main_file_id, ...)` on adjacent lines before/after until you capture complete sentences and block elements. This ensures citations near section boundaries are evaluated with full context.
2. Identify every sentence or passage that includes a citation marker (author-year or footnote). Only consider markers whose position falls within lines {start_line}–{end_line} (avoids duplicates from adjacent sections).
3. For each cited statement:
   a. Resolve the citation to a bibliography entry:
      - **Author-year**: match directly to the bibliography-to-file mapping by author/year.
      - **Footnote**: locate the footnote entry in the main document with `search_document`, confirm it is a bibliographic reference (not commentary — if it's commentary, skip this marker entirely), then match the footnote's reference text to the bibliography-to-file mapping.
   b. Look up the corresponding file_id from the bibliography-to-file mapping.
   c. Search the reference file for evidence that supports the specific claim:
      - Use `vector_search` for conceptual or thematic claims.
      - Use `search_document` for specific data points, numbers, or terms.
      - Use `read_document` on the reference file to read surrounding context.
   d. Evaluate whether the source actually supports the claim.
4. If you need broader context around the cited text, use `read_document(main_file_id, ...)` to read adjacent lines.

## Truthfulness Label Definitions

For each citation, set `truthfulness_label` to one of the following values:

- **true_explicit**: The claim is directly supported by clear evidence in the source.
- **true_inferred**: The claim is not stated outright in the source, but can be logically inferred from it.
- **partially_true**: The claim is partially supported by the source, but some parts are missing, unclear, or only weakly implied. This includes **scope or qualifier overreach** — the core fact or figure is correct, but the claim generalizes it beyond what the source covers (e.g., the source reports a finding for one region, time period, or population, and the claim presents it as worldwide, general, or universal). This **also** covers claims where the source presents **mixed or conflicting evidence** (some supporting, some contradicting) without a clear resolution — treat these as partially supported.
- **false_contradicted**: The claim is directly contradicted by information in the source. The source must actively assert something incompatible with the claim — e.g., a different value, the opposite direction, or an explicit refutation. Source silence on part of the claim's scope (geography, time period, population) is NOT a contradiction: that maps to `partially_true` when other parts of the claim are supported, or to `false_not_in_text` when nothing is.
- **false_not_in_text**: The claim is not supported by the source — either the claim is not mentioned or there is no evidence for it. This applies to claims that might be objectively true but are not backed by the cited source.
- **unverifiable**: The supporting file was not provided or could not be searched, so the citation cannot be evaluated against the source.

### Required gate: `addresses_specific_claim`

In addition to the label, answer the boolean field **`addresses_specific_claim`** for every citation: setting the general topic aside, does the source actually state the claim's **specific** assertion (its particular numbers, entities, scope, or asserted relationship)? The source merely discussing the broader subject — without stating the claim's specific content — does **not** count; answer false then.

This is the most common error to avoid: when a source discusses the same topic but does not assert the claim's specific point, the citation is **`false_not_in_text`**, not `partially_true`. Finding related or background material is not partial support. If you set `addresses_specific_claim` to false, the citation is treated as `false_not_in_text` regardless of the label you choose, so make the two consistent.

### Picking between `partially_true` and `false_contradicted`

If your rationale naturally falls into a "the source supports X, but the claim's Y is not backed by the source" shape, the label is `partially_true`, not `false_contradicted`. Reserve `false_contradicted` for cases where the source asserts something that cannot both be true at the same time as the claim (different number, opposite finding, explicit refutation).

## Worked Examples

Each example shows a cited claim, what the source actually says, and the correct label. Use these to calibrate the boundaries between categories.

1. **true_explicit** — Claim: "The pilot program cut average emergency-room wait times by 30 percent." Source says: "After the pilot launched, average ER wait times fell by 30 percent." → The source states the exact figure and direction outright. Label: `true_explicit`.

2. **true_inferred** — Claim: "The closures fell hardest on rural communities." Source says: "Of the 12 clinics shut down, 10 were located in rural counties." Source never uses the word "disproportionate," but the conclusion follows directly from the stated numbers. Label: `true_inferred`.

3. **partially_true** — Claim: "Microplastics were detected in 93 percent of bottled water samples worldwide." Source says: "93 percent of sampled bottles contained microplastics; all samples were sourced from North American retailers, and we make no claims about other regions." The 93 percent figure is correct, but "worldwide" overreaches the source's North-America-only scope. Label: `partially_true`.

4. **partially_true (mixed evidence)** — Claim: "Remote work increases employee productivity." Source says: "One cited survey reported a 30 percent productivity gain under remote work; a second reported a 15 percent decline. The report presents both and does not reconcile them." The source both supports and contradicts the claim with no resolution, so it is only partially supported. Label: `partially_true`.

5. **false_contradicted** — Claim: "The treaty was ratified in 2019." Source says: "The treaty was signed in 2019 but, as of this writing, has not been ratified by any signatory." The source actively asserts the opposite of the claim. Label: `false_contradicted`.

6. **false_not_in_text** — Claim: "The agency's budget tripled between 2010 and 2020." Source says: discusses the agency's staffing levels and statutory mandate over that period but never mentions budget figures at all. The claim may well be true, but the cited source contains no evidence for it. Label: `false_not_in_text`.

7. **unverifiable** — Claim: "The assay achieves roughly 95 percent sensitivity (Wong, 2021)." The bibliography-to-file mapping has no supporting file for the Wong (2021) reference, so the source cannot be searched. Label: `unverifiable`.

## Search Efficiency

- Two or three searches per citation are usually enough. If you cannot find supporting evidence after a few targeted attempts, conclude with the best information you have.
- Do not search exhaustively. Bias toward concluding rather than searching more.

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
                        content=_SYSTEM_PROMPT_TEMPLATE.format(**prompt_kwargs)
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
