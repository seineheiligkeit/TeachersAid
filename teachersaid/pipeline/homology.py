"""Homologie-Schema — a curated schematic-comparison figure for the vertebrate Bauplan.

The didactic point a bar chart gets backwards: Fisch, Frosch, Vogel and Hund look utterly
different, yet every one is built on the SAME plan — exactly two pairs of Gliedmaßen (a
Vordergliedmaßenpaar + a Hintergliedmaßenpaar), only formed differently (Flossen, Beine,
Flügel). Homologe Gliedmaßen → gemeinsame Abstammung. So the figure must make "same two
pairs, different form" read at a glance — a bar chart invites "find the differences", the
exact opposite message.

The load-bearing encoding is COLOUR CONSISTENCY: the forelimb pair is drawn in ONE role
(`focus`) and the hindlimb pair in ANOTHER (`primary`) — the SAME two colours on every
animal — while the SHAPE varies (a red fin on the fish, a red wing on the bird, a red leg
on the dog: homologous, differently formed — that variation IS the lesson). A redundant
edge treatment (solid outline for the forelimb pair, dashed for the hindlimb pair) keeps
the two pairs apart in a black-and-white photocopy, and a legend maps colour → pair.

Two-tier, like every scene family: the LLM never authors this scene. The limb homologies
are CURATED biological facts (`ANIMALS`); a didactic recipe (`homology_scene`) COMPUTES the
figure from them — correct by curation, not by invented numbers. Each animal declares
EXACTLY two forelimbs and two hindlimbs, and the recipe enforces the "genau zwei Paare"
invariant. The unpaired fish fins (Rücken-/Schwanzflosse) are drawn in neutral grey, never a
pair colour, so the count stays honest.

Builds `scene.Scene`; the `matplotlib:homology_schema` generator in `assets.py` wraps it.
Imports only the scene primitives + figstyle + math.
"""
from __future__ import annotations

import math

from . import figstyle as fs
from .scene import Canvas, CircleShape, Label, PointMark, Polyline, Region, Scene

# The two pair roles — constant across every animal (that constancy is the message).
FORE_ROLE = "focus"     # Vordergliedmaßenpaar (Brustflossen / Vorderbeine / Flügel)
HIND_ROLE = "primary"   # Hintergliedmaßenpaar (Bauchflossen / Hinterbeine / Beine)
_NEUTRAL = "muted"      # unpaired parts (fish Rücken-/Schwanzflosse) — never a pair colour


# --- geometry helpers ---------------------------------------------------------
def _ellipse(cx: float, cy: float, rx: float, ry: float,
             t0: float = 0.0, t1: float = 360.0, n: int = 48) -> list[tuple[float, float]]:
    """Points along an ellipse arc (degrees, counter-clockwise) — a smooth body outline."""
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
            for a in [t0 + (t1 - t0) * i / n for i in range(n + 1)]]


def _limb(p_top: tuple[float, float], p_foot: tuple[float, float],
          w_top: float, w_foot: float) -> list[tuple[float, float]]:
    """A tapered limb quad from hip `p_top` (width `w_top`) to foot `p_foot` (width
    `w_foot`) — the generic leg; a fin/wing is authored as an explicit polygon instead."""
    (x1, y1), (x2, y2) = p_top, p_foot
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    return [(x1 + nx * w_top / 2, y1 + ny * w_top / 2),
            (x2 + nx * w_foot / 2, y2 + ny * w_foot / 2),
            (x2 - nx * w_foot / 2, y2 - ny * w_foot / 2),
            (x1 - nx * w_top / 2, y1 - ny * w_top / 2)]


