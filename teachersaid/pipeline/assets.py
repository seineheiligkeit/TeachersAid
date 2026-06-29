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
from matplotlib.patches import Circle, Polygon  # noqa: E402

from ..config import RUNS_DIR  # noqa: E402
from ..schema.assets import Asset  # noqa: E402

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
    fig, ax = plt.subplots(figsize=(7.4, 2.0 if has_labels else 1.1))
    ax.axhline(0, color="#33506e", lw=1.4, zorder=1)
    t = lo
    while t <= hi + 1e-9:
        ax.plot([t, t], [-0.07, 0.07], color="#33506e", lw=1)
        ax.text(t, -0.22, f"{t:g}", ha="center", va="top", fontsize=9)
        t += step
    levels = (0.18, 0.40, 0.62)                    # cycle 3 heights so clustered labels never collide
    for i, m in enumerate(marks):
        at = float(m["at"])
        ax.plot([at], [0], "o", color="#b03a2e", ms=9, zorder=3)
        if m.get("label"):
            y = levels[i % len(levels)]
            ax.plot([at, at], [0.07, y - 0.04], color="#b03a2e", lw=0.6, zorder=2)
            ax.text(at, y, str(m["label"]), ha="center", va="bottom",
                    color="#b03a2e", fontsize=8.5)
    ax.set_xlim(lo - step * 0.6, hi + step * 0.6)
    ax.set_ylim(-0.5, 0.95 if has_labels else 0.5)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _bar_value_labels(ax, vals, *, horizontal: bool) -> None:
    """Annotate every bar with its value, so even a tiny bar is readable."""
    for i, v in enumerate(vals):
        txt = f"{v:g}"
        if horizontal:
            ax.text(v, i, " " + txt, va="center", ha="left", fontsize=8, color="#33506e")
        else:
            ax.annotate(txt, (i, v), textcoords="offset points", xytext=(0, 2),
                        ha="center", va="bottom", fontsize=8, color="#33506e")


@_generator("matplotlib:bar_chart")
def _bar_chart(asset: Asset, path: Path) -> None:
    """A bar chart. spec: {categories, values, title?, xlabel?, ylabel?, log?, horizontal?}.

    Legibility is part of correctness: long/many labels auto-switch to horizontal bars
    (full-width labels, no overlap); every bar is value-labelled (no 'invisible' bar);
    `log` gives a log value-axis for orders-of-magnitude ranges; the title wraps and
    constrained_layout keeps title/axis labels from colliding."""
    s = asset.spec or {}
    cats = [str(c).replace("\n", " ") for c in s.get("categories", [])]
    vals = [float(v) for v in s.get("values", [])]
    n = max(len(cats), 1)
    log = bool(s.get("log"))
    horizontal = bool(s.get("horizontal")) or any(len(c) > 10 for c in cats) or n > 6

    if horizontal:
        fig, ax = plt.subplots(figsize=(6.8, max(2.4, 0.5 * n + 1.1)), layout="constrained")
        ax.barh(range(n), vals, color="#4f6f8f", edgecolor="#33506e")
        ax.set_yticks(range(n))
        ax.set_yticklabels(cats)
        ax.invert_yaxis()
        if log:
            ax.set_xscale("log")
        if s.get("ylabel"):
            ax.set_xlabel(s["ylabel"])      # the value axis is horizontal now
        ax.margins(x=0.12)                  # room for the value labels
        _bar_value_labels(ax, vals, horizontal=True)
    else:
        fig, ax = plt.subplots(figsize=(max(4.0, 0.95 * n + 1.5), 3.3), layout="constrained")
        ax.bar(range(n), vals, color="#4f6f8f", edgecolor="#33506e")
        ax.set_xticks(range(n))
        ax.set_xticklabels(cats)
        if log:
            ax.set_yscale("log")
        if s.get("ylabel"):
            ax.set_ylabel(s["ylabel"])
        if s.get("xlabel"):
            ax.set_xlabel(s["xlabel"])
        ax.margins(y=0.12)
        _bar_value_labels(ax, vals, horizontal=False)
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
    fig, ax = plt.subplots(figsize=(6.8, max(3.0, 0.42 * n + 1.0)), layout="constrained")
    ax.barh(y, [-v for v in male], color="#4f6f8f", edgecolor="#33506e",
            label=s.get("male_label", "Männer"))
    ax.barh(y, female, color="#b06b4f", edgecolor="#8a4a33",
            label=s.get("female_label", "Frauen"))
    ax.axvline(0, color="#33506e", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(groups)
    ax.set_ylabel(s.get("ylabel") or "Altersgruppe")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6, symmetric=True))
    ax.xaxis.set_major_formatter(  # both wings show positive counts, German grouping
        FuncFormatter(lambda x, _: f"{abs(x):,.0f}".replace(",", ".")))
    ax.set_xlabel(s.get("xlabel") or "Personen")
    ax.margins(y=0.01)
    ax.legend(loc="lower right", fontsize=8)
    if s.get("title"):
        ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 52)))
    fig.savefig(path, dpi=150)
    plt.close(fig)


