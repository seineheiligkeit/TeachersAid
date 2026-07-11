"""Correct-by-construction nets (Körpernetze) composed on the scene engine.

The geometry and rendering are deliberately separate. ``cuboid_net`` computes an
axis-aligned six-face layout whose face dimensions and five fold adjacencies are explicit;
``solid_net_scene`` merely projects that layout into ``Region``/``Line``/``Label`` scene
primitives. Tests can therefore prove that the drawn net really folds to the requested
solid instead of trusting a hand-drawn picture.

The first family covers Quader and Würfel, the missing Unterstufe geometry recipe. A
Quader net contains two ``a×b``, two ``a×c`` and two ``b×c`` faces. It is a tree of faces:
one central face, its four side faces, and the opposite face attached to one side. Labels
are supplied by the caller (``"a = 3 cm"``, ``"O = ?"``), so the same geometry can be used
for a worked example or a leak-safe student task.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from . import figstyle as fs
from .scene import Canvas, Label, Line, Region, Scene

Point = tuple[float, float]
Segment = tuple[Point, Point]


def _segment(p: Point, q: Point) -> Segment:
    """Canonical segment order, useful for exact shared-edge comparisons."""
    return (p, q) if p <= q else (q, p)


@dataclass(frozen=True)
class NetFace:
    """One axis-aligned rectangular face in a computed net."""

    name: str
    origin: Point
    width: float
    height: float
    dimensions: tuple[str, str]

    @property
    def points(self) -> list[Point]:
        x, y = self.origin
        return [(x, y), (x + self.width, y),
                (x + self.width, y + self.height), (x, y + self.height)]

    @property
    def edges(self) -> tuple[Segment, Segment, Segment, Segment]:
        p = self.points
        return tuple(_segment(p[i], p[(i + 1) % 4]) for i in range(4))  # type: ignore[return-value]

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class NetLayout:
    """Computed faces plus the edges along which the paper folds."""

    faces: tuple[NetFace, ...]
    folds: tuple[Segment, ...]

    def adjacencies(self) -> dict[tuple[str, str], Segment]:
        """Every pair of faces sharing a complete edge (point contacts do not count)."""
        out: dict[tuple[str, str], Segment] = {}
        for i, left in enumerate(self.faces):
            for right in self.faces[i + 1:]:
                shared = set(left.edges) & set(right.edges)
                if shared:
                    out[(left.name, right.name)] = shared.pop()
        return out


def _positive(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite length")
    return value


def cuboid_net(a: float, b: float, c: float) -> NetLayout:
    """Compute a true six-face net for a cuboid with edge lengths ``a``, ``b``, ``c``.

    The central ``a×b`` face carries four side faces; the second ``a×b`` face is attached
    to the far edge of the back ``a×c`` face. Consequently the face-adjacency graph has
    six vertices and exactly five edges: it is connected and cycle-free, hence a foldable
    net rather than an overlapping arrangement of rectangles.
    """
    a, b, c = _positive("a", a), _positive("b", b), _positive("c", c)
    faces = (
        NetFace("base", (0.0, 0.0), a, b, ("a", "b")),
        NetFace("front", (0.0, -c), a, c, ("a", "c")),
        NetFace("back", (0.0, b), a, c, ("a", "c")),
        NetFace("left", (-c, 0.0), c, b, ("c", "b")),
        NetFace("right", (a, 0.0), c, b, ("c", "b")),
        NetFace("opposite", (0.0, b + c), a, b, ("a", "b")),
    )
    folds = (
        _segment((0.0, 0.0), (a, 0.0)),
        _segment((0.0, b), (a, b)),
        _segment((0.0, 0.0), (0.0, b)),
        _segment((a, 0.0), (a, b)),
        _segment((0.0, b + c), (a, b + c)),
    )
    return NetLayout(faces=faces, folds=folds)


def _cuboid_lengths(spec: dict) -> tuple[float, float, float, bool]:
    kind = str(spec.get("kind", "cuboid")).lower()
    if kind in {"cube", "wuerfel", "würfel"}:
        side = _positive("side", spec.get("side", spec.get("a", 3)))
        return side, side, side, True
    if kind not in {"cuboid", "quader"}:
        raise ValueError(f"unsupported solid-net kind {kind!r}; expected cuboid or cube")
    return (_positive("a", spec.get("a", 4)),
            _positive("b", spec.get("b", 3)),
            _positive("c", spec.get("c", 2)), False)


def solid_net_scene(spec: dict | None = None) -> Scene:
    """Project a cuboid/cube net spec into house-styled scene primitives.

    Spec: ``kind`` (``cuboid``/``cube``), ``a``/``b``/``c`` or ``side``, optional
    ``label_a``/``label_b``/``label_c``, ``result_label`` and ``title``. Every visible
    label comes from the spec (or is a symbolic default), never from a computed answer.
    """
    spec = spec or {}
    a, b, c, is_cube = _cuboid_lengths(spec)
    layout = cuboid_net(a, b, c)

    min_x, max_x = -c, a + c
    min_y, max_y = -c, 2 * b + c
    span = max(max_x - min_x, max_y - min_y)
    pad = max(0.28, 0.11 * span)
    width, height = max_x - min_x, max_y - min_y
    ratio = width / height
    figsize = (5.2, max(3.8, min(6.2, 5.2 / max(ratio, 0.55))))

    scene = Scene(canvas=Canvas(
        figsize=figsize, aspect="equal", frame="off",
        xlim=(min_x - pad, max_x + pad), ylim=(min_y - pad, max_y + pad),
        title=str(spec["title"]) if spec.get("title") else None,
    ))
    for face in layout.faces:
        scene.add(Region(face.points, role="surface", alpha=1.0,
                         edge_role="ink", edge_width=1.6, z=1))
    for p, q in layout.folds:
        scene.add(Line(p, q, role="muted", width=1.15, dash=(0, (4, 3)), z=4))

    # Representative outer edges state the three dimensions without repeating them on
    # every congruent face. Cube defaults intentionally show only one side length.
    label_a = spec.get("label_a", "a")
    label_b = spec.get("label_b", None if is_cube else "b")
    label_c = spec.get("label_c", None if is_cube else "c")
    label_gap = 0.16 * pad
    if label_a:
        scene.add(Label((a / 2, -c - label_gap), str(label_a), size=fs.TYPE.annot_lg,
                        va="top", halo=False))
    if label_b:
        scene.add(Label((-c - label_gap, b / 2), str(label_b), size=fs.TYPE.annot_lg,
                        ha="right", halo=False))
    if label_c:
        scene.add(Label((a + label_gap, -c / 2), str(label_c), size=fs.TYPE.annot_lg,
                        ha="left", halo=False))
    if spec.get("result_label"):
        scene.add(Label((a / 2, b + c + b / 2), str(spec["result_label"]),
                        role="focus", size=fs.TYPE.annot_lg, bold=True))
    return scene
