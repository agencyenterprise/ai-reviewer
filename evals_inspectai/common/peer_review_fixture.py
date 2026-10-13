"""Project setup for the `review-assistant` e2e evals.

Every review-assistant output comes from one place, the Review Assistant: the
author names the outputs they want and hands over their documents unlabeled,
and one agent run works out what each document is. These evals reach it
through the same endpoints the Review Assistant tab calls:

1. create the project with the reviewed draft as its main document, running
   only `document_processing`, and wait for it;
2. upload every other document (reviewer memos, the revised draft, response
   memos) with the `review_input` role, which carries no label and no revision;
3. start a request naming the outputs and every document, and wait for it.

The order the documents are named in matters: the skill letters reviewers in
the order their documents are given, so memos go in the dataset's order.
"""

import logging
from typing import Any, NamedTuple

from evals_inspectai.common.api_client import (
    create_project_and_start_workflows,
    get_project_files,
    poll_until_complete,
    poll_workflow_run_until_complete,
    start_review_assistant_request,
    tus_upload_file,
)

logger = logging.getLogger(__name__)

_DOCUMENT_PROCESSING = "document_processing"
_REVIEW_INPUT_ROLE = "review_input"

DOCUMENT_PROCESSING_TIMEOUT_S = 900


class ReviewDocument(NamedTuple):
    """One document handed to the Review Assistant: its display name and bytes."""

    file_name: str
    content: str | bytes


async def build_review_project(
    main_file_name: str,
    main_markdown: str,
    documents: list[ReviewDocument],
    document_processing_timeout_s: float = DOCUMENT_PROCESSING_TIMEOUT_S,
) -> tuple[str, dict[str, str]]:
    """Create a project with the main document as its draft and upload the rest.

    Returns the project id and each document's file id by its file name. Names
    must be unique across the main document and ``documents``: the upload does
    not return an id, so a file is found again by its name.
    """
    names = [main_file_name, *(d.file_name for d in documents)]
    if len(set(names)) != len(names):
        raise ValueError(f"Document file names must be unique, got {names}")

    project_id = await create_project_and_start_workflows(
        file_content=main_markdown,
        file_name=main_file_name,
        workflow_types=[_DOCUMENT_PROCESSING],
    )
    await poll_until_complete(
        project_id=project_id,
        workflow_type=_DOCUMENT_PROCESSING,
        timeout_s=document_processing_timeout_s,
    )

    for document in documents:
        await tus_upload_file(
            project_id=project_id,
            file_name=document.file_name,
            content=document.content,
            role=_REVIEW_INPUT_ROLE,
        )

    ids_by_name = {f["file_name"]: str(f["id"]) for f in await get_project_files(project_id)}
    logger.info("Review project %s ready with %d document(s)", project_id, len(names))
    return project_id, ids_by_name


async def run_review_request(
    project_id: str,
    outputs: list[str],
    file_ids: list[str],
    timeout_s: float,
    poll_interval_s: float = 10,
) -> dict[str, Any]:
    """Start a Review Assistant request and return the completed run's detail."""
    run_id = await start_review_assistant_request(project_id, outputs, file_ids)
    return await poll_workflow_run_until_complete(
        run_id, timeout_s=timeout_s, interval_s=poll_interval_s
    )


async def run_review_assistant_request(
    draft: str,
    memos: list[ReviewDocument],
    output: str,
    timeout_s: float,
    revised_draft: str | None = None,
    response_memos: list[ReviewDocument] | None = None,
    # Neither name says which draft came first: the way a second download of
    # the same file is named, so the agent has to tell them apart by content,
    # as it does for an author's own files.
    draft_file_name: str = "report.md",
    revised_draft_file_name: str = "report (1).md",
    poll_interval_s: float = 10,
) -> dict[str, Any]:
    """Ask the Review Assistant for one output over a classic review cycle.

    The reviewed draft is the project's main document; the memos, the revised
    draft and the response memos are uploaded unlabeled. They are named in the
    request in that order (draft, memos in the order given, revised draft,
    response memos), so the reviewer letters follow the memos' order.

    Returns the completed run's WorkflowRunDetail dict.
    """
    if not memos:
        raise ValueError("A review cycle needs at least one reviewer memo")
    if response_memos and revised_draft is None:
        raise ValueError("response_memos describe a revised draft; pass revised_draft as well")
    if revised_draft is not None and revised_draft == draft:
        raise ValueError("revised_draft is identical to draft, so there is nothing to compare")

    rest = [
        *memos,
        *([ReviewDocument(revised_draft_file_name, revised_draft)] if revised_draft is not None else []),
        *(response_memos or []),
    ]
    project_id, ids_by_name = await build_review_project(draft_file_name, draft, rest)
    file_ids = [ids_by_name[draft_file_name], *(ids_by_name[d.file_name] for d in rest)]
    return await run_review_request(
        project_id, [output], file_ids, timeout_s=timeout_s, poll_interval_s=poll_interval_s
    )
