"""Code-generated, correct-by-construction assets (schema §6 MediaPolicy).

Content-bearing visuals are built by code (matplotlib), never diffusion — correct
by construction beats correct-by-review. An asset marked `intentionally_flawed`
(v0.4 B3) is built WRONG ON PURPOSE; the builder must not silently correct it.

**Pluggable backends (Phase 4).** An `Asset(generator, spec)` is a *declarative
request*: `generator` is a `<backend>:<recipe>` id, `spec` carries the parameters.
Builders register against the id; `build_asset` just dispatches. Today the backends
are `matplotlib:` (parameterized, correct-by-construction recipes) and the existing
bespoke figures. A future `diffusion:` backend (the SME's image-gen agent) plugs in
the same way — it fulfils the request for a *decorative, content-free* asset — without
touching the schema or callers. So: add a recipe = register one function.
"""
from __future__ import annotations

import html
import re
import textwrap
from collections.abc import Callable
from pathlib import Path

import fitz  # PyMuPDF — rasterises SVG decorative assets (already a dep; no extra)
import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from ..config import RUNS_DIR  # noqa: E402
from ..schema.assets import Asset  # noqa: E402
from . import figstyle as fs  # noqa: E402  — the styleguide: semantic roles, ramps, house font
from .calculus import (area_between_scene, distribution_scene, extrema_scene,  # noqa: E402
                       function_scene, integral_scene, riemann_scene, tangent_scene)
from .circuits import circuit_construction  # noqa: E402
from .constructions import construction_scene, triangle_geometry  # noqa: E402
from .nodelink import cause_effect_scene, process_scene, tree_scene  # noqa: E402
from .nets import solid_net_scene  # noqa: E402
from .optics import lens_construction  # noqa: E402
from .figstyle import fmt_de, unit_scale  # noqa: E402
from .scene3d import axonometric_solid_scene, riss_pair_scene  # noqa: E402
from .scene import (Canvas, Label, Line, PointMark, Polyline, Region,  # noqa: E402
                    Scene, scene_to_png)

# The house style is applied per-figure via `with plt.rc_context(fs.house_rc())` (the scoped
# scene-renderer pattern) rather than the global `use_house_style()`, so a recipe never leaks
# rcParams onto another figure built in the same process. Colours come from the SEMANTIC ROLES
# in `figstyle` (PALETTE / c() / cat() / edge()); NO recipe hard-codes a hex — that debt is
# what roadmap A1 pays down, and `tests/test_figstyle_port.py` locks it shut.
_HOUSE = fs.house_rc

# generator id ("<backend>:<recipe>")  ->  builder(asset, path) -> writes the PNG
_GENERATORS: dict[str, Callable[[Asset, Path], None]] = {}


def _generator(gid: str):
    def _register(fn: Callable[[Asset, Path], None]):
        _GENERATORS[gid] = fn
        return fn
    return _register


def _outdir() -> Path:
    d = RUNS_DIR / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


_NUMERIC_RE = re.compile(r"-?\d+([.,]\d+)?")


def _all_numeric(vals) -> bool:
    """True when every label is a plain number (e.g. years) — plot on a numeric axis."""
    return bool(vals) and all(_NUMERIC_RE.fullmatch(str(v).strip()) for v in vals)


def _german_value_axis(ax, axis: str = "y") -> None:
    """German plain tick labels on a linear VALUE axis — never scientific notation,
    never an offset multiplier ("1e7" in the corner). The figstyle representation rule."""
    from matplotlib.ticker import FuncFormatter
    getattr(ax, f"{axis}axis").set_major_formatter(FuncFormatter(lambda v, _: fmt_de(v)))


def _year_axis(ax) -> None:
    """Integer ticks without thousands grouping for a time/x axis of whole numbers
    (years): "1960", not "1.960", not one categorical tick per year — with matplotlib
    picking a sensible density over the span."""
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))


# --- parameterized recipes (read asset.spec) ---------------------------------
@_generator("matplotlib:number_line")
def _number_line(asset: Asset, path: Path) -> None:
    """A number line. spec: {min, max, step?, marks?: [{at, label?}]}. Marked labels
    are staggered over two levels (with stems) so clustered/long labels stay legible."""
    s = asset.spec or {}
    lo, hi = float(s.get("min", 0)), float(s.get("max", 10))
    step = float(s.get("step", 1)) or 1.0
    marks = sorted(s.get("marks", []), key=lambda m: float(m["at"]))
    has_labels = any(m.get("label") for m in marks)
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(7.4, 2.0 if has_labels else 1.1))
        ax.axhline(0, color=fs.PALETTE.ink, lw=1.4, zorder=1)
        t = lo
        while t <= hi + 1e-9:
            ax.plot([t, t], [-0.07, 0.07], color=fs.PALETTE.ink, lw=1)
            ax.text(t, -0.22, f"{t:g}", ha="center", va="top", fontsize=fs.TYPE.annot)
            t += step
        levels = (0.18, 0.40, 0.62)                # cycle 3 heights so clustered labels never collide
        for i, m in enumerate(marks):
            at = float(m["at"])
            ax.plot([at], [0], "o", color=fs.PALETTE.focus, ms=9, zorder=3)
            if m.get("label"):
                y = levels[i % len(levels)]
                ax.plot([at, at], [0.07, y - 0.04], color=fs.PALETTE.focus, lw=0.6, zorder=2)
                ax.text(at, y, str(m["label"]), ha="center", va="bottom",
                        color=fs.PALETTE.focus, fontsize=fs.TYPE.annot)
        ax.set_xlim(lo - step * 0.6, hi + step * 0.6)
        ax.set_ylim(-0.5, 0.95 if has_labels else 0.5)
        ax.axis("off")
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)


def _bar_value_labels(ax, vals, *, horizontal: bool, decimals: int | None = None) -> None:
    """Annotate every bar with its value, so even a tiny bar is readable. German
    formatting (fmt_de) — a large value prints "8.916.845", never "8.9e+06"; a
    unit-scaled one "8,9" (decimals=1)."""
    for i, v in enumerate(vals):
        txt = fmt_de(v, decimals)
        if horizontal:
            ax.text(v, i, " " + txt, va="center", ha="left", fontsize=fs.TYPE.tick,
                    color=fs.PALETTE.ink)
        else:
            ax.annotate(txt, (i, v), textcoords="offset points", xytext=(0, 2),
                        ha="center", va="bottom", fontsize=fs.TYPE.tick, color=fs.PALETTE.ink)


@_generator("matplotlib:bar_chart")
def _bar_chart(asset: Asset, path: Path) -> None:
    """A bar chart. spec: {categories, values, title?, xlabel?, ylabel?, log?, horizontal?}.

    Legibility is part of correctness: long/many labels auto-switch to horizontal bars
    (full-width labels, no overlap); every bar is value-labelled (no 'invisible' bar);
    `log` gives a log value-axis for orders-of-magnitude ranges; the title wraps and
    constrained_layout keeps title/axis labels from colliding. Large values scale to
    Mio./Mrd. with the unit in the value-axis label, ticks + value labels print German
    — never scientific notation (the figstyle representation rule)."""
    s = asset.spec or {}
    cats = [str(c).replace("\n", " ") for c in s.get("categories", [])]
    vals = [float(v) for v in s.get("values", [])]
    n = max(len(cats), 1)
    log = bool(s.get("log"))
    horizontal = bool(s.get("horizontal")) or any(len(c) > 10 for c in cats) or n > 6
    ylabel, div = s.get("ylabel") or "", 1.0
    if not log:                              # a log axis already compresses magnitudes
        vals, ylabel, div = unit_scale(vals, ylabel)
    label_decimals = 1 if div > 1 else None  # scaled → "8,9"; raw → auto ("42", "0,25")
    bar_c, bar_e = fs.PALETTE.primary, fs.edge("primary")

    with plt.rc_context(_HOUSE()):
        if horizontal:
            fig, ax = plt.subplots(figsize=(6.8, max(2.4, 0.5 * n + 1.1)), layout="constrained")
            ax.barh(range(n), vals, color=bar_c, edgecolor=bar_e)
            ax.set_yticks(range(n))
            ax.set_yticklabels(cats)
            ax.invert_yaxis()
            if log:
                ax.set_xscale("log")
            else:
                _german_value_axis(ax, "x")
            if ylabel:
                ax.set_xlabel(ylabel)           # the value axis is horizontal now
            ax.margins(x=0.12)                  # room for the value labels
            _bar_value_labels(ax, vals, horizontal=True, decimals=label_decimals)
        else:
            fig, ax = plt.subplots(figsize=(max(4.0, 0.95 * n + 1.5), 3.3), layout="constrained")
            ax.bar(range(n), vals, color=bar_c, edgecolor=bar_e)
            ax.set_xticks(range(n))
            # Safety net: even below the horizontal-switch thresholds, mid-length or
            # numerous labels can collide on a vertical axis — rotate them so they never
            # overlap (constrained_layout then reclaims the space).
            rot = max((len(c) for c in cats), default=0) > 6 or n >= 5
            ax.set_xticklabels(cats, rotation=30 if rot else 0, ha="right" if rot else "center")
            if log:
                ax.set_yscale("log")
            else:
                _german_value_axis(ax, "y")
            if ylabel:
                ax.set_ylabel(ylabel)
            if s.get("xlabel"):
                ax.set_xlabel(s["xlabel"])
            ax.margins(y=0.12)
            _bar_value_labels(ax, vals, horizontal=False, decimals=label_decimals)
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 52)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:population_pyramid")
def _population_pyramid(asset: Asset, path: Path) -> None:
    """A Bevölkerungspyramide — back-to-back horizontal age×sex bars (men left,
    women right), the iconic demographic figure a single-axis bar can't show.
    spec: {age_groups:[str], male:[num], female:[num], title?, xlabel?, ylabel?,
    male_label?, female_label?}. Youngest band at the bottom; a shared, absolute-
    valued x-axis so both wings read in real counts (the left side is negative only
    internally). Use only with real, cited data (the asset's data_source)."""
    from matplotlib.ticker import FuncFormatter, MaxNLocator

    s = asset.spec or {}
    groups = [str(g) for g in s.get("age_groups", [])]
    male = [float(v) for v in s.get("male", [])]
    female = [float(v) for v in s.get("female", [])]
    n = max(len(groups), 1)
    y = list(range(n))
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(6.8, max(3.0, 0.42 * n + 1.0)), layout="constrained")
        ax.barh(y, [-v for v in male], color=fs.PALETTE.primary, edgecolor=fs.edge("primary"),
                label=s.get("male_label", "Männer"))
        ax.barh(y, female, color=fs.PALETTE.secondary, edgecolor=fs.edge("secondary"),
                label=s.get("female_label", "Frauen"))
        ax.axvline(0, color=fs.PALETTE.ink, lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels(groups)
        ax.set_ylabel(s.get("ylabel") or "Altersgruppe")
        ax.xaxis.set_major_locator(MaxNLocator(nbins=6, symmetric=True))
        ax.xaxis.set_major_formatter(  # both wings show positive counts, German grouping
            FuncFormatter(lambda x, _: fmt_de(abs(x), 0)))
        ax.set_xlabel(s.get("xlabel") or "Personen")
        ax.margins(y=0.01)
        ax.legend(loc="lower right", fontsize=fs.TYPE.tick)
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 52)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:timeline")
def _timeline(asset: Asset, path: Path) -> None:
    """A horizontal timeline — chronological events on a time axis (GPB history). spec:
    {events:[{"at":num,"label":str}]} or {categories:[label],"values":[year]}; title?. Each label
    carries its own year and is **measured and lane-packed** above the line with a leader, so
    clustered dates never overlap and the axis needs no colliding tick labels (the legibility fix —
    see `pipeline/figtext.py`)."""
    from .figtext import lane_pack, measure_widths

    s = asset.spec or {}
    events = s.get("events")
    if not events:
        events = [{"at": v, "label": c}
                  for c, v in zip(s.get("categories", []), s.get("values", []))]
    events = sorted(events, key=lambda e: float(e["at"]))
    xs = [float(e["at"]) for e in events]

    def _stamp(e) -> str:
        at = e["at"]
        return f"{at:g}" if isinstance(at, (int, float)) else str(at)

    labels = ["\n".join(textwrap.wrap(f"{_stamp(e)} — {e.get('label', '')}", 22)) for e in events]
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(8.8, 3.2))       # NOT constrained: stable box for measuring
        fig.subplots_adjust(left=0.03, right=0.97, top=0.88, bottom=0.05)
        ax.axhline(0, color=fs.PALETTE.ink, lw=1.6, zorder=1)
        ax.set_yticks([])
        ax.set_xticks([])
        for sp in ("left", "right", "top", "bottom"):
            ax.spines[sp].set_visible(False)
        if not xs:
            fig.savefig(path, dpi=150)
            plt.close(fig)
            return
        span = (max(xs) - min(xs)) or 1.0
        ax.set_xlim(min(xs) - span * 0.12, max(xs) + span * 0.12)
        ax.set_ylim(-0.4, 1.0)                            # provisional; widened after packing
        widths = measure_widths(ax, labels, fontsize=fs.TYPE.annot)
        lanes = lane_pack(xs, widths, gap=span * 0.02)
        nlanes = (max(lanes) + 1) if lanes else 1
        max_lines = max((lab.count("\n") + 1 for lab in labels), default=1)
        lane_h = 0.30 * max_lines + 0.30
        base = 0.42
        for i, (x, lab) in enumerate(zip(xs, labels)):
            y = base + lanes[i] * lane_h
            ax.plot([x], [0], "o", color=fs.PALETTE.focus, ms=7, zorder=3)
            ax.plot([x, x], [0.05, y - 0.05], color=fs.PALETTE.focus, lw=0.7, zorder=2)
            ax.annotate(lab, (x, y), ha="center", va="bottom", fontsize=fs.TYPE.annot,
                        color=fs.PALETTE.ink)
        ax.set_ylim(-0.35, base + (nlanes - 1) * lane_h + 0.30 * max_lines + 0.25)
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 60)), fontsize=fs.TYPE.title)
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)


