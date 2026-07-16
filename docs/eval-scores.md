# Eval Scores Report

Current Inspect AI eval numbers across every eval in `evals_inspectai/e2e/`.

- **Last updated:** 2026-07-09
- **Total:** 17 evals · 233 runnable samples · run at epochs=3

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
the footnotes for what each scorer checks. **Overall avg** is the unweighted
mean of that eval's per-scorer accuracies (a rough headline number: scorers
measure different things, so it is not a rigorous aggregate). Model-graded
scores use `openai/gpt-5.4` as the grader.

| # | Eval | Samples | Epochs | Scorer results | Overall avg | Date | Log |
|---|------|--------:|-------:|----------------|:-----------:|------|-----|
| 1 | `abbreviation_checker` | 26 | 3 | `structured_output_scorer` 0.998 ±0.001[^abbr-list]<br>`structured_output_scorer1` 1.000 ±0.000[^abbr-sect]<br>`model_graded_check` 0.981 ±0.014[^mg] | **0.993** | 2026-07-09 | [`…_jHzP74HoUt2dKvWSSzCEWS.eval`](./evals/2026-07-09T14-58-26-00-00_abbreviation-checker-e2e_jHzP74HoUt2dKvWSSzCEWS.eval) |
| 2 | `about_this_ger` | 13 | 3 | `structured_output_scorer` 1.000 ±0.000[^ger-preface]<br>`structured_output_scorer1` 1.000 ±0.000[^ger-authors]<br>`model_graded_check` 0.987 ±0.013[^mg] | **0.996** | 2026-07-09 | [`…_kXXKYATn64JhsSM5t4TYF3.eval`](./evals/2026-07-09T16-03-16-00-00_about-this-ger-e2e_kXXKYATn64JhsSM5t4TYF3.eval) |
| 3 | `advocacy_tone_v2` | 14 | 3 | `structured_output_scorer` 1.000 ±0.000[^advv2-titles]<br>`model_graded_check` 0.988 ±0.012[^mg] | **0.994** | 2026-07-09 | [`…_7uj4JtsTMKfZvvux8hca9c.eval`](./evals/2026-07-09T16-07-17-00-00_advocacy-tone-v2-e2e_7uj4JtsTMKfZvvux8hca9c.eval) |
| 4 | `citation_detection` | 17 | 3 | `structured_output_scorer` 0.773 ±0.046[^cit-detect] | **0.773** | 2026-07-09 | [`…_gqybaRsNFVV8tXEpGHoZE3.eval`](./evals/2026-07-09T16-07-19-00-00_citation-detection-e2e_gqybaRsNFVV8tXEpGHoZE3.eval) |
| 5 | `claim_reference_validation_v2` | 7 | 3 | `citation_alignment_match` 1.000 ±0.000[^cr-align]<br>`citation_count_match` 1.000 ±0.000[^cr-count]<br>`model_graded_check` 1.000 ±0.000[^mg] | **1.000** | 2026-07-09 | [`…_HiRkyvQYCUuYJ3g8B8wa9L.eval`](./evals/2026-07-09T16-07-21-00-00_claim-reference-validation-v2-e2e_HiRkyvQYCUuYJ3g8B8wa9L.eval) |
| 6 | `document_structure` | 5 | 3 | `structured_output_scorer` 0.911 ±0.065[^issue-titles]<br>`model_graded_check` 0.733 ±0.194[^mg] | **0.822** | 2026-07-09 | [`…_AvxR8yUFKqbrd7THBoA4PR.eval`](./evals/2026-07-09T16-13-30-00-00_document-structure-e2e_AvxR8yUFKqbrd7THBoA4PR.eval) |
| 7 | `figures_tables_check` | 19 | 3 | `structured_output_scorer` 0.775 ±0.060[^issue-titles]<br>`model_graded_check` 0.956 ±0.031[^mg] | **0.866** | 2026-07-09 | [`…_R79SgLdDysAMuo8LcKMa2R.eval`](./evals/2026-07-09T16-13-33-00-00_figures-tables-check-e2e_R79SgLdDysAMuo8LcKMa2R.eval) |
| 8 | `inference_validation_v2` | 6 | 3 | `structured_output_scorer` 0.889 ±0.111[^inf-count]<br>`model_graded_check` 0.944 ±0.056[^mg] | **0.917** | 2026-07-09 | [`…_bLkqc5z3WXq7u8fk65DLCd.eval`](./evals/2026-07-09T16-13-34-00-00_inference-validation-v2-e2e_bLkqc5z3WXq7u8fk65DLCd.eval) |
| 9 | `literature_review_v2` | 3 | 3 | `structured_output_scorer` 0.963 ±0.037[^score-structure]<br>`model_graded_check` 0.889 ±0.111[^mg] | **0.926** | 2026-07-09 | [`…_fbZ4xxXFiswd9whZPLEEwp.eval`](./evals/2026-07-09T16-18-17-00-00_literature-review-v2-e2e_fbZ4xxXFiswd9whZPLEEwp.eval) |
| 10 | `live_reports_v2` | 3 | 3 | `structured_output_scorer` 1.000 ±0.000[^score-structure]<br>`model_graded_check` 1.000 ±0.000[^mg] | **1.000** | 2026-07-09 | [`…_dNcWGbnu4YMbQvWtqmdrL4.eval`](./evals/2026-07-09T16-18-20-00-00_live-reports-v2-e2e_dNcWGbnu4YMbQvWtqmdrL4.eval) |
| 11 | `methodological_alignment` | 2 | 3 | `structured_output_scorer` 1.000 ±0.000[^meth-analysis]<br>`model_graded_check` 0.917 ±0.083[^mg] | **0.958** | 2026-07-09 | [`…_Pb2TBcXsi4xTtgqGXz2Loo.eval`](./evals/2026-07-09T16-18-22-00-00_methodological-alignment-e2e_Pb2TBcXsi4xTtgqGXz2Loo.eval) |
| 12 | `recommendation_check` | 6 | 3 | `structured_output_scorer` 0.994 ±0.006[^rec-severity]<br>`model_graded_check` 0.944 ±0.035[^mg] | **0.969** | 2026-07-09 | [`…_m49mXFHqKSEvnYaeTpfrAv.eval`](./evals/2026-07-09T16-35-09-00-00_recommendation-check-e2e_m49mXFHqKSEvnYaeTpfrAv.eval) |
| 13 | `reference_downloader` | 31 | 3 | `structured_output_scorer` 0.903 ±0.044[^refdl-conclusion] | **0.903** | 2026-07-09 | [`…_oN2efxg7PdxNHc4fqTrGrS.eval`](./evals/2026-07-09T16-35-10-00-00_reference-downloader-e2e_oN2efxg7PdxNHc4fqTrGrS.eval) |
| 14 | `reference_text_extractor` | 7 | 3 | `structured_output_scorer` 0.922 ±0.051[^refext-refs] | **0.922** | 2026-07-09 | [`…_J9X7AhUPtfGiQDHWUjLet4.eval`](./evals/2026-07-09T16-35-12-00-00_reference-text-extractor-e2e_J9X7AhUPtfGiQDHWUjLet4.eval) |
| 15 | `reference_validation_v2` | 70 | 3 | `structured_output_scorer` 0.843 ±0.042[^refval-result]<br>`model_graded_check` 0.852 ±0.030[^mg] | **0.848** | 2026-07-09 | [`…_FHKPPCyJVbpmziCPy9ZMn9.eval`](./evals/2026-07-09T16-54-14-00-00_reference-validation-v2-e2e_FHKPPCyJVbpmziCPy9ZMn9.eval) |
| 16 | `results_extraction` | 2 | 3 | `structured_output_scorer` 1.000 ±0.000[^res-check]<br>`model_graded_check` 1.000 ±0.000[^mg] | **1.000** | 2026-07-09 | [`…_QgbmBhdvsYSiRup43bSRcG.eval`](./evals/2026-07-09T16-54-16-00-00_results-extraction-e2e_QgbmBhdvsYSiRup43bSRcG.eval) |
| 17 | `reviewer_2` | 2 | 3 | `structured_output_scorer` 1.000 ±0.000[^rev-produced]<br>`model_graded_check` 1.000 ±0.000[^mg] | **1.000** | 2026-07-09 | [`…_Hvsv4KmhjdSPMGFbKCjykd.eval`](./evals/2026-07-09T16-54-17-00-00_reviewer-2-e2e_Hvsv4KmhjdSPMGFbKCjykd.eval) |
| | **Mean across all evals** | | | | **0.935** | | |

