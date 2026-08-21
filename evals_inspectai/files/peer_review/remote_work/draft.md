# Distributed Work and Team Productivity: Evidence from a Two-Year Panel

## About This Report

This report examines how the shift to distributed work between 2021 and 2023
affected the productivity of software engineering teams. It was prepared for a
general policy audience and draws on a panel of 84 teams at 12 firms.

## Background

When large employers moved to distributed work, the debate about its effects
ran ahead of the evidence. Early studies were mostly cross-sectional, comparing
teams that had chosen to work remotely against teams that had not, and they
disagreed with each other. A panel design lets us follow the same teams as
their working arrangements change, which removes the most obvious source of
selection bias.

## Methods

We assembled a panel of 84 software engineering teams at 12 firms in the
financial services, health technology, and logistics sectors. Firms were
recruited through an industry consortium; participation was voluntary. Each
team was observed quarterly for eight quarters, giving 672 team-quarters.

Our productivity measure combines three components: story points completed per
engineer-week, median cycle time from first commit to production deployment,
and a defect-escape rate measured as production incidents per 1,000 deployments.
We standardized each component within firm and quarter, then averaged the three
standardized scores into a single index. Standardizing within firm removes
level differences in how firms size their stories, which would otherwise
dominate the variation.

Working arrangement was coded from each team's calendar and badge data into
three categories: fully co-located, hybrid (two or more scheduled days on
site), and fully distributed. Teams changed category 61 times over the panel.

We estimated a two-way fixed effects model with team and quarter fixed effects,
clustering standard errors at the firm level. Team fixed effects absorb any
time-invariant differences between teams, so the coefficient on working
arrangement is identified from teams that changed arrangement during the panel.

We also ran three robustness checks: dropping the first quarter after any
change, to allow for transition effects; restricting to teams observed for all
eight quarters; and re-estimating with each of the three productivity
components as a separate outcome.

## Results

Fully distributed teams scored 0.11 standard deviations lower on the
productivity index than the same teams did when co-located (95% CI: -0.21 to
-0.01). Hybrid teams were statistically indistinguishable from co-located teams
(-0.02, 95% CI: -0.10 to 0.06).

Decomposing the index, the distributed penalty was concentrated in cycle time,
which rose by roughly a day and a half at the median. Story points per
engineer-week and the defect-escape rate did not move detectably.

The effect was larger for teams that had been formed within the previous year
(-0.24) than for teams that had been together longer (-0.06), though the
difference between those two estimates was not itself statistically
significant.

## Discussion

The headline result is small. A tenth of a standard deviation is well within
the range that a single reorganization or a change in on-call load could
produce, and the confidence interval touches zero. What the decomposition
suggests is that the cost of distributed work in this sample is a coordination
cost rather than an effort cost: teams shipped the same amount of work with the
same defect rate, but each change took longer to get through review and
deployment.

The team-age result is the one we find most suggestive. If the penalty really
does fall on newly formed teams, then the policy question is not whether to
allow distributed work but when in a team's life to require co-location.

## Recommendations

1. Firms should not treat distributed work as a productivity problem to be
   solved by mandating a return to the office. The measured effect is too small
   to justify a blanket mandate.
2. Firms should consider co-locating newly formed teams for their first two
   quarters, then letting the team choose its arrangement.
3. Firms that adopt distributed work should invest in reducing review and
   deployment latency, since that is where the measured cost falls.
4. Future work should extend the panel beyond eight quarters and should include
   sectors outside the three studied here.

## References

Available on request.
