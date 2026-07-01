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

# --- the projection: one fixed axonometric map ℝ³ → ℝ² (a Schrägbild) --------
# Columns are the screen images of the unit axes x̂, ŷ, ẑ. The SAME linear map is applied
# to every point, so it is a consistent parallel projection — exactly what a textbook draws
# on the board. These six numbers are the only "camera" dial; tuned for a 3/4 view from
# the upper front-left (depth axis receding to the lower-left).
AXO = {
    "x": np.array([-0.80, -0.40]),   # x̂ recedes to the lower-left (the depth axis)
    "y": np.array([0.96, -0.18]),    # ŷ to the right, slightly down
    "z": np.array([0.00, 1.00]),     # ẑ straight up
}


def project(p) -> tuple[float, float]:
    x, y, z = float(p[0]), float(p[1]), float(p[2])
    v = x * AXO["x"] + y * AXO["y"] + z * AXO["z"]
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


def main() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    pairs = []
    for name, builder in (("plane3d_normal", scene_plane_normal),
                          ("plane3d_intersection", scene_two_planes)):
        col = scene_to_png(builder(), RUNS_DIR / f"{name}.png", dpi=170)
        bw = _greyscale(col)
        pairs.append((col, bw))
        print("wrote", col, "and", bw)
    sheet = _contact_sheet(pairs, RUNS_DIR / "plane3d_contact.png")
    print("contact sheet:", sheet)


if __name__ == "__main__":
    main()
