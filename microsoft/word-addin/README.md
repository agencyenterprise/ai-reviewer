# Word add-in

One of the Microsoft integrations — see [`../README.md`](../README.md) for how this
one differs from the Teams bot, and why only this path can change a document.

## Office Add-in (local dev)

### Prereqs

- Run the backend API locally with `uv run dev.py`
- Run the frontend locally with `pnpm dev` from `frontend/`

### Expose local apps (tunnel)

You need public HTTPS URLs for:

- frontend (`localhost:3000`)
- API (`localhost:8000`)

Use any tunnel provider. Two common options:

#### Ngrok

1. Copy `microsoft/word-addin/ngrok.yaml` to a new file (for example, `microsoft/word-addin/ngrok-dev.yaml`).
2. Update the new file with your ngrok token.
3. From `microsoft/word-addin/`, run `ngrok start --config ngrok-dev.yaml --all`.

#### Port Forward

Forward the ports 3000 and 8000 in VSCode/Cursor. Make sure they are public.

Use the generated public HTTPS URLs in the steps below.

### Get the manifest

The frontend serves the add-in's manifest at `/addin/manifest.xml`, filled in for itself:
its address (`AUTH_URL`, or the host it was reached at), the Entra app it signs in with
(`AUTH_MICROSOFT_ENTRA_ID_ID`, see "Signing in" below), its version and its name
(`ADDIN_NAME`, "Draft Detective" by default) (`frontend/lib/addin/manifest.ts`). Give a
tunnel's add-in a name of its own, such as `Draft Detective (local)`, so Word tells it
apart from a published one. The add-in's id is derived from the host, so each
deployment, and each tunnel, is its own add-in.

Set `AUTH_URL` in `frontend/.env` to the frontend tunnel's URL, then save
`https://<frontend tunnel>/addin/manifest.xml` to a file, such as
`microsoft/word-addin/manifest-dev.local.xml`.

### Frontend API URL

- Set `NEXT_PUBLIC_API_URL` in `frontend/.env` to your public API URL (the 8000 tunnel).

### Add to Office

1. Open Word Web (https://word.cloud.microsoft/) and create a blank file.
2. Go to `Home` → `Add-ins` → `More Add-ins`.
3. Go to `My Add-ins`.
4. Choose `Manage My Add-in` → `Upload My Add-in`.
5. Select the manifest file you saved.

### Notes

- Keep both the API and frontend running while testing.
- If your tunnel URLs change, update `.env`, then save the manifest and upload it again.

## Sideload Office Add-ins on Mac for testing

To test the add-in locally on MacOS, inside installed word (Microsoft 365):

https://learn.microsoft.com/en-us/office/dev/add-ins/testing/sideload-an-office-add-in-on-mac

```bash
cp microsoft/word-addin/manifest-dev.local.xml ~/Library/Containers/com.microsoft.Word/Data/Documents/wef
```

Requires re-opening Word every time manifest changes.

## Preview in browser (without Word)

To work on the pane's layout, open `http://localhost:3000/addin` in a browser. Anything
that reads or writes the document needs Word, and so does signing in.

## The chat

The pane's **Chat** tab is a conversation with Draft Detective about the open document
(`frontend/components/addin/chat/`, backend `lib/api/routers/microsoft/word_chat.py`).

- With each message the pane reads the document as a .docx (Office.js `getFileAsync`,
  which makes Word save any pending edit first) and uploads it only when it changed since
  it was last sent in this conversation (`frontend/lib/addin/pane-document.ts`). The
  backend reads it like any uploaded .docx (`lib/services/microsoft/word/pane_document.py`).
  It is converted as the web app converts a project's main document: charts and
  metafile pictures are rendered to images, and every image is saved as a `files` row
  owned by the conversation (`conversation_id`, no project) and referenced from the
  markdown as `draftdetective://{id}`. The agent opens them with `view_image`, bound to
  that conversation when the turn is built, so it can read no other conversation's or
  project's images. The text selected in Word goes along too, so "this paragraph"
  means something.
- Checks run by name: the list button beside the message box, or "/" in it, offers the
  workflows that can run without the internet (`lib/agents/word_chat_checks.py`), and
  picking one sends "Run the … check" straight away.
- The agent's comments and tracked changes come back as one card per answer, shown once
  the answer ends. The agent may store them in several calls (it batches long lists);
  each call after the first adds to that answer's card, until a card is full (100
  comments, 100 edits) or applying it has begun. The card is a handoff card: Apply
  claims, writes and reports them through `/handoffs`, like the ones from Teams, and the
  result goes back to the agent with the next message.