@_generator("matplotlib:climate_diagram")
def _climate_diagram(asset: Asset, path: Path) -> None:
    """A Klimadiagramm — monthly temperature (line) + precipitation (bars) on two y-axes,
    the iconic geography figure no single-axis recipe can show. spec: {months?:[12],
    temp:[12], precip:[12], title?}. Walter-Lieth convention: temperature left (°C, red
    line), precipitation right (mm, blue bars)."""
    s = asset.spec or {}
    months = s.get("months") or ["Jän", "Feb", "Mär", "Apr", "Mai", "Jun",
                                 "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    temp = [float(v) for v in s.get("temp", [])]
    precip = [float(v) for v in s.get("precip", [])]
    n = len(months)
    temp_c, precip_c = fs.PALETTE.focus, fs.PALETTE.primary   # Walter-Lieth: T line, N bars
    with plt.rc_context(_HOUSE()):
        fig, ax1 = plt.subplots(figsize=(6.6, 3.8), layout="constrained")
        ax2 = ax1.twinx()
        ax2.bar(range(n), precip, color=precip_c, edgecolor=fs.edge("primary"), width=0.7, zorder=1)
        ax1.plot(range(n), temp, "-o", color=temp_c, lw=2, ms=4, zorder=3)
        ax1.set_zorder(ax2.get_zorder() + 1)   # draw the temperature line above the bars
        ax1.patch.set_visible(False)
        ax1.set_xticks(range(n))
        ax1.set_xticklabels(months, fontsize=fs.TYPE.tick)
        ax1.set_ylabel("Temperatur (°C)", color=temp_c)
        ax2.set_ylabel("Niederschlag (mm)", color=precip_c)
        ax1.tick_params(axis="y", labelcolor=temp_c)
        ax2.tick_params(axis="y", labelcolor=precip_c)
        ax2.set_ylim(0, max(precip + [1]) * 1.15)
        if s.get("title"):
            ax1.set_title("\n".join(textwrap.wrap(str(s["title"]), 52)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:line")
def _line(asset: Asset, path: Path) -> None:
    """A line graph — for a TREND / change over time. spec: a single series via
    {categories|x, values|y} or several via {series:[{label?, x:[...], y:[...]}]};
    plus title?, xlabel?, ylabel?, log?. Numeric x (e.g. years) plot on a real numeric
    axis — whole-number x gets integer ticks at a sensible density ("1960 … 2020", never
    one tick per year and never a grouped "1.960"); true categorical x plots over an
    index, thinned to ~12 ticks. A marker only when sparse so a long dense series (e.g.
    65 yearly points) stays legible. Large y-values scale to Mio./Mrd. with the unit in
    the ylabel; ticks print German plain — never scientific notation (figstyle rule)."""
    s = asset.spec or {}
    series = s.get("series") or [{"x": s.get("x") or s.get("categories"),
                                  "y": s.get("y") or s.get("values")}]
    log = bool(s.get("log"))
    ylabel, div = s.get("ylabel") or s.get("y_label") or "", 1.0
    if not log:                                          # one shared divisor across series
        pool = [float(v) for ser in series for v in (ser.get("y") or [])]
        _, ylabel, div = unit_scale(pool, ylabel)
    multi = len(series) > 1
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(6.2, 3.7), layout="constrained")
        cat_labels = None
        numeric_xs: list[float] = []
        for si, ser in enumerate(series):
            y = [float(v) / div for v in (ser.get("y") or [])]
            x = ser.get("x")
            marker = "o" if len(y) <= 24 else None       # no dot-soup on long series
            # a single series is the house `primary`; several get a paired hue+dash from the
            # ramps (redundant encoding, so overlaid trends survive a B/W photocopy).
            style = fs.line_kind(si, lw=2.0) if multi else {"color": fs.PALETTE.primary, "linewidth": 2.0}
            if x and any(isinstance(v, str) for v in x) and not _all_numeric(x):
                cat_labels = [str(v) for v in x]        # true categorical → index + ticklabels
                ax.plot(range(len(y)), y, marker=marker, ms=5, label=ser.get("label"), **style)
            else:                                        # numeric x (years, quantities) → numeric axis
                xs = [float(str(v).replace(",", ".")) for v in (x or range(len(y)))]
                numeric_xs += xs
                ax.plot(xs, y, marker=marker, ms=5, label=ser.get("label"), **style)
        if cat_labels is not None:
            n = len(cat_labels)
            step = max(1, n // 12)                       # thin to ~12 ticks (no overlap smear)
            idx = list(range(0, n, step))
            rot = 30 if any(len(c) > 6 for c in cat_labels) else 0
            ax.set_xticks(idx)
            ax.set_xticklabels([cat_labels[i] for i in idx], rotation=rot,
                               ha="right" if rot else "center")
        elif numeric_xs and all(v == int(v) for v in numeric_xs):
            _year_axis(ax)                               # whole numbers (years): plain integer ticks
        if log:
            ax.set_yscale("log")
        else:
            _german_value_axis(ax, "y")
        ax.grid(True, color=fs.PALETTE.grid, lw=fs.STROKE.grid)
        ax.set_axisbelow(True)
        if s.get("xlabel") or s.get("x_label"):
            ax.set_xlabel(s.get("xlabel") or s.get("x_label"))
        if ylabel:
            ax.set_ylabel(ylabel)
        if multi and any(ser.get("label") for ser in series):
            ax.legend(fontsize=fs.TYPE.tick)
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 52)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:scatter")
def _scatter(asset: Asset, path: Path) -> None:
    """A scatter plot — for a RELATIONSHIP between two numeric variables. spec:
    {points:[[x,y],…], xlabel?, ylabel?, title?, fit? (a linear trend line)}."""
    s = asset.spec or {}
    pts = s.get("points", [])
    xs = [float(p[0]) for p in pts]
    ys = [float(p[1]) for p in pts]
    # large values scale to Mio./Mrd. (unit into the axis label) — never scientific ticks;
    # a scaled/big axis prints German, a small one (e.g. years) keeps plain default ticks
    xs, xlabel, xdiv = unit_scale(xs, s.get("xlabel") or s.get("x_label") or "")
    ys, ylabel, ydiv = unit_scale(ys, s.get("ylabel") or s.get("y_label") or "")
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(5.4, 4.0), layout="constrained")
        ax.scatter(xs, ys, color=fs.PALETTE.primary, s=38, zorder=3)
        if s.get("fit") and len(xs) >= 2:                # the trend is the point of interest → focus
            import numpy as np
            m, b = np.polyfit(xs, ys, 1)
            xr = [min(xs), max(xs)]
            ax.plot(xr, [m * x + b for x in xr], color=fs.PALETTE.focus, lw=1.5, zorder=2)
        for axis, div, vals in (("x", xdiv, xs), ("y", ydiv, ys)):
            if div > 1 or (vals and max(abs(v) for v in vals) >= 1e5):
                _german_value_axis(ax, axis)
        ax.grid(True, color=fs.PALETTE.grid, lw=fs.STROKE.grid)
        ax.set_axisbelow(True)
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 50)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:histogram")
def _histogram(asset: Asset, path: Path) -> None:
    """A histogram — for the DISTRIBUTION of a numeric variable. spec:
    {values:[…], bins?, xlabel?, ylabel?, title?}."""
    s = asset.spec or {}
    vals = [float(v) for v in s.get("values", [])]
    # large measured values scale to Mio./Mrd. (unit into the xlabel) — never scientific
    vals, xlabel, xdiv = unit_scale(vals, s.get("xlabel") or s.get("x_label") or "")
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(5.6, 3.6), layout="constrained")
        ax.hist(vals, bins=int(s.get("bins", 8)), color=fs.PALETTE.primary,
                edgecolor=fs.edge("primary"))
        if xdiv > 1 or (vals and max(abs(v) for v in vals) >= 1e5):
            _german_value_axis(ax, "x")
        if xlabel:
            ax.set_xlabel(xlabel)
        ax.set_ylabel(s.get("ylabel") or s.get("y_label") or "Häufigkeit")
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 50)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:boxplot")
def _boxplot(asset: Asset, path: Path) -> None:
    """A box-and-whisker plot — the FIVE-NUMBER SUMMARY of a distribution (a WS-strand
    staple the Matura uses heavily). Correct-by-construction: render from an explicit
    summary so the figure never invents data. spec:
    {summary:{min,q1,median,q3,max}} (one box) | {values:[…]} (compute the quartiles) |
    {groups:[{label, summary|values}, …]} (compare distributions, e.g. Datenliste A vs B);
    xlabel?, title?, vertical? (default horizontal — the Austrian Kastenschaubild convention)}."""
    import numpy as np
    s = asset.spec or {}

    def _stats(item: dict) -> dict:
        if item.get("summary"):
            su = item["summary"]
            return {"whislo": float(su["min"]), "q1": float(su["q1"]),
                    "med": float(su["median"]), "q3": float(su["q3"]),
                    "whishi": float(su["max"]), "fliers": [], "label": item.get("label", "")}
        vals = sorted(float(v) for v in item.get("values", []))
        q1, med, q3 = (float(np.percentile(vals, p)) for p in (25, 50, 75))
        return {"whislo": vals[0], "q1": q1, "med": med, "q3": q3, "whishi": vals[-1],
                "fliers": [], "label": item.get("label", "")}

    groups = s.get("groups") or [s]
    stats = [_stats(g) for g in groups]
    horizontal = not s.get("vertical")
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(5.6, 0.9 + 0.7 * len(stats)) if horizontal
                               else (1.2 + 1.0 * len(stats), 3.8), layout="constrained")
        ax.bxp(stats, orientation="horizontal" if horizontal else "vertical",
               showfliers=False, patch_artist=True,
               boxprops={"facecolor": fs.lighten(fs.PALETTE.primary, 0.72),
                         "edgecolor": fs.PALETTE.ink},
               medianprops={"color": fs.PALETTE.focus, "linewidth": 2},   # the median = focus
               whiskerprops={"color": fs.PALETTE.ink}, capprops={"color": fs.PALETTE.ink})
        whisk = [abs(st[k]) for st in stats for k in ("whislo", "whishi")]
        if whisk and max(whisk) >= 1e5:            # big values: German grouping, never sci
            _german_value_axis(ax, "x" if horizontal else "y")
        (ax.set_xlabel if horizontal else ax.set_ylabel)(s.get("xlabel") or s.get("x_label") or "")
        (ax.grid)(True, axis="x" if horizontal else "y", color=fs.PALETTE.grid, lw=fs.STROKE.grid)
        ax.set_axisbelow(True)
        if not any(st["label"] for st in stats):
            (ax.set_yticks if horizontal else ax.set_xticks)([])
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 50)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:function_graph")
def _function_graph(asset: Asset, path: Path) -> None:
    """A coordinate graph. spec: {xmin?, xmax?, m?, b? (line y=mx+b), points?: [[x,y],…],
    connect? (join the points with a line, e.g. a v-t graph), xlabel?, ylabel?,
    ymin?, ymax?, title?}."""
    s = asset.spec or {}
    xmin, xmax = float(s.get("xmin", -5)), float(s.get("xmax", 5))
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(4.6, 4.2), layout="constrained")
        ax.axhline(0, color=fs.PALETTE.muted, lw=0.8)
        ax.axvline(0, color=fs.PALETTE.muted, lw=0.8)
        ax.grid(True, color=fs.PALETTE.grid, lw=fs.STROKE.grid)
        ax.set_axisbelow(True)
        if "m" in s:                            # the line/graph is the object of interest → focus
            m, b = float(s["m"]), float(s.get("b", 0))
            ax.plot([xmin, xmax], [m * xmin + b, m * xmax + b], color=fs.PALETTE.focus, lw=2)
        pts = s.get("points", [])
        if s.get("connect") and len(pts) >= 2:  # join points into a curve (e.g. a v-t graph)
            ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", color=fs.PALETTE.primary,
                    lw=2, ms=6)
        else:
            for p in pts:
                ax.plot([p[0]], [p[1]], "o", color=fs.PALETTE.primary, ms=6)
        ax.set_xlim(xmin, xmax)
        if "ymin" in s and "ymax" in s:
            ax.set_ylim(float(s["ymin"]), float(s["ymax"]))
        if s.get("xlabel"):
            ax.set_xlabel(s["xlabel"])
        if s.get("ylabel"):
            ax.set_ylabel(s["ylabel"])
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 46)))
        fig.savefig(path, dpi=150)  # constrained_layout keeps title/labels from colliding
        plt.close(fig)