@_generator("matplotlib:timeline")
def _timeline(asset: Asset, path: Path) -> None:
    """A horizontal timeline — chronological events on a time axis (GPB history). spec:
    {events:[{"at":num,"label":str}]} or {categories:[label],"values":[year]}; title?,
    xlabel?. Event labels stagger above/below the line with stems so they don't collide."""
    s = asset.spec or {}
    events = s.get("events")
    if not events:
        events = [{"at": v, "label": c}
                  for c, v in zip(s.get("categories", []), s.get("values", []))]
    events = sorted(events, key=lambda e: float(e["at"]))
    xs = [float(e["at"]) for e in events]
    labels = ["\n".join(textwrap.wrap(str(e.get("label", "")), 18)) for e in events]
    fig, ax = plt.subplots(figsize=(7.6, 3.0), layout="constrained")
    ax.axhline(0, color="#33506e", lw=1.6, zorder=1)
    if xs:
        span = (max(xs) - min(xs)) or 1.0
        ax.set_xlim(min(xs) - span * 0.08, max(xs) + span * 0.08)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{x:g}" for x in xs], fontsize=8)
    for i, (x, lab) in enumerate(zip(xs, labels)):
        y = 0.62 if i % 2 == 0 else -0.62
        ax.plot([x], [0], "o", color="#b03a2e", ms=8, zorder=3)
        ax.plot([x, x], [0, y * 0.78], color="#b03a2e", lw=0.7, zorder=2)
        ax.annotate(lab, (x, y), ha="center", va="bottom" if y > 0 else "top",
                    fontsize=8.5, color="#33506e")
    ax.set_ylim(-1.25, 1.25)
    ax.set_yticks([])
    for sp in ("left", "right", "top"):
        ax.spines[sp].set_visible(False)
    if s.get("xlabel"):
        ax.set_xlabel(s["xlabel"])
    if s.get("title"):
        ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 52)))
    fig.savefig(path, dpi=150)
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
    fig, ax1 = plt.subplots(figsize=(6.6, 3.8), layout="constrained")
    ax2 = ax1.twinx()
    ax2.bar(range(n), precip, color="#6f9fc8", edgecolor="#33506e", width=0.7, zorder=1)
    ax1.plot(range(n), temp, "-o", color="#b03a2e", lw=2, ms=4, zorder=3)
    ax1.set_zorder(ax2.get_zorder() + 1)   # draw the temperature line above the bars
    ax1.patch.set_visible(False)
    ax1.set_xticks(range(n))
    ax1.set_xticklabels(months, fontsize=8)
    ax1.set_ylabel("Temperatur (°C)", color="#b03a2e")
    ax2.set_ylabel("Niederschlag (mm)", color="#33506e")
    ax1.tick_params(axis="y", labelcolor="#b03a2e")
    ax2.tick_params(axis="y", labelcolor="#33506e")
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
    axis (clean auto-ticks); true categorical x plots over an index, thinned to ~12 ticks
    and a marker only when sparse so a long dense series (e.g. 65 yearly points) stays legible."""
    s = asset.spec or {}
    series = s.get("series") or [{"x": s.get("x") or s.get("categories"),
                                  "y": s.get("y") or s.get("values")}]
    fig, ax = plt.subplots(figsize=(6.2, 3.7), layout="constrained")
    cat_labels = None
    for ser in series:
        y = [float(v) for v in (ser.get("y") or [])]
        x = ser.get("x")
        marker = "-o" if len(y) <= 24 else "-"          # no dot-soup on long series
        if x and any(isinstance(v, str) for v in x) and not _all_numeric(x):
            cat_labels = [str(v) for v in x]            # true categorical → index + ticklabels
            ax.plot(range(len(y)), y, marker, lw=2, ms=5, label=ser.get("label"))
        else:                                            # numeric x (years, quantities) → numeric axis
            xs = [float(v) for v in (x or range(len(y)))]
            ax.plot(xs, y, marker, lw=2, ms=5, label=ser.get("label"))
    if cat_labels is not None:
        n = len(cat_labels)
        step = max(1, n // 12)                           # thin to ~12 ticks (no overlap smear)
        idx = list(range(0, n, step))
        rot = 30 if any(len(c) > 6 for c in cat_labels) else 0
        ax.set_xticks(idx)
        ax.set_xticklabels([cat_labels[i] for i in idx], rotation=rot,
                           ha="right" if rot else "center")
    if s.get("log"):
        ax.set_yscale("log")
    ax.grid(True, color="#e9e9e9", lw=0.6)
    if s.get("xlabel") or s.get("x_label"):
        ax.set_xlabel(s.get("xlabel") or s.get("x_label"))
    if s.get("ylabel") or s.get("y_label"):
        ax.set_ylabel(s.get("ylabel") or s.get("y_label"))
    if len(series) > 1 and any(ser.get("label") for ser in series):
        ax.legend(fontsize=8)
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
    fig, ax = plt.subplots(figsize=(5.4, 4.0), layout="constrained")
    ax.scatter(xs, ys, color="#33506e", s=38, zorder=3)
    if s.get("fit") and len(xs) >= 2:
        import numpy as np
        m, b = np.polyfit(xs, ys, 1)
        xr = [min(xs), max(xs)]
        ax.plot(xr, [m * x + b for x in xr], color="#b03a2e", lw=1.5, zorder=2)
    ax.grid(True, color="#e9e9e9", lw=0.6)
    if s.get("xlabel") or s.get("x_label"):
        ax.set_xlabel(s.get("xlabel") or s.get("x_label"))
    if s.get("ylabel") or s.get("y_label"):
        ax.set_ylabel(s.get("ylabel") or s.get("y_label"))
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
    fig, ax = plt.subplots(figsize=(5.6, 3.6), layout="constrained")
    ax.hist(vals, bins=int(s.get("bins", 8)), color="#4f6f8f", edgecolor="#33506e")
    if s.get("xlabel") or s.get("x_label"):
        ax.set_xlabel(s.get("xlabel") or s.get("x_label"))
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
    fig, ax = plt.subplots(figsize=(5.6, 0.9 + 0.7 * len(stats)) if horizontal
                           else (1.2 + 1.0 * len(stats), 3.8), layout="constrained")
    ax.bxp(stats, orientation="horizontal" if horizontal else "vertical",
           showfliers=False, patch_artist=True,
           boxprops={"facecolor": "#cfe0ee", "edgecolor": "#33506e"},
           medianprops={"color": "#b03a2e", "linewidth": 2},
           whiskerprops={"color": "#33506e"}, capprops={"color": "#33506e"})
    (ax.set_xlabel if horizontal else ax.set_ylabel)(s.get("xlabel") or s.get("x_label") or "")
    (ax.grid)(True, axis="x" if horizontal else "y", color="#e6e6e6", lw=0.6)
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
    fig, ax = plt.subplots(figsize=(4.6, 4.2), layout="constrained")
    ax.axhline(0, color="#999", lw=0.8)
    ax.axvline(0, color="#999", lw=0.8)
    ax.grid(True, color="#e6e6e6", lw=0.6)
    if "m" in s:
        m, b = float(s["m"]), float(s.get("b", 0))
        ax.plot([xmin, xmax], [m * xmin + b, m * xmax + b], color="#b03a2e", lw=2)
    pts = s.get("points", [])
    if s.get("connect") and len(pts) >= 2:  # join points into a curve (e.g. a v-t graph)
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-o", color="#33506e", lw=2, ms=6)
    else:
        for p in pts:
            ax.plot([p[0]], [p[1]], "o", color="#33506e", ms=6)
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
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${s.get('latex', '')}$", fontsize=20)
    fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.15, transparent=True)
    plt.close(fig)


@_generator("matplotlib:tree_diagram")
def _tree_diagram(asset: Asset, path: Path) -> None:
    """A probability tree (Baumdiagramm) — a multi-stage Zufallsversuch, a WS-strand staple.
    Structural (declared on body.assets, like geometry), correct-by-construction: branch
    probabilities + outcome labels are spec-provided so the figure never invents them.
    spec: {branches:[{label, p?, children?:[{label, p?, children?…}]}], title?}; p renders as
    the edge label (e.g. "0,3"). Any depth; parents sit at the mean of their children."""
    s = asset.spec or {}
    roots = s.get("branches", []) or []
    fig, ax = plt.subplots(figsize=(6.0, 3.8), layout="constrained")
    ax.axis("off")
    leaf = [0.0]
    max_depth = [1]

    def place(node: dict, depth: int) -> float:
        max_depth[0] = max(max_depth[0], depth)
        kids = node.get("children") or []
        if kids:
            y = sum(place(k, depth + 1) for k in kids) / len(kids)
        else:
            y = leaf[0]
            leaf[0] += 1
        node["_xy"] = (depth, y)
        return y

    for r in roots:
        place(r, 1)
    root_y = sum(r["_xy"][1] for r in roots) / len(roots) if roots else 0
    root_xy = (0.0, root_y)

    def draw(node: dict, parent_xy: tuple) -> None:
        x, y = node["_xy"]
        ax.plot([parent_xy[0], x], [parent_xy[1], y], color="#33506e", lw=1.3, zorder=1)
        if node.get("p") not in (None, ""):
            mx, my = (parent_xy[0] + x) / 2, (parent_xy[1] + y) / 2
            ax.text(mx, my, str(node["p"]), fontsize=9, color="#b03a2e",
                    ha="center", va="center",
                    bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none"})
        ax.plot([x], [y], "o", color="#33506e", ms=5, zorder=2)
        ax.text(x + 0.06, y, str(node.get("label", "")), fontsize=10, va="center")
        for k in node.get("children") or []:
            draw(k, (x, y))

    if roots:
        ax.plot([root_xy[0]], [root_xy[1]], "o", color="#33506e", ms=5, zorder=2)
    for r in roots:
        draw(r, root_xy)
    ax.set_xlim(-0.3, max_depth[0] + 0.9)
    ax.set_ylim(-0.6, max(leaf[0], 1) - 0.4)
    if s.get("title"):
        ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 50)))
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
    (e.g. "a = 3 cm" or "c = ?") so the figure shows the task, not the answer."""
    s = asset.spec or {}
    a, b = float(s.get("a", 4)), float(s.get("b", 3))
    fig, ax = _geo_fig(4.2, 3.6)
    ax.add_patch(Polygon([(0, 0), (a, 0), (0, b)], closed=True,
                         facecolor="#dce6f2", edgecolor="#33506e", lw=1.8))
    m = min(a, b) * 0.13                                   # right-angle square at the origin
    ax.plot([m, m, 0], [0, m, m], color="#33506e", lw=1)
    ax.text(a / 2, -0.07 * b, str(s.get("label_a", "a")), ha="center", va="top", fontsize=11)
    ax.text(-0.03 * a, b / 2, str(s.get("label_b", "b")), ha="right", va="center", fontsize=11)
    ax.text(a / 2 + 0.03 * a, b / 2 + 0.03 * b, str(s.get("label_c", "c")),
            ha="left", va="bottom", fontsize=11, color="#b03a2e")
    ax.set_xlim(-0.2 * a, a * 1.12)
    ax.set_ylim(-0.2 * b, b * 1.12)
    _geo_title(ax, s)
    fig.savefig(path, dpi=150)
    plt.close(fig)


