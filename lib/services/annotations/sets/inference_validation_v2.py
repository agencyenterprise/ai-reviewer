"""The Inference Validation annotation set; guidance paraphrases its skill for a person."""

from lib.services.annotations.set_spec import AnnotationSetSpec, should_flag_question

INFERENCE_VALIDATION = AnnotationSetSpec(
    slug="inference_validation_v2",
    title="Inference Validation",
    workflow_type="inference_validation_v2",
    summary="Does the highlighted sentence draw a conclusion its own premises do not support?",
    guidance="""\
Read the argument around the passage, then decide whether the highlighted sentence draws a conclusion that does not follow from what comes before it. Start from the view that the reasoning is sound: flag the sentence only when you can name the specific gap between premise and conclusion.

The check flags:

- **A conclusion that goes beyond its evidence:** a cause read off a correlation, a trend read off two data points, or a whole population judged from a few cases or an unrepresentative sample.
- **A logical fallacy:** a recognizable error such as *post hoc* reasoning, a false choice between two options, circular reasoning or affirming the consequent.
- **A misread figure:** the text says a chart shows something it does not. When the sentence rests on a figure, look at the figure; the premise is what it shows, not what the text says it shows.

It leaves these alone:

- A conclusion bounded to what was studied (*in this sample*, *under the conditions tested*), or hedged (*may*, *suggests*).
- A claim backed by evidence in proportion to it: a stated sample size, test or effect size, a cited source, or a figure that does show what the text says.
- Descriptive statistics that report what was measured without concluding anything from it.
- A valid deduction, and a limitation the authors state themselves.
- An argument that is only weak or could be stronger. A missing robustness check is not an inferential error.
""",
    questions=[should_flag_question()],
    decoy_reasons={
        "adequate_support": "the evidence it gives is proportionate to the claim",
        "bounded_claim": "the conclusion is limited to what was studied",
        "cited_support": "a cited source backs the claim",
        "descriptive_statistic": "it reports what was measured without drawing a conclusion",
        "figure_supports_claim": "the figure it points to does show what it says",
        "hedged_claim": "the claim is hedged to match its evidence",
        "representative_sample": "the sample is representative of the population it generalizes to",
        "stated_limitation": "it states a limitation of the study",
        "valid_deduction": "the conclusion follows from its premises",
    },
    single_issue_kind=True,
)
