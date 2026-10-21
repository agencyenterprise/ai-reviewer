"""Project setup for the `review-assistant` e2e evals.

Every review-assistant output comes from one place, the Review Assistant: the
author names the outputs they want and hands over their documents unlabeled,
and one agent run works out what each document is. These evals reach it
through the same endpoints the Review Assistant tab calls:

1. create the project with the reviewed draft as its main document, running
   only `document_processing`, and wait for it;
2. upload every other document (reviewer memos, marked-up copies, the revised
   draft, response memos) with the `review_input` role, which carries no label
   and no revision;
3. start a request naming the outputs and every document, and wait for it.

`review_assistant_solver` runs those steps for a sample, and `memo_document`
reads a memo the way every suite's dataset gives it.

The order the documents are named in matters: the skill letters reviewers in
the order their documents are given, so memos go in the dataset's order.
"""

import json
import logging
from pathlib import Path
from typing import Any, NamedTuple

from inspect_ai.model import ModelOutput
from inspect_ai.solver import Generate, Solver, TaskState, solver

from evals_inspectai.common.api_client import (
    create_project_and_start_workflows,
    get_project_files,
    poll_until_complete,
    poll_workflow_run_until_complete,
    start_review_assistant_request,
    tus_upload_file,
)
from evals_inspectai.common.api_solver import surface_conversations
from evals_inspectai.common.docx_fixture import MarkedUpCopy, with_byline
from evals_inspectai.common.loaders import resolve_input
from evals_inspectai.common.model_override import output_model_name

logger = logging.getLogger(__name__)

_WORKFLOW = "review_assistant"
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

    ids_by_name = {
        f["file_name"]: str(f["id"]) for f in await get_project_files(project_id)
    }
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


# Neither name says which draft came first: the way a second download of the
# same file is named, so the agent has to tell them apart by content, as it does
# for an author's own files.
DRAFT_FILE_NAME = "report.md"
REVISED_DRAFT_FILE_NAME = "report (1).md"


def expected_input_roles(
    memo_names: list[str],
    revised: bool = False,
    response_names: list[str] | None = None,
    marked_up_names: list[str] | None = None,
) -> dict[str, str]:
    """What the agent should take each uploaded document to be, by file name.

    The roles are the ones the Review Assistant's prompt asks the agent to
    record for every document; `input_identification` compares against them.
    """
    roles = {DRAFT_FILE_NAME: "original draft"}
    roles.update(dict.fromkeys(memo_names, "reviewer memo"))
    roles.update(dict.fromkeys(marked_up_names or [], "marked-up draft"))
    if revised:
        roles[REVISED_DRAFT_FILE_NAME] = "revised draft"
    roles.update(dict.fromkeys(response_names or [], "response memo"))
    return roles


async def run_review_assistant_request(
    draft: str,
    memos: list[ReviewDocument],
    outputs: list[str],
    timeout_s: float,
    revised_draft: str | None = None,
    response_memos: list[ReviewDocument] | None = None,
    marked_up: list[ReviewDocument] | None = None,
    poll_interval_s: float = 10,
) -> dict[str, Any]:
    """Ask the Review Assistant for some outputs over a classic review cycle.

    The reviewed draft is the project's main document; the memos, any
    marked-up copies, the revised draft and the response memos are uploaded
    unlabeled. They are named in the request in that order, so the reviewer
    letters follow the memos' order, with a commenter after them.

    Returns the completed run's WorkflowRunDetail dict.
    """
    if not memos and not marked_up:
        raise ValueError(
            "A review cycle needs reviewer feedback: a memo or a marked-up copy"
        )
    if response_memos and revised_draft is None:
        raise ValueError(
            "response_memos describe a revised draft; pass revised_draft as well"
        )
    if revised_draft is not None and revised_draft == draft:
        raise ValueError(
            "revised_draft is identical to draft, so there is nothing to compare"
        )

    rest = [
        *memos,
        *(marked_up or []),
        *(
            [ReviewDocument(REVISED_DRAFT_FILE_NAME, revised_draft)]
            if revised_draft is not None
            else []
        ),
        *(response_memos or []),
    ]
    project_id, ids_by_name = await build_review_project(DRAFT_FILE_NAME, draft, rest)
    file_ids = [ids_by_name[DRAFT_FILE_NAME], *(ids_by_name[d.file_name] for d in rest)]
    return await run_review_request(
        project_id,
        outputs,
        file_ids,
        timeout_s=timeout_s,
        poll_interval_s=poll_interval_s,
    )


def memo_document(entry: str | dict) -> dict[str, str]:
    """A memo's display name and text; a mapping may sign it with a `byline`.

    The memo is a `file://` reference, and its file name is carried through as
    its display name on upload.
    """
    ref = entry if isinstance(entry, str) else entry["source"]
    text = resolve_input(ref)
    if isinstance(entry, dict) and entry.get("byline"):
        text = with_byline(text, entry["byline"])
    return {"file_name": Path(ref.removeprefix("file://")).name, "content": text}


def _documents(memos: list[dict[str, str]]) -> list[ReviewDocument]:
    return [ReviewDocument(m["file_name"], m["content"]) for m in memos]


@solver
def review_assistant_solver(timeout_s: float, poll_interval_s: float = 10) -> Solver:
    """Ask the Review Assistant for the sample's outputs over its documents.

    The reviewed draft is the sample input; the rest comes from metadata:
    `memos`, and when the sample has them `revised_draft`, `response_memos`
    and `marked_up` copies. The outputs are `outputs` when the sample asks for
    several, else its one `output`.

    A custom solver rather than the shared `api_workflow_agent` because the
    documents have to be uploaded alongside the draft and named in the request.
    """

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata or {}
        run_detail = await run_review_assistant_request(
            draft=state.input_text,
            memos=_documents(meta["memos"]),
            outputs=meta.get("outputs", [meta["output"]]),
            timeout_s=timeout_s,
            revised_draft=meta.get("revised_draft"),
            response_memos=_documents(meta.get("response_memos", [])),
            marked_up=[
                ReviewDocument(m.file_name, m.content())
                for m in map(MarkedUpCopy.model_validate, meta.get("marked_up", []))
            ],
            poll_interval_s=poll_interval_s,
        )
        workflow_state = run_detail.get("state") or {}

        # Hand the agent's own conversation to Inspect, the same way the shared
        # `api_workflow_agent` does: lifted out of the state dict so the
        # completion the scorers parse stays just the workflow result.
        await surface_conversations(state, workflow_state, _WORKFLOW)

        state.output = ModelOutput(
            completion=json.dumps(workflow_state), model=output_model_name(run_detail)
        )
        return state

    return solve
