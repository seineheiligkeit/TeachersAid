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

import numpy as np
from PIL import Image
from sympy import Plane, Point3D

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.scene import (Canvas, Label, Line, PointMark, Polyline,
                                        Region, Scene, scene_to_png)

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
    ts = np.linspace(0, 2 * math.pi, 200)
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
    # the section curve — the Kegelschnitt itself (focus, on top)
    items.append(Path3(section, role="focus", width=2.8, closed=True, z=6))
    # label just outside the ellipse on its left, so it never sits on the curve
    ctr = np.array([0.0, y0, c + m * y0])
    sp = [project(p) for p in section]
    iLbl = min(range(len(section)), key=lambda i: sp[i][0])
    lbl = np.array(section[iLbl]) + 0.8 * _unit(np.array(section[iLbl]) - ctr)
    items.append(Text3(tuple(lbl), "Ellipse", role="focus", size=12, bold=True, z=7))
    return to_scene(items, title="Kegelschnitt:  Kegel ∩ Ebene ε  =  Ellipse")


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


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    planes = [("plane3d_normal", scene_plane_normal),
              ("plane3d_intersection", scene_two_planes)]
    use_projection(AXO_34)                       # the 3/4 view (for comparison)
    for name, builder in planes:
        _render(builder, name)
    use_projection(SCHRAEGRISS)                  # the strict Schrägriss
    for name, builder in planes:
        _render(builder, name + "_schraeg")
    use_projection(AXO_34)                        # the Kegelschnitt
    _render(scene_cone_section, "kegelschnitt_ellipse")


if __name__ == "__main__":
    main()
