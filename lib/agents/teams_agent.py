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

Nothing here writes to the document. That is the point of this path -- a question
answered in chat needs no document access at all, which sidesteps both the 423 a
server-side write hits while someone is editing and the licensing questions around
automating a Word client.
"""

import logging
from typing import Any, Optional

from deepagents import create_deep_agent
from langchain.agents.structured_output import AutoStrategy
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langfuse import propagate_attributes
from pydantic import BaseModel, Field

from lib.agents.deep_agent_setup import (
    DEFAULT_MODEL,
    RECURSION_LIMIT,
    build_llm,
    build_skill_files,
    tool_names,
)
from lib.agents.tools.sharepoint import open_document_for
from lib.config.langfuse import langfuse_handler
from lib.config.llm_error_logger import ErrorLoggingCallback
from lib.config.llm_models import LLMModel

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are Draft Detective, a document review assistant. Someone has asked you a \
question about a Word document from a chat, and you are answering them there.

## Getting the document

No document is open when you start. `open_document(url)` opens one from a SharePoint \
link: it becomes available at `/main.md`, and any comments already on it at \
`/comments.md`. Read or search those files with your usual tools; the tool does not \
hand you the text.

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

You are writing in a chat, so markdown renders and a list is often clearer than a \
paragraph. Still write like a colleague who has read the document:

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


class QuestionReply(BaseModel):
    """The structured answer, so an empty reply is detectable rather than posted."""

    answer: str = Field(description="The answer, as markdown, for a chat client")


class QuestionAnswer(BaseModel):
    """What the caller gets back, including how it failed if it did."""

    text: str
    model: Optional[str] = None
    steps: int = 0
    tools_used: list[str] = Field(default_factory=list)
    failed: bool = False
    error: Optional[str] = None


async def answer_question(
    question: str,
    graph_token: str,
    document_hint: Optional[str] = None,
    asked_by: str = "Someone",
    model: LLMModel = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> QuestionAnswer:
    """Answer a question about a document the agent opens for itself.

    ``graph_token`` is the identity the document is read with -- the asker's own,
    under Teams SSO. Required rather than optional: the alternative would be reading
    as the service, which is exactly the privilege this path is meant not to have.

    ``document_hint`` is a link found in the message, when there was one. Without it
    the agent has no way to reach a document and will ask for the link, so this is
    what makes a question about a document answerable at all.

    ``thread_id`` groups a conversation's traces in Langfuse, so a follow-up in the
    same Teams thread reads as one session. Never raises: a failure comes back as
    ``failed`` so the caller can decide whether to say anything.
    """

    hint = HINT_PREAMBLE.format(hint=document_hint) if document_hint else ""
    prompt = REQUEST_PROMPT.format(
        who=asked_by, question=question.strip(), hint=hint
    )

    # Langfuse discards propagated metadata that is not a string, so these are
    # stringified rather than silently going missing from the trace.
    metadata: dict[str, Any] = {
        "langfuse_tags": ["teams-agent", "document-question"],
        "had_link": str(bool(document_hint)),
    }
    if thread_id:
        metadata["langfuse_session_id"] = thread_id
    if user_id:
        metadata["langfuse_user_id"] = user_id

    run_config: RunnableConfig = {
        "run_name": "teams_agent",
        "recursion_limit": RECURSION_LIMIT,
        "callbacks": [langfuse_handler, ErrorLoggingCallback()],
        "metadata": metadata,
    }

    try:
        agent = create_deep_agent(
            model=build_llm(model, api_key),
            tools=[open_document_for(graph_token)],
            response_format=AutoStrategy(QuestionReply),
            skills=["/skills/"],
        )
        with propagate_attributes(user_id=user_id):
            result = await agent.ainvoke(
                {
                    # Skills only: the document arrives via open_document, and skills
                    # cannot be added mid-run.
                    "files": build_skill_files(),
                    "messages": [
                        SystemMessage(content=SYSTEM_PROMPT),
                        HumanMessage(content=prompt),
                    ],
                },
                config=run_config,
            )
    except Exception as error:  # noqa: BLE001 - the caller decides what to do
        logger.exception("Draft Detective could not answer a question")
        return QuestionAnswer(
            text="", model=model.model_name, failed=True, error=str(error)
        )

    messages = result.get("messages", [])
    structured = result.get("structured_response")
    text = (structured.answer if structured else "").strip()
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
