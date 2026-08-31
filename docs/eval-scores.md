# Eval Scores Report

Current Inspect AI eval numbers across every eval in `evals_inspectai/e2e/`.

- **Last updated:** 2026-08-31
- **Model:** `gpt-5.6-terra`, on every agent
- **Total:** 18 evals · 235 runnable samples · run at epochs=3

> [!IMPORTANT]
> **This is the current baseline, measured on `gpt-5.6-terra`.** On 28 Aug 2026
> every agent moved off the three-tier `gpt-5.4-mini` / `gpt-5.4` / `gpt-5.5`
> stack onto a single model. The numbers those tiers last scored are kept in
> [`docs/eval-scores-gpt-5.4-5.5.md`](./eval-scores-gpt-5.4-5.5.md) for
> comparison; they no longer describe the running system.

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
> `uv run inspect view --log-dir docs/evals`. Where an eval is recorded from
> more than one invocation of the same configuration, every log is linked and
> the figures are pooled over all of their sample-runs.

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

Three suites — `results_extraction` (15) and the two review-assistant ones
(17 and 18) — report one metric per check rather than a single blended score, so
every rule they enforce is listed separately. A broken rule is a defect and a
lower judged score is a trend; averaging them together hides both.

Every run below completed in full: no sample was dropped, errored or retried.
`results_extraction` is recorded from three invocations of one configuration
(90 sample-runs); every other eval is a single run.

