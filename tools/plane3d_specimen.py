"""PROTOTYPE — 3D analytic geometry as a projected 2D scene (Schrägbild).

The design probe behind "can the figure engine do ℝ³?": model the situation in 3D,
compute every load-bearing object with **sympy** (correct-by-construction — a plane, its
normal, the Schnittgerade of two planes, the enclosed angle are COMPUTED, never authored),
then apply a single fixed **axonometric projection** ℝ³→ℝ² and emit ordinary 2D `scene`
primitives — so the whole existing renderer (`scene.render_scene`) + styleguide
(`figstyle`: house colours, halos, the photocopy-safe dash ramp) is reused unchanged.
No `mplot3d`, nothing interactive: a print-first Schrägbild, the way an AHS textbook draws it.

`Scene3D` here is deliberately a throwaway sketch of the eventual `pipeline/scene3d.py` —
enough to judge whether projected-2.5D holds its didactic value on paper before we commit.

    python -m tools.plane3d_specimen        # -> runs/plane3d_*.png  (+ _bw greyscale)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from sympy import Plane, Point3D, Rational, ilcm  # noqa: E402

from teachersaid.config import RUNS_DIR  # noqa: E402
from teachersaid.pipeline import figstyle as fs  # noqa: E402
from teachersaid.pipeline.scene import (Canvas, Label, Line, PointMark, Polyline,  # noqa: E402
                                        Region, Scene, render_scene, scene_to_png)

P3 = tuple[float, float, float]

# --- the projection: one fixed linear map ℝ³ → ℝ² (a Schrägbild) -------------
# Columns are the screen images of the unit axes x̂, ŷ, ẑ. The SAME linear map is applied
# to every point, so it is a consistent parallel projection — exactly what a textbook draws
# on the board. These six numbers are the only "camera" dial. Two conventions to compare:
#
#   AXO_34       a general axonometric 3/4 view (depth axis receding to the lower-left).
#   SCHRAEGRISS  the strict Austrian Schrägriss (Kabinettprojektion): ŷ horizontal, ẑ
#                vertical, x̂ (the receding depth axis) at 45° lower-left, foreshortened ½.
AXO_34 = {
    "x": np.array([-0.80, -0.40]),
    "y": np.array([0.96, -0.18]),
    "z": np.array([0.00, 1.00]),
}
_S = 0.5 * math.cos(math.radians(45))
SCHRAEGRISS = {
    "x": np.array([-_S, -_S]),
    "y": np.array([1.00, 0.00]),
    "z": np.array([0.00, 1.00]),
}
_ACTIVE = {"axo": AXO_34}


def use_projection(axo: dict) -> None:
    """Swap the active projection (all builders read it via `project`)."""
    _ACTIVE["axo"] = axo


def project(p) -> tuple[float, float]:
    axo = _ACTIVE["axo"]
    x, y, z = float(p[0]), float(p[1]), float(p[2])
    v = x * axo["x"] + y * axo["y"] + z * axo["z"]
    return (float(v[0]), float(v[1]))


# --- occlusion: hidden-line determination against analytic surfaces ----------
# Parallel projection ⇒ the projection rays are ONE fixed 3D direction (the null vector of
# the 2×3 AXO matrix). "In front" is a global sort along it; visibility of a curve point is a
# closed-form ray/surface test. One write-once predicate per surface TYPE (cone, plane,
# sphere…), then a generic curve-splitter — not case-by-case per figure.
def view_direction() -> np.ndarray:
    """The 3D direction the projection collapses (points differing along it overlap on
    screen), oriented toward the above-front camera."""
    axo = _ACTIVE["axo"]
    r1 = np.array([axo["x"][0], axo["y"][0], axo["z"][0]])
    r2 = np.array([axo["x"][1], axo["y"][1], axo["z"][1]])
    d = np.cross(r1, r2)
    d = d / (np.linalg.norm(d) or 1.0)
    return -d if d[2] < 0 else d


def _quad_roots(a: float, b: float, c: float) -> list:
    if abs(a) < 1e-12:
        return [] if abs(b) < 1e-12 else [-c / b]
    disc = b * b - 4 * a * c
    if disc < 0:
        return []
    s = math.sqrt(disc)
    return [(-b - s) / (2 * a), (-b + s) / (2 * a)]


def cone_occluder(k: float, zmax: float, zmin: float = 0.0, eps: float = 1e-3):
    """Predicate: is point P hidden behind the cone x²+y²=(k·z)², zmin≤z≤zmax, seen along d?
    Cast the ray P + t·d toward the camera (t>eps); a hit inside the finite nappe(s) occludes.
    zmin=-zmax gives the DOUBLE cone (both nappes), needed for the hyperbola."""
    def hidden(P, d) -> bool:
        px, py, pz = P
        dx, dy, dz = d
        a = dx * dx + dy * dy - k * k * dz * dz
        b = 2 * (px * dx + py * dy - k * k * pz * dz)
        c = px * px + py * py - k * k * pz * pz
        for t in _quad_roots(a, b, c):
            if t > eps and zmin - eps <= (pz + t * dz) <= zmax + eps:
                return True
        return False
    return hidden


def split_visibility(pts: list, occluders: list, d: np.ndarray) -> list:
    """Split a sampled curve into contiguous (visible: bool, run_pts) segments. For a closed
    curve, rotate to a visibility boundary first so no run is severed at the seam."""
    vis = [not any(occ(p, d) for occ in occluders) for p in pts]
    if any(vis[i] != vis[i - 1] for i in range(len(vis))):
        b0 = next(i for i in range(len(vis)) if vis[i] != vis[i - 1])
        pts, vis = pts[b0:] + pts[:b0], vis[b0:] + vis[:b0]
    runs, i, n = [], 0, len(pts)
    while i < n:
        j = i
        while j + 1 < n and vis[j + 1] == vis[i]:
            j += 1
        runs.append((vis[i], pts[i:j + 1]))
        i = j + 1
    return runs


# --- a tiny 3D scene vocabulary (projects into the existing 2D primitives) ----
@dataclass
class Seg3:
    a: P3; b: P3; role: str = "ink"; width: float = 1.3; dash: object = "solid"; z: int = 3


@dataclass
class Path3:
    pts: list; role: str = "ink"; width: float = 2.0; dash: object = "solid"
    closed: bool = False; z: int = 4


@dataclass
class Patch3:
    """A bounded piece of a plane — a translucent fill + a (dash-coded) boundary, so two
    planes stay distinguishable in a black-and-white photocopy."""
    corners: list; color: str = "primary"; alpha: float = 0.26
    dash: object = "solid"; z: int = 2


@dataclass
class Fill3:
    """A filled polygon with no boundary — a soft body fill (e.g. the cone silhouette)."""
    corners: list; color: str = "surface"; alpha: float = 0.14; z: int = 1


@dataclass
class Arrow3:
    a: P3; b: P3; role: str = "focus"; width: float = 1.9
    label: str | None = None; label_role: str | None = None; z: int = 6


@dataclass
class Dot3:
    p: P3; label: str | None = None; role: str = "ink"
    off: tuple = (0.14, 0.16); z: int = 6


@dataclass
class Text3:
    p: P3; text: str; role: str = "ink"; size: float = 10.0; bold: bool = False; z: int = 7


def _arrowhead(pa2, pb2, size=0.26, half=0.12) -> list:
    d = np.array(pb2) - np.array(pa2)
    L = float(np.hypot(*d))
    if L < 1e-9:
        return []
    d /= L
    perp = np.array([-d[1], d[0]])
    back = np.array(pb2) - size * d
    h1, h2 = back + half * perp, back - half * perp
    return [(tuple(pb2), tuple(h1)), (tuple(pb2), tuple(h2))]


def to_scene(items: list, *, title: str | None = None, pad: float = 0.6) -> Scene:
    """Project every 3D item and emit the flat 2D `Scene` the existing renderer draws."""
    layers: list = []
    xs: list[float] = []
    ys: list[float] = []

    def note(*pts2):
        for (px, py) in pts2:
            xs.append(px)
            ys.append(py)

    for it in items:
        if isinstance(it, Seg3):
            a, b = project(it.a), project(it.b)
            layers.append(Line(a, b, role=it.role, width=it.width, dash=it.dash, z=it.z))
            note(a, b)
        elif isinstance(it, Path3):
            pts = [project(p) for p in it.pts]
            layers.append(Polyline(pts, role=it.role, width=it.width, dash=it.dash,
                                   closed=it.closed, z=it.z))
            note(*pts)
        elif isinstance(it, Patch3):
            pts = [project(p) for p in it.corners]
            layers.append(Region(pts, role=it.color, alpha=it.alpha, z=it.z))
            layers.append(Polyline(pts, role=it.color, width=1.4, dash=it.dash,
                                   closed=True, z=it.z + 1))
            note(*pts)
        elif isinstance(it, Fill3):
            pts = [project(p) for p in it.corners]
            layers.append(Region(pts, role=it.color, alpha=it.alpha, z=it.z))
            note(*pts)
        elif isinstance(it, Arrow3):
            a, b = project(it.a), project(it.b)
            layers.append(Line(a, b, role=it.role, width=it.width, z=it.z))
            for (t, h) in _arrowhead(a, b):
                layers.append(Line(t, h, role=it.role, width=it.width, z=it.z))
            if it.label:
                d = np.array(b) - np.array(a)
                d = d / (np.hypot(*d) or 1.0)
                lp = (b[0] + 0.28 * d[0] + 0.12, b[1] + 0.28 * d[1] + 0.06)
                layers.append(Label(lp, it.label, role=it.label_role or it.role,
                                    size=fs.TYPE.annot_lg, bold=True, z=it.z + 1))
            note(a, b)
        elif isinstance(it, Dot3):
            a = project(it.p)
            layers.append(PointMark(a, label=it.label, role=it.role, size=5.5,
                                    label_offset=it.off, bold=True, z=it.z))
            note(a)
        elif isinstance(it, Text3):
            a = project(it.p)
            layers.append(Label(a, it.text, role=it.role, size=it.size, bold=it.bold, z=it.z))
            note(a)

    canvas = Canvas(figsize=(5.8, 5.2), aspect="equal", frame="off",
                    xlim=(min(xs) - pad, max(xs) + pad),
                    ylim=(min(ys) - pad, max(ys) + pad), title=title)
    return Scene(canvas=canvas, layers=layers)


# --- shared scaffolding: coordinate frame + ground grid ----------------------
def coord_frame(length: float = 4.2) -> list:
    items: list = []
    for axis, lab in (("x", "x"), ("y", "y"), ("z", "z")):
        tip = tuple((length if k == axis else 0.0) for k in ("x", "y", "z"))
        items.append(Arrow3((0, 0, 0), tip, role="muted", width=1.1,
                            label=f"${lab}$", label_role="muted", z=3))
    return items


def ground_grid(lo: int = -1, hi: int = 4) -> list:
    grid: list = []
    for x in range(lo, hi + 1):
        grid.append(Seg3((x, lo, 0), (x, hi, 0), role="grid", width=0.7, z=0))
    for y in range(lo, hi + 1):
        grid.append(Seg3((lo, y, 0), (hi, y, 0), role="grid", width=0.7, z=0))
    return grid


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) or 1.0)


def _in_plane_basis(n) -> tuple[np.ndarray, np.ndarray]:
    """Two orthonormal directions spanning the plane with normal n (derived from n)."""
    n = _unit(n)
    ref = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = _unit(np.cross(n, ref))
    v = _unit(np.cross(n, u))
    return u, v


# --- Figure A: a plane built from its normal vector --------------------------
def scene_plane_normal() -> Scene:
    A = (1.4, 1.4, 1.1)          # a point on the plane
    n = (1.0, 1.0, 2.0)          # its normal vector
    E = Plane(Point3D(*A), normal_vector=n)   # sympy owns the geometry
    nn = _unit([float(c) for c in E.normal_vector])
    u, v = _in_plane_basis(nn)
    c = np.array(A, float)
    s = 1.9
    corners = [c + s * u + s * v, c - s * u + s * v, c - s * u - s * v, c + s * u - s * v]

    items: list = []
    items += ground_grid(-1, 4)
    items += coord_frame(4.2)
    items.append(Patch3([tuple(p) for p in corners], color="primary", alpha=0.24, z=2))
    # name the plane at its top-left corner (deterministic: leftmost-highest projected),
    # nudged outward so it never collides with the normal
    proj = [project(tuple(p)) for p in corners]
    kE = min(range(4), key=lambda i: proj[i][0] - proj[i][1])
    e_pt = np.array(corners[kE]) + 0.35 * _unit(np.array(corners[kE]) - c)
    items.append(Text3(tuple(e_pt), "$E$", role="primary", size=13, bold=True, z=7))
    # the normal, from the anchor point
    tip = c + 2.1 * nn
    items.append(Arrow3(tuple(c), tuple(tip), role="focus", width=2.1,
                        label=r"$\vec n$", z=6))
    # a right-angle marker: n ⟂ (a direction in E)
    r = 0.42
    items.append(Path3([tuple(c + r * u), tuple(c + r * u + r * nn), tuple(c + r * nn)],
                       role="muted", width=1.1, z=5))
    items.append(Dot3(A, label="$A$", role="ink", off=(-0.22, -0.26), z=6))
    return to_scene(items, title="Ebene aus ihrem Normalvektor  (Normalvektorform)")


# --- Figure B: the intersection line of two planes ---------------------------
def scene_two_planes() -> Scene:
    A1, n1 = (0, 0, 1), (1, 0, 1)     # E1: x + z = 1
    A2, n2 = (0, 0, 1), (0, 1, 1)     # E2: y + z = 1
    E = Plane(Point3D(*A1), normal_vector=n1)
    F = Plane(Point3D(*A2), normal_vector=n2)
    g = E.intersection(F)[0]                       # the Schnittgerade (sympy → a Line3D)
    phi = math.degrees(float(E.angle_between(F)))  # the enclosed angle (computed)

    d = _unit([float(c) for c in g.direction_ratio])
    p0 = np.array([float(c) for c in g.p1], float)
    cm = p0 + float(np.dot(np.array([0.5, 0.5, 0.5]) - p0, d)) * d   # a central point on g

    def patch(n):                                  # a plane piece straddling the crease
        vv = _unit(np.cross(n, d))
        Ld, Wv = 2.4, 2.1
        return [cm - Ld * d - Wv * vv, cm + Ld * d - Wv * vv,
                cm + Ld * d + Wv * vv, cm - Ld * d + Wv * vv]

    items: list = []
    items += ground_grid(-1, 3)
    items += coord_frame(3.4)
    items.append(Patch3([tuple(p) for p in patch(n1)], color="primary", alpha=0.22,
                        dash="solid", z=2))
    items.append(Patch3([tuple(p) for p in patch(n2)], color=fs.CATEGORICAL[2], alpha=0.22,
                        dash=(0, (5, 3)), z=2))
    items.append(Text3(tuple(cm - 2.0 * _unit(np.cross(n1, d)) - 1.0 * d), "$E_1$",
                       role="primary", size=12, bold=True, z=7))
    items.append(Text3(tuple(cm + 2.0 * _unit(np.cross(n2, d)) - 1.0 * d), "$E_2$",
                       role=fs.darken(fs.CATEGORICAL[2], 0.15), size=12, bold=True, z=7))
    # the Schnittgerade — the element of interest (focus), drawn last / on top
    ga, gb = cm - 2.9 * d, cm + 2.9 * d
    items.append(Path3([tuple(ga), tuple(gb)], role="focus", width=2.6, z=6))
    items.append(Text3(tuple(gb + 0.25 * d), "$g$", role="focus", size=13, bold=True, z=7))
    items.append(Text3(tuple(cm + 0.15 * d + np.array([0, 0, 0.55])),
                       f"φ ≈ {phi:.0f}°", role="ink", size=10, z=7))
    return to_scene(items, title="Schnitt zweier Ebenen — die Schnittgerade g")


# --- Figure C: a Kegelschnitt — a cone sliced by a plane ---------------------
def scene_cone_section() -> Scene:
    """The literal Kegelschnitt: a plane cuts a cone, and the section is an ELLIPSE whose
    shape is computed from the two equations (correct-by-construction). Cone x²+y²=(k·z)²
    (apex at O, opening up); cutting plane z = c + m·y (an ellipse iff |m| < 1/k). Substituting
    the plane into the cone gives A·x² + B·y² + D·y + F = 0, solved here for the ellipse's
    centre and semi-axes, sampled, lifted back to 3D, and projected."""
    k, zmax = 0.62, 3.4          # cone: tan(half-angle), height
    m, c = 0.35, 1.7             # cutting plane z = c + m·y  (gentle tilt → open ellipse)

    B = 1.0 - k * k * m * m      # cone ∩ plane → A x² + B y² + D y + F = 0  (A = 1)
    D = -2.0 * k * k * c * m
    F = -k * k * c * c
    y0 = -D / (2 * B)                                   # ellipse centre (in y)
    rhs = -F + B * y0 * y0
    axs, ays = math.sqrt(rhs), math.sqrt(rhs / B)      # semi-axes in x, y
    ts = np.linspace(0, 2 * math.pi, 240, endpoint=False)
    section = [(axs * math.cos(t), y0 + ays * math.sin(t),
                c + m * (y0 + ays * math.sin(t))) for t in ts]

    R = k * zmax                                        # rim circle at the top
    rim = [(R * math.cos(s), R * math.sin(s), zmax)
           for s in np.linspace(0, 2 * math.pi, 120)]
    rp = [project(p) for p in rim]
    iL = min(range(len(rim)), key=lambda i: rp[i][0])  # silhouette generators = the
    iR = max(range(len(rim)), key=lambda i: rp[i][0])  # extreme-x rim points

    items: list = []
    items += ground_grid(-2, 2)
    items += coord_frame(3.9)
    items.append(Fill3([(0, 0, 0)] + rim, color="muted", alpha=0.12, z=1))     # cone body
    items.append(Path3(rim, role="muted", width=1.2, closed=True, z=2))        # rim
    items.append(Seg3((0, 0, 0), rim[iL], role="muted", width=1.3, z=2))       # generators
    items.append(Seg3((0, 0, 0), rim[iR], role="muted", width=1.3, z=2))
    items.append(Text3(rim[iR], "Kegel", role="muted", size=9.5, z=3))
    # the cutting plane ε
    cen = np.array([0.0, y0, c + m * y0])
    ex, ey = np.array([1.0, 0, 0]), _unit(np.array([0, 1.0, m]))
    corners = [cen + 2.3 * ex + 2.3 * ey, cen - 2.3 * ex + 2.3 * ey,
               cen - 2.3 * ex - 2.3 * ey, cen + 2.3 * ex - 2.3 * ey]
    items.append(Patch3([tuple(p) for p in corners], color="primary", alpha=0.15, z=3))
    items.append(Text3(tuple(cen - 2.3 * ex + 2.3 * ey), "ε", role="primary", size=13,
                       bold=True, z=7))
    # the section curve — the Kegelschnitt itself; its BACK half is hidden behind the
    # cone's near wall, computed by ray-casting each sample against the cone (hidden→dashed)
    d = view_direction()
    for visible, run in split_visibility(section, [cone_occluder(k, zmax)], d):
        if len(run) < 2:
            continue
        if visible:
            items.append(Path3(run, role="focus", width=2.8, z=6))
        else:
            items.append(Path3(run, role="focus", width=1.5, dash=(0, (3, 3)), z=6))
    # label just outside the ellipse on its left, so it never sits on the curve
    ctr = np.array([0.0, y0, c + m * y0])
    sp = [project(p) for p in section]
    iLbl = min(range(len(section)), key=lambda i: sp[i][0])
    lbl = np.array(section[iLbl]) + 0.8 * _unit(np.array(section[iLbl]) - ctr)
    items.append(Text3(tuple(lbl), "Ellipse", role="focus", size=12, bold=True, z=7))
    return to_scene(items, title="Kegelschnitt:  Kegel ∩ Ebene ε  =  Ellipse")


# --- Figure D: the three Kegelschnitte from one cone -------------------------
def double_cone_items(k: float, zmax: float) -> list:
    """A double cone (both nappes, apex at O) as light fill + rims + silhouette generators."""
    R = k * zmax

    def rim(z):
        return [(R * math.cos(s), R * math.sin(s), z)
                for s in np.linspace(0, 2 * math.pi, 120)]

    items: list = []
    for z in (zmax, -zmax):
        r = rim(z)
        items.append(Fill3([(0, 0, 0)] + r, color="muted", alpha=0.10, z=1))
        items.append(Path3(r, role="muted", width=1.1, closed=True, z=2))
        rp = [project(p) for p in r]
        for pick in (min, max):
            i = pick(range(len(r)), key=lambda j: rp[j][0])
            items.append(Seg3((0, 0, 0), r[i], role="muted", width=1.2, z=2))
    return items


def cone_section_curve(k, m, c, zmax, zmin=0.0, n=420) -> list:
    """The cone ∩ plane {z=c+m·y}, solved as x² = A·y² + B·y + C and sampled by y. Returns a
    list of curves (1 closed loop = ellipse; 1 open arc = parabola; 2 branches = hyperbola),
    each computed — the SAME machinery, the conic TYPE decided by sign(A) = sign(k²m²−1)."""
    A, B, C = k * k * m * m - 1.0, 2 * k * k * c * m, k * k * c * c
    ylo, yhi = sorted(((zmin - c) / m, (zmax - c) / m))
    runs, cur = [], []
    for y in np.linspace(ylo, yhi, n):
        if A * y * y + B * y + C >= 0:
            cur.append(float(y))
        elif len(cur) > 1:
            runs.append(cur); cur = []
    if len(cur) > 1:
        runs.append(cur)
    curves = []
    for ys in runs:
        top = [(math.sqrt(max(0.0, A * y * y + B * y + C)), y, c + m * y) for y in ys]
        bot = [(-x, y, z) for (x, y, z) in reversed(top)]
        curves.append(top + bot)
    return curves


def scene_cone_conic(kind: str) -> Scene:
    """One double cone, one cutting plane whose tilt m decides the conic: |m|<1/k ellipse,
    m=1/k parabola, |m|>1/k hyperbola. Section computed + occluded against the cone."""
    k, zmax = 0.6, 3.2
    m, c, zmin = {"ellipse": (0.35, 1.7, 0.0),
                  "parabola": (1.0 / k, 1.4, 0.0),
                  "hyperbola": (2.4, 0.5, -zmax)}[kind]
    curves = cone_section_curve(k, m, c, zmax, zmin)

    items = double_cone_items(k, zmax)
    pts = [p for cv in curves for p in cv]
    cen = np.mean(np.array(pts), axis=0)
    ex, ey = np.array([1.0, 0, 0]), _unit(np.array([0, 1.0, m]))
    sx = max(abs(p[0]) for p in pts) + 0.9
    sy = max(abs(float(np.dot(np.array(p) - cen, ey))) for p in pts) + 0.9
    corners = [cen + sx * ex + sy * ey, cen - sx * ex + sy * ey,
               cen - sx * ex - sy * ey, cen + sx * ex - sy * ey]
    items.append(Patch3([tuple(p) for p in corners], color="primary", alpha=0.13, z=3))
    # the section curve(s), hidden arcs dashed (occluded by the double cone)
    d = view_direction()
    occ = [cone_occluder(k, zmax, zmin)]
    for curve in curves:
        for visible, run in split_visibility(curve, occ, d):
            if len(run) < 2:
                continue
            items.append(Path3(run, role="focus", width=2.6 if visible else 1.4,
                               dash="solid" if visible else (0, (3, 3)), z=6))
    return to_scene(items, pad=0.5)


# --- Figure E: the 2D conic-plus-tangent (the working representation) ---------
def scene_ellipse_tangent(show_equation: bool = True) -> Scene:
    """The Kl. 7 task surface: an ellipse in the coordinate plane + the tangent at a point P,
    with the tangent equation COMPUTED (cleared to integers via sympy Rational). Pure 2D — it
    drops straight into the EXISTING scene engine, no 3D machinery. Maskable (show_equation)."""
    a, b = 4.0, 2.5
    x0, y0 = 2.4, 2.0                     # a rational point ON the ellipse: (0.6)²+(0.8)²=1
    ct, st = x0 / a, y0 / b               # tangent dir from d/dt (a cosθ, b sinθ)
    tdir = _unit(np.array([-a * st, b * ct]))
    p1 = (x0 - 3.4 * tdir[0], y0 - 3.4 * tdir[1])
    p2 = (x0 + 3.4 * tdir[0], y0 + 3.4 * tdir[1])
    ell = [(a * math.cos(t), b * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 240)]
    cf = math.sqrt(a * a - b * b)         # foci — the ellipse's defining points

    sc = Scene(canvas=Canvas(figsize=(5.9, 4.9), aspect="equal", frame="center", grid=True,
                             xlim=(-a - 1.8, a + 2.1), ylim=(-b - 1.8, b + 2.1),
                             title="Ellipse mit Tangente im Punkt P"))
    sc.add(Polyline(ell, role="primary", width=2.3, closed=True, z=4))
    sc.add(PointMark((cf, 0), label="$F_2$", role="muted", size=3.5,
                     label_offset=(0.12, -0.5), bold=False, z=5),
           PointMark((-cf, 0), label="$F_1$", role="muted", size=3.5,
                     label_offset=(-0.12, -0.5), bold=False, z=5))
    sc.add(Line(p1, p2, role="focus", width=2.0, z=5))
    sc.add(PointMark((x0, y0), label="$P$", role="focus", size=6,
                     label_offset=(0.4, 0.35), bold=True, z=6))
    if show_equation:                     # tangent x·x₀/a² + y·y₀/b² = 1, cleared to integers
        cx, cy = Rational(str(x0)) / Rational(str(a)) ** 2, Rational(str(y0)) / Rational(str(b)) ** 2
        den = ilcm(cx.q, cy.q)
        eqtxt = f"t:  {cx * den}x + {cy * den}y = {den}"
    else:
        eqtxt = "t:  ?"
    sc.add(Label((-a - 1.5, b + 1.4), eqtxt, role="focus", size=11.5, bold=True, ha="left", z=7))
    sc.add(Label((a + 1.7, -b - 1.1), r"$\frac{x^2}{16}+\frac{y^2}{6{,}25}=1$", role="primary",
                 size=11, ha="right", z=7))
    return sc


# --- render (colour + greyscale) + a contact sheet ---------------------------
def _greyscale(png: Path) -> Path:
    out = png.with_name(png.stem + "_bw.png")
    Image.open(png).convert("L").save(out)
    return out


def _contact_sheet(pairs: list[tuple[Path, Path]], out: Path) -> Path:
    cols = [Image.open(c).convert("RGB") for c, _ in pairs]
    bws = [Image.open(b).convert("RGB") for _, b in pairs]
    w = max(im.width for im in cols + bws)
    h = max(im.height for im in cols + bws)
    sheet = Image.new("RGB", (w * 2, h * len(pairs)), "white")
    for i, (cim, bim) in enumerate(zip(cols, bws)):
        sheet.paste(cim, (0, i * h))
        sheet.paste(bim, (w, i * h))
    sheet.save(out)
    return out


def _render(builder, name: str, dpi: int = 170) -> None:
    col = scene_to_png(builder(), RUNS_DIR / f"{name}.png", dpi=dpi)
    bw = _greyscale(col)
    print("wrote", col.name, "+", bw.name)


def render_triptych(path: Path, dpi: int = 150) -> None:
    """The three Kegelschnitte as ONE worksheet figure: one cone, three cutting planes.
    Rendered in the 3/4 view (cones read better with depth than in a strict Schrägriss)."""
    use_projection(AXO_34)
    panels = [("Ellipse", scene_cone_conic("ellipse")),
              ("Parabel", scene_cone_conic("parabola")),
              ("Hyperbel", scene_cone_conic("hyperbola"))]
    # a COMMON view box from the cone, so all three cones render identically sized (the
    # planes just run to the frame edge — they're infinite anyway)
    R = 0.6 * 3.2
    box = [project((R * math.cos(s), R * math.sin(s), z))
           for z in (3.2, -3.2) for s in np.linspace(0, 2 * math.pi, 60)]
    bx, by = [p[0] for p in box], [p[1] for p in box]
    px, py = (max(bx) - min(bx)) * 0.16, (max(by) - min(by)) * 0.06
    for _, scene in panels:
        scene.canvas.xlim = (min(bx) - px, max(bx) + px)
        scene.canvas.ylim = (min(by) - py, max(by) + py)
    with plt.rc_context(fs.house_rc()):
        fig, axes = plt.subplots(1, 3, figsize=(13.8, 5.0))
        for ax, (name, scene) in zip(axes, panels):
            render_scene(scene, ax)
            ax.set_title(name, fontsize=fs.TYPE.title, color=fs.PALETTE.ink)
        fig.suptitle("Die drei Kegelschnitte — ein Kegel, drei Schnittebenen ε",
                     fontsize=fs.TYPE.title + 2, color=fs.PALETTE.ink, y=0.99)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
    _greyscale(path)
    print("wrote", path.name)


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    planes = [("plane3d_normal", scene_plane_normal),
              ("plane3d_intersection", scene_two_planes)]
    use_projection(AXO_34)                       # the 3/4 view (for comparison)
    for name, builder in planes:
        _render(builder, name)
    use_projection(SCHRAEGRISS)                  # the strict Schrägriss (house default)
    for name, builder in planes:
        _render(builder, name + "_schraeg")
    use_projection(AXO_34)                        # the standalone (detailed) Kegelschnitt
    _render(scene_cone_section, "kegelschnitt_ellipse")
    render_triptych(RUNS_DIR / "kegelschnitte_drei.png")      # the 3-conic worksheet figure
    _render(scene_ellipse_tangent, "ellipse_tangente_2d")     # the 2D working representation


if __name__ == "__main__":
    main()
