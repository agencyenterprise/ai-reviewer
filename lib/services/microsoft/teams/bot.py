"""Draft Detective as a Teams bot.

The webhook prototype worked but cost too many manual steps and could only answer
in a separate message. A bot gets the proper thing: its own identity and icon,
replies threaded under the question, typing indicators, and it works in channels,
group chats and one-to-one alike.

Built on the Microsoft 365 Agents SDK. ``botbuilder-python`` is end of life -- the
repository was archived in January 2026 -- and this is its supported successor.
Only ``hosting-core`` is used, not ``hosting-aiohttp``: the core does not depend on
a web framework, so the FastAPI route in
``lib/api/routers/microsoft/teams.py`` stays ours while the SDK handles the part
worth not hand-rolling, which is validating the token Teams presents.

Answering takes about a minute, far longer than the request should stay open. So a
turn acknowledges and ends, and the answer is delivered afterwards through
``process_proactive`` against the conversation reference, which is what puts it in
the same thread rather than in a new message.

**Whose access the bot reads with is configured here, and it is a security decision
rather than a preference.** With ``TEAMS_USER_AUTH_CONNECTION`` set, the SDK obtains a
token for the person who asked before the question is answered, so the bot can reach
nothing they could not. Without it the service reads app-only -- a tenant-wide grant,
bounded only by the Graph allowlist, which means anyone able to mention the bot could
have it read a document they have no access to themselves.

One thing the user token does *not* solve: the answer is posted into the conversation
the question came from, so in a channel it is visible to everyone in that channel,
access to the document or not. Gating the read closes "I cannot open it, so I will ask
the bot"; it does not close "someone who can open it asks somewhere I can see".
"""

import html
import json
import logging
import re
from collections.abc import Awaitable, Iterator
from typing import Any, Callable, Optional

from microsoft_agents.activity import Activity, ActivityTypes, ConversationReference
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.core import (
    AgentApplication,
    AgentAuthConfiguration,
    ApplicationOptions,
    AuthenticationConstants,
    AuthHandler,
    Authorization,
    AuthTypes,
    ChannelServiceAdapter,
    ClaimsIdentity,
    JwtTokenValidator,
    MemoryStorage,
    RestChannelServiceClientFactory,
    TurnContext,
)
from pydantic import ValidationError

from lib.config.env import config

logger = logging.getLogger(__name__)

# The SDK looks this key up by name and refuses to build without it.
CONNECTION = "SERVICE_CONNECTION"
BOT_AUDIENCE = "https://api.botframework.com"

# The id the sign-in route refers to. One handler: read a document as the asker.
GRAPH_HANDLER = "graph"

# What the application calls for a message. The second argument is the SDK's turn
# state, which this bot does not use -- its own state lives in Langfuse and the thread.
QuestionHandler = Callable[[TurnContext, Any], Awaitable[None]]

_question_handler: Optional[QuestionHandler] = None


async def _dispatch(context: TurnContext, state: Any) -> None:
    """The route the application holds, resolving the handler when a message arrives.

    Indirect on purpose. Baking the handler into the route at build time would make
    building the bot depend on the router having been imported first, and the failure
    would be an exception on a live request rather than at startup.
    """

    if _question_handler is None:
        logger.error(
            "a message arrived with no question handler registered; the Teams router "
            "was not imported"
        )
        return
    await _question_handler(context, state)

# Backslash is excluded along with the quotes: a URL never contains one, and these
# are read out of JSON and HTML where it is the escape character.
_SHAREPOINT_URL = re.compile(r"https://[\w.-]+\.sharepoint\.com/[^\s<>\"'\\]+", re.I)

# Teams' preview endpoints sit on the same host as the document itself, so a card's
# thumbnail would otherwise be taken for the thing it is a picture of.
_NOT_A_DOCUMENT = ("getpreview.ashx", "thumbnail.ashx", "/_api/", "/_vti_")


class NotConfigured(Exception):
    """Raised when the bot's credentials are absent, so it cannot be trusted."""


