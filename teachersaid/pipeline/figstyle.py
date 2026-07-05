"""The figure styleguide — the single source of truth for how a TeachersAid figure *looks*.

Today every recipe in `pipeline/assets.py` hard-codes its own palette as inline hex
literals (`#33506e`, `#4f6f8f`, `#b03a2e`, …), copy-pasted ~25 times. That is why every
figure looks the same *and* why there is no lever to change it. This module replaces the
scattered literals with a small, **named, semantic** design system that the recipes
reference — so the look is consistent, meaningful, and tunable in one place.

The organising idea is **semantic colour roles**, not decoration: a colour MEANS something
and means the *same* thing in every figure —

    ink      structure: axes, frames, the default curve, primary text
    muted    secondary: leaders, citations, captions, secondary ticks
    grid     gridlines (quiet)
    primary  the main data (a single series of bars / one line)
    focus    the element/region of INTEREST — the unknown, the result, "look here"
    positive / negative   honest-vs-misleading, correct-vs-wrong, +/-
    surface  soft box fills (info boxes, geometry interiors)

`categorical` is the qualitative ramp for *several* series at once (the gap today: a
multi-series line silently falls back to matplotlib's default cycle). `subject_accent`
is the theming hook — a restrained per-subject hue layered on top of the constant
semantic roles, so we can dial identity (Q2: roles-first, light subject accents) without
rewriting anything: change the dict, not the recipes.

Pure data + thin matplotlib helpers; imports nothing from the engine. Call
`use_house_style()` once before building figures (the recipes will, like
`inline_math.configure`). Mirrors `rendering/reportlab_base`'s font discovery so the
figure text matches the worksheet body text (Carlito/Calibri) instead of DejaVu — figures
read as part of the document, not pasted in.

**Representation rule (SME review, 3 Jul 2026):** axes never use scientific notation;
large values scale to Mio./Mrd. with the unit named in the axis label (`unit_scale`),
numbers print German-style (`fmt_de` — dot thousands, comma decimals), and time (years)
belongs on a numeric x-axis, never on category ticks or bars.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import matplotlib.colors as mcolors
import matplotlib.font_manager as fm

# --- semantic colour roles ---------------------------------------------------
# A refined evolution of the existing palette (same blue-ink / red-focus language,
# so figures stay recognisable) with the missing roles named and a real data ramp.
PALETTE = SimpleNamespace(
    ink="#2b3d4f",        # structure: axes, frames, default curve, primary text
    muted="#6a7a88",      # secondary text, leaders, citations, captions
    grid="#e6eaed",       # gridlines (quiet)
    primary="#3a6ea5",    # the main data — single series of bars / one line
    secondary="#b06b4f",  # a paired SECOND series against `primary` (e.g. the women's
                          # wing of a population pyramid, g against f) — warm, not `focus`
                          # (which is reserved for the region of interest, never a series)
    focus="#c0392b",      # the element/region of interest: unknown · result · "look here"
    positive="#2e8b57",   # honest / correct / positive change
    negative="#b5403a",   # misleading / wrong / negative change
    surface="#eef3f8",    # soft box fill (info boxes, geometry interiors) — cool
    surface_warm="#fdecec",  # soft box fill — warm (process/cause-effect boxes)
    no_data="#e8e8e8",    # a "kein Wert" fill (an unmapped choropleth region)
    paper="#ffffff",
)

# Qualitative ramp for several series at once — distinguishable, reasonably
# colour-vision-deficiency-aware, and harmonious with `primary` (slot 0 == primary,
# so single-series and the first-of-many agree). The accessible alternative
# (Okabe–Ito) is a one-line swap when we want maximum CVD-safety.
CATEGORICAL = ["#3a6ea5", "#e08a3c", "#3f9e7a", "#9b5fa3", "#cf5c6b", "#c7a93b", "#5b8aa0"]

# Sequential colormap for thematic maps / intensity (choropleth, heat).
SEQUENTIAL = "YlOrRd"

# Dash ramp — the linestyle analogue of CATEGORICAL, for DENSE figures where many lines
# overlay one canvas (a triangle's bisectors/medians/altitudes, overlapping function
# families). The load-bearing reason it exists: a worksheet gets PHOTOCOPIED in black &
# white, so colour alone can't carry a distinction — pair a hue with a dash (redundant
# encoding) and the figure survives greyscale. matplotlib (offset, on-off…) tuples.
DASHES = [
    "solid",
    (0, (5, 3)),               # dashed
    (0, (1, 2.2)),             # dotted
    (0, (6, 2, 1, 2)),         # dash-dot
    (0, (9, 3)),               # long dash
    (0, (3, 2, 1, 2, 1, 2)),   # dash-dot-dot
]


def line_kind(i: int, *, lw: float = 1.1) -> dict:
    """A distinguishable line style for family `i` — a paired hue + dash (redundant, so it
    reads in colour AND in a black-and-white photocopy). Spread kwargs into ax.plot."""
    return {"color": CATEGORICAL[i % len(CATEGORICAL)],
            "linestyle": DASHES[i % len(DASHES)], "linewidth": lw}

# --- typography (matplotlib points) ------------------------------------------
TYPE = SimpleNamespace(
    base=10.0,      # default text
    title=12.5,     # figure / axes title
    label=10.0,     # axis labels
    tick=8.5,       # tick labels
    annot=9.0,      # in-figure annotations / data labels
    annot_lg=11.0,  # emphasised annotation (geometry side labels)
    caption=7.0,    # citation / source line
)

# --- strokes & marker sizes --------------------------------------------------
STROKE = SimpleNamespace(
    axis=1.0,
    curve=2.0,
    thin=0.8,
    grid=0.6,
    leader=0.7,
    marker=6.0,
    marker_sm=4.0,
)

# --- per-subject accent (the theming hook) -----------------------------------
# Restrained: an accent layered on the CONSTANT semantic roles (used sparingly, e.g. a
# title rule), so identity is tunable without the colours losing meaning. Keyed by a
# lowercase substring of the subject name; `subject_accent` matches loosely. Default = ink.
SUBJECT_ACCENTS = {
    "mathematik": "#3a6ea5",
    "physik": "#2b6ca3",
    "chemie": "#2f8f83",
    "biologie": "#3f9e5a",
    "geographie": "#b07a32",   # GW(B)
    "wirtschaft": "#b07a32",
    "geschichte": "#9a6b4f",   # GP(B)
    "politische": "#9a6b4f",
    "deutsch": "#9b5fa3",
    "englisch": "#c0566b",
    "französisch": "#c0566b",
    "latein": "#8a6f4a",
}


def subject_accent(subject: str | None) -> str:
    """The accent hue for a subject (loose substring match); `ink` when unknown/None."""
    s = (subject or "").strip().lower()
    for key, col in SUBJECT_ACCENTS.items():
        if key in s:
            return col
    return PALETTE.ink


# --- number display (never scientific notation) -------------------------------
# The magnitudes a value axis may be scaled to, largest first. "Tsd." is deliberately
# absent: 4–6-digit numbers still read fine with German dot-grouping ("129.086").
UNIT_SCALES: tuple[tuple[float, str], ...] = ((1e9, "Mrd."), (1e6, "Mio."))


def fmt_de(v: float, decimals: int | None = None) -> str:
    """German-format a number — dot thousands, comma decimals, NEVER scientific
    notation (8916845 → "8.916.845", 8.9 → "8,9"). With `decimals=None` the precision
    is chosen automatically (integers bare; 1 decimal ≥10, else 2; trailing zeros
    stripped); an explicit `decimals` is rendered exactly (7.04 @ 1 → "7,0")."""
    x = float(v)
    auto = decimals is None
    if auto:
        decimals = 0 if x == int(x) else (1 if abs(x) >= 10 else 2)
    s = f"{x:,.{decimals}f}".translate(str.maketrans(",.", ".,"))
    if auto and "," in s:
        s = s.rstrip("0").rstrip(",")
    return s


def unit_scale(values, label: str = "") -> tuple[list[float], str, float]:
    """Auto-scale large values for display — the SME rule "nie 8.9e+06 an der Achse":
    max ≥ 1e9 → divide by 1e9 and suffix the label "(in Mrd.)", ≥ 1e6 → "(in Mio.)".
    Returns (scaled_values, labelled, divisor); small values pass through unchanged.
    An empty label becomes just "in Mio." so the unit is never silently dropped."""
    vals = [float(v) for v in values]
    vmax = max((abs(v) for v in vals), default=0.0)
    for div, name in UNIT_SCALES:
        if vmax >= div:
            lbl = f"{label} (in {name})" if label else f"in {name}"
            return [v / div for v in vals], lbl, div
    return vals, label, 1.0


# --- colour helpers ----------------------------------------------------------
def _blend(color: str, toward: str, t: float) -> str:
    a = mcolors.to_rgb(color)
    b = mcolors.to_rgb(toward)
    return mcolors.to_hex(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def lighten(color: str, t: float = 0.5) -> str:
    """Blend `color` toward white by fraction `t`."""
    return _blend(color, "#ffffff", t)


def darken(color: str, t: float = 0.3) -> str:
    """Blend `color` toward black by fraction `t`."""
    return _blend(color, "#000000", t)


def region_fill(color: str | None = None, alpha: float = 0.18) -> tuple:
    """An RGBA fill for a shaded region (e.g. the area under a curve) — translucent
    `focus` by default, so the region reads as 'of interest' without hiding gridlines."""
    return mcolors.to_rgba(color or PALETTE.focus, alpha)


# --- font discovery (mirror rendering/reportlab_base so figures match the body) ---
_FONT_DIRS = [
    "/usr/share/fonts/truetype/crosextra",
    "/usr/share/fonts/truetype/carlito",
    "/usr/share/fonts",
    str(Path.home() / "AppData/Local/Microsoft/Windows/Fonts"),
    "C:/Windows/Fonts",
]
# (filename candidates, in preference order) — Carlito first, then its metric twin Calibri.
_FONT_FILES = [
    ("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf"),
    ("calibri.ttf", "calibrib.ttf", "calibrii.ttf", "calibriz.ttf"),
]


def _find(name: str) -> Path | None:
    for d in _FONT_DIRS:
        p = Path(d) / name
        if p.exists():
            return p
    return None


def _renders_small(family: str) -> bool:
    """Does `family` actually rasterise small text, or drop most glyphs?

    Some real-world TTFs (notably the Windows **Calibri** build seen on the dev machine)
    hit a matplotlib+Agg small-size rendering bug: a raw text artist at ~9 pt loses most of
    its glyphs (e.g. "Zitronensaft" → "ft"), while the SAME font renders fine at ≥ 11 pt and
    via the tick machinery — so the failure is invisible in the big-figure specimens and only
    bites the small-label recipes (number line, timeline). We refuse such a font here rather
    than ship broken worksheets: render a probe string at 9 pt and require that it lays down
    ink across a reasonable fraction of its width (a dropped-glyph render is nearly blank).
    Measured, not assumed — the figure-side twin of the layout lint."""
    try:
        import numpy as np
        import matplotlib.pyplot as plt
    except Exception:
        return True                              # no numpy/plt at import → don't block
    probe = "Zitronensaft"
    try:
        fig = plt.figure(figsize=(3.0, 0.6), dpi=100)
        fig.text(0.5, 0.5, probe, family=family, fontsize=9, ha="center", va="center",
                 color="black")
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(
            fig.canvas.get_width_height()[::-1] + (4,))
        plt.close(fig)
    except Exception:
        return True                              # probe itself failed → don't block the font
    dark = buf[..., :3].sum(axis=2) < 400        # near-black pixels (the glyph strokes)
    cols_with_ink = int(dark.any(axis=0).sum())
    # a healthy 12-char render inks ~55–70 columns; a dropped-glyph render inks < 10.
    return cols_with_ink >= 25


def _register_font() -> str:
    """Register the first available real family that actually renders (Carlito → Calibri),
    else the DejaVu Sans fallback (always present, always renders). A candidate that fails the
    small-text probe (`_renders_small`) is registered but skipped for selection, so a buggy
    Calibri never becomes the house font and silently blanks the small-label figures."""
    fallback: str | None = None
    for regular, *others in _FONT_FILES:
        path = _find(regular)
        if not path:
            continue
        fm.fontManager.addfont(str(path))
        for extra in others:                     # bold/italic so weight= works
            p = _find(extra)
            if p:
                fm.fontManager.addfont(str(p))
        name = fm.FontProperties(fname=str(path)).get_name()
        if _renders_small(name):
            return name
        if fallback is None:                     # remember it for metrics, but keep looking
            fallback = name
    return "DejaVu Sans"


FONT_FAMILY = _register_font()

_APPLIED = False


def house_rc() -> dict:
    """The house rcParams as a dict — the document font, the type scale, the ink/grid colours,
    and the categorical colour cycle (so a multi-series plot uses the ramp, not matplotlib's
    defaults). Use with `plt.rc_context(house_rc())` to scope the style to one figure (e.g. the
    scene engine) WITHOUT restyling the not-yet-ported recipes; `use_house_style()` applies it
    globally (for when the recipes are ported)."""
    from cycler import cycler

    return {
        "font.family": FONT_FAMILY,
        "font.size": TYPE.base,
        "axes.edgecolor": PALETTE.ink,
        "axes.labelcolor": PALETTE.ink,
        "axes.titlesize": TYPE.title,
        "axes.titlecolor": PALETTE.ink,
        "axes.labelsize": TYPE.label,
        "axes.linewidth": STROKE.axis,
        "axes.prop_cycle": cycler(color=CATEGORICAL),
        "text.color": PALETTE.ink,
        "xtick.color": PALETTE.ink,
        "ytick.color": PALETTE.ink,
        "xtick.labelsize": TYPE.tick,
        "ytick.labelsize": TYPE.tick,
        "grid.color": PALETTE.grid,
        "grid.linewidth": STROKE.grid,
        "legend.fontsize": TYPE.tick,
        "legend.frameon": False,
        "figure.facecolor": PALETTE.paper,
        "savefig.facecolor": PALETTE.paper,
    }


def use_house_style() -> None:
    """Apply the house rcParams globally, once (idempotent). The ported recipes in
    `pipeline/assets.py` scope the style per-figure via `plt.rc_context(house_rc())` (so a recipe
    never leaks rcParams onto another figure); this global form is kept for the multi-panel
    specimen scripts that render one styled sheet in a single process."""
    global _APPLIED
    if _APPLIED:
        return
    import matplotlib as mpl
    mpl.rcParams.update(house_rc())
    _APPLIED = True


def style_axes(ax, *, frame: str = "lb", grid: bool = True, grid_axis: str = "both") -> None:
    """Apply the house axis treatment.

    frame: which spines to keep — "lb" (left+bottom, the clean default for data charts),
    "box" (all four), "off" (none — geometry/diagrams), or "center" (axes through the origin,
    for a coordinate plane). Grid is drawn quietly in the `grid` colour when requested.
    """
    if frame == "off":
        ax.axis("off")
        return
    if frame == "center":
        for side in ("left", "bottom"):
            ax.spines[side].set_position("zero")
            ax.spines[side].set_color(PALETTE.muted)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    elif frame == "lb":
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(PALETTE.ink)
    else:  # "box"
        for side in ("top", "right", "left", "bottom"):
            ax.spines[side].set_color(PALETTE.ink)
    if grid:
        ax.grid(True, axis=grid_axis, color=PALETTE.grid, linewidth=STROKE.grid, zorder=0)
        ax.set_axisbelow(True)


def c(role: str) -> str:
    """Look up a semantic role colour by name (e.g. `c("focus")`)."""
    return getattr(PALETTE, role)


def cat(i: int) -> str:
    """The i-th hue of the categorical ramp (wraps). Slot 0 == `primary`, so a single
    series and the first-of-many agree."""
    return CATEGORICAL[i % len(CATEGORICAL)]


def edge(role: str = "primary", t: float = 0.22) -> str:
    """A darker edge for a filled shape in `role` — a bar/box/geometry outline that reads
    against its fill (the ported recipes' `edgecolor`; replaces the hand-picked pairs like
    `#4f6f8f` filled + `#33506e` edged)."""
    return darken(c(role), t)


# --- SVG (decorative kit) — the same design system, expressed as literal strings ---
# The svg: recipes are content-FREE decoration, but their default hues should still be the
# house colours (not a fourth scattered set). These are the only place a hex string is a
# legitimate *value* — an SVG attribute — rather than a matplotlib colour, so they live here.
SVG = SimpleNamespace(
    ink=PALETTE.ink,
    primary=PALETTE.primary,
    accent=SUBJECT_ACCENTS["geographie"],   # a warm ochre banner/rule
    paper=PALETTE.paper,
)
