---
name: review-assistant
description: >-
  Generate the artifacts of a RAND peer-review response cycle from an author's
  inputs. Produces three things: a revision-planning summary, one reviewer
  response memo per reviewer, and a consolidated reviewer coverage report for a
  QA manager. Use this whenever someone has a report (or a draft plus a revised
  draft) together with one or more reviewer memos and needs to respond to
  reviewers, draft reviewer response memos, plan revisions from a review memo,
  check whether a revised draft actually addresses the reviewers' comments, or
  produce a coverage / responsiveness report for a QA manager. Trigger even when
  the user does not say "skill" or name an output, for example: "respond to
  these reviewer comments", "draft a response memo to the reviewer", "did my
  revision address the review", "what does this reviewer want me to change",
  "summarize the revisions the reviewers asked for", "check my responses cover
  everything the reviewers raised".
---

# Review Assistant

## What this skill does

RAND reports go out for peer review. Each reviewer returns a memo, and the
authors then write a revised draft plus a response memo per reviewer explaining
how they handled each point. A QA manager (QAM) signs off on whether the authors
were responsive. This skill automates the author-side and QAM-side paperwork of
that loop from the documents the author already has.

It produces three outputs. You do not have to produce all three every time.
Read what the user is asking for and produce the ones that fit, but they share
the same foundation (parsing the memos and locating each point in the draft), so
build that once and reuse it.

- **Revision-planning summary.** Earliest in the cycle. From the
  original draft and the reviewer memos, list the topics the reviewers want
  changed, where each sits in the draft, and a short suggestion for addressing
  it. This is an orientation aid the author uses before revising.
- **Reviewer response memos, one per reviewer.** From the original
  draft, the revised draft, and the reviewer memos, draft a response memo for
  each reviewer that echoes every reviewer point and states how the revision
  addressed it (or why it was not changed).
- **Reviewer coverage report.** For the QAM. From the original draft,
  the revised draft, the reviewer memos, and the response memos, consolidate
  everything the reviewers asked for and whether and how each item was
  addressed, with an overall responsiveness read.

## Inputs

Ask for or identify what you have. Not all inputs are needed for all outputs.

- **Original draft**: the version that was reviewed. Needed for all outputs.
- **Reviewer memos**: one or more. Can be any text-based format, though usually
  Word or PDF. Needed for all outputs.
- **Revised draft**: the version that addresses the comments. Needed for the
  reviewer response memos and the reviewer coverage report.
- **Response memos**: the author's replies. If they already exist they are an
  input to the reviewer coverage report; if they do not, the coverage report can
  run on the revised draft alone, and the reviewer response memos produce them.
- **Reviewer marked-up copy** (optional): a copy of the report with inline Word
  comments and tracked edits. Treat these as secondary and editorial (see
  "Word comments" below).

The documents in one cycle are small enough to hold at once: memos and response
memos run roughly 800 to 1,700 words, and a full report is around 12,000 words.
Do not chunk them. Read each in full so cross-references resolve.

## The shared foundation

Do these two steps first, whatever output you are producing.

### 1. Parse each reviewer memo into discrete points

A reviewer memo does not follow a fixed layout, so do not rely on a standard
header or structure. One element does usually appear: a rating question,
"Does the product meet RAND's standards for high-quality and objective research
and analysis?", with three options:

1. The product meets RAND's standards as is.
2. Specific, limited revisions are needed to meet RAND's standards.
3. Substantial or complex revisions are needed to meet RAND's standards.

Two things about the rating are easy to get wrong:

- **The selected option is usually not plain text.** All three options appear as
  list items; the reviewer's choice is marked by formatting (bold, highlight, a
  checkbox) or is only stated in prose. Do not assume a line says "selected".
  Read run-level formatting if you can, and otherwise infer the rating from the
  reviewer's overall-assessment paragraph (for example, "may benefit from
  substantial revisions" means option 3).

The body is where the real work is. It is typically an "Areas for improvement"
section followed by "Additional Suggestions". Reviewers write it in one of two
shapes, and you must handle both:

- **Hierarchical**: thematic headers (for example "Methodological Justification")
  with bullets, sometimes nested sub-bullets. One bullet is usually one point.
- **Flowing prose**: paragraphs with no headers, where each paragraph is one
  point.

Segment the body into discrete, individually addressable points. A point is one
thing the author could act on. Split compound bullets that bundle several asks.
Preserve the reviewer's own wording for each point, because the response memo
will echo it. For each point, record: the reviewer, the verbatim text, its
place in the memo, and any location hint the reviewer gave.

Assign each point a stable **ID** and use it in every output. Give each reviewer
a letter in the order their memos are provided (the first reviewer is A, the
second B, and so on), and number that reviewer's points in memo order: A1, A2,
A3 for the first reviewer, B1, B2, B3 for the second. Use sub-point IDs (A1.1,
A1.2) only when a single point genuinely contains distinct sub-asks worth
tracking separately, such as a bullet with nested sub-bullets; do not force them
otherwise. Once assigned, an ID always refers to the same point. The
revision-planning summary, the reviewer response memos, and the reviewer
coverage report all cite these same IDs, so a reader can trace one point across
every document.

### 2. Locate each point in the draft

Reviewers point to places loosely: by page ("around page 8"), by named concept
or section ("Model 5", "the fourth model"), by figure, or at the whole report.

The important trap: **numbers and headings move between the original and revised
draft.** Authors reorder and rename sections in response to reviews. A point
that referenced "Concept 4" in the original may be a differently numbered and
retitled section in the revised draft. So map points by **semantic anchor**, the
topic or concept the point is about, not by page number, section number, or
heading text. When you report a location, describe it by content ("the section
introducing the five concepts") so it survives renumbering, and verify presence
by matching meaning, not position.

Classify each point's scope, since it changes what the tool can check:

- **report-wide** (applies to the whole document or its framing),
- **section-level** (a chapter, concept, or named part),
- **paragraph-level or local** (a specific passage, figure, or sentence).

## Word comments and marked-up copies

If a reviewer returned a marked-up copy with inline Word comments, treat those
as editorial and lower authority than the memo. The memos say as much
explicitly: inline suggestions that are not repeated in the memo are
non-binding, and the author may decide how to respond. Attach a marked-up copy
to its reviewer's memo. Surface its comments only as optional, clearly
secondary, and never let an unaddressed inline comment lower the responsiveness
read the way an unaddressed memo point does.

## Include the reviewer memo verbatim in every output

Every output this skill produces must reproduce the reviewer's original memo in
full and verbatim, not paraphrased or summarized away. The reviewer's exact
words are the anchor of the whole exchange, and authors, reviewers, and QAMs
need to see them unaltered so they can trust that nothing was dropped or
reworded. This applies to all three outputs, including the planning summary and
the coverage report, not just the response memos.

Make the boundary between the reviewer's words and your own contribution
unmistakable. Never blur the two, and never present your own wording as if the
reviewer wrote it.

- **Mark quoted text clearly.** Render the reviewer's verbatim text as a Markdown
  blockquote (each line prefixed with `> `), or in a Word deliverable as a
  visually distinct, labeled "Reviewer (verbatim)" block. Reproduce the memo in
  full, including any header or rating block and the "Additional Suggestions"
  section.
- **Match the original formatting where you can.** Beyond the text, try to carry
  over the reviewer's own formatting: headings, bullet and numbering structure,
  bold and italic, indentation, tables. The closer the reproduction looks to the
  source, the more easily the author can visually anchor each item back to the
  original document. If the output medium cannot reproduce a formatting element
  faithfully, keep the text and structure and do not let anything drop.
- **Put your contribution next to each point.** After each quoted point, add your
  own content for it (the suggestion, the author's response, or the verdict and
  evidence, depending on the output), clearly labeled and outside the quote.
- **Overall-suggestion headers are welcome.** You may add your own headers that
  carry a higher-level or overall suggestion for a group of related points, or an
  opening summary, as long as they are plainly your commentary. RAND reviewers
  themselves group points under thematic headers, so mirroring that is natural.
- **Preserve the reviewer's order and wording.** Reproduce the memo in the
  reviewer's own order, and do not drop, reorder, or reword any of the reviewer's
  text.

The per-output sections below say what your contribution next to each point
should contain. The verbatim reproduction and clear marking are constant across
all of them.

## Tone and voice

Everything this skill writes should sound like a RAND colleague, not a generic
assistant. Reviewer response memos, revision plans, and coverage reports share a
specific register: collegial and plain, anchored in the text, opinions owned in
the first person, critiques framed as suggestions or questions, and declines
given with a clear reason rather than an apology or reflexive agreement.

Before drafting any prose output, read `references/voice-and-tone.md` and
follow it. It has separate guidance for the reviewer voice and the
author-response voice, phrase banks, and a list of generic-AI tells to avoid
(sycophancy, hype, empty hedging, exclamation marks, em dashes, emoji).
The response memos in particular use the author-response voice; the coverage
report and revision plan stay neutral and evidence-anchored.

## Revision-planning summary

Goal: help the author see the whole ask before revising. Inputs: original draft
and reviewer memos.

Reproduce the reviewer memo(s) in full, verbatim, following the reviewer's own
structure (see "Include the reviewer memo verbatim in every output"), and label
each point with its ID (see step 1). Directly under each quoted point, add a
compact planning note with:

- where it lives in the draft (by content, per step 2), and its scope,
- a one or two sentence suggestion for how to address it,
- which reviewer(s) raised it.

This is a planning aid, so keep your added notes brief even though the reviewer's
text is reproduced in full.

## Reviewer response memos

Goal: one response memo per reviewer, in the form RAND authors write by hand.
Inputs: original draft, revised draft, reviewer memos.

The response memo is a near-mechanical transform of the reviewer memo: clone the
memo and interleave the author's replies. Follow this shape, which mirrors what
RAND authors actually produce:

1. Reuse whatever header the memo uses, reframed as a response (for example a
   "Re:" line becomes "Response to Review of ..."). Keep the rating question and
   its three options if the memo has them.
2. Open with a short courtesy preamble and state how the author's replies are
   distinguished from the reviewer's text (see formatting below). It is common to
   also restate the reviewer's overall-assessment paragraph.
3. For every point in the reviewer's memo, in the reviewer's order, label it
   with its ID (see step 1), echo the reviewer's original text verbatim as a
   clearly marked quote, then add the author's response directly after it in a
   clearly differentiable way. Reproduce the entire memo this way, including the
   "Additional Suggestions" section, so nothing is dropped (see "Include the
   reviewer memo verbatim in every output").

For each response, compare the revised draft against the original to determine
what actually changed, and write the reply accordingly:

- If addressed, say concretely what changed and where, and quote the new text
  when short (for example, the new opening sentence of a section).
- If partially addressed, say what was done and what was not.
- If not changed, give the reason. Reasoned declines are normal and expected,
  not failures. Common and legitimate grounds include the document type (see
  below), scope, and disagreement with the reviewer. Write these plainly and
  respectfully.

When you cannot write a real response to a point because nothing in the revised
draft addresses it and there is no stated reason, flag it for the author rather
than inventing a change. That flag is the signal that prompts another revision.

Produce one such memo per reviewer. Do not generate the reviewer memos
themselves, and do not edit the draft.

## Reviewer coverage report

Goal: one consolidated view for the QAM. Inputs: original draft, revised draft,
reviewer memos, and response memos.

Always lay the report out in this order:

1. **Opening.** A title, the document type (see below), and the list of
   reviewers, followed by a short overall responsiveness read: how responsive the
   authors were across the board, and a short list of anything genuinely
   unaddressed that would need another pass.
2. **Summary verdict table.** A table with the count of points in each verdict
   category: addressed, partially addressed, declined with rationale, and not
   addressed. Give the totals, and break the counts down per reviewer when there
   is more than one. It helps to list the point IDs that fall into each category
   so the QAM can jump straight to them.
3. **Each reviewer's memo, verbatim, with your verdicts interleaved.** For each
   reviewer in turn, reproduce their memo in full and verbatim as a clearly
   marked quote (see "Include the reviewer memo verbatim in every output"), in
   the reviewer's own order, labeling each point with its ID (see step 1).
   Directly under each quoted point, record your assessment: the verdict, the
   point's location in the draft by content, and brief evidence (what changed in
   the revised draft, or the author's stated reason for not changing it).

Use a verdict scale that reflects how real responses look, not a binary:

- **addressed**: the revision resolves the point.
- **partially addressed**: some of the point was handled.
- **declined with rationale**: deliberately not changed, with a stated reason
  (scope, document type, disagreement).
- **not addressed**: no change and no reason. This is the only verdict that
  should read as a gap.

Be document-type aware, because it changes what "responsive" means. A RAND
Expert Insights or Perspective piece is shorter and more opinion-oriented than a
formal research report, so many substantial asks are legitimately declined as
out of scope. Judge responsiveness against what the document is, not against an
ideal of addressing everything.

When two reviewers raised the same underlying point, do not drop either memo's
text, since each memo is reproduced in full. Instead note the overlap in your
assessment, referring to the other point by its ID (for example "also raised as
B3"), so the QAM can see the counts are not double-weighting the same concern. Overlap is common on themes
like methodology and premise.

## Formatting conventions

- **Distinguish quoted reviewer text from your additions.** Reviewer text is
  reproduced verbatim and clearly marked as a quote (a Markdown blockquote, or a
  labeled and visually distinct block in a Word deliverable). Your own content
  sits outside the quote under a clear label. This boundary must hold in every
  output (see "Include the reviewer memo verbatim in every output").
- **Make author replies clearly differentiable.** In response memos, the reader
  needs to tell the author's reply from the reviewer's text at a glance. Choose a
  method the output format actually supports: blue text is the RAND convention in
  a Word deliverable, but Markdown and other plain formats do not support color,
  so use a clear textual marker instead (for example a bold "Response:" label).
  Whatever you choose, apply it consistently.
- **Carry over the memo's own header and rating question.** Memos do not share a
  fixed layout, so reproduce whatever header the memo uses rather than imposing a
  standard one, and reproduce the rating question when it appears.
- **Describe locations by content, not by number**, for the reasons in step 2.

## References

- `references/voice-and-tone.md`: how to sound like an experienced research
  colleague. Read it before writing any prose output (see "Tone and voice" above).