# --- the curated animals (side view, facing left) -----------------------------
# Each animal is a small correct-by-construction spec: a body silhouette, some neutral
# details, and EXACTLY two forelimbs + two hindlimbs. A limb is a LIST of polygons (a
# straight leg is one quad; a bent frog leg is a thigh + a shin), so "genau zwei Paare"
# is `len(fore) == len(hind) == 2` regardless of how many pieces each limb is drawn from.
# Coordinates live in a local 0..10 (x) × 0..9 (y) frame; the recipe translates each into
# its grid cell.
def _fisch() -> dict:
    return {
        "name": "Fisch",
        "fore_form": "Brustflossen",
        "hind_form": "Bauchflossen",
        "body": [_ellipse(5.0, 6.0, 3.1, 1.5)],
        "details": [                                       # unpaired fins = neutral grey
            ("fill", [(7.8, 6.0), (9.5, 7.2), (9.0, 6.0), (9.5, 4.8)]),   # Schwanzflosse
            ("fill", [(4.3, 7.45), (5.2, 8.4), (6.0, 7.35)]),           # Rückenflosse
        ],
        "eye": (3.0, 6.3),
        "fore": [                                          # Brustflossen (2), a clear fan pair
            [[(2.9, 4.75), (2.0, 3.5), (2.85, 3.7), (3.4, 4.35)]],        # near
            [[(3.55, 4.7), (2.95, 3.55), (3.75, 3.8), (4.15, 4.35)]],     # far (offset back)
        ],
        "hind": [                                          # Bauchflossen (2), clearly further back
            [[(5.6, 4.45), (4.95, 3.4), (5.75, 3.55), (6.15, 4.15)]],     # near
            [[(6.25, 4.4), (5.8, 3.45), (6.6, 3.6), (6.9, 4.05)]],        # far
        ],
    }


def _frosch() -> dict:
    return {
        "name": "Frosch",
        "fore_form": "Vorderbeine",
        "hind_form": "Hinterbeine",
        "body": [_ellipse(5.0, 5.3, 2.9, 1.5)],
        "details": [
            ("eye_bump", (3.2, 6.35, 0.5)),                # raised eye (circle)
            ("line", [(2.15, 5.0), (3.4, 4.75), (4.4, 4.95)]),   # wide Froschmaul
        ],
        "eye": (3.15, 6.4),
        "fore": [                                          # Vorderbeine (2), short, front
            [_limb((3.6, 4.15), (3.35, 2.55), 0.5, 0.36)],
            [_limb((4.2, 4.25), (4.0, 2.7), 0.46, 0.34)],
        ],
        "hind": [                                          # Hinterbeine (2), bent thigh + shin
            [_limb((5.75, 4.2), (7.55, 4.6), 0.9, 0.66),   # near: thigh back-up …
             _limb((7.45, 4.65), (6.5, 2.4), 0.66, 0.4)],   #        … shin down to foot
            [_limb((6.15, 4.6), (7.95, 5.0), 0.84, 0.6),   # far (offset up-right)
             _limb((7.85, 5.05), (7.05, 2.85), 0.58, 0.36)],
        ],
    }


def _vogel() -> dict:
    return {
        "name": "Vogel",
        "fore_form": "Flügel",
        "hind_form": "Beine",
        "body": [
            _ellipse(5.5, 5.3, 2.3, 1.8),                  # trunk
            [(2.0, 7.0), (0.7, 6.75), (2.0, 6.35)],        # Schnabel (beak)
        ],
        "body_circles": [(2.95, 6.9, 0.95)],               # head
        "eye": (2.7, 7.1),
        "fore": [                                          # Flügel (2), clearly separated
            [[(4.3, 6.0), (7.1, 5.6), (6.4, 4.7), (4.8, 5.25)]],          # near wing (on body)
            [[(4.9, 7.0), (6.7, 6.85), (6.2, 6.15), (5.1, 6.4)]],         # far wing (over the back)
        ],
        "hind": [                                          # Beine (2), thin
            [_limb((4.9, 3.6), (4.7, 2.2), 0.3, 0.22)],
            [_limb((5.6, 3.65), (5.65, 2.25), 0.3, 0.22)],
        ],
    }