@_generator("matplotlib:math_formula")
def _math_formula(asset: Asset, path: Path) -> None:
    """Typeset a formula via matplotlib mathtext — math is a content asset.
    spec: {latex}. Store math semantically (LaTeX) so a future HTML renderer can
    typeset the same string via KaTeX."""
    s = asset.spec or {}
    with plt.rc_context(_HOUSE()):
        fig = plt.figure(figsize=(0.01, 0.01))
        # pinned black (not PALETTE.ink): a display formula sits in the TEXT flow and must
        # match the inline-math runs (rendering/inline_math.py), which render outside the
        # house rc and therefore black.
        fig.text(0, 0, f"${s.get('latex', '')}$", fontsize=20, color="black")
        fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.15, transparent=True)
        plt.close(fig)


@_generator("matplotlib:tree_diagram")
def _tree_diagram(asset: Asset, path: Path) -> None:
    """A probability tree (Baumdiagramm) — a multi-stage Zufallsversuch, a WS-strand staple.
    Structural (declared on body.assets, like geometry), correct-by-construction: branch
    probabilities + outcome labels are spec-provided so the figure never invents them.
    spec: {branches:[{label, p?, children?:[{label, p?, children?…}]}], title?}; p renders as
    the edge label (e.g. "0,3"). Any depth; parents sit at the mean of their children.

    Composed on the scene engine (`nodelink.tree_scene`): plain dot-nodes + labelled edges +
    white p-chips, one node-link visual language shared with cause_effect/process_flow."""
    scene_to_png(tree_scene(asset.spec or {}), path, dpi=150)


@_generator("matplotlib:cause_effect")
def _cause_effect(asset: Asset, path: Path) -> None:
    """A Wirkungsgefüge — cause→effect links as labelled boxes joined by arrows (the
    Sachverhalt content layer, GPB/history). Structural, correct-by-construction: the boxes
    and arrows are spec-provided, so the figure never invents a relationship. spec:
    {links:[{"cause":str,"effect":str,"kind"?:str}], title?}. Distinct causes stack on the
    left, distinct effects on the right; each link draws one arrow (a cause may fan out).

    Composed on the scene engine (`nodelink.cause_effect_scene`)."""
    scene_to_png(cause_effect_scene(asset.spec or {}), path, dpi=150)


@_generator("matplotlib:process_flow")
def _process_flow(asset: Asset, path: Path) -> None:
    """A process / cycle — ordered named steps joined by arrows (the Sachverhalt content layer,
    Biology's undated sibling of the timeline). Structural, correct-by-construction: the steps and
    their order are spec-provided. spec: {steps:[{name, text?}], cyclic?:bool, title?}. A cyclic
    process (e.g. der Blutkreislauf) is drawn around a circle with the last step looping back to the
    first; a linear one flows top→bottom.

    Composed on the scene engine (`nodelink.process_scene`)."""
    scene_to_png(process_scene(asset.spec or {}), path, dpi=150)


def _geo_centroid(geom: dict) -> tuple[float, float]:
    """A label anchor — the mean of the largest polygon's exterior ring (good enough; a true
    area centroid is overkill for placing a region name)."""
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    ring = max(polys, key=lambda p: len(p[0]))[0]
    xs = [pt[0] for pt in ring]
    ys = [pt[1] for pt in ring]
    return sum(xs) / len(xs), sum(ys) / len(ys)


@_generator("matplotlib:choropleth_map")
def _choropleth_map(asset: Asset, path: Path) -> None:
    """A thematic (choropleth) map — regions of a SOURCED boundary set, filled by a CITED value
    (the map analogue of the grounded-facts figures, GWB). spec: {geo_id, values:{region:number},
    value_label?, citation?, title?}. Boundaries are FACTS (loaded by `geo_id` from the geo store,
    never authored); the fill values are sourced + cited. Pure matplotlib polygons — no geo
    dependency. A hole (e.g. Wien enclosed by Niederösterreich) renders via the even-odd rule."""
    import math

    import matplotlib.patheffects as pe
    from matplotlib.colors import Normalize
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MplPath

    from ..grounding import geo_store

    s = asset.spec or {}
    geo_id = s.get("geo_id")
    values = {str(k): float(v) for k, v in (s.get("values") or {}).items() if v is not None}
    geoms = geo_store.load_boundaries(geo_id) if geo_id else {}
    # semantic roles as locals (the choropleth draws with explicit colours: region borders =
    # paper, labels/leaders = ink/muted, an unmapped region = no_data). `fs` is the styleguide.
    _ink, _muted, _paper, _nodata = (fs.PALETTE.ink, fs.PALETTE.muted, fs.PALETTE.paper,
                                     fs.PALETTE.no_data)

    def feature_path(geom: dict) -> "MplPath":
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        verts: list = []
        codes: list = []
        for poly in polys:                       # polygon = [exterior, *holes]
            for ring in poly:
                if len(ring) < 3:
                    continue
                verts.append((ring[0][0], ring[0][1]))
                codes.append(MplPath.MOVETO)
                for pt in ring[1:]:
                    verts.append((pt[0], pt[1]))
                    codes.append(MplPath.LINETO)
                verts.append((ring[0][0], ring[0][1]))
                codes.append(MplPath.CLOSEPOLY)
        return MplPath(verts, codes)

    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(7.4, 6.2), layout="constrained")
        ax.axis("off")
        norm = Normalize(vmin=min(values.values()) if values else 0.0,
                         vmax=max(values.values()) if values else 1.0)
        cmap = plt.get_cmap(fs.SEQUENTIAL)
        xs_all: list[float] = []
        ys_all: list[float] = []
        cents: dict[str, tuple[float, float]] = {}
        bboxes: dict[str, tuple[float, float, float, float]] = {}
        for name, geom in geoms.items():
            mp = feature_path(geom)
            val = values.get(name)
            fc = cmap(norm(val)) if val is not None else _nodata
            ax.add_patch(PathPatch(mp, facecolor=fc, edgecolor=_paper, lw=0.7, zorder=2))
            gx = [v[0] for v in mp.vertices]
            gy = [v[1] for v in mp.vertices]
            xs_all += gx
            ys_all += gy
            cents[name] = _geo_centroid(geom)
            bboxes[name] = (min(gx), max(gx), min(gy), max(gy))
        if xs_all:
            mx = (max(xs_all) - min(xs_all)) * 0.03 or 0.1
            my = (max(ys_all) - min(ys_all)) * 0.03 or 0.1
            ax.set_xlim(min(xs_all) - mx, max(xs_all) + mx)
            ax.set_ylim(min(ys_all) - my, max(ys_all) + my)
            mean_lat = (min(ys_all) + max(ys_all)) / 2
            ax.set_aspect(1.0 / max(0.3, math.cos(math.radians(mean_lat))))   # equirectangular fix
        # labels: a big region's name fits in place (font shrunk to its width); a tiny enclave
        # (e.g. Wien inside Niederösterreich) is leadered out BELOW the map, so it can never collide
        # with the enclosing region's label (the small-polygon labelling fix; see figtext.py).
        if geoms and xs_all:
            from .figtext import measure_widths
            areas = {n: (b[1] - b[0]) * (b[3] - b[2]) for n, b in bboxes.items()}
            amax = max(areas.values()) or 1.0
            yspan = (max(ys_all) - min(ys_all)) or 1.0
            small = [n for n in geoms if areas[n] < 0.06 * amax]
            for name in geoms:
                cx, cy = cents[name]
                if name not in small:
                    rw = bboxes[name][1] - bboxes[name][0]
                    fsz = 8.0                    # NB: local font size, NOT the `fs` styleguide module
                    while measure_widths(ax, [name], fsz)[0] > rw * 0.94 and fsz > 6.0:
                        fsz -= 0.5
                    ax.text(cx, cy, name, ha="center", va="center", fontsize=fsz, color=_ink,
                            zorder=4, path_effects=[pe.withStroke(linewidth=2.0, foreground=_paper)])
                else:
                    # leader + label as SEPARATE artists (not an arrow-annotation), so the label's
                    # measured bbox is the text alone — the choropleth's small-polygon labelling.
                    ly = min(ys_all) - yspan * 0.02
                    ax.plot([cx, cx], [cy, ly], color=_muted, lw=0.7, zorder=5)
                    ax.plot([cx], [cy], "o", ms=2.5, color=_ink, zorder=5)
                    ax.text(cx, ly, name, ha="center", va="top", fontsize=7.5, color=_ink,
                            zorder=5, path_effects=[pe.withStroke(linewidth=2.0, foreground=_paper)])
            if small:
                ax.set_ylim(min(ys_all) - yspan * 0.13, max(ys_all) + my)
        if values:
            sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])
            cb = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02)
            cb.ax.tick_params(labelsize=7)
            # German plain tick labels — never a "1e6" offset in the corner (the figstyle
            # representation rule; the value axis is scaled into the label if it's large).
            cvals = list(values.values())
            _, clabel, cdiv = unit_scale(cvals, s.get("value_label") or "")
            from matplotlib.ticker import FuncFormatter
            cb.ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_de(v / cdiv)))
            cb.set_label(clabel or str(s.get("value_label", "")), fontsize=8)
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 48)), fontsize=fs.TYPE.title)
        cits = []                                # a map rests on TWO facts: values + boundaries
        if s.get("citation"):
            cits.append(f"Daten: {s['citation']}")
        if geo_id:
            cits.append(f"Grenzen: {geo_store.citation(geo_id)}")
        if cits:
            fig.text(0.5, 0.008, "Quelle — " + " · ".join(cits), ha="center", fontsize=6.5,
                     color=_muted)
        fig.savefig(path, dpi=150)
        plt.close(fig)


