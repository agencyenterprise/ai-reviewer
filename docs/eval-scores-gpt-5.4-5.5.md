# Eval Scores Report — gpt-5.4 / gpt-5.5 tiers (superseded)

> [!IMPORTANT]
> **These numbers are historical.** They record the three-tier
> `gpt-5.4-mini` / `gpt-5.4` / `gpt-5.5` stack that every agent ran on until
> 28 Aug 2026. The current scores are in
> [`docs/eval-scores.md`](./eval-scores.md), measured on `gpt-5.6-terra`.
>
> This file is kept so the switch can be audited: the `.eval` logs it links are
> still committed, and comparing the two tables shows exactly what the model
> change cost and saved. Do not add new runs here.

Inspect AI eval numbers across every eval in `evals_inspectai/e2e/`, as of the
last run on the gpt-5.4 / gpt-5.5 tiers.

- **Superseded:** 2026-08-28, by `gpt-5.6-terra`
- **Last updated:** 2026-08-27
- **Total:** 18 evals · 227 runnable samples · run at epochs=3

> [!NOTE]
> All evals are **end-to-end**: they trigger the real workflow through the API,
> so the backend must be running (`uv run dev.py`). Scorer numbers are
> **accuracy** (mean over samples, `0.00`–`1.00`), shown as `value ±stderr`.
>
> Run an eval with:
> `uv run inspect eval evals_inspectai/e2e/<eval>/<eval>_e2e.py --epochs=<n>`
>
> The raw Inspect `.eval` log for each recorded run is copied under
> [`docs/evals/`](./evals/) and linked in the **Log** column. Open one with
> `uv run inspect view --log-dir docs/evals`.

## Results

Each eval defines its own scorers. The **Scorer results** column lists every
scorer that eval runs, by its Inspect name, with the per-scorer accuracy — see
the footnotes for what each scorer checks. Expand a cell to read them; the
summary line gives the count and the spread on each side of the deterministic
/ model-graded split, which is what **Overall avg** flattens. That average is
computed over every metric in the cell, not only the ones a reader expands. **Overall avg** is the unweighted
mean of that eval's per-scorer accuracies (a rough headline number: scorers
measure different things, so it is not a rigorous aggregate). Model-graded
scores use `openai/gpt-5.4` as the grader, except the two review-assistant
suites (17 and 18), which pin `openai/gpt-5.6-terra`.

Those two also report one metric per check rather than a single blended score,
so every rule they enforce is listed separately. A broken rule is a defect and a
lower judged score is a trend; averaging them together hides both.

