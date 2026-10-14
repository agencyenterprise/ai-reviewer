"""Find and read the Abbreviations section for abbreviation scan v2.

Runs before chunking: the section's lines are kept out of the chunks, and its
entries supply each occurrence's Abbreviations-section definition. When the
section cannot be read, the run stops here (see `after_section`).
"""

import logging

from langgraph.graph import END
from langgraph.runtime import Runtime

from lib.agents.abbreviations_section_extractor import (
    AbbreviationsSectionExtractorAgent,
)
from lib.workflows.abbreviation_scan_v2.chunk_models import (
    AbbreviationsSectionRange,
    LineRange,
)
from lib.workflows.abbreviation_scan_v2.section_candidates import find_candidate_lines
from lib.workflows.abbreviation_scan_v2.state import AbbreviationScanV2State
from lib.workflows.context import ContextSchema
from lib.workflows.decorators import register_node
from lib.workflows.models import WorkflowErrorSeverity

logger = logging.getLogger(__name__)


@register_node("Read Abbreviations section")
async def read_abbreviations_section_node(
    state: AbbreviationScanV2State, runtime: Runtime[ContextSchema]
) -> dict:
    main_file = await runtime.context.file_artifacts_service.get_main_file()
    markdown = (main_file.markdown or "") if main_file else ""
    if not markdown.strip():
        return {}
    if not find_candidate_lines(markdown):
        # Nothing the extractor could find; skip the call rather than send a
        # long document to the model for nothing.
        logger.info("[AbbreviationScanV2] No line mentions an Abbreviations section; skipping the extractor")
        return {"abbreviations_section_found": False}

    result, messages = await AbbreviationsSectionExtractorAgent(runtime.context).ainvoke(
        {"markdown": markdown}
    )
    sections = _valid_sections(result.sections, markdown.count("\n") + 1)
    ranges = [LineRange(start_line=s.start_line, end_line=s.end_line) for s in sections]
    # Every reported section stays out of the chunks (the skill never
    # catalogues a glossary's own lines), but a glossary of ordinary terms is
    # not where abbreviations are listed, so only a listing section counts.
    # Both are judged on the sections that survived validation: a listing
    # reported outside the document is not evidence the section exists, so
    # its entries are not trusted as section definitions either.
    entries = result.entries if sections else []
    found = bool(sections) and (
        any(s.lists_abbreviations for s in sections) or bool(entries)
    )

    logger.info(
        f"[AbbreviationScanV2] Abbreviations section found={found}: "
        f"{[(r.start_line, r.end_line) for r in ranges]}, {len(entries)} entries"
    )
    return {
        "abbreviations_section_found": found,
        "abbreviations_section_ranges": ranges,
        "abbreviations_section_entries": entries,
        "messages": messages,
    }


def _valid_sections(
    sections: list[AbbreviationsSectionRange], total_lines: int
) -> list[AbbreviationsSectionRange]:
    """Clamp the agent's line numbers to the document, dropping impossible ranges."""
    valid: list[AbbreviationsSectionRange] = []
    for section in sections:
        start = max(section.start_line, 1)
        end = min(section.end_line, total_lines)
        if start > end:
            logger.warning(
                f"[AbbreviationScanV2] Ignoring section range {section.start_line}-"
                f"{section.end_line} outside a {total_lines}-line document"
            )
            continue
        valid.append(section.model_copy(update={"start_line": start, "end_line": end}))
    return valid


def after_section(state: AbbreviationScanV2State) -> str:
    """Go on to chunking, or end the run when the section could not be read.

    Without the section's result the section's own entries would be catalogued
    as body text, and every abbreviation would be reported "missing from
    Abbreviations section", alongside a false "No Abbreviations section found".
    Ending here leaves the node's error as the run's outcome and reports no
    issues, so the user retries instead of reading false ones.
    """
    failed = any(
        error.task_name == read_abbreviations_section_node.__name__
        and error.severity == WorkflowErrorSeverity.ERROR
        for error in state.errors
    )
    return END if failed else "prepare_chunks"