# --- geometry recipe family (KB3 Figuren und Körper) -------------------------
# Correct-by-construction geometric figures; labels are spec-provided so a figure never
# leaks the answer (e.g. show "c = ?" for a Pythagoras task). Equal aspect, no data axes.
def _geo_fig(w: float = 4.4, h: float = 3.8):
    fig, ax = plt.subplots(figsize=(w, h), layout="constrained")
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def _geo_title(ax, s: dict) -> None:
    if s.get("title"):
        ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 46)))


@_generator("matplotlib:right_triangle")
def _right_triangle(asset: Asset, path: Path) -> None:
    """A right triangle for Pythagoras: legs a (bottom) and b (left), right angle marked,
    hypotenuse c. spec: {a, b, label_a?, label_b?, label_c?, title?}. Labels are strings
    (e.g. "a = 3 cm" or "c = ?") so the figure shows the task, not the answer.

    Composed as a `Scene` (a filled `Region` + a right-angle `Polyline` + `Label`s) and drawn by
    the shared `render_scene` — the geometry face of the scene engine, so the house style (surface
    fill, ink edge, the unknown in `focus`) is guaranteed, not re-specified per recipe."""
    s = asset.spec or {}
    a, b = float(s.get("a", 4)), float(s.get("b", 3))
    m = min(a, b) * 0.13                                   # right-angle square at the origin
    sc = Scene(canvas=Canvas(figsize=(4.2, 3.6), aspect="equal", frame="off",
                             xlim=(-0.2 * a, a * 1.12), ylim=(-0.2 * b, b * 1.12),
                             title=str(s["title"]) if s.get("title") else None))
    sc.add(Region([(0, 0), (a, 0), (0, b)], role="surface", alpha=1.0,
                  edge_role="ink", edge_width=1.8, z=1))
    sc.add(Polyline([(m, 0), (m, m), (0, m)], role="ink", width=1.0, z=3))
    sc.add(Label((a / 2, -0.07 * b), str(s.get("label_a", "a")), role="ink",
                 size=fs.TYPE.annot_lg, va="top", halo=False))
    sc.add(Label((-0.03 * a, b / 2), str(s.get("label_b", "b")), role="ink",
                 size=fs.TYPE.annot_lg, ha="right", halo=False))
    sc.add(Label((a / 2 + 0.03 * a, b / 2 + 0.03 * b), str(s.get("label_c", "c")),
                 role="focus", size=fs.TYPE.annot_lg, ha="left", va="bottom"))  # the unknown → focus
    scene_to_png(sc, path)


@_generator("matplotlib:rectangle")
def _rectangle_fig(asset: Asset, path: Path) -> None:
    """A labeled rectangle. spec: {length, width, label_l?, label_w?, title?}. A `Scene`
    (filled `Region` + side `Label`s) drawn by `render_scene` — the geometry house style."""
    s = asset.spec or {}
    le, w = float(s.get("length", 6)), float(s.get("width", 4))
    sc = Scene(canvas=Canvas(figsize=(4.8, 3.4), aspect="equal", frame="off",
                             xlim=(-0.22 * le, le * 1.08), ylim=(-0.28 * w, w * 1.12),
                             title=str(s["title"]) if s.get("title") else None))
    sc.add(Region([(0, 0), (le, 0), (le, w), (0, w)], role="surface", alpha=1.0,
                  edge_role="ink", edge_width=1.8, z=1))
    sc.add(Label((le / 2, -0.09 * w), str(s.get("label_l", f"{le:g}")), role="ink",
                 size=fs.TYPE.annot_lg, va="top", halo=False))
    sc.add(Label((-0.02 * le, w / 2), str(s.get("label_w", f"{w:g}")), role="ink",
                 size=fs.TYPE.annot_lg, ha="right", halo=False))
    scene_to_png(sc, path)


@_generator("matplotlib:polygon")
def _polygon(asset: Asset, path: Path) -> None:
    """A general labeled polygon (triangles, quadrilaterals, Vielecke). spec:
    {points:[[x,y],…], vertex_labels?:[str], side_labels?:[str], title?}. A `Scene` — a filled
    `Region`, `PointMark` vertices labelled outward from the centroid, side `Label`s in `focus`."""
    s = asset.spec or {}
    pts = [(float(x), float(y)) for x, y in s.get("points", [(0, 0), (4, 0), (2, 3)])]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    span = max(max(p[0] for p in pts) - min(p[0] for p in pts),
               max(p[1] for p in pts) - min(p[1] for p in pts)) or 1.0
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    pad = 0.18 * span
    sc = Scene(canvas=Canvas(figsize=(4.4, 3.8), aspect="equal", frame="off",
                             xlim=(min(xs) - pad, max(xs) + pad),
                             ylim=(min(ys) - pad, max(ys) + pad),
                             title=str(s["title"]) if s.get("title") else None))
    sc.add(Region(pts, role="surface", alpha=1.0, edge_role="ink", edge_width=1.8, z=1))
    vl = s.get("vertex_labels") or []
    for i, (x, y) in enumerate(pts):
        lab = str(vl[i]) if i < len(vl) else None
        if lab is not None:                                # label offset outward from the centroid
            dx, dy = x - cx, y - cy
            n = (dx * dx + dy * dy) ** 0.5 or 1
            off = (0.12 * span * dx / n, 0.12 * span * dy / n)
        else:
            off = (0.0, 0.0)
        sc.add(PointMark((x, y), label=lab, role="ink", size=4.0, label_offset=off,
                         bold=False, z=6))
    for i, lab in enumerate(s.get("side_labels") or []):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        sc.add(Label(((x1 + x2) / 2, (y1 + y2) / 2), str(lab), role="focus",
                     size=fs.TYPE.annot, halo=True))
    scene_to_png(sc, path)


@_generator("matplotlib:solid_net")
def _solid_net(asset: Asset, path: Path) -> None:
    """A computed Quader/Würfel net composed from scene primitives.

    The geometry function owns the face dimensions and fold adjacencies; this wrapper is
    deliberately only the registered asset projection.
    """
    scene_to_png(solid_net_scene(asset.spec or {}), path)


@_generator("matplotlib:circle")
def _circle(asset: Asset, path: Path) -> None:
    """A circle with centre + radius. spec: {radius, label_r?, title?}. Kept as
    matplotlib-on-figstyle (the scene `CircleShape` ties face and edge to one role, so a
    surface fill with an ink outline needs the patch here); colours are semantic roles."""
    s = asset.spec or {}
    r = float(s.get("radius", 3))
    with plt.rc_context(_HOUSE()):
        fig, ax = _geo_fig(4.0, 4.0)
        ax.add_patch(Circle((0, 0), r, facecolor=fs.PALETTE.surface,
                            edgecolor=fs.PALETTE.ink, lw=1.8))
        ax.plot([0], [0], "o", color=fs.PALETTE.ink, ms=4)
        ax.plot([0, r], [0, 0], color=fs.PALETTE.focus, lw=1.4)   # radius = the measure of interest
        ax.text(r / 2, 0.05 * r, str(s.get("label_r", f"r = {r:g}")), ha="center", va="bottom",
                fontsize=fs.TYPE.annot_lg, color=fs.PALETTE.focus)
        ax.set_xlim(-r * 1.15, r * 1.15)
        ax.set_ylim(-r * 1.15, r * 1.15)
        _geo_title(ax, s)
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:coordinate_plane")
def _coordinate_plane(asset: Asset, path: Path) -> None:
    """A cartesian grid with labeled points + optional segments (KB2/3 coordinate geometry).
    spec: {points:[{x,y,label?}]|[[x,y]], segments?:[[i,j]], xmin?,xmax?,ymin?,ymax?, title?}."""
    s = asset.spec or {}
    raw = s.get("points", [])
    pts = [(p if isinstance(p, dict) else {"x": p[0], "y": p[1]}) for p in raw]
    xs = [p["x"] for p in pts] or [0]
    ys = [p["y"] for p in pts] or [0]
    xmin = int(s.get("xmin", min(0, *xs)))
    xmax = int(s.get("xmax", max(5, *xs)))
    ymin = int(s.get("ymin", min(0, *ys)))
    ymax = int(s.get("ymax", max(5, *ys)))
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(4.6, 4.4), layout="constrained")
        ax.set_xlim(xmin - 0.5, xmax + 0.5)
        ax.set_ylim(ymin - 0.5, ymax + 0.5)
        ax.set_xticks(range(xmin, xmax + 1))
        ax.set_yticks(range(ymin, ymax + 1))
        ax.grid(True, color=fs.PALETTE.grid, lw=fs.STROKE.grid)
        ax.set_axisbelow(True)
        ax.set_aspect("equal")
        ax.axhline(0, color=fs.PALETTE.muted, lw=1.0)          # the axes through the origin
        ax.axvline(0, color=fs.PALETTE.muted, lw=1.0)
        for i, j in s.get("segments", []):
            ax.plot([pts[i]["x"], pts[j]["x"]], [pts[i]["y"], pts[j]["y"]],
                    color=fs.PALETTE.ink, lw=1.8)
        for p in pts:                                          # the plotted points = focus
            ax.plot([p["x"]], [p["y"]], "o", color=fs.PALETTE.focus, ms=6)
            if p.get("label"):
                ax.text(p["x"] + 0.15, p["y"] + 0.15, str(p["label"]), fontsize=fs.TYPE.annot,
                        color=fs.PALETTE.focus)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        if s.get("title"):
            ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 46)))
        fig.savefig(path, dpi=150)
        plt.close(fig)


