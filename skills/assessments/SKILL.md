---
name: assessments
description: Use this skill as the entry point when the user gives a generic, unspecified request to analyze, review, or check their document with Draft Detective — e.g. "run draft detective", "analyze my document", "review this document", "check my paper", "what can you check?". It lists the available assessments and asks the user which one(s) to run. Do NOT use it when the user has already named a specific assessment (run that assessment's skill directly).
---

# Draft Detective — Choose an Assessment

The user has asked to analyze their document but has **not** specified which assessment to run. Draft Detective offers several distinct assessments, each implemented as its own skill. Your job here is **only to help them choose** — do not run any assessment yet, and do not guess one on their behalf.

## What to do

1. Present the list of available assessments below, each with its short description.
2. Ask the user **which assessment (or assessments)** they would like to run. Make it clear they can pick more than one, or ask for all of them.
3. Wait for their answer. Once they choose, invoke the corresponding skill(s) listed in the "Skill" column. If they ask for several, run them in parallel.

Keep your message concise and scannable — a short intro line, the list, and the question.

## Available assessments

| Assessment | What it checks | Skill |
|---|---|---|
| **Reference Error Checker** | Are your references accurate? Uses web search to confirm each citation exists and that the author, title, publisher, and year match public sources — catching typos and hallucinated references. | `reference-validation` |
| **Figures & Tables Check** | Are all figures and tables properly titled, consistently numbered, cited in the body text, and do all body-text references resolve to a real figure or table? | `figures-tables-check` |
| **Document Contents** | Does the document include all required sections — About This, Acknowledgements, Methods, Results, Conclusion, References, and an Appendix when one is referenced? | `document-contents` |
| **Recommendation Check** | Is each recommendation supported by the document's own findings? Flags recommendations with weak, indirect, missing, or contradictory backing. | `recommendation-check` |
| **Internal Inference Validation** | Does the reasoning hold up? Flags logical leaps, unsupported conclusions, and arguments where the evidence doesn't support the claim. | `inference-validation` |
| **Reviewer 2** | A rigorous simulated peer review — summary, strengths, weaknesses, and prioritized next steps — plus a separate devil's-advocate rebuttal. (Beta.) | `reviewer-2` |

## Notes

- If the user's request actually does name a specific assessment (e.g. "check my references"), skip the menu and invoke that assessment's skill directly instead of using this one.
- Several assessments analyze the document the user has provided or uploaded; if no document is available yet, ask them to share it.
