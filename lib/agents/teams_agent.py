"""Answering a question about a document, in a chat rather than a margin.

Replying inside a Word comment means writing into a pane that renders no markup and
rewards brevity above all. A question asked in Teams is the opposite: it is read in
a chat client, markdown renders, and the useful answer is sometimes a short list
rather than three sentences. So the reply guidance differs enough to warrant its own
prompt.

What does not differ is the construction, which is shared through
``lib/agents/deep_agent_setup.py``: once a document is open it is at ``/main.md``
with numbered paragraphs, the skills are available, and there is no internet.

The document is not chosen for the agent. A question from Teams may paste a link or
not, so opening one is the agent's job via ``open_document_for`` in
``lib/agents/tools/sharepoint.py``. A link is the only way in -- there is no lookup
by name -- so a question that names a document without linking to it gets a request
for the link. Skills are still mounted up front, because the skills middleware reads
them once before the run and a tool cannot add them later.

``graph_token`` is whose reading this run does. The tool is built from it per run, so
the agent inherits the asker's own access rather than the service's: a document they
cannot open is refused by Graph and the agent says so.

One Teams thread is one LangGraph thread, so a follow-up arrives with the earlier turns
in view. Its document does not: only the link persists, and every turn re-reads it as
whoever is asking then. Two reasons, either sufficient -- the document may have been
edited since, and a shared thread's next question may come from someone who cannot open
it. Re-reading is itself the permission check, since Graph applies that person's access.

Nothing here writes to the document. That is the point of this path -- a question
answered in chat needs no document access at all, which sidesteps both the 423 a
server-side write hits while someone is editing and the licensing questions around
automating a Word client.
"""

import logging
from collections.abc import Sequence
from typing import Any, Optional

from deepagents import create_deep_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langfuse import propagate_attributes
from pydantic import BaseModel, Field

from lib.agents.checkpointer import get_checkpointer
from lib.agents.deep_agent_setup import (
    DEFAULT_MODEL,
    RECURSION_LIMIT,
    build_llm,
    build_skill_files,
    tool_names,
)
from lib.agents.tools.sharepoint import (
    document_files,
    evict_document,
    mounted_document,
    open_document_for,
)
from lib.config.langfuse import langfuse_handler
from lib.config.llm_error_logger import ErrorLoggingCallback
from lib.config.llm_models import LLMModel
from lib.services.microsoft.graph import documents
from lib.services.microsoft.graph.client import redacted

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are Draft Detective, a document review assistant. Someone has asked you a \
question about a Word document from a chat, and you are answering them there.

## The conversation so far

You may be part-way through a conversation. Earlier questions and your own earlier \
answers are above, and any document this conversation is about is open and freshly \
re-read — so check what you already have before asking for something again. Because it \
is re-read every time, it may have changed since you last looked.

More than one person may be in this thread. Each question says who asked it; answer \
the person asking now, and do not assume they are the person who asked before.

## Getting the document

`open_document(url)` opens a document from a SharePoint link: it becomes available at \
`/main.md`, and any comments already on it at `/comments.md`. Read or search those \
files with your usual tools; the tool does not hand you the text.

Check whether a document is already open before asking for a link — on a follow-up \
there usually is one, and asking again for what you have is worse than useless.

**A link is the only way to reach a document.** You cannot look one up by name or \
title, and you must not guess at a URL. If someone asks about a document without \
linking to it, say you need the link and ask them to paste it — even when the name \
they used sounds unambiguous. This is deliberate: a link is something they already \
had access to, and searching on their behalf could reach documents they cannot open.

Open a document before answering anything about one. Never answer from a name or a \
file title alone, and never describe content you have not read.

Some questions need no document at all — what you can do, how you work. Answer \
those directly rather than asking for a link you do not need.

## Reading it

Every paragraph in `/main.md` is prefixed with its number, like `[12]`. Those \
numbers are not part of the text, and they are for your own navigation rather than \
for the reader: nobody can jump to paragraph 93 in Word.

## What you can and cannot reach

You can read this document and your own reference material. You have no access to \
the internet, and no way to run commands. This is deliberate: documents reviewed \
here are confidential, and the deployment does not allow outbound requests.