- The agent asks before it carries on: after its last batch it calls `ask_to_apply`,
  which pauses the answer on the card (LangGraph's `interrupt`). Applying or dismissing
  the card resumes it (`POST /api/microsoft/word/chat/thread/resume`), and the agent,
  reading the card's outcome itself, says what landed and may retry a failed quote once.
  A new message while it waits moves on; the card stays open.
- One conversation per document and account. **New chat** clears it; the old one stays in
  the database, out of the pane's reach. A document never saved has no URL, so the pane
  gives it a key of its own (`unsaved:<id>`, kept in sessionStorage) and each unsaved
  document gets its own conversation.

## Publish the Word add-in in your organization

Official deployment guide:
https://learn.microsoft.com/en-us/microsoft-365/admin/manage/office-addins?view=o365-worldwide#upload-custom-office-add-ins-in-your-organization

In step 3, choose **Add-in only manifest** and provide the deployment's manifest URL:
`https://<frontend>/addin/manifest.xml`. It answers 503 until `AUTH_MICROSOFT_ENTRA_ID_ID`
is set. Its version follows the app's, so after a release that changes the manifest,
update the add-in from the same page.

Reference video (older, but still useful): https://www.youtube.com/watch?v=p3aeO9muEI8&t=181s

## How the pane writes to the document

With Word's own API (`frontend/lib/addin/apply-handoff.ts`): each quote is found with
Word's search inside its paragraph, an edit replaces those words with `insertText` while
change tracking is on for everyone, and a comment is added with `insertComment`. The
author's tracking setting is restored afterwards. Each write takes under a tenth of a
second in Word for the web, and it touches only the quoted words, so a coauthor's edits
elsewhere in the paragraph are left alone.

Word records these under the name of whoever clicks Apply: no Word API can set the
author of a tracked change or a comment. So the pane starts each comment with
"Draft Detective:".

Things worth knowing:

- Quotes are matched with curly quotes, dashes and spacing evened out, then Word is asked
  for the paragraph's own characters (`frontend/lib/addin/quote-search.ts`). Word's
  search takes at most 255 characters, so a longer quote is found by its first and last
  hundred and the range between them is checked against it. The chat agent's quotes are
  checked the same way before they are offered
  (`lib/services/microsoft/word/quote_check.py`), so a quote Word would not find, or
  would find twice, goes back to the agent instead of onto a card.
- An item is reported as not applied, with nothing written, when Word's search finds a
  different number of hits than the paragraph's text has (a field, a footnote mark, an
  earlier tracked change inside the quote), or when Word refuses the write. There is no
  fallback: what happens to each item is reported back to Teams or to the chat agent.
- Each write is its own round trip, so a refusal is pinned on its own item.
- Change tracking and comments need WordApi 1.4. Older Word cannot apply at all.

## Signing in

The pane signs in as a Microsoft account, because changes asked for in Teams are
released only to the account that asked (matched by Entra object id, not email).

1. **Office single sign-on**, tried silently when the pane opens: Office hands over a
   token for the account signed in to Word, issued for the add-in's Entra app. The
   backend verifies it (`lib/api/addin_auth.py`).
2. **A dialog**, when single sign-on is not available: `/addin/sign-in` signs in with
   Draft Detective's own Microsoft sign-in and hands the session token back. Only a
   Microsoft sign-in works here; it is the one that carries the object id.

Either way the pane is a Microsoft account, not a Draft Detective user: what it may do
is decided by the object id. A conversation it starts is still listed under the Draft
Detective user with the account's `email` claim (`conversations.user_id`, see
`lib/services/microsoft/linked_users.py`), as the web app knows people by email, but only
while `AUTH_MICROSOFT_ENTRA_ID_ISSUER` names one tenant and the account is from it: Entra
does not verify that claim, so an email from another tenant could be anyone's. Teams
conversations are listed under whoever asked first, by their mail address in Graph.

Both use one Entra app registration per environment: the same one as Draft Detective's
own "Sign in with Microsoft" (`AUTH_MICROSOFT_ENTRA_ID_ID`), with:

- **Expose an API**: Application ID URI `api://<frontend host>/<client id>`, a scope
  `access_as_user` (admins and users can consent), and the client application
  `ea5a67f6-b6f3-4338-b240-c655ddc3cc8e` (Microsoft Office) pre-authorized for it.
- **Manifest**: `requestedAccessTokenVersion` set to `2`.
- **Authentication**: Web redirect URI `https://<frontend host>/api/auth/callback/microsoft-entra-id`.
- **Token configuration**: optional claim `email` on the ID and access tokens.
- **API permissions**: Microsoft Graph delegated `openid`, `profile`, `email`,
  `offline_access`, `User.Read`, with admin consent.
- **Certificates & secrets**: a client secret, for the frontend.

Then set `AUTH_MICROSOFT_ENTRA_ID_ID`, `AUTH_MICROSOFT_ENTRA_ID_SECRET` and
`AUTH_MICROSOFT_ENTRA_ID_ISSUER` (`https://login.microsoftonline.com/<tenant id>/v2.0`) in
**both** the frontend and the backend. All three are required: a deployment that does not
sign its users in with Microsoft has no add-in sign-in. A tenant-specific issuer means only
that tenant's accounts are accepted. The manifest's `WebApplicationInfo` names the
same client id and Application ID URI, filled in by `/addin/manifest.xml`. The URI
contains the frontend host, so a tunnel whose URL changes needs the app's Application ID
URI and redirect URI updated with it, and the manifest saved again.
