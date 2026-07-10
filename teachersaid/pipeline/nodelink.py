"""The node-link scene family — one composable visual language for the three "boxes + edges"
figures that used to be three bespoke matplotlib functions in `assets.py`:

    tree_scene(spec)          Baumdiagramm — a multi-stage probability tree (plain dot-nodes +
                              labelled edges; parents at the mean of their children)
    cause_effect_scene(spec)  Wirkungsgefüge — a two-column cause→effect diagram (fan-out arrows)
    process_scene(spec)       Ablauf — a circular (cyclic) or linear ordered process of steps

Each COMPUTES a `scene.Scene` from the recipe's existing spec (contracts unchanged), so the three
`assets.py` builders become thin wrappers (parse spec → scene → `scene_to_png`). Two-tier like the
rest of the engine: the LLM never authors a Scene; these didactic builders compute it from a small
spec. Semantic roles (from the figstyle port): node faces are `surface` (cool) / `surface_warm`
(warm), borders `ink` / `focus`, edges `muted`, a tree's edge-probability chips `focus` on a white
`paper` face.

Pure: imports only the scene primitives + stdlib. `assets.matplotlib:{tree_diagram,cause_effect,
process_flow}` wrap these for the engine.
"""
from __future__ import annotations

import math
import textwrap

from .scene import Arrow, Canvas, Label, Line, Node, PointMark, Scene


# --- probability tree (Baumdiagramm) -----------------------------------------
def tree_scene(spec: dict) -> Scene:
    """A probability tree from spec {branches:[{label, p?, children?:[…]}], title?}. Leaf-packing
    layout: leaves get incrementing integer heights, a parent sits at the mean of its children;
    depth is the x-column. Each edge carries its p as a white chip at the midpoint (the answer is
    spec-provided — the figure never invents a probability). Does not mutate the caller's spec."""
    roots = spec.get("branches", []) or []
    pos: dict[int, tuple[float, float]] = {}          # id(node) -> (x=depth, y)
    leaf = [0.0]
    max_depth = [1]

    def place(node: dict, depth: int) -> float:
        max_depth[0] = max(max_depth[0], depth)
        kids = node.get("children") or []
        if kids:
            y = sum(place(k, depth + 1) for k in kids) / len(kids)
        else:
            y = leaf[0]
            leaf[0] += 1
        pos[id(node)] = (float(depth), y)
        return y

    for r in roots:
        place(r, 1)
    root_y = sum(pos[id(r)][1] for r in roots) / len(roots) if roots else 0.0
    root_xy = (0.0, root_y)

    # collect by kind so z-layering is clean (edges under dots under chips/labels)
    edges: list = []
    chips: list = []
    dots: list = []
    labels: list = []

    def walk(node: dict, parent_xy: tuple[float, float]) -> None:
        x, y = pos[id(node)]
        edges.append(Line(parent_xy, (x, y), role="ink", width=1.3, z=1))
        p = node.get("p")
        if p not in (None, ""):
            mx, my = (parent_xy[0] + x) / 2, (parent_xy[1] + y) / 2
            chips.append(Node((mx, my), str(p), face_role="paper", edge_role=None,
                              text_role="focus", pad=0.12, size=9.0, z=4))
        dots.append(PointMark((x, y), label=None, role="ink", size=5.0, bold=False, z=2))
        labels.append(Label((x + 0.06, y), str(node.get("label", "")), role="ink", size=10.0,
                            ha="left", va="center", halo=True, z=5))
        for k in node.get("children") or []:
            walk(k, (x, y))

    if roots:
        dots.append(PointMark(root_xy, label=None, role="ink", size=5.0, bold=False, z=2))
    for r in roots:
        walk(r, root_xy)

    sc = Scene(canvas=Canvas(figsize=(6.0, 3.8), frame="off",
                             xlim=(-0.3, max_depth[0] + 0.9), ylim=(-0.6, max(leaf[0], 1) - 0.4)))
    sc.add(*edges, *chips, *dots, *labels)
    if spec.get("title"):
        sc.canvas.title = str(spec["title"])
    return sc


# --- Wirkungsgefüge (cause → effect) -----------------------------------------
def _wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width))