@_generator("matplotlib:rectangle")
def _rectangle_fig(asset: Asset, path: Path) -> None:
    """A labeled rectangle. spec: {length, width, label_l?, label_w?, title?}."""
    s = asset.spec or {}
    le, w = float(s.get("length", 6)), float(s.get("width", 4))
    fig, ax = _geo_fig(4.8, 3.4)
    ax.add_patch(Polygon([(0, 0), (le, 0), (le, w), (0, w)], closed=True,
                         facecolor="#dce6f2", edgecolor="#33506e", lw=1.8))
    ax.text(le / 2, -0.09 * w, str(s.get("label_l", f"{le:g}")), ha="center", va="top", fontsize=11)
    ax.text(-0.02 * le, w / 2, str(s.get("label_w", f"{w:g}")), ha="right", va="center", fontsize=11)
    ax.set_xlim(-0.22 * le, le * 1.08)
    ax.set_ylim(-0.28 * w, w * 1.12)
    _geo_title(ax, s)
    fig.savefig(path, dpi=150)
    plt.close(fig)


@_generator("matplotlib:polygon")
def _polygon(asset: Asset, path: Path) -> None:
    """A general labeled polygon (triangles, quadrilaterals, Vielecke). spec:
    {points:[[x,y],…], vertex_labels?:[str], side_labels?:[str], title?}."""
    s = asset.spec or {}
    pts = [(float(x), float(y)) for x, y in s.get("points", [(0, 0), (4, 0), (2, 3)])]
    fig, ax = _geo_fig()
    ax.add_patch(Polygon(pts, closed=True, facecolor="#dce6f2", edgecolor="#33506e", lw=1.8))
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    span = max(max(p[0] for p in pts) - min(p[0] for p in pts),
               max(p[1] for p in pts) - min(p[1] for p in pts)) or 1.0
    for i, (x, y) in enumerate(pts):
        ax.plot([x], [y], "o", color="#33506e", ms=4)
        vl = s.get("vertex_labels") or []
        if i < len(vl):                                    # label outward from the centroid
            dx, dy = x - cx, y - cy
            n = (dx * dx + dy * dy) ** 0.5 or 1
            ax.text(x + 0.12 * span * dx / n, y + 0.12 * span * dy / n, str(vl[i]),
                    ha="center", va="center", fontsize=11)
    for i, lab in enumerate(s.get("side_labels") or []):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, str(lab), ha="center", va="center",
                fontsize=10, color="#b03a2e",
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))
    ax.autoscale_view()
    ax.margins(0.18)
    _geo_title(ax, s)
    fig.savefig(path, dpi=150)
    plt.close(fig)


