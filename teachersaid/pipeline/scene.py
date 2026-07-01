"""The scene engine — a small algebra of typed, annotated primitives over a coordinate canvas.

The structural answer to "every figure is a monolithic recipe": instead of one bespoke
matplotlib function per figure, a figure is a `Scene` = a `Canvas` + an ordered list of typed
`layers` (Polyline · Line · PointMark · CircleShape · Arc · Region · Label). One renderer
(`render_scene`) walks the scene and draws each layer in the house style (`figstyle`). So a new
figure becomes "compose a few primitives", not "write a new recipe", and the SAME scene can be
rendered at different densities (a `stage`/subset) — which is what makes a step-by-step
construction worksheet fall out of one computed object.

Two-tier design (mirrors the existing `GenDataFigure → choose_representation` seam): the LLM
never authors a Scene (that would let it draw a wrong tangent / leak an answer). A *didactic
recipe* COMPUTES the scene from a small, correct-by-construction spec (e.g.
`constructions.triangle_geometry` → `construction_scene`); this module is only the substrate +
the renderer. Pure data + a matplotlib renderer; the style is scoped via `figstyle.house_rc()`
so building a scene does NOT restyle the not-yet-ported recipes. Renderer-agnostic in shape (a
future SVG/Typst backend could walk the same Scene).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc as MArc  # noqa: E402
from matplotlib.patches import Circle as MCircle  # noqa: E402

from . import figstyle as fs  # noqa: E402

Point = tuple[float, float]
_HALO = [pe.withStroke(linewidth=2.6, foreground="white")]


# --- canvas + primitives -----------------------------------------------------
@dataclass
class Canvas:
    figsize: tuple[float, float] = (5.0, 4.6)
    aspect: str | float = "auto"          # "equal" for geometry
    frame: str = "off"                    # figstyle.style_axes frame: off|lb|box|center
    grid: bool = False
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    title: str | None = None


@dataclass
class Polyline:
    """A path (the object outline, a function curve, any multi-point line)."""
    points: list[Point]
    role: str = "ink"
    width: float = 2.2
    dash: object = "solid"
    closed: bool = False
    alpha: float = 1.0
    z: int = 4


@dataclass
class Line:
    """A styled segment. `family` (int) → a paired hue+dash from the ramp (redundant encoding
    that survives a B/W photocopy); else `role`/`color` + `dash`."""
    p: Point
    q: Point
    family: int | None = None
    role: str = "ink"
    width: float = 1.3
    dash: object = "solid"
    alpha: float = 0.95
    z: int = 3


@dataclass
class PointMark:
    p: Point
    label: str | None = None
    role: str = "focus"
    family: int | None = None
    size: float = 6.5
    label_offset: Point = (0.16, 0.16)
    leader: bool = False
    bold: bool = True
    z: int = 6


@dataclass
class CircleShape:
    center: Point
    radius: float
    role: str = "ink"
    family: int | None = None
    width: float = 1.4
    dash: object = "solid"
    fill: bool = False
    alpha: float = 1.0
    z: int = 2


@dataclass
class Arc:
    """A circular arc (e.g. an angle mark), optionally labelled at its mid-angle."""
    center: Point
    radius: float
    theta1: float
    theta2: float
    label: str | None = None
    role: str = "ink"
    width: float = 1.1
    z: int = 5


@dataclass
class Region:
    """A filled area (a polygon, or sampled points under a curve) — the shaded integral, a
    Riemann rectangle, the area between two curves. Optional outline via `edge_role`."""
    points: list[Point]
    role: str = "focus"
    alpha: float = 0.18
    edge_role: str | None = None
    edge_width: float = 1.0
    z: int = 1


@dataclass
class Label:
    p: Point
    text: str
    role: str = "ink"
    size: float = 9.0
    ha: str = "center"
    va: str = "center"
    halo: bool = True
    bold: bool = False
    z: int = 7


@dataclass
class Scene:
    canvas: Canvas = field(default_factory=Canvas)
    layers: list = field(default_factory=list)

    def add(self, *layers) -> "Scene":
        self.layers.extend(layers)
        return self


# --- rendering ---------------------------------------------------------------
def _color(role_or_color: str) -> str:
    """Resolve a semantic role name (`figstyle.PALETTE`) to its colour; pass a literal through."""
    return getattr(fs.PALETTE, role_or_color, role_or_color)


def _line_style(prim) -> dict:
    if prim.family is not None:
        st = fs.line_kind(prim.family, lw=prim.width)
        st["alpha"] = prim.alpha
        return st
    return {"color": _color(prim.role), "linestyle": prim.dash,
            "linewidth": prim.width, "alpha": prim.alpha}


def render_scene(scene: Scene, ax) -> None:
    """Draw every layer of `scene` onto `ax` (style already scoped by the caller)."""
    fs.style_axes(ax, frame=scene.canvas.frame, grid=scene.canvas.grid)
    if scene.canvas.aspect != "auto":
        ax.set_aspect(scene.canvas.aspect)
    for L in scene.layers:
        if isinstance(L, Region):
            xs = [p[0] for p in L.points]
            ys = [p[1] for p in L.points]
            ax.fill(xs, ys, facecolor=fs.region_fill(_color(L.role), L.alpha),
                    edgecolor=_color(L.edge_role) if L.edge_role else "none",
                    lw=L.edge_width if L.edge_role else 0, zorder=L.z)
        elif isinstance(L, CircleShape):
            col = fs.CATEGORICAL[L.family] if L.family is not None else _color(L.role)
            ax.add_patch(MCircle(L.center, L.radius, fill=L.fill,
                                 facecolor=col if L.fill else "none", edgecolor=col,
                                 lw=L.width, linestyle=L.dash, alpha=L.alpha, zorder=L.z))
        elif isinstance(L, Arc):
            ax.add_patch(MArc(L.center, 2 * L.radius, 2 * L.radius, angle=0,
                              theta1=L.theta1, theta2=L.theta2, color=_color(L.role),
                              lw=L.width, zorder=L.z))
            if L.label:
                import math
                m = math.radians((L.theta1 + L.theta2) / 2)
                ax.text(L.center[0] + L.radius * 1.6 * math.cos(m),
                        L.center[1] + L.radius * 1.6 * math.sin(m), L.label,
                        fontsize=fs.TYPE.annot, color=_color(L.role), ha="center",
                        va="center", zorder=L.z + 2, path_effects=_HALO)
        elif isinstance(L, Line):
            ax.plot([L.p[0], L.q[0]], [L.p[1], L.q[1]], **_line_style(L), zorder=L.z)
        elif isinstance(L, Polyline):
            pts = L.points + ([L.points[0]] if L.closed and L.points else [])
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=_color(L.role),
                    linestyle=L.dash, lw=L.width, alpha=L.alpha, zorder=L.z,
                    solid_capstyle="round")
        elif isinstance(L, PointMark):
            col = fs.CATEGORICAL[L.family] if L.family is not None else _color(L.role)
            ax.plot([L.p[0]], [L.p[1]], "o", color=col, ms=L.size, mec="white", mew=1.2,
                    zorder=L.z)
            if L.label:
                lp = (L.p[0] + L.label_offset[0], L.p[1] + L.label_offset[1])
                if L.leader:
                    ax.plot([L.p[0], lp[0]], [L.p[1], lp[1]], color=col, lw=0.6, zorder=L.z - 1)
                ax.text(lp[0], lp[1], L.label, fontsize=fs.TYPE.annot_lg,
                        fontweight="bold" if L.bold else "normal", color=col, ha="center",
                        va="center", zorder=L.z + 1, path_effects=_HALO)
        elif isinstance(L, Label):
            ax.text(L.p[0], L.p[1], L.text, fontsize=L.size, color=_color(L.role), ha=L.ha,
                    va=L.va, fontweight="bold" if L.bold else "normal", zorder=L.z,
                    path_effects=_HALO if L.halo else None)
    if scene.canvas.xlim:
        ax.set_xlim(*scene.canvas.xlim)
    if scene.canvas.ylim:
        ax.set_ylim(*scene.canvas.ylim)
    if scene.canvas.title:
        ax.set_title("\n".join(__import__("textwrap").wrap(scene.canvas.title, 48)))


def scene_to_png(scene: Scene, path: Path, *, dpi: int = 165) -> Path:
    """Render a Scene to a PNG. Style is scoped (rc_context) so it does NOT restyle the
    not-yet-ported recipes built elsewhere in the same process."""
    with plt.rc_context(fs.house_rc()):
        fig, ax = plt.subplots(figsize=scene.canvas.figsize, layout="constrained")
        render_scene(scene, ax)
        fig.savefig(path, dpi=dpi)
        plt.close(fig)
    return path