def cause_effect_scene(spec: dict) -> Scene:
    """A cause→effect Wirkungsgefüge from spec {links:[{cause, effect, kind?}], title?}. Distinct
    causes stack on the left (cool `surface` boxes), distinct effects on the right (warm
    `surface_warm`); each link draws one arrow, so a cause can fan out. Correct-by-construction:
    the boxes and arrows are spec-provided (no invented relationship)."""
    links = spec.get("links", []) or []
    causes: list[str] = []
    effects: list[str] = []
    for ln in links:
        c, e = str(ln.get("cause", "")), str(ln.get("effect", ""))
        if c and c not in causes:
            causes.append(c)
        if e and e not in effects:
            effects.append(e)
    n = max(len(causes), len(effects), 1)

    def ypos(idx: int, total: int) -> float:
        if total <= 1:
            return (n + 0.4) / 2
        top, bot = n, 0.4
        return top - (top - bot) * idx / (total - 1)

    cpos: dict[str, float] = {}
    epos: dict[str, float] = {}
    arrows: list = []
    nodes: list = []
    for i, c in enumerate(causes):
        y = ypos(i, len(causes))
        cpos[c] = y
        nodes.append(Node((1.7, y), _wrap(c, 24), face_role="surface", edge_role="ink", size=9.0))
    for i, e in enumerate(effects):
        y = ypos(i, len(effects))
        epos[e] = y
        nodes.append(Node((8.3, y), _wrap(e, 24), face_role="surface_warm", edge_role="focus",
                          size=9.0))
    for ln in links:
        c, e = str(ln.get("cause", "")), str(ln.get("effect", ""))
        if c in cpos and e in epos:
            arrows.append(Arrow((2.8, cpos[c]), (7.2, epos[e]), role="muted", width=1.2,
                                shrink_a=3.0, shrink_b=3.0, z=2))

    sc = Scene(canvas=Canvas(figsize=(7.8, max(2.6, 1.0 * n)), frame="off",
                             xlim=(0, 10), ylim=(0, n + 0.4)))
    sc.add(*arrows, *nodes)                            # arrows (z=2) under nodes (z=3)
    if spec.get("title"):
        sc.canvas.title = str(spec["title"])
    return sc


# --- process / cycle (Ablauf) ------------------------------------------------
def process_scene(spec: dict) -> Scene:
    """An ordered process from spec {steps:[{name, text?}], cyclic?:bool, title?}. A cyclic process
    of ≥3 steps is drawn around a circle with the last step looping back to the first (der
    Blutkreislauf); a shorter or non-cyclic one flows top→bottom (a short cyclic one still gets a
    curved loop-back). Structural, correct-by-construction: the steps + their order are given."""
    steps = [str(st.get("name", "")) for st in (spec.get("steps") or []) if st.get("name")]
    cyclic = bool(spec.get("cyclic"))
    n = len(steps)

    if n == 0:
        return Scene(canvas=Canvas(figsize=(4.0, 2.0), frame="off"))

    if cyclic and n >= 3:
        r = 1.0
        posv = [(r * math.cos(math.pi / 2 - 2 * math.pi * i / n),
                 r * math.sin(math.pi / 2 - 2 * math.pi * i / n)) for i in range(n)]
        lim = r + 0.65
        sc = Scene(canvas=Canvas(figsize=(6.6, 6.0), aspect="equal", frame="off",
                                 xlim=(-lim, lim), ylim=(-lim, lim)))
        arrows = [Arrow(posv[i], posv[(i + 1) % n], role="muted", width=1.3, curve=0.16,
                        shrink_a=26.0, shrink_b=26.0, z=2) for i in range(n)]
        nodes = [Node(posv[i], _wrap(steps[i], 18), face_role="surface_warm", edge_role="focus",
                      size=9.0) for i in range(n)]
    else:
        ys = [n - i for i in range(n)]                # top to bottom
        sc = Scene(canvas=Canvas(figsize=(5.2, max(2.4, 1.2 * n)), frame="off",
                                 xlim=(0, 4), ylim=(0, n + 0.5)))
        arrows = [Arrow((2, ys[i] - 0.30), (2, ys[i + 1] + 0.30), role="muted", width=1.3,
                        shrink_a=2.0, shrink_b=2.0, z=2) for i in range(n - 1)]
        if cyclic:                                    # a short process that still loops
            arrows.append(Arrow((2, ys[-1]), (2, ys[0]), role="muted", width=1.0, curve=-0.55,
                                shrink_a=2.0, shrink_b=2.0, z=2))
        nodes = [Node((2, ys[i]), _wrap(steps[i], 18), face_role="surface", edge_role="ink",
                      size=9.0) for i in range(n)]

    sc.add(*arrows, *nodes)                           # arrows (z=2) under boxes (z=3)
    if spec.get("title"):
        sc.canvas.title = str(spec["title"])
    return sc
