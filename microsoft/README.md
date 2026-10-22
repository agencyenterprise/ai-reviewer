# Microsoft integrations: for developers

How Draft Detective's Word add-in and Teams bot work, why they are built the way they
are, and how to run them locally.

**Setting one up for a deployment?** See
[`docs/microsoft-integrations.md`](../docs/microsoft-integrations.md), the admin guide.
This file assumes you have read it.

| | Code | Can it change a document? |
|---|---|---|
| Word add-in | `frontend/app/addin/`, `frontend/components/addin/`, `frontend/lib/addin/`; API under `/api/microsoft/word` | Yes |
| Teams bot | `lib/services/microsoft/teams/`, `lib/agents/teams_agent.py`; API under `/api/microsoft/teams`; package at `/api/microsoft/teams/package.zip` | Only through the add-in |

## Why two integrations

**Only a Word client can write to a document someone is editing.** SharePoint refuses a
whole-file write with `423 Locked` while anyone has the document open, whoever asks. It
was probed on 2026-10-08, writing as the account that had the document open: an idle Word
for the web tab and a View Only Word desktop session both got 423. Closing the web tab
released the lock within seconds; quitting Word desktop did not release it for more than
nine minutes. So "write when nobody has it open" is no plan either.

So anything that adds a comment or a tracked change runs inside Word, in the add-in, and
anything that only reads can run on the server. "Write in the margin" and "answer in
chat" are different capabilities, not two renderings of one.

### From Teams to Word: handoffs

Asked for comments or changes, the bot cannot write them, so it stores them as a
**handoff**, keyed by the document and by who asked (`lib/services/microsoft/word/handoffs.py`),
and says so in the thread. When that person opens the document with the add-in, the pane
lists the handoffs released to their account and **Apply** writes one; the result is
posted back to the thread.

A handoff is released only to the same Microsoft account that asked, matched by Entra
object id and tenant, never by email. That fails closed: a guest asking from another
organization's Team, whom Teams signs in as their guest account while Word signs them in
as their home account, does not see theirs.

The add-in's own chat stores its suggestions as handoffs too (`chat_thread_id` set, no
Teams `reference`), so both are applied, claimed and reported the same way.

### Conversations

