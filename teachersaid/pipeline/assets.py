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

from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402

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


# --- parameterized recipes (read asset.spec) ---------------------------------
@_generator("matplotlib:number_line")
def _number_line(asset: Asset, path: Path) -> None:
    """A number line. spec: {min, max, step?, marks?: [{at, label?}]}."""
    s = asset.spec or {}
    lo, hi = float(s.get("min", 0)), float(s.get("max", 10))
    step = float(s.get("step", 1)) or 1.0
    fig, ax = plt.subplots(figsize=(7.2, 1.1))
    ax.axhline(0, color="#33506e", lw=1.4, zorder=1)
    t = lo
    while t <= hi + 1e-9:
        ax.plot([t, t], [-0.07, 0.07], color="#33506e", lw=1)
        ax.text(t, -0.22, f"{t:g}", ha="center", va="top", fontsize=9)
        t += step
    for m in s.get("marks", []):
        at = float(m["at"])
        ax.plot([at], [0], "o", color="#b03a2e", ms=9, zorder=3)
        if m.get("label"):
            ax.text(at, 0.16, str(m["label"]), ha="center", va="bottom",
                    color="#b03a2e", fontsize=9)
    ax.set_xlim(lo - step * 0.6, hi + step * 0.6)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


@_generator("matplotlib:bar_chart")
def _bar_chart(asset: Asset, path: Path) -> None:
    """A bar chart. spec: {categories: [...], values: [...], title?, xlabel?, ylabel?}."""
    s = asset.spec or {}
    cats = [str(c) for c in s.get("categories", [])]
    vals = [float(v) for v in s.get("values", [])]
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    ax.bar(cats, vals, color="#4f6f8f", edgecolor="#33506e")
    if s.get("title"):
        ax.set_title(s["title"])
    if s.get("xlabel"):
        ax.set_xlabel(s["xlabel"])
    if s.get("ylabel"):
        ax.set_ylabel(s["ylabel"])
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")  # don't clip a long title/labels
    plt.close(fig)


@_generator("matplotlib:function_graph")
def _function_graph(asset: Asset, path: Path) -> None:
    """A coordinate graph. spec: {xmin?, xmax?, m?, b? (line y=mx+b), points?: [[x,y],…],
    connect? (join the points with a line, e.g. a v-t graph), xlabel?, ylabel?,
    ymin?, ymax?, title?}."""
    s = asset.spec or {}
    xmin, xmax = float(s.get("xmin", -5)), float(s.get("xmax", 5))
    fig, ax = plt.subplots(figsize=(4.3, 4.0))
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
        ax.set_title(s["title"])
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")  # don't clip a long title/label
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
    'fix' the axis: the task is to spot the manipulation (geschönte Kurve)."""
    years = ["2019", "2020", "2021", "2022"]
    values = [101.0, 101.4, 101.9, 102.3]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.bar(years, values, color="#c0504d")
    ax.set_ylim(100.5, 102.5)  # <-- the trick: zoomed axis exaggerates change
    ax.set_ylabel("Index")
    ax.set_title("Dramatischer Anstieg?!")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


@_generator("matplotlib:honest_axis")
def _honest_axis(asset: Asset, path: Path) -> None:
    """The same data with a zero-based axis — the teacher-only honest comparison."""
    years = ["2019", "2020", "2021", "2022"]
    values = [101.0, 101.4, 101.9, 102.3]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.bar(years, values, color="#4f6f52")
    ax.set_ylim(0, 110)  # zero-based: the change is tiny
    ax.set_ylabel("Index")
    ax.set_title("Dieselben Daten, ehrliche Achse")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


# Recipes an LLM may REQUEST (parameterized, correct-by-construction). The bespoke
# figures (em_spectrum, truncated/honest axis) are curated-only and NOT here — a
# generated worksheet may only ask for these safe, spec-driven recipes.
GENERATION_RECIPES: dict[str, str] = {
    "matplotlib:number_line":
        'Zahlenstrahl — spec {"min":num,"max":num,"step"?:num,"marks"?:[{"at":num,"label"?:str}]}',
    "matplotlib:bar_chart":
        'Balkendiagramm — spec {"categories":[str],"values":[num],"title"?:str,"xlabel"?:str,"ylabel"?:str}',
    "matplotlib:function_graph":
        'Koordinatensystem/Gerade — spec {"xmin"?,"xmax"?,"m"?,"b"? (Gerade y=mx+b),'
        '"points"?:[[x,y]],"connect"? (Punkte zu einer Kurve verbinden, z. B. v-t-Diagramm),'
        '"xlabel"?,"ylabel"?,"ymin"?,"ymax"?,"title"?}',
    "matplotlib:math_formula":
        'Formel via LaTeX — spec {"latex":str}',
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
