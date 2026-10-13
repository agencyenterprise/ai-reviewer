"""The Methodological Alignment annotation set; guidance paraphrases its skill for a person."""

from lib.services.annotations.set_spec import AnnotationSetSpec, should_flag_question

METHODOLOGICAL_ALIGNMENT = AnnotationSetSpec(
    slug="methodological_alignment",
    title="Methodological Alignment",
    workflow_type="methodological_alignment",
    summary="Does the highlighted design choice fall short of standard practice in the paper's field?",
    guidance="""\
Each example is the methods of a short paper. Judge the highlighted choice against what researchers in that field normally do, as a methods reviewer would. Papers state their choices neutrally and never name the flaw, so you need to know, or look up, what the field expects. Skip the item if the field is outside what you can judge.

The check flags:

- **A missing standard component:** a check, control, data source or analysis step that is routine in the field but absent or very weak here, such as no control group or no correction for multiple comparisons. When the paper is silent on something, the highlight sits on the passage describing the analysis it affects.
- **A methodological risk:** a departure from standard practice that threatens how far the results can be trusted, generalized or interpreted, such as stopping an experiment early, a single pre-period, or standard errors that ignore clustering.

It leaves these alone:

- Choices that match or exceed standard practice: random sampling, a power analysis, blinding, validated or pretested instruments, held-out test data, reported uncertainty.
- Choices that look like gaps but are right for this design, such as no margin of error for a non-probability sample, or a sample restricted to the units a policy covers.
- Differences from the field that are innovations rather than weaknesses.
""",
    questions=[should_flag_question()],
    decoy_reasons={
        "administrative_data": "administrative records are an accepted data source here",
        "blinding": "it blinds participants or assessors, as the field expects",
        "counterbalancing": "counterbalancing the order of conditions is standard practice",
        "coverage_restriction": "restricting the sample to the units the policy covers is correct",
        "full_weekly_cycles": "planning the experiment in full weekly cycles is recommended practice",
        "guardrail_metrics": "monitoring guardrail metrics is standard practice",
        "held_out_test": "evaluating on held-out data is standard practice",
        "member_checking": "member checking is a standard credibility check in qualitative work",
        "no_margin_of_error": "a margin of sampling error does not apply to a non-probability sample",
        "piloted_guide": "piloting the interview guide is standard practice",
        "placebo_test": "a placebo test is a standard robustness check",
        "power_analysis": "a power analysis is standard practice",
        "pretested_instrument": "pretesting the instrument is standard practice",
        "random_sampling": "random sampling is standard practice",
        "randomization_method": "the randomization method is sound",
        "reference_standard": "it uses the field's reference standard",
        "seed_variance_reported": "reporting variance across random seeds is standard practice",
        "standardized_cointervention": "standardizing co-interventions across arms is standard practice",
        "uncertainty_reported": "it reports the uncertainty of its estimates",
        "unit_of_randomization": "the unit of randomization fits the design",
        "validated_instrument": "it uses a validated instrument",
    },
)
