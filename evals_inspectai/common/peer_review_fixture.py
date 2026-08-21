"""Project setup for the peer-review (`review-assistant`) e2e evals.

The three `review-assistant` workflows (revision-planning summary, reviewer
response memos, reviewer coverage report) need more project state than the
other e2e evals: alongside the draft they need one or more files with the
`reviewer_memo` role, attached to the revision the reviewers reviewed. That
state cannot be created by `/api/start-analysis`, which only assigns the MAIN
and SUPPORT roles, so the memos go up through TUS afterwards.

The sequence is:

1. create the project with the reviewed draft as its main document, running
   only `document_processing`;
2. wait for that to finish, so memo uploads do not race the conversion of the
   main document;
3. upload each reviewer memo with `role=reviewer_memo` against revision 1;
4. start the target workflow and wait for it.

Step 4 is separate from step 1 on purpose: the workflows short-circuit through
their `precheck` when no reviewer memos exist, so the target workflow must not
be started until the memos are in place.

Reviewer response memos and the coverage report additionally need a *revised*
draft in a second revision. That step is not implemented here yet; it belongs
in this module when those suites land.
"""

import logging
from typing import Any, NamedTuple

from evals_inspectai.common.api_client import (
    poll_until_complete,
    start_workflow_types,
    tus_upload_file,
    upload_and_start_analysis,
)

logger = logging.getLogger(__name__)

_DOCUMENT_PROCESSING = "document_processing"
_REVIEWER_MEMO_ROLE = "reviewer_memo"

# The reviewed revision. Every project this fixture builds has exactly one
# revision, so the memos always attach to revision 1.
REVIEWED_REVISION = 1

DOCUMENT_PROCESSING_TIMEOUT_S = 900


class ReviewerMemo(NamedTuple):
    """One reviewer memo to attach to the reviewed revision."""

    file_name: str
    content: str


async def setup_peer_review_project(
    draft: str,
    memos: list[ReviewerMemo],
    draft_file_name: str = "eval-draft.md",
    document_processing_timeout_s: float = DOCUMENT_PROCESSING_TIMEOUT_S,
) -> str:
    """Create a project holding a reviewed draft plus its reviewer memos.

    Args:
        draft: Markdown of the draft the reviewers reviewed.
        memos: Reviewer memos, in the order the reviewers should be lettered
            (the first is reviewer A, the second B, and so on).
        draft_file_name: Display name for the main document.
        document_processing_timeout_s: How long to wait for the initial
            `document_processing` run.

    Returns:
        The project_id, with memos uploaded and no analysis workflow started.
    """
    if not memos:
        raise ValueError("A peer-review project needs at least one reviewer memo")

    project_id = await upload_and_start_analysis(
        file_content=draft,
        file_name=draft_file_name,
        workflow_types=[_DOCUMENT_PROCESSING],
    )

    await poll_until_complete(
        project_id=project_id,
        workflow_type=_DOCUMENT_PROCESSING,
        timeout_s=document_processing_timeout_s,
    )

    for memo in memos:
        await tus_upload_file(
            project_id=project_id,
            file_name=memo.file_name,
            content=memo.content,
            role=_REVIEWER_MEMO_ROLE,
            revision=REVIEWED_REVISION,
        )

    logger.info(
        "Peer-review project %s ready with %d reviewer memo(s)",
        project_id,
        len(memos),
    )
    return project_id


async def run_review_assistant_workflow(
    project_id: str,
    workflow_type: str,
    timeout_s: float,
    poll_interval_s: float = 5,
) -> dict[str, Any]:
    """Start one review-assistant workflow on a prepared project and await it.

    Returns the completed run's WorkflowRunDetail dict.
    """
    await start_workflow_types(project_id, [workflow_type])
    return await poll_until_complete(
        project_id=project_id,
        workflow_type=workflow_type,
        timeout_s=timeout_s,
        interval_s=poll_interval_s,
    )
