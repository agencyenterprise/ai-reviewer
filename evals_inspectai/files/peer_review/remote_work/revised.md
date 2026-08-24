# Distributed Work and Team Coordination: Evidence from a Two-Year Panel

## About This Report

This report examines how the shift to distributed work between 2021 and 2023
affected software engineering teams. It was prepared for a general policy
audience and draws on a panel of 84 teams at 12 firms.

A note on what we measure. Throughout this report, the "delivery index" means
one specific construct: a standardized average of throughput, cycle time, and
defect escape rate, defined in the Methods section. It is not a measure of
productivity in any broader sense, and we have retitled the report to reflect
that.

## Background

When large employers moved to distributed work, the debate about its effects ran
ahead of the evidence. Early studies were mostly cross-sectional, comparing
teams that had chosen to work remotely against teams that had not.

That design has a specific weakness. Teams that choose to work remotely may
differ from teams that do not in ways that also affect their delivery: they may
be more senior, working on more modular systems, or simply better managed. A
comparison between them measures those differences along with any effect of the
working arrangement. A panel design follows the same teams as their arrangements
change, so each team acts as its own comparison.

## Methods

We assembled a panel of 84 teams at 12 firms in the financial services, health
technology, and logistics sectors. Firms were recruited through an industry
consortium; participation was voluntary. Each team was observed quarterly for
eight quarters, giving 672 team-quarters.

### How the sample was built

Within each participating firm we included every team that had shipped to
production in the two quarters before enrollment, which is how we arrived at 84
of the 96 eligible teams. Twelve teams were excluded as newly formed.
Nine teams dissolved or merged during the panel; they contribute the quarters
they were observed and are not carried forward.

### What drove arrangement changes

The 61 arrangement changes were not team decisions in most cases. Forty-four
followed a firm-wide policy change applied to all teams at that site, which is
the variation we lean on most heavily. Twelve were team-initiated requests
approved by a manager. Five followed an office closure or relocation. We report
results for the firm-wide subset separately in the appendix; they are close to
the headline estimate.

### Outcome measure

Our delivery index combines three components: story points completed per
engineer-week, median cycle time from first commit to production deployment, and
a defect-escape rate measured as production incidents per 1,000 deployments. We
standardized each component within firm and quarter, then averaged the three
standardized scores.

One caution on the third component. Because it is scaled per 1,000 deployments,
a team that deploys less often can improve its rate without improving its work.
We report the three components separately in Table 1 for this reason.

### Estimation

We estimated a two-way fixed effects model with team and quarter fixed effects,
clustering standard errors at the firm level. We also ran three robustness
checks: dropping the first quarter after any change, restricting to teams
observed for all eight quarters, and re-estimating with each component as a
separate outcome.

We have kept this section in the body rather than moving it to an appendix.
Reviewer A asked us to condense it and Reviewer B asked us to expand it; we have
sided with expansion, because the questions Reviewer B raised about the sampling
frame and the source of the arrangement changes go to whether the design
identifies anything at all, and a reader cannot check that from an appendix.

## Results

**Table 1. Effect of working arrangement on the delivery index and its
components.**

| Outcome | Fully distributed | Hybrid |
| --- | --- | --- |
| Delivery index | -0.11 (95% CI: -0.21 to -0.01) | -0.02 (-0.10 to 0.06) |
| Story points per engineer-week | -0.02 (-0.11 to 0.07) | 0.01 (-0.06 to 0.08) |
| Median cycle time (days) | +1.4 (0.3 to 2.5) | +0.2 (-0.5 to 0.9) |
| Defect escape rate | 0.00 (-0.08 to 0.08) | -0.01 (-0.08 to 0.06) |

Fully distributed teams scored 0.11 standard deviations lower on the delivery
index than the same teams did when co-located, with a 95% confidence interval
running from -0.21 to -0.01. The interval excludes zero, but only just, and we
would not want a reader to treat the lower bound as a precise figure.

Decomposing the index, the difference was concentrated in cycle time, which rose
by roughly a day and a half at the median. Story points per engineer-week and
the defect-escape rate did not move detectably.

The effect was larger for teams formed within the previous year (-0.24) than for
teams that had been together longer (-0.06). This was the only subgroup split we
examined, and it was specified before we saw the results, but the difference
between the two estimates is not itself statistically significant.

## Discussion

The headline result is small. A tenth of a standard deviation is well within the
range that a single reorganization or a change in on-call load could produce.

What the decomposition suggests, and we put this no more strongly than that, is
that the cost of distributed work in this sample may be a coordination cost
rather than an effort cost: teams shipped the same amount of work with the same
defect rate, but each change took longer to get through review and deployment.
Cycle time can lengthen for reasons that have nothing to do with coordination,
including reviewers covering more surface area, and we have not tested those
alternatives.

The team-age result is suggestive rather than established. We report it as a
hypothesis for a future study rather than a finding, for the reason given above.

A limitation we want to be explicit about. Firms that join an industry
consortium and agree to be measured are not a random draw from the population of
firms; they are likely to be larger, more process-mature, and more confident
about their own numbers. All three sectors studied are also ones where software
is a cost center or a regulated function. We would be cautious about extending
these estimates to firms where the software team is the product, and the
recommendations below should be read as applying to firms resembling those in
the panel.

## Recommendations

1. Firms resembling those in this panel should not treat distributed work as a
   productivity problem to be solved by mandating a return to the office. The
   measured effect is too small to justify a blanket mandate.
2. Firms should consider co-locating newly formed teams for their first two
   quarters, then letting the team choose its arrangement.
3. Firms that adopt distributed work should invest in reducing review and
   deployment latency, since that is where the measured cost falls.
4. Future work should extend the panel beyond eight quarters and should include
   sectors outside the three studied here.

## References

1. Bloom, N., Liang, J., Roberts, J., and Ying, Z. J. (2015). Does working from
   home work? Evidence from a Chinese experiment. *Quarterly Journal of
   Economics*, 130(1), 165-218.
2. Emanuel, N. and Harrington, E. (2023). Working remotely? Selection, treatment
   and the market for remote work. *FRB of New York Staff Report* No. 1061.
3. Forsgren, N., Humble, J., and Kim, G. (2018). *Accelerate: The Science of
   Lean Software and DevOps*. IT Revolution Press.