@_generator("matplotlib:circle")
def _circle(asset: Asset, path: Path) -> None:
    """A circle with centre + radius. spec: {radius, label_r?, title?}."""
    s = asset.spec or {}
    r = float(s.get("radius", 3))
    fig, ax = _geo_fig(4.0, 4.0)
    ax.add_patch(Circle((0, 0), r, facecolor="#dce6f2", edgecolor="#33506e", lw=1.8))
    ax.plot([0], [0], "o", color="#33506e", ms=4)
    ax.plot([0, r], [0, 0], color="#b03a2e", lw=1.4)       # radius
    ax.text(r / 2, 0.05 * r, str(s.get("label_r", f"r = {r:g}")), ha="center", va="bottom",
            fontsize=11, color="#b03a2e")
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
    fig, ax = plt.subplots(figsize=(4.6, 4.4), layout="constrained")
    ax.set_xlim(xmin - 0.5, xmax + 0.5)
    ax.set_ylim(ymin - 0.5, ymax + 0.5)
    ax.set_xticks(range(xmin, xmax + 1))
    ax.set_yticks(range(ymin, ymax + 1))
    ax.grid(True, color="#e2e2e2", lw=0.6)
    ax.set_aspect("equal")
    ax.axhline(0, color="#888", lw=1.0)
    ax.axvline(0, color="#888", lw=1.0)
    for i, j in s.get("segments", []):
        ax.plot([pts[i]["x"], pts[j]["x"]], [pts[i]["y"], pts[j]["y"]], color="#33506e", lw=1.8)
    for p in pts:
        ax.plot([p["x"]], [p["y"]], "o", color="#b03a2e", ms=6)
        if p.get("label"):
            ax.text(p["x"] + 0.15, p["y"] + 0.15, str(p["label"]), fontsize=9.5, color="#b03a2e")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if s.get("title"):
        ax.set_title("\n".join(textwrap.wrap(str(s["title"]), 46)))
    fig.savefig(path, dpi=150)
    plt.close(fig)


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
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    xs = range(len(bands))
    ax.bar(xs, [1] * len(bands), color="#dce6f2", edgecolor="#33506e")
    for x, lab in zip(xs, labels):
        ax.text(x, 0.5, lab, ha="center", va="center", fontsize=9)
    thr = 4.5  # ionizing threshold between UV and Röntgen
    ax.axvline(thr, color="#b03a2e", linestyle="--", linewidth=1.5)
    ax.text(thr + 0.05, 1.05, "ionisierend →", color="#b03a2e", fontsize=8, va="bottom")
    ax.text(thr - 0.05, 1.05, "← nicht-ionisierend", color="#2e6b3a", fontsize=8,
            va="bottom", ha="right")
    ax.set_xlim(-0.6, len(bands) - 0.4)
    ax.set_ylim(0, 1.3)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlabel("Energie nimmt zu  →", fontsize=9)
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
    fig, ax = plt.subplots(figsize=(4.6, 3.0), layout="constrained")
    ax.bar(cats, values, color="#c0504d")
    lo = float(s["ymin"]) if "ymin" in s else min(values) - 0.5  # <-- the trick: zoomed axis
    hi = float(s["ymax"]) if "ymax" in s else max(values) + 0.2
    ax.set_ylim(lo, hi)
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
    fig, ax = plt.subplots(figsize=(4.6, 3.0), layout="constrained")
    ax.bar(cats, values, color="#4f6f52")
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
    color, txt = s.get("color", "#33506e"), s.get("text_color", "#ffffff")
    svg = (f'{_SVG_HDR}width="120" height="120" viewBox="0 0 120 120">'
           f'<circle cx="60" cy="60" r="54" fill="{color}"/>'
           f'<text x="60" y="78" font-size="44" font-family="sans-serif" '
           f'text-anchor="middle" fill="{txt}">{label}</text></svg>')
    _svg_to_png(svg, path)


