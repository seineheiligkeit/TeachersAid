"""Geometric constructions as computed scenes — the first didactic recipe of the scene engine.

`triangle_geometry` computes every notable point/value of a triangle (the merkwürdige Punkte)
from its three vertices — circumcircle U/R, incircle I/r, centroid S, orthocentre H, the
nine-point centre N, side lengths, angles. Nothing is hand-placed: move a vertex and it all
re-solves (correct by construction). `construction_scene` projects that fact-set into a
`scene.Scene` at a given **stage** (1–6) — the step-by-step construction a worksheet builds up,
helping lines bright in their step then receded to just the result. So one computed object →
the whole figure-heavy construction worksheet.

Pure: imports only the scene primitives + numpy. The Asset generator
(`assets.matplotlib:triangle_construction`) wraps this for the engine.
"""
from __future__ import annotations

import math

import numpy as np

from .scene import Arc, Canvas, CircleShape, Label, Line, PointMark, Polyline, Scene

# family slots into the figstyle ramps (hue + dash), one per construction family
PERP, ALT, BISEC, MEDIAN = 0, 1, 2, 3
_RECEDED = "#aeb6bd"
_LOFF = {"U": (-0.34, 0.30), "I": (-0.30, -0.34), "S": (0.40, -0.10), "H": (0.20, 0.40)}


def triangle_geometry(A, B, C) -> dict:
    """All notable points/values of triangle ABC, computed from the vertices."""
    A, B, C = (np.asarray(p, float) for p in (A, B, C))
    a, b, c = (np.linalg.norm(p - q) for p, q in ((B, C), (C, A), (A, B)))   # a opp. A, …
    area = 0.5 * abs((B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1]))
    s = (a + b + c) / 2
    S = (A + B + C) / 3                                    # centroid
    I = (a * A + b * B + c * C) / (a + b + c)              # incentre
    r = area / s                                           # inradius
    ax_, ay = A; bx, by = B; cx, cy = C                    # circumcentre
    d = 2 * (ax_ * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    U = np.array([
        ((ax_**2 + ay**2) * (by - cy) + (bx**2 + by**2) * (cy - ay) + (cx**2 + cy**2) * (ay - by)) / d,
        ((ax_**2 + ay**2) * (cx - bx) + (bx**2 + by**2) * (ax_ - cx) + (cx**2 + cy**2) * (bx - ax_)) / d,
    ])
    R = float(np.linalg.norm(U - A))
    H = A + B + C - 2 * U                                  # orthocentre (Euler relation)
    N = (U + H) / 2                                        # nine-point centre

    def foot(P, Q, X):                                     # foot of perpendicular from X onto PQ
        PQ = Q - P
        return P + np.dot(X - P, PQ) / np.dot(PQ, PQ) * PQ

    def ang(V, P, Q):
        u, v = P - V, Q - V
        return math.degrees(math.acos(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))))

    return dict(
        A=A, B=B, C=C, a=float(a), b=float(b), c=float(c), S=S, I=I, r=r, U=U, R=R, H=H, N=N,
        Mbc=(B + C) / 2, Mca=(C + A) / 2, Mab=(A + B) / 2,
        Da=(b * B + c * C) / (b + c), Db=(c * C + a * A) / (c + a), Dc=(a * A + b * B) / (a + b),
        Ha=foot(B, C, A), Hb=foot(C, A, B), Hc=foot(A, B, C),
        alpha=ang(A, B, C), beta=ang(B, C, A), gamma=ang(C, A, B),
    )


def _pt(P) -> tuple[float, float]:
    return (float(P[0]), float(P[1]))


def _arc(V, P, Q, label) -> Arc:
    a1 = math.degrees(math.atan2(P[1] - V[1], P[0] - V[0]))
    a2 = math.degrees(math.atan2(Q[1] - V[1], Q[0] - V[0]))
    sweep = (a2 - a1) % 360
    if sweep > 180:
        a1, sweep = a2, 360 - sweep
    return Arc(center=_pt(V), radius=0.6, theta1=a1, theta2=a1 + sweep, label=label)