Every conversation, on any surface (the web app's /chat, the add-in's chat, Teams), has a
row in `conversations`; the images of a document read in it are `files` rows it owns
(`conversation_id`, no project). Each surface keeps its own details in a table linked
one-to-one by id: `chat_threads`, `microsoft_word_chat_threads`,
`microsoft_teams_conversations` (which holds the Teams conversation id that keys the
agent's history). A conversation is listed under a Draft Detective user by email
(`lib/services/microsoft/linked_users.py`), only when `AUTH_MICROSOFT_ENTRA_ID_ISSUER` names
one tenant and the account is from it: Entra does not verify that claim. Access is never
decided by it.

## Word add-in

The pane is the frontend's `/addin` page, opened by Word from the manifest the frontend
serves at `/addin/manifest.xml` (`frontend/lib/addin/manifest.ts`). The manifest's id is a
UUID v5 of the frontend host, so each deployment is its own add-in, and its version
follows the app's.

The pane is the chat. Where the Teams bot runs (`GET /api/microsoft/word/features`, which
reports whether every setting the bot needs is set), a notice above the chat says what
waits from Teams, only while something does, and **Review** opens those suggestions in
the chat's place.

### Signing in

The pane is a Microsoft account, not a Draft Detective user: what it may do is decided by
the Entra object id (`lib/api/addin_auth.py`).

1. **Office single sign-on**, tried silently when the pane opens: Office hands over a
   token for the account signed in to Word, issued for the deployment's sign-in app with
   the `access_as_user` scope. The API checks it against Microsoft's signing keys.
2. **A dialog**, when single sign-on fails: `/addin/sign-in` signs in with the web app's
   own Microsoft sign-in and hands the session token back. Only a Microsoft sign-in works
   there, as it is the one that carries the object id.

Both need all three `AUTH_MICROSOFT_ENTRA_ID_*` settings; without them the API accepts no
add-in token.

### The chat

The **Chat** tab talks to a Draft Detective agent about the open document
(`lib/agents/word_chat_agent.py`, routes in `lib/api/routers/microsoft/word_chat.py`), with
the /chat page's skills and no web search.

- **The document goes with the message.** The pane reads it as a .docx with
  `getFileAsync`, which makes Word save any pending edit first, and uploads it only when
  it changed since it was last sent (`frontend/lib/addin/pane-document.ts`). Only the pane
  can see a document mid-edit: SharePoint's copy, which Graph serves, was measured lagging
  a fresh edit by most of a minute. It is converted like a project's main document, charts
  and metafiles rendered to images, and the agent opens those with `view_image`, bound to
  the conversation when the turn is built.
- **Changes come back as one card per answer.** The agent may store them in several
  `suggest_changes` calls; each adds to the answer's card. Its quotes are checked against
  the document first (`lib/services/microsoft/word/quote_check.py`), so one Word would not
  find, or would find twice, goes back to the agent.
- **The answer waits for the card.** After its last batch the agent calls `ask_to_apply`,
  a LangGraph `interrupt`. Applying or dismissing the card resumes it
  (`POST /api/microsoft/word/chat/thread/resume`), and the agent reads the outcome from the
  card itself.
- **One conversation per document and account.** **New chat** sets it aside for good. An
  unsaved document has no URL, so the pane gives it a key of its own (`unsaved:<id>`).
- **One turn at a time.** A turn claims its conversation (`running_since`); another
  message meanwhile gets 423.

### Writing to the document

With Word's own API (`frontend/lib/addin/apply-handoff.ts`): each quote is found with
Word's search inside its paragraph, an edit replaces those words with `insertText` while
change tracking is on for everyone, and a comment is added with `insertComment`. The
author's tracking setting is restored afterwards. Each write takes under a tenth of a
second and touches only the quoted words.

- **Authorship:** Word records changes under whoever clicks **Apply**; no Word API sets
  another author. So each comment starts with "Draft Detective:".
- **Matching:** quotes are compared with quotes, dashes and spacing evened out, and found
  by Word's search, which takes at most 255 characters: a longer quote is found by its
  ends (`frontend/lib/addin/quote-search.ts`).
- **No fallback:** an item Word's search does not find exactly once in its paragraph (a
  field, a footnote mark, an earlier tracked change inside the quote), or whose write Word
  refuses, is reported as not applied. Each write is its own round trip, so a refusal is
  pinned on its own item.
- **WordApi 1.4** is needed for change tracking and comments; older Word cannot apply.

## Teams bot

A bot with its own identity, mentioned in a chat or channel. It reads documents and
writes none.

- **A link is the only way to name a document.** Looking one up by name was built and
  removed: a search reaches wider than what the asker may read, while a link is something
  they already had.
- **It reads as the person who asked**, with a delegated token from the OAuth connection
  `TEAMS_USER_AUTH_CONNECTION`, so it reaches nothing they could not. The Bot Framework
  token service keeps the refresh token; this service never stores one. Gating the read
  does not gate the audience: the answer goes to the whole chat or channel.
- **Documents are converted like a project's**, images kept for the conversation, so the
  bot judges a figure by what it shows.

### Signing in where the question was asked

The Bot Framework's usual sign-in card, the `OAuthCard`, only works in a 1:1 chat; in a
channel it fails with a misleading "the app does not exist or has been uninstalled". So
the bot posts an Adaptive Card whose button is an `Action.Execute`, the one route Teams
documents for signing in inside a group chat or channel. Without a token the bot answers
the action with a `loginRequest`, Teams opens the sign-in window, then sends the action
again with a code the token service turns into the user's token, and the parked question
is answered (`lib/services/microsoft/teams/sign_in.py`). Only the person who asked can
release it.

