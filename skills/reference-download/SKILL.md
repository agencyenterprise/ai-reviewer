---
name: reference-download
description: Use this skill to locate and download the full original content of a bibliographic reference from the web — given a citation, find a direct URL to the full text (not an abstract or metadata page), download it, verify it matches the reference, and report the outcome. Invoke when the user asks to download, fetch, or retrieve the full text/PDF of one or more references or citations. Handles one reference at a time; for several, apply the procedure to each.
---

Locate the full original content of a user-provided reference with web search; download and verify its completeness; report failure if needed.

- When given a reference (e.g., citation or bibliographic entry), use web search tool to locate a direct URL for the full, original content of the reference (not an abstract, summary, or metadata-only page).
- Upon finding a candidate full-content URL, use the available tool to download the file; this tool will return a file ID for the downloaded file.
- Next, validate the downloaded file: use the provided tool to read/check the file by its ID, ensuring it matches the full original content described in the reference (e.g., contains correct title, authors, and full text/content).
- If the file is confirmed as the correct full original content, return the downloaded file ID and stop.
- If the download does not contain the full content (e.g., is incomplete, paywalled, preview-only, or mismatched), resume searching for a different URL hosting the full content; repeat the process.
- Continue searching and verifying until either the correct file is found or all viable options are exhausted.
- As "final_conclusion", return one of the following:
  - "source_found": the full original content is available and accessible; you read the file and confirmed it matches the reference.
  - "source_found_but_not_accessible": the source exists, but the full original content is behind a paywall or otherwise inaccessible; you download the file but it does not match the reference. You MUST also set "inaccessibility_reason" to a single concise sentence explaining why the content is not accessible (e.g., "The content is behind a JSTOR paywall requiring institutional login.", "The site uses Cloudflare bot protection that blocks automated downloads.", "Access requires a paid subscription to the publisher's platform.").
  - "source_not_found": the source cannot be located; the online presence of the source cannot be confirmed.

Follow this sequence strictly:
REASONING (search, download, verify, repeat as needed) → CONCLUSION

## Example

**Input:**
Ablon, Lillian, and Andy Bogart, Zero Days, Thousands of Nights: The Life and Times of Zero-Day Vulnerabilities and Their Exploits, RAND Corporation, RR-1751-RC, 2017. As of February 15, 2024: https://www.rand.org/pubs/research_reports/RR1751.html

**Process (REASONING FIRST):**
- Search online using the full citation to find the official or reputable link (RAND's official report page) hosting the report.
- Confirm the link points to the full PDF (not a summary).
- Download the linked PDF.
- Read the downloaded file, check metadata: title, author, and full text match reference.
- If all criteria met, accept and return file ID.
- If not, try 2-3 alternative sources. If all fail with paywall/access issues, conclude "source_found_but_not_accessible".
- If all efforts fail to locate the source, return "source_not_found".

(Reminder: Always start your output with your reasoning and ensure that you do not output any conclusions before finishing your verification steps. This order is required.)

---

**Important:**
- Always perform reasoning steps (search, download, validate) before answering.
