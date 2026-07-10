"""Physics vector scenes — vector addition (Kräfteaddition) and the free-body diagram
(Kräfteplan), the third scene-engine recipe family (after geometry and analysis).

Correct-by-construction: the author/LLM gives only the INPUT vectors (magnitude + direction,
or components) — the **resultant is COMPUTED from the component sum**, never authored, so the
figure can never show a wrong Kräftesumme or a mis-drawn parallelogram diagonal. Value labels
are maskable (`show_value=False` → "F_R = ?"), so one scene serves the student task and the
teacher solution. Arrow lengths are drawn **true to scale** (a force twice as large IS twice
as long — the honesty rule for representation applies to diagrams, not only charts).

Conventions (documented for authors, enforced by code):
* Angles are in DEGREES, measured from the +x axis, counterclockwise (mathematically
  positive): 0° = right, 90° = up, 270° (or −90°) = down.
* A simple symbolic label ("F_1", "F_G", "F_res") is typeset via mathtext with a vector
  arrow, letter subscripts upright (physics convention: a *label* subscript is roman,
  F⃗_G, while the magnitude is written without the arrow, "F_G = 20 N"). Anything already
  containing `$`, or a plain word ("Gewichtskraft"), passes through verbatim.

Anchors (plausibility, not enforced here): PHY Unterstufe 3. Klasse *Mechanik*
(PHY.US.3.MEC.02/03 — die Wirkung verschiedener Kräfte qualitativ untersuchen; the
qualitative approach to the Newtonian relation between force and change of motion) and the
Oberstufe vector strand (MAT: Vektoren).

Builds `scene.Scene` objects (the shared substrate); the Asset generators in `assets.py`
wrap these. Imports only the scene primitives + math.
"""
from __future__ import annotations

import math
import re

from . import figstyle as fs
from .scene import Arrow, Canvas, Label, Line, PointMark, Polyline, Region, Scene


# --- the computed core ---------------------------------------------------------
def vector_components(v) -> tuple[float, float]:
    """Normalise one vector spec to components (dx, dy). Accepts {"dx","dy"} or
    {"magnitude","angle_deg"} (degrees from +x, counterclockwise) — or a (dx, dy) pair.
    A zero/negative magnitude is rejected (a negative magnitude is a hidden direction
    flip — the author must say what they mean)."""
    if isinstance(v, dict):
        if "dx" in v or "dy" in v:
            return float(v.get("dx", 0.0)), float(v.get("dy", 0.0))
        if "magnitude" in v:
            m = float(v["magnitude"])
            if m <= 0:
                raise ValueError(f"vector magnitude must be > 0, got {m}")
            a = math.radians(float(v.get("angle_deg", 0.0)))
            return m * math.cos(a), m * math.sin(a)
        raise ValueError(f"vector spec needs dx/dy or magnitude/angle_deg, got {sorted(v)}")
    dx, dy = float(v[0]), float(v[1])
    return dx, dy


def resultant(vectors) -> tuple[float, float]:
    """The computed resultant (Σdx, Σdy) — the correctness core of both recipes."""
    rx = ry = 0.0
    for v in vectors:
        dx, dy = vector_components(v)
        rx += dx
        ry += dy
    return rx, ry


def _de(v: float) -> str:
    """German decimal-comma number; integers without a trailing ',0'."""
    v = round(float(v), 2)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")


_SYMBOL = re.compile(r"^[A-Za-z][A-Za-z0-9]?(?:_([A-Za-z0-9]{1,6}))?$")


def _mathify(label: str, *, vec: bool = True) -> str:
    """Deterministic label typesetting. '$…$' passes verbatim; a bare symbol 'F' /
    'F_G' / 'F_res' becomes mathtext — with a vector arrow when `vec` (an arrow in a
    figure IS a vector), letter subscripts upright (they are labels: F⃗_G, not
    variables), digit subscripts as-is (F⃗_1). A plain word ('Gewichtskraft') stays
    plain text. Pass an explicit '$…$' to override (e.g. a variable subscript F_x)."""
    m = _SYMBOL.match(label or "")
    if "$" in (label or "") or not m:
        return label
    head, _, sub = label.partition("_")
    core = rf"\vec{{{head}}}" if vec else head
    if sub:
        core += f"_{{{sub}}}" if sub.isdigit() else rf"_{{\mathrm{{{sub}}}}}"
    return f"${core}$"


