"""Measurement-driven figure-label utilities — the shared *measure → fit → de-collide* helpers,
so recipes place text by MEASURING it rather than guessing with a magic character count. This is
the legibility analogue of the semantic lints: the same discipline (don't assert, verify) applied
to layout. matplotlib only — no new dependency.

* `measure_widths` — a label's true width in DATA x-units (set xlim before calling).
* `lane_pack` — greedy interval-scheduling: stack labels into as many vertical lanes as needed so
  no two in a lane overlap horizontally (fixes clustered timelines).
* `overlap_pairs` — overlapping text artists on a built figure, for the layout lint / tests.
"""

from __future__ import annotations

from matplotlib.transforms import Bbox


def measure_widths(ax, strings: list[str], fontsize: float, *, ha: str = "center") -> list[float]:
    """Width of each string in DATA x-units at `fontsize` on `ax`. Requires xlim to be set (the
    data↔pixel scale depends on it) and a stable axes box (avoid constrained_layout). One draw
    pass; the temporary artists are removed."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    out: list[float] = []
    for s in strings:
        t = ax.text(0, 0, s, fontsize=fontsize, ha=ha)
        bb = t.get_window_extent(renderer=renderer)
        (x0, _), (x1, _) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y0)])
        t.remove()
        out.append(abs(x1 - x0))
    return out


def lane_pack(positions: list[float], widths: list[float], *, gap: float) -> list[int]:
    """Assign each item (centred at `positions[i]`, `widths[i]` wide) to the lowest lane in which
    it does not horizontally overlap an earlier item (+ `gap`). Items are processed left-to-right,
    so leader lines never cross. Returns a lane index per item (0 = closest to the axis)."""
    order = sorted(range(len(positions)), key=lambda i: positions[i])
    lane_right: list[float] = []
    lane_of = [0] * len(positions)
    for i in order:
        left = positions[i] - widths[i] / 2 - gap
        right = positions[i] + widths[i] / 2 + gap
        for ln, edge in enumerate(lane_right):
            if left > edge:
                lane_of[i] = ln
                lane_right[ln] = right
                break
        else:
            lane_of[i] = len(lane_right)
            lane_right.append(right)
    return lane_of


def overlap_pairs(fig, *, min_overlap_pt: float = 1.5) -> list[tuple[str, str]]:
    """For the layout LINT (the figure-side analogue of the table-overflow guard): pairs of label
    text artists whose drawn bounding boxes overlap by more than `min_overlap_pt` points in each
    dimension. Compared **within each axes** (so a data label and an unrelated colorbar tick in a
    different axes aren't a false positive); the axes title and empty strings are ignored."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    pairs: list[tuple[str, str]] = []
    for ax in fig.axes:
        title = ax.title
        items = [(t.get_text(), t.get_window_extent(renderer=renderer))
                 for t in ax.texts if t is not title and t.get_text().strip()]
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                inter = Bbox.intersection(items[i][1], items[j][1])
                if inter is not None and inter.width > min_overlap_pt \
                        and inter.height > min_overlap_pt:
                    pairs.append((items[i][0], items[j][0]))
    return pairs
