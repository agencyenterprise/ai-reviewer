"""Reading SharePoint documents with the service's own identity.

Draft Detective is asked about documents from places that have no Word session to
borrow -- a Teams channel, most of all -- so the backend has to load them itself.
This is the app-only half of that: a client-credentials token, resolving a
SharePoint URL to a drive item, and downloading its bytes.

Which documents may be read is decided by ``GRAPH_ALLOWED_HOSTS`` and
``GRAPH_ALLOWED_SITE_PATHS``, and the order the two are applied in matters: see
``resolve``. A sharing link has no path to check, only an opaque identifier, so the
site is checked against what Graph resolves rather than against what was pasted.

Two things were established by probing a real tenant rather than from documentation:

- A delegated token is refused when Conditional Access requires a compliant device
  (AADSTS530035). A server has no device identity, so app-only is not a shortcut
  here, it is the only option.
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
from urllib.parse import unquote, urlparse

import httpx

from lib.config.env import config

logger = logging.getLogger(__name__)

GRAPH = "https://graph.microsoft.com/v1.0"
_TOKEN_MARGIN_SECONDS = 120

# The ``/:w:/r/`` that "Copy link" puts in front of an otherwise ordinary path.
_SHARING_PREFIX = re.compile(r"^/:[a-z]:/[a-z]/", re.I)

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

    So the query string always goes. A path is kept when it is an ordinary
    site-relative one, since that is the part worth having when a read is refused and
    it names no secret. An opaque sharing path is reduced to its shape:

    >>> redacted("https://x.sharepoint.com/:w:/r/sites/Reviews/Drafts/a.docx?e=1")
    'https://x.sharepoint.com/:w:/r/sites/Reviews/Drafts/a.docx'
    >>> redacted("https://x.sharepoint.com/:w:/s/Reviews/EWabc123?e=xyz")
    'https://x.sharepoint.com/:w:/s/[redacted]'
    """

    parsed = urlparse(url)
    if not parsed.netloc:
        return "[unparseable url]"

    prefix = _SHARING_PREFIX.match(parsed.path)
    remainder = _SHARING_PREFIX.sub("", parsed.path).lstrip("/")
    if prefix and not remainder.lower().startswith(("sites/", "personal/")):
        # Nothing here is a path -- it is the share id itself.
        return f"{parsed.scheme}://{parsed.netloc}{prefix.group(0)}[redacted]"
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


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


async def resolve(url: str) -> dict[str, Any]:
    """The drive item for a SharePoint URL, if this service may read it.

    ``/shares`` is the documented shortcut and works app-only; walking site then
    path is the fallback, because a URL that has been through a chat message does
    not always decode back to the exact stored name.

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
    token = await access_token()
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

    site = await client.get(f"{GRAPH}/sites/{parsed.netloc}:/{parts[0]}/{parts[1]}")
    if site.status_code != 200:
        raise GraphError(
            f"could not resolve the site: {site.status_code} {site.text[:200]}"
        )
    site_id = site.json()["id"]

    # parts[2] is the document library; the rest is the path inside its drive.
    within = "/".join(parts[3:])
    item = await client.get(f"{GRAPH}/sites/{site_id}/drive/root:/{within}")
    if item.status_code != 200:
        raise GraphError(f"could not find {within!r}: {item.status_code}")
    return dict(item.json())


async def download(item: dict[str, Any]) -> bytes:
    """The document's bytes as SharePoint last persisted them.

    ``/content`` answers 302 with a short-lived pre-authenticated URL. That URL is
    fetched without our bearer token: it carries its own authorisation, and sending
    ours to a storage host would put it somewhere other than Graph.
    """

    token = await access_token()
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
