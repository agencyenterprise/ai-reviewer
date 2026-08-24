# Auditing Algorithmic Hiring Tools: A Practical Framework for Regulators

## About This Report

This report proposes a framework that regulators can use to audit automated
hiring tools. It is written for staff at labor and civil rights agencies. It
assumes no technical background, but it does conclude that running the framework
requires technical staff an agency probably does not yet have, and the final
section is an argument for hiring them.

## The problem

Automated hiring tools now sit at the front of most large hiring funnels. They
screen resumes, score video interviews, and rank candidates. Existing
anti-discrimination law applies to their outputs, but the standard enforcement
posture, which is to investigate after a complaint, works poorly when the
decision is made by a system the complainant cannot see and the employer often
cannot explain.

Several jurisdictions have responded with audit mandates. New York City's Local
Law 144 requires annual bias audits of automated employment decision tools.
Comparable rules are under consideration elsewhere. The mandates share a
weakness: they specify that an audit must happen without specifying what an
audit is.

We reviewed all 41 published Local Law 144 audit summaries available on employer
websites as of March 2024. Thirty-eight reported selection rates by demographic
group and nothing further. Two added a brief statement about the vendor's
training data. One included a validity discussion. We treat that as evidence of
convergence on a narrow reading, and note that the sample is the population of
published audits rather than a draw from it.

## A three-layer framework

We propose that a complete audit has three layers.

**Layer 1: outcome parity.** The familiar analysis. Compute selection rates by
protected group at each stage of the funnel and compare them. This is what
current audits do, and it remains necessary. It is not sufficient, because a
tool can produce acceptable aggregate selection rates while systematically
misranking candidates within groups.

**Layer 2: construct validity.** Construct validity asks a simple question in a
formal way: does the thing the tool measures correspond to the thing it claims to
measure? A tool that scores "enthusiasm" from vocal prosody is asserting that
prosody stands in for enthusiasm, and that enthusiasm predicts performance in the
role being hired for. Both are empirical claims, and both can be tested.

A video interview tool that scores enthusiasm from prosody is making a claim
about the relationship between prosody and job performance. That claim is
testable and usually untested. Auditors should require the validation evidence
that the tool's own marketing implies exists.

**Layer 3: deployment context.** The same tool can be lawful in one deployment
and unlawful in another, depending on the cutoff the employer sets, the
population it is applied to, and what happens to candidates it rejects. We mean
this as a description of current doctrine, not a proposal: disparate impact
analysis has always turned on the particular selection procedure as used by the
particular employer. An audit of the tool in isolation cannot answer it.
Auditors need the employer's configuration, not just the vendor's model.

## Access and capacity

The framework is only useful if auditors can get what it requires. Layer 1 needs
outcome data the employer already holds. Layer 2 needs validation studies, which
vendors treat as proprietary. Layer 3 needs configuration records that are rarely
retained.

We recommend that agencies use their existing recordkeeping authority to require
retention of configuration records, and that they treat a vendor's refusal to
produce validation evidence as itself a finding, reportable in the audit, rather
than as an obstacle that ends the audit.

On what authority. Agencies with recordkeeping rules can require retention as a
condition of the rule, and non-production of a required record is ordinarily
reportable on its own terms. An adverse finding grounded in non-production is a
finding about the record, not a finding of discrimination, and the audit should
say which of the two it is making.

## Capacity

Most agencies do not have staff who can read a model card, let alone evaluate a
validation study. We estimate that a regional office would need two technically
trained staff to run this framework across its caseload. That is a small number
in absolute terms and a large one relative to current agency staffing.

## Recommendations

1. Agencies should adopt the three-layer framework as their working definition of
   an adequate audit.
2. Agencies should require retention of deployment configuration records.
3. Agencies should treat unproduced validation evidence as a reportable finding,
   stated as a record finding rather than a discrimination finding.
4. Legislatures should fund technical staff at enforcement agencies before
   expanding audit mandates further.

## References

1. Raghavan, M., Barocas, S., Kleinberg, J., and Levy, K. (2020). Mitigating bias
   in algorithmic hiring. *Proceedings of FAT* 2020, 469-481.
2. Wilson, C., Ghosh, A., Jiang, S., et al. (2021). Building and auditing fair
   algorithms. *Proceedings of FAccT* 2021, 666-677.
3. Equal Employment Opportunity Commission (1978). Uniform Guidelines on
   Employee Selection Procedures. 29 CFR Part 1607.
