"""Geometric-optics scenes from the RECTILINEAR-propagation model (geradlinige Lichtausbreitung)
— the shadow-projection family, complementing the refraction/lens family in `optics.py`.

Two didactic recipes, both COMPUTED from a small correct-by-construction spec (the two-tier rule:
the LLM never draws a ray — it declares a spec, code lays down the geometry):

  * `pinhole_scene` — die Lochkamera. An upright object, its light through the SINGLE hole of a
    Lochblende, and the inverted image on the screen. The single aperture FORCES the tip-ray and
    the base-ray to cross at the hole, so the image is upside-down BY CONSTRUCTION; the image
    height follows the similar triangles B = G·b/a. That crossing is exactly what the "warum steht
    das Bild kopf?" task asks — the figure answers it geometrically, it cannot show an upright image.

  * `shadow_scene` — der Schattenraum (Kernschatten) hinter einer Kugel. Closed-form tangent lines
    from an external POINT source to the sphere (the two grazing rays, tangent points where the
    radius is perpendicular to the ray); the umbra is the wedge behind the sphere bounded by those
    tangents. A point source gives exactly ONE tangent per side → a single, SHARP boundary (no
    penumbra) — the answer to "warum ist der Schatten überall gleich scharf begrenzt?". An extended
    source would give a fan of grazing rays and a Halbschatten; the point source cannot.

Both masking hooks follow the gegeben→gesucht split of `optics.py`: the givens stay visible,
`show_value=False` masks only the sought quantity ("B = ?"). For the delivered worksheets the full
construction is shown.

Pure: imports only the scene primitives + numpy. The Asset generators
(`assets.matplotlib:pinhole_camera` / `matplotlib:shadow_cone`) wrap these for the engine.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .scene import Arrow, Canvas, CircleShape, Label, Line, Region, Scene

Point = tuple[float, float]


def _pt(x, y) -> Point:
    return (float(x), float(y))


# =====================================================================================
# A — Lochkamera (pinhole camera)
# =====================================================================================
@dataclass
class PinholeSpec:
    """A correct-by-construction Lochkamera setup, positive magnitudes. The pinhole sits at the
    origin, the optical axis is the x-axis; the object is on the left, the screen on the right."""
    G: float = 3.0   # Gegenstandsgröße (object height)
    a: float = 6.0   # Gegenstandsweite (object → hole distance)
    b: float = 4.0   # Bildweite (hole → screen distance)


def pinhole_geometry(spec: PinholeSpec) -> dict:
    """The image quantities from the SINGLE-hole geometry. B = G·b/a by similar triangles; the
    image is inverted (tip below the axis) because both rays cross at the hole."""
    G, a, b = float(spec.G), float(spec.a), float(spec.b)
    if G <= 0 or a <= 0 or b <= 0:
        raise ValueError("G, a and b must be positive magnitudes")
    B = G * b / a
    return dict(G=G, a=a, b=b, B=B,
                obj_base=_pt(-a, 0.0), obj_tip=_pt(-a, G),
                hole=_pt(0.0, 0.0),
                img_base=_pt(b, 0.0), img_tip=_pt(b, -B))


def pinhole_scene(spec: PinholeSpec, *, show_value: bool = True) -> Scene:
    """The Lochkamera ray diagram — COMPUTED from the spec. The two rays (object tip → hole →
    screen, object base → hole → screen) cross at the hole, so the image is inverted by
    construction. `show_value=False` masks only the sought image height ("B = ?")."""
    geo = pinhole_geometry(spec)
    G, B, a, b = geo["G"], geo["B"], geo["a"], geo["b"]
    tip, base, hole = geo["obj_tip"], geo["obj_base"], geo["hole"]
    itip, ibase = geo["img_tip"], geo["img_base"]

    top = max(G, B) + 0.9                         # barrier / screen half-height
    x_left, x_right = -a, b
    padx = (x_right - x_left) * 0.10 + 0.9
    sc = Scene(canvas=Canvas(figsize=(7.4, 4.5), aspect="equal", frame="off"))

    # optical axis — a quiet reference line through object foot, hole and image foot
    sc.add(Line(_pt(x_left - padx * 0.7, 0), _pt(x_right + padx * 0.7, 0),
                role="muted", width=1.0, dash=(0, (6, 4)), z=1))

    # the two light rays: object TIP → hole → screen (crosses to below the axis) and object
    # BASE → hole → screen (along the axis). Drawn as two segments so the hole is a visible vertex
    # — the crossing at the hole IS why the image is kopfstehend.
    for src, dst in ((tip, itip), (base, ibase)):
        sc.add(Line(src, hole, role="secondary", width=1.5, z=3))
        sc.add(Line(hole, dst, role="secondary", width=1.5, z=3))

    # the object (Kerze/Gegenstand) — an upright arrow, base on the axis
    sc.add(Arrow(base, tip, role="primary", width=2.4, z=5))
    sc.add(Label(_pt(-a, top * 0.62), "Gegenstand", role="primary", size=10,
                 ha="center", va="bottom", bold=True))
    sc.add(Label(_pt(-a - 0.18, G / 2), "G", role="primary", size=10, ha="right", va="center",
                 bold=True))

    # the Lochblende: two thick vertical bars with a small gap (the hole) exactly on the axis
    gap = 0.16
    sc.add(Line(_pt(0, gap), _pt(0, top), role="ink", width=3.4, z=4))
    sc.add(Line(_pt(0, -gap), _pt(0, -top), role="ink", width=3.4, z=4))
    sc.add(Label(_pt(0, top + 0.10), "Lochblende", role="ink", size=10, ha="center",
                 va="bottom", bold=True))

    # the screen (Rückwand/Mattscheibe) + the inverted image arrow (the result → focus)
    sc.add(Line(_pt(b, -top), _pt(b, top), role="ink", width=2.2, z=3))
    sc.add(Label(_pt(b, top + 0.10), "Schirm", role="ink", size=10, ha="center", va="bottom"))
    sc.add(Arrow(ibase, itip, role="focus", width=2.4, z=5))
    sc.add(Label(_pt(b + 0.20, -B / 2), "B" if show_value else "B = ?", role="focus", size=10,
                 ha="left", va="center", bold=True))
    sc.add(Label(_pt(b, -top - 0.12), "Bild (kopfstehend)", role="focus", size=10,
                 ha="center", va="top", bold=True))

    sc.canvas.xlim = (x_left - padx, x_right + padx + 1.4)
    sc.canvas.ylim = (-top - 0.95, top + 0.75)
    return sc


def pinhole_construction(G: float = 3.0, a: float = 6.0, b: float = 4.0, *,
                         show_value: bool = True) -> Scene:
    """Build the Lochkamera Scene — the public entry point (mirrors optics.lens_construction).
    G, a, b positive magnitudes; the image height B = G·b/a is computed, the image inverted by
    construction. `show_value=False` masks the sought image height ("B = ?")."""
    return pinhole_scene(PinholeSpec(G=G, a=a, b=b), show_value=show_value)


# =====================================================================================
# B — Schattenraum (shadow cone behind a sphere)
# =====================================================================================
@dataclass
class ShadowSpec:
    """A correct-by-construction Schattenwurf setup. `source` is a POINT light source external to
    the sphere; `center`/`r` the Kugel; `screen_x` an optional Wand to the right of the sphere."""
    source: Point = (-6.5, 0.0)
    center: Point = (0.0, 0.0)
    r: float = 1.5
    screen_x: float | None = 6.5


def shadow_geometry(spec: ShadowSpec) -> dict:
    """The two tangent points + tangent rays from the point source to the sphere, closed form.

    Right triangle source–tangent–centre (right angle at the tangent point, |C→T| = r,
    |C→S| = D): the tangent points sit at angle ±α about the source direction, α = arccos(r/D).
    A point source → exactly one tangent per side → one sharp boundary (no penumbra)."""
    S = np.asarray(spec.source, float)
    C = np.asarray(spec.center, float)
    r = float(spec.r)
    if r <= 0:
        raise ValueError("sphere radius r must be positive")
    d = S - C
    D = float(np.linalg.norm(d))
    if D <= r:
        raise ValueError(f"point source must be OUTSIDE the sphere (D={D:.3f} ≤ r={r:.3f})")
    phi = float(np.arctan2(d[1], d[0]))           # direction centre → source
    alpha = float(np.arccos(r / D))               # half-angle of the tangent cone at the centre
    tangents = []
    for sign in (+1, -1):
        theta = phi + sign * alpha
        tangents.append(_pt(C[0] + r * np.cos(theta), C[1] + r * np.sin(theta)))
    return dict(S=_pt(*S), C=_pt(*C), r=r, D=D, alpha=alpha,
                tangents=tangents, far_dir=phi + np.pi)


def _extend(p_from: Point, through: Point, x_target: float) -> Point:
    """The point on the ray p_from→through at abscissa x_target (ray must advance in +x)."""
    (x0, y0), (x1, y1) = p_from, through
    dx = x1 - x0
    if abs(dx) < 1e-12:
        raise ValueError("shadow ray is vertical — source must be off the tangent x")
    t = (x_target - x0) / dx
    return _pt(x_target, y0 + (y1 - y0) * t)


def shadow_scene(spec: ShadowSpec, *, show_screen: bool = True) -> Scene:
    """The Schattenraum scene — COMPUTED from the spec: the sphere, the two grazing tangent rays,
    the shaded Kernschatten wedge between them, and (optionally) the sharp shadow on a screen.
    The sharpness is structural: a point source has one tangent per side, hence one crisp edge."""
    geo = shadow_geometry(spec)
    S, C, r = geo["S"], geo["C"], geo["r"]
    T_a, T_b = geo["tangents"]

    # where the rays terminate: on the screen if given, else past the sphere at the frame edge
    x_end = float(spec.screen_x) if spec.screen_x is not None else C[0] + geo["D"] * 1.15
    P_a = _extend(S, T_a, x_end)
    P_b = _extend(S, T_b, x_end)

    ys = [P_a[1], P_b[1], C[1] + r, C[1] - r, S[1]]
    top = max(abs(y) for y in ys) + 0.8
    x_left = S[0]
    padx = (x_end - x_left) * 0.08 + 0.9
    sc = Scene(canvas=Canvas(figsize=(7.6, 4.6), aspect="equal", frame="off"))

    # the Kernschatten wedge (behind the sphere, between the two tangent rays) — the region of
    # interest. Its left side clips into the sphere; the opaque Kugel is drawn ON TOP, so the fill
    # emerges cleanly from the sphere's far side and opens rightward (a point source → diverging).
    sc.add(Region([T_a, P_a, P_b, T_b], role="focus", alpha=0.20, z=1))

    # the two grazing light rays from the source (tangent at T_a/T_b) — the SHARP boundary; focus
    # so the eye lands on the crisp edges that answer the task.
    sc.add(Line(S, P_a, role="focus", width=1.7, z=3))
    sc.add(Line(S, P_b, role="focus", width=1.7, z=3))

    # the opaque Kugel: a surface-filled disk with an ink outline (two shapes — CircleShape ties
    # face and edge to one role, so the outline is a second shape)
    sc.add(CircleShape(C, r, role="surface", fill=True, width=0.0, z=4))
    sc.add(CircleShape(C, r, role="ink", fill=False, width=1.8, z=5))
    sc.add(Label(_pt(C[0], C[1] + r + 0.16), "Kugel", role="ink", size=10, ha="center",
                 va="bottom", bold=True))

    # the point source + a few radiating ticks (emits in all directions) and its label
    for k in range(8):
        ang = k * np.pi / 4
        sc.add(Line(_pt(S[0] + 0.14 * np.cos(ang), S[1] + 0.14 * np.sin(ang)),
                    _pt(S[0] + 0.42 * np.cos(ang), S[1] + 0.42 * np.sin(ang)),
                    role="ink", width=1.2, z=5))
    sc.add(Label(_pt(S[0], S[1] + 0.62), "punktförmige\nLichtquelle", role="ink", size=9.5,
                 ha="center", va="bottom", bold=True))

    # the Kernschatten label, placed inside the visible wedge (right of the sphere, on the axis)
    lbl_x = C[0] + r + (x_end - C[0] - r) * 0.42
    sc.add(Label(_pt(lbl_x, C[1]), "Kernschatten\n(Schattenraum)", role="focus", size=10,
                 ha="center", va="center", bold=True))

    if show_screen and spec.screen_x is not None:
        sc.add(Line(_pt(x_end, -top + 0.3), _pt(x_end, top - 0.3), role="ink", width=2.2, z=3))
        sc.add(Label(_pt(x_end, top - 0.3 + 0.10), "Wand", role="ink", size=10, ha="center",
                     va="bottom"))
        # the sharp shadow band on the wall (between the two rays' hit points)
        lo, hi = sorted((P_a[1], P_b[1]))
        sc.add(Line(_pt(x_end, lo), _pt(x_end, hi), role="focus", width=4.0, z=6))
        sc.add(Label(_pt(x_end + 0.18, C[1]), "scharfer\nSchattenrand", role="focus", size=9,
                     ha="left", va="center", bold=True))

    right_pad = 2.2 if (show_screen and spec.screen_x is not None) else padx
    sc.canvas.xlim = (x_left - padx, x_end + right_pad)
    sc.canvas.ylim = (-top, top)
    return sc


def shadow_construction(source: Point = (-6.5, 0.0), center: Point = (0.0, 0.0),
                        r: float = 1.5, screen_x: float | None = 6.5, *,
                        show_screen: bool = True) -> Scene:
    """Build the Schattenraum Scene — the public entry point (mirrors optics.lens_construction).
    Point source → closed-form tangents → the umbra wedge; a point source yields exactly one
    sharp boundary per side (no Halbschatten). `screen_x=None` drops the Wand."""
    return shadow_scene(ShadowSpec(source=source, center=center, r=r, screen_x=screen_x),
                        show_screen=show_screen)
