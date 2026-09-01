"""The reproducibility-check dataset's own arithmetic has to hold.

Eight of the ten documents in `results_extraction/dataset.yaml` are written for
the eval, and several declare results the ground truth calls **fully
reproducible** -- meaning a reader could regenerate them from the document
alone. Twice that claim was false: one document specified a queue at an unstable
utilisation, so the finite percentiles it reported were impossible, and another
asserted a reservoir yield its own inflow record could not supply. Both were
found by the agent under test rather than by us, and an eval whose ground truth
is wrong scores the system down for being right.

So the numbers a `fully_reproducible` expectation rests on are checked here, by
redoing them from the document text the way a reader would. The stochastic
reservoir arm is left out on purpose: reproducing it means 1,000 replicates of a
bisection, too slow for the unit suite. That arm is checked by
`evals_inspectai/e2e/results_extraction/verify_reservoir_yields.py`, which is in
the repo and runs the same model over every inflow assumption.
"""

import calendar
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pytest
import yaml

DATASET = (
    Path(__file__).resolve().parents[3]
    / "evals_inspectai"
    / "e2e"
    / "results_extraction"
    / "dataset.yaml"
)


@pytest.fixture(scope="module")
def documents() -> dict[str, str]:
    records = yaml.safe_load(DATASET.read_text())
    return {record["id"]: record["input"] for record in records}


@pytest.fixture(scope="module")
def expectations() -> dict[str, list[dict]]:
    records = yaml.safe_load(DATASET.read_text())
    return {record["id"]: record["expected_results"] for record in records}


def _capture(pattern: str, text: str, what: str) -> str:
    """The single capture of `pattern`, or a failure naming what went missing.

    Reworded documents should fail with "could not find the arrival rate", not
    with an AttributeError on None.
    """
    found = re.search(pattern, text)
    assert found is not None, f"could not find {what} in the document"
    return found.group(1)


def test_anchors_are_unique_within_a_sample(expectations: dict[str, list[dict]]):
    """A `match` anchor shared with a sibling result steals its pairing.

    The scorer assigns expected results to reported issues one-to-one, so an
    anchor that appears in two results' text lets the first entry capture the
    other's issue: the sibling then reads as missing and the captured issue as an
    invention, from one duplicated string. Four such collisions have already cost
    real runs -- two exact duplicates and two by substring -- so they are a test
    failure rather than a review comment.
    """
    for sample, entries in expectations.items():
        anchors = [
            (entry["id"], anchor.lower())
            for entry in entries
            for anchor in entry["match"]
        ]
        for index, (owner, anchor) in enumerate(anchors):
            for other_owner, other in anchors[index + 1 :]:
                if owner == other_owner:
                    continue
                # Containment, not just equality: anchors are matched as raw
                # substrings, so '0.4' silently matches "10.43 ms" and steals
                # that issue from whichever result it belongs to.
                assert anchor not in other and other not in anchor, (
                    f"{sample}: anchor {anchor!r} ({owner}) and {other!r} "
                    f"({other_owner}) are substrings of one another"
                )


def test_inline_simulation_load_is_stable(documents: dict[str, str]):
    """A single-server queue only has the reported percentiles below rho = 1."""
    doc = documents["inline_simulation"]
    lam = float(_capture(r"\\lambda = (\d+)\$ requests per second", doc, "the arrival rate"))
    mu = float(_capture(r"\$\\mu = (-?[\d.]+)\$", doc, "the lognormal mu"))
    sigma = float(_capture(r"\$\\sigma = ([\d.]+)\$", doc, "the lognormal sigma"))

    mean_service = np.exp(mu + sigma**2 / 2)
    rho = lam * mean_service
    stated_rho = float(
        _capture(r"\\rho = \\lambda E\[S\] = ([\d.]+)\$", doc, "the stated utilisation")
    )
    assert rho == pytest.approx(stated_rho, abs=0.005), (
        f"arrival rate {lam}/s and mean service {mean_service * 1000:.3f} ms give "
        f"rho={rho:.3f}, but the document states {stated_rho}"
    )
    assert rho < 1, "the document reports steady-state percentiles for an unstable queue"

    # The Pollaczek-Khinchine value the document checks its simulator against.
    cv = np.sqrt(np.exp(sigma**2) - 1)
    wait_ms = rho / (1 - rho) * (1 + cv**2) / 2 * mean_service * 1000
    stated_wait = float(
        _capture(r"FIFO waiting time of ([\d.]+) ms", doc, "the Pollaczek-Khinchine value")
    )
    assert wait_ms == pytest.approx(stated_wait, abs=0.05)


