"""Reading SharePoint documents through Graph.

Draft Detective is asked about documents from places that have no Word session to
borrow -- a Teams channel, most of all -- so the backend has to load them itself:
resolving a SharePoint URL to a drive item, and downloading its bytes.

**Whose identity does the reading is the caller's decision, and it is not optional.**
``resolve`` and ``download`` take a bearer token rather than reaching for one, so a
call site cannot fall back to the service's own identity by forgetting to say. Two
tokens are possible and they are not equivalent:

- A **user** token, obtained through Teams SSO. Graph then applies that person's own
  permissions, so a document they cannot open comes back 403 or 404. This is the only
  arrangement in which the bot is not a more privileged reader than the person asking.
- The **app-only** token from ``access_token()``. Tenant-wide unless narrowed to
  ``Sites.Selected``, so it can read documents the asker could not, which is why the
  allowlist below exists at all.

Which documents may be read is decided by ``GRAPH_ALLOWED_HOSTS`` and
``GRAPH_ALLOWED_SITE_PATHS``, and the order the two are applied in matters: see
``resolve``. A sharing link has no path to check, only an opaque identifier, so the
site is checked against what Graph resolves rather than against what was pasted.
These stay in force under a user token too -- narrower than the user's own access,
and defence in depth rather than the only boundary.

Two things were established by probing a real tenant rather than from documentation:

- A delegated token acquired *from the server* is refused when Conditional Access
  requires a compliant device (AADSTS530035), because a server has no device
  identity. A token acquired through Teams SSO comes from the user's own client, so
  it is not the same case -- see ``lib/services/microsoft/teams/bot.py``.
- Graph serves whatever SharePoint last persisted. Under AutoSave that trails a
  live edit by about half a second, but with nobody editing it is simply current.

Writing is deliberately absent. A whole-file PUT is refused with 423 while anyone
has the document open, whatever identity asks, so writes belong to a Word client --
see ``lib/services/microsoft/word/word_package.py`` and the add-in.
"""

import base64
import logging
import re
import time
from typing import Any, Optional
from urllib.parse import quote, unquote, urlparse

import httpx

from lib.config.env import config

logger = logging.getLogger(__name__)

GRAPH = "https://graph.microsoft.com/v1.0"
_TOKEN_MARGIN_SECONDS = 120

# The ``/:w:/r/`` that "Copy link" puts in front of an otherwise ordinary path. The
# second letter is the *form*, and it decides whether what follows is a path at all.
_SHARING_PREFIX = re.compile(r"^/:[a-z]:/(?P<form>[a-z])/", re.I)

# Of the forms Microsoft emits, only ``r`` ("resource") embeds the document's real
# path. ``s``, ``g``, ``p`` and ``u`` carry an opaque share id in its place. Anything
# unrecognised is treated as opaque as well, so a form added later fails safe.
_PATH_BEARING_FORM = "r"

_cached_token: Optional[tuple[str, float]] = None


class GraphError(Exception):
    """Raised when Graph will not give us what we asked for."""


class DocumentNotAllowed(GraphError):
    """Raised when a document is outside the sites this service may read.

    The app-only grant is tenant-wide unless narrowed to ``Sites.Selected``, so
    without this the service would happily read any file in the organisation --
    including ones the person asking cannot open themselves.
    """


def _allowed_hosts() -> list[str]:
    raw = config.GRAPH_ALLOWED_HOSTS or ""
    return [host.strip().lower() for host in raw.split(",") if host.strip()]


def _allowed_site_paths() -> list[str]:
    raw = config.GRAPH_ALLOWED_SITE_PATHS or ""
    return [path.strip().lower() for path in raw.split(",") if path.strip()]


def _site_relative_path(url: str) -> str:
    """A URL's path with any sharing prefix stripped.

    "Copy link" in Word and Teams produces ``/:w:/r/sites/X/...`` rather than the
    plain ``/sites/X/...``. Same site, same document; only the prefix differs, and
    comparing without removing it would refuse the very link someone pasted from
    Word itself.

    Case is preserved, because this is also used to address Graph and a document
    library's name is not case-insensitive there. Callers comparing against the
    allowlist lower it themselves.
    """

    return _SHARING_PREFIX.sub("/", urlparse(url).path)