class InvalidActivity(Exception):
    """Raised when the body is not an activity this SDK will parse.

    Its own type so the route can answer 400 rather than 500, and that distinction is
    the same one that already matters for a bad token: the Bot Connector retries a 5xx
    and gives up on a 4xx. A payload we cannot parse will not parse on the retry
    either, so a 500 here turns one malformed -- or merely newer -- activity into
    sustained load. ``Activity`` is strict enough for that to be a live risk: it once
    rejected all thirty fields of an activity this codebase built itself.
    """


class NotSignedIn(Exception):
    """Raised when a user token is needed and there is none.

    Deliberately not a fallback to the service's own identity: reading as the app on
    behalf of someone who has not proved they may read is the exact confusion this
    path exists to avoid.
    """


def _auth_configuration() -> AgentAuthConfiguration:
    if not config.TEAMS_BOT_APP_ID or not config.TEAMS_BOT_APP_PASSWORD:
        raise NotConfigured(
            "TEAMS_BOT_APP_ID and TEAMS_BOT_APP_PASSWORD must be set before the bot "
            "can accept a request"
        )
    return AgentAuthConfiguration(
        auth_type=AuthTypes.client_secret,
        client_id=config.TEAMS_BOT_APP_ID,
        client_secret=config.TEAMS_BOT_APP_PASSWORD,
        # Only for a single-tenant bot; a multi-tenant one must not pin an authority.
        tenant_id=config.TEAMS_BOT_TENANT_ID or None,
    )


def reads_as_the_user() -> bool:
    """Whether a document is read with the asker's identity rather than the service's.

    Configuration decides, because the two are not interchangeable and the difference
    is a security property rather than a preference. With a connection configured the
    bot can reach nothing the person asking could not. Without one it reads app-only,
    which is wider than any single user and bounded only by the Graph allowlist.
    """

    return bool(config.TEAMS_USER_AUTH_CONNECTION)


def _user_auth_handler() -> AuthHandler:
    """The sign-in the SDK runs before a question is answered.

    ``abs_oauth_connection_name`` names a connection configured on the *Azure Bot
    resource*, not here -- the client id and secret for it live in Azure, so a leak of
    this service's environment does not hand over the ability to ask for user tokens.
    """

    return AuthHandler(
        name=GRAPH_HANDLER,
        title="Sign in",
        text="Sign in so I can read the document as you rather than as the service.",
        auth_type="userauthorization",
        abs_oauth_connection_name=config.TEAMS_USER_AUTH_CONNECTION or "",
        scopes=[
            scope.strip()
            for scope in config.TEAMS_USER_AUTH_SCOPES.split(",")
            if scope.strip()
        ],
    )


