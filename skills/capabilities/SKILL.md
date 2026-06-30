---
name: capabilities
description: Use this skill as the entry point when the user gives a generic, unspecified request to use Draft Detective on their document — e.g. "run draft detective", "analyze my document", "review this document", "check my paper", "what can you check?", "what can you do?". It lists everything Draft Detective offers and asks the user what to run. Do NOT use it when the user has already named a specific check or operation (run that skill directly).
---

# Draft Detective — What would you like to run?

The user has asked to use Draft Detective but has **not** specified what to run. Draft Detective offers several capabilities, each implemented as its own skill. Your job here is **only to help them choose** — do not run anything yet, and do not guess on their behalf.

## What to do

1. Present the capabilities below, grouped as shown, each with its short description.
2. Ask the user **what they would like to run**. Make it clear they can pick more than one, or ask for all of them.
3. Wait for their answer. Once they choose, invoke the corresponding skill(s) listed in the "Skill" column. If they ask for several, run them in parallel.

Keep your message concise and scannable — a short intro line, the lists, and the question.

## Assessments

These review the document and flag issues.

| Assessment | What it checks | Skill |
|---|---|---|
| **Reference Error Checker** | Are your references accurate? Uses web search to confirm each citation exists and that the author, title, publisher, and year match public sources — catching typos and hallucinated references. | `reference-validation` |
| **Figures & Tables Check** | Are all figures and tables properly titled, consistently numbered, cited in the body text, and do all body-text references resolve to a real figure or table? | `figures-tables-check` |
| **Abbreviation Scan** | Are abbreviations and acronyms defined inline at first use, listed in an Abbreviations section, used consistently, and never given conflicting meanings? | `abbreviation-scan` |
| **Document Contents** | Does the document include all required sections — About This, Acknowledgements, Methods, Results, Conclusion, References, and an Appendix when one is referenced? | `document-contents` |
| **About This** | Does the preface / "About This" section cover the required elements (context, objectives, audience, situating in the literature, contribution, and scope), and does each author biography meet publication requirements (sentence count, position & affiliation, research focus, and highest degree)? | `about-this-preface`, `about-this-authors` |
| **Recommendation Check** | Is each recommendation supported by the document's own findings? Flags recommendations with weak, indirect, missing, or contradictory backing. | `recommendation-check` |
| **Internal Inference Validation** | Does the reasoning hold up? Flags logical leaps, unsupported conclusions, and arguments where the evidence doesn't support the claim. | `inference-validation` |
| **Advocacy & Tone** | Does the document use neutral, objective language? Flags trigger words (certainty language without evidence), advocacy language (unsupported recommendations or opinion framing), and subjective tone. (Beta.) | `advocacy-tone` |
| **Reviewer 2** | A rigorous simulated peer review — summary, strengths, weaknesses, and prioritized next steps — plus a separate devil's-advocate rebuttal. (Beta.) | `reviewer-2` |
| **Literature Review** | Are there relevant sources you may have missed? Searches the web for academic sources related to your document's claims — both supporting and conflicting — that aren't already cited. (Beta.) | `literature-review` |
| **Live Reports** | Have your findings been updated or contradicted by newer research? Searches the web for sources published after your document's date and produces an addendum of what to update. (Beta.) | `live-reports` |
| **Methodological Alignment** | Does your methodology match standard practice in the field? Uses web search to characterize the field baseline, then compares your approach — similarities, differences, missing components, rigor, and suggested improvements. | `methodology-comparison` |
| **Reproducibility Check** | Could someone reproduce your results from the document alone? Extracts the main results and classifies each by how reproducible it is. (Beta.) | `reproducibility-check` |

## Tools

These operate on the document rather than flagging issues.

| Tool | What it does | Skill |
|---|---|---|
| **Download References** | Search the web for a reference and download its full original content (PDF/Markdown), verifying the match. Reports found / found-but-inaccessible / not-found. | `reference-download` |
| **Extract Methodology** | Extract a structured, reproducible description of the paper's methodology, and classify how reproducible it is. | `methodology-extraction` |
| **Extract References** | Find and list all bibliographic references from the document's reference/bibliography section. | `reference-extraction` |
| **Extract Abbreviations** | Find and catalogue every abbreviation/acronym occurrence — with its inline definition, occurrence count, location, Abbreviations-section entry, and exempt-class status. | `abbreviation-extraction` |

## Notes

- If the user's request actually does name a specific capability (e.g. "check my references", "extract the bibliography", "download this citation"), skip the menu and invoke that skill directly instead of using this one.
- Most capabilities operate on the document the user has provided or uploaded; if none is available yet, ask them to share it.
