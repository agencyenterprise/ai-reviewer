# Microsoft 365 integrations

How to connect a Draft Detective deployment to an organization's Microsoft 365, for the
admin who sets it up. There are three integrations, and each builds on the one before:

| | What people get | Builds on |
|---|---|---|
| **1. Sign in with Microsoft** | Signing in to Draft Detective with their work account | – |
| **2. Word add-in** | A Draft Detective pane in Word: chat about the open document, and apply its comments and tracked changes | 1 |
| **3. Teams bot** | Ask Draft Detective about a Word document from a Teams chat or channel; changes it suggests are applied through the Word add-in | 2 |

Set them up in order. Each part ends with a check, so a mistake shows up where it was made.

## Before you start

You need:

- **The deployment's two public addresses.** In this guide:
  - `<frontend>` is the web app's host, such as `draftdetective.example.com`;
  - `<api>` is the API's host, such as `api.draftdetective.example.com`.

  Use the final hosts: several settings contain them, and a later change of host means
  changing those settings and republishing the add-in.
- **A Microsoft 365 account with the Global Administrator role**, or Application
  Administrator plus Teams Administrator. You register apps, grant consent for the
  organization and publish apps to it.
- **For the Teams bot only, an Azure subscription** in the same tenant, for the Azure Bot
  resource. The bot's Teams channel is free.
- **Access to the deployment's environment variables**, for the frontend service and the
  API service.

