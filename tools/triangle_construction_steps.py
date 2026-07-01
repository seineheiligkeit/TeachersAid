"""The step-by-step construction worksheet — the layering idea as a SEQUENCE.

One computed scene (the triangle's notable points) rendered as six cumulative stages, the
way a construction worksheet builds it up: start with the triangle, construct one notable
point per step. The step's helping lines are bright WHILE you build it, then dimmed to just
the result (the centre / circle) so the next step stays readable — "Hilfslinien erscheinen
im Schritt, danach bleibt nur das Ergebnis". Everything is computed from the three vertices
(`geometry`), so the whole figure-heavy worksheet costs three points of input.

    python -m tools.triangle_construction_steps    # -> runs/triangle_construction.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402
from tools.triangle_centers_specimen import FAM, geometry  # noqa: E402

_HALO = [pe.withStroke(linewidth=2.6, foreground="white")]
_FAINT = "#aeb6bd"   # a constructed result, receded so the active step reads


def _hue(slot: int) -> str:
    return fs.CATEGORICAL[slot]


def _seg(ax, p, q, slot, *, lw=1.35):
    ax.plot([p[0], q[0]], [p[1], q[1]], **fs.line_kind(slot, lw=lw), alpha=0.95, zorder=3)


def _triangle(ax, g, *, full_labels: bool):
    A, B, C = g["A"], g["B"], g["C"]
    tri = np.array([A, B, C, A])
    ax.plot(tri[:, 0], tri[:, 1], color=fs.PALETTE.ink, lw=2.3, zorder=5, solid_capstyle="round")
    cen = g["S"]
    for P, name in ((A, "A"), (B, "B"), (C, "C")):
        ax.plot([P[0]], [P[1]], "o", color=fs.PALETTE.ink, ms=4.5, zorder=6)
        off = (P - cen) / np.linalg.norm(P - cen) * 0.42
        ax.text(P[0] + off[0], P[1] + off[1], name, fontsize=fs.TYPE.annot, color=fs.PALETTE.ink,
                ha="center", va="center", zorder=7, path_effects=_HALO)
    if full_labels:
        for (P, Q, lab) in ((B, C, "a"), (C, A, "b"), (A, B, "c")):
            mid = (P + Q) / 2
            out = (mid - cen) / np.linalg.norm(mid - cen) * 0.32
            ax.text(mid[0] + out[0], mid[1] + out[1], lab, fontsize=fs.TYPE.tick,
                    color=fs.PALETTE.muted, ha="center", va="center", zorder=7, path_effects=_HALO)


def _result_center(ax, P, label, slot, loff, *, active: bool):
    col = _hue(slot) if active else _FAINT
    ms = 7.5 if active else 5
    ax.plot([P[0]], [P[1]], "o", color=col, ms=ms, mec="white", mew=1.2, zorder=6)
    lp = (P[0] + loff[0], P[1] + loff[1])
    if active:
        ax.plot([P[0], lp[0]], [P[1], lp[1]], color=col, lw=0.6, zorder=5)
    ax.text(lp[0], lp[1], label, fontsize=fs.TYPE.annot_lg if active else fs.TYPE.tick,
            fontweight="bold", color=col, ha="center", va="center", zorder=7, path_effects=_HALO)


def _circle(ax, center, radius, slot, *, active: bool):
    ax.add_patch(Circle(center, radius, fill=False,
                        edgecolor=_hue(slot) if active else _FAINT,
                        lw=1.6 if active else 1.0, alpha=1.0 if active else 0.7, zorder=2))


_LOFF = {"U": (-0.34, 0.30), "I": (-0.30, -0.34), "S": (0.40, -0.10), "H": (0.20, 0.40)}


def draw_stage(ax, g, stage: int) -> None:
    fs.style_axes(ax, frame="off")
    ax.set_aspect("equal")
    _triangle(ax, g, full_labels=(stage == 1))

    perp = [(M, g["U"] + (g["U"] - M) * 0.22) for M in (g["Mbc"], g["Mca"], g["Mab"])]
    bisec = [(g["A"], g["Da"]), (g["B"], g["Db"]), (g["C"], g["Dc"])]
    median = [(g["A"], g["Mbc"]), (g["B"], g["Mca"]), (g["C"], g["Mab"])]
    alt = [(g["A"], g["Ha"]), (g["B"], g["Hb"]), (g["C"], g["Hc"])]

    # constructed-in-an-earlier-step results persist, RECEDED (centres only — circles would clutter)
    if stage > 2:
        _result_center(ax, g["U"], "U", FAM["perp"]["slot"], _LOFF["U"], active=False)
    if stage > 3:
        _result_center(ax, g["I"], "I", FAM["bisec"]["slot"], _LOFF["I"], active=False)
    if stage > 4:
        _result_center(ax, g["S"], "S", FAM["median"]["slot"], _LOFF["S"], active=False)
    if stage > 5:
        _result_center(ax, g["H"], "H", FAM["alt"]["slot"], _LOFF["H"], active=False)

    # the ACTIVE step: bright helping lines + its result
    if stage == 2:
        for p, q in perp:
            _seg(ax, p, q, FAM["perp"]["slot"])
        _circle(ax, g["U"], g["R"], FAM["perp"]["slot"], active=True)
        _result_center(ax, g["U"], "U", FAM["perp"]["slot"], _LOFF["U"], active=True)
    elif stage == 3:
        for p, q in bisec:
            _seg(ax, p, q, FAM["bisec"]["slot"])
        _circle(ax, g["I"], g["r"], FAM["bisec"]["slot"], active=True)
        _result_center(ax, g["I"], "I", FAM["bisec"]["slot"], _LOFF["I"], active=True)
    elif stage == 4:
        for p, q in median:
            _seg(ax, p, q, FAM["median"]["slot"])
        _result_center(ax, g["S"], "S", FAM["median"]["slot"], _LOFF["S"], active=True)
    elif stage == 5:
        for p, q in alt:
            _seg(ax, p, q, FAM["alt"]["slot"])
        _result_center(ax, g["H"], "H", FAM["alt"]["slot"], _LOFF["H"], active=True)
    elif stage == 6:
        # synthesis: U, S, H are collinear (Eulergerade); the nine-point circle through N
        for name, P, slot in (("U", g["U"], FAM["perp"]["slot"]),
                              ("S", g["S"], FAM["median"]["slot"]),
                              ("H", g["H"], FAM["alt"]["slot"])):
            _result_center(ax, P, name, slot, _LOFF[name], active=True)
        d = g["H"] - g["U"]
        p0, p1 = g["U"] - 1.3 * d, g["H"] + 0.7 * d
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=fs.PALETTE.ink, lw=1.6, zorder=4)
        _circle(ax, g["N"], g["R"] / 2, FAM["bisec"]["slot"], active=False)
        ax.add_patch(Circle(g["N"], g["R"] / 2, fill=False, edgecolor=fs.PALETTE.focus,
                            lw=1.5, linestyle=(0, (5, 3)), zorder=3))

    pad = g["R"] * 0.14 + 0.35
    ax.set_xlim(g["U"][0] - g["R"] - pad, g["U"][0] + g["R"] + pad)
    ax.set_ylim(g["U"][1] - g["R"] - pad, g["U"][1] + g["R"] + pad)


_TITLES = [
    "1 · Das Dreieck",
    "2 · Mittelsenkrechten → Umkreis",
    "3 · Winkelhalbierende → Inkreis",
    "4 · Seitenhalbierenden → Schwerpunkt",
    "5 · Höhen → Höhenschnittpunkt",
    "6 · Eulergerade & Feuerbachkreis",
]


def render(out: Path | None = None) -> Path:
    fs.use_house_style()
    g = geometry((0, 0), (8, 0), (1.5, 4.0))
    fig = plt.figure(figsize=(13.5, 8.6), layout="constrained")
    gs = fig.add_gridspec(2, 3)
    for i in range(6):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        draw_stage(ax, g, i + 1)
        ax.set_title(_TITLES[i], loc="left", color=fs.PALETTE.ink, fontsize=fs.TYPE.label)
    fig.suptitle("Eine Konstruktion, sechs Schritte — alles aus drei Eckpunkten berechnet",
                 fontsize=14, fontweight="bold", color=fs.PALETTE.ink)
    fig.text(0.5, 0.005,
             "Hilfslinien sind im jeweiligen Schritt hell; danach bleibt nur das Ergebnis "
             "(Mittelpunkt / Kreis), damit der nächste Schritt lesbar bleibt.",
             ha="center", fontsize=fs.TYPE.caption, color=fs.PALETTE.muted)
    out = out or (RUNS_DIR / "triangle_construction.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=165)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(render())