def redacted(url: str) -> str:
    """A SharePoint URL with the part that grants access removed, for logging.

    A sharing link is a bearer credential rather than merely an address: an "anyone
    with the link" URL is openable by whoever holds it, and what makes that work is
    the ``?e=`` token in the query string together with the opaque id in a
    ``/:w:/s/Site/EWabc...`` path.

    That matters for logs specifically because logs *widen* the audience. The link was
    already visible to one Teams channel; a log record reaches ops dashboards and
    whatever aggregator ships them, none of whom were in that channel.

    So the query string always goes. What survives is decided by the sharing *form*
    rather than by what the path looks like: only ``r`` embeds a real path, which is
    worth keeping because it is the part that tells you where a refused read pointed
    and it names no secret. Every other form is reduced to its shape.

    Keying on the form matters. An earlier version exempted any path beginning
    ``sites/`` or ``personal/``, which handed back the share id in
    ``/:w:/g/personal/<user>/EWabc...`` -- an OneDrive share link, where those segments
    precede the credential rather than replacing it.

    >>> redacted("https://x.sharepoint.com/:w:/r/sites/Reviews/Drafts/a.docx?e=1")
    'https://x.sharepoint.com/:w:/r/sites/Reviews/Drafts/a.docx'
    >>> redacted("https://x.sharepoint.com/:w:/g/personal/carlos/EWabc123?e=xyz")
    'https://x.sharepoint.com/:w:/g/[redacted]'
    """

    parsed = urlparse(url)
    if not parsed.netloc:
        return "[unparseable url]"

    # Any userinfo goes with it. A SharePoint link never carries one, but a log record
    # is the last place a stray credential should turn up.
    host = parsed.netloc.rsplit("@", 1)[-1]

    prefix = _SHARING_PREFIX.match(parsed.path)
    if prefix and prefix.group("form").lower() != _PATH_BEARING_FORM:
        # What follows the prefix is the share id, whatever it happens to look like.
        return f"{parsed.scheme}://{host}{prefix.group(0)}[redacted]"
    return f"{parsed.scheme}://{host}{parsed.path}"


def _is_addressable(segment: str) -> bool:
    """Whether a decoded path segment names one thing rather than moving the path.

    Read after ``unquote``, which is the point: ``%2F`` and ``%5C`` become separators
    only once decoded, so a segment written as ``Drafts%2F..%2FSecret.docx`` arrives
    here as three. Interpolated into a Graph URL it would address a document the link
    did not name.

    Refused rather than repaired. SharePoint permits neither a separator nor a
    bare dot-segment in a name, so a link that needs one is not a link to a document.
    Control characters go too -- a newline in a log record is its own problem.
    """

    if segment in (".", ".."):
        return False
    if "/" in segment or "\\" in segment:
        return False
    return not any(ord(character) < 0x20 for character in segment)


def check_host(url: str) -> None:
    """Refuse a host this service may not read from at all.

    The tenant boundary, and the one check cheap enough to make before anything is
    resolved. Fails closed: an unset allowlist reads nothing rather than everything,
    because the app-only grant is tenant-wide.
    """

    hosts = _allowed_hosts()
    if not hosts:
        raise DocumentNotAllowed(
            "GRAPH_ALLOWED_HOSTS is not set, so no document may be read. Set it to "
            "the SharePoint hosts this service is allowed to load from."
        )

    netloc = urlparse(url).netloc.lower()
    if netloc not in hosts:
        raise DocumentNotAllowed(f"{netloc} is not an allowed SharePoint host")


def check_site(url: str) -> None:
    """Refuse a document outside the configured sites.

    Belongs on a document's *canonical* ``webUrl``, not on whatever was pasted. A
    sharing link is deliberately opaque -- "Copy link" produces ``/:w:/s/X/EWabc...``,
    in which the site does not appear at all -- so checking the pasted string either
    refuses a legitimate link or, worse, invites pattern-matching an identifier that
    was never meant to be read.

    There is deliberately no helper that runs this together with ``check_host``. The
    two are separated *because* they belong at different points, and a convenience
    wrapper taking one URL is exactly the thing that would put the site check back on
    the pasted link. ``resolve`` is the only caller and owns the ordering.
    """

    paths = _allowed_site_paths()
    if not paths:
        return

    path = _site_relative_path(url).lower()
    if not any(path.startswith(p) for p in paths):
        raise DocumentNotAllowed(
            f"{urlparse(url).path} is outside the site paths this service may read"
        )


async def access_token() -> str:
    """An app-only Graph token, cached until shortly before it expires."""

    global _cached_token
    if _cached_token and _cached_token[1] > time.time() + _TOKEN_MARGIN_SECONDS:
        return _cached_token[0]

    missing = [
        name
        for name in ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_CLIENT_SECRET")
        if not getattr(config, name, None)
    ]
    if missing:
        raise GraphError(f"Graph is not configured: {', '.join(missing)} unset")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://login.microsoftonline.com/{config.AZURE_TENANT_ID}"
            "/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": config.AZURE_CLIENT_ID,
                "client_secret": config.AZURE_CLIENT_SECRET,
                "scope": "https://graph.microsoft.com/.default",
            },
        )
    body = response.json()
    token = body.get("access_token")
    if not token:
        raise GraphError(
            f"could not get a Graph token: {body.get('error')} "
            f"{str(body.get('error_description'))[:200]}"
        )
    _cached_token = (str(token), time.time() + float(body.get("expires_in", 3600)))
    return str(token)