- **`validDomains` must contain `token.botframework.com`**, or sign-in fails in every
  scope with the same misleading error. The package's manifest sets it.
- **The parked question lives in the database** (`microsoft_teams_signin_state`), not in
  memory: the card and its actions arrive as separate requests, which land on different
  workers in production. A row nobody finishes is swept after an hour.
- **No Teams SSO.** It would save one click, once per person, but needs an Application ID
  URI, an exposed scope and Teams' client ids pre-authorized, and bot SSO does not work in
  channels at all.

### The package

`GET /api/microsoft/teams/package.zip` builds the zip from the manifest and the committed
icons (`lib/services/microsoft/teams/package.py`), refused with 503 until the bot is
configured. The app id is the bot's (`TEAMS_BOT_APP_ID`), which keeps the two from
drifting apart. Teams recognizes an upload by that id and refuses an update that does not
raise the version, so the version is the application's own, which every release raises.
In the Teams admin center,
the **External app ID** is that id; the **App ID** is Teams' own, and putting it in the
manifest fails with a bare "cannot upload the app".

## Local development

Word and Teams reach the app over the public internet, so both the frontend
(`localhost:3000`) and the API (`localhost:8000`) need public HTTPS URLs. Any tunnel
works: VS Code's public port forwarding, or ngrok (copy `ngrok.yaml` here to
`ngrok-dev.yaml`, which is git-ignored, add your token, and run
`ngrok start --config ngrok-dev.yaml --all` from `microsoft/`). A reserved
domain saves redoing the steps below each time the tunnel restarts.

Set it up as its own deployment, following the admin guide with the tunnel hosts as
`<frontend>` and `<api>`, in a tenant where you can register apps. Then, in your `.env`
files:

- `frontend/.env`: `AUTH_URL` (the frontend tunnel), `NEXT_PUBLIC_API_URL` (the API
  tunnel), the three `AUTH_MICROSOFT_ENTRA_ID_*`, and `ADDIN_NAME`, such as
  `Draft Detective (local)`, so Word tells it apart from a published add-in.
- `.env`: the three `AUTH_MICROSOFT_ENTRA_ID_*`, and the `TEAMS_*` settings for the bot.

**Add-in.** Save `https://<frontend tunnel>/addin/manifest.xml` to a file and sideload it,
rather than publishing it to the tenant:

- Word for the web: in a document, **Home → Add-ins → More Add-ins → My Add-ins →
  Upload My Add-in**.
- Word for Mac: copy it into `~/Library/Containers/com.microsoft.Word/Data/Documents/wef/`
  and reopen Word, as after every change to it
  ([Microsoft's guide](https://learn.microsoft.com/en-us/office/dev/add-ins/testing/sideload-an-office-add-in-on-mac)).

To work on the pane without Word, a tunnel or a Microsoft sign-in, open
`/addin/preview` on any deployment, or `http://localhost:3000/addin/preview` locally. It runs the real pane
with Office and the add-in's API stood in for in the browser (`frontend/lib/addin/preview/`),
and its controls switch between scenarios: the Teams bot on or off, suggestions waiting
from Teams, a new conversation, an answer or one waiting on a card, a missing OpenAI key,
and the pane's width. Messages get canned replies; asking for comments or changes offers a
card, and dismissing it carries the answer on. Apply cannot write without Word.

**Bot.** Point your Azure Bot's messaging endpoint at
`https://<api tunnel>/api/microsoft/teams/messages`. A stale endpoint fails silently: the
message never arrives. The API logs each question and the document it resolved.

**When a tunnel's host changes**, update the Entra app's redirect URI and Application ID
URI, `AUTH_URL` and `NEXT_PUBLIC_API_URL`, the bot's messaging endpoint, and save and
sideload the manifest again.