def construction_scene(g: dict, stage: int = 6) -> Scene:
    """The construction at `stage` (1–6), cumulative: prior results recede, the active step's
    helping lines are bright. Stage 1 the triangle · 2 Umkreis · 3 Inkreis · 4 Schwerpunkt ·
    5 Höhenschnittpunkt · 6 Eulergerade + Feuerbachkreis."""
    A, B, C, S = g["A"], g["B"], g["C"], g["S"]
    sc = Scene(canvas=Canvas(figsize=(5.0, 4.8), aspect="equal", frame="off"))

    # the triangle + vertices (always)
    sc.add(Polyline([_pt(A), _pt(B), _pt(C)], role="ink", width=2.3, closed=True, z=5))
    for P, name in ((A, "A"), (B, "B"), (C, "C")):
        off = (P - S) / np.linalg.norm(P - S) * 0.42
        sc.add(PointMark(_pt(P), label=name, role="ink", size=4.5, label_offset=_pt(off),
                         bold=False, z=6))
    if stage == 1:                                          # the starting figure: fully labelled
        for (P, Q, lab) in ((B, C, "a"), (C, A, "b"), (A, B, "c")):
            mid = (P + Q) / 2
            out = (mid - S) / np.linalg.norm(mid - S) * 0.32
            sc.add(Label(_pt(mid + out), lab, role="muted", size=8.5))
        sc.add(_arc(A, B, C, "α"), _arc(B, C, A, "β"), _arc(C, A, B, "γ"))

    perp = [(M, g["U"] + (g["U"] - M) * 0.22) for M in (g["Mbc"], g["Mca"], g["Mab"])]
    bisec = [(A, g["Da"]), (B, g["Db"]), (C, g["Dc"])]
    median = [(A, g["Mbc"]), (B, g["Mca"]), (C, g["Mab"])]
    alt = [(A, g["Ha"]), (B, g["Hb"]), (C, g["Hc"])]

    def receded(P, label):
        return PointMark(_pt(P), label=label, role=_RECEDED, size=5, leader=False,
                         label_offset=_LOFF[label], bold=False, z=6)

    def active_center(P, label, slot):
        return PointMark(_pt(P), label=label, family=slot, size=7.5, leader=True,
                         label_offset=_LOFF[label], bold=True, z=6)

    # prior results persist, receded (centres only — circles would clutter)
    if stage > 2:
        sc.add(receded(g["U"], "U"))
    if stage > 3:
        sc.add(receded(g["I"], "I"))
    if stage > 4:
        sc.add(receded(g["S"], "S"))
    if stage > 5:
        sc.add(receded(g["H"], "H"))

    # the active step: bright helping lines + its result
    if stage == 2:
        sc.add(*[Line(_pt(p), _pt(q), family=PERP) for p, q in perp])
        sc.add(CircleShape(_pt(g["U"]), g["R"], family=PERP, width=1.6),
               active_center(g["U"], "U", PERP))
    elif stage == 3:
        sc.add(*[Line(_pt(p), _pt(q), family=BISEC) for p, q in bisec])
        sc.add(CircleShape(_pt(g["I"]), g["r"], family=BISEC, width=1.6),
               active_center(g["I"], "I", BISEC))
    elif stage == 4:
        sc.add(*[Line(_pt(p), _pt(q), family=MEDIAN) for p, q in median])
        sc.add(active_center(g["S"], "S", MEDIAN))
    elif stage == 5:
        sc.add(*[Line(_pt(p), _pt(q), family=ALT) for p, q in alt])
        sc.add(active_center(g["H"], "H", ALT))
    elif stage == 6:
        d = g["H"] - g["U"]                                 # the Eulergerade through U, S, H
        sc.add(Line(_pt(g["U"] - 1.3 * d), _pt(g["H"] + 0.7 * d), role="ink", width=1.6, z=4))
        sc.add(CircleShape(_pt(g["N"]), g["R"] / 2, role="focus", dash=(0, (5, 3)), width=1.5, z=3))
        for name, P, slot in (("U", g["U"], PERP), ("S", g["S"], MEDIAN), ("H", g["H"], ALT)):
            sc.add(active_center(P, name, slot))

    # frame the view on the circumcircle so the box never jumps between stages
    pad = g["R"] * 0.14 + 0.35
    sc.canvas.xlim = (g["U"][0] - g["R"] - pad, g["U"][0] + g["R"] + pad)
    sc.canvas.ylim = (g["U"][1] - g["R"] - pad, g["U"][1] + g["R"] + pad)
    return sc