# --- the Rätsel engine (A5): one parameterized grid recipe for all puzzle types --------
# Curated/derived-only (NOT in GENERATION_RECIPES — a puzzle is built by pipeline/puzzles.py,
# never requested by an LLM). Draws empty (student) or solved (teacher) states in house style:
# ink outlines on paper, solution letters/marks in `focus`, the TYPE scale for legibility.
@_generator("matplotlib:puzzle_grid")
def _puzzle_grid(asset: Asset, path: Path) -> None:
    """Render a puzzle grid. spec: {puzzle_type, solved, …type-specific…}. Dispatches on
    `puzzle_type` to a crossword / suchsel / domino / rechenmauer drawer; all share the house
    ink/paper roles and put the solution in `focus`."""
    s = asset.spec or {}
    ptype = s.get("puzzle_type")
    drawer = {"crossword": _draw_crossword, "suchsel": _draw_suchsel,
              "domino": _draw_domino, "rechenmauer": _draw_rechenmauer}.get(ptype)
    if drawer is None:
        raise ValueError(f"puzzle_grid: unknown puzzle_type {ptype!r}")
    with plt.rc_context(_HOUSE()):
        drawer(s, path)


def _puzzle_title(ax, s: dict) -> None:
    if s.get("title"):
        ax.set_title(str(s["title"]), fontsize=fs.TYPE.title, color=fs.PALETTE.ink)


def _draw_crossword(s: dict, path: Path) -> None:
    from matplotlib.patches import Rectangle
    cells = s.get("cells", [])
    nrows, ncols = s.get("nrows", len(cells)), s.get("ncols", len(cells[0]) if cells else 1)
    fig, ax = plt.subplots(figsize=(min(9.0, 0.62 * ncols + 1.0),
                                    min(9.0, 0.62 * nrows + 1.0)), layout="constrained")
    ax.set_aspect("equal")
    ax.axis("off")
    for r in range(nrows):
        for c in range(ncols):
            cell = cells[r][c]
            y = nrows - 1 - r                          # row 0 at the top
            if not cell.get("fill"):
                continue                               # blocked square: leave it blank (paper)
            ax.add_patch(Rectangle((c, y), 1, 1, facecolor=fs.PALETTE.paper,
                                   edgecolor=fs.PALETTE.ink, lw=1.2, zorder=1))
            if cell.get("number") is not None:
                ax.text(c + 0.06, y + 0.94, str(cell["number"]), ha="left", va="top",
                        fontsize=fs.TYPE.caption, color=fs.PALETTE.muted, zorder=3)
            if cell.get("letter"):                     # solved: the answer in focus
                ax.text(c + 0.5, y + 0.44, str(cell["letter"]), ha="center", va="center",
                        fontsize=fs.TYPE.title, color=fs.PALETTE.focus, zorder=3)
    ax.set_xlim(-0.2, ncols + 0.2)
    ax.set_ylim(-0.2, nrows + 0.6)
    _puzzle_title(ax, s)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _draw_suchsel(s: dict, path: Path) -> None:
    from matplotlib.patches import Rectangle
    cells = s.get("cells", [])
    n = s.get("size", len(cells))
    fig, ax = plt.subplots(figsize=(min(9.0, 0.52 * n + 1.0),
                                    min(9.0, 0.52 * n + 1.0)), layout="constrained")
    ax.set_aspect("equal")
    ax.axis("off")
    for r in range(n):
        for c in range(n):
            cell = cells[r][c]
            y = n - 1 - r
            if cell.get("mark"):                       # solved: highlight the found letters
                ax.add_patch(Rectangle((c, y), 1, 1,
                                       facecolor=fs.lighten(fs.PALETTE.focus, 0.7),
                                       edgecolor="none", zorder=1))
            colour = fs.PALETTE.focus if cell.get("mark") else fs.PALETTE.ink
            ax.text(c + 0.5, y + 0.5, str(cell.get("letter", "")), ha="center", va="center",
                    fontsize=fs.TYPE.base, color=colour, zorder=3)
    ax.set_xlim(-0.2, n + 0.2)
    ax.set_ylim(-0.2, n + 0.6)
    _puzzle_title(ax, s)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _draw_domino(s: dict, path: Path) -> None:
    from matplotlib.patches import Rectangle
    tiles = s.get("tiles", [])
    solved = bool(s.get("solved"))
    n = len(tiles)
    per_row = 3 if n > 4 else n or 1                   # wrap long chains onto several rows
    nrows = (n + per_row - 1) // per_row
    tw, th, gap = 3.4, 1.2, 0.5
    fig, ax = plt.subplots(figsize=(min(11.0, per_row * (tw + gap) + 0.6),
                                    max(1.8, nrows * (th + gap) + 0.6)), layout="constrained")
    ax.set_aspect("equal")
    ax.axis("off")

    def wrap(t: str, width: int = 16) -> str:
        return "\n".join(textwrap.wrap(str(t), width)) or str(t)

    for idx, tile in enumerate(tiles):
        row, col = divmod(idx, per_row)
        x = col * (tw + gap)
        y = (nrows - 1 - row) * (th + gap)
        # tile body + the centre divider (a real domino)
        ax.add_patch(Rectangle((x, y), tw, th, facecolor=fs.PALETTE.surface,
                               edgecolor=fs.PALETTE.ink, lw=1.4, zorder=1))
        ax.plot([x + tw / 2, x + tw / 2], [y + 0.08, y + th - 0.08],
                color=fs.PALETTE.ink, lw=1.0, zorder=2)
        ax.text(x + tw / 4, y + th / 2, wrap(tile["left"]), ha="center", va="center",
                fontsize=fs.TYPE.annot, color=fs.PALETTE.ink, zorder=3)
        ax.text(x + 3 * tw / 4, y + th / 2, wrap(tile["right"]), ha="center", va="center",
                fontsize=fs.TYPE.annot, color=fs.PALETTE.focus if solved else fs.PALETTE.ink,
                zorder=3)
        if solved and idx < n - 1 and col < per_row - 1:   # a connector arrow in the loop
            ax.annotate("", xy=(x + tw + gap, y + th / 2), xytext=(x + tw, y + th / 2),
                        arrowprops={"arrowstyle": "-|>", "color": fs.PALETTE.muted, "lw": 1.2})
    ax.set_xlim(-0.3, per_row * (tw + gap))
    ax.set_ylim(-0.3, nrows * (th + gap) + 0.3)
    _puzzle_title(ax, s)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _draw_rechenmauer(s: dict, path: Path) -> None:
    from matplotlib.patches import Rectangle
    rows = s.get("rows", [])                           # apex first (top), base last
    nrows = len(rows)
    base_n = max((len(r) for r in rows), default=1)
    bw = 1.0
    fig, ax = plt.subplots(figsize=(min(10.0, base_n * bw + 1.0),
                                    max(2.0, nrows * bw + 0.8)), layout="constrained")
    ax.set_aspect("equal")
    ax.axis("off")
    for i, row in enumerate(rows):
        y = (nrows - 1 - i) * bw                        # apex (i=0) at the top
        offset = (base_n - len(row)) / 2.0             # centre each row over the base
        for j, brick in enumerate(row):
            x = (offset + j) * bw
            val = brick.get("value")
            # a masked (blank) brick reads as the thing to solve → focus edge; a given one is ink
            given = val is not None
            ax.add_patch(Rectangle((x, y), bw, bw,
                                   facecolor=fs.PALETTE.paper if given
                                   else fs.lighten(fs.PALETTE.focus, 0.85),
                                   edgecolor=fs.PALETTE.ink if given else fs.PALETTE.focus,
                                   lw=1.4, zorder=1))
            if given:
                ax.text(x + bw / 2, y + bw / 2, str(val), ha="center", va="center",
                        fontsize=fs.TYPE.title, color=fs.PALETTE.ink, zorder=3)
    ax.set_xlim(-0.2, base_n * bw + 0.2)
    ax.set_ylim(-0.2, nrows * bw + 0.6)
    _puzzle_title(ax, s)
    fig.savefig(path, dpi=150)
    plt.close(fig)


# --- scene-engine recipes (composed: a Scene of primitives, not one bespoke figure) ----
@_generator("matplotlib:triangle_construction")
def _triangle_construction(asset: Asset, path: Path) -> None:
    """The triangle's notable points (merkwürdige Punkte) as a step-by-step construction —
    the first scene-engine recipe. spec: {vertices:[[x,y],[x,y],[x,y]], stage?:1–6, title?}.
    Everything (centres, circles, angles) is COMPUTED from the vertices; `stage` selects how
    far the construction has progressed (so one scene → the whole construction worksheet)."""
    s = asset.spec or {}
    verts = s.get("vertices") or [[0, 0], [8, 0], [1.5, 4.0]]
    g = triangle_geometry(*[tuple(v) for v in verts])
    scene = construction_scene(g, int(s.get("stage", 6)))
    if s.get("title"):
        scene.canvas.title = str(s["title"])
    scene_to_png(scene, path)


@_generator("matplotlib:function_plot")
def _function_plot(asset: Asset, path: Path) -> None:
    """A function graph y = f(x) over an interval (an ARBITRARY function via sympy — what the
    line/point `function_graph` can't do). spec: {expr, xmin?, xmax?, ymin?, ymax?, label?, title?}."""
    s = asset.spec or {}
    scene_to_png(function_scene(s.get("expr", "x"), float(s.get("xmin", -5)),
                                float(s.get("xmax", 5)), **_drop(s, "expr", "xmin", "xmax")), path)


@_generator("matplotlib:integral_area")
def _integral_area(asset: Asset, path: Path) -> None:
    """f(x) with the area under it on [a,b] shaded — the definite integral; the value is COMPUTED
    (sympy) and maskable. spec: {expr, a, b, xmin?, xmax?, show_value?, label?, title?}."""
    s = asset.spec or {}
    scene_to_png(integral_scene(s.get("expr", "x"), float(s["a"]), float(s["b"]),
                                s.get("xmin"), s.get("xmax"),
                                show_value=s.get("show_value", True), **_drop(s, "expr", "a", "b",
                                "xmin", "xmax", "show_value")), path)


@_generator("matplotlib:tangent")
def _tangent(asset: Asset, path: Path) -> None:
    """f(x) with the tangent at x0 — the derivative as slope, k = f'(x0) COMPUTED (sympy) and
    maskable. spec: {expr, x0, xmin?, xmax?, show_slope?, slope_triangle?, label?, title?}."""
    s = asset.spec or {}
    scene_to_png(tangent_scene(s.get("expr", "x**2"), float(s["x0"]), s.get("xmin"), s.get("xmax"),
                               show_slope=s.get("show_slope", True),
                               slope_triangle=s.get("slope_triangle", True),
                               **_drop(s, "expr", "x0", "xmin", "xmax", "show_slope",
                               "slope_triangle")), path)


@_generator("matplotlib:riemann_sum")
def _riemann_sum(asset: Asset, path: Path) -> None:
    """The definite integral approximated by n rectangles (motivates ∫; Ober-/Untersumme).
    spec: {expr, a, b, n?, mode?:left|right|mid, xmin?, xmax?, title?}. Sum + exact value COMPUTED."""
    s = asset.spec or {}
    scene_to_png(riemann_scene(s.get("expr", "x"), float(s["a"]), float(s["b"]),
                               int(s.get("n", 6)), s.get("mode", "left"), s.get("xmin"),
                               s.get("xmax"), **_drop(s, "expr", "a", "b", "n", "mode",
                               "xmin", "xmax")), path)


