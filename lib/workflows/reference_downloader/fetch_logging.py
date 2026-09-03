"""Log lines for the reference downloader: one per reference, one per run.

Kept apart from the node so the node stays about control flow and this stays
about what a person reading the log needs to see.
"""

import logging
from collections import Counter
from typing import List, Optional

from langchain_core.messages import BaseMessage

from lib.workflows.reference_downloader.agents.reference_fetcher import (
    ReferenceFetchConclusion,
    ReferenceFetchItem,
)
from lib.workflows.reference_downloader.state import (
    ReferenceFetchResult,
    ReferenceFetchStatus,
)
from lib.workflows.reference_downloader.tool_usage import summarize_tool_usage

logger = logging.getLogger(__name__)

# How much of a reference to echo in a log line: enough to recognise it, not the
# whole bibliography entry.
REFERENCE_LOG_CHARS = 120


def short_reference(reference: str) -> str:
    return reference[:REFERENCE_LOG_CHARS]


def log_fetch_outcome(
    reference: str,
    result: Optional[ReferenceFetchItem],
    messages: List[BaseMessage],
) -> None:
    """One line per reference saying what was concluded and what it took."""
    usage = summarize_tool_usage(messages).describe()
    if result is None:
        logger.warning(
            "Reference %r: agent returned no result (%s)",
            short_reference(reference),
            usage,
        )
        return

    conclusion = result.final_conclusion.value
    detail = (
        f"conclusion={conclusion} source_url={result.source_url} "
        f"file_id={result.file_id} {usage}"
    )
    if result.final_conclusion == ReferenceFetchConclusion.SOURCE_FOUND:
        logger.info("Reference %r: %s", short_reference(reference), detail)
        return

    logger.warning(
        "Reference %r: %s reason=%r",
        short_reference(reference),
        detail,
        result.inaccessibility_reason,
    )


def log_run_summary(
    project_id: str, fetched_references: List[ReferenceFetchResult]
) -> None:
    """Tally the run so the headline is readable without counting lines."""
    outcomes: Counter[str] = Counter()
    for item in fetched_references:
        if item.status != ReferenceFetchStatus.COMPLETED:
            outcomes[item.status.value] += 1
        elif item.result is None:
            outcomes["no_result"] += 1
        else:
            outcomes[item.result.final_conclusion.value] += 1
    tally = ", ".join(f"{name}={count}" for name, count in sorted(outcomes.items()))
    logger.info(
        "Reference downloader summary for project %s: %d references (%s)",
        project_id,
        len(fetched_references),
        tally,
    )