So when a request needs something only the internet could settle, say so plainly \
and stop. Verifying that a DOI resolves, checking whether a paper exists, \
confirming a URL: none of those are possible here. Say which specific check you \
cannot make, and where useful say what in the document would settle it instead. Do \
not guess, and do not imply you looked something up.

## You cannot change the document

You are answering a question, not editing. You cannot add comments, make tracked \
changes, or alter the text from here. If the answer is really a request to change \
something, say what you would change and where, and say plainly that it has to be \
applied in Word.

## Your review expertise

Your capabilities are described as skills under `/skills/`. Consult the ones \
relevant to what has been asked and ignore the rest. A question about a citation, \
for instance, is covered by `/skills/reference-validation/SKILL.md`. Do not read \
every skill; find the ones that apply.

## How to answer

Your last message is posted into the chat as it is, so write the answer itself as \
markdown — no JSON, no wrapper object, no preamble about what you are about to say. A \
list is often clearer than a paragraph. Still write like a colleague who has read the \
document:

- Answer the question that was actually asked. Nothing else.
- Point at places by quoting them, not by numbering them. A short distinctive \
phrase in quotation marks is something the reader can search for in Word; "[93]" is \
not. Quote the words at issue, and add the paragraph number in brackets afterwards \
only as a rough position.
- Be concrete about figures and claims: give the number or the wording you mean, \
not a description of it.
- Length should match the question. A yes-or-no question gets a sentence. "Check \
every citation" gets a list.
- If the document does not settle the question, say so plainly and say what would. \
Never invent a source, a figure or a citation.
- If you are confident something is wrong, say it directly. Hedging wastes time.
"""

REQUEST_PROMPT = """\
{who} asked:

{question}
{hint}"""

HINT_PREAMBLE = """
They linked to this document, so open it:

