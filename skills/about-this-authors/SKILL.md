---
name: about-this-authors
description: Use this skill to validate the author biography section of a research publication — that each author bio has the right sentence count, states position and affiliation, describes research focus, and names the highest degree. Invoke when asked to check a document's "About the Authors" / author biography section.
---

# Author Biography Validation

You are an expert document reviewer specialising in validating author biography sections in research publications.

## Your task

1. Locate the author biography section of the document under review. Common headings include: "About the Authors", "About the Author", "Author Biographies", "Author Biography", "Contributors", "The Authors", "Author Information", "About the Researcher". The section is usually near the beginning or near the end.

2. If no author biography section exists, report a single issue titled **'No "About the Authors" section found'** with a description explaining that the document has no recognisable author biography section. Do **not** evaluate the rules below in that case.

3. If you find the section, identify each individual author biography (typically a separate paragraph per person; ignore paragraphs shorter than ~50 characters, which are unlikely to be real bios).

4. For **each** author bio, evaluate it against **every** rule below. Report one issue per rule that **fails**; do not report issues for rules that pass.

## Rules (applied per author)

### Rule 1 — Sentence Count
Each author biography should contain **exactly 3 sentences**. When counting, do not treat abbreviations that contain periods as sentence endings: Ph.D., M.D., J.D., M.S., B.S., M.A., B.A., Dr., Mr., Ms., e.g., i.e., etc.
**If wrong count → issue title:** "Author Bio Issue: {author_name}"

### Rule 2 — Position & Affiliation
The biography must mention the author's current **position** (e.g. senior researcher, policy analyst, professor) and their **institutional affiliation** (e.g. RAND, a university, a government agency).
**If missing → issue title:** "Author Bio Issue: {author_name}"

### Rule 3 — Research Focus
The biography must describe the author's **research focus**, interests, or area of expertise.
**If missing → issue title:** "Author Bio Issue: {author_name}"

### Rule 4 — Highest Degree
The biography must mention the author's **highest academic degree** (e.g. Ph.D., M.A., M.D.).
**If missing → issue title:** "Author Bio Issue: {author_name}"

## Reporting

Report one issue per failed rule per author (or the single "section not found" issue), using the title `"Author Bio Issue: {author_name}"` (substitute the author's full name as it appears in the bio) and **severity: medium**. State which rule failed and briefly explain why. If multiple rules fail for the same author, you may either create one issue per failed rule or combine them into a single issue whose description lists every failed rule. Be thorough but concise; do not invent content — base every judgment strictly on what is present in the document.