| # | Eval | Samples | Epochs | Scorer results | Overall avg | Date | Log |
|---|------|--------:|-------:|----------------|:-----------:|------|-----|
| 1 | `abbreviation_checker` | 26 | 3 | <details><summary>2 deterministic 0.999–1.000 · 1 judged 0.987</summary>`structured_output_scorer` 0.999 ±0.001[^abbr-list]<br>`structured_output_scorer1` 1.000 ±0.000[^abbr-sect]<br>`model_graded_check` 0.987 ±0.009[^mg]</details> | **0.995** | 2026-08-26 | [`…_9L7LFJgP4rM2Z6oAmDgCg8.eval`](./evals/2026-08-26T13-36-25-00-00_abbreviation-checker-e2e_9L7LFJgP4rM2Z6oAmDgCg8.eval) |
| 2 | `about_this_ger` | 13 | 3 | <details><summary>2 deterministic 0.983–0.987 · 1 judged 0.936</summary>`structured_output_scorer` 0.983 ±0.017[^ger-preface]<br>`structured_output_scorer1` 0.987 ±0.013[^ger-authors]<br>`model_graded_check` 0.936 ±0.052[^mg]</details> | **0.969** | 2026-08-26 | [`…_RDABwXSRrsEUEeTGCDyPAX.eval`](./evals/2026-08-26T13-42-24-00-00_about-this-ger-e2e_RDABwXSRrsEUEeTGCDyPAX.eval) |
| 3 | `advocacy_tone_v2` | 14 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^advv2-titles]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-26 | [`…_TR6MVXLpKk5aABsjrrd3BG.eval`](./evals/2026-08-26T16-59-19-00-00_advocacy-tone-v2-e2e_TR6MVXLpKk5aABsjrrd3BG.eval) |
| 4 | `claim_reference_validation_v2` | 7 | 3 | <details><summary>2 deterministic all 1.000 · 1 judged 1.000</summary>`citation_alignment_match` 1.000 ±0.000[^cr-align]<br>`citation_count_match` 1.000 ±0.000[^cr-count]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-26 | [`…_P6c7epQuUUuYnrhLJszKwY.eval`](./evals/2026-08-26T16-55-04-00-00_claim-reference-validation-v2-e2e_P6c7epQuUUuYnrhLJszKwY.eval) |
| 5 | `document_structure` | 5 | 3 | <details><summary>1 deterministic 0.933 · 1 judged 0.800</summary>`structured_output_scorer` 0.933 ±0.067[^issue-titles]<br>`model_graded_check` 0.800 ±0.200[^mg]</details> | **0.867** | 2026-08-28 | [`…_gVQDPn5E5ru4cJJdYpuGBk.eval`](./evals/2026-08-28T18-11-07-00-00_document-structure-e2e_gVQDPn5E5ru4cJJdYpuGBk.eval) |
| 6 | `figures_tables_check` | 19 | 3 | <details><summary>1 deterministic 0.710 · 1 judged 0.851</summary>`structured_output_scorer` 0.710 ±0.068[^issue-titles]<br>`model_graded_check` 0.851 ±0.044[^mg]</details> | **0.780** | 2026-08-28 | [`…_Z9HXQpWvUiJedwbjCZCXDn.eval`](./evals/2026-08-28T18-18-27-00-00_figures-tables-check-e2e_Z9HXQpWvUiJedwbjCZCXDn.eval) |
| 7 | `inference_validation_v2` | 6 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^inf-count]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-27 | [`…_ETnaSF9iyWUPQYf6Ac7VHm.eval`](./evals/2026-08-27T15-39-52-00-00_inference-validation-v2-e2e_ETnaSF9iyWUPQYf6Ac7VHm.eval) |
| 8 | `literature_review_v2` | 4 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 0.958</summary>`structured_output_scorer` 1.000 ±0.000[^score-structure]<br>`model_graded_check` 0.958 ±0.042[^mg]</details> | **0.979** | 2026-08-26 | [`…_jkRHzj4yivsY66vtVbCo4a.eval`](./evals/2026-08-26T16-39-44-00-00_literature-review-v2-e2e_jkRHzj4yivsY66vtVbCo4a.eval) |
| 9 | `live_reports_v2` | 3 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^score-structure]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-26 | [`…_B8DravaK7UWAGrngodBEco.eval`](./evals/2026-08-26T16-36-22-00-00_live-reports-v2-e2e_B8DravaK7UWAGrngodBEco.eval) |
| 10 | `methodological_alignment` | 2 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^meth-analysis]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-26 | [`…_gUqTHjY4RMC2DJyPMuLers.eval`](./evals/2026-08-26T13-47-33-00-00_methodological-alignment-e2e_gUqTHjY4RMC2DJyPMuLers.eval) |
| 11 | `recommendation_check` | 6 | 3 | <details><summary>1 deterministic 0.988 · 1 judged 0.917</summary>`structured_output_scorer` 0.988 ±0.012[^rec-severity]<br>`model_graded_check` 0.917 ±0.083[^mg]</details> | **0.953** | 2026-08-26 | [`…_4PUbGQZhFYt9PfBHf8TyXe.eval`](./evals/2026-08-26T16-52-03-00-00_recommendation-check-e2e_4PUbGQZhFYt9PfBHf8TyXe.eval) |
| 12 | `reference_downloader` | 31 | 3 | <details><summary>1 deterministic 0.849</summary>`structured_output_scorer` 0.849 ±0.060[^refdl-conclusion]</details> | **0.849** | 2026-08-28 | [`…_YHhh9v2dMmLZVkBdoGLaNi.eval`](./evals/2026-08-28T18-24-42-00-00_reference-downloader-e2e_YHhh9v2dMmLZVkBdoGLaNi.eval) |
| 13 | `reference_text_extractor` | 7 | 3 | <details><summary>1 deterministic 0.878</summary>`structured_output_scorer` 0.878 ±0.084[^refext-refs]</details> | **0.878** | 2026-08-28 | [`…_EcCoBLxfCqnUGhVwdMwCzR.eval`](./evals/2026-08-28T18-12-45-00-00_reference-text-extractor-e2e_EcCoBLxfCqnUGhVwdMwCzR.eval) |
| 14 | `reference_validation_v2` | 70 | 3 | <details><summary>1 deterministic 0.814 · 1 judged 0.824</summary>`structured_output_scorer` 0.814 ±0.044[^refval-result]<br>`model_graded_check` 0.824 ±0.033[^mg]</details> | **0.819** | 2026-08-26 | [`…_LVNQd5h6f5bUWnD2eYogUb.eval`](./evals/2026-08-26T17-17-18-00-00_reference-validation-v2-e2e_LVNQd5h6f5bUWnD2eYogUb.eval) |
| 15 | `results_extraction`[^res-devsplit] | 10 | 3 ×3 | <details><summary>11 deterministic 0.952–1.000 · 2 judged 0.867–0.956</summary>`report` 1.000 ±0.000<br>`inventory_table` 1.000 ±0.000<br>`result_count` 0.978 ±0.016<br>`labels` 1.000 ±0.000<br>`severity_split` 1.000 ±0.000<br>`line_ranges` 1.000 ±0.000<br>`no_duplicates` 1.000 ±0.000[^res-shape]<br>`completeness` 0.989 ±0.007<br>`class_accuracy` 0.952 ±0.020<br>`no_extras` 0.975 ±0.008<br>`severity_ordering` 1.000 ±0.000[^res-truth]<br>`classification_grounded` 0.956 ±0.015<br>`sample_expectations` 0.867 ±0.030[^res-rubric]</details> | **0.978** | 2026-08-31 | [`…_ZTxbpeH5XEf2cpsh5ZoRDg.eval`](./evals/2026-08-31T21-00-24-00-00_results-extraction-e2e_ZTxbpeH5XEf2cpsh5ZoRDg.eval)<br>[`…_YMwiUPkKZwTUdahemi3akE.eval`](./evals/2026-08-31T21-05-44-00-00_results-extraction-e2e_YMwiUPkKZwTUdahemi3akE.eval)<br>[`…_ZVwrG4t2tTbjbj6YbvCsWt.eval`](./evals/2026-08-31T21-10-47-00-00_results-extraction-e2e_ZVwrG4t2tTbjbj6YbvCsWt.eval) |
| 16 | `reviewer_2` | 2 | 3 | <details><summary>1 deterministic 1.000 · 1 judged 1.000</summary>`structured_output_scorer` 1.000 ±0.000[^rev-produced]<br>`model_graded_check` 1.000 ±0.000[^mg]</details> | **1.000** | 2026-08-26 | [`…_i3Bm2FbzhmJAwqas6MUyri.eval`](./evals/2026-08-26T14-14-47-00-00_reviewer-2-e2e_i3Bm2FbzhmJAwqas6MUyri.eval) |
| 17 | `reviewer_coverage_report` | 5 | 3 | <details><summary>9 deterministic all 1.000 · 4 judged 0.800–0.967</summary>`verbatim` 1.000 ±0.000<br>`quoted` 1.000 ±0.000<br>`id_scheme` 1.000 ±0.000<br>`self_contained` 1.000 ±0.000<br>`two_part_layout` 1.000 ±0.000<br>`voice` 1.000 ±0.000[^ra-structure]<br>`verdict_table` 1.000 ±0.000<br>`verdict_vocabulary` 1.000 ±0.000<br>`recommendation` 1.000 ±0.000[^rcr-bookkeeping]<br>`verdicts_correct` 0.800 ±0.062<br>`part1_is_decision_grade` 0.900 ±0.041<br>`evidence_and_location` 0.967 ±0.033<br>`scenario_trap` 0.800 ±0.133[^rcr-rubric]</details> | **0.959** | 2026-08-26 | [`…_nnzWgW7JK6KsFFqorqCSck.eval`](./evals/2026-08-26T15-01-34-00-00_reviewer-coverage-report-e2e_nnzWgW7JK6KsFFqorqCSck.eval) |
| 18 | `revision_planning_summary` | 5 | 3 | <details><summary>6 deterministic all 1.000 · 4 judged 0.800–1.000</summary>`verbatim` 1.000 ±0.000<br>`quoted` 1.000 ±0.000<br>`id_scheme` 1.000 ±0.000<br>`self_contained` 1.000 ±0.000<br>`two_part_layout` 1.000 ±0.000<br>`voice` 1.000 ±0.000[^ra-structure]<br>`locations_by_content` 0.967 ±0.033<br>`part1_triage` 0.800 ±0.062<br>`planning_notes` 1.000 ±0.000<br>`scenario_trap` 0.800 ±0.097[^rps-rubric]</details> | **0.957** | 2026-08-26 | [`…_iUkias5YSUsBuY2EoRoKqm.eval`](./evals/2026-08-26T15-11-52-00-00_revision-planning-summary-e2e_iUkias5YSUsBuY2EoRoKqm.eval) |
| | **Mean across all evals** | | | | **0.943** | | |