def _hund() -> dict:
    return {
        "name": "Hund",
        "fore_form": "Vorderbeine",
        "hind_form": "Hinterbeine",
        "body": [
            _ellipse(5.4, 5.5, 2.9, 1.25),                 # trunk
            [(1.0, 5.55), (2.3, 5.95), (2.3, 5.05)],       # Schnauze (snout)
            [(2.2, 6.5), (2.55, 7.5), (3.15, 6.55)],       # Ohr (ear)
            _limb((8.0, 6.1), (9.2, 7.0), 0.6, 0.28),      # Schwanz (tail)
        ],
        "body_circles": [(2.5, 5.9, 1.02)],                # head
        "eye": (2.25, 6.15),
        "fore": [                                          # Vorderbeine (2)
            [_limb((3.5, 4.5), (3.4, 2.3), 0.58, 0.44)],
            [_limb((4.15, 4.55), (4.1, 2.4), 0.52, 0.4)],
        ],
        "hind": [                                          # Hinterbeine (2), haunch + shank
            [_limb((6.7, 4.55), (7.5, 3.5), 1.0, 0.5),     # near: haunch …
             _limb((7.45, 3.6), (7.35, 2.3), 0.5, 0.4)],   #        … lower leg
            [_limb((7.15, 4.6), (7.95, 3.6), 0.92, 0.46),  # far
             _limb((7.9, 3.7), (7.85, 2.45), 0.46, 0.38)],
        ],
    }


ANIMALS: list[dict] = [_fisch(), _frosch(), _vogel(), _hund()]


# --- the recipe ---------------------------------------------------------------
def _translate(points, ox: float, oy: float):
    return [(x + ox, y + oy) for x, y in points]


def _limb_layers(points, ox: float, oy: float, role: str, *, dashed: bool, z: int,
                 group: str) -> list:
    """One limb → a translucent fill (the pair colour) + a solid/dashed outline (the
    B/W-safe redundancy: forelimbs solid, hindlimbs dashed). Both layers carry `group`
    (`forelimb`/`hindlimb`), the scene-engine density/selection idiom."""
    pts = _translate(points, ox, oy)
    dash = (0, (4, 2)) if dashed else "solid"
    return [
        Region(pts, role=role, alpha=0.55, edge_role=None, z=z, group=group),
        Polyline(pts, role=fs.edge(role, 0.28), width=1.7, dash=dash, closed=True, z=z + 1,
                 group=group),
    ]


def _place_animal(sc: Scene, animal: dict, ox: float, oy: float, allpts: list) -> None:
    """Draw one animal into the scene at cell origin (ox, oy)."""
    # body silhouette(s) — light surface fill, ink outline
    for poly in animal.get("body", []):
        pts = _translate(poly, ox, oy)
        allpts += pts
        sc.add(Region(pts, role="surface", alpha=1.0, edge_role="ink", edge_width=1.7, z=3))
    for cx, cy, r in animal.get("body_circles", []):
        # a head reads like the body: a light surface disc + a separate ink outline ring
        # (CircleShape fills face==edge, so face≠edge needs two circles)
        sc.add(CircleShape((cx + ox, cy + oy), r, role="surface", fill=True, width=0, z=3))
        sc.add(CircleShape((cx + ox, cy + oy), r, role="ink", fill=False, width=1.7, z=4))
    # neutral details (grey unpaired fins, eye bump, mouth line)
    for kind, data in animal.get("details", []):
        if kind == "fill":
            pts = _translate(data, ox, oy)
            allpts += pts
            sc.add(Region(pts, role=_NEUTRAL, alpha=0.5, edge_role=_NEUTRAL,
                          edge_width=1.2, z=2))
        elif kind == "eye_bump":
            cx, cy, r = data
            sc.add(CircleShape((cx + ox, cy + oy), r, role="surface", fill=True, width=0, z=4))
            sc.add(CircleShape((cx + ox, cy + oy), r, role="ink", fill=False, width=1.4, z=4))
        elif kind == "line":
            sc.add(Polyline(_translate(data, ox, oy), role="ink", width=1.3, z=4))
    # forelimb pair (focus, solid) + hindlimb pair (primary, dashed). A limb is a list of
    # polygons (a bent leg = thigh + shin); all pieces share the pair colour.
    for limb in animal["fore"]:
        for poly in limb:
            allpts += _translate(poly, ox, oy)
            sc.add(*_limb_layers(poly, ox, oy, FORE_ROLE, dashed=False, z=5,
                                 group="forelimb"))
    for limb in animal["hind"]:
        for poly in limb:
            allpts += _translate(poly, ox, oy)
            sc.add(*_limb_layers(poly, ox, oy, HIND_ROLE, dashed=True, z=5,
                                 group="hindlimb"))
    # eye
    if animal.get("eye"):
        ex, ey = animal["eye"]
        sc.add(PointMark((ex + ox, ey + oy), role="ink", size=3.4, bold=False, z=8))
    # labels: name (bold ink) + the two limb FORMS, each in its pair colour
    sc.add(Label((ox + 5.0, oy + 1.7), animal["name"], role="ink", size=fs.TYPE.annot_lg,
                 bold=True, halo=True, z=9))
    sc.add(Label((ox + 5.0, oy + 0.85), animal["fore_form"], role=FORE_ROLE,
                 size=fs.TYPE.annot, halo=True, z=9))
    sc.add(Label((ox + 5.0, oy + 0.1), animal["hind_form"], role=HIND_ROLE,
                 size=fs.TYPE.annot, halo=True, z=9))