@_generator("matplotlib:extrema")
def _extrema(asset: Asset, path: Path) -> None:
    """f(x) with local extrema (Hoch-/Tiefpunkt) marked + horizontal tangents — from f'(x)=0
    COMPUTED. spec: {expr, xmin?, xmax?, title?}."""
    s = asset.spec or {}
    scene_to_png(extrema_scene(s.get("expr", "x**3-3*x"), float(s.get("xmin", -5)),
                               float(s.get("xmax", 5)), **_drop(s, "expr", "xmin", "xmax")), path)


@_generator("matplotlib:area_between")
def _area_between(asset: Asset, path: Path) -> None:
    """The area between two curves f and g — A = ∫|f−g| dx COMPUTED. spec: {expr, expr2, a?, b?
    (default the outer intersections), xmin?, xmax?, show_value?, title?}."""
    s = asset.spec or {}
    scene_to_png(area_between_scene(s.get("expr", "x"), s.get("expr2", "0"), s.get("a"),
                                    s.get("b"), s.get("xmin"), s.get("xmax"),
                                    show_value=s.get("show_value", True),
                                    **_drop(s, "expr", "expr2", "a", "b", "xmin", "xmax",
                                    "show_value")), path)


@_generator("matplotlib:distribution")
def _distribution(asset: Asset, path: Path) -> None:
    """A normal density N(μ,σ) with a probability region shaded — area = probability COMPUTED
    (WS). spec: {mu?, sigma?, a?, b?, mode?:between|le|ge, show_value?, title?}."""
    s = asset.spec or {}
    scene_to_png(distribution_scene(float(s.get("mu", 0)), float(s.get("sigma", 1)),
                                    a=s.get("a"), b=s.get("b"), mode=s.get("mode", "between"),
                                    show_value=s.get("show_value", True),
                                    **_drop(s, "mu", "sigma", "a", "b", "mode", "show_value")),
                 path)


@_generator("matplotlib:vector_addition")
def _vector_addition(asset: Asset, path: Path) -> None:
    """Vector addition (Kräfteaddition), tip-to-tail or parallelogram — the resultant is
    COMPUTED from the component sum, maskable ("F_R = ?"). spec: {vectors:[{magnitude,
    angle_deg}|{dx,dy}, label?…], method?, show_resultant?, show_value?, unit?,
    resultant_name?, title?}."""
    from .physics_scenes import vector_addition_scene
    s = asset.spec or {}
    scene_to_png(vector_addition_scene(
        s.get("vectors") or [{"magnitude": 3, "angle_deg": 0}, {"magnitude": 4, "angle_deg": 90}],
        method=s.get("method", "tip_to_tail"),
        show_resultant=s.get("show_resultant", True),
        show_value=s.get("show_value", True),
        **_drop(s, "vectors", "method", "show_resultant", "show_value")), path)


@_generator("matplotlib:force_diagram")
def _force_diagram(asset: Asset, path: Path) -> None:
    """Free-body diagram (Kräfteplan) — force arrows from the body's centre, lengths true to
    scale; the resultant is COMPUTED (equilibrium → "F_res = 0 N") and maskable. spec:
    {forces:[{magnitude, angle_deg, label?}…], body_label?, show_magnitudes?,
    show_resultant?, show_value?, unit?, resultant_name?, title?}."""
    from .physics_scenes import force_diagram_scene
    s = asset.spec or {}
    scene_to_png(force_diagram_scene(
        s.get("forces") or [{"magnitude": 15, "angle_deg": 270, "label": "F_G"},
                            {"magnitude": 15, "angle_deg": 90, "label": "F_N"}],
        body_label=s.get("body_label"),
        show_magnitudes=s.get("show_magnitudes", True),
        show_resultant=s.get("show_resultant", False),
        show_value=s.get("show_value", True),
        **_drop(s, "forces", "body_label", "show_magnitudes", "show_resultant",
                "show_value")), path)


@_generator("matplotlib:labeled_parts")
def _labeled_parts(asset: Asset, path: Path) -> None:
    """A "Beschrifte die Teile" schematic — numbered margin callouts with leader lines;
    numbering, leaders and solution names all DERIVED from one parts list (student figure
    and answer key cannot drift). spec: {shapes, parts, show_names? (false → numbered task,
    true → named solution), title?, figsize?}; empty spec → the curated volcano flagship."""
    from .labeled_diagram import VULKAN_SPEC, labeled_parts_scene
    s = asset.spec or {}
    spec = s if (s.get("shapes") or s.get("parts")) else {**VULKAN_SPEC, **s}
    scene_to_png(labeled_parts_scene(spec), path)


@_generator("matplotlib:optics_ray")
def _optics_ray(asset: Asset, path: Path) -> None:
    """Bildkonstruktion an einer dünnen Linse — the drei Hauptstrahlen as a step-by-step
    construction; the image position b/B and magnification are COMPUTED (thin-lens equation,
    sympy) and maskable. spec: {kind:"sammellinse"|"zerstreuungslinse", f:num, g:num, G:num,
    stage?:1–6, show_value?:bool, title?}. f/g/G are positive magnitudes; the lens type carries
    the focal-length sign (Sammellinse +f, Zerstreuungslinse −f). show_value=False masks ONLY
    the sought image quantities ("b = ?", "B = ?", "B′ = ?") — the givens g/G stay visible
    (gegeben→gesucht)."""
    s = asset.spec or {}
    scene = lens_construction(str(s.get("kind", "sammellinse")), float(s.get("f", 3.0)),
                              float(s.get("g", 6.0)), float(s.get("G", 2.0)),
                              stage=int(s.get("stage", 6)),
                              show_value=bool(s.get("show_value", True)))
    if s.get("title"):
        scene.canvas.title = str(s["title"])
    scene_to_png(scene, path)


@_generator("matplotlib:circuit")
def _circuit(asset: Asset, path: Path) -> None:
    """Stromkreis-Schaltbild aus einer Netzliste (verschachtelter Reihen-/Parallel-Baum von
    Widerständen) — Ersatzwiderstand, Ströme und Spannungen werden BERECHNET (Kirchhoff, sympy,
    exakt) und sind maskierbar. spec: {net:{type,children|ohm,label}, volt?:num,
    mask?:[str] (maskiert GENAU diese Werte — Element-Labels bzw. "U"/"I"/"Rers"; die übrigen
    Angaben bleiben sichtbar — die kanonische gegeben→gesucht-Aufgabe), show_value?:bool
    (false OHNE mask → alles maskiert; Rückwärtskompatibilität), ask?:str (Fokus-Element,
    z. B. "R₂"/"U"/"I" — orthogonal zu mask), title?}."""
    s = asset.spec or {}
    net = s.get("net") or {"type": "resistor", "ohm": 100, "label": "R"}
    scene_to_png(circuit_construction(net, float(s.get("volt", 12.0)),
                                      show_value=bool(s.get("show_value", True)),
                                      mask=s.get("mask"), ask=s.get("ask"),
                                      title=s.get("title")), path)


def _drop(d: dict, *keys) -> dict:
    """The remaining spec keys (label/title/ymin/ymax) passed through to a scene builder."""
    return {k: v for k, v in d.items() if k not in keys}


# --- 3D scene-engine recipes (Schrägbild: model in ℝ³, project to a 2D Scene) ----
# GZ (Geometrisches Zeichnen, US) / DG (Darstellende Geometrie, OS). Correct-by-construction: the
# solid's vertices/faces are COMPUTED from a few size parameters, the projection is one fixed
# linear map, and hidden-edge visibility is a closed-form back-face test (convex solids only —
# `pipeline/scene3d.py` + `Documents/scene3d-geometry-design.md`). The renderer stays the shared
# `render_scene`; no new backend.
@_generator("matplotlib:axonometric_solid")
def _axonometric_solid(asset: Asset, path: Path) -> None:
    """Schrägriss (Austrian Kabinettprojektion) of a school solid, hidden edges DASHED.
    spec: {kind:"quader"|"prism"|"pyramid"|"cylinder"|"cone" (German aliases ok), size params
    (quader a,b,c · prism/cylinder n,r,h · pyramid/cone n,r,h), labels?:{"a"|"b"|"c"|"r"|"h":str},
    show_measures?:bool (false → every measure prints "h = ?" for the student task), title?}.
    Vertices, faces and edge visibility are COMPUTED — the figure can never show a wrong hidden
    edge or a fabricated measurement; the measure labels are maskable (task vs. solution)."""
    s = asset.spec or {}
    scene_to_png(axonometric_solid_scene(
        s.get("kind", "quader"), labels=s.get("labels"),
        show_measures=s.get("show_measures", True), title=s.get("title"),
        **_drop(s, "kind", "labels", "show_measures", "title")), path)


@_generator("matplotlib:riss_pair")
def _riss_pair(asset: Asset, path: Path) -> None:
    """A Grund-/Aufriss pair (zugeordnete Normalrisse) — top view below + front view above one
    horizontal Rissachse, joined by vertical Ordnungslinien at a SHARED x scale. spec:
    {kind:… (as axonometric_solid), size params, ordnungslinien?:bool (default true), title?}.
    The two Risse are the same solid at the same measurement scale (the correspondence is exact:
    a point's x is identical in both), computed from the solid's geometry."""
    s = asset.spec or {}
    scene_to_png(riss_pair_scene(
        s.get("kind", "quader"), title=s.get("title"),
        ordnungslinien=s.get("ordnungslinien", True),
        **_drop(s, "kind", "title", "ordnungslinien")), path)


# --- bespoke figures (kept; correctness lives in the recipe, not params) ------
@_generator("matplotlib:em_spectrum")
def _em_spectrum(asset: Asset, path: Path) -> None:
    """EM spectrum, ordered by energy. correctness_surface: energy increases
    left→right; ionizing threshold marked. The figure itself is correct."""
    bands = [
        ("Radio", 1e-9), ("Mikro", 1e-6), ("IR", 1e-3),
        ("sichtbar", 2.0), ("UV", 1e2), ("Röntgen", 1e4), ("Gamma", 1e6),
    ]
    labels = [b[0] for b in bands]
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(7.2, 2.4))
        xs = range(len(bands))
        ax.bar(xs, [1] * len(bands), color=fs.PALETTE.surface, edgecolor=fs.PALETTE.ink)
        for x, lab in zip(xs, labels):
            ax.text(x, 0.5, lab, ha="center", va="center", fontsize=fs.TYPE.annot)
        thr = 4.5  # ionizing threshold between UV and Röntgen
        ax.axvline(thr, color=fs.PALETTE.focus, linestyle="--", linewidth=1.5)
        ax.text(thr + 0.05, 1.05, "ionisierend →", color=fs.PALETTE.focus, fontsize=fs.TYPE.tick,
                va="bottom")
        ax.text(thr - 0.05, 1.05, "← nicht-ionisierend", color=fs.PALETTE.positive,
                fontsize=fs.TYPE.tick, va="bottom", ha="right")
        ax.set_xlim(-0.6, len(bands) - 0.4)
        ax.set_ylim(0, 1.3)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.set_xlabel("Energie nimmt zu  →", fontsize=fs.TYPE.annot)
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:truncated_axis")
def _truncated_axis(asset: Asset, path: Path) -> None:
    """A bar chart with a TRUNCATED y-axis — intentionally misleading. Do NOT
    'fix' the axis: the task is to spot the manipulation (geschönte Kurve).
    spec (all optional, else the demo defaults): {categories, values, ymin, ymax,
    title, ylabel}. ymin defaults just below the smallest value (the zoom trick)."""
    s = asset.spec or {}
    cats = [str(c) for c in (s.get("categories") or ["2019", "2020", "2021", "2022"])]
    values = [float(v) for v in (s.get("values") or [101.0, 101.4, 101.9, 102.3])]
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(4.6, 3.0), layout="constrained")
        ax.bar(cats, values, color=fs.PALETTE.negative)      # negative role = the misleading twin
        lo = float(s["ymin"]) if "ymin" in s else min(values) - 0.5  # <-- the trick: zoomed axis
        hi = float(s["ymax"]) if "ymax" in s else max(values) + 0.2  # (NEVER "fixed" — the flaw IS
        ax.set_ylim(lo, hi)                                          #  the teaching point)
        ax.set_ylabel(s.get("ylabel") or "Index")
        ax.set_title(s.get("title") or "Dramatischer Anstieg?!")
        fig.savefig(path, dpi=150)
        plt.close(fig)