You will be asked for your **tenant ID**. It is on the
[Microsoft Entra overview](https://entra.microsoft.com/#view/Microsoft_AAD_IAM/TenantOverview.ReactView)
as **Tenant ID**.

---

## 1. Sign in with Microsoft

People sign in to Draft Detective with their Microsoft work account instead of a
password. Part 2 builds on this: the Word add-in signs in with the same Microsoft Entra
app registration, so set this up first, even if you only want the add-in.

### 1.1 Register the app

Open [**App registrations → New registration**](https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/CreateApplicationBlade/quickStartType~/null/isMSAApp~/false)
in the Microsoft Entra admin center.

- **Name:** `Draft Detective`. People see it on Microsoft's sign-in and consent screens.
- **Supported account types:** **Accounts in this organizational directory only (Single
  tenant)**.
- **Redirect URI:** platform **Web**,
  `https://<frontend>/api/auth/callback/microsoft-entra-id`.

Select **Register**. On the app's **Overview**, note the **Application (client) ID**.

### 1.2 Add the email claim

Draft Detective knows people by email address, and Microsoft only puts it in the sign-in
token when asked to.

Open [**App registrations**](https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade),
select the **All applications** tab, and select the app you just registered. The steps
below are on its pages, in the menu on the left.

Open **Token configuration** → **Add optional claim**. Choose token
type **ID**, tick **email** and select **Add**. When asked, tick **Turn on the Microsoft
Graph email permission** and select **Add**.

### 1.3 Grant consent

Open **API permissions**. It lists Microsoft Graph's `User.Read` and `email`. Select **Add
a permission** → **Microsoft Graph** → **Delegated permissions**, tick **openid** and
**profile**, and select **Add permissions**.

Then select **Grant admin consent for <your organization>** and confirm, so nobody is
asked to consent on their first sign-in.

### 1.4 Create a client secret

Open **Certificates & secrets** → **Client secrets** → **New client secret**. Choose an
expiry and select **Add**. Copy the **Value** now: it is shown only once.

Note the expiry date. When the secret expires, nobody can sign in with Microsoft, and the
add-in stops working with it, until a new one is set.

### 1.5 Configure the deployment

Set these on **both the frontend and the API**, then redeploy both:

| Variable | Value |
|---|---|
| `AUTH_MICROSOFT_ENTRA_ID_ID` | The Application (client) ID (1.1) |
| `AUTH_MICROSOFT_ENTRA_ID_SECRET` | The secret's value (1.4) |
| `AUTH_MICROSOFT_ENTRA_ID_ISSUER` | `https://login.microsoftonline.com/<tenant ID>/v2.0` |

The issuer names your tenant, so only your organization's accounts are accepted.

### Check

Open `https://<frontend>` signed out. **Sign in with Microsoft** is offered, and signing in
with a work account lands you in Draft Detective.

---

## 2. Word add-in

A **Draft Detective** button on Word's Home tab opens a pane beside the document. In it,
people chat with Draft Detective about the document they have open, unsaved edits
included. Asked for changes, it offers them as comments and tracked changes, which
**Apply** writes into the document under the person's own name, for them to accept or
reject as usual. The pane also applies the changes asked for in Teams (part 3).

It works in Word for the web, Windows and Mac.

### 2.1 Let Office sign people in

The pane signs people in silently, as the account they are signed in to Word with
(Office single sign-on). That needs four more settings on the app from part 1. Open
[**App registrations**](https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade),
select the **All applications** tab, and select that app.

1. **Manifest**: find `"requestedAccessTokenVersion": null` and change it to
   `"requestedAccessTokenVersion": 2`. Select **Save**.
2. **Expose an API**:
   - Next to **Application ID URI**, select **Add**. Replace the suggested value with
     `api://<frontend>/<client ID>` and select **Save**.
   - Select **Add a scope**. **Scope name:** `access_as_user`. **Who can consent:**
     **Admins and users**. **Admin consent display name:** `Use Draft Detective in
     Office`. **Admin consent description:** `Lets Office sign you in to Draft Detective.`
     Select **Add scope**.
   - Select **Add a client application**. **Client ID:**
     `ea5a67f6-b6f3-4338-b240-c655ddc3cc8e`, which is Microsoft Office. Tick the
     `access_as_user` scope and select **Add application**.
3. **Token configuration** → **Add optional claim**. Choose token type **Access**, tick
   **email** and select **Add**.

Nothing changes in the deployment's settings.

### 2.2 Publish the add-in

The deployment serves the add-in's manifest, already filled in for it, at:

```
https://<frontend>/addin/manifest.xml
```

Open it in a browser first. You should see XML naming your `<frontend>`. A message naming
`AUTH_MICROSOFT_ENTRA_ID_*` settings means part 1.5 is not deployed yet.

**Publishing more than one deployment in the tenant**, such as a test one beside
production? Give each one its own name first: set `ADDIN_NAME` on the frontend, such as
`Draft Detective (test)`, and redeploy it. Word shows that name on the add-in and on its
button, so people can tell which one they are using. Set it before publishing: Office
only picks up a changed name with the next release.

Then open [**Integrated apps**](https://admin.cloud.microsoft/#/Settings/IntegratedApps)
in the Microsoft 365 admin center:

1. Select **Upload custom apps**.
2. **App type:** **Office Add-in**. Choose **Provide link to the manifest file**, paste the
   URL above and select **Validate**, then **Next**.
3. Choose who gets it: **Just me** to try it first, then **Entire organization** or
   **Specific users/groups**. Select **Next**.
4. Accept the permissions and select **Finish deployment**.

It can take a few hours to reach everyone's Word; people may need to restart Word, or
sign out of it and back in.

### Check

Open a document in [Word for the web](https://word.cloud.microsoft/) as someone the
add-in was assigned to.

1. **Home** shows a **Draft Detective** button. Select it: the pane opens and reads
   "Signed in as" your account, without asking you to sign in.
2. Ask in the chat for comments on a paragraph. Its answer ends with a card listing them;
   **Apply** adds them to the document.

If the pane shows a **Sign in with Microsoft** button instead of signing you in, single
sign-on is not set up right: recheck 2.1. The button still works, through a pop-up.

### Later

- **Releases:** the manifest's version follows the app's. When a release changes the
  add-in, open it in Integrated apps and update it from the same URL.
- **A new host:** the add-in's identity is tied to `<frontend>`. On a new host, update the
  redirect URI (1.1) and Application ID URI (2.1), then publish the new manifest URL and
  remove the old add-in: Office treats it as a different add-in.

---

## 3. Teams bot

People mention Draft Detective in a Teams chat or channel with a question and a link to a
Word document in SharePoint or OneDrive, and it answers there. It reads the document as
the person who asked, so it can only read what they can. It never writes to a document:
asked for comments or changes, it leaves them for the Word add-in, and the person applies
them from the pane the next time they open the document.

The bot needs three things, set up in this order:

1. **An app registration for reading documents.** Each person signs in to it once, and
   the bot reads documents with their access.
2. **An app registration for the bot itself.** This is the identity Teams talks to.
3. **An Azure Bot resource.** It connects Teams to the deployment, and holds each
   person's sign-in.

### 3.1 Register the document-reading app

Open [**App registrations → New registration**](https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/CreateApplicationBlade/quickStartType~/null/isMSAApp~/false).

- **Name:** `Draft Detective (Teams sign-in)`.
- **Supported account types:** **Single tenant**.
- **Redirect URI:** platform **Web**, `https://token.botframework.com/.auth/web/redirect`.

Select **Register** and note its **Application (client) ID**. Then:

1. **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated
   permissions**. Tick **Files.Read.All** and select **Add permissions**. Then select
   **Grant admin consent for <your organization>** and confirm.
2. **Certificates & secrets** → **New client secret** → **Add**. Copy the **Value**.

### 3.2 Register the bot's app

Open [**New registration**](https://entra.microsoft.com/#view/Microsoft_AAD_RegisteredApps/CreateApplicationBlade/quickStartType~/null/isMSAApp~/false)
again.

- **Name:** `Draft Detective (Teams bot)`.
- **Supported account types:** **Single tenant**.
- **Redirect URI:** leave it empty.

Select **Register** and note its **Application (client) ID**. Then open **Certificates &
secrets** → **New client secret** → **Add**, and copy the **Value**.

It needs no API permissions.

### 3.3 Create the Azure Bot

Open [**Create an Azure Bot**](https://portal.azure.com/#create/Microsoft.AzureBot) in the
Azure portal.

- **Bot handle:** a unique name, such as `draft-detective-bot`.
- **Subscription** and **Resource group:** yours. Create a resource group if you have none.
- **Data residency:** **Global**.
- **Pricing tier:** select **Change plan** and choose **Free**. The Teams channel costs
  nothing.
- **Type of App:** **Single Tenant**.
- **Creation type:** **Use existing app registration**. **App ID:** the bot app's client
  ID (3.2). **App tenant ID:** your tenant ID.

Select **Review + create**, then **Create**, and **Go to resource** when it is done.

### 3.4 Connect it to the deployment and to Teams

In the bot's menu:

1. **Settings → Configuration**. **Messaging endpoint:**
   `https://<api>/api/microsoft/teams/messages`. Select **Apply**.
2. **Settings → Channels** → **Microsoft Teams**. Accept the terms, keep the defaults and
   select **Apply**. Without this channel, Teams refuses the app later with "Invalid Bot".

### 3.5 Add the sign-in connection

Still in the bot, open **Settings → Configuration** → **Add OAuth Connection Settings**:

- **Name:** `graph-user`.
- **Service Provider:** **Azure Active Directory v2**.
- **Client id** and **Client secret:** the document-reading app's (3.1).
- **Token Exchange URL:** leave it empty.
- **Tenant ID:** your tenant ID.
- **Scopes:** `Files.Read.All User.Read`.

Select **Save**. Then select the `graph-user` connection and **Test Connection**: a
sign-in window opens, and it should end with a token. If your organization's Conditional
Access refuses the sign-in, this is where it shows; an exclusion for the app fixes it.

### 3.6 Configure the deployment

Set these on **the API**, then redeploy it:

| Variable | Value |
|---|---|
| `TEAMS_BOT_APP_ID` | The bot app's client ID (3.2) |
| `TEAMS_BOT_APP_PASSWORD` | The bot app's secret (3.2) |
| `TEAMS_BOT_TENANT_ID` | Your tenant ID |
| `TEAMS_USER_AUTH_CONNECTION` | `graph-user` (3.5) |

### 3.7 Publish the bot in Teams

Teams installs a bot from a small zip package. Build it from a checkout of this
repository, with the bot app's client ID:

```bash
TEAMS_BOT_APP_ID=<bot client ID> uv run python microsoft/teams-app/build_package.py
```

It writes `microsoft/teams-app/draft-detective-teams.zip`.

Then open [**Manage apps**](https://admin.teams.microsoft.com/policies/manage-apps) in the
Teams admin center, select **Upload new app** → **Upload**, and choose the zip. Draft
Detective is now in your organization's app catalog, available to everyone.

To add it, people open **Apps → Built for your org** in Teams, select **Draft Detective**
and **Add**. To use it in a channel, they add it to that team.

### Check

1. In Teams, open a chat with Draft Detective. Send a question with a link to a Word
   document, such as "What does this document conclude? <link>".
2. The first time, it replies with a card asking you to sign in. Sign in: the answer
   follows.
3. Ask it for comments on the document. It replies that they will be added in Word.
4. Open the document in Word with the add-in. The pane lists the comments under **From
   Teams**; **Apply** adds them, and the Teams thread gets an "Applied to … in Word"
   message.

Worth knowing: the answer goes to the chat or channel the question came from, and
everyone there can read it, even those who cannot open the document. Add the bot only
where that is acceptable.

### Later

- **A new package:** Teams recognizes the bot by its app ID, so uploading the same
  package twice is refused. Build it with a higher version
  (`build_package.py 1.2.2`), then open Draft Detective in
  [Manage apps](https://admin.teams.microsoft.com/policies/manage-apps) and update it
  there. Updating from Teams itself is not offered.
- **A new API host:** update the messaging endpoint (3.4).

---

## Reference: settings

| Variable | Service | Part |
|---|---|---|
| `AUTH_MICROSOFT_ENTRA_ID_ID` | frontend and API | 1 |
| `AUTH_MICROSOFT_ENTRA_ID_SECRET` | frontend and API | 1 |
| `AUTH_MICROSOFT_ENTRA_ID_ISSUER` | frontend and API | 1 |
| `ADDIN_NAME` (optional) | frontend | 2 |
| `TEAMS_BOT_APP_ID` | API | 3 |
| `TEAMS_BOT_APP_PASSWORD` | API | 3 |
| `TEAMS_BOT_TENANT_ID` | API | 3 |
| `TEAMS_USER_AUTH_CONNECTION` | API | 3 |

What lives in Microsoft 365 and Azure when all three are set up:

| Where | What | Part |
|---|---|---|
| Entra app registration | `Draft Detective` | 1, 2 |
| Entra app registration | `Draft Detective (Teams sign-in)` | 3 |
| Entra app registration | `Draft Detective (Teams bot)` | 3 |
| Microsoft 365 admin center, Integrated apps | The Word add-in | 2 |
| Azure | The Azure Bot, with its Teams channel and `graph-user` connection | 3 |
| Teams admin center, Manage apps | The Teams app | 3 |

Three client secrets expire: the sign-in app's (1.4) and the Teams apps' (3.1, 3.2).
Renew each before its expiry date. The sign-in app's goes in
`AUTH_MICROSOFT_ENTRA_ID_SECRET`, the Teams sign-in app's in the `graph-user` connection,
and the bot's in `TEAMS_BOT_APP_PASSWORD`.