def homology_scene(spec: dict | None = None) -> Scene:
    """The vertebrate-homology comparison figure. `spec` may override {title, animals}
    (animals = a list of the curated animal dicts); by default all four (Fisch, Frosch,
    Vogel, Hund) are drawn in a 2×2 grid. Each animal shows its body plus its two
    colour-coded limb pairs; a legend maps colour → Gliedmaßenpaar."""
    spec = spec or {}
    animals = spec.get("animals") or ANIMALS
    title = spec.get("title", "Zwei Gliedmaßenpaare – ein gemeinsamer Bauplan")

    cell_w, cell_h, gap_x, gap_y = 10.0, 9.0, 3.0, 1.5
    sc = Scene(canvas=Canvas(aspect="equal", frame="off"))
    allpts: list = []
    ncol = 2
    for i, animal in enumerate(animals):
        col, row = i % ncol, i // ncol
        ox = col * (cell_w + gap_x)
        # rows top-down: row 0 is the top row
        nrow = (len(animals) + ncol - 1) // ncol
        oy = (nrow - 1 - row) * (cell_h + gap_y)
        _place_animal(sc, animal, ox, oy, allpts)

    # extents from the drawn geometry
    xs = [p[0] for p in allpts]
    ys = [p[1] for p in allpts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)

    # legend, centred above the top row
    leg_y = y1 + 1.4
    sw = 0.85                                              # swatch half-size
    cx = (x0 + x1) / 2
    entries = [(cx - 8.4, FORE_ROLE, False, "Vordergliedmaßenpaar"),
               (cx + 0.4, HIND_ROLE, True, "Hintergliedmaßenpaar")]
    for lx, role, dashed, text in entries:
        box = [(lx, leg_y - sw), (lx + 2 * sw, leg_y - sw),
               (lx + 2 * sw, leg_y + sw), (lx, leg_y + sw)]
        sc.add(Region(box, role=role, alpha=0.55, edge_role=None, z=6, group="legend"))
        sc.add(Polyline(box, role=fs.edge(role, 0.28), width=1.7,
                        dash=(0, (4, 2)) if dashed else "solid", closed=True, z=7,
                        group="legend"))
        sc.add(Label((lx + 2 * sw + 0.35, leg_y), text, role="ink", size=fs.TYPE.annot,
                     ha="left", va="center", halo=True, z=7, group="legend"))
    ys += [leg_y - sw, leg_y + sw]

    pad = 0.7
    sc.canvas.xlim = (x0 - pad, x1 + pad)
    sc.canvas.ylim = (min(ys) - pad, leg_y + sw + pad)
    xspan = (x1 - x0) + 2 * pad
    yspan = (leg_y + sw + pad) - (min(ys) - pad)
    width = 9.0
    sc.canvas.figsize = (width, max(4.0, width * yspan / xspan))
    if title:
        sc.canvas.title = str(title)
    return sc