## What the model switch changed

Against the last gpt-5.4 / gpt-5.5 figures. Six evals are unchanged, four
improved and eight fell, for a suite mean **0.009 lower**. Only one movement is
large enough to matter on its own.

| Eval | gpt-5.4 / gpt-5.5 | gpt-5.6-terra | Δ |
|------|------------------:|--------------:|--:|
| `abbreviation_checker` | 0.993 | 0.995 | +0.002 |
| `about_this_ger` | 0.983 | 0.969 | -0.014 |
| `advocacy_tone_v2` | 0.994 | 1.000 | +0.006 |
| `claim_reference_validation_v2` | 1.000 | 1.000 | — |
| `document_structure` | 0.867 | 0.867 | — |
| `figures_tables_check` | 0.864 | 0.780 | -0.084 |
| `inference_validation_v2` | 1.000 | 1.000 | — |
| `literature_review_v2` | 0.944 | 0.979 | +0.035 |
| `live_reports_v2` | 1.000 | 1.000 | — |
| `methodological_alignment` | 0.958 | 1.000 | +0.042 |
| `recommendation_check` | 0.955 | 0.953 | -0.002 |
| `reference_downloader` | 0.903 | 0.849 | -0.054 |
| `reference_text_extractor` | 0.922 | 0.878 | -0.044 |
| `reference_validation_v2` | 0.848 | 0.819 | -0.029 |
| `results_extraction` | 1.000 | 1.000 | — |
| `reviewer_2` | 1.000 | 1.000 | — |
| `reviewer_coverage_report` | 0.972 | 0.959 | -0.013 |
| `revision_planning_summary` | 0.967 | 0.957 | -0.010 |
| **Mean across all evals** | **0.954** | **0.945** | **-0.009** |

