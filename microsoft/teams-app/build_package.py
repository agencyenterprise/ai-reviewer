"""Build the Teams app package that installs Draft Detective as a bot.

Teams installs a bot from a zip holding a manifest and two icons. The manifest is
generated rather than committed with the ids baked in, because the bot's app id and
the tenant come from the environment and a manifest with someone else's ids in it is
a confusing thing to find in a repository.

    uv run python microsoft/teams-app/build_package.py [version]

Writes ``draft-detective-teams.zip`` next to this script. Upload it in Teams via
Apps > Manage your apps > Upload a custom app, which the tenant has to allow.

The version matters on every upload after the first. Teams identifies an app by the
``id`` in its manifest, so re-uploading the same id is refused with "this app has
already been submitted in your org". To change an installed app, raise the version
and use the update action rather than uploading it as new.

Two ids are easy to confuse, and the admin centre shows the wrong one first:

- **ID do aplicativo externo / External app ID** -- this is ``manifest.id``, and the
  one that must match on an update.
- **ID do Aplicativo / App ID** -- Teams' own catalog id, read-only. Putting it in
  the manifest fails with a bare "cannot upload the app, try again".

Updating an app whose entry already exists in the org catalog is done from the Teams
admin centre (Teams apps > Manage apps), not from Manage your apps in the client,
where the only actions offered are View details and Copy link.
"""

import argparse
import json
import uuid
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from lib.config.env import config

HERE = Path(__file__).parent
PACKAGE = HERE / "draft-detective-teams.zip"

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

BRAND = (15, 108, 189)  # the blue used on the cards this bot posts

# The last version built, so running with no argument does not silently reproduce a
# version already in the org catalog -- which Teams refuses on update. Bump it here
# when you bump it in the catalog, or pass the version as an argument.
DEFAULT_VERSION = "1.2.1"


def manifest(app_id: str, bot_id: str, version: str) -> dict:
    return {
        "$schema": (
            "https://developer.microsoft.com/en-us/json-schemas/teams/v1.17/"
            "MicrosoftTeams.schema.json"
        ),
        "manifestVersion": MANIFEST_VERSION,
        "version": version,
        "id": app_id,
        "developer": {
            "name": "AE Studio",
            "websiteUrl": "https://ae.studio",
            "privacyUrl": "https://ae.studio/privacy",
            "termsOfUseUrl": "https://ae.studio/terms",
        },
        "name": {"short": BOT_NAME, "full": f"{BOT_NAME} document review"},
        "description": {"short": DESCRIPTION_SHORT, "full": DESCRIPTION_LONG},
        "icons": {"color": "color.png", "outline": "outline.png"},
        "accentColor": "#0F6CBD",
        "bots": [
            {
                "botId": bot_id,
                "scopes": ["personal", "team", "groupChat"],
                "supportsFiles": False,
                "isNotificationOnly": False,
                "commandLists": [
                    {
                        "scopes": ["personal", "team", "groupChat"],
                        "commands": [
                            {
                                "title": "Does this overclaim?",
                                "description": (
                                    "Look for claims the document does not support"
                                ),
                            },
                            {
                                "title": "Check the citations",
                                "description": (
                                    "Check references against what the text says"
                                ),
                            },
                            {
                                "title": "Summarise the argument",
                                "description": "What the document argues, and where",
                            },
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


def _icons() -> tuple[Path, Path]:
    """A colour icon and an outline icon, to the sizes Teams requires.

    Teams rejects a package whose icons are the wrong size, and the outline must be
    single-colour on transparency -- it is tinted by the client, so anything else
    comes out as a silhouette.
    """

    colour_path = HERE / "color.png"
    outline_path = HERE / "outline.png"

    colour = Image.new("RGBA", (192, 192), BRAND + (255,))
    draw = ImageDraw.Draw(colour)
    # A magnifying glass over a page: the same idea as the product's own mark.
    draw.rounded_rectangle((44, 34, 130, 150), radius=8, fill=(255, 255, 255, 255))
    for offset in range(0, 5):
        y = 56 + offset * 18
        draw.line((60, y, 114, y), fill=BRAND + (90,), width=5)
    draw.ellipse((92, 88, 156, 152), outline=(255, 255, 255, 255), width=12)
    draw.line((146, 142, 168, 164), fill=(255, 255, 255, 255), width=14)
    colour.save(colour_path)

    outline = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    pen = ImageDraw.Draw(outline)
    pen.ellipse((5, 5, 21, 21), outline=(255, 255, 255, 255), width=3)
    pen.line((19, 19, 27, 27), fill=(255, 255, 255, 255), width=3)
    outline.save(outline_path)

    return colour_path, outline_path


def _options() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Teams app package.")
    parser.add_argument(
        "version",
        nargs="?",
        default=DEFAULT_VERSION,
        help="Manifest version. Raise it to update an already-installed app.",
    )
    parser.add_argument(
        "--app-id",
        help="Teams app id. Defaults to the bot's, which is normally right.",
    )
    parser.add_argument(
        "--new-app-id",
        action="store_true",
        help=(
            "Generate a fresh app id, sidestepping 'this app has already been "
            "submitted in your org'. Leaves the old catalog entry behind."
        ),
    )
    return parser.parse_args()


def main() -> None:
    bot_id = config.TEAMS_BOT_APP_ID
    if not bot_id:
        raise SystemExit(
            "TEAMS_BOT_APP_ID is not set. It is the Microsoft App ID of the Azure Bot "
            "resource, and Teams needs it to route messages to this bot."
        )

    options = _options()
    version = options.version
    # The app id defaults to the bot's, which keeps the two from drifting apart.
    # It is what Teams recognises an upload by, so changing it creates a second app
    # in the org rather than updating this one -- occasionally what you want, when a
    # catalog entry is in the way and deleting it is more trouble than it is worth.
    app_id = options.app_id or (str(uuid.uuid4()) if options.new_app_id else bot_id)
    document = manifest(app_id=app_id, bot_id=bot_id, version=version)
    colour_path, outline_path = _icons()

    with zipfile.ZipFile(PACKAGE, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(document, indent=2))
        archive.write(colour_path, "color.png")
        archive.write(outline_path, "outline.png")

    print(f"wrote {PACKAGE}")
    print(f"  app id: {app_id}" + ("  (a new app in the org)" if app_id != bot_id else ""))
    print(f"  bot id: {bot_id}")
    print(f"  version: {version}")
    print(f"  scopes: {', '.join(document['bots'][0]['scopes'])}")
    print(f"  size:   {PACKAGE.stat().st_size:,} bytes")
    print()
    print("First time:  Teams > Apps > Manage your apps > Upload a custom app.")
    print("Afterwards:  find the app there and use its update action. Uploading it")
    print("             as new is refused, because the id already exists in the org.")


if __name__ == "__main__":
    main()