| # | Eval | Samples | Epochs | Scorer results | Overall avg | Date | Log |
|---|------|--------:|-------:|----------------|:-----------:|------|-----|
| 1 | `abbreviation_checker` | 26 | 3 | <details><summary>2 deterministic 0.998–1.000 · 1 judged 0.981</summary>`structured_output_scorer` 0.998 ±0.001[^abbr-list]<br>`structured_output_scorer1` 1.000 ±0.000[^abbr-sect]<br>`model_graded_check` 0.981 ±0.014[^mg]</details> | **0.993** | 2026-07-09 | [`…_jHzP74HoUt2dKvWSSzCEWS.eval`](./evals/2026-07-09T14-58-26-00-00_abbreviation-checker-e2e_jHzP74HoUt2dKvWSSzCEWS.eval) |
| 2 | `about_this_ger` | 13 | 3 | <details><summary>2 deterministic 0.987–1.000 · 1 judged 0.962</summary>`structured_output_scorer` 1.000 ±0.000[^ger-preface]<br>`structured_output_scorer1` 0.987 ±0.013[^ger-authors]<br>`model_graded_check` 0.962 ±0.038[^mg]</details> | **0.983** | 2026-08-27 | [`…_npKRHAhccSxgCC4BMUgyx4.eval`](./evals/2026-08-27T17-17-27-00-00_about-this-ger-e2e_npKRHAhccSxgCC4BMUgyx4.eval) |
| 3 | `advocacy_tone_v2` | 14 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 0.988</summary>`structured_output_scorer` 1.000 ±0.000[^advv2-titles]<br>`model_graded_check` 0.988 ±0.012[^mg]</details> | **0.994** | 2026-08-27 | [`…_gVcoBzoyb2RkGAyyMTmXxe.eval`](./evals/2026-08-27T17-21-14-00-00_advocacy-tone-v2-e2e_gVcoBzoyb2RkGAyyMTmXxe.eval) |
| 4 | `claim_reference_validation_v2` | 7 | 3 | <details><summary>2 deterministic all 1.000 · 1 judged 1.000</summary>`citation_alignment_match` 1.000 ±0.000[^cr-align]<br>`citation_count_match` 1.000 ±0.000[^cr-count]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-07-09 | [`…_HiRkyvQYCUuYJ3g8B8wa9L.eval`](./evals/2026-07-09T16-07-21-00-00_claim-reference-validation-v2-e2e_HiRkyvQYCUuYJ3g8B8wa9L.eval) |
| 5 | `document_structure` | 5 | 3 | <details><summary>1 deterministic 0.933 · 1 judged 0.800</summary>`structured_output_scorer` 0.933 ±0.067[^issue-titles]<br>`model_graded_check` 0.800 ±0.200[^mg]</details> | **0.867** | 2026-08-27 | [`…_8KmjYXwXhLxsh9wZf3iiaR.eval`](./evals/2026-08-27T17-13-55-00-00_document-structure-e2e_8KmjYXwXhLxsh9wZf3iiaR.eval) |
| 6 | `figures_tables_check` | 19 | 3 | <details><summary>1 deterministic 0.771 · 1 judged 0.956</summary>`structured_output_scorer` 0.771 ±0.064[^issue-titles]<br>`model_graded_check` 0.956 ±0.031[^mg]</details> | **0.864** | 2026-08-27 | [`…_UYBwguspWd9v7ho6hYqiDF.eval`](./evals/2026-08-27T17-23-54-00-00_figures-tables-check-e2e_UYBwguspWd9v7ho6hYqiDF.eval) |
| 7 | `inference_validation_v2` | 6 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^inf-count]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-26 | [`…_4S6mpv7uW3Tty4GdXwz4gA.eval`](./evals/2026-08-26T20-30-17-00-00_inference-validation-v2-e2e_4S6mpv7uW3Tty4GdXwz4gA.eval) |
| 8 | `literature_review_v2` | 4 | 3 | <details><summary>1 deterministic 0.972 · 1 judged 0.917</summary>`structured_output_scorer` 0.972 ±0.028[^score-structure]<br>`model_graded_check` 0.917 ±0.083[^mg]</details> | **0.944** | 2026-08-27 | [`…_fX3YfGjX975VkBdNWKAj66.eval`](./evals/2026-08-27T15-48-45-00-00_literature-review-v2-e2e_fX3YfGjX975VkBdNWKAj66.eval) |
| 9 | `live_reports_v2` | 3 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^score-structure]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-27 | [`…_g5NWoxQUscAExStE6VHXb2.eval`](./evals/2026-08-27T17-10-43-00-00_live-reports-v2-e2e_g5NWoxQUscAExStE6VHXb2.eval) |
| 10 | `methodological_alignment` | 2 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 0.917</summary>`structured_output_scorer` 1.000 ±0.000[^meth-analysis]<br>`model_graded_check` 0.917 ±0.083[^mg]</details> | **0.958** | 2026-07-09 | [`…_Pb2TBcXsi4xTtgqGXz2Loo.eval`](./evals/2026-07-09T16-18-22-00-00_methodological-alignment-e2e_Pb2TBcXsi4xTtgqGXz2Loo.eval) |
| 11 | `recommendation_check` | 6 | 3 | <details><summary>1 deterministic 0.994 · 1 judged 0.917</summary>`structured_output_scorer` 0.994 ±0.006[^rec-severity]<br>`model_graded_check` 0.917 ±0.057[^mg]</details> | **0.955** | 2026-08-27 | [`…_58XcSeUXYChQ3qVcbRTyXC.eval`](./evals/2026-08-27T17-15-14-00-00_recommendation-check-e2e_58XcSeUXYChQ3qVcbRTyXC.eval) |
| 12 | `reference_downloader` | 31 | 3 | <details><summary>1 deterministic 0.903</summary>`structured_output_scorer` 0.903 ±0.044[^refdl-conclusion]</details> | **0.903** | 2026-07-09 | [`…_oN2efxg7PdxNHc4fqTrGrS.eval`](./evals/2026-07-09T16-35-10-00-00_reference-downloader-e2e_oN2efxg7PdxNHc4fqTrGrS.eval) |
| 13 | `reference_text_extractor` | 7 | 3 | <details><summary>1 deterministic 0.922</summary>`structured_output_scorer` 0.922 ±0.051[^refext-refs]</details> | **0.922** | 2026-07-09 | [`…_J9X7AhUPtfGiQDHWUjLet4.eval`](./evals/2026-07-09T16-35-12-00-00_reference-text-extractor-e2e_J9X7AhUPtfGiQDHWUjLet4.eval) |
| 14 | `reference_validation_v2` | 70 | 3 | <details><summary>1 deterministic 0.843 · 1 judged 0.852</summary>`structured_output_scorer` 0.843 ±0.042[^refval-result]<br>`model_graded_check` 0.852 ±0.030[^mg]</details> | **0.848** | 2026-07-09 | [`…_FHKPPCyJVbpmziCPy9ZMn9.eval`](./evals/2026-07-09T16-54-14-00-00_reference-validation-v2-e2e_FHKPPCyJVbpmziCPy9ZMn9.eval) |
| 15 | `results_extraction` | 2 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^res-check]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-07-09 | [`…_QgbmBhdvsYSiRup43bSRcG.eval`](./evals/2026-07-09T16-54-16-00-00_results-extraction-e2e_QgbmBhdvsYSiRup43bSRcG.eval) |
| 16 | `reviewer_2` | 2 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^rev-produced]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-27 | [`…_8fwVc4DAF6geqvbirXNmtu.eval`](./evals/2026-08-27T17-08-50-00-00_reviewer-2-e2e_8fwVc4DAF6geqvbirXNmtu.eval) |
| 17 | `reviewer_coverage_report` | 5 | 3 | <details><summary>9 deterministic all 1.000 · 4 judged 0.833–0.967</summary>`verbatim` 1.000 ±0.000<br>`quoted` 1.000 ±0.000<br>`id_scheme` 1.000 ±0.000<br>`self_contained` 1.000 ±0.000<br>`two_part_layout` 1.000 ±0.000<br>`voice` 1.000 ±0.000[^ra-structure]<br>`verdict_table` 1.000 ±0.000<br>`verdict_vocabulary` 1.000 ±0.000<br>`recommendation` 1.000 ±0.000[^rcr-bookkeeping]<br>`verdicts_correct` 0.900 ±0.041<br>`part1_is_decision_grade` 0.933 ±0.041<br>`evidence_and_location` 0.967 ±0.033<br>`scenario_trap` 0.833 ±0.075[^rcr-rubric]</details> | **0.972** | 2026-08-24 | [`…_QQLyTtYCQDafkbvYJ6JSHE.eval`](./evals/2026-08-24T17-17-04-00-00_reviewer-coverage-report-e2e_QQLyTtYCQDafkbvYJ6JSHE.eval) |
| 18 | `revision_planning_summary` | 5 | 3 | <details><summary>6 deterministic all 1.000 · 4 judged 0.833–1.000</summary>`verbatim` 1.000 ±0.000<br>`quoted` 1.000 ±0.000<br>`id_scheme` 1.000 ±0.000<br>`self_contained` 1.000 ±0.000<br>`two_part_layout` 1.000 ±0.000<br>`voice` 1.000 ±0.000[^ra-structure]<br>`locations_by_content` 0.933 ±0.041<br>`part1_triage` 0.900 ±0.067<br>`planning_notes` 1.000 ±0.000<br>`scenario_trap` 0.833 ±0.075[^rps-rubric]</details> | **0.967** | 2026-08-24 | [`…_FUKLiArqfTX2ebmzGjEHuQ.eval`](./evals/2026-08-24T17-12-20-00-00_revision-planning-summary-e2e_FUKLiArqfTX2ebmzGjEHuQ.eval) |
| | **Mean across all evals** | | | | **0.954** | | |

