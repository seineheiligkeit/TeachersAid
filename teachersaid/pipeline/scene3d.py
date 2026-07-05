"""3D solids as projected 2D scenes — the promoted Schrägbild engine (roadmap A7).

The validated prototype (`tools/plane3d_specimen.py`) proved the load-bearing idea: **model a
situation in ℝ³, project it through one fixed parallel map ℝ³→ℝ², and emit ordinary 2D `scene`
primitives** — so the entire existing renderer (`scene.render_scene`) + styleguide (`figstyle`:
semantic roles, halos, the photocopy-safe dash ramp) is reused unchanged. No `mplot3d`, nothing
interactive: a print-first Schrägbild, the way an AHS textbook draws it. See
`Documents/scene3d-geometry-design.md` (the design record + the occlusion boundary).

This module promotes that machinery into the package and adds the two didactic recipes the GZ
(Geometrisches Zeichnen, US) / DG (Darstellende Geometrie, OS) curriculum needs first — a subject
with zero coverage getting its engine:

* **`axonometric_solid_scene`** — the Schrägriss (Austrian Kabinettprojektion) of the school solids
  (Quader, right prisms, pyramids, Drehzylinder, Drehkegel), **hidden edges dashed** via a
  closed-form back-face test; maskable dimension labels ("h = ?").
* **`riss_pair_scene`** — a Grund-/Aufriss pair (top + front orthographic view) side by side, with
  the Rissachse and Ordnungslinien, at a consistent shared measurement scale.

**Two-tier, like everywhere else** (`GenDataFigure → choose_representation`, the calculus recipes):
the LLM never authors a Scene (it could draw a wrong hidden edge or leak a measurement). A
*didactic recipe COMPUTES* the scene from a small, correct-by-construction spec — the solid's
vertices/faces are generated from a handful of parameters (Kantenlänge, Radius, Höhe), the
projection is one fixed linear map, and edge visibility is a **computed** predicate, never drawn to
look right. The `@_generator` wrappers in `assets.py` are the engine's request surface.

Correct-by-construction, print-first, greyscale-robust. Pure: imports only the scene primitives +
figstyle + numpy (sympy is used only where an exact rational is wanted; the school solids need
none). No matplotlib here — `scene_to_png` in the wrapper renders.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import figstyle as fs
from .scene import Canvas, Label, Line, PointMark, Polyline, Region, Scene

P3 = tuple[float, float, float]


# --- the projection: one fixed linear map ℝ³ → ℝ² (a Schrägbild) --------------
# The columns are the screen images of the unit axes x̂, ŷ, ẑ; the SAME linear map applied to
# every point ⇒ a consistent parallel projection — exactly what a textbook draws on the board.
# Two conventions:
#   SCHRAEGRISS  the strict Austrian Schrägriss (Kabinettprojektion) and the HOUSE DEFAULT
#                (SME preference): ŷ horizontal, ẑ vertical, x̂ (the receding depth axis) at 45°
#                lower-left, foreshortened ½ — coordinate-reading is easy; it is what students see.
#   AXO_34       a general 3/4 axonometric view (nothing axis-aligned); reads more "spatial".
_S = 0.5 * math.cos(math.radians(45))          # ½-foreshortened depth at 45° = the cabinet factor
SCHRAEGRISS: dict[str, np.ndarray] = {
    "x": np.array([-_S, -_S]),
    "y": np.array([1.00, 0.00]),
    "z": np.array([0.00, 1.00]),
}
AXO_34: dict[str, np.ndarray] = {
    "x": np.array([-0.80, -0.40]),
    "y": np.array([0.96, -0.18]),
    "z": np.array([0.00, 1.00]),
}


def project(p, axo: dict[str, np.ndarray] = SCHRAEGRISS) -> tuple[float, float]:
    """Project a 3D point through the fixed linear map (Schrägriss by default). The projection is a
    parameter, not a global — a recipe passes the one it wants (no hidden mutable state)."""
    x, y, z = float(p[0]), float(p[1]), float(p[2])
    v = x * axo["x"] + y * axo["y"] + z * axo["z"]
    return (float(v[0]), float(v[1]))


def view_direction(axo: dict[str, np.ndarray] = SCHRAEGRISS) -> np.ndarray:
    """The 3D direction the projection collapses — points differing along it overlap on screen.
    Under a parallel projection this is the null vector of the 2×3 projection matrix (the cross
    product of its two rows), oriented toward the above-front camera (positive z)."""
    r1 = np.array([axo["x"][0], axo["y"][0], axo["z"][0]])
    r2 = np.array([axo["x"][1], axo["y"][1], axo["z"][1]])
    d = np.cross(r1, r2)
    d = d / (np.linalg.norm(d) or 1.0)
    return -d if d[2] < 0 else d


# --- the solid: vertices + faces, correct-by-construction from a few parameters -----
@dataclass
class Solid:
    """A convex solid in ℝ³: `verts` (Nx3) + `faces` (each a tuple of vertex indices, ordered so
    the polygon winds counter-clockwise seen from OUTSIDE — the outward normal follows the
    right-hand rule). `smooth_faces` names faces whose boundary is a sampled curve (a cylinder/cone
    lateral surface): they are drawn as a silhouette, not as edges. `apex` (if set) is the index of
    a cone's apex — the tip, treated as a single generator anchor.

    Convexity is the load-bearing precondition for the closed-form hidden-line test (see
    `hidden_edges`); the school-solid builders below only produce convex solids."""
    verts: np.ndarray                                   # (N, 3)
    faces: list[tuple[int, ...]]                         # CCW-from-outside index polygons
    smooth_faces: set[int] = field(default_factory=set)  # indices into `faces` that are curved
    apex: int | None = None                             # a cone's apex vertex index
    kind: str = "polyhedron"                             # for messaging/recipes


def _ring(cx: float, cy: float, r: float, z: float, n: int, phase: float = 0.0) -> np.ndarray:
    """n points on a circle of radius r at height z, centred (cx, cy)."""
    return np.array([(cx + r * math.cos(2 * math.pi * i / n + phase),
                      cy + r * math.sin(2 * math.pi * i / n + phase), z) for i in range(n)])


def quader(a: float = 4.0, b: float = 3.0, c: float = 2.5) -> Solid:
    """A right rectangular box (Quader / Würfel when a=b=c), one corner at the origin, edges along
    the axes. 8 vertices, 6 quad faces with outward CCW winding."""
    v = np.array([[0, 0, 0], [a, 0, 0], [a, b, 0], [0, b, 0],
                  [0, 0, c], [a, 0, c], [a, b, c], [0, b, c]], float)
    faces = [
        (0, 3, 2, 1),   # bottom  (z-), CCW seen from below  → outward normal -z
        (4, 5, 6, 7),   # top     (z+)
        (0, 1, 5, 4),   # front   (y-)
        (2, 3, 7, 6),   # back    (y+)
        (1, 2, 6, 5),   # right   (x+)
        (3, 0, 4, 7),   # left    (x-)
    ]
    return Solid(verts=v, faces=faces, kind="quader")


def prism(n: int = 6, r: float = 2.2, h: float = 3.5) -> Solid:
    """A right regular prism with an n-gon base (n=3 triangular, n=6 hexagonal), base centred at the
    origin in z=0, top at z=h. 2n vertices, 2 n-gon caps + n rectangular sides."""
    n = int(n)
    bot = _ring(0, 0, r, 0.0, n)
    top = _ring(0, 0, r, h, n)
    v = np.vstack([bot, top])
    faces: list[tuple[int, ...]] = [tuple(range(n - 1, -1, -1))]   # bottom cap (z-), CW→outward -z
    faces.append(tuple(range(n, 2 * n)))                           # top cap (z+), CCW
    for i in range(n):                                             # sides, outward-CCW
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return Solid(verts=v, faces=faces, kind=f"prism{n}")


def pyramid(n: int = 4, r: float = 2.4, h: float = 3.6) -> Solid:
    """A right regular pyramid: an n-gon base (n=4 square is the default school solid) centred at
    the origin in z=0, apex on the z-axis at height h. n+1 vertices, 1 base + n triangular sides."""
    n = int(n)
    base = _ring(0, 0, r, 0.0, n)
    apex_i = n
    v = np.vstack([base, np.array([[0, 0, h]])])
    faces: list[tuple[int, ...]] = [tuple(range(n - 1, -1, -1))]   # base (z-), outward -z
    for i in range(n):                                             # triangular sides
        j = (i + 1) % n
        faces.append((i, j, apex_i))
    return Solid(verts=v, faces=faces, apex=apex_i, kind=f"pyramid{n}")


def cylinder(r: float = 1.8, h: float = 3.6, n: int = 48) -> Solid:
    """A right circular cylinder (Drehzylinder), base at z=0, top at z=h. Sampled as a fine 2n-gon
    prism; the lateral surface is flagged `smooth` so it renders as a silhouette (two generators +
    the elliptical rims), not as 48 visible facet edges."""
    s = prism(n, r, h)
    s.smooth_faces = set(range(2, len(s.faces)))       # every side face is part of the curved wall
    s.kind = "cylinder"
    return s


def cone(r: float = 2.0, h: float = 3.8, n: int = 48) -> Solid:
    """A right circular cone (Drehkegel), base circle at z=0, apex on the z-axis at height h.
    Sampled as a fine n-gon pyramid; the lateral surface is flagged `smooth` → silhouette
    generators to the apex + the base rim, not n facet edges."""
    s = pyramid(n, r, h)
    s.smooth_faces = set(range(1, len(s.faces)))       # every triangular side is the curved wall
    s.kind = "cone"
    return s


_SOLID_BUILDERS = {
    "quader": quader, "wuerfel": quader, "cube": quader,
    "prism": prism, "prisma": prism,
    "pyramid": pyramid, "pyramide": pyramid,
    "cylinder": cylinder, "zylinder": cylinder,
    "cone": cone, "kegel": cone,
}


def build_solid(kind: str, **params) -> Solid:
    """Construct a school solid by name (German or English) with size parameters. Raises on an
    unknown kind (no silent wrong solid)."""
    key = str(kind).strip().lower()
    if key not in _SOLID_BUILDERS:
        raise ValueError(f"unknown solid {kind!r} — one of {sorted(set(_SOLID_BUILDERS))}")
    fn = _SOLID_BUILDERS[key]
    allowed = fn.__code__.co_varnames[:fn.__code__.co_argcount]
    return fn(**{k: v for k, v in params.items() if k in allowed})


# --- occlusion: hidden-line determination (closed form, CONVEX solids only) ---
# The design boundary (scene3d-geometry-design.md §Occlusion): crisp hidden-line dashing through
# MANY mutually-interpenetrating opaque surfaces is the classical hidden-surface problem
# (GPU-z-buffer territory) — we DON'T do it. For ONE convex polyhedron the problem is exact and
# closed-form: an edge is hidden iff BOTH faces adjacent to it face away from the camera
# (back-face culling). This is the doc's "convex-polyhedron edge visibility is classifiable
# per-face-normal" tier. It is provably correct for a convex body (a back edge is occluded by the
# front hull; a silhouette edge — one front, one back face — is visible).
def _face_normal(solid: Solid, face: tuple[int, ...]) -> np.ndarray:
    """The outward normal of a face (right-hand rule over its CCW-from-outside winding)."""
    p = solid.verts[list(face)]
    n = np.zeros(3)
    for i in range(len(p)):                            # Newell's method (robust for any polygon)
        a, b = p[i], p[(i + 1) % len(p)]
        n += np.cross(a, b)
    nn = np.linalg.norm(n)
    return n / nn if nn else n


def _is_convex(solid: Solid, eps: float = 1e-6) -> bool:
    """Every vertex lies on the inner side of (or on) every face plane — the definition of a convex
    polyhedron. Cheap (N·F) and exact enough for the handful-of-vertices school solids."""
    for face in solid.faces:
        p0 = solid.verts[face[0]]
        nrm = _face_normal(solid, face)
        # outward normal ⇒ all other vertices satisfy (v - p0)·n ≤ 0
        if np.max((solid.verts - p0) @ nrm) > eps:
            return False
    return True


def back_facing(solid: Solid, d: np.ndarray) -> list[bool]:
    """Per-face: does the face point AWAY from the camera (outward normal · view dir < 0)?"""
    return [float(_face_normal(solid, f) @ d) < -1e-9 for f in solid.faces]


def _edge_faces(solid: Solid) -> dict[tuple[int, int], list[int]]:
    """Undirected edge → the indices of the faces that share it."""
    ef: dict[tuple[int, int], list[int]] = {}
    for fi, face in enumerate(solid.faces):
        for i in range(len(face)):
            e = tuple(sorted((face[i], face[(i + 1) % len(face)])))
            ef.setdefault(e, []).append(fi)
    return ef


def classify_edges(solid: Solid, d: np.ndarray) -> dict[tuple[int, int], bool]:
    """Every edge → visible (True) / hidden (False). CONVEX ONLY: an edge is hidden iff both
    adjacent faces are back-facing. Raises `NotConvex` otherwise (the doc's bound, enforced)."""
    if not _is_convex(solid):
        raise NotConvex(
            f"hidden-line determination for solid {solid.kind!r} is closed-form only for a CONVEX "
            "body (scene3d-geometry-design.md §Occlusion bounds many-body/non-convex away) — "
            "draw it translucent or split it into convex parts")
    back = back_facing(solid, d)
    out: dict[tuple[int, int], bool] = {}
    for e, fs_ in _edge_faces(solid).items():
        out[e] = not all(back[fi] for fi in fs_)       # visible unless every adjacent face is away
    return out


class NotConvex(ValueError):
    """Raised when hidden-line determination is asked for a non-convex / many-body scene — the
    exact-occlusion boundary the design doc draws."""


# --- silhouette of a smooth (curved) body: cylinder / cone --------------------
def _smooth_edge_indices(solid: Solid) -> set[tuple[int, int]]:
    """The edges that belong to a smooth face — these are facet edges of the sampling polygon, NOT
    real edges, so they are never drawn as visible/hidden lines (only the silhouette is)."""
    smooth: set[tuple[int, int]] = set()
    for fi in solid.smooth_faces:
        face = solid.faces[fi]
        for i in range(len(face)):
            smooth.add(tuple(sorted((face[i], face[(i + 1) % len(face)]))))
    return smooth


def _silhouette_generators(solid: Solid, axo: dict[str, np.ndarray], apex: np.ndarray | None,
                           base_center: np.ndarray, rim_idx: list[int]) -> list[tuple[int, int]]:
    """The two lateral generators of a cylinder/cone that form its outline: the rim points whose
    PROJECTION is extreme in x (leftmost / rightmost), i.e. the profile edges under this view."""
    rp = {i: project(solid.verts[i], axo) for i in rim_idx}
    iL = min(rim_idx, key=lambda i: rp[i][0])
    iR = max(rim_idx, key=lambda i: rp[i][0])
    return [iL, iR]


# --- shared: assemble a Scene from projected 3D primitives --------------------
def _bounds(pts2: list[tuple[float, float]], pad: float) -> tuple[tuple, tuple]:
    xs = [p[0] for p in pts2]
    ys = [p[1] for p in pts2]
    return (min(xs) - pad, max(xs) + pad), (min(ys) - pad, max(ys) + pad)


_VISIBLE = dict(role="ink", width=2.0)
_HIDDEN = dict(role="muted", width=1.2, dash=(0, (4, 3)))   # dashed = the Schrägriss hidden-edge


def _solid_layers(solid: Solid, axo: dict[str, np.ndarray], *, z0: int = 3) -> tuple[list, list]:
    """Build the 2D layers for a solid (edges classified visible/hidden; a smooth body drawn as
    silhouette). Returns (layers, projected_points) so the caller can frame the view."""
    layers: list = []
    seen: list[tuple[float, float]] = []

    def pt(i: int) -> tuple[float, float]:
        q = project(solid.verts[i], axo)
        seen.append(q)
        return q

    smooth = _smooth_edge_indices(solid)
    if solid.smooth_faces:                              # cylinder / cone: silhouette, not facets
        # rim = the shared boundary of the smooth wall and a cap; recover it as the vertices that
        # appear in a smooth face AND (for a cylinder) in a cap, or simply the base ring.
        rim_bottom = [i for i in range(len(solid.verts))
                      if abs(solid.verts[i][2] - solid.verts[:, 2].min()) < 1e-9]
        rim_bottom.sort(key=lambda i: math.atan2(solid.verts[i][1], solid.verts[i][0]))
        base_center = np.array([0.0, 0.0, float(solid.verts[:, 2].min())])
        # base rim ellipse (always visible for these upright solids seen from above)
        layers.append(Polyline([pt(i) for i in rim_bottom], role="ink", width=1.8,
                               closed=True, z=z0 + 1))
        if solid.apex is not None:                      # cone: two generators to the apex
            gens = _silhouette_generators(solid, axo, solid.verts[solid.apex], base_center,
                                          rim_bottom)
            ap = pt(solid.apex)
            for i in gens:
                layers.append(Line(pt(i), ap, **_VISIBLE, z=z0 + 1))
        else:                                           # cylinder: top rim + two vertical generators
            rim_top = [i for i in range(len(solid.verts))
                       if abs(solid.verts[i][2] - solid.verts[:, 2].max()) < 1e-9]
            rim_top.sort(key=lambda i: math.atan2(solid.verts[i][1], solid.verts[i][0]))
            layers.append(Polyline([pt(i) for i in rim_top], role="ink", width=1.8,
                                   closed=True, z=z0 + 1))
            gens = _silhouette_generators(solid, axo, None, base_center, rim_bottom)
            for i in gens:                              # match bottom generator to the top above it
                top_i = min(rim_top, key=lambda t: np.linalg.norm(
                    solid.verts[t][:2] - solid.verts[i][:2]))
                layers.append(Line(pt(i), pt(top_i), **_VISIBLE, z=z0 + 1))
        return layers, seen

    # polyhedron: classify every real edge, draw hidden dashed / visible solid
    cls = classify_edges(solid, view_direction(axo))
    for e, visible in sorted(cls.items()):
        if e in smooth:
            continue
        style = _VISIBLE if visible else _HIDDEN
        layers.append(Line(pt(e[0]), pt(e[1]), **style, z=z0 + (1 if visible else 0)))
    return layers, seen


# --- Recipe 1: axonometric_solid (Schrägriss of a school solid) --------------
def axonometric_solid_scene(kind: str = "quader", *, labels: dict[str, str] | None = None,
                            show_measures: bool = True, title: str | None = None,
                            axo: dict[str, np.ndarray] = SCHRAEGRISS, **params) -> Scene:
    """The Schrägriss (Austrian Kabinettprojektion) of a school solid, hidden edges DASHED.

    `kind` ∈ quader·prism·pyramid·cylinder·cone (German aliases accepted). `params` size it
    (a/b/c · n/r/h). `labels` maps an edge/measure key to a string ("a", "h = 4 cm", "h = ?"); when
    `show_measures` is False every measure prints its key with "?" so one scene serves both the
    student task and the teacher solution. Everything — vertices, faces, edge visibility — is
    COMPUTED; the figure can never show a wrong hidden edge or a fabricated measurement."""
    solid = build_solid(kind, **params)
    layers, seen = _solid_layers(solid, axo)

    # dimension labels: a maskable measure per solid family. Each names a 3D edge (a→b) + a screen
    # direction; the label sits at the projected edge midpoint, offset in SCREEN space so it reads
    # BESIDE the edge, never on it (robust across solids/projections — no fragile 3D nudging).
    for (a3, b3), key, sdir in _measure_specs(solid, kind, axo):
        pa, pb = np.array(project(a3, axo)), np.array(project(b3, axo))
        mid = (pa + pb) / 2
        off = np.array(sdir, float)
        off = off / (np.linalg.norm(off) or 1.0) * _MEASURE_OFFSET
        p = tuple(mid + off)
        seen.append(p)
        given = (labels or {}).get(key)
        text = given if given is not None else (key if show_measures else f"{key} = ?")
        layers.append(Label(p, text, role="focus", size=fs.TYPE.annot_lg, bold=True, halo=True,
                            z=8))

    xlim, ylim = _bounds(seen, pad=0.6)
    sc = Scene(canvas=Canvas(figsize=(5.4, 5.0), aspect="equal", frame="off",
                             xlim=xlim, ylim=ylim,
                             title=title if title else _default_title(kind)))
    sc.layers = layers
    return sc


_MEASURE_OFFSET = 0.42          # screen-space label stand-off from the labelled edge


def _measure_specs(solid: Solid, kind: str, axo: dict[str, np.ndarray] = SCHRAEGRISS
                   ) -> list[tuple[tuple[P3, P3], str, tuple[float, float]]]:
    """The (edge, key, screen-direction) triples for a solid family. KEYS are the stored contract
    (documented on the wrapper): quader a·b·c; prism/cylinder/pyramid/cone r·h. The screen direction
    points the label OUTWARD from the figure so it clears the edge it names."""
    v = solid.verts
    key = kind.strip().lower()
    zmin, zmax = float(v[:, 2].min()), float(v[:, 2].max())
    # rightmost base vertex (in the ACTIVE projection's screen x) — the visible base edge / generator
    # to hang r/h on (uses the same axo the scene is drawn with, so it holds under AXO_34 too).
    base = [i for i in range(len(v)) if abs(v[i][2] - zmin) < 1e-9]
    ir = max(base, key=lambda i: project(v[i], axo)[0])
    center_bottom: P3 = (0.0, 0.0, zmin)
    if key in ("quader", "wuerfel", "cube"):
        # a = receding depth edge (v0→v1, dashed) label DOWN-LEFT; b = visible front-bottom edge
        # (v1→v2) label DOWN; c = visible front-right vertical (v1→v5) label RIGHT.
        return [((tuple(v[0]), tuple(v[1])), "a", (-0.5, -0.9)),
                ((tuple(v[1]), tuple(v[2])), "b", (0.2, -1.0)),
                ((tuple(v[1]), tuple(v[5])), "c", (1.0, 0.0))]
    if key in ("cylinder", "zylinder", "prism", "prisma"):
        return [((tuple(v[ir][:2]) + (zmin,), tuple(v[ir][:2]) + (zmax,)), "h", (1.0, 0.0)),
                (((v[ir][0] / 2, v[ir][1] / 2, zmin), tuple(v[ir][:2]) + (zmin,)), "r", (0.0, -1.0))]
    if key in ("pyramid", "pyramide", "cone", "kegel"):
        # h = the vertical apex→base-centre axis, label to the LEFT (clear of the front slant edge,
        # which projects near-vertical through the centre); r = a visible base edge, label DOWN.
        return [((center_bottom, (0.0, 0.0, zmax)), "h", (-1.0, 0.0)),
                ((center_bottom, tuple(v[ir][:2]) + (zmin,)), "r", (0.4, -1.0))]
    return []


_DEFAULT_TITLES = {
    "quader": "Quader im Schrägriss", "wuerfel": "Würfel im Schrägriss",
    "cube": "Würfel im Schrägriss", "prism": "Prisma im Schrägriss",
    "prisma": "Prisma im Schrägriss", "pyramid": "Pyramide im Schrägriss",
    "pyramide": "Pyramide im Schrägriss", "cylinder": "Drehzylinder im Schrägriss",
    "zylinder": "Drehzylinder im Schrägriss", "cone": "Drehkegel im Schrägriss",
    "kegel": "Drehkegel im Schrägriss",
}


def _default_title(kind: str) -> str:
    return _DEFAULT_TITLES.get(kind.strip().lower(), "Körper im Schrägriss")


# --- Recipe 2: riss_pair (Grund- und Aufriss) --------------------------------
def riss_pair_scene(kind: str = "quader", *, title: str | None = None,
                    ordnungslinien: bool = True, labels: dict[str, str] | None = None,
                    **params) -> Scene:
    """A Grund-/Aufriss pair — top (Draufsicht) and front (Vorderansicht) orthographic views, one
    above the other across a horizontal Rissachse, joined by vertical Ordnungslinien.

    The two Risse share the x measurement exactly (the defining property): a vertex P=(x,y,z) maps
    to Grundriss (x, −y − gap) BELOW the axis and Aufriss (x, z) ABOVE it — so every point sits on
    one shared vertical Ordnungslinie. Same solid, same scale. This is the paper-and-pencil
    zugeordnete Normalrisse layout of GZ/DG, not a projection view — nothing is foreshortened."""
    solid = build_solid(kind, **params)
    v = solid.verts

    xmin, xmax = float(v[:, 0].min()), float(v[:, 0].max())
    ymin, ymax = float(v[:, 1].min()), float(v[:, 1].max())
    zmin, zmax = float(v[:, 2].min()), float(v[:, 2].max())
    gap = 0.9                                          # Rissachse band between the two views
    depth = ymax - ymin

    # Grundriss (top view): (x, y) but drawn BELOW the axis, y receding downward.
    def gr(i: int) -> tuple[float, float]:
        return (float(v[i][0]), -gap - (float(v[i][1]) - ymin))
    # Aufriss (front view): (x, z) ABOVE the axis.
    def au(i: int) -> tuple[float, float]:
        return (float(v[i][0]), gap + (float(v[i][2]) - zmin))

    layers: list = []
    seen: list[tuple[float, float]] = []

    # the Rissachse (fold line) at y=0
    axis_lo, axis_hi = xmin - 0.6, xmax + 0.6
    layers.append(Line((axis_lo, 0.0), (axis_hi, 0.0), role="muted", width=1.2, z=2))
    layers.append(Label((axis_hi, 0.0), "  Rissachse", role="muted", size=fs.TYPE.tick,
                        ha="left", va="center", halo=True, z=6))

    # Ordnungslinien: one vertical projector per DISTINCT x column (shared between the two Risse).
    # A SMOOTH body (cylinder/cone) is sampled as a fine polygon → dozens of x-columns would be a
    # forest of clutter; for it we draw only the meaningful projectors: the two silhouette extents
    # (the outline width) and the centre axis. A polyhedron uses its real vertex columns.
    if ordnungslinien:
        if solid.smooth_faces:
            xs = [xmin, (xmin + xmax) / 2, xmax]
        else:
            xs = sorted({round(float(x), 6) for x in v[:, 0]})
        y_lo = -gap - depth - 0.15
        y_hi = gap + (zmax - zmin) + 0.15
        for x in xs:
            layers.append(Line((x, y_lo), (x, y_hi), role="grid", width=0.7, dash=(0, (2, 3)),
                               z=1))

    # draw each Riss as its own convex outline + visible internal edges (orthographic → an edge is
    # "hidden" in a Riss only if it is occluded along the view axis; for these single convex solids
    # seen face-on we draw the silhouette solid and interior edges lighter).
    _riss_body(solid, gr, layers, seen, view="top")
    _riss_body(solid, au, layers, seen, view="front")

    # riss captions
    layers.append(Label(((xmin + xmax) / 2, gap + (zmax - zmin) + 0.5), "Aufriss",
                        role="ink", size=fs.TYPE.annot, bold=True, halo=True, z=7))
    seen.append(((xmin + xmax) / 2, gap + (zmax - zmin) + 0.5))
    layers.append(Label(((xmin + xmax) / 2, -gap - depth - 0.5), "Grundriss",
                        role="ink", size=fs.TYPE.annot, bold=True, halo=True, z=7))
    seen.append(((xmin + xmax) / 2, -gap - depth - 0.5))

    xlim, ylim = _bounds(seen, pad=0.5)
    sc = Scene(canvas=Canvas(figsize=(5.0, 6.0), aspect="equal", frame="off",
                             xlim=xlim, ylim=ylim,
                             title=title if title else f"{_default_title(kind).split(' im ')[0]} "
                                                        "— Grund- und Aufriss"))
    sc.layers = layers
    return sc


def _riss_body(solid: Solid, mapfn, layers: list, seen: list, *, view: str) -> None:
    """Draw one orthographic Riss of the solid via `mapfn` (index → 2D point). The outline is the
    convex hull of the projected vertices (the true silhouette of a convex body); interior edges of
    the real faces render as light structure lines. A smooth body shows its rim as an ellipse or a
    line, per the view."""
    pts2 = {i: mapfn(i) for i in range(len(solid.verts))}
    for p in pts2.values():
        seen.append(p)

    # silhouette outline = convex hull of the 2D points (correct for a convex solid)
    hull = _convex_hull_2d(list(pts2.items()))
    layers.append(Polyline([p for _, p in hull], role="ink", width=1.9, closed=True, z=4))

    if solid.smooth_faces:
        # a curved body: top/bottom view of a cylinder/cone is a circle; front view is the hull
        # already drawn. Add the base-circle ellipse in the top view for legibility.
        if view == "top":
            zmin = float(solid.verts[:, 2].min())
            rim = [i for i in range(len(solid.verts)) if abs(solid.verts[i][2] - zmin) < 1e-9]
            rim.sort(key=lambda i: math.atan2(solid.verts[i][1], solid.verts[i][0]))
            layers.append(Polyline([mapfn(i) for i in rim], role="ink", width=1.6,
                                   closed=True, z=5))
        return

    # polyhedron: draw the real edges that fall INSIDE the hull as light structure (so a Riss shows
    # the solid's construction, not just its outline). An edge on the hull is already the outline.
    hull_edges = set()
    hidx = [i for i, _ in hull]
    for a, b in zip(hidx, hidx[1:] + hidx[:1]):
        hull_edges.add(tuple(sorted((a, b))))
    for face in solid.faces:
        for i in range(len(face)):
            e = tuple(sorted((face[i], face[(i + 1) % len(face)])))
            if e not in hull_edges:
                layers.append(Line(pts2[e[0]], pts2[e[1]], role="muted", width=0.9,
                                   dash=(0, (4, 3)), z=3))
                hull_edges.add(e)                      # draw each interior edge once


def _convex_hull_2d(indexed_pts: list[tuple[int, tuple[float, float]]]
                    ) -> list[tuple[int, tuple[float, float]]]:
    """Andrew's monotone-chain convex hull, keeping the original vertex index with each point."""
    pts = sorted(set((round(p[0], 9), round(p[1], 9), i) for i, p in indexed_pts))
    if len(pts) <= 2:
        return [(i, (x, y)) for x, y, i in pts]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return [(i, (x, y)) for x, y, i in hull]
