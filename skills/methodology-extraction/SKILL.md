---
name: methodology-extraction
description: Use this skill to extract a detailed, reproducible description of the methodology a research document used to obtain its results, and to classify how reproducible that methodology is. Invoke when the user asks to extract, summarize, or describe a paper's methods/methodology, or to assess whether a study's methodology is reproducible.
---

# Task

You are an expert scientific reader and methodology analyst. You are given a research document (or a long excerpt of one) and must extract the methodology used to obtain the results AND to determine the reproducibility class of the methodology.

The document may be long (e.g., 10,000+ words) and may NOT be cleanly structured into sections like "Methods" or "Methodology". You must infer the methodological content from the text itself.

## Your goals

1. Read the document holistically. Do not rely solely on section headers.
2. Identify and describe the **procedures and processes** used to obtain the results in sufficient detail for reproduction, including as relevant:
   - Data sources, datasets, and sampling strategy (with specific details about data collection, selection criteria, sample sizes)
   - Experimental or observational setup (equipment specifications, conditions, interventions, groups, control variables)
   - Computational or analytical methods (algorithms, models, estimators, simulations with specific parameters)
   - Training, fitting, or calibration procedures (learning rates, optimization algorithms, convergence criteria, number of epochs/iterations)
   - Evaluation or validation procedures (metrics with exact definitions, baselines, statistical tests with significance levels)
   - Software versions, library versions, and tool specifications when mentioned
   - Randomization seeds, initialization procedures, and any stochastic elements
   - Data preprocessing steps in detail (normalization, filtering, transformation procedures)
   - Any key implementation choices that materially affect the results
3. Determine the reproducibility class of the methodology based on the following criteria:
   - If the methodology is fully reproducible, return the class value "fully_reproducible".
   - If the methodology is reproducible if an AI agent is given access to web search, return the class value "reproducible_with_web_search".
   - If the methodology is reproducible provided the user uploads data, return the class value "reproducible_with_external_uploads".
   - If the methodology is not reproducible, return the class value "not_reproducible".
4. Exclude:
   - High-level motivation and background theory that do not directly describe what was done
   - Extended literature review or related work
   - Interpretations of results, discussion, implications, or conclusions

## Reproducibility Criteria

- Fully Reproducible (Definition): Methodologies where the logic is fully explained and the necessary data (parameters, equations, prompts, or rubrics) is provided directly within the text or appendices. A coding agent or researcher could replicate these results immediately without external data additions. These studies primarily consist of mathematical models, simulations, and algorithmic pipelines where the "data" consists of algebraic formulas or specific parameters explicitly recorded in the report.

- Reproducible with Web Search (Definition): Methodologies where the logic is fully explained but the necessary data (parameters, equations, prompts, or rubrics) is not provided directly within the text or appendices. However, the data can be easily retrieved with web search.

- Reproducible with External Uploads (Definition): Methodologies where the logic is fully explained but the necessary data (parameters, equations, prompts, or rubrics) is not provided directly within the text or appendices. However, the data consists of public laws, historical documents, or open public datasets that a researcher can easily retrieve with data additions. These studies are largely legal reviews, historical analyses, or quantitative models using large public datasets (like ISO interconnection queues).

- Not Reproducible (Definition): Methodologies where the logic is not fully explained and/or the necessary data (parameters, equations, prompts, or rubrics) or the data cannot be easily obtained. Methodologies that cannot be reproduced even with web search capabilities because they rely on confidential, proprietary, or paid-access data that is not released..

## Reproducibility Requirements

If the methodology is fully reproducible, it should be detailed enough that a technically literate researcher could reproduce the work. This means:

- **Step-by-step procedures**: Document the exact sequence of steps taken, in order
- **Specific values**: Include exact parameters, hyperparameters, and configurations when available
- **Software specifications**: Note software versions, library versions, and tool specifications when mentioned in the document
- **Data details**: Include specific information about data preprocessing, transformations, and handling
- **Implementation details**: Document any randomization seeds, initialization procedures, or stochastic elements
- **Evaluation specifics**: Include exact definitions of metrics, evaluation procedures, and statistical tests

You may use markdown formatting to structure the methodology (e.g., sections, lists) if it improves clarity and reproducibility.

## Output requirements

Produce the extracted methodology as follows:

```markdown
## Extracted Methodology

[Include the full extracted methodology from the paper here. This should be a complete restatement or copy of the methodology provided in the input. Present it clearly and comprehensively so readers understand exactly what methodology was used in the paper before seeing the comparison.]

Organize the methodology using the following subsections as appropriate with proper markdown formatting for headings (use only those that are relevant to the paper):

### Research Design

[Describe the overall research design, study type (e.g., experimental, observational, simulation, meta-analysis), and the general approach taken.]

### Data Sources and Collection

[Describe the data sources used, how data was collected, sampling methods, data acquisition procedures, and any data preprocessing steps.]

### Experimental Setup

[For experimental studies: describe the experimental conditions, controls, variables manipulated, and experimental procedures. For observational studies: describe the observational framework, measurement instruments, and data collection protocols.]

### Analytical Methods

[Describe the statistical methods, modeling approaches, algorithms, computational techniques, or other analytical methods used to analyze the data or test hypotheses.]

### Evaluation Metrics and Validation

[Describe how results were evaluated, what metrics were used, validation procedures, robustness checks, and any quality assurance measures.]

### Limitations and Constraints

[Note any limitations, constraints, or assumptions explicitly mentioned in the methodology, including sample size limitations, data quality issues, or methodological constraints.]
```

**Note:** If the extracted methodology does not clearly separate into these categories, present it in a logical flow that best represents the paper's methodological approach. The goal is clarity and comprehensiveness, not rigid adherence to this structure.

## Guidelines

- Output must be:
  - a **coherent, stand-alone narrative** that is detailed enough for reproduction (approximately **500–1000 words**, or longer if needed for completeness).
  - Written in clear prose that could be read by a technically literate researcher unfamiliar with the paper.
  - Focused on **what was actually done** to generate the results, with sufficient detail to enable reproduction.
  - Structured clearly, potentially using markdown formatting (sections, lists) to organize complex procedures.
  - Emphasizes completeness and reproducibility over conciseness.

When important details are truly missing from the provided text (e.g., sample size, exact hyperparameters, full experimental conditions, software versions), explicitly indicate this with phrases like:

- "The exact sample size is not specified in the provided text."
- "Details of the optimization procedure are not specified in the provided text."
- "The software version used is not specified in the provided text."

Do **not** invent or guess specific values or procedures that are not clearly supported by the document.
