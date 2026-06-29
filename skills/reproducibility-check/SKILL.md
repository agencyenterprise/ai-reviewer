---
name: reproducibility-check
description: Use this skill to extract a research document's main results and classify how reproducible each one is (fully reproducible, reproducible with web search, reproducible with external uploads, or not reproducible) from the information in the paper. Invoke when the user asks whether their results could be reproduced from the document alone, or to assess the reproducibility of a paper's findings.
---

# Task
You are an expert scientific reader and results analyst. You will be given a research document (or a long excerpt of one), and must extract the main results of the document AND determine whether these each of these main results is reproducible given the information provided in the paper.

"Results" are defined as any qualitative, mathematical, or quantitative end-points of an analysis. Things that aren't included in results are assumptions or initial conditions.

The document may be long (e.g., 10,000+ words) and may NOT be cleanly structured into sections labeled as "Results."

## Your goals

1. Read the document holistically. Do not rely solely on section headers.
2. Identify the main results of the paper. "Results" are defined as any qualitative, mathematical, or quantitative end-points of an analysis. Things that aren't included in results are assumptions or initial conditions.
3. Determine the "Result Type"
    - Figure: The result is a figure within the text
    - Table: The result is a table within the text
    - Equation: The result is a final equation
    - Text: The result is a section of text (e.g., numerical statements within text)
    - Algorithm: The result is an algorithm stated in pseudo-code in text
    - Other: The result doesn't fit in any of the given categories
4. Determine the reproducibility class of the result based on the following criteria:
   - If the result is fully reproducible, return the class value "fully_reproducible".
   - If the result is reproducible if an AI agent is given access to web search, return the class value "reproducible_with_web_search".
   - If the result is reproducible provided the user uploads data, return the class value "reproducible_with_external_uploads".
   - If the result is not reproducible, return the class value "not_reproducible".
   Provide a rationale for this categorization and explain what would be needed to make the result fully reproducible
5. Describe the result in no more than five sentences
6. Provide the location of the result.  This should be a description of the page number, figure number, table number, equation number, etc
7. Provide a descriptive title for the result


## Results extraction guidelines

Results are sometimes represented as equations, figures, tables, or specific numerical quantities stated within the text. In general, they are defined as the end-points of some quantitative or qualitative analysis. For the results extraction, we want to extract results and put them within the same section according to their natural grouping within the paper. For example, a table could contain dozens of values, but it should represent a single result. Similarly with figures. Each of these particular results should have a reproducibility category.

## Reproducibility Criteria

- Fully Reproducible (Definition): Methodologies where the logic is fully explained and the necessary data (parameters, equations, prompts, or rubrics) is provided directly within the text or appendices. A coding agent or researcher could replicate these results immediately without external data additions. These studies primarily consist of mathematical models, simulations, and algorithmic pipelines where the "data" consists of algebraic formulas or specific parameters explicitly recorded in the report.

- Reproducible with Web Search (Definition): Methodologies where the logic is fully explained but the necessary data (parameters, equations, prompts, or rubrics) is not provided directly within the text or appendices. However, the data can be easily retrieved with web search.

- Reproducible with External Uploads (Definition): Methodologies where the logic is fully explained but the necessary data (parameters, equations, prompts, or rubrics) is not provided directly within the text or appendices. However, the data consists of public laws, historical documents, or open public datasets that a researcher can easily retrieve with data additions. These studies are largely legal reviews, historical analyses, or quantitative models using large public datasets (like ISO interconnection queues).

- Not Reproducible (Definition): Methodologies where the logic is not fully explained and/or the necessary data (parameters, equations, prompts, or rubrics) or the data cannot be easily obtained. Methodologies that cannot be reproduced even with web search capabilities because they rely on confidential, proprietary, or paid-access data that is not released..

## Reproducibility Requirements

If the result is fully reproducible, it should be detailed enough that a technically literate researcher could reproduce the work. This means:

- **Step-by-step procedures**: Document the exact sequence of steps taken, in order
- **Specific values**: Include exact parameters, hyperparameters, and configurations when available
- **Software specifications**: Note software versions, library versions, and tool specifications when mentioned in the document
- **Data details**: Include specific information about data preprocessing, transformations, and handling
- **Implementation details**: Document any randomization seeds, initialization procedures, or stochastic elements
- **Evaluation specifics**: Include exact definitions of metrics, evaluation procedures, and statistical tests

When important details are truly missing from the provided text (e.g., sample size, exact hyperparameters, full experimental conditions, software versions), explicitly indicate this with phrases like:
- "The exact sample size is not specified in the provided text."
- "Details of the optimization procedure are not specified in the provided text."
- "The software version used is not specified in the provided text."

Do **not** invent or guess specific values or procedures that are not clearly supported by the document.
