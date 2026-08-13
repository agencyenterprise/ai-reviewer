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

Which document to read is not decided here. Every link in the message is passed along as
a candidate and the agent opens what it needs, because which one is meant depends on what
was asked. A link is the only way in: naming a document without linking to it gets a
request for the link, because searching on someone's behalf could reach documents they
cannot open.

Two other transports were tried and removed. An outgoing webhook needed a Workflows
flow to post answers and could only reply in a separate message. A transport-neutral
``/ask`` endpoint outlived its purpose once the bot was the only caller.
"""

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response

from lib.agents.teams_agent import answer_question
from lib.services.microsoft.graph import client as graph
from lib.services.microsoft.graph.client import redacted
from lib.services.microsoft.teams import bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["microsoft", "teams"])

# A detached task is only weakly referenced by the event loop, so without this the
# answer can be garbage collected mid-flight.
_running: set[asyncio.Task[None]] = set()

APOLOGY = "I could not work that one out, sorry."


def _finished(task: "asyncio.Task[None]") -> None:
    """Retire a detached task, and make sure a failure in one cannot vanish.

    Discarding the reference without reading the result is what asyncio calls an
    unretrieved exception: it surfaces as a warning at interpreter shutdown, if at all,
    while the person who was told "I will follow up here shortly" waits forever.

    This is a backstop rather than the handler. ``_answer_into_thread`` catches its own
    failures, because that is where the conversation is still reachable and something
    can be said. Reaching here means the failure was outside even that -- a
    ``BaseException``, or a fault in the apology itself.
    """

    _running.discard(task)
    try:
        task.result()
    except asyncio.CancelledError:
        # Shutdown cancelling in-flight work is not a fault.
        pass
    except Exception:  # noqa: BLE001 - a lost answer must not also be a silent one
        logger.exception("a detached answer task failed after the turn ended")


def _invoke_response(invoked: Any) -> Response:
    """An invoke's reply, as the channel expects to read it.

    ``InvokeResponse.body`` is typed ``object``, so it is serialised defensively: the
    SDK hands back a plain dict today, having round-tripped its own model through
    ``model_dump``, but a model or anything else must not become a 500 on a path whose
    whole job is to report a status accurately.

    ``by_alias`` is what makes that branch protocol-correct rather than merely
    non-crashing. The SDK's models carry a camelCase alias generator and do not
    serialise by alias, so a plain dump would emit ``connection_name`` where the wire
    format says ``connectionName``.
    """

    if invoked.body is None:
        return Response(status_code=invoked.status)

    body = invoked.body
    if hasattr(body, "model_dump"):
        body = body.model_dump(exclude_unset=True, by_alias=True)
    return Response(
        content=json.dumps(body, default=str),
        status_code=invoked.status,
        media_type="application/json",
    )


async def _graph_token(context: Any) -> str:
    """The identity this turn's document reading is done with.

    The one place the choice is made, so it can be read in one go. Under a configured
    user-auth connection the token is the asker's, obtained by the SDK before the
    handler ran; otherwise it is the service's own, which is wider than any one user.
    There is deliberately no fallback from the first to the second: a missing user
    token is an error, not a reason to read as the service.
    """

    if bot.reads_as_the_user():
        return await bot.user_token(context)
    return await graph.access_token()


async def _answer_into_thread(
    reference: Any,
    question: str,
    author: str,
    conversation: str,
    document_urls: list[str],
    graph_token: str,
) -> None:
    """Ask, and post the answer back into the thread the question came from.

    No document is loaded here, and none is chosen. The links found in the message go
    along as candidates and the agent opens what it needs -- which also means a document
    that is missing, not allowed, or not readable *by the person asking* comes back as
    something the agent can explain, rather than as an exception this function has to
    translate.

    Detached from the request, so nothing here can return an error to a caller. A
    failure is posted into the conversation instead: leaving someone waiting for a
    reply that never arrives is worse than telling them it went wrong. The person has
    already been told an answer is coming, so *every* way out of this function ends in
    something being said -- which is why the raise is handled here, where the
    conversation is still in reach, rather than only in the task's done callback.
    """

    try:
        answer = await answer_question(
            question=question,
            graph_token=graph_token,
            # The Teams conversation *is* the agent's thread, which is what makes a
            # follow-up here a follow-up there. In a channel this id already carries a
            # ``;messageid=`` suffix per reply chain, so separate chains are separate
            # conversations without anything having to parse it.
            thread_id=conversation,
            document_urls=document_urls,
            asked_by=author,
            user_id=author,
        )
    except Exception:  # noqa: BLE001 - nobody upstream to hand this to
        # ``answer_question`` reports a failure rather than raising, so arriving here
        # means something outside its own guard broke. Truncated like the request log:
        # a question can quote the document, and what is reviewed here is confidential.
        logger.exception("could not answer %r", question[:120])
        await bot.post_later(reference, APOLOGY)
        return

    if answer.failed:
        logger.error("could not answer %r: %s", question[:120], answer.error)
        await bot.post_later(reference, APOLOGY)
        return

    await bot.post_later(reference, answer.text)


@bot.on_question
async def _on_question(context: Any, state: Any) -> None:
    """Acknowledge a question and hand the answering off.

    Registered on the bot's application at import rather than per request, so it must
    close over nothing belonging to one request. By the time this runs the SDK has
    already obtained a user token if one is required, which is why asking for it here
    cannot block.
    """

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
    await context.send_activity("Looking at that now — I will follow up here shortly.")

    # From the activity, not the question: Teams shows a pasted link as a
    # hyperlink and keeps the href out of the text entirely. All of them, because
    # choosing between them is the agent's job.
    document_urls = bot.document_urls_in(context.activity)
    logger.info(
        "Teams bot question from %s: %r (links: %s, reading as %s)",
        author,
        question[:120],
        ", ".join(redacted(url) for url in document_urls) or "none found",
        "the asker" if bot.reads_as_the_user() else "the service",
    )
    if not document_urls and ".doc" in question.lower():
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

    # Fetched inside the turn, while the context that carries the signed-in user is
    # still available, and handed to the detached task rather than looked up there.
    try:
        graph_token = await _graph_token(context)
    except bot.NotSignedIn as error:
        logger.error("no user token for %s: %s", author, error)
        await context.send_activity(
            "I could not confirm your access to SharePoint, so I have not read "
            "anything. Try signing in again, or ask an admin to check the bot's "
            "sign-in connection."
        )
        return

    # Detached rather than a FastAPI background task: the answer is posted
    # proactively, so it does not belong to this request's lifecycle, and the handler
    # must not depend on anything the request owns.
    task = asyncio.create_task(
        _answer_into_thread(
            bot.reference_for(context.activity),
            question,
            author,
            conversation,
            document_urls,
            graph_token,
        )
    )
    _running.add(task)
    task.add_done_callback(_finished)


@router.post("/messages")
async def bot_messages(
    request: Request,
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

    try:
        invoked = await bot.handle(authorization, body)
    except bot.NotConfigured as error:
        logger.error("the Teams bot is not configured: %s", error)
        raise HTTPException(
            status_code=503, detail="The bot is not configured"
        ) from error
    except PermissionError as error:
        logger.warning("a bot request failed token validation: %s", error)
        raise HTTPException(status_code=401, detail="Unauthorized") from error
    except bot.InvalidActivity as error:
        # 400 rather than 500 on purpose: the Connector retries a 5xx, and a payload
        # this SDK will not parse will not parse on the retry either. Logged at error
        # because the cost of the correct answer is that the message is dropped -- most
        # likely from schema drift between the Bot service and our pinned SDK, which
        # would otherwise be invisible.
        logger.error("could not parse a bot activity: %s", error)
        raise HTTPException(status_code=400, detail="Malformed activity") from error
    except Exception as error:  # noqa: BLE001 - the Connector retries on a 5xx
        logger.exception("could not process a bot activity")
        raise HTTPException(status_code=500, detail="Could not process") from error

    if invoked is not None:
        # An invoke -- a `signin/*` among them -- is answered with the status and body
        # the SDK produced, not with a blanket 200. That reply is part of the protocol:
        # a token exchange that needs consent comes back as 412 carrying a
        # TokenExchangeInvokeResponse, which Teams reads as "fall back to the sign-in
        # card". Swallowing it would tell Teams the exchange succeeded, and sign-in
        # would stall with nothing to show for it.
        return _invoke_response(invoked)

    # For everything else the Connector wants an empty 200; a body it would treat as
    # a payload.
    return Response(status_code=200)