{hint}"""

# In the request rather than the system prompt: it is about this turn. Worded without
# asserting why -- a refusal and a timeout arrive the same way here, so claiming they lack
# access would sometimes be a confident falsehood about someone's permissions.
LOST_DOCUMENT_NOTICE = """
The document this conversation was about could not be opened for the person asking now, \
so it is no longer available to you. Do not answer from what was said about it earlier, \
and do not describe its contents. Say plainly that you could not open it as them -- they \
may not have access, or it may have moved -- and ask for a link they can open."""


def answer_text(messages: Sequence[BaseMessage]) -> str:
    """What the agent said this turn, as markdown. Empty if it said nothing.

    Read from the messages rather than through a structured ``response_format``. The
    answer is one markdown string, and asking for it as JSON made the model escape a
    whole review into a string literal -- tokens spent on backslashes, and a parse to
    fail.

    Stops at the most recent question, which a persisted thread makes load-bearing:
    without it, a turn that produced no text would reach back and re-post the previous
    turn's answer as though it were new.
    """

    for message in reversed(messages):
        if message.type == "human":
            break
        if message.type == "ai" and (text := str(message.text).strip()):
            return text
    return ""


class QuestionAnswer(BaseModel):
    """What the caller gets back, including how it failed if it did."""

    text: str
    model: Optional[str] = None
    steps: int = 0
    tools_used: list[str] = Field(default_factory=list)
    failed: bool = False
    error: Optional[str] = None


async def _document_for_this_turn(
    agent: Any,
    run_config: RunnableConfig,
    *,
    graph_token: str,
    document_hint: Optional[str],
) -> tuple[dict[str, Any], bool]:
    """Re-read the document this thread is about, as the person asking now.

    Returns the turn's ``files`` update and whether the document had to be given up;
    empty on a thread with nothing open. A re-read rather than a check on the cached copy
    because the document may have been edited, and because re-reading *is* the permission
    check -- Graph applies this person's own access.

    Any failure gives the document up. Fail-closed on purpose: a 403 and a timeout are
    indistinguishable from here, and the wrong guess costs someone else's confidentiality
    in one direction and a re-paste in the other.
    """

    snapshot = await agent.aget_state(run_config)
    url = mounted_document(snapshot.values.get("files"))
    if not url:
        return {}, False

    if document_hint and document_hint != url:
        # They linked to something else, so the agent will open that instead. The old
        # document goes now rather than lingering as a copy nobody re-read.
        logger.info("this turn links elsewhere, so %s is closed", redacted(url))
        return evict_document(), False

    try:
        document = await documents.load(url, token=graph_token)
    except Exception as error:  # noqa: BLE001 - every failure ends the same way
        logger.info("could not re-open %s for the asker: %s", redacted(url), error)
        return evict_document(), True

    logger.info("re-opened %s as the asker for this turn", redacted(url))
    return document_files(document, url), False


async def answer_question(
    question: str,
    graph_token: str,
    thread_id: str,
    document_hint: Optional[str] = None,
    asked_by: str = "Someone",
    model: LLMModel = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    user_id: Optional[str] = None,
) -> QuestionAnswer:
    """Answer a question about a document the agent opens for itself.

    ``graph_token`` is the identity the document is read with -- the asker's own,
    under Teams SSO. Required rather than optional: the alternative would be reading
    as the service, which is exactly the privilege this path is meant not to have.

    ``thread_id`` keys both the checkpoint and the Langfuse session, deliberately under
    one name so a conversation is findable in the trace view under what it is stored as.
    Required: a caller with nothing to continue passes a fresh id rather than opting out,
    which would be a second path where the document is never re-read.

    ``document_hint`` is a link found in the message, when there was one. Without it the
    agent falls back on whatever the conversation already has open.

    Never raises: a failure comes back as ``failed`` so the caller can decide whether to
    say anything.
    """

    # Langfuse discards propagated metadata that is not a string, so these are
    # stringified rather than silently going missing from the trace.
    metadata: dict[str, Any] = {
        "langfuse_tags": ["teams-agent", "document-question"],
        "had_link": str(bool(document_hint)),
        # The same id the checkpoint is keyed by, so a conversation can be found in the
        # trace view under what it is stored as.
        "langfuse_session_id": thread_id,
    }
    if user_id:
        metadata["langfuse_user_id"] = user_id

    run_config: RunnableConfig = {
        "run_name": "teams_agent",
        "recursion_limit": RECURSION_LIMIT,
        "callbacks": [langfuse_handler, ErrorLoggingCallback()],
        "metadata": metadata,
        # The checkpointer and this are a pair: LangGraph refuses a checkpointer with no
        # ``configurable`` to key it by.
        "configurable": {"thread_id": thread_id},
    }

    try:
        async with get_checkpointer() as saver:
            agent = create_deep_agent(
                model=build_llm(model, api_key),
                tools=[open_document_for(graph_token)],
                skills=["/skills/"],
                system_prompt=SYSTEM_PROMPT,
                checkpointer=saver,
            )

            document, lost = await _document_for_this_turn(
                agent,
                run_config,
                graph_token=graph_token,
                document_hint=document_hint,
            )

            hint = HINT_PREAMBLE.format(hint=document_hint) if document_hint else ""
            prompt = REQUEST_PROMPT.format(
                who=asked_by, question=question.strip(), hint=hint
            )
            if lost:
                prompt += LOST_DOCUMENT_NOTICE

            with propagate_attributes(user_id=user_id):
                result = await agent.ainvoke(
                    {
                        # Skills, and the thread's document as of now. Skills must be
                        # mounted up front because a tool cannot add them later; the
                        # re-mount each turn is the same paths and content.
                        "files": {**build_skill_files(), **document},
                        "messages": [HumanMessage(content=prompt)],
                    },
                    config=run_config,
                )
    except Exception as error:  # noqa: BLE001 - the caller decides what to do
        logger.exception("Draft Detective could not answer a question")
        return QuestionAnswer(
            text="", model=model.model_name, failed=True, error=str(error)
        )

    messages = result.get("messages", [])
    text = answer_text(messages)
    if not text:
        logger.warning("the question agent returned an empty answer")
        return QuestionAnswer(
            text="",
            model=model.model_name,
            steps=len(messages),
            tools_used=tool_names(messages),
            failed=True,
            error="the agent returned an empty answer",
        )

    return QuestionAnswer(
        text=text,
        model=model.model_name,
        steps=len(messages),
        tools_used=tool_names(messages),
    )