@_generator("matplotlib:honest_axis")
def _honest_axis(asset: Asset, path: Path) -> None:
    """The same data with a ZERO-based axis — the honest comparison. spec mirrors
    truncated_axis; ymin defaults to 0 (that is the whole point)."""
    s = asset.spec or {}
    cats = [str(c) for c in (s.get("categories") or ["2019", "2020", "2021", "2022"])]
    values = [float(v) for v in (s.get("values") or [101.0, 101.4, 101.9, 102.3])]
    with plt.rc_context(_HOUSE()):
        fig, ax = plt.subplots(figsize=(4.6, 3.0), layout="constrained")
        ax.bar(cats, values, color=fs.PALETTE.positive)      # positive role = the honest twin
        lo = float(s.get("ymin", 0))  # zero-based: the change is tiny
        ax.set_ylim(lo, float(s["ymax"]) if "ymax" in s else max(values) * 1.08)
        ax.set_ylabel(s.get("ylabel") or "Index")
        ax.set_title(s.get("title") or "Dieselben Daten, ehrliche Achse")
        fig.savefig(path, dpi=150)
        plt.close(fig)


# --- decorative kit (svg: backend) -------------------------------------------
# Decorative assets are CONTENT-FREE and reusable (the media-policy gate enforces
# that). SVG is the durable artifact (crisp, the SME asked for svg icons); we
# rasterise it to PNG via PyMuPDF for embedding. These are curated-only — an LLM
# generating a worksheet never requests decoration (not in GENERATION_RECIPES).
_SVG_HDR = '<svg xmlns="http://www.w3.org/2000/svg" '


def _svg_to_png(svg: str, path: Path, scale: float = 2.0) -> None:
    doc = fitz.open(stream=svg.encode("utf-8"), filetype="svg")
    doc[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=True).save(path)
    doc.close()


@_generator("svg:inline")
def _svg_inline(asset: Asset, path: Path) -> None:
    """Rasterise raw SVG markup (spec.svg) — for curated/stored decorative assets."""
    svg = (asset.spec or {}).get("svg", "")
    if not svg.strip():
        raise ValueError(f"asset {asset.id}: svg:inline needs spec.svg")
    _svg_to_png(svg, path)


@_generator("svg:badge")
def _svg_badge(asset: Asset, path: Path) -> None:
    """A round badge with a short label — a decorative subject/topic marker.
    spec: {label, color?, text_color?}."""
    s = asset.spec or {}
    label = html.escape(str(s.get("label", ""))[:3])
    color, txt = s.get("color", fs.SVG.ink), s.get("text_color", fs.SVG.paper)
    svg = (f'{_SVG_HDR}width="120" height="120" viewBox="0 0 120 120">'
           f'<circle cx="60" cy="60" r="54" fill="{color}"/>'
           f'<text x="60" y="78" font-size="44" font-family="sans-serif" '
           f'text-anchor="middle" fill="{txt}">{label}</text></svg>')
    _svg_to_png(svg, path)


@_generator("svg:banner")
def _svg_banner(asset: Asset, path: Path) -> None:
    """A decorative header band (dotted rule) — content-free framing. spec: {color?}."""
    color = (asset.spec or {}).get("color", fs.SVG.accent)
    dots = "".join(f'<circle cx="{12 + i * 24}" cy="12" r="4" fill="{color}"/>'
                   for i in range(28))
    svg = (f'{_SVG_HDR}width="680" height="24" viewBox="0 0 680 24">'
           f'<rect x="0" y="10" width="680" height="4" fill="{color}" opacity="0.35"/>'
           f'{dots}</svg>')
    _svg_to_png(svg, path)


@_generator("svg:motif")
def _svg_motif(asset: Asset, path: Path) -> None:
    """A geometric corner motif — content-free decoration. spec: {color?}."""
    color = (asset.spec or {}).get("color", fs.SVG.primary)
    tris = "".join(
        f'<polygon points="{x},120 {x + 20},120 {x},{100 - x // 3}" '
        f'fill="{color}" opacity="{0.25 + (x % 60) / 120:.2f}"/>'
        for x in range(0, 120, 20))
    svg = f'{_SVG_HDR}width="120" height="120" viewBox="0 0 120 120">{tris}</svg>'
    _svg_to_png(svg, path)


# --- diffusion: backend seam -------------------------------------------------
# The SME's image-gen agent plugs in here: register_diffusion_backend(fn) where
# fn(asset, path) writes a PNG for a decorative, content-free asset (the prompt
# rides in asset.spec). The media-policy gate guarantees only content-free
# decorative assets ever carry a diffusion id, so this can't smuggle in slop-as-
# content. Offline (no agent registered) it fails loudly rather than inventing one.
_DIFFUSION_BACKEND: Callable[[Asset, Path], None] | None = None


class DiffusionNotConfigured(RuntimeError):
    pass


def register_diffusion_backend(fn: Callable[[Asset, Path], None]) -> None:
    """Wire an image-gen pipeline as the `diffusion:` backend (Phase 4 #4)."""
    global _DIFFUSION_BACKEND
    _DIFFUSION_BACKEND = fn


def _diffusion_dispatch(asset: Asset, path: Path) -> None:
    if _DIFFUSION_BACKEND is None:
        raise DiffusionNotConfigured(
            f"asset {asset.id}: generator {asset.generator!r} needs a diffusion backend — "
            "register one via assets.register_diffusion_backend (the SME's image-gen agent)"
        )
    _DIFFUSION_BACKEND(asset, path)


# --- audio: backend seam (TTS for Hörverstehen) ------------------------------
# Modern FS is oral-heavy (Hören/Sprechen); a printable sheet can't carry spoken audio.
# The SME wires a TTS pipeline via register_audio_backend(fn) where fn(asset, path) writes
# an audio file for asset.spec {script, lang?, voice?}. TTS is legitimately machine-
# generatable for language (unlike music). Offline → AudioNotConfigured (no silent slop);
# the transcript is the always-present printable fallback, so a worksheet still works.
_AUDIO_BACKEND: Callable[[Asset, Path], None] | None = None


class AudioNotConfigured(RuntimeError):
    pass


def register_audio_backend(fn: Callable[[Asset, Path], None]) -> None:
    """Wire a TTS pipeline as the `audio:` backend (the SME's TTS engine)."""
    global _AUDIO_BACKEND
    _AUDIO_BACKEND = fn


def build_audio(asset: Asset, outdir: Path | None = None) -> Path:
    """Render an audio asset (audio:tts) to a file via the registered TTS backend and
    return its path. A separate path from build_asset — audio is not a PDF-embeddable
    image. Offline → AudioNotConfigured."""
    outdir = outdir or (RUNS_DIR / "audio")
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{asset.id}.mp3"
    if _AUDIO_BACKEND is None:
        raise AudioNotConfigured(
            f"asset {asset.id}: generator {asset.generator!r} needs a TTS backend — "
            "register one via assets.register_audio_backend (the SME's TTS engine)"
        )
    _AUDIO_BACKEND(asset, path)
    return path


