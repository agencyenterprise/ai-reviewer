---
name: reference-download
description: Use this skill to locate and download the full original content of a bibliographic reference from the web — given a citation, find a direct URL to the full text (not an abstract or metadata page), download and save it, verify it matches the reference, and report the outcome. Invoke when the user asks to download, fetch, or retrieve the full text/PDF of one or more references or citations. Handles one reference at a time; for several, apply the procedure to each.
---

<!-- interactive-only:start -->
## Before you search — get the user's consent

This check sends parts of the user's document to an external web search provider. Do not run a search, fetch a URL, or call any other web tool until the user has explicitly agreed to it in this conversation.

1. If you do not already have the user's consent for this document in this conversation, relay this to them verbatim and stop for their answer:

   > To run this assessment, parts of your document — and possibly the whole document — will be sent to a web search provider as search queries. Don't proceed if the document contains confidential information you aren't comfortable sharing with an external search engine. Do you consent to running web search on this document?

2. Continue only on an explicit yes. One consent covers this document for the rest of the conversation — don't re-ask per reference or per section.
3. If the user declines, stop and do not search. Do not fall back on memory or on what you can infer without searching, and do not report partial findings as if the check ran. Say the check needs web access, and offer one that doesn't (the `capabilities` skill marks which checks need web search).
<!-- interactive-only:end -->

Locate the full original content of a user-provided reference using web search; download and verify it; report the outcome (including failure) clearly.

- When given a reference (e.g., citation or bibliographic entry), search the web to locate a direct URL for the full, original content of the reference (not an abstract, summary, or metadata-only page).
- Upon finding a candidate full-content URL, use the available tools to download and save the file locally.
- Then verify the downloaded file: inspect its contents and confirm it matches the full original content described in the reference (e.g., contains the correct title, authors, and full text/content).
- If the file is confirmed as the correct full original content, keep it as the result and stop.
- If the download does not contain the full content (e.g., it is incomplete, paywalled, preview-only, or mismatched), resume searching for a different URL hosting the full content; repeat the process.
- Continue searching and verifying until either the correct file is found or all viable options are exhausted.
- Conclude with one of the following outcomes:
  - **found**: the full original content is available and accessible; you downloaded the file and confirmed it matches the reference. Report where the saved file is and the source URL.
  - **found but not accessible**: the source exists, but the full original content is behind a paywall or otherwise inaccessible (you could not obtain a file that matches the reference). Give a single concise sentence explaining why it is not accessible (e.g., "The content is behind a JSTOR paywall requiring institutional login.", "The site uses Cloudflare bot protection that blocks automated downloads.", "Access requires a paid subscription to the publisher's platform.").
  - **not found**: the source cannot be located; its online presence cannot be confirmed.

Follow this sequence strictly:
REASONING (search, download, verify, repeat as needed) → CONCLUSION

## Example

**Input:**
Ablon, Lillian, and Andy Bogart, Zero Days, Thousands of Nights: The Life and Times of Zero-Day Vulnerabilities and Their Exploits, RAND Corporation, RR-1751-RC, 2017. As of February 15, 2024: https://www.rand.org/pubs/research_reports/RR1751.html

**Process (REASONING FIRST):**
- Search online using the full citation to find the official or reputable link (RAND's official report page) hosting the report.
- Confirm the link points to the full PDF (not a summary).
- Download and save the linked PDF.
- Inspect the downloaded file; check that the title, author, and full text match the reference.
- If all criteria are met, accept it as the result.
- If not, try 2-3 alternative sources. If all fail with paywall/access issues, conclude "found but not accessible".
- If all efforts fail to locate the source, conclude "not found".

(Reminder: Always start your output with your reasoning and ensure that you do not state a conclusion before finishing your verification steps. This order is required.)

---

**Important:**
- Always perform the reasoning steps (search, download, verify) before answering.