@_generator("svg:banner")
def _svg_banner(asset: Asset, path: Path) -> None:
    """A decorative header band (dotted rule) — content-free framing. spec: {color?}."""
    color = (asset.spec or {}).get("color", "#b5651d")
    dots = "".join(f'<circle cx="{12 + i * 24}" cy="12" r="4" fill="{color}"/>'
                   for i in range(28))
    svg = (f'{_SVG_HDR}width="680" height="24" viewBox="0 0 680 24">'
           f'<rect x="0" y="10" width="680" height="4" fill="{color}" opacity="0.35"/>'
           f'{dots}</svg>')
    _svg_to_png(svg, path)


@_generator("svg:motif")
def _svg_motif(asset: Asset, path: Path) -> None:
    """A geometric corner motif — content-free decoration. spec: {color?}."""
    color = (asset.spec or {}).get("color", "#4f6f8f")
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
    "matplotlib:circle":
        'Kreis mit Radius — spec {"radius":num,"label_r"?,"title"?}.',
    "matplotlib:coordinate_plane":
        'Koordinatensystem mit Punkten/Strecken — spec {"points":[{"x":num,"y":num,"label"?}],'
        '"segments"?:[[i,j]],"xmin"?,"xmax"?,"ymin"?,"ymax"?,"title"?}.',
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
