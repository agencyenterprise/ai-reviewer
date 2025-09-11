from typing import List, Optional
from lib.agents.reference_matcher import (
    reference_matcher_agent,
    ReferenceMatch,
)
from lib.agents.tools import format_supporting_documents_prompt_section
from lib.workflows.claim_substantiation.state import ClaimSubstantiatorState


async def match_references(state: ClaimSubstantiatorState) -> ClaimSubstantiatorState:
    if not state.get("references") or not state.get("supporting_files"):
        return {}

    references = state["references"]
    matches: List[ReferenceMatch] = []

    for supporting_file in state["supporting_files"]:
        supporting_preview = await format_supporting_documents_prompt_section(
            supporting_file
        )
        try:
            match: Optional[ReferenceMatch] = await reference_matcher_agent.apply(
                {"references": references, "supporting_document": supporting_preview}
            )
            if match:
                matches.append(match)
        except Exception:
            # Best-effort matching per supporting file
            continue

    return {"matches": matches}
