"""Render the figure-styleguide SPECIMEN — a one-page visual reference of the house style.

This is the artifact you look at and tune. It draws representative figure types *in the
proposed style* (consuming `pipeline.figstyle`) WITHOUT touching the production recipes in
`pipeline/assets.py` — so we can settle the look cheaply before porting the ~25 recipes.

It also previews one *composed* scene (area-under-curve + tangent) to show where the
composability work is heading — several annotated primitives on one coordinate canvas.

    python -m tools.style_specimen        # -> runs/style_specimen.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402


def _accent_tab(ax, subject: str) -> None:
    """A short accent rule above a panel — previews the per-subject theming hook (the accent
    rides on top of the constant semantic roles)."""
    ax.plot([0.0, 0.10], [1.045, 1.045], transform=ax.transAxes,
            color=fs.subject_accent(subject), lw=3.2, clip_on=False, solid_capstyle="butt")


def _title(ax, text: str, subject: str) -> None:
    ax.set_title(text, loc="left", pad=10)
    _accent_tab(ax, subject)


# --- palette band ------------------------------------------------------------
def panel_palette(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    roles = [("ink", fs.PALETTE.ink), ("primary", fs.PALETTE.primary),
             ("focus", fs.PALETTE.focus), ("positive", fs.PALETTE.positive),
             ("negative", fs.PALETTE.negative), ("muted", fs.PALETTE.muted),
             ("surface", fs.PALETTE.surface), ("grid", fs.PALETTE.grid)]
    n = len(roles)
    w = 1.0 / n
    for i, (name, col) in enumerate(roles):
        x = i * w
        ax.add_patch(Rectangle((x + 0.01, 0.45), w - 0.02, 0.5, facecolor=col,
                               edgecolor=fs.PALETTE.muted, lw=0.5))
        ax.text(x + w / 2, 0.30, name, ha="center", va="top", fontsize=fs.TYPE.tick,
                color=fs.PALETTE.ink)
    # the categorical ramp as a thin strip
    m = len(fs.CATEGORICAL)
    for i, col in enumerate(fs.CATEGORICAL):
        ax.add_patch(Rectangle((i / m, 0.06), 1 / m - 0.004, 0.12, facecolor=col, edgecolor="none"))
    ax.text(0.0, 0.0, "categorical ramp (mehrere Reihen)", ha="left", va="top",
            fontsize=fs.TYPE.caption, color=fs.PALETTE.muted)


# --- representative figure types in the house style --------------------------
def panel_bar(ax) -> None:
    cats = ["Wien", "NÖ", "OÖ", "Steierm.", "Tirol"]
    vals = [2.0, 1.7, 1.5, 1.25, 0.77]
    fs.style_axes(ax, frame="lb", grid_axis="y")
    ax.bar(range(len(cats)), vals, color=fs.PALETTE.primary, edgecolor=fs.darken(fs.PALETTE.primary, .2))
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(cats)
    ax.margins(y=0.14)
    for i, v in enumerate(vals):
        ax.annotate(f"{v:g}", (i, v), textcoords="offset points", xytext=(0, 3),
                    ha="center", va="bottom", fontsize=fs.TYPE.annot, color=fs.PALETTE.muted)
    ax.set_ylabel("Mio. Einw.")
    _title(ax, "Balkendiagramm", "Geographie")


def panel_line(ax) -> None:
    years = list(range(2017, 2025))
    series = {"Modell A": [3, 4, 5, 6, 8, 9, 11, 13],
              "Modell B": [5, 5, 6, 6, 7, 7, 8, 9],
              "Modell C": [9, 8, 8, 7, 6, 6, 5, 4]}
    fs.style_axes(ax, frame="lb")
    for label, ys in series.items():               # no explicit colour -> the ramp (prop_cycle)
        ax.plot(years, ys, "-o", lw=fs.STROKE.curve, ms=fs.STROKE.marker_sm, label=label)
    ax.legend()
    ax.set_ylabel("Wert")
    _title(ax, "Liniendiagramm · mehrere Reihen", "Physik")


def panel_scatter(ax) -> None:
    pts = [(1, 2.1), (2, 2.0), (3, 3.2), (4, 3.0), (5, 4.4), (6, 4.1), (7, 5.6), (8, 6.0)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    fs.style_axes(ax, frame="lb")
    ax.scatter(xs, ys, color=fs.PALETTE.primary, s=42, zorder=3)
    # least-squares fit, drawn in focus (the relationship is the point of interest)
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    ax.plot([min(xs), max(xs)], [a + b * min(xs), a + b * max(xs)],
            color=fs.PALETTE.focus, lw=1.6, zorder=2)
    _title(ax, "Streudiagramm + Trend", "Mathematik")


def panel_triangle(ax) -> None:
    a, b = 4.0, 3.0
    fs.style_axes(ax, frame="off")
    ax.set_aspect("equal")
    ax.add_patch(Polygon([(0, 0), (a, 0), (0, b)], closed=True,
                         facecolor=fs.PALETTE.surface, edgecolor=fs.PALETTE.ink, lw=1.8))
    m = 0.42
    ax.plot([m, m, 0], [0, m, m], color=fs.PALETTE.ink, lw=1)        # right-angle mark
    ax.text(a / 2, -0.25, "a = 4 cm", ha="center", va="top", fontsize=fs.TYPE.annot_lg, color=fs.PALETTE.ink)
    ax.text(-0.15, b / 2, "b = 3 cm", ha="right", va="center", fontsize=fs.TYPE.annot_lg, color=fs.PALETTE.ink)
    ax.text(a / 2 + 0.15, b / 2 + 0.15, "c = ?", ha="left", va="bottom",
            fontsize=fs.TYPE.annot_lg, color=fs.PALETTE.focus)        # the unknown -> focus
    ax.set_xlim(-0.9, a * 1.1)
    ax.set_ylim(-0.7, b * 1.15)
    _title(ax, "Geometrie · der Unbekannte = focus", "Mathematik")


def panel_coordinate(ax) -> None:
    pts = [(1, 2, "A"), (4, 3, "B"), (3, -1, "C")]
    fs.style_axes(ax, frame="center")
    ax.set_aspect("equal")
    ax.set_xlim(-2, 5.5)
    ax.set_ylim(-2.5, 4)
    ax.set_xticks(range(-1, 6))
    ax.set_yticks(range(-2, 4))
    ax.grid(True, color=fs.PALETTE.grid, lw=fs.STROKE.grid)
    ax.set_axisbelow(True)
    ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], color=fs.PALETTE.ink, lw=1.8)  # segment AB
    for x, y, lab in pts:
        ax.plot([x], [y], "o", color=fs.PALETTE.focus, ms=fs.STROKE.marker)
        ax.text(x + 0.15, y + 0.15, lab, fontsize=fs.TYPE.annot, color=fs.PALETTE.focus)
    _title(ax, "Koordinatensystem", "Mathematik")


def panel_composed(ax) -> None:
    """The composability preview: f(x) curve + shaded area (integral) + tangent + annotations
    — several typed primitives on one canvas, the direction the scene engine goes."""
    import numpy as np

    def f(x):
        return 0.18 * x ** 2 + 0.4 * x + 1.0

    def fp(x):
        return 0.36 * x + 0.4

    xs = np.linspace(-1.0, 5.2, 200)
    fs.style_axes(ax, frame="center")
    ax.set_xlim(-1.3, 5.6)
    ax.set_ylim(-0.6, 7.5)
    ax.plot(xs, f(xs), color=fs.PALETTE.ink, lw=fs.STROKE.curve, zorder=3)          # the curve
    # shaded area under the curve on [a,b] — the integral, in translucent focus
    a, bnd = 1.0, 4.0
    xr = np.linspace(a, bnd, 60)
    ax.fill_between(xr, 0, f(xr), color=fs.region_fill(alpha=0.20), zorder=1)
    ax.plot([a, a], [0, f(a)], color=fs.PALETTE.focus, lw=0.8, zorder=2)
    ax.plot([bnd, bnd], [0, f(bnd)], color=fs.PALETTE.focus, lw=0.8, zorder=2)
    ax.text((a + bnd) / 2, 1.0, "A = ∫ f(x) dx", ha="center", va="bottom",
            fontsize=fs.TYPE.annot, color=fs.darken(fs.PALETTE.focus, .1), zorder=4)
    # tangent at x0 — slope COMPUTED (f'(x0)); the element of interest, in focus
    x0 = 3.0
    y0, k = f(x0), fp(x0)
    tx = np.array([x0 - 1.3, x0 + 1.3])
    ax.plot(tx, y0 + k * (tx - x0), color=fs.PALETTE.focus, lw=1.7, zorder=4)
    ax.plot([x0], [y0], "o", color=fs.PALETTE.focus, ms=fs.STROKE.marker, zorder=5)
    ax.annotate("Tangente · k = f '(x₀)", (x0, y0), textcoords="offset points", xytext=(8, 14),
                fontsize=fs.TYPE.annot, color=fs.PALETTE.focus,
                arrowprops={"arrowstyle": "-", "color": fs.PALETTE.muted, "lw": 0.7})
    _title(ax, "Komponierte Szene: Fläche + Tangente", "Mathematik")


def render(out: Path | None = None) -> Path:
    fs.use_house_style()
    fig = plt.figure(figsize=(9.4, 12.6), layout="constrained")
    gs = fig.add_gridspec(4, 2, height_ratios=[0.42, 1, 1, 1])
    panel_palette(fig.add_subplot(gs[0, :]))
    panel_bar(fig.add_subplot(gs[1, 0]))
    panel_line(fig.add_subplot(gs[1, 1]))
    panel_scatter(fig.add_subplot(gs[2, 0]))
    panel_triangle(fig.add_subplot(gs[2, 1]))
    panel_coordinate(fig.add_subplot(gs[3, 0]))
    panel_composed(fig.add_subplot(gs[3, 1]))
    fig.suptitle("TeachersAid · Abbildungs-Styleguide  (Entwurf v0)",
                 fontsize=15, fontweight="bold", color=fs.PALETTE.ink, ha="left", x=0.02)
    fig.text(0.02, 0.005, f"Schrift: {fs.FONT_FAMILY}   ·   semantische Farbrollen + categorical ramp",
             fontsize=fs.TYPE.caption, color=fs.PALETTE.muted)
    out = out or (RUNS_DIR / "style_specimen.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(render())