# Recipes an LLM may REQUEST (parameterized, correct-by-construction). The bespoke
# figures (em_spectrum, truncated/honest axis), the decorative svg: kit, and the
# diffusion: backend are curated-only and NOT here — a generated worksheet may only
# ask for these safe, content-bearing, spec-driven recipes.
GENERATION_RECIPES: dict[str, str] = {
    "matplotlib:number_line":
        'Zahlenstrahl — spec {"min":num,"max":num,"step"?:num,"marks"?:[{"at":num,"label"?:str}]}',
    "matplotlib:bar_chart":
        'Balkendiagramm für einen MENGEN-Vergleich (nicht für eine Ja/Nein-Klassifikation!) — '
        'spec {"categories":[str],"values":[num],"title"?:str,"xlabel"?:str,"ylabel"?:str,"log"?:bool}. '
        'Kurze Kategorienamen; bei Werten über mehrere Größenordnungen "log":true setzen.',
    "matplotlib:line":
        'Liniendiagramm für einen TREND / Verlauf über die Zeit — spec {"categories":[str]|"x":[num],'
        '"values":[num] | "series":[{"label"?,"x":[...],"y":[...]}],"xlabel"?,"ylabel"?,"title"?,"log"?}',
    "matplotlib:scatter":
        'Streudiagramm für einen ZUSAMMENHANG zweier numerischer Größen — '
        'spec {"points":[[x,y]],"xlabel"?,"ylabel"?,"title"?,"fit"? (Trendgerade)}',
    "matplotlib:histogram":
        'Histogramm für die VERTEILUNG (Form) der Rohdaten einer numerischen Größe — '
        'spec {"values":[num],"bins"?,"xlabel"?,"ylabel"?,"title"?}',
    "matplotlib:boxplot":
        'Boxplot/Kastenschaubild — Fünf-Punkte-Zusammenfassung (Streuung) bzw. Vergleich von '
        'Verteilungen (WS). spec {"summary":{"min","q1","median","q3","max"}} ODER {"values":[num]} '
        'ODER {"groups":[{"label","summary"|"values"}]} (z. B. Datenliste A vs. B); '
        '"xlabel"?,"title"?,"vertical"? (Standard waagrecht).',
    "matplotlib:vector_addition":
        'Vektor-/Kräfteaddition (Pfeile maßstabsgetreu; Vektoren aneinandergehängt oder '
        'Kräfteparallelogramm) — spec {"vectors":[{"magnitude":num,"angle_deg":num '
        '(0° = nach rechts, gegen den Uhrzeigersinn)} ODER {"dx":num,"dy":num}, je "label"?:str],'
        '"method"?:"tip_to_tail"|"parallelogram" (nur bei genau 2 Vektoren),'
        '"show_resultant"?:bool,"show_value"?:bool (false → "F_R = ?" als Aufgabe),'
        '"unit"?:str (Standard "N"),"resultant_name"?:str,"title"?}. Die Resultierende wird '
        'aus der Komponentensumme BERECHNET — die Abbildung erfindet nichts und verrät mit '
        'show_value:false keine Lösung.',
    "matplotlib:force_diagram":
        'Kräfteplan (Freikörperbild): Körper mit Kraftpfeilen vom Mittelpunkt aus, Längen '
        'maßstabsgetreu — spec {"forces":[{"magnitude":num,"angle_deg":num (0° = nach rechts, '
        '90° = nach oben),"label"?:str (z. B. "F_G")}],"body_label"?:str,'
        '"show_magnitudes"?:bool,"show_resultant"?:bool,"show_value"?:bool (false → '
        '"F_res = ?"),"unit"?:str,"title"?}. Die resultierende Kraft wird BERECHNET '
        '(Komponentensumme; Kräftegleichgewicht → "F_res = 0 N").',
    "matplotlib:labeled_parts":
        'Beschriftungs-Abbildung ("Beschrifte die Teile"): schematischer Querschnitt/Aufbau '
        'aus einfachen Formen, Teile mit nummerierten Hinweislinien — spec {"shapes":'
        '[{"kind":"region"|"circle"|"polyline"|"line",…,"color"?:str}],"parts":[{"at":[x,y],'
        '"name":str,"side"?:"left"|"right"}],"show_names"?:bool (false → nummerierte Aufgabe '
        'zum Beschriften, true → beschriftete Lösung),"title"?}. Nummerierung, Hinweislinien '
        'und Lösungsnamen werden aus derselben Teile-Liste ABGELEITET — Schülerblatt und '
        'Lösung können nicht auseinanderlaufen. Die Formen sind schematisch (kein '
        'Datendiagramm).',
    "matplotlib:tree_diagram":
        'Baumdiagramm — mehrstufiger Zufallsversuch (WS). spec {"branches":[{"label","p"? (Astbeschriftung, '
        'z. B. "0,3"),"children"?:[{"label","p"?,"children"?…}]}],"title"?}. Astwahrscheinlichkeiten '
        'sind vorgegeben — die Abbildung erfindet keine Zahlen.',
    "matplotlib:function_graph":
        'Koordinatensystem/Gerade — spec {"xmin"?,"xmax"?,"m"?,"b"? (Gerade y=mx+b),'
        '"points"?:[[x,y]],"connect"? (Punkte zu einer Kurve verbinden, z. B. v-t-Diagramm),'
        '"xlabel"?,"ylabel"?,"ymin"?,"ymax"?,"title"?}',
    "matplotlib:math_formula":
        'Formel via LaTeX — spec {"latex":str}',
    "matplotlib:population_pyramid":
        'Bevölkerungspyramide (Alter × Geschlecht, gegenläufige Balken) — '
        'spec {"age_groups":[str],"male":[num],"female":[num],"title"?:str,"xlabel"?:str}. '
        'NUR mit echten, zitierten Daten verwenden (data_source auf einen Datensatz setzen).',
    "matplotlib:right_triangle":
        'Rechtwinkliges Dreieck (Pythagoras) — spec {"a":num,"b":num,"label_a"?,"label_b"?,'
        '"label_c"?,"title"?}. Beschriftungen sind Strings (z. B. "a = 3 cm", "c = ?") — '
        'die Abbildung darf die Lösung NICHT verraten.',
    "matplotlib:rectangle":
        'Rechteck mit Maßen — spec {"length":num,"width":num,"label_l"?,"label_w"?,"title"?}.',
    "matplotlib:polygon":
        'Vieleck (Dreieck/Viereck …) — spec {"points":[[x,y]],"vertex_labels"?:[str],'
        '"side_labels"?:[str],"title"?}.',
    "matplotlib:solid_net":
        'Körpernetz eines Quaders/Würfels — spec {"kind"?:"cuboid"|"cube",'
        '"a"?:num,"b"?:num,"c"?:num | "side"?:num,"label_a"?:str,"label_b"?:str,'
        '"label_c"?:str,"result_label"?:str,"title"?:str}. Die sechs Flächen und fünf '
        'Faltkanten werden geometrisch BERECHNET; Beschriftungen sind vorgegeben (z. B. '
        '"a = 3 cm", "O = ?"), damit die Abbildung keine Lösung verrät.',
    "matplotlib:circle":
        'Kreis mit Radius — spec {"radius":num,"label_r"?,"title"?}.',
    "matplotlib:coordinate_plane":
        'Koordinatensystem mit Punkten/Strecken — spec {"points":[{"x":num,"y":num,"label"?}],'
        '"segments"?:[[i,j]],"xmin"?,"xmax"?,"ymin"?,"ymax"?,"title"?}.',
    "matplotlib:triangle_construction":
        'Dreieckskonstruktion (merkwürdige Punkte) — spec {"vertices":[[x,y],[x,y],[x,y]],'
        '"stage"?:1–6,"title"?}. stage 1 Dreieck · 2 Umkreis · 3 Inkreis · 4 Schwerpunkt · '
        '5 Höhenschnittpunkt · 6 Eulergerade+Feuerbachkreis. Mittelpunkte, Kreise und Winkel '
        'werden aus den Eckpunkten BERECHNET — die Abbildung erfindet nichts.',
    "matplotlib:axonometric_solid":
        'Körper im Schrägriss (Kabinettprojektion, GZ/DG) — spec {"kind":"quader"|"prism"|'
        '"pyramid"|"cylinder"|"cone","a"?,"b"?,"c"? (Quader) | "n"?,"r"?,"h"? (Prisma/Pyramide/'
        'Zylinder/Kegel),"labels"?:{"a"|"b"|"c"|"r"|"h":str},"show_measures"?:bool (false → '
        '"h = ?" als Aufgabe),"title"?}. Verdeckte Kanten werden BERECHNET (strichliert), Maße sind '
        'maskierbar — die Abbildung erfindet keine verdeckte Kante und verrät kein Maß.',
    "matplotlib:riss_pair":
        'Grund- und Aufriss eines Körpers (zugeordnete Normalrisse, GZ/DG) — spec {"kind":… (wie '
        'axonometric_solid),Maße,"ordnungslinien"?:bool (Standard true),"title"?}. Grundriss unten, '
        'Aufriss oben, gemeinsame Rissachse und Ordnungslinien; beide Risse im selben Maßstab '
        '(die x-Zuordnung ist exakt), aus der Körpergeometrie berechnet.',
    "matplotlib:function_plot":
        'Funktionsgraph y = f(x) (BELIEBIGE Funktion via Term) — spec {"expr":str (z. B. '
        '"0.25*x**2-1" oder "sin(x)"),"xmin"?,"xmax"?,"ymin"?,"ymax"?,"label"?,"title"?}.',
    "matplotlib:integral_area":
        'Fläche unter der Kurve (bestimmtes Integral) — spec {"expr":str,"a":num,"b":num,'
        '"xmin"?,"xmax"?,"show_value"?:bool (false → "A = ?" als Aufgabe),"title"?}. '
        'Der Flächenwert wird aus dem Term BERECHNET (sympy), nicht erfunden.',
    "matplotlib:tangent":
        'Tangente an f in x0 (Ableitung als Steigung) — spec {"expr":str,"x0":num,"xmin"?,'
        '"xmax"?,"show_slope"?:bool (false → "k = ?"),"slope_triangle"?:bool,"title"?}. '
        'Die Steigung k = f\'(x0) wird BERECHNET (sympy).',
    "matplotlib:riemann_sum":
        'Rechteck-Näherung des Integrals (Ober-/Untersumme) — spec {"expr":str,"a":num,"b":num,'
        '"n"?:int,"mode"?:"left"|"right"|"mid","title"?}. Summe UND exakter Wert berechnet.',
    "matplotlib:extrema":
        'Extremstellen (Hoch-/Tiefpunkt) mit waagrechten Tangenten — spec {"expr":str,"xmin"?,'
        '"xmax"?,"title"?}. Aus f\'(x)=0 berechnet und mit f\'\'(x) klassifiziert.',
    "matplotlib:area_between":
        'Fläche zwischen zwei Kurven — spec {"expr":str,"expr2":str,"a"?:num,"b"?:num '
        '(Standard: äußere Schnittpunkte),"show_value"?:bool,"title"?}. A = ∫|f−g| berechnet.',
    "matplotlib:distribution":
        'Normalverteilung N(μ,σ) mit schraffierter Wahrscheinlichkeit (WS) — spec {"mu"?:num,'
        '"sigma"?:num,"a"?:num,"b"?:num,"mode"?:"between"|"le"|"ge","show_value"?:bool,"title"?}. '
        'Fläche = Wahrscheinlichkeit, berechnet.',
    "matplotlib:optics_ray":
        'Bildkonstruktion an einer dünnen Linse (Physik) — spec {"kind":"sammellinse"|'
        '"zerstreuungslinse","f":num,"g":num,"G":num,"stage"?:1–6,"show_value"?:bool (false → '
        'NUR die gesuchten Bildgrößen maskiert: "b = ?","B = ?","B′ = ?" — die Angaben g/G '
        'bleiben sichtbar),"title"?}. f/g/G sind positive Beträge; das Bild (Bildweite b, '
        'Bildgröße B) wird aus der Abbildungsgleichung 1/f = 1/g + 1/b BERECHNET (sympy). '
        'stage 1 Achse+Linse+Gegenstand+Brennpunkte · 2 Parallelstrahl · 3 Mittelpunktstrahl · '
        '4 Brennpunktstrahl · 5 Bildpfeil · 6 Maße.',
    "matplotlib:circuit":
        'Stromkreis-Schaltbild aus einer Netzliste (Physik) — spec {"net":{Baum aus '
        '{"type":"series"|"parallel","children":[…]} und Blättern {"type":"resistor"|"lamp",'
        '"ohm":num,"label":str}},"volt"?:num,"mask"?:[str] (maskiert GENAU diese Werte — '
        'Element-Labels bzw. "U"/"I"/"Rers", z. B. ["R₂","Rers"]; die Angaben bleiben sichtbar '
        '— die kanonische Aufgabe „gegeben U, R₁, R₃, I — berechne R₂"),"show_value"?:bool '
        '(false ohne mask → ALLES maskiert),"ask"?:str (Fokus, z. B. "R₂"/"U"/"I"),"title"?}. '
        'Ersatzwiderstand, Ströme und Spannungen werden nach Kirchhoff BERECHNET (sympy, exakt) '
        '— nichts erfunden.',
    "matplotlib:timeline":
        'Zeitleiste (chronologische Ereignisse, GPB) — '
        'spec {"events":[{"at":num,"label":str}],"title"?:str,"xlabel"?:str}.',
    "matplotlib:climate_diagram":
        'Klimadiagramm (Monats-Temperatur als Linie + Niederschlag als Balken, zwei Achsen) — '
        'spec {"months"?:[12 str],"temp":[12 num],"precip":[12 num],"title"?:str}. '
        'Echte Klimadaten zitieren (data_source), sonst illustrative=true.',
}


def build_asset(asset: Asset, outdir: Path | None = None) -> Path:
    """Render an asset to a PNG and return its path. Dispatches on the generator id;
    a `diffusion:`/`svg:` backend plugs in by registering builders.

    Guard: an intentionally_flawed asset must route to a builder that preserves the
    flaw; we never substitute a 'corrected' generator.
    """
    outdir = outdir or _outdir()
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{asset.id}.png"
    builder = _GENERATORS.get(asset.generator or "")
    if builder is None and (asset.generator or "").startswith("diffusion:"):
        builder = _diffusion_dispatch  # open recipe space → the registered backend
    if builder is None:
        raise ValueError(
            f"no code generator for asset '{asset.id}' (generator={asset.generator!r}); "
            "content-bearing assets must be code-generated"
        )
    if asset.intentionally_flawed and asset.generator == "matplotlib:em_spectrum":
        # defensive: the correct generator must never be used for a flawed asset
        raise ValueError(f"asset {asset.id} marked intentionally_flawed but uses a correct generator")
    builder(asset, path)
    return path
