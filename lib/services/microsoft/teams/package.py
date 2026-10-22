"""The Teams app package that installs Draft Detective as a bot.

Teams installs a bot from a zip holding a manifest and two icons. The API builds it on
request (``GET /api/microsoft/teams/package.zip``) from this deployment's settings, so an
admin downloads it and uploads it to the Teams admin center
(``docs/microsoft-integrations.md``, part 3.7) with nothing to build or edit.

The app id is the bot's (``TEAMS_BOT_APP_ID``), which keeps the two from drifting apart:
Teams recognises an upload by it. The version is the application's own, so each release
raises it, and Teams refuses an update that does not.
"""

import io
import json
import tomllib
import zipfile
from functools import cache
from pathlib import Path

ICONS = Path(__file__).parent / "icons"
PYPROJECT = Path(__file__).resolve().parents[4] / "pyproject.toml"

BOT_NAME = "Draft Detective"
DESCRIPTION_SHORT = "Ask about a Word document without leaving Teams."
DESCRIPTION_LONG = (
    "Draft Detective reads a Word document from SharePoint and answers questions "
    "about it here: what it claims, whether it overclaims, whether its citations "
    "hold up. Mention it with a question, and paste a document link to ask about a "
    "particular file. It reads only and never changes the document; comments and "
    "tracked changes are made by the Word add-in instead."
)

# 1.17 is broadly supported. A newer schema buys nothing for a bot-only app and
# risks being rejected by an older client.
MANIFEST_VERSION = "1.17"

COMMANDS = [
    ("Does this overclaim?", "Look for claims the document does not support"),
    ("Check the citations", "Check references against what the text says"),
    ("Summarise the argument", "What the document argues, and where"),
]


def manifest(bot_id: str, version: str, frontend_url: str) -> dict:
    scopes = ["personal", "team", "groupChat"]
    return {
        "$schema": (
            "https://developer.microsoft.com/en-us/json-schemas/teams/v1.17/"
            "MicrosoftTeams.schema.json"
        ),
        "manifestVersion": MANIFEST_VERSION,
        "version": version,
        "id": bot_id,
        # Teams requires all three links. They point at this deployment: its About page
        # says how documents are handled, and there is no separate terms page.
        "developer": {
            "name": BOT_NAME,
            "websiteUrl": frontend_url,
            "privacyUrl": f"{frontend_url}/about",
            "termsOfUseUrl": f"{frontend_url}/about",
        },
        "name": {"short": BOT_NAME, "full": f"{BOT_NAME} document review"},
        "description": {"short": DESCRIPTION_SHORT, "full": DESCRIPTION_LONG},
        "icons": {"color": "color.png", "outline": "outline.png"},
        "accentColor": "#0F6CBD",
        "bots": [
            {
                "botId": bot_id,
                "scopes": scopes,
                "supportsFiles": False,
                "isNotificationOnly": False,
                "commandLists": [
                    {
                        "scopes": scopes,
                        "commands": [
                            {"title": title, "description": description}
                            for title, description in COMMANDS
                        ],
                    }
                ],
            }
        ],
        "permissions": ["identity", "messageTeamMembers"],
        # Private channel support reached standard tenants in January 2026 and has
        # to be opted into here. Note the platform still restricts what a bot may
        # do there: posting a message or Adaptive Card into a private channel
        # conversation is documented as unsupported, and the follow-up answer is
        # sent proactively, so it is the part most likely to be refused.
        "supportedChannelTypes": ["privateChannels", "sharedChannels"],
        # There are no tabs or embedded content here, so this looks like it should be
        # empty -- and it was, which broke sign-in. The OAuthCard's button opens a link
        # on the Bot Framework token service, and Teams will not open a domain the
        # manifest has not declared. The failure names neither: it reads "this action
        # can't be performed since the app does not exist or has been uninstalled".
        "validDomains": ["token.botframework.com"],
    }


@cache
def app_version() -> str:
    """The application's version, as the release workflow sets it in pyproject.toml."""

    with PYPROJECT.open("rb") as file:
        return str(tomllib.load(file)["project"]["version"])


def package(bot_id: str, frontend_url: str) -> bytes:
    """The zip Teams installs: the manifest and the two icons Teams requires.

    The icons are the site's favicon (``frontend/app/icon.svg``), committed as PNGs:
    Teams rejects a package whose icons are the wrong size (192 and 32 pixels). The
    colour icon is a full square, since Teams rounds its corners itself; the outline must
    be opaque white on transparency, so it is the mark alone.
    """

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        document = manifest(bot_id, app_version(), frontend_url.rstrip("/"))
        archive.writestr("manifest.json", json.dumps(document, indent=2))
        archive.write(ICONS / "color.png", "color.png")
        archive.write(ICONS / "outline.png", "outline.png")
    return buffer.getvalue()
