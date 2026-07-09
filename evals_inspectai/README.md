# Evals (Inspect AI)

LLM evaluation tasks built with [Inspect AI](https://inspect.ai-safety-institute.org.uk/).

## Folder Structure

```
evals_inspectai/
├── common/                            # Shared utilities (scorers, comparers, API client, solver)
├── internal/                          # Evals that import agents directly from lib/
│   ├── abbreviation_checker/
│   ├── claim_reference_validation_v2/
│   ├── reference_text_extractor/
│   └── reference_validation/
└── e2e/                               # Evals that call the API end-to-end
    ├── abbreviation_checker/
    ├── about_this_ger/
    ├── advocacy_tone_v2/
    ├── citation_detection/
    ├── claim_reference_validation_v2/
    ├── document_structure/
    ├── figures_tables_check/
    ├── inference_validation_v2/
    ├── literature_review_v2/
    ├── live_reports_v2/
    ├── methodological_alignment/
    ├── recommendation_check/
    ├── reference_downloader/
    ├── reference_text_extractor/
    ├── reference_validation/
    ├── results_extraction/
    └── reviewer_2/
```

**Internal evals** invoke agents directly via Python imports. They require the full
codebase and its dependencies.

**E2E evals** trigger workflows through the HTTP API. They only depend on
`evals_inspectai/common/`, making them portable to a standalone repository in
the future.

## Available Evals

Each eval directory contains a task module (e.g. `<name>.py` for internal, `<name>_e2e.py` for e2e) and its dataset.

### Internal

| Eval | Description |
|------|-------------|
| `internal/abbreviation_checker` | Detects abbreviation compliance issues (missing inline definitions, abbreviations not in the Abbreviations section). |
| `internal/claim_reference_validation_v2` | Judges whether each cited source supports the claim attached to it (supported / partially supported / unsupported / unverifiable). |
| `internal/reference_text_extractor` | Extracts bibliographic reference entries from document reference/bibliography sections. |
| `internal/reference_validation` | Classifies bibliography items as `valid`, `not_found`, or `found_with_inconsistencies`. |

### E2E

Each e2e eval runs the corresponding workflow end-to-end through the API.

| Eval | Description |
|------|-------------|
| `e2e/abbreviation_checker` | Abbreviation compliance checks, run via the full workflow. |
| `e2e/about_this_ger` | Validates the preface / "About This" section and author biographies against publication requirements. |
| `e2e/advocacy_tone_v2` | Flags trigger words, advocacy language, and subjective tone. |
| `e2e/citation_detection` | Detects in-text citations and maps them to their references. |
| `e2e/claim_reference_validation_v2` | Judges whether each cited source supports its claim. |
| `e2e/document_structure` | Checks that required sections are present (Document Contents). |
| `e2e/figures_tables_check` | Verifies figures and tables are titled, numbered, and cross-referenced. |
| `e2e/inference_validation_v2` | Flags invalid inferences, logical fallacies, and unsupported conclusions. |
| `e2e/literature_review_v2` | Finds relevant academic sources — supporting and conflicting — that aren't already cited. |
| `e2e/live_reports_v2` | Finds sources published after the document's date that may update or contradict its claims. |
| `e2e/methodological_alignment` | Compares the document's methodology against standard field practice (uses web search). |
| `e2e/recommendation_check` | Checks whether each recommendation is backed by the document's own findings. |
| `e2e/reference_downloader` | Searches for and downloads the full text of a reference. |
| `e2e/reference_text_extractor` | Extracts bibliographic reference entries, run via the full workflow. |
| `e2e/reference_validation` | Reference Error Checker — verifies each citation exists online and matches public sources. |
| `e2e/results_extraction` | Reproducibility Check — extracts main results and classifies each by reproducibility. |
| `e2e/reviewer_2` | Produces a senior-reviewer-style critique and a devil's-advocate rebuttal. |

## Running Evals

All commands should be run from the project root.

### Internal evals

```bash
# Run a specific eval
uv run inspect eval evals_inspectai/internal/reference_validation/reference_validation.py

# Choose models
uv run inspect eval evals_inspectai/internal/abbreviation_checker/abbreviation_checker.py --model openai/gpt-5.4

# Multiple epochs and sample limit
uv run inspect eval evals_inspectai/internal/reference_validation/reference_validation.py --epochs=2 --limit=5
```

### E2E evals

E2E evals require a running API server. Configure the following environment
variables before running:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EVAL_API_BASE_URL` | No | `http://localhost:8000` | Base URL of the API server |
| `EVAL_API_AUTH_TOKEN` | One of these | — | Pre-minted JWT Bearer token |
| `AUTH_SECRET` | One of these | — | Secret used to auto-generate a JWT |

```bash
# Start the API server first
uv run dev.py

# Run an e2e eval
uv run inspect eval evals_inspectai/e2e/abbreviation_checker/abbreviation_checker_e2e.py
```

## Viewing Results

Launch the Inspect AI log viewer to browse evaluation results interactively:

```bash
uv run inspect view
```

## Resources

- [Inspect AI Documentation](https://inspect.ai-safety-institute.org.uk/docs/)
