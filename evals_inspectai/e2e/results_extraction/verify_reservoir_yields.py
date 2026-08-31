"""Recompute the `appendix_parameters` yields from the document's own model.

The fixture claims its results are fully reproducible, which is only true if a
reader running the model described in its Appendix A gets the numbers in its
Table 1. The unit suite checks the historical arm; the stochastic arm needs 1,000
replicates of a bisection, so it lives here instead.

    uv run python evals_inspectai/e2e/results_extraction/verify_reservoir_yields.py

Every figure it prints should match the document. It exists because two of these
documents shipped with numbers their own models could not produce.
"""
import calendar, re
import numpy as np
import yaml
from pathlib import Path

records = yaml.safe_load(Path("evals_inspectai/e2e/results_extraction/dataset.yaml").read_text())
doc = [r for r in records if r["id"] == "appendix_parameters"][0]["input"]

rows = [(y, l) for y, l in re.findall(r"^\| (\d{4}-\d{2}) \| (.+) \|$", doc, re.M) if y[0] == "2"]
WY_MONTHS = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]
series = []                                   # (year, month, inflow Ml)
for label, line in rows:
    start = int(label[:4])
    vals = [int(x.strip().replace(",", "")) for x in line.split("|")]
    for m, v in zip(WY_MONTHS, vals):
        series.append((start if m >= 10 else start + 1, m, float(v)))

SMAX = 9840.0
AREA = 1.42                                    # km^2 -> mm depth * area = Ml
EVAP_MM = {m: v for m, v in enumerate([4, 8, 21, 44, 71, 86, 92, 78, 47, 22, 7, 3], start=1)}
CLIMATE = {m: v for m, v in enumerate(
    [1.08, 1.06, 1.02, 0.96, 0.91, 0.84, 0.79, 0.81, 0.88, 0.97, 1.04, 1.07], start=1)}


def comp_rate(month):                          # Ml/d
    return 4.1 if 4 <= month <= 9 else 6.8


def fails(months, demand, evap_scale=1.0):
    """Count months whose mass balance would drive storage below zero."""
    storage, failures = SMAX, 0
    for year, month, inflow in months:
        days = calendar.monthrange(year, month)[1]
        out = demand * days + EVAP_MM[month] * AREA * evap_scale + comp_rate(month) * days
        nxt = storage + inflow - out
        if nxt < 0:
            failures += 1
            nxt = 0.0
        storage = min(SMAX, nxt)
    return failures


def yield_of(months, evap_scale=1.0, allowed_fraction=0.0):
    """Largest constant demand meeting the criterion, by bisection to 0.01 Ml/d."""
    allowed = int(len(months) * allowed_fraction)
    lo, hi = 0.0, 200.0
    while hi - lo > 0.01:
        mid = (lo + hi) / 2
        if fails(months, mid, evap_scale) <= allowed:
            lo = mid
        else:
            hi = mid
    return lo


hist_yield = yield_of(series)
climate_series = [(y, m, i * CLIMATE[m]) for y, m, i in series]
clim_yield = yield_of(climate_series, evap_scale=1.12)
hist_99 = yield_of(series, allowed_fraction=0.01)
clim_99 = yield_of(climate_series, evap_scale=1.12, allowed_fraction=0.01)

# Stochastic: AR(1) on standardised log inflows, exactly as the appendix states.
by_month = {m: np.log([i for _, mm, i in series if mm == m]) for m in range(1, 13)}
mu = {m: by_month[m].mean() for m in by_month}
sd = {m: by_month[m].std(ddof=0) for m in by_month}
rng = np.random.default_rng(20240115)
PHI = 0.61
REPLICATES, YEARS = 1000, 60
BURN = 12
month_cycle = [(2001 + (k + 9) // 12, WY_MONTHS[k % 12]) for k in range(YEARS * 12 + BURN)]

yields = []
for _ in range(REPLICATES):
    z, months = 0.0, []
    eps = rng.standard_normal(YEARS * 12 + BURN)
    for k, (yr, m) in enumerate(month_cycle):
        z = PHI * z + np.sqrt(1 - PHI**2) * eps[k]
        if k >= BURN:
            months.append((yr, m, float(np.exp(mu[m] + sd[m] * z))))
    yields.append(yield_of(months))
stoch_yield = float(np.median(yields))

print("historical yield      : %.1f Ml/d" % hist_yield)
print("stochastic (median)   : %.1f Ml/d" % stoch_yield)
print("climate-adjusted      : %.1f Ml/d" % clim_yield)
print("historical @99%%       : %.1f Ml/d (+%.1f%%)" % (hist_99, 100 * (hist_99 / hist_yield - 1)))
print("climate @99%%          : %.1f Ml/d (+%.1f%%)" % (clim_99, 100 * (clim_99 / clim_yield - 1)))
print("hist - climate spread : %.1f Ml/d" % (hist_yield - clim_yield))
