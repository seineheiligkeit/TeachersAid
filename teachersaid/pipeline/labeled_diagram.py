""""Beschrifte die Teile" diagrams — annotated schematic figures over the scene engine.

A labelled diagram is TWO projections of ONE spec: `show_names=False` renders numbered
callout markers with leader lines (the student sheet — write the names on the task's
answer lines), `show_names=True` renders the names (the teacher solution / the learn
figure). The correct-by-construction guarantee here is the one that matters for a
labelling task: the numbering, the leader targets, and the solution names are all DERIVED
from the same `parts` list, so the student figure and the answer key cannot drift apart —
masking is a projection, exactly like `show_value=False` in the analysis scenes.

The shapes are explicitly SCHEMATIC (a didactic cross-section built from primitives, not a
data figure — nothing here claims measured values), which is why a spec may freely place
polylines/circles/regions; what is load-bearing is the parts↔names correspondence. Colour
may be representational (magma red, ash grey) — the semantic-role discipline applies to
data/geometry figures; a schematic names its colours per shape.

Layout follows the house *measure → fit → de-collide* discipline (`pipeline/figtext.py`):
callout labels sit on the left/right margins, stacked top-down with measured text heights
(so labels in one column can never collide), leaders never cross within a side (slots are
assigned in anchor order), and the canvas window is widened by the MEASURED label widths
(two fit passes, because under an equal-aspect axes the data↔pixel scale moves when the
window does).

Flagship spec: `VULKAN_SPEC` — the classic GWB "Beschrifte den Vulkan" cross-section
(Magmakammer · Schlot · Krater · Lavastrom · Aschewolke · Vulkankegel), plausibly anchored
by GWB.US.1.LEB4.02 (1. Klasse, *Leben und Wirtschaften unter Beachtung der natürlichen
Prozesse* — Naturgefahren).

Builds `scene.Scene` objects; the Asset generator in `assets.py` wraps this. Imports only
the scene primitives + figstyle + figtext.
"""
from __future__ import annotations

from . import figstyle as fs
from .figtext import measure_widths
from .scene import (Canvas, CircleShape, Label, Line, PointMark, Polyline, RasterImage,
                    Region, Scene)


# --- shapes: spec dicts → scene primitives ------------------------------------
def _shape_layers(shapes: list[dict]) -> list:
    """Map declarative shape dicts onto scene primitives. Spec order is paint order
    (later shapes draw on top — a cut-away chamber is painted over the mountain body).
    An unknown `kind` raises (surface the mistake; never silently skip a shape)."""
    layers = []
    for i, s in enumerate(shapes):
        kind = s.get("kind")
        z = 1 + i                                  # spec order = paint order
        color = s.get("color") or s.get("role") or "ink"
        if kind == "region":
            layers.append(Region([tuple(p) for p in s["points"]], role=color,
                                 alpha=float(s.get("alpha", 1.0)),
                                 edge_role=s.get("edge"),
                                 edge_width=float(s.get("edge_width", 1.6)), z=z))
        elif kind == "circle":
            layers.append(CircleShape(tuple(s["center"]), float(s["radius"]), role=color,
                                      width=float(s.get("width", 1.4)),
                                      fill=bool(s.get("fill", True)),
                                      alpha=float(s.get("alpha", 1.0)), z=z))
        elif kind == "polyline":
            layers.append(Polyline([tuple(p) for p in s["points"]], role=color,
                                   width=float(s.get("width", 2.2)),
                                   closed=bool(s.get("closed", False)),
                                   alpha=float(s.get("alpha", 1.0)), z=z))
        elif kind == "line":
            layers.append(Line(tuple(s["p"]), tuple(s["q"]), role=color,
                               width=float(s.get("width", 1.3)),
                               dash=s.get("dash", "solid"), z=z))
        else:
            raise ValueError(f"unknown shape kind {kind!r} (shape #{i})")
    return layers


def _shape_bbox(shapes: list[dict], parts: list[dict],
                background: dict | None = None) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for s in shapes:
        if "points" in s:
            xs += [float(p[0]) for p in s["points"]]
            ys += [float(p[1]) for p in s["points"]]
        if "center" in s:
            r = float(s.get("radius", 0))
            xs += [s["center"][0] - r, s["center"][0] + r]
            ys += [s["center"][1] - r, s["center"][1] + r]
        for key in ("p", "q"):
            if key in s:
                xs.append(float(s[key][0]))
                ys.append(float(s[key][1]))
    for p in parts:
        xs.append(float(p["at"][0]))
        ys.append(float(p["at"][1]))
    if background:
        extent = background.get("extent")
        if not extent or len(extent) != 4:
            raise ValueError("labeled_parts background needs extent [left,right,bottom,top]")
        xs += [float(extent[0]), float(extent[1])]
        ys += [float(extent[2]), float(extent[3])]
    if not xs:
        raise ValueError("labeled_parts needs at least one shape or part")
    return min(xs), min(ys), max(xs), max(ys)


