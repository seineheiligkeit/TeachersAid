"""A HARD figure, to develop the line vocabulary: the notable points/centres of a triangle
(merkwürdige Punkte) — the classic compass-and-straightedge construction, with every line
family at once. Everything is COMPUTED from the three vertices (correct-by-construction):

  · the triangle, its side labels a/b/c and angle arcs α/β/γ
  · Mittelsenkrechten  (perpendicular bisectors)  → Umkreis (circumcircle), centre U
  · Winkelhalbierende  (angle bisectors)          → Inkreis (incircle), centre I
  · Seitenhalbierende  (medians)                  → Schwerpunkt (centroid) S
  · Höhen              (altitudes)                 → Höhenschnittpunkt (orthocentre) H
  · Feuerbachkreis (nine-point circle) + Eulergerade (Euler line through U, S, H)

Rendered twice — colour and GREYSCALE — to test the redundant hue+dash encoding under a
black-and-white photocopy (`pipeline.figstyle.line_kind` / `DASHES`).

    python -m tools.triangle_centers_specimen     # -> runs/triangle_centers.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Arc, Circle  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402

_HALO = [pe.withStroke(linewidth=2.6, foreground="white")]


def geometry(A, B, C) -> dict:
    """All notable points/values of triangle ABC, computed from the vertices."""
    A, B, C = (np.asarray(p, float) for p in (A, B, C))
    a, b, c = (np.linalg.norm(p - q) for p, q in ((B, C), (C, A), (A, B)))  # a opp. A, …
    area = 0.5 * abs((B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1]))
    s = (a + b + c) / 2
    S = (A + B + C) / 3                                   # centroid
    I = (a * A + b * B + c * C) / (a + b + c)             # incentre
    r = area / s                                          # inradius
    ax_, ay = A; bx, by = B; cx, cy = C                   # circumcentre
    d = 2 * (ax_ * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    U = np.array([
        ((ax_**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d,
        ((ax_**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax_ - cx) + (cx**2 + cy**2) * (bx - ax_)) / d,
    ])
    R = np.linalg.norm(U - A)
    H = A + B + C - 2 * U                                 # orthocentre (Euler relation)
    N = (U + H) / 2                                       # nine-point centre

    def foot(P, Q, X):                                    # foot of perpendicular from X onto PQ
        PQ = Q - P
        return P + np.dot(X - P, PQ) / np.dot(PQ, PQ) * PQ

    def ang(V, P, Q):                                     # interior angle at V (degrees)
        u, v = P - V, Q - V
        return np.degrees(np.arccos(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))))

    return dict(
        A=A, B=B, C=C, a=a, b=b, c=c, S=S, I=I, r=r, U=U, R=R, H=H, N=N,
        Mbc=(B + C) / 2, Mca=(C + A) / 2, Mab=(A + B) / 2,
        Da=(b * B + c * C) / (b + c), Db=(c * C + a * A) / (c + a), Dc=(a * A + b * B) / (a + b),  # bisector feet
        Ha=foot(B, C, A), Hb=foot(C, A, B), Hc=foot(A, B, C),                                       # altitude feet
        alpha=ang(A, B, C), beta=ang(B, C, A), gamma=ang(C, A, B),
    )


# Each construction family: a slot in the ramps (hue + dash) and its circle/centre.
FAM = {
    "perp":   dict(slot=0, name="Mittelsenkrechte → Umkreis (U)"),
    "bisec":  dict(slot=2, name="Winkelhalbierende → Inkreis (I)"),
    "median": dict(slot=3, name="Seitenhalbierende → Schwerpunkt (S)"),
    "alt":    dict(slot=1, name="Höhe → Höhenschnittpunkt (H)"),
}


def _style(slot: int, mono: bool, *, lw: float = 1.1) -> dict:
    """Family line style: hue+dash in colour; gray + dash-only in mono (the photocopy test)."""
    k = fs.line_kind(slot, lw=lw)
    if mono:
        k["color"] = "#3a3a3a"
    return k


def draw(ax, g: dict, *, mono: bool) -> None:
    A, B, C = g["A"], g["B"], g["C"]
    ink = "#222" if mono else fs.PALETTE.ink
    fs.style_axes(ax, frame="off")
    ax.set_aspect("equal")

    # --- construction families (drawn first, so the triangle sits on top) ---
    def seg(p, q, slot, lw=1.1):
        ax.plot([p[0], q[0]], [p[1], q[1]], **_style(slot, mono, lw=lw), zorder=2, alpha=0.95)

    # Mittelsenkrechten: from each side midpoint through U (perpendicular to the side)
    for M in (g["Mbc"], g["Mca"], g["Mab"]):
        seg(M, g["U"] + (g["U"] - M) * 0.28, FAM["perp"]["slot"])
    # Winkelhalbierende: vertex → foot on opposite side (through I)
    for V, D in ((A, g["Da"]), (B, g["Db"]), (C, g["Dc"])):
        seg(V, D, FAM["bisec"]["slot"])
    # Seitenhalbierende: vertex → opposite midpoint (through S)
    for V, M in ((A, g["Mbc"]), (B, g["Mca"]), (C, g["Mab"])):
        seg(V, M, FAM["median"]["slot"])
    # Höhen: vertex → foot on opposite side (through H)
    for V, F in ((A, g["Ha"]), (B, g["Hb"]), (C, g["Hc"])):
        seg(V, F, FAM["alt"]["slot"])

    # --- circles ---
    perp_c = "#555" if mono else fs.CATEGORICAL[FAM["perp"]["slot"]]
    bisec_c = "#555" if mono else fs.CATEGORICAL[FAM["bisec"]["slot"]]
    ax.add_patch(Circle(g["U"], g["R"], fill=False, edgecolor=perp_c,
                        linestyle="solid", lw=1.4, zorder=1))            # Umkreis
    ax.add_patch(Circle(g["I"], g["r"], fill=False, edgecolor=bisec_c,
                        linestyle=(0, (5, 3)) if mono else "solid", lw=1.4, zorder=1))  # Inkreis
    ax.add_patch(Circle(g["N"], g["R"] / 2, fill=False, edgecolor="#aaa",
                        linestyle=(0, (1, 2.2)), lw=1.0, zorder=1))      # Feuerbachkreis
    # Eulergerade through U, S, H
    dvec = g["H"] - g["U"]
    p0, p1 = g["U"] - 1.4 * dvec, g["H"] + 0.8 * dvec
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color="#9aa3ab", lw=0.9,
            linestyle=(0, (7, 4)), zorder=1)

    # --- the triangle on top ---
    tri = np.array([A, B, C, A])
    ax.plot(tri[:, 0], tri[:, 1], color=ink, lw=2.4, zorder=4, solid_capstyle="round")

    # --- centres (direct-labelled, with halos so they read over the mesh) ---
    # The four centres cluster near the centroid; fan the labels in fixed directions so
    # they never collide, and connect each to its marker with a short leader.
    def centre(P, label, slot, loff):
        col = ink if mono else fs.CATEGORICAL[slot]
        lp = (P[0] + loff[0], P[1] + loff[1])
        ax.plot([P[0], lp[0]], [P[1], lp[1]], color=col, lw=0.6, zorder=5)
        ax.plot([P[0]], [P[1]], "o", color=col, ms=7, mec="white", mew=1.2, zorder=6)
        ax.text(lp[0], lp[1], label, fontsize=fs.TYPE.annot_lg, fontweight="bold",
                color=col, ha="center", va="center", zorder=7, path_effects=_HALO)
    centre(g["U"], "U", FAM["perp"]["slot"], (-0.34, 0.30))
    centre(g["I"], "I", FAM["bisec"]["slot"], (-0.30, -0.34))
    centre(g["S"], "S", FAM["median"]["slot"], (0.40, -0.10))
    centre(g["H"], "H", FAM["alt"]["slot"], (0.18, 0.40))

    # --- vertices, side labels, angle arcs ---
    cen = g["S"]
    for P, name in ((A, "A"), (B, "B"), (C, "C")):
        ax.plot([P[0]], [P[1]], "o", color=ink, ms=5, zorder=6)
        off = (P - cen)
        off = off / np.linalg.norm(off) * 0.42
        ax.text(P[0] + off[0], P[1] + off[1], name, fontsize=fs.TYPE.annot_lg, color=ink,
                ha="center", va="center", zorder=7, path_effects=_HALO)
    for (P, Q, lab) in ((B, C, "a"), (C, A, "b"), (A, B, "c")):
        mid = (P + Q) / 2
        out = mid - cen
        out = out / np.linalg.norm(out) * 0.34
        ax.text(mid[0] + out[0], mid[1] + out[1], lab, fontsize=fs.TYPE.annot, color=ink,
                ha="center", va="center", zorder=7, path_effects=_HALO)

    def arc(V, P, Q, lab):
        a1 = np.degrees(np.arctan2(P[1] - V[1], P[0] - V[0]))
        a2 = np.degrees(np.arctan2(Q[1] - V[1], Q[0] - V[0]))
        sweep = (a2 - a1) % 360
        if sweep > 180:
            a1, sweep = a2, 360 - sweep
        rad = 0.62
        ax.add_patch(Arc(V, 2 * rad, 2 * rad, angle=0, theta1=a1, theta2=a1 + sweep,
                         color=ink, lw=1.1, zorder=5))
        m = np.radians(a1 + sweep / 2)
        ax.text(V[0] + rad * 1.6 * np.cos(m), V[1] + rad * 1.6 * np.sin(m), lab,
                fontsize=fs.TYPE.annot, color=ink, ha="center", va="center", zorder=7,
                path_effects=_HALO)
    arc(A, B, C, "α")
    arc(B, C, A, "β")
    arc(C, A, B, "γ")

    # frame the view around the circumcircle
    pad = g["R"] * 0.18 + 0.4
    ax.set_xlim(g["U"][0] - g["R"] - pad, g["U"][0] + g["R"] + pad)
    ax.set_ylim(g["U"][1] - g["R"] - pad, g["U"][1] + g["R"] + pad)


def _de(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def _value_box(ax, g: dict) -> None:
    lines = [
        f"a = {_de(g['a'])}    α = {_de(g['alpha'])}°",
        f"b = {_de(g['b'])}    β = {_de(g['beta'])}°",
        f"c = {_de(g['c'])}    γ = {_de(g['gamma'])}°",
        f"Umkreis  R = {_de(g['R'])}",
        f"Inkreis   r = {_de(g['r'])}",
    ]
    ax.text(0.015, 0.02, "\n".join(lines), transform=ax.transAxes, va="bottom", ha="left",
            fontsize=fs.TYPE.tick, color=fs.PALETTE.ink, linespacing=1.5,
            bbox={"boxstyle": "round,pad=0.5", "fc": fs.PALETTE.surface,
                  "ec": fs.PALETTE.grid, "lw": 1})


def render(out: Path | None = None) -> Path:
    fs.use_house_style()
    g = geometry((0, 0), (8, 0), (1.5, 4.0))
    fig = plt.figure(figsize=(13.0, 7.7), layout="constrained")
    gs = fig.add_gridspec(1, 2)
    axc = fig.add_subplot(gs[0, 0])
    axm = fig.add_subplot(gs[0, 1])
    draw(axc, g, mono=False)
    draw(axm, g, mono=True)
    _value_box(axc, g)
    axc.set_title("Farbe — Farbrolle + Strichart", loc="left", color=fs.PALETTE.ink)
    axm.set_title("Schwarz-Weiß (Fotokopie) — nur Strichart", loc="left", color=fs.PALETTE.ink)

    legend = [
        Line2D([0], [0], color=fs.PALETTE.ink, lw=2.4, label="Dreieck ABC"),
        Line2D([0], [0], **fs.line_kind(FAM["perp"]["slot"]), label=FAM["perp"]["name"]),
        Line2D([0], [0], **fs.line_kind(FAM["bisec"]["slot"]), label=FAM["bisec"]["name"]),
        Line2D([0], [0], **fs.line_kind(FAM["median"]["slot"]), label=FAM["median"]["name"]),
        Line2D([0], [0], **fs.line_kind(FAM["alt"]["slot"]), label=FAM["alt"]["name"]),
        Line2D([0], [0], color="#9aa3ab", lw=0.9, linestyle=(0, (7, 4)), label="Eulergerade"),
        Line2D([0], [0], color="#aaa", lw=1.0, linestyle=(0, (1, 2.2)), label="Feuerbachkreis (9-Punkte)"),
    ]
    fig.legend(handles=legend, loc="outside lower center", ncol=4, frameon=False,
               fontsize=fs.TYPE.tick)
    fig.suptitle("Merkwürdige Punkte des Dreiecks — alles aus den Eckpunkten berechnet",
                 fontsize=14, fontweight="bold", color=fs.PALETTE.ink)
    out = out or (RUNS_DIR / "triangle_centers.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=165)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(render())