class _Bot:
    """The adapter, validator and turn application, built once and reused.

    Held lazily rather than at import: the credentials may be absent in a
    deployment that does not run the bot, and that should not stop the service
    starting.

    Turn handling is ``AgentApplication``'s rather than ours, and that is what buys
    the sign-in flow. Declaring ``auth_handlers`` on the route makes the SDK obtain a
    user token *before* the handler runs: it posts the sign-in card, parks the original
    question, handles the ``signin/tokenExchange`` or ``signin/verifyState`` invoke
    that comes back, and then replays the question. Driving that by hand would mean
    reaching into private SDK internals, which this codebase has been bitten by twice.
    """

    def __init__(self) -> None:
        self._adapter: Optional[ChannelServiceAdapter] = None
        self._validator: Optional[JwtTokenValidator] = None
        self._app: Optional[AgentApplication] = None
        self._authorization: Optional[Authorization] = None

    def _build(self) -> None:
        if self._adapter is not None:
            return
        auth = _auth_configuration()
        connections = MsalConnectionManager(
            connections_configurations={CONNECTION: auth}
        )
        self._adapter = ChannelServiceAdapter(
            RestChannelServiceClientFactory(connections)
        )
        self._validator = JwtTokenValidator(auth)

        # Sign-in bookkeeping only, and only for the length of a flow: the refresh
        # token itself is held by the Bot Framework token service, never by us. In
        # process memory it is lost on restart, which costs a user mid-sign-in one
        # more click and costs a signed-in user nothing.
        storage = MemoryStorage()
        self._authorization = Authorization(
            storage=storage,
            connection_manager=connections,
            auth_handlers={GRAPH_HANDLER: _user_auth_handler()},
        )
        self._app = AgentApplication(
            ApplicationOptions(
                adapter=self._adapter,
                bot_app_id=config.TEAMS_BOT_APP_ID or "",
                storage=storage,
                # The mention is stripped by the SDK, which reads the entity metadata
                # Teams sends rather than guessing from the markup.
                remove_recipient_mention=True,
                # Ours is sent explicitly alongside the acknowledgement instead.
                start_typing_timer=False,
            ),
            authorization=self._authorization,
        )
        self._app.message(
            re.compile(r"(?s).*"),
            # The whole feature, in one argument. Present, the SDK will not run the
            # handler until it holds a token for this user.
            auth_handlers=[GRAPH_HANDLER] if reads_as_the_user() else None,
        )(_dispatch)

        logger.info(
            "Teams bot ready for app id %s, reading documents as %s",
            config.TEAMS_BOT_APP_ID,
            "the asking user" if reads_as_the_user() else "the service (app-only)",
        )

    @property
    def adapter(self) -> ChannelServiceAdapter:
        self._build()
        assert self._adapter is not None
        return self._adapter

    @property
    def application(self) -> AgentApplication:
        self._build()
        assert self._app is not None
        return self._app

    async def user_token(self, context: TurnContext) -> str:
        """The asker's Graph token for this turn.

        Only reached once the SDK has completed the sign-in flow, so an absent token
        here means something is misconfigured rather than that the user has not signed
        in yet -- and it must not fall back to the service's identity, which would
        silently undo the whole arrangement.
        """

        self._build()
        assert self._authorization is not None
        response = await self._authorization.get_token(context, GRAPH_HANDLER)
        if not response or not response.token:
            raise NotSignedIn(
                "no user token after the sign-in flow completed; check that the "
                f"{config.TEAMS_USER_AUTH_CONNECTION!r} connection on the Azure Bot "
                "grants the delegated Graph scopes this bot asks for"
            )
        return str(response.token)

    async def claims_for(self, authorization: Optional[str]) -> ClaimsIdentity:
        """Who sent this, according to the token Teams presented.

        Raises if the token is missing or does not verify. This is the only thing
        standing between the endpoint and anyone who can reach it, which is why it
        is the SDK's job and not ours.
        """

        if not authorization or not authorization.lower().startswith("bearer "):
            raise PermissionError("no bearer token")
        self._build()
        assert self._validator is not None
        try:
            return await self._validator.validate_token(
                authorization.split(" ", 1)[1].strip()
            )
        except PermissionError:
            raise
        except Exception as error:
            # A token the SDK will not accept is a refusal, not a server fault. The
            # difference matters: the Bot Connector retries a 5xx and gives up on a
            # 401, so mislabelling this produces a retry storm.
            raise PermissionError(f"token rejected: {error}") from error


bot = _Bot()


def on_question(handler: QuestionHandler) -> QuestionHandler:
    """Register the one thing this bot does, as a decorator.

    Registered here rather than passed per request because the route lives on the
    application, which is built once. A handler that closed over anything belonging to
    a single request would leak that request's state into every later one.
    """

    global _question_handler
    _question_handler = handler
    return handler


async def user_token(context: TurnContext) -> str:
    """The Graph token for whoever asked, once the SDK has signed them in.

    Module-level for the same reason ``handle`` is: callers should not have to know
    that the adapter and the application hang off one lazily built object.
    """

    return await bot.user_token(context)


def question_from(context: TurnContext) -> str:
    """The question, as asked.

    The mention of the bot is already gone: ``remove_recipient_mention`` is set on the
    application, and the SDK reads the entity metadata Teams sends rather than guessing
    from the markup. What is left to do is normalise the whitespace that leaves behind.
    """

    return " ".join((context.activity.text or "").split()).strip()


