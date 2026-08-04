"""Answering questions about a document from outside Word.

A request arriving from a Teams channel has no Word session to borrow, so the
service loads the document itself. That works: Graph serves what SharePoint last
persisted, which is current when nobody is editing and trails a live edit by under
a second.

Read-only, deliberately. A whole-file write back is refused with 423 while anyone
has the document open, whatever identity asks, so this path answers in chat and
never touches the document. Requests that really need a comment or a tracked change
belong to the add-in, which is the only client that can write into a live session.

One way in: ``/messages``, the bot's endpoint. It authenticates with the token the
Bot Connector presents, acknowledges immediately, and posts the answer into the same
thread about a minute later.

Which document to read is not decided here. A link in the message is passed along as
a hint and the agent opens it itself. A link is the only way in: naming a document
without linking to it gets a request for the link, because searching on someone's
behalf could reach documents they cannot open.

Two other transports were tried and removed. An outgoing webhook needed a Workflows
flow to post answers and could only reply in a separate message. A transport-neutral
``/ask`` endpoint outlived its purpose once the bot was the only caller.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response

from lib.agents.teams_agent import answer_question
from lib.services.microsoft.teams import bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["microsoft", "teams"])


async def _answer_into_thread(
    reference: Any,
    question: str,
    author: str,
    conversation: str,
    document_hint: Optional[str],
) -> None:
    """Ask, and post the answer back into the thread the question came from.

    The document is not loaded here. The link is part of the question, so the agent
    opens it through its own tool -- which also means a document that is missing or
    not allowed comes back as something the agent can explain, rather than as an
    exception this function has to translate.

    A background task, so nothing here can return an error to a caller. A failure is
    posted into the conversation instead: leaving someone waiting for a reply that
    never arrives is worse than telling them it went wrong.
    """

    answer = await answer_question(
        question=question,
        document_hint=document_hint,
        asked_by=author,
        thread_id=conversation,
        user_id=author,
    )
    if answer.failed:
        # Truncated like the request log: a question can quote the document, and
        # what is reviewed here is confidential.
        logger.error("could not answer %r: %s", question[:120], answer.error)
        await bot.post_later(reference, "I could not work that one out, sorry.")
        return

    await bot.post_later(reference, answer.text)


@router.post("/messages")
async def bot_messages(
    request: Request,
    background: BackgroundTasks,
    authorization: Optional[str] = Header(default=None),
) -> Response:
    """The bot's messaging endpoint, called by the Bot Connector.

    The turn acknowledges and ends; the answer follows about a minute later into
    the same thread. Keeping the request short is what lets Teams show a reply
    immediately instead of waiting on the model.

    Outside ``get_current_user``: the Bot Connector presents its own token, which
    the Agents SDK validates. That token is the authentication.
    """

    body = await request.json()

    async def on_message(context: Any) -> None:
        question = bot.question_from(context)
        author = (
            context.activity.from_property.name
            if context.activity.from_property
            else "someone"
        )
        conversation = (
            context.activity.conversation.id if context.activity.conversation else ""
        )

        if not question:
            await context.send_activity(
                "Mention me with a question about the document and I will take a look."
            )
            return

        await bot.send_typing(context)
        await context.send_activity(
            "Looking at that now — I will follow up here shortly."
        )

        # From the activity, not the question: Teams shows a pasted link as a
        # hyperlink and keeps the href out of the text entirely.
        document_url = bot.document_url_in(context.activity)
        logger.info(
            "Teams bot question from %s: %r (document: %s)",
            author,
            question[:120],
            document_url or "none found",
        )
        if not document_url and ".doc" in question.lower():
            # Someone named a document but no href was found anywhere in the activity.
            # Teams keeps a rendered hyperlink's href in an attachment rather than in
            # the text, and which attachment depends on how the link was shared, so
            # what is logged is the shapes that were present. Deliberately not the
            # payload: it carries the message body and the sender's ids, and the
            # documents discussed here are confidential.
            logger.warning(
                "a message named a document but carried no link; attachments were: %s",
                [
                    attachment.content_type
                    for attachment in context.activity.attachments or []
                ],
            )

        background.add_task(
            _answer_into_thread,
            bot.reference_for(context.activity),
            question,
            author,
            conversation,
            document_url,
        )

    try:
        await bot.handle(authorization, body, on_message)
    except bot.NotConfigured as error:
        logger.error("the Teams bot is not configured: %s", error)
        raise HTTPException(
            status_code=503, detail="The bot is not configured"
        ) from error
    except PermissionError as error:
        logger.warning("a bot request failed token validation: %s", error)
        raise HTTPException(status_code=401, detail="Unauthorized") from error
    except Exception as error:  # noqa: BLE001 - the Connector retries on a 5xx
        logger.exception("could not process a bot activity")
        raise HTTPException(status_code=500, detail="Could not process") from error

    # The Connector wants an empty 200; anything else it treats as a payload.
    return Response(status_code=200)