# --- measured label metrics (the figtext discipline) ---------------------------
def _measure(figsize, xlim, ylim, texts: list[str], size: float) -> tuple[list[float], float]:
    """Label widths (data units) + one text height (data units) on a throwaway axes with
    the SAME figsize/lims/aspect as the final render — measured, not guessed. Bold labels
    measure slightly wider than the normal-weight probe; callers pad for that."""
    import matplotlib.pyplot as plt

    with plt.rc_context(fs.house_rc()):
        fig, ax = plt.subplots(figsize=figsize)
        try:
            ax.set_aspect("equal")
            ax.set_xlim(*xlim)
            ax.set_ylim(*ylim)
            widths = measure_widths(ax, texts, size) if texts else []
            fig.canvas.draw()
            probe = ax.text(0, 0, "Ag", fontsize=size)
            bb = probe.get_window_extent(fig.canvas.get_renderer())
            inv = ax.transData.inverted()
            (_, y0), (_, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
            probe.remove()
        finally:
            plt.close(fig)
    return widths, abs(y1 - y0)


# --- the recipe -----------------------------------------------------------------
def labeled_parts_scene(spec: dict, *, show_names: bool | None = None) -> Scene:
    """A "Beschrifte die Teile" figure from `spec` = {shapes, parts, title?, figsize?,
    show_names?}. Each part {at:[x,y], name:str, side?:"left"|"right"} becomes a numbered
    margin callout (number = position in the parts list — the spec's didactic order) with
    a leader line to its anchor point; `show_names=True` appends the names (the solution)."""
    shapes = spec.get("shapes") or []
    parts = spec.get("parts") or []
    if show_names is None:
        show_names = bool(spec.get("show_names", True))
    background = spec.get("background")
    x0, y0, x1, y1 = _shape_bbox(shapes, parts, background)
    bw, bh = (x1 - x0) or 1.0, (y1 - y0) or 1.0
    figsize = tuple(spec.get("figsize") or (6.2, 4.8))
    size = fs.TYPE.annot if show_names else fs.TYPE.annot_lg

    # side assignment: spec override, else nearest margin
    cx = (x0 + x1) / 2
    entries = []                                     # (index, part, side, text)
    for i, p in enumerate(parts):
        side = p.get("side") or ("left" if float(p["at"][0]) <= cx else "right")
        text = f"{i + 1}  {p['name']}" if show_names else f"{i + 1}"
        entries.append((i, p, side, text))

    # measured fit: two passes, because equal-aspect rescales when the window widens
    lead = 0.07 * bw                                 # bbox edge → leader end
    tick = 0.015 * bw                                # leader end → text start
    xlim = (x0 - 0.05 * bw, x1 + 0.05 * bw)
    ylim = (y0 - 0.06 * bh, y1 + 0.06 * bh)
    slots: dict[int, float] = {}
    for _ in range(2):
        widths, th = _measure(figsize, xlim, ylim, [e[3] for e in entries], size)
        gap = 1.65 * th
        wmax = {"left": 0.0, "right": 0.0}
        for (idx, _p, side, _t), w in zip(entries, widths):
            wmax[side] = max(wmax[side], w * 1.12)   # bold/halo safety on the probe
        slots = {}
        for side in ("left", "right"):
            col = [e for e in entries if e[2] == side]
            col.sort(key=lambda e: -float(e[1]["at"][1]))          # top-down
            prev = None
            for e in col:
                want = float(e[1]["at"][1])
                y = want if prev is None else min(want, prev - gap)
                slots[e[0]] = y
                prev = y
        margin = 0.04 * (xlim[1] - xlim[0])
        xlim = (x0 - lead - tick - wmax["left"] - margin,
                x1 + lead + tick + wmax["right"] + margin)
        ylo = min([y0] + [slots[i] - th for i in slots]) - 0.06 * bh
        yhi = max([y1] + [slots[i] + th for i in slots]) + 0.06 * bh
        ylim = (ylo, yhi)

    sc = Scene(canvas=Canvas(figsize=figsize, aspect="equal", frame="off",
                             xlim=xlim, ylim=ylim))
    if background:
        path = background.get("path")
        if not path:
            raise ValueError("labeled_parts background must be resolved to a file path")
        sc.add(RasterImage(str(path), tuple(float(v) for v in background["extent"]),
                           alpha=float(background.get("alpha", 1.0))))
    sc.add(*_shape_layers(shapes))
    zbase = 40                                       # callouts above every shape
    for idx, p, side, text in entries:
        at = (float(p["at"][0]), float(p["at"][1]))
        ax_ = x0 - lead if side == "left" else x1 + lead
        tx = ax_ - tick if side == "left" else ax_ + tick
        ha = "right" if side == "left" else "left"
        sc.add(PointMark(at, role="ink", size=3.8, z=zbase + 2))
        sc.add(Line(at, (ax_, slots[idx]), role="muted", width=fs.STROKE.leader,
                    z=zbase + 1))
        sc.add(Label((tx, slots[idx]), text, role="ink" if show_names else "primary",
                     size=size, ha=ha, va="center", bold=not show_names, z=zbase + 3))
    if spec.get("title"):
        sc.canvas.title = str(spec["title"])
    return sc


# --- flagship spec ----------------------------------------------------------------
# The classic 1./2.-Klasse GWB volcano cross-section: solid schematic shapes (a cut-away
# chamber + conduit painted over the cone), representational colour, six parts in eruption
# order. Deliberately composed from primitives a Scene draws WELL — filled regions, a thick
# lava polyline, a cloud of overlapping circles.
VULKAN_SPEC: dict = {
    "title": "Aufbau eines Vulkans (Schema)",
    "figsize": (6.4, 4.9),
    "shapes": [
        {"kind": "region", "points": [[0, 0], [10, 0], [10, 1.1], [0, 1.1]],
         "color": "#d9c3a4"},                                     # deeper crust stratum
        {"kind": "region", "points": [[0, 1.1], [10, 1.1], [10, 2.2], [0, 2.2]],
         "color": "#e7d8bd"},                                     # upper crust stratum
        {"kind": "line", "p": [0, 2.2], "q": [10, 2.2], "color": "ink", "width": 1.5},
        {"kind": "region",                                        # the cone, crater notch
         "points": [[1.1, 2.2], [2.5, 3.5], [3.6, 5.0], [4.15, 6.3], [4.55, 6.02],
                    [4.95, 6.32], [5.65, 5.1], [6.9, 3.5], [8.9, 2.2]],
         "color": "#b08f72", "edge": "ink", "edge_width": 2.0},
        {"kind": "circle", "center": [4.75, 1.05], "radius": 0.95,
         "color": "#e05a33"},                                     # magma chamber (cut-away)
        {"kind": "region",                                        # conduit, chamber → crater
         "points": [[4.5, 1.6], [4.62, 6.12], [4.88, 6.12], [5.0, 1.6]],
         "color": "#e05a33"},
        {"kind": "polyline",                                      # lava flow down the flank
         "points": [[4.97, 6.28], [5.68, 5.14], [6.93, 3.54], [8.55, 2.26]],
         "color": "#c8432c", "width": 5.0},
        {"kind": "circle", "center": [4.25, 7.45], "radius": 0.38, "color": "#a7b0b7"},
        {"kind": "circle", "center": [4.75, 7.2], "radius": 0.5, "color": "#a7b0b7"},
        {"kind": "circle", "center": [5.35, 7.55], "radius": 0.62, "color": "#a7b0b7"},
        {"kind": "circle", "center": [6.1, 7.8], "radius": 0.58, "color": "#a7b0b7"},
        {"kind": "circle", "center": [6.9, 7.95], "radius": 0.48, "color": "#a7b0b7"},
    ],
    "parts": [                                       # numbering = eruption order
        {"at": [4.5, 0.95], "name": "Magmakammer", "side": "left"},
        {"at": [4.7, 4.1], "name": "Schlot", "side": "left"},
        {"at": [4.75, 6.15], "name": "Krater", "side": "right"},
        {"at": [6.93, 3.54], "name": "Lavastrom", "side": "right"},
        {"at": [6.0, 7.8], "name": "Aschewolke", "side": "right"},
        {"at": [3.35, 3.6], "name": "Vulkankegel", "side": "left"},
    ],
}


# Wave-B hybrid flagship: generated pixels provide only the botanical depiction;
# these curated anchors, numbering and answer names remain deterministic code.
# The referenced file stays independently SME-gated in AssetStore.
FLOWER_HYBRID_SPEC: dict = {
    "title": "Aufbau einer Blüte (vereinfachtes Modell)",
    "figsize": (7.2, 5.2),
    "background": {
        "asset_id": "img-bio-flower-cutaway",
        "extent": [0, 12, 0, 8],
    },
    "parts": [
        {"at": [2.6, 5.1], "name": "Kronblatt", "side": "left"},
        {"at": [2.9, 2.8], "name": "Kelchblatt", "side": "left"},
        {"at": [4.0, 5.8], "name": "Staubbeutel", "side": "left"},
        {"at": [6.0, 6.3], "name": "Narbe", "side": "right"},
        {"at": [6.0, 4.6], "name": "Griffel", "side": "right"},
        {"at": [6.0, 2.3], "name": "Fruchtknoten", "side": "right"},
        {"at": [6.45, 2.15], "name": "Samenanlage", "side": "right"},
    ],
}