def _scannable(activity: Activity) -> Iterator[str]:
    """Every part of a message that could carry a link, most faithful first.

    ``activity.text`` is only the *visible* text. Teams renders a pasted link as a
    hyperlink whose anchor is the file name, and the href does not appear there at
    all -- so a message that plainly contains a link arrives looking like a bare file
    name. The href survives in the attachments Teams sends alongside: the message's
    own HTML, and the card it unfurls a SharePoint link into.
    """

    yield activity.text or ""
    for attachment in activity.attachments or []:
        content = attachment.content
        if isinstance(content, str):
            yield content
        elif content is not None:
            # Shape-agnostic on purpose. Teams has several card types for a file and
            # the href sits under a different key in each, so the whole card is
            # scanned rather than one guessed-at field.
            yield json.dumps(content, default=str)
        if attachment.content_url:
            yield attachment.content_url


def document_url_in(activity: Activity) -> Optional[str]:
    """A SharePoint link to a document in this message, if there is one.

    Trailing punctuation is trimmed: Teams decorates a pasted link, and an href in
    HTML arrives escaped, so the match is cleaned rather than used raw.
    """

    for text in _scannable(activity):
        for match in _SHAREPOINT_URL.finditer(html.unescape(text)):
            url = match.group(0).rstrip(").,;'\"")
            if any(marker in url.lower() for marker in _NOT_A_DOCUMENT):
                continue
            return url
    return None


def reference_for(activity: Activity) -> ConversationReference:
    """Where to send the answer so it lands under the question."""

    return activity.get_conversation_reference()


async def send_typing(context: TurnContext) -> None:
    """Show that something is happening, since the answer is a minute away."""

    try:
        await context.send_activity(Activity(type=ActivityTypes.typing))
    except Exception as error:  # noqa: BLE001 - cosmetic, never worth failing for
        logger.debug("could not send a typing indicator: %s", error)


async def post_later(reference: ConversationReference, text: str) -> None:
    """Send a message into a conversation after its turn has ended.

    Never raises: by this point the request has been answered and there is nobody
    to return an error to, so a failure is logged instead.
    """

    async def deliver(context: TurnContext) -> None:
        await context.send_activity(Activity(type=ActivityTypes.message, text=text))

    # Used as returned, not round-tripped through model_dump/model_validate:
    # model_dump emits None for every unset optional field, and validating that
    # back fails on all thirty of them.
    continuation = TurnContext.apply_conversation_reference(
        Activity(type=ActivityTypes.event, name="continue"),
        reference,
        is_incoming=False,
    )
    # The adapter needs to know who is sending, since there is no inbound request
    # to infer it from.
    identity = ClaimsIdentity(
        claims={
            AuthenticationConstants.AUDIENCE_CLAIM: config.TEAMS_BOT_APP_ID or "",
            AuthenticationConstants.APP_ID_CLAIM: config.TEAMS_BOT_APP_ID or "",
        },
        is_authenticated=True,
    )

    try:
        await bot.adapter.process_proactive(
            identity, continuation, BOT_AUDIENCE, deliver
        )
        logger.info("posted a follow-up to Teams (%s chars)", len(text))
    except Exception as error:  # noqa: BLE001
        logger.error("could not post the follow-up to Teams: %s", error)


async def handle(authorization: Optional[str], body: dict[str, Any]) -> Optional[Any]:
    """Authenticate and dispatch one activity.

    Everything past authentication is the application's: it routes messages to the
    registered handler, drives any sign-in in progress, and accepts and ignores what
    the bot does not act on -- which is what stops Teams retrying membership and typing
    events forever.

    The ``signin/*`` invokes that complete a sign-in arrive here like any other
    activity, and must reach the application rather than being filtered out, or the
    flow never finishes.
    """

    claims = await bot.claims_for(authorization)
    try:
        activity = Activity.model_validate(body)
    except ValidationError as error:
        # Distinguished from a server fault so the route can answer 400. Retrying an
        # unparseable payload cannot help, and the Connector retries a 5xx.
        raise InvalidActivity(str(error)) from error

    return await bot.adapter.process_activity(claims, activity, bot.application.on_turn)