## Scorer reference

[^mg]: `model_graded_check` — an LLM grader compares the workflow's full output against the target answer, with partial credit. Some evals grade against a `target_answer` in sample metadata; the mechanism is otherwise identical across evals.
[^abbr-list]: `abbreviation_checker` · deterministic match of the extracted abbreviations list against the target (inline definition, line span, section definition, ignored flag).
[^abbr-sect]: `abbreviation_checker` · deterministic check that the "Abbreviations section found" boolean matches the target.
[^ger-preface]: `about_this_ger` · deterministic match of the flagged preface / "About This" issue titles against the target.
[^ger-authors]: `about_this_ger` · deterministic match of the flagged author-biography issue titles against the target.
[^advv2-titles]: `advocacy_tone_v2` · deterministic match of the count of flagged issue titles against the target.
[^cit-detect]: `citation_detection` · deterministic match of detected in-text citations against the target.
[^cr-align]: `claim_reference_validation_v2` · checks each citation's support label aligns with the target (supported / partially / unsupported / unverifiable).
[^cr-count]: `claim_reference_validation_v2` · checks the number of citations found matches the target.
[^issue-titles]: `document_structure` and `figures_tables_check` · deterministic match of the detected issue titles against the target.
[^inf-count]: `inference_validation_v2` · deterministic match of the count of invalid inferences against the target.
[^score-structure]: `literature_review_v2` and `live_reports_v2` · structural checks averaged into a `[0,1]` score (result present with non-empty report, issue count within the expected band, sane line ranges, citation-like detail when recommendations are expected). Exact sources aren't asserted because web search is non-deterministic.
[^meth-analysis]: `methodological_alignment` · shape check that the analysis ran and populated a reproducibility class plus the field-alignment section (comparison prose is free-form, so exact wording isn't scored).
[^rec-severity]: `recommendation_check` · deterministic match of the counts of recommendations by severity against the target.
[^refdl-conclusion]: `reference_downloader` · deterministic match of the final download conclusion against the target.
[^refext-refs]: `reference_text_extractor` · deterministic match of the extracted bibliographic references against the target.
[^refval-result]: `reference_validation_v2` · deterministic match of the final validation result label against the target.
[^res-check]: `results_extraction` · checks at least the expected number of result sections were extracted and every one carries a recognised reproducibility classification (titles/descriptions are free-form, so exact wording isn't scored).
[^rev-produced]: `reviewer_2` · shape check that both the peer review and the rebuttal were produced and are substantive (the model-graded scorer judges whether they cover strengths, weaknesses, and next steps).
