# Teams app (bot)

Draft Detective as a bot: mention it in a channel or a chat with a question about a
Word document, and it answers there. It reads the document from SharePoint with the
service's own identity and never writes to it — see [`../README.md`](../README.md) for
why that division exists.

Setting this up means creating **three** things in Azure, which is the part that
surprises people:

| What                            | Why                                                       |
| ------------------------------- | --------------------------------------------------------- |
| An **Azure Bot** resource       | Gives Teams somewhere to deliver messages, and an identity |
| An **app registration** for Graph | Lets the backend read documents from SharePoint          |
| A **Teams app package** (this directory) | Installs the bot in the tenant                    |

The bot's identity and the Graph identity are deliberately separate registrations.
They have different purposes, different secrets to rotate, and different blast radii
if one leaks: the bot credential lets someone impersonate the bot, while the Graph
credential can read documents.

---

## 1. The Azure Bot resource

1. In the Azure portal, create a resource of type **Azure Bot**.
2. Choose **Multi-tenant** or **Single-tenant**. Whichever you pick has to match
   `TEAMS_BOT_TENANT_ID` below — set it for single-tenant, leave it unset for
   multi-tenant. Mismatched, tokens are issued for the wrong authority and every
   request fails validation.
3. Let it create a new Microsoft App ID, or point it at an existing registration.
   That App ID is `TEAMS_BOT_APP_ID`.
4. Under **Configuration**, set the **Messaging endpoint** to your public HTTPS URL
   plus the bot's path:

   ```
   https://<your-host>/api/microsoft/teams/messages
   ```

5. Under **Channels**, add **Microsoft Teams**. This is easy to miss and the failure
   is unhelpful: uploading the app package reports **"Invalid Bot"** with no mention
   of channels.
6. Under the registration's **Certificates & secrets**, create a client secret. That
   value is `TEAMS_BOT_APP_PASSWORD`, and it is shown once.

## 2. The Graph app registration

The backend loads the document itself for this path, so it needs its own credentials.

1. Register a new application (App registrations > New registration).
2. Under **API permissions**, add the Microsoft Graph **application** permission
   **`Files.Read.All`**, then grant admin consent. Application, not delegated — see
   the note below.
3. Create a client secret.

That gives you `AZURE_CLIENT_ID`, `AZURE_TENANT_ID` and `AZURE_CLIENT_SECRET`.

> **Why application permissions and not the asking user's own?** Delegated
> (on-behalf-of) access would be better — the user's own permissions would apply, and
> the bot could not read anything they cannot. It does not work here: Conditional
> Access refuses a delegated token from a device that is not registered
> (`AADSTS530035`), and a server has no device identity. App-only was the only option.
>
> The consequence is that the app can read anything in the tenant, and the bot answers
> anyone who can mention it. `GRAPH_ALLOWED_HOSTS` and `GRAPH_ALLOWED_SITE_PATHS` are
> what stop that from being a read-anything oracle, and they **fail closed**: with
> `GRAPH_ALLOWED_HOSTS` unset, every document is refused. The better fix is
> **`Sites.Selected`** instead of `Files.Read.All`, which moves the boundary into the
> token where our code cannot forget to enforce it.

## 3. Environment

```bash
# The bot's identity
TEAMS_BOT_APP_ID=00000000-0000-0000-0000-000000000000
TEAMS_BOT_APP_PASSWORD=<client secret>
TEAMS_BOT_TENANT_ID=<tenant id, single-tenant bots only>

# Reading documents from SharePoint
AZURE_CLIENT_ID=00000000-0000-0000-0000-000000000000
AZURE_TENANT_ID=<tenant id>
AZURE_CLIENT_SECRET=<client secret>

# Required. Unset means no document may be read at all.
GRAPH_ALLOWED_HOSTS=yourtenant.sharepoint.com
# Optional, narrows further. Checked against the document Graph resolves, not
# against the pasted link, because a sharing link has no path in it.
GRAPH_ALLOWED_SITE_PATHS=/sites/YourSite
```

## 4. Build and install the app package

```bash
uv run python microsoft/teams-app/build_package.py
```

This writes `draft-detective-teams.zip` next to the script — generated rather than
committed, because the manifest carries your tenant's ids. Then in the Teams client:

**Apps → Manage your apps → Upload a custom app** (`Fazer upload de um aplicativo
personalizado`). The tenant has to permit custom app uploads; if the option is absent,
that policy is why.

### Updating an installed app

Teams identifies an app by the `id` in its manifest, so re-uploading the same id is
refused with **"This app has already been submitted in your org"**. To change an
installed app:

1. Raise the version: `uv run python microsoft/teams-app/build_package.py 1.0.2`
2. Update it from the **Teams admin centre** (Teams apps → Manage apps), not from
   *Manage your apps* in the client — there the only actions offered are *View
   details* and *Copy link*.

Two ids are easy to confuse, and the admin centre shows the wrong one first:

- **External app ID** (`ID do aplicativo externo`) — this is `manifest.id`, and the
  one that must match on an update.
- **App ID** (`ID do Aplicativo`) — Teams' own catalog id, read-only. Putting it in
  the manifest fails with a bare *"cannot upload the app, try again"*.

If a catalog entry is in the way and removing it is more trouble than it is worth,
`--new-app-id` mints a fresh id and installs a second app alongside the old one.

## 5. Local development

Teams delivers messages over the public internet, so the backend needs a public HTTPS
URL even for local work. Any tunnel does — VS Code dev tunnels and ngrok both work:

```bash
uv run dev.py                                    # the backend on :8000
# then expose :8000 and use the resulting host
```

Put the tunnel host in the Azure Bot's **Messaging endpoint** (step 1.4). The host
changes each time the tunnel restarts unless it is a reserved one, and a stale
endpoint fails silently from the Teams side — the message simply never arrives.

Watch the log for what the bot resolved:

```
Teams bot question from Carlos Bonetti: 'check the abbreviations' (document: https://...)
resolved https://...:w:/s/... to https://.../sites/YourSite/DD Test/v3-CERN.docx
```