Four things worth knowing before reading that table:

- **`results_extraction` is no longer comparable, in either direction.** Both
  columns read 1.000 because that is what its old scorers measured: 2 samples,
  every expected result not-reproducible, and a deterministic check that counted
  results and validated a class string. The eval was rebuilt on 31 Aug — 10
  samples, ground-truth inventories, 13 per-check metrics — and now reads 0.978,
  pooled over three invocations. The two numbers measure different things and
  differencing them means nothing. This is also why the suite mean in the table
  above (0.945) and the one in the Results table (0.943) differ: the table above
  is a frozen record of the model switch, the Results table is current.
- **`figures_tables_check` is the one real regression.** It fell 8.4 points, on
  both of its scorers, and it is the only movement here that was measured twice
  and held both times — 0.798 on 26 Aug and 0.780 on 28 Aug. The deterministic
  issue-title match moving means terra flags different figures and tables, not
  that a grader changed its mind. This is a known cost of the switch, not noise.
- **The small evals swing.** `document_structure` read 0.778 on 26 Aug and
  0.867 — exactly its old figure — on 28 Aug, with nothing changed between the
  runs. At 15 runs with a judged scorer carrying ±0.200, single readings on the
  sub-20-run evals should not be read as trends in either direction.
- **The review-assistant suites now grade themselves.** `reviewer_coverage_report`
  and `revision_planning_summary` pin `openai/gpt-5.6-terra` as their judge,
  which is now also the model under test. Their judged criteria should be read
  with that in mind; their deterministic rules, all of which still pass at 1.000,
  are unaffected.

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
[^res-devsplit]: `results_extraction` · **read this as a dev-split figure, not an unbiased estimate.** These ten samples were built and then tuned against this workflow across roughly fifteen runs on 31 Aug: three documents, the skill's class-selection guidance, the judged criteria and the workflow's reasoning effort were all edited while these same samples were being scored. Eight of the ten documents are synthetic. Two independent audits found ground-truth defects that had been scoring the workflow *down for being right* — an engineering estimate that did not follow from its own coefficients, a reservoir yield its own inflow record could not supply, a matching variable the document never stated, and paid-access sources cited in a fixture whose expected class requires openly available ones. Each is fixed, and `tests/unit/evals/test_reproducibility_dataset_arithmetic.py` plus `evals_inspectai/e2e/results_extraction/verify_reservoir_yields.py` now re-derive the numbers behind every fully-reproducible expectation. But a dataset repaired wherever the system under test objected to it is a dataset biased towards that system: the gain from 0.899 to 0.978 across this day is mostly eval error being removed, not the workflow improving, and nothing here has been measured on samples the workflow has never influenced. Held-out samples are the outstanding work — blind-authored documents, one adversarial case that falsely claims reproducibility, and one full-length real report. Until those exist, treat this eval as a tripwire for large regressions rather than a quality score.
[^res-shape]: `results_extraction` · seven deterministic checks on the shape of the delivery: a substantive markdown report, an inventory table in it (found by the reproducibility column its header names, not by being the widest table in the report) with at least a row per reported result, at least as many results as the dataset declares, a recognised reproducibility label in every issue title, the severity split the skill mandates (anything reproducible is informational `none`; only not-reproducible carries a real severity), line ranges that land inside the document, and no result reported twice. None of these say whether a classification is *right*.
[^res-truth]: `results_extraction` · four deterministic checks against the dataset's own ground-truth inventory, which names every result each document presents together with the class it should be given and how much the document rests on it: whether every expected result was found, the fraction given the right reproducibility class, whether anything was reported that the document does not present as a result, and whether the severities of the non-reproducible results are ordered by importance. Which of low/medium/high a result earns is the agent's judgement, so only the ordering is asserted, not the level.
[^res-rubric]: `results_extraction` · two judged criteria, each graded three times with the median taken, because single grader calls disagreed with themselves across repeats of an unchanged output. `classification_grounded` asks only whether each rationale names the ingredients present or missing and how a reader would obtain them; it is given the four class definitions and the list of absences the skill says are *not* deficiencies, since without them the grader marked down rationales for correctly declining to treat an unrendered figure or a fixed-seed simulation as a gap. `sample_expectations` is the dataset's own per-sample rubric. Both use a requirement-shaped prompt rather than Inspect's model-graded-fact template, which asks whether the submission *contains* the expert answer and misgrades a criterion that states a property the output must have.
[^ra-structure]: `reviewer_coverage_report` and `revision_planning_summary` · the rules the `review-assistant` skill states outright, checked deterministically against the report's HTML: every reviewer memo reproduced verbatim, that reproduced text sitting inside a marked quote, a valid per-reviewer point-ID scheme numbered from 1 with no gaps, a self-contained document (no external stylesheets, fonts, scripts or images, and no `<script>`), a visible two-part split with a short first part, and none of the generic-assistant tells the `voice-and-tone` skill bans, counted only outside quotes so the reviewer's own punctuation is not held against it.
[^rcr-bookkeeping]: `reviewer_coverage_report` · the arithmetic of the summary table, checked deterministically: all four verdict categories present including the ones that scored zero, every point accounted for exactly once and at one granularity with the stated counts matching the IDs listed, the four-point scale actually used in Part 2 rather than only declared in the table header, and Part 1 stating the sign-off decision outright. Whether an individual verdict is *right* is judged separately.
[^rcr-rubric]: `reviewer_coverage_report` · four judged criteria, each graded in its own call so one weak area cannot colour the rest: each point's verdict is correct against both drafts, Part 1 is decision-grade for a QAM, each verdict cites evidence and a location, and a per-scenario trap criterion for the specific failure that scenario is built to provoke.
[^rps-rubric]: `revision_planning_summary` · four judged criteria, graded one call each: reviewer points located by content rather than by numbers the revision will move, Part 1 triaging substantial asks apart from quick fixes, a planning note under each quoted point carrying scope and location and a suggestion, and a per-scenario trap criterion.
[^rev-produced]: `reviewer_2` · shape check that both the peer review and the rebuttal were produced and are substantive (the model-graded scorer judges whether they cover strengths, weaknesses, and next steps).
