"""Pillow-drawn charts for the image-viewing eval fixtures.

Deterministic and dependency-light (no matplotlib): every chart is drawn from
its numbers with straight lines, rectangles and the default font, at a size a
vision model reads comfortably. Values, units and notes are rendered *in* the
image, because the fixtures exist to test that the agent reads them there.
"""

import io
from typing import Optional, Sequence

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 960, 600
LEFT, RIGHT, TOP, BOTTOM = 120, 40, 90, 110

INK = (30, 30, 30)
GRID = (205, 205, 205)
BLUE = (52, 101, 164)
ORANGE = (214, 120, 40)
GREY = (150, 150, 150)

Series = tuple[str, Sequence[float], tuple[int, int, int]]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def _png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _fmt(value: float, span: float) -> str:
    return f"{value:.1f}" if span < 20 else f"{value:.0f}"


def _canvas(title: Optional[str]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    if title:
        # Shrink a long title rather than clip it: the fixtures rely on every
        # word of an in-image caption being readable.
        size = 26
        while size > 14 and _font(size).getlength(title) > WIDTH - LEFT - RIGHT:
            size -= 2
        draw.text((LEFT, 14), title, font=_font(size), fill=INK)
    return image, draw


_STEPS = (0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000)


def _nice_top(highest: float) -> float:
    """A y-axis top a little above ``highest`` that lands the ticks on round numbers."""
    raw = highest * 1.15
    candidates = [step * n for step in _STEPS for n in (4, 5, 6) if step * n >= raw]
    return min(candidates) if candidates else raw


def _tick_count(y_min: float, y_max: float) -> int:
    span = y_max - y_min
    for n in (5, 4, 6):
        if any(abs(span / n - step) < 1e-9 for step in _STEPS):
            return n
    return 5


def _y_axis(draw: ImageDraw.ImageDraw, y_min: float, y_max: float, unit: str) -> None:
    """Axis line, evenly spaced labelled ticks with gridlines, and the unit."""
    ticks = _tick_count(y_min, y_max)
    draw.line((LEFT, TOP, LEFT, HEIGHT - BOTTOM), fill=INK, width=2)
    draw.line(
        (LEFT, HEIGHT - BOTTOM, WIDTH - RIGHT, HEIGHT - BOTTOM), fill=INK, width=2
    )
    span = y_max - y_min
    for i in range(ticks + 1):
        value = y_min + span * i / ticks
        y = _y_pixel(value, y_min, y_max)
        draw.line((LEFT - 6, y, WIDTH - RIGHT, y), fill=GRID, width=1)
        label = _fmt(value, span)
        draw.text(
            (LEFT - 14 - 11 * len(label), y - 10), label, font=_font(18), fill=INK
        )
    if unit:
        draw.text((14, TOP - 40), unit, font=_font(18), fill=INK)


def _y_pixel(value: float, y_min: float, y_max: float) -> int:
    plot_height = HEIGHT - TOP - BOTTOM
    fraction = (value - y_min) / (y_max - y_min)
    return int(HEIGHT - BOTTOM - fraction * plot_height)


def _note(draw: ImageDraw.ImageDraw, note: Optional[str]) -> None:
    if note:
        draw.text((LEFT, HEIGHT - 42), note, font=_font(17), fill=GREY)


def _legend(draw: ImageDraw.ImageDraw, series: Sequence[Series]) -> None:
    x = WIDTH - RIGHT - 250
    for label, _, color in series:
        draw.rectangle((x, TOP - 30, x + 18, TOP - 12), fill=color)
        draw.text((x + 26, TOP - 34), label, font=_font(18), fill=INK)
        x += 130


def grouped_bar_chart(
    categories: Sequence[str],
    series: Sequence[Series],
    *,
    unit: str = "",
    title: Optional[str] = None,
    y_min: float = 0.0,
    y_max: Optional[float] = None,
    value_labels: bool = True,
    note: Optional[str] = None,
) -> bytes:
    """One group of bars per category, one bar per series, values on top."""
    image, draw = _canvas(title)
    top = (
        y_max
        if y_max is not None
        else _nice_top(max(max(values) for _, values, _ in series))
    )
    _y_axis(draw, y_min, top, unit)
    if len(series) > 1:
        _legend(draw, series)
    plot_width = WIDTH - LEFT - RIGHT
    group_width = plot_width / len(categories)
    bar_width = group_width * 0.7 / len(series)
    for c, category in enumerate(categories):
        group_left = LEFT + c * group_width + group_width * 0.15
        for s, (_, values, color) in enumerate(series):
            x0 = group_left + s * bar_width
            y0 = _y_pixel(values[c], y_min, top)
            draw.rectangle(
                (x0, y0, x0 + bar_width - 6, HEIGHT - BOTTOM - 1), fill=color
            )
            if value_labels:
                label = _fmt(values[c], top - y_min)
                draw.text(
                    (x0 + bar_width / 2 - 6 * len(label), y0 - 26),
                    label,
                    font=_font(19),
                    fill=INK,
                )
        draw.text(
            (group_left + group_width * 0.35 - 5 * len(category), HEIGHT - BOTTOM + 12),
            category,
            font=_font(19),
            fill=INK,
        )
    _note(draw, note)
    return _png(image)


def bar_chart(
    categories: Sequence[str],
    values: Sequence[float],
    *,
    unit: str = "",
    title: Optional[str] = None,
    y_min: float = 0.0,
    y_max: Optional[float] = None,
    value_labels: bool = True,
    note: Optional[str] = None,
) -> bytes:
    return grouped_bar_chart(
        categories,
        [("", values, BLUE)],
        unit=unit,
        title=title,
        y_min=y_min,
        y_max=y_max,
        value_labels=value_labels,
        note=note,
    )


def line_chart(
    xs: Sequence[int],
    ys: Sequence[float],
    *,
    unit: str = "",
    title: Optional[str] = None,
    marker_x: Optional[int] = None,
    marker_label: Optional[str] = None,
    note: Optional[str] = None,
) -> bytes:
    """A single series over evenly spaced x values, optionally with a vertical marker."""
    image, draw = _canvas(title)
    top = _nice_top(max(ys))
    _y_axis(draw, 0.0, top, unit)
    plot_width = WIDTH - LEFT - RIGHT
    step = plot_width / (len(xs) - 1)
    points = [(int(LEFT + i * step), _y_pixel(y, 0.0, top)) for i, y in enumerate(ys)]
    if marker_x is not None and marker_x in xs:
        mx = points[list(xs).index(marker_x)][0]
        for y in range(TOP, HEIGHT - BOTTOM, 12):
            draw.line((mx, y, mx, y + 6), fill=ORANGE, width=2)
        if marker_label:
            draw.text((mx + 8, TOP + 4), marker_label, font=_font(18), fill=ORANGE)
    draw.line(points, fill=BLUE, width=4)
    for (x, y), value in zip(points, ys):
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=BLUE)
        draw.text((x - 12, y - 30), _fmt(value, top), font=_font(17), fill=INK)
    for (x, _), label in zip(points, xs):
        draw.text((x - 18, HEIGHT - BOTTOM + 12), str(label), font=_font(18), fill=INK)
    _note(draw, note)
    return _png(image)


def placeholder(text: str) -> bytes:
    """A grey box where a figure should be: the image file is missing."""
    image = Image.new("RGB", (WIDTH, HEIGHT), (236, 236, 236))
    draw = ImageDraw.Draw(image)
    draw.rectangle((2, 2, WIDTH - 3, HEIGHT - 3), outline=GREY, width=3)
    draw.text(
        (WIDTH // 2 - 9 * len(text), HEIGHT // 2 - 16), text, font=_font(30), fill=GREY
    )
    return _png(image)


def logo(name: str) -> bytes:
    """A wordmark with a simple emblem: decorative, not a figure."""
    image = Image.new("RGB", (700, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 20, 160, 160), fill=BLUE)
    for i, y in enumerate((70, 95, 120)):
        draw.arc((40 + i * 4, y, 140 - i * 4, y + 40), 0, 180, fill="white", width=6)
    draw.text((190, 60), name, font=_font(40), fill=BLUE)
    return _png(image)