## Scorer reference

[^mg]: `model_graded_check` — an LLM grader compares the workflow's full output against the target answer, with partial credit. Some evals grade against a `target_answer` in sample metadata; the mechanism is otherwise identical across evals.
[^abbr-list]: `abbreviation_checker` · deterministic match of the extracted abbreviations list against the target (inline definition, line span, section definition, ignored flag).
[^abbr-sect]: `abbreviation_checker` · deterministic check that the "Abbreviations section found" boolean matches the target.
[^ger-preface]: `about_this_ger` · deterministic match of the flagged preface / "About This" issue titles against the target.
[^ger-authors]: `about_this_ger` · deterministic match of the flagged author-biography issue titles against the target.
[^advv2-titles]: `advocacy_tone_v2` · deterministic match of the count of flagged issue titles against the target.
[^cr-align]: `claim_reference_validation_v2` · checks each citation's support label aligns with the target (supported / partially / unsupported / unverifiable).
[^cr-count]: `claim_reference_validation_v2` · checks the number of citations found matches the target.
[^issue-titles]: `document_structure` and `figures_tables_check` · deterministic match of the detected issue titles against the target.
[^inf-count]: `inference_validation_v2` · deterministic match of the count of reported invalid inferences against the target. An informational (`none`) issue fails the sample outright rather than counting towards the total: this assessment reports invalid inferences only, so sound reasoning is reported as nothing at all.
[^score-structure]: `literature_review_v2` and `live_reports_v2` · structural checks averaged into a `[0,1]` score (result present with non-empty report, issue count within the expected band, sane line ranges, citation-like detail when recommendations are expected). Exact sources aren't asserted because web search is non-deterministic.
[^meth-analysis]: `methodological_alignment` · shape check that the analysis ran and populated a reproducibility class plus the field-alignment section (comparison prose is free-form, so exact wording isn't scored).
[^rec-severity]: `recommendation_check` · deterministic match of the counts of recommendations by severity against the target.
[^refdl-conclusion]: `reference_downloader` · deterministic match of the final download conclusion against the target.
[^refext-refs]: `reference_text_extractor` · deterministic match of the extracted bibliographic references against the target.
[^refval-result]: `reference_validation_v2` · deterministic match of the final validation result label against the target.
[^res-check]: `results_extraction` · checks at least the expected number of result sections were extracted and every one carries a recognised reproducibility classification (titles/descriptions are free-form, so exact wording isn't scored).
[^ra-structure]: `reviewer_coverage_report` and `revision_planning_summary` · the rules the `review-assistant` skill states outright, checked deterministically against the report's HTML: every reviewer memo reproduced verbatim, that reproduced text sitting inside a marked quote, a valid per-reviewer point-ID scheme numbered from 1 with no gaps, a self-contained document (no external stylesheets, fonts, scripts or images, and no `<script>`), a visible two-part split with a short first part, and none of the generic-assistant tells the `voice-and-tone` skill bans, counted only outside quotes so the reviewer's own punctuation is not held against it.
[^rcr-bookkeeping]: `reviewer_coverage_report` · the arithmetic of the summary table, checked deterministically: all four verdict categories present including the ones that scored zero, every point accounted for exactly once and at one granularity with the stated counts matching the IDs listed, the four-point scale actually used in Part 2 rather than only declared in the table header, and Part 1 stating the sign-off decision outright. Whether an individual verdict is *right* is judged separately.
[^rcr-rubric]: `reviewer_coverage_report` · four judged criteria, each graded in its own call so one weak area cannot colour the rest: each point's verdict is correct against both drafts, Part 1 is decision-grade for a QAM, each verdict cites evidence and a location, and a per-scenario trap criterion for the specific failure that scenario is built to provoke.
[^rps-rubric]: `revision_planning_summary` · four judged criteria, graded one call each: reviewer points located by content rather than by numbers the revision will move, Part 1 triaging substantial asks apart from quick fixes, a planning note under each quoted point carrying scope and location and a suggestion, and a per-scenario trap criterion.
[^rev-produced]: `reviewer_2` · shape check that both the peer review and the rebuttal were produced and are substantive (the model-graded scorer judges whether they cover strengths, weaknesses, and next steps).