def test_mixed_classes_engineering_estimate_follows_its_own_table(
    documents: dict[str, str],
):
    """The stated coefficients must be what OLS returns, and the estimate follow."""
    doc = documents["mixed_classes"]
    a = float(_capture(r"\$a = ([\d,]+)\$ GBP/kW", doc, "coefficient a").replace(",", ""))
    b = float(_capture(r"\$b = ([\d,]+)\$ GBP/m", doc, "coefficient b").replace(",", ""))
    c = float(
        _capture(r"\$c = ([\d{},]+)\$ GBP", doc, "coefficient c")
        .replace("{,}", "")
        .replace(",", "")
    )
    q = float(_capture(r"Q_\{\\text\{design\}\} = ([\d.]+)\$ kW", doc, "the design heat loss"))
    area = float(
        _capture(r"A_\{\\text\{emitter\}\} = ([\d.]+)\$\n?\s*m", doc, "the emitter area")
    )
    stated = float(
        _capture(r"m²\) gives \*\*([\d,]+) GBP\*\*", doc, "the engineering estimate").replace(
            ",", ""
        )
    )

    rows = re.findall(r"^\| \d+ \| ([\d.]+) \| ([\d.]+) \| ([\d,]+) \|$", doc, re.M)
    assert len(rows) == 18, f"expected 18 worked examples, found {len(rows)}"
    design = np.array([[float(h), float(e), 1.0] for h, e, _ in rows])
    cost = np.array([float(k.replace(",", "")) for *_, k in rows])
    fit, *_ = np.linalg.lstsq(design, cost, rcond=None)

    assert fit == pytest.approx([a, b, c], abs=1.0), (
        f"OLS on the document's own table gives {fit.round(1).tolist()}, "
        f"but it states {[a, b, c]}"
    )
    assert a * q + b * area + c == pytest.approx(stated, abs=1.0)


def _reservoir_months(doc: str) -> list[tuple[int, int, float]]:
    """The document's historical inflow record, as (year, month, Ml)."""
    water_year_months = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    months: list[tuple[int, int, float]] = []
    for label, line in re.findall(r"^\| (\d{4}-\d{2}) \| (.+) \|$", doc, re.M):
        if not label.startswith("2"):
            continue
        start = int(label[:4])
        values = [float(v.strip().replace(",", "")) for v in line.split("|")]
        for month, value in zip(water_year_months, values):
            months.append((start if month >= 10 else start + 1, month, value))
    return months


def _reservoir_failures(
    months: Iterable[tuple[int, int, float]], demand: float, capacity: float
) -> int:
    """Months whose mass balance would drive storage below zero, per Equation 1."""
    evaporation_mm = dict(
        enumerate([4, 8, 21, 44, 71, 86, 92, 78, 47, 22, 7, 3], start=1)
    )
    storage, failures = capacity, 0
    for year, month, inflow in months:
        days = calendar.monthrange(year, month)[1]
        release = (4.1 if 4 <= month <= 9 else 6.8) * days
        outflow = demand * days + evaporation_mm[month] * 1.42 + release
        nxt = storage + inflow - outflow
        if nxt < 0:
            failures, nxt = failures + 1, 0.0
        storage = min(capacity, nxt)
    return failures


def test_appendix_parameters_historical_yield_is_achievable(documents: dict[str, str]):
    """Running the document's own model has to give the yield it reports."""
    doc = documents["appendix_parameters"]
    capacity = float(
        _capture(r"S_\{\\max\} = ([\d{},]+)\$ Ml", doc, "the usable capacity")
        .replace("{,}", "")
        .replace(",", "")
    )
    stated = float(
        _capture(r"\| Historical \(2011–2020\) \| ([\d.]+) \|", doc, "the historical yield")
    )
    months = _reservoir_months(doc)
    assert len(months) == 120, f"expected 120 monthly inflows, found {len(months)}"

    # Yield is the largest constant demand that never empties the store, found by
    # bisection exactly as the methods section specifies.
    low, high = 0.0, 200.0
    while high - low > 0.01:
        mid = (low + high) / 2
        if _reservoir_failures(months, mid, capacity) == 0:
            low = mid
        else:
            high = mid

    assert low == pytest.approx(stated, abs=0.1), (
        f"the document's own inflows and parameters yield {low:.1f} Ml/d, "
        f"but Table 1 reports {stated} Ml/d"
    )
