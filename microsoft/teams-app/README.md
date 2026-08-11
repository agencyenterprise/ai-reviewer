# Teams app (bot)

Draft Detective as a bot: mention it in a channel or a chat with a question about a
Word document, and it answers there. It reads the document from SharePoint with the
service's own identity and never writes to it — see [`../README.md`](../README.md) for
why that division exists.

Setting this up means creating **three** things in Azure, which is the part that
surprises people:

| What                                     | Why                                                        |
| ---------------------------------------- | ---------------------------------------------------------- |
| An **Azure Bot** resource                | Gives Teams somewhere to deliver messages, and an identity |
| An **app registration** for Graph        | Lets the backend read documents from SharePoint            |
| A **Teams app package** (this directory) | Installs the bot in the tenant                             |

The bot's identity and the Graph identity are deliberately separate registrations.
They have different purposes, different secrets to rotate, and different blast radii
if one leaks: the bot credential lets someone impersonate the bot, while the Graph
credential can read documents.

---

## 1. The Azure Bot resource

→ [**Azure Bot resources**](https://portal.azure.com/#browse/Microsoft.BotService%2FbotServices)
in the Azure portal.

1. Select **+ Create** and choose the **Azure Bot** resource type.
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

→ [**App registrations**](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
in Microsoft Entra ID.

1. Select **New registration** and give it a name.
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

## 2b. Reading as the person who asked (recommended)

Without this the bot reads documents with the service's own identity, which is
tenant-wide: anyone who can mention the bot could have it open a document they have no
access to. With it, the bot holds a token for the _asker_, so Graph refuses anything
they could not open themselves.

Each person clicks a Sign in card once, from a 1:1 chat with the bot, and never again.
It has to be a 1:1 chat: Teams cannot acquire a token in a channel at all — see
[below](#each-person-must-sign-in-from-a-11-chat-first).

→ your bot under [**Azure Bot resources**](https://portal.azure.com/#browse/Microsoft.BotService%2FbotServices).

1. Go to **Configuration → Add OAuth Connection Settings**.
2. Name it (for example `graph-user`) and choose the **Azure Active Directory v2**
   service provider.
3. Give it the client id and secret of an app registration with the **delegated**
   Graph scope `Files.Read.All`, and that app's tenant id. Put `Files.Read.All` in
   **Scopes**, and **leave Token Exchange URL blank** — that field is only used for
   silent SSO, which this setup deliberately does not use. Use the _Graph_ registration
   here, not the bot's: the two are separate so that a leak of one is not a leak of
   both. This registration's secret lives in Azure, not in this service's environment.
4. Set `TEAMS_USER_AUTH_CONNECTION` to the connection's name.
5. **Grant admin consent for the delegated scopes.** Without it each person also
   sees Entra's consent screen the first time they sign in. With it they still see the
   Sign in card either way: consent and the card are separate steps.

What the user experiences: nothing, once signed in. If there is no token, the bot
posts a Sign in card, parks the question, and answers it automatically after sign-in
completes — no need to ask again. The refresh token is held by the Bot Framework token
service; this service never stores it.

### Each person must sign in from a 1:1 chat first

**Clicking Sign in inside a channel does not work.** It fails with:

> This action can't be performed since the app does not exist or has been uninstalled.

The message is misleading — the app is installed and the server side is fine. Teams
does not support the interactive OAuth card in channel or group-chat scope at all:

> OAuth isn't supported in the group chat or channel scopes directly. If you enable
> authentication and users install your bot in group chats or channels, they must
> authenticate in their personal scopes before they can use the bot in the group chat
> or channel.
>
> — [Teams bot authentication](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/authentication/add-authentication)

So the sequence for every new user is:

1. Open a **1:1 chat** with Draft Detective, ask it anything, and sign in there.
2. From then on, ask in channels as normal — the token service has their token, so no
   card appears and nothing is asked again.

The server log tells you which case you are in. It records the conversation, and a
sign-in attempt whose state carries `"conversationType": "channel"` will always fail
at the client. Everything else in the log looking healthy — the connection resolving,
a sign-in resource obtained, the card posted, a 200 returned — is consistent with this
failure, because the refusal happens entirely inside Teams.

**`validDomains` must contain `token.botframework.com`** or sign-in cannot work in any
scope, with the same misleading error. `build_package.py` sets it; the comment there
explains why it is not empty despite this app having no tabs.

### Where the sign-in state lives

Sign-in spans two requests — the message that posts the card, and the `signin/*` invoke
that completes it — so the flow state cannot live in process memory. Production runs
Uvicorn with `--workers 4`, so the two requests usually land on different processes and
an in-memory store would lose the parked question about three times in four. A
single-process dev server never shows this.

It is kept in the `microsoft_teams_signin_state` table instead, which any server running
current migrations already has. Rows are written when a sign-in starts and deleted when
it finishes; a sign-in nobody finishes is swept an hour later, because the parked message
is in there.

No tokens are stored — the refresh token stays in the Bot Framework token service. Only
flow bookkeeping and the activity waiting to be replayed.

### Why there is no way around the click

The only way to avoid sign-in entirely **and** keep per-user access control is to stop
needing a user token: read with the app identity, but first ask SharePoint whether the
asker may read that item (`GetUserEffectivePermissions`, keyed on the `aadObjectId` that
arrives on every activity). That was investigated and rejected — it needs SharePoint
`Sites.FullControl.All`, so it would make the app strictly more powerful in order to
restrict it.

Teams SSO, which replaces the card with a silent token exchange, was also implemented and
removed: it needs an Application ID URI, an exposed scope and the Teams client ids
pre-authorised on a third app registration, and it still cannot acquire a token in a
channel — so it removes one click, once per person, for a permanent increase in setup
complexity.

### One more thing to know before relying on it

- **Conditional Access may refuse.** A delegated token acquired from a server is
  refused when a compliant device is required (`AADSTS530035`). Teams SSO starts from
  the token the user's own client already holds, which is a better position — and it
  passed here — but it is a tenant policy question, not a guarantee. If it is refused,
  an admin can scope an exclusion for this app, a reasonable ask given the alternative
  is a tenant-wide app-only grant. **Test Connection** on the OAuth connection settles
  it on its own, before any code runs.
- **This gates the read, not the audience.** The answer is posted into the channel the
  question came from, so everyone there sees the document's contents whether or not
  they can open the file. If that matters, restrict which channels the bot is in.

## 3. Environment

```bash
# The bot's identity
TEAMS_BOT_APP_ID=00000000-0000-0000-0000-000000000000
TEAMS_BOT_APP_PASSWORD=<client secret>
TEAMS_BOT_TENANT_ID=<tenant id, single-tenant bots only>

# Read documents as the person who asked, not as the service. Unset means app-only,
# which can reach documents the asker cannot. See section 2b.
TEAMS_USER_AUTH_CONNECTION=graph-user
TEAMS_USER_AUTH_SCOPES=Files.Read.All


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
committed, because the manifest carries your tenant's ids.

→ [**Teams**](https://teams.microsoft.com/), then:

**Apps → Manage your apps → Upload a custom app** (`Fazer upload de um aplicativo
personalizado`). The tenant has to permit custom app uploads; if the option is absent,
that policy is why.

Then, if you configured section 2b, **sign in once from a 1:1 chat with the bot before
using it in a channel.** Sign-in cannot complete in channel scope, and the error blames
the app rather than the scope. See [above](#each-person-must-sign-in-from-a-11-chat-first).

### Updating an installed app

Teams identifies an app by the `id` in its manifest, so re-uploading the same id is
refused with **"This app has already been submitted in your org"**. To change an
installed app:

→ [**Teams admin centre → Manage apps**](https://admin.teams.microsoft.com/policies/manage-apps).

1. Raise the version: `uv run python microsoft/teams-app/build_package.py 1.0.2`
2. Find the app there and use its update action — not _Manage your apps_ in the Teams
   client, where the only actions offered are _View details_ and _Copy link_.

Two ids are easy to confuse, and the admin centre shows the wrong one first:

- **External app ID** (`ID do aplicativo externo`) — this is `manifest.id`, and the
  one that must match on an update.
- **App ID** (`ID do Aplicativo`) — Teams' own catalog id, read-only. Putting it in
  the manifest fails with a bare _"cannot upload the app, try again"_.

If a catalog entry is in the way and removing it is more trouble than it is worth,
`--new-app-id` mints a fresh id and installs a second app alongside the old one.

## 5. Local development

Teams delivers messages over the public internet, so the backend needs a public HTTPS
URL even for local work. Any tunnel does — VS Code dev tunnels and ngrok both work:

```bash
uv run dev.py                                    # the backend on :8000
# then expose :8000 and use the resulting host
```

Put the tunnel host in the **Messaging endpoint** of your bot under
[Azure Bot resources](https://portal.azure.com/#browse/Microsoft.BotService%2FbotServices)
(step 1.4). The host
changes each time the tunnel restarts unless it is a reserved one, and a stale
endpoint fails silently from the Teams side — the message simply never arrives.

Watch the log for what the bot resolved:

```
Teams bot question from Carlos Bonetti: 'check the abbreviations' (document: https://...)
resolved https://...:w:/s/... to https://.../sites/YourSite/DD Test/v3-CERN.docx
```