def _value_text(name: str, value: float | None, unit: str, *, show: bool) -> str:
    """'F_R = 5,4 N' (magnitude — written without the vector arrow) or 'F_R = ?'."""
    sym = _mathify(name, vec=False)
    if not show or value is None:
        return f"{sym} = ?"
    sfx = f" {unit}" if unit else ""
    return f"{sym} = {_de(value)}{sfx}"


def _perp_offset(p, q, centroid, span: float, *, factor: float = 0.055) -> tuple[float, float]:
    """A label offset perpendicular to segment p→q, on the side pointing AWAY from
    `centroid` (so mid-shaft labels fan outward, not into the figure)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
    if nx * (mx - centroid[0]) + ny * (my - centroid[1]) < 0:
        nx, ny = -nx, -ny
    off = span * factor
    return nx * off, ny * off


# --- vector addition -------------------------------------------------------------
def vector_addition_scene(vectors, method: str = "tip_to_tail", *,
                          show_resultant: bool = True, show_value: bool = True,
                          unit: str = "N", resultant_name: str = "F_R", **opts) -> Scene:
    """Vector addition, drawn true to scale on a quiet grid. `method="tip_to_tail"` chains
    the vectors (any number); `"parallelogram"` needs exactly two from a common origin and
    completes the parallelogram with muted helper dashes. The resultant (origin → final tip
    resp. the diagonal) is COMPUTED from the component sum; its magnitude label masks via
    `show_value=False` → "F_R = ?". `show_resultant=False` draws only the given vectors
    (the construction task)."""
    comps = [vector_components(v) for v in vectors]
    if not comps:
        raise ValueError("vector_addition needs at least one vector")
    labels = [(v.get("label") if isinstance(v, dict) else None) or f"F_{i + 1}"
              for i, v in enumerate(vectors)]
    if method == "parallelogram" and len(comps) != 2:
        raise ValueError(f"method='parallelogram' needs exactly 2 vectors, got {len(comps)}")

    rx, ry = resultant(vectors)
    origin = (0.0, 0.0)

    # arrow geometry (positions only; labels are attached after the extent is known)
    arrows: list[tuple[tuple[float, float], tuple[float, float], str]] = []
    helpers: list[tuple[tuple[float, float], tuple[float, float]]] = []
    if method == "parallelogram":
        tips = [comps[0], comps[1]]
        for (dx, dy), lab in zip(comps, labels):
            arrows.append((origin, (dx, dy), lab))
        helpers = [(tips[0], (rx, ry)), (tips[1], (rx, ry))]
    else:                                     # tip_to_tail
        cur = origin
        for (dx, dy), lab in zip(comps, labels):
            nxt = (cur[0] + dx, cur[1] + dy)
            arrows.append((cur, nxt, lab))
            cur = nxt

    pts = [origin, (rx, ry)] + [p for a in arrows for p in (a[0], a[1])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    cen = (sum(xs) / len(xs), sum(ys) / len(ys))

    sc = Scene(canvas=Canvas(aspect="equal", frame="lb", grid=True))
    for p, q, lab in arrows:
        sc.add(Arrow(p, q, role="primary", width=2.0, label=_mathify(lab),
                     label_offset=_perp_offset(p, q, cen, span), z=5))
    for p, q in helpers:
        sc.add(Line(p, q, role="muted", width=1.0, dash=(0, (5, 3)), z=3))
    if show_resultant:
        sc.add(Arrow(origin, (rx, ry), role="focus", width=2.5,
                     label=_value_text(resultant_name,
                                       math.hypot(rx, ry), unit, show=show_value),
                     label_offset=_perp_offset(origin, (rx, ry), cen, span,
                                               factor=-0.075), z=6))

    pad = span * 0.18 + 0.02 * span
    xlim = (min(xs) - pad, max(xs) + pad)
    ylim = (min(ys) - pad, max(ys) + pad)
    sc.canvas.xlim, sc.canvas.ylim = xlim, ylim
    if xlim[0] <= 0 <= xlim[1] and ylim[0] <= 0 <= ylim[1]:
        sc.canvas.frame = "center"
    w = 5.6
    h = min(max(w * (ylim[1] - ylim[0]) / (xlim[1] - xlim[0]), 3.2), 5.6)
    sc.canvas.figsize = (w, h)
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc


# --- free-body diagram -----------------------------------------------------------
def force_diagram_scene(forces, *, body_label: str | None = None,
                        show_magnitudes: bool = True, show_resultant: bool = False,
                        show_value: bool = True, unit: str = "N",
                        resultant_name: str = "F_res", **opts) -> Scene:
    """A free-body diagram (Kräfteplan): a small box for the body, every force an arrow from
    its centre, lengths true to scale. Unterstufe simplification (documented): all forces are
    drawn from the body's centre point. `show_resultant=True` adds the COMPUTED resultant
    (focus red); equilibrium renders honestly as "F_res = 0 N" (no arrow); `show_value=False`
    masks it to "F_res = ?" without leaking whether the forces balance."""
    if not forces:
        raise ValueError("force_diagram needs at least one force")
    comps = [vector_components(f) for f in forces]
    labels = [(f.get("label") if isinstance(f, dict) else None) or f"F_{i + 1}"
              for i, f in enumerate(forces)]
    mags = [math.hypot(dx, dy) for dx, dy in comps]
    scale = 3.0 / max(mags)                          # longest arrow = 3 data units
    rx, ry = resultant(forces)
    rmag = math.hypot(rx, ry)
    equilibrium = rmag < 1e-9 * max(mags)

    sc = Scene(canvas=Canvas(aspect="equal", frame="off", grid=False))
    half = 0.28                                       # body half-size (data units)
    box = [(-half, -half), (half, -half), (half, half), (-half, half)]
    sc.add(Region(box, role="surface", alpha=1.0, edge_role="ink", edge_width=1.6, z=2))
    if body_label:
        sc.add(Label((0, 0), _mathify(body_label, vec=False), role="ink",
                     size=fs.TYPE.annot, bold=True, z=4))
    else:
        sc.add(PointMark((0, 0), role="ink", size=3.4, z=4))

    tips = []
    for (dx, dy), lab, mag in zip(comps, labels, mags):
        tip = (dx * scale, dy * scale)
        tips.append(tip)
        text = _mathify(lab)
        if show_magnitudes:
            text = _value_text(lab, mag, unit, show=True)
        ux, uy = tip[0] / (mag * scale), tip[1] / (mag * scale)
        lp = (tip[0] + ux * 0.34, tip[1] + uy * 0.34)
        ha = "left" if ux > 0.35 else ("right" if ux < -0.35 else "center")
        va = "bottom" if uy > 0.35 else ("top" if uy < -0.35 else "center")
        sc.add(Arrow((0, 0), tip, role="primary", width=2.1, z=5))
        sc.add(Label(lp, text, role="primary", size=fs.TYPE.annot_lg, ha=ha, va=va,
                     bold=True, z=7))

    if show_resultant:
        rtxt = _value_text(resultant_name, 0.0 if equilibrium else rmag, unit,
                           show=show_value)
        if equilibrium or not show_value:
            # no arrow: arrows are true to scale, so a masked resultant arrow would
            # leak the answer to anyone with a ruler (and equilibrium HAS no arrow)
            sc.add(Label((0, -3.0 * 0.42 - half), rtxt, role="focus",
                         size=fs.TYPE.annot_lg, bold=True, va="top", z=7))
        else:
            tip = (rx * scale, ry * scale)
            cen = (0.0, 0.0)
            sc.add(Arrow((0, 0), tip, role="focus", width=2.4, label=rtxt,
                         label_offset=_perp_offset((0, 0), tip, cen, 6.0, factor=0.09), z=6))

    xs = [p[0] for p in tips] + [-half, half]
    ys = [p[1] for p in tips] + [-half, half, -3.0 * 0.42 - half if show_resultant else 0.0]
    pad = 3.0 * 0.42
    sc.canvas.xlim = (min(xs) - pad, max(xs) + pad)
    sc.canvas.ylim = (min(ys) - pad, max(ys) + pad)
    w = 5.2
    xspan = sc.canvas.xlim[1] - sc.canvas.xlim[0]
    yspan = sc.canvas.ylim[1] - sc.canvas.ylim[0]
    sc.canvas.figsize = (w, min(max(w * yspan / xspan, 3.0), 5.6))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc
