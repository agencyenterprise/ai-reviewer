---
name: citation-support
description: Use this skill to check whether an in-text citation is actually supported by the source it cites — deciding, for each cited claim, whether the cited source explicitly states it, lets it be inferred, only partially supports it, contradicts it, is silent on it, or cannot be checked. Invoke when asked to validate that a document's claims are backed by their cited references (claim / citation substantiation), given access to the cited sources.
---

# Citation Support Validation

You are a citation validation specialist. Your task is to find every statement that cites a reference and verify whether the cited source **actually supports the specific claim** being made — not merely that the source discusses the same topic.

## What is a citation

Documents cite references in two main forms:

1. **Author-year** — e.g. `(Smith, 2020)`, `Smith (2020)`, `(Smith et al., 2020)`. These map directly to a bibliography entry by author and year.

2. **Footnote markers** — e.g. `[2]`, `[^2]`, or a superscript `²`. These are *indirect*: the marker points to a footnote entry elsewhere (often at the bottom of the section or the end of the document, like `2. Smith, 2020, Title`), which in turn identifies the referenced work.
   - **Not every footnote is a citation.** Footnotes are also used for author notes, clarifications, side commentary, and disclaimers. Treat a footnote as a citation only if its content is a bibliographic reference (author, year, title, or similar metadata pointing to an external work). If it is commentary, skip it — do not report it.
   - **Validate the in-text marker, not the footnote entry.** A footnote entry line (e.g. `[^1]: Smith, 2020. Title` or `1. Smith, 2020. Title`) is the *target* of a marker, not a standalone claim. Do not raise an issue for the footnote entry itself — footnote references are validated only through the `[^N]`/`[N]` markers that appear in the body.

**Bibliography sections.** Lines inside a dedicated `References`, `Bibliography`, `Works Cited`, or similar section are reference *entries*, not in-text citations. Do not raise an issue for any line inside such a section.

## How to check a citation

For each cited statement:

1. **Resolve** the citation to the work it refers to (match an author-year marker to its bibliography entry; for a footnote, find the footnote entry, confirm it is a bibliographic reference rather than commentary, then match it to its work).
2. **Locate the evidence** in the cited source. You can read line ranges of both the document and each cited source, search them by keyword or regex (good for specific numbers, statistics, names, or exact phrases), and semantically search the sources (good for conceptual or thematic claims where the wording differs). Read surrounding context in the source as needed.
3. **Judge** whether the source actually supports the specific claim, and assign one of the categories below.

A couple of targeted searches per citation are usually enough. If you cannot find supporting evidence after a few attempts, conclude with the best information you have — bias toward concluding over searching exhaustively.

If a cited statement sits near the start or end of the passage you were given and appears to begin or end mid-sentence or mid-block (table, equation), read the adjacent lines first so you evaluate it with full context.

## Judgment categories

Assign each citation exactly one category:

- **true_explicit** — The claim is directly supported by clear evidence in the source.
- **true_inferred** — The claim is not stated outright, but follows logically from what the source does state.
- **partially_true** — The claim is only partially supported: some parts are missing, unclear, or weakly implied. This includes **scope / qualifier overreach** — the core fact or figure is correct, but the claim generalizes it beyond what the source covers (e.g. the source reports a finding for one region, period, or population and the claim presents it as worldwide or universal). It also covers **mixed or conflicting evidence** — the source both supports and contradicts the claim without a clear resolution.
- **false_contradicted** — The claim is directly contradicted by the source. The source must actively assert something incompatible — a different value, the opposite direction, or an explicit refutation. Source *silence* on part of the claim's scope is not a contradiction.
- **false_not_in_text** — The claim is not supported by the source: it is not mentioned, or there is no evidence for it. This applies even to claims that may be objectively true but are not backed by the cited source.
- **unverifiable** — The cited source was not provided or could not be searched, so the citation cannot be evaluated.

### The specific-claim gate

Before settling on a category, answer one gate question: **setting the general topic aside, does the source actually state the claim's *specific* assertion** — its particular numbers, entities, scope, or the relationship it asserts? A source that merely discusses the broader subject *without* stating the claim's specific content does **not** count.

This is the most common error to avoid: when a source discusses the same topic but does not assert the claim's specific point, the citation is **false_not_in_text**, not partially_true. Finding related or background material is **not** partial support.

### partially_true vs false_contradicted

If your reasoning takes the shape "the source supports X, but the claim's Y is not backed by the source," the category is **partially_true**, not false_contradicted. Reserve **false_contradicted** for cases where the source asserts something that cannot be true at the same time as the claim (a different number, the opposite finding, an explicit refutation).

## Worked examples

Each shows a cited claim, what the source says, and the correct category.

1. **true_explicit** — Claim: "The pilot program cut average emergency-room wait times by 30 percent." Source: "After the pilot launched, average ER wait times fell by 30 percent." The source states the exact figure and direction outright.

2. **true_inferred** — Claim: "The closures fell hardest on rural communities." Source: "Of the 12 clinics shut down, 10 were located in rural counties." The source never says "disproportionate," but the conclusion follows directly from the stated numbers.

3. **partially_true** — Claim: "Microplastics were detected in 93 percent of bottled water samples worldwide." Source: "93 percent of sampled bottles contained microplastics; all samples were sourced from North American retailers, and we make no claims about other regions." The figure is correct, but "worldwide" overreaches the source's North-America-only scope.

4. **partially_true (mixed evidence)** — Claim: "Remote work increases employee productivity." Source: "One survey reported a 30 percent productivity gain under remote work; a second reported a 15 percent decline. The report presents both and does not reconcile them." The source both supports and contradicts the claim without resolution.

5. **false_contradicted** — Claim: "The treaty was ratified in 2019." Source: "The treaty was signed in 2019 but, as of this writing, has not been ratified by any signatory." The source actively asserts the opposite.

6. **false_not_in_text** — Claim: "The agency's budget tripled between 2010 and 2020." Source: discusses the agency's staffing levels and statutory mandate over that period but never mentions budget figures. The claim may be true, but the cited source contains no evidence for it.

7. **unverifiable** — Claim: "The assay achieves roughly 95 percent sensitivity (Wong, 2021)." No supporting file exists for the Wong (2021) reference, so the source cannot be searched.

## Reporting

For each validated citation, report the cited passage, the category above, a brief rationale grounded in what the source actually says, and an actionable suggestion for the author (or "No changes needed" when the citation is well supported). Base every judgment strictly on the cited source — do not invent evidence. Follow the shared reporting conventions in the issues skill (`/skills/issues/SKILL.md`).

## Scope & scale

This skill performs the **in-context substantiation judgment** for citations whose sources you can access. It does not, by itself, solve retrieval at scale: the full Draft Detective workflow around it adds the infrastructure to chunk and embed many full-text reference PDFs, retrieve the relevant passages by semantic similarity, map each bibliography entry to its source file, and fan the judgment out across document sections in parallel. When running this skill standalone, you rely on whatever sources and search tools are available in your environment; when a source is unavailable, the correct category is **unverifiable**.
