"""Optics ray constructions as computed scenes — the third scene-engine recipe family (after
geometry and analysis), the physics face of "a didactic recipe COMPUTES the figure".

The Bildkonstruktion an einer dünnen Linse (Sammel-/Zerstreuungslinse): the LLM never draws a
ray — it declares a small, correct-by-construction spec (element kind, Brennweite f,
Gegenstandsweite g, Gegenstandsgröße G) and code computes the image via the exact thin-lens
equation (sympy) and lays the drei Hauptstrahlen down as scene primitives. The rays' intersection
IS the image tip, so the figure can never show a wrong image position or leak the answer; the
Bildweite b, Bildgröße B and the magnification are computed and maskable (`show_value=False` →
"b = ?" / "B′ = ?"), so ONE scene serves the student task and the teacher solution. Masking
follows the gegeben→gesucht split: the GIVENS g and G (the spec inputs — a task needs its
Angaben) always stay visible; only the SOUGHT image quantities (b, B, B′) mask.

Sign convention (Austrian Schulbuch, documented deliberately): distances are entered as POSITIVE
magnitudes — f is the Brennweite, g the Gegenstandsweite, G the Gegenstandsgröße — and the LENS
TYPE carries the sign of the focal length internally (Sammellinse +f, Zerstreuungslinse −f). The
Abbildungsgleichung 1/f = 1/g + 1/b is solved for the (signed) Bildweite b: b > 0 is a reelles
Bild on the far (image) side, b < 0 a virtuelles Bild on the object side (its rays are the DASHED
backward extensions). The Abbildungsmaßstab is V = −b/g (negative ⇒ umgekehrtes Bild). The three
regimes fall out of the same formula:

  Sammellinse, g > f : reelles, umgekehrtes Bild (b > 0)
  Sammellinse, g < f : virtuelles, aufrechtes, vergrößertes Bild (b < 0) — the Lupe
  Sammellinse, g = f : kein (endliches) Bild — parallel emerging rays (drawn deliberately)
  Zerstreuungslinse  : immer virtuelles, aufrechtes, verkleinertes Bild (b < 0)

The drei Hauptstrahlen (built cumulatively as `stage`s, mirroring `constructions.py`):
  Parallelstrahl    — parallel in, through F′ out
  Mittelpunktstrahl — straight through the Linsenmitte (undeviated)
  Brennpunktstrahl  — through F in, parallel out

Element symbol (Austrian Schulbuch): a vertical line on the axis with arrowheads at BOTH ends —
outward-pointing = Sammellinse (konvex), inward-pointing = Zerstreuungslinse (konkav); a
Hohlspiegel is a hatched vertical line. Roles: the object arrow is `primary`, the three rays are
distinguished by paired hue+dash from the ramp (photocopy-safe), the IMAGE arrow is `focus` (it IS
the sought result), and virtual (backward) ray extensions are dashed + `muted`.

Pure: imports only the scene primitives + numpy + sympy. The Asset generator
(`assets.matplotlib:optics_ray`) wraps this for the engine.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp

from .scene import Canvas, Label, Line, PointMark, Polyline, Scene

# ray families → paired hue+dash slots in the figstyle ramps (redundant encoding, B/W-safe)
PARALLEL, CENTER, FOCAL = 0, 2, 4          # spread across the ramp so the three read apart

# lens kinds that this recipe fully implements; mirrors are a documented follow-up
LENS_KINDS = ("sammellinse", "zerstreuungslinse")
MIRROR_KINDS = ("hohlspiegel", "ebener_spiegel")

_B = sp.Symbol("b")


@dataclass
class OpticsSpec:
    """A correct-by-construction optics setup. Distances are POSITIVE magnitudes; the lens type
    carries the focal-length sign internally (see the module docstring)."""
    kind: str = "sammellinse"      # sammellinse | zerstreuungslinse (mirrors: follow-up)
    f: float = 3.0                 # Brennweite (Betrag), > 0
    g: float = 6.0                 # Gegenstandsweite, > 0
    G: float = 2.0                 # Gegenstandsgröße (Pfeilhöhe), > 0


# --- the thin-lens core (the correct-by-construction layer) ------------------
def image_geometry(spec: OpticsSpec) -> dict:
    """Solve the Abbildungsgleichung exactly (sympy) and return every quantity the figure needs.

    Returns a dict with the SIGNED optical quantities (f_signed, b, B, V) plus the boolean
    classifications (real, upright, enlarged) and a `regime` label. `b` is None for the g = f
    degenerate case (parallel emerging rays — no finite image)."""
    kind = spec.kind.lower()
    if kind not in LENS_KINDS:
        raise ValueError(
            f"optics recipe implements {LENS_KINDS}; got {spec.kind!r} "
            f"(mirrors {MIRROR_KINDS} are a documented follow-up)")
    f_mag, g, G = float(spec.f), float(spec.g), float(spec.G)
    if f_mag <= 0 or g <= 0 or G <= 0:
        raise ValueError("f, g and G must be positive magnitudes")
    # the lens type carries the sign of the focal length
    f_signed = f_mag if kind == "sammellinse" else -f_mag

    # 1/f = 1/g + 1/b  →  b = 1 / (1/f − 1/g), solved symbolically (exact)
    degenerate = kind == "sammellinse" and abs(g - f_mag) < 1e-9
    if degenerate:
        return dict(kind=kind, f=f_signed, f_mag=f_mag, g=g, G=G, b=None, B=None, V=None,
                    real=False, upright=True, enlarged=True, regime="grenzfall",
                    F=(-f_mag, 0.0), Fp=(f_mag, 0.0))
    b_sol = sp.solve(sp.Eq(1 / f_signed, 1 / g + 1 / _B), _B)
    b = float(b_sol[0])
    B = -G * b / g                                   # signed image height (Abbildungsmaßstab)
    V = -b / g
    real = b > 0
    upright = B > 0
    enlarged = abs(B) > G + 1e-9
    if kind == "zerstreuungslinse":
        regime = "zerstreuungslinse"
    elif real:
        regime = "reell"                             # Sammellinse, g > f
    else:
        regime = "virtuell"                          # Sammellinse, g < f (Lupe)
    return dict(kind=kind, f=f_signed, f_mag=f_mag, g=g, G=G, b=b, B=B, V=V,
                real=real, upright=upright, enlarged=enlarged, regime=regime,
                F=(-f_mag, 0.0), Fp=(f_mag, 0.0))


# --- small geometry helpers --------------------------------------------------
def _pt(x, y) -> tuple[float, float]:
    return (float(x), float(y))


def _line_y(p, q, x: float) -> float:
    """y on the straight line p→q at abscissa x (p, q distinct in x)."""
    (x0, y0), (x1, y1) = p, q
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def _arrow_head(tip, direction, *, role="ink", size=0.30, width=1.4, z=6, family=None) -> list:
    """A small open arrowhead (two short segments) at `tip`, opening back along −`direction`.
    Composed from Line primitives — the scene engine has no arrow primitive by design."""
    d = np.asarray(direction, float)
    n = np.linalg.norm(d)
    if n == 0:
        return []
    d = d / n
    perp = np.array([-d[1], d[0]])
    tip = np.asarray(tip, float)
    back = tip - d * size
    wings = size * 0.55
    a = back + perp * wings
    b = back - perp * wings
    kw = dict(width=width, z=z)
    if family is not None:
        kw["family"] = family
    else:
        kw["role"] = role
    return [Line(_pt(*tip), _pt(*a), **kw), Line(_pt(*tip), _pt(*b), **kw)]


def _object_arrow(g: float, G: float) -> list:
    """The upright Gegenstand: a `primary` arrow from the axis up to (−g, G)."""
    base, tip = (-g, 0.0), (-g, G)
    return [Line(_pt(*base), _pt(*tip), role="primary", width=2.4, z=5),
            *_arrow_head(tip, (0, 1), role="primary", size=min(0.32, G * 0.22), width=2.2, z=5)]


def _image_arrow(b: float, B: float) -> list:
    """The image arrow at (b, B) — the `focus` result (dashed when the image is virtual)."""
    dash = "solid" if b > 0 else (0, (5, 3))
    base, tip = (b, 0.0), (b, B)
    layers = [Line(_pt(*base), _pt(*tip), role="focus", width=2.4, dash=dash, z=5)]
    head_dir = (0, 1) if B >= 0 else (0, -1)
    # a dashed arrow's head stays solid so the tip reads; keep it focus-coloured
    layers += _arrow_head(tip, head_dir, role="focus", size=min(0.34, abs(B) * 0.22 + 0.12),
                          width=2.2, z=5)
    return layers


def _lens_symbol(kind: str, half_height: float) -> list:
    """The Austrian Schulbuch lens symbol: a vertical line through the axis with arrowheads at
    BOTH ends — pointing OUTWARD for a Sammellinse (konvex), INWARD for a Zerstreuungslinse."""
    top, bot = (0.0, half_height), (0.0, -half_height)
    layers = [Line(_pt(*bot), _pt(*top), role="ink", width=2.0, z=4)]
    hs = min(0.34, half_height * 0.16)
    if kind == "sammellinse":                        # outward: ↑ at top, ↓ at bottom
        layers += _arrow_head(top, (0, 1), role="ink", size=hs, width=1.6, z=4)
        layers += _arrow_head(bot, (0, -1), role="ink", size=hs, width=1.6, z=4)
    else:                                            # inward: ↓ at top, ↑ at bottom
        layers += _arrow_head(top, (0, -1), role="ink", size=hs, width=1.6, z=4)
        layers += _arrow_head(bot, (0, 1), role="ink", size=hs, width=1.6, z=4)
    return layers


# --- the ray construction (stages 1–6, cumulative) ---------------------------
def _de(v: float) -> str:
    """German decimal-comma number (integers bare; 2 decimals stripped)."""
    v = round(float(v), 2)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _ray(p_from, p_to, *, family, solid_seg=True, back_ext=None) -> list:
    """A principal ray segment (paired hue+dash), optionally with a dashed backward extension
    (the virtual continuation) to `back_ext`."""
    layers = [Line(_pt(*p_from), _pt(*p_to), family=family, width=1.5, z=3)]
    if back_ext is not None:
        layers.append(Line(_pt(*p_to), _pt(*back_ext), role="muted", width=1.1,
                           dash=(0, (4, 3)), z=2))
    return layers


def ray_scene(spec: OpticsSpec, stage: int = 6, *, show_value: bool = True) -> Scene:
    """The Bildkonstruktion at `stage` (1–6), cumulative — the step-by-step ray diagram a
    worksheet builds up. Everything is COMPUTED from the spec via the thin-lens equation.

    stage 1  optische Achse + Linse + Gegenstandspfeil + Brennpunkte F/F′
          2  + Parallelstrahl  (parallel hinein → durch F′)
          3  + Mittelpunktstrahl (gerade durch die Linsenmitte)
          4  + Brennpunktstrahl (durch F hinein → parallel hinaus)
          5  + Bildpfeil im Schnittpunkt der Strahlen
          6  + Maße g, G, b, B — the gegeben→gesucht split: the GIVENS g and G always show
             their values (a task needs its Angaben); `show_value=False` masks only the
             SOUGHT image quantities ("b = ?", "B = ?", "B′ = ?")
    """
    geo = image_geometry(spec)
    g, G, f_mag = geo["g"], geo["G"], geo["f_mag"]
    b, B = geo["b"], geo["B"]
    P = (-g, G)                                       # the object tip (source of the rays)
    Fp = geo["Fp"]                                    # far focal point (image side)
    F = geo["F"]                                      # near focal point (object side)
    grenz = b is None                                 # the g = f degenerate case
    real = geo["real"]

    # --- frame the view asymmetrically (so a virtual image far to the left doesn't cramp the
    #     object on the right). Collect the x-extents that MUST be visible on each side.
    left_pts = [-g, -f_mag]                           # object, near focus (always left of lens)
    right_pts = [f_mag]                               # far focus (right of lens)
    if b is not None and b > 0:
        right_pts.append(b)                           # real image on the right
    if b is not None and b < 0:
        left_pts.append(b)                            # virtual image on the left
    x_left = min(left_pts)
    # rays should climax at the image, not overshoot to the corner: forward extent stops just
    # past the image (real) / a bit past F′ (virtual/grenzfall) so divergence still reads.
    if real:
        forward = max(b, f_mag) * 1.14
    else:
        forward = max(f_mag, g * 0.6) * 1.45
    x_right = max([*right_pts, forward])
    span = x_right - x_left
    padx = span * 0.10 + 0.6

    ys_pts = [G, -G] + ([B, -B] if B is not None else [])
    yr = max(abs(y) for y in ys_pts + [1.0])
    half_h = max(abs(G), abs(B) if B is not None else 0, 1.0) * 1.30 + 0.4
    pady = yr * 0.26 + 0.5
    sc = Scene(canvas=Canvas(figsize=(6.6, 4.4), frame="off",
                             xlim=(x_left - padx, x_right + padx),
                             ylim=(-half_h - pady * 0.2, half_h + pady * 0.2)))

    # optical axis (always), with a right-pointing arrow (light travels left→right)
    axr = x_right + padx * 0.7
    sc.add(Line(_pt(x_left - padx * 0.7, 0), _pt(axr, 0), role="muted", width=1.1, z=1))
    sc.add(*_arrow_head((axr, 0), (1, 0), role="muted", size=0.28, width=1.1, z=1))

    # the lens symbol + optical-centre mark (always)
    sc.add(*_lens_symbol(geo["kind"], half_h * 0.9))
    sc.add(PointMark(_pt(0, 0), role="ink", size=3.0, bold=False, z=6))

    # focal points F (object side) and F′ (image side), labelled below the axis
    for (fx, _), name in ((F, "F"), (Fp, "F′")):
        sc.add(PointMark(_pt(fx, 0), role="ink", size=3.5, bold=False, z=6))
        sc.add(Label(_pt(fx, -pady * 0.32), name, role="ink", size=9.5, va="top", bold=True))

    # the object arrow (always) + its label
    sc.add(*_object_arrow(g, G))
    sc.add(Label(_pt(-g - padx * 0.05, G + pady * 0.18), "G", role="primary", size=10,
                 ha="right", va="bottom", bold=True))

    # where each ray meets the lens plane (x = 0)
    y_parallel = G                                    # Parallelstrahl hits the lens at height G
    xend = x_right                                    # forward rays climax at the image, not the corner
    backx = x_left - padx * 0.3                       # where a virtual backward extension terminates

    # stage 2: Parallelstrahl — parallel in to (0, G), then out through F′
    if stage >= 2:
        sc.add(*_ray(P, (0, y_parallel), family=PARALLEL))     # incoming (horizontal)
        if grenz:                                              # g = f: emerges PARALLEL to axis
            sc.add(*_ray((0, y_parallel), (xend, y_parallel), family=PARALLEL))
        else:
            yq = _line_y((0, y_parallel), Fp, xend)            # out through F′
            sc.add(*_ray((0, y_parallel), (xend, yq), family=PARALLEL,
                         back_ext=(backx, _line_y((0, y_parallel), Fp, backx))
                         if not real else None))

    # stage 3: Mittelpunktstrahl — straight through the optical centre (0,0), undeviated
    if stage >= 3:
        yq = _line_y(P, (0, 0), xend)
        sc.add(*_ray(P, (xend, yq), family=CENTER,
                     back_ext=(backx, _line_y(P, (0, 0), backx))
                     if not real and not grenz else None))

    # stage 4: Brennpunktstrahl — through F in, then parallel to the axis out
    if stage >= 4 and not grenz:
        y_lens = _line_y(P, F, 0.0)                            # ray P → F, at the lens plane
        sc.add(*_ray(P, (0, y_lens), family=FOCAL))            # in, through F
        sc.add(*_ray((0, y_lens), (xend, y_lens), family=FOCAL,
                     back_ext=(backx, y_lens) if not real else None))
    elif stage >= 4 and grenz:
        # g = f: F coincides with the object foot; the third ray leaves parallel below the axis
        y_lens = _line_y(P, F, 0.0) if abs(P[0] - F[0]) > 1e-9 else G
        sc.add(*_ray(P, (0, y_lens), family=FOCAL))
        sc.add(*_ray((0, y_lens), (xend, y_lens), family=FOCAL))

    # stage 5: the image arrow at the rays' intersection (focus)
    if stage >= 5 and not grenz:
        sc.add(*_image_arrow(b, B))
        img_lbl = "B′" if show_value else "B′ = ?"
        sgn = 1.0 if (B or 0) >= 0 else -1.0
        sc.add(Label(_pt(b, B + pady * 0.20 * sgn), img_lbl, role="focus", size=10,
                     ha="center", va="bottom" if sgn > 0 else "top", bold=True))

    # stage 6: the measurement labels — the gegeben→gesucht split. The GIVENS g and G (the spec
    # inputs) ALWAYS show their values: a student task needs its Angaben. Only the SOUGHT image
    # quantities (b, B — and the B′ point label above) mask via show_value. g on the axis
    # baseline; b on a SECOND lower baseline so a virtual image (b < 0) never collides.
    if stage >= 6:
        base_g = -half_h - pady * 0.02
        base_b = base_g - pady * 0.42 if (b is not None and b < 0) else base_g
        sc.add(Line(_pt(-g, base_g), _pt(0, base_g), role="muted", width=0.9, z=1))
        sc.add(_tick(-g, base_g), _tick(0, base_g))
        sc.add(Label(_pt(-g / 2, base_g - pady * 0.13), f"g = {_de(g)}",
                     role="muted", size=9, va="top"))
        sc.add(Label(_pt(-g - padx * 0.06, G / 2), f"G = {_de(G)}",
                     role="primary", size=9, ha="right", va="center"))
        if not grenz:
            sc.add(Line(_pt(0, base_b), _pt(b, base_b), role="focus", width=0.9, z=1))
            sc.add(_tick(0, base_b, role="focus"), _tick(b, base_b, role="focus"))
            sc.add(Label(_pt(b / 2, base_b - pady * 0.13),
                         f"b = {_de(abs(b))}" if show_value else "b = ?",
                         role="focus", size=9, va="top"))
            sc.add(Label(_pt(b + padx * 0.06 * (1 if b >= 0 else -1), B / 2),
                         f"B = {_de(abs(B))}" if show_value else "B = ?",
                         role="focus", size=9, ha="left" if b >= 0 else "right", va="center"))

    return sc


def _tick(x: float, y: float, *, role: str = "muted", h: float = 0.12) -> Line:
    """A short vertical end-tick on a measurement baseline."""
    return Line(_pt(x, y - h), _pt(x, y + h), role=role, width=0.9, z=1)


# public API — mirrors constructions.construction_scene / calculus.*_scene
def lens_construction(kind: str = "sammellinse", f: float = 3.0, g: float = 6.0, G: float = 2.0,
                      stage: int = 6, *, show_value: bool = True) -> Scene:
    """Build the ray-construction Scene for a lens setup — the public entry point.

    kind ∈ {sammellinse, zerstreuungslinse}; f, g, G positive magnitudes; stage 1–6;
    show_value=False masks the SOUGHT image quantities ("b = ?", "B = ?", "B′ = ?") for the
    student task — the GIVENS g and G stay visible (gegeben→gesucht)."""
    return ray_scene(OpticsSpec(kind=kind, f=f, g=g, G=G), stage=stage, show_value=show_value)
