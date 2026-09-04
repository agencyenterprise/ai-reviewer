"""Draw the chart PNGs for the image-viewing eval samples.

    uv run python -m evals_inspectai.files.figures.generate_fixtures

The dataset records are ordinary markdown that reference these files by path
(``![](files/figures/<name>.png)``, relative to the evals root). The eval solver
inlines them as data URIs at upload time and the backend extracts them like any
embedded picture, so the agent meets them exactly as it meets a Word document's
figures. Each chart carries information the sample's text does not, which is
what makes the right verdict reachable only by looking at it. Drawing is
deterministic, so rerunning this rewrites identical bytes.
"""

from pathlib import Path
from typing import Callable

from evals_inspectai.files.figures import charts

OUT_DIR = Path(__file__).parent

_YEARS = list(range(2016, 2024))
_SITES = ["Site A", "Site B", "Site C"]

FIXTURES: dict[str, Callable[[], bytes]] = {
    # Figures & Tables Check
    "ft_logo": lambda: charts.logo("Northfield Water Authority"),
    "ft_storage": lambda: charts.line_chart(
        list(range(1, 13)),
        [78, 81, 85, 88, 84, 76, 66, 58, 54, 57, 63, 70],
        unit="percent of capacity",
    ),
    # The caption lives inside the image; the document has no caption paragraph.
    "ft_defects_captioned": lambda: charts.grouped_bar_chart(
        ["Ashford", "Belmont", "Carver"],
        [
            ("Before", [3.8, 4.6, 2.9], charts.GREY),
            ("After", [2.1, 2.4, 1.7], charts.BLUE),
        ],
        unit="percent",
        title="Figure 1: Defect rate by plant before and after the inspection protocol (percent)",
    ),
    "ft_ridership": lambda: charts.bar_chart(
        ["Red", "Blue", "Green", "Orange"], [142, 118, 96, 71], unit="thousand riders"
    ),
    # An author's placeholder box where Figure 2 should be.
    "ft_placeholder": lambda: charts.placeholder("CHART TO BE INSERTED"),
    # Reproducibility Check: the tercile means exist only here.
    "rc_canopy": lambda: charts.bar_chart(
        ["Low canopy", "Medium canopy", "High canopy"],
        [31.4, 29.6, 27.9],
        unit="degrees C",
        y_min=20.0,
        y_max=35.0,
        note="n = 40 tracts per tercile. Mean daytime surface temperature, June to August 2024.",
    ),
    # Inference Validation: the same text is true of one chart and false of the other.
    "iv_steady_growth": lambda: charts.line_chart(
        _YEARS,
        [4, 5, 9, 15, 24, 35, 48, 63],
        unit="thousand e-bikes",
        marker_x=2021,
        marker_label="Subsidy introduced",
    ),
    "iv_flat_then_jump": lambda: charts.line_chart(
        _YEARS,
        [4, 4, 5, 5, 5, 6, 22, 41],
        unit="thousand e-bikes",
        marker_x=2021,
        marker_label="Subsidy introduced",
    ),
    # Recommendation Check: the finding is only in the chart.
    "rec_safety_reduction": lambda: charts.grouped_bar_chart(
        _SITES,
        [
            ("Before", [8.2, 7.5, 9.1], charts.GREY),
            ("After", [5.1, 4.4, 5.9], charts.BLUE),
        ],
        unit="incidents per 100 workers",
        y_max=12.0,
    ),
    "rec_safety_flat": lambda: charts.grouped_bar_chart(
        _SITES,
        [
            ("Before", [8.2, 7.5, 9.1], charts.GREY),
            ("After", [8.0, 7.7, 9.0], charts.BLUE),
        ],
        unit="incidents per 100 workers",
        y_max=12.0,
    ),
    # Reviewer 2: a sub-point gap drawn on a 49 to 51 axis.
    "r2_completion": lambda: charts.bar_chart(
        ["Control", "Peer coaching"],
        [49.6, 50.4],
        unit="completion rate (percent)",
        y_min=49.0,
        y_max=51.0,
    ),
}


if __name__ == "__main__":
    for name, draw in FIXTURES.items():
        (OUT_DIR / f"{name}.png").write_bytes(draw())
    print(f"wrote {len(FIXTURES)} charts to {OUT_DIR}")