def _share_id(url: str) -> str:
    """Graph's encoding for "the item at this URL"."""

    encoded = base64.b64encode(url.encode("utf-8")).decode("ascii")
    return "u!" + encoded.rstrip("=").replace("/", "_").replace("+", "-")


async def resolve(url: str, *, token: str) -> dict[str, Any]:
    """The drive item for a SharePoint URL, if this identity may read it.

    ``token`` is whose reading this is, and it is required rather than defaulted:
    under a user token Graph refuses a document that person cannot open, which is the
    real permission check, and a call site that could silently fall back to app-only
    would lose it.

    ``/shares`` is the documented shortcut and works with either identity; walking
    site then path is the fallback, because a URL that has been through a chat message
    does not always decode back to the exact stored name.

    The two allowlist checks straddle the resolve, deliberately. The host is checked
    first, before any call. The *site* is checked afterwards, against the item's own
    ``webUrl``: a sharing link carries an opaque identifier instead of a path, so the
    pasted string cannot answer which site the document is in -- only Graph can. This
    is the stricter order as well as the working one, since it authorises the document
    that was actually found rather than the string someone typed.

    What the resolve itself can reveal before that check is a name and a path, to a
    caller who already held a working link to the document. No content is read.
    """

    check_host(url)
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=60, headers=headers) as client:
        item = await _resolve_item(client, url)

    canonical = str(item.get("webUrl") or url)
    logger.info("resolved %s to %s", redacted(url), redacted(canonical))
    check_host(canonical)
    check_site(canonical)
    return item


async def _resolve_item(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    """The drive item, by whichever route Graph will give it up. No authorisation."""

    shared = await client.get(f"{GRAPH}/shares/{_share_id(url)}/driveItem")
    if shared.status_code == 200:
        return dict(shared.json())
    logger.info(
        "/shares did not resolve %s (%s)", redacted(url), shared.status_code
    )

    parsed = urlparse(url)
    # The sharing prefix has to go before the path is read as a path: "Copy link"
    # produces ``/:w:/r/sites/X/...``, whose first segment is ``:w:`` rather than
    # ``sites``, so this branch used to refuse a link the other branch handles fine.
    # An opaque ``/:w:/s/Site/EWabc...`` link is still beyond it -- there is no path
    # in one to walk -- and that is what ``/shares`` above is for.
    parts = [unquote(p) for p in _site_relative_path(url).split("/") if p]
    if len(parts) < 4 or parts[0].lower() != "sites":
        raise GraphError(f"cannot read a site and path out of {parsed.path}")

    unaddressable = [part for part in parts if not _is_addressable(part)]
    if unaddressable:
        # ``repr`` rather than the raw value: this is attacker-controlled text on its
        # way into a log, and a control character in one is how a log gets forged.
        logger.warning("refusing a link with unaddressable segments: %r", unaddressable)
        raise GraphError("that link's path cannot be addressed safely")

    site = await client.get(
        f"{GRAPH}/sites/{parsed.netloc}:/{quote(parts[0])}/{quote(parts[1])}"
    )
    if site.status_code != 200:
        raise GraphError(
            f"could not resolve the site: {site.status_code} {site.text[:200]}"
        )
    site_id = site.json()["id"]

    # parts[2] is the document library; the rest is the path inside its drive. Each
    # segment is re-encoded rather than interpolated raw, because a decoded ``#`` or
    # ``?`` in a file name ends the path component and would silently address
    # something else -- httpx reads them as a fragment and a query respectively.
    within = "/".join(quote(part, safe="") for part in parts[3:])
    item = await client.get(f"{GRAPH}/sites/{site_id}/drive/root:/{within}")
    if item.status_code != 200:
        raise GraphError(f"could not find {within!r}: {item.status_code}")
    return dict(item.json())


async def download(item: dict[str, Any], *, token: str) -> bytes:
    """The document's bytes as SharePoint last persisted them.

    Takes the same identity that resolved the item, so a user token is still the one
    fetching the content rather than only the metadata.

    ``/content`` answers 302 with a short-lived pre-authenticated URL. That URL is
    fetched without our bearer token: it carries its own authorisation, and sending
    ours to a storage host would put it somewhere other than Graph.
    """

    url = item.get("@microsoft.graph.downloadUrl")

    async with httpx.AsyncClient(timeout=180) as client:
        if not url:
            drive = item["parentReference"]["driveId"]
            redirect = await client.get(
                f"{GRAPH}/drives/{drive}/items/{item['id']}/content",
                headers={"Authorization": f"Bearer {token}"},
                follow_redirects=False,
            )
            url = redirect.headers.get("location")
            if not url:
                raise GraphError(
                    f"no download URL for {item.get('name')}: {redirect.status_code}"
                )
        response = await client.get(url, follow_redirects=True)

    if response.status_code != 200:
        raise GraphError(f"could not download {item.get('name')}: {response.status_code}")
    return response.content
