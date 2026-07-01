"""Analysis scenes — the second scene-engine recipe family (after geometry), so the substrate
is proven across domains. The figures the brief asked for first: a function plot, the **area
under a curve** (the definite integral), and a **tangent** (the derivative as slope).

Correct-by-construction via sympy: the LLM declares the function as an EXPRESSION string
(`"0.25*x**2 + 1"`, `"sin(x)"`) — a parameter, not a drawing — and code samples it, differentiates
it (`tangent_slope`), and integrates it (`definite_integral`). The curve, the slope, and the area
are computed; the figure can never show a wrong tangent or a faked area. Value labels are
maskable (`show_value=False` → "A = ?"), so the same scene serves the student task and the
teacher solution.

Builds `scene.Scene` objects (the shared substrate); the Asset generators in `assets.py` wrap
these. Imports only the scene primitives + numpy + sympy.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from . import figstyle as fs
from .scene import Canvas, Label, Line, PointMark, Polyline, Region, Scene

_X = sp.Symbol("x")


# --- sympy core (the correct-by-construction layer) --------------------------
def _parse(expr_str: str) -> sp.Expr:
    """Parse a function expression in x (implicit multiplication allowed: '2x' == '2*x')."""
    from sympy.parsing.sympy_parser import (implicit_multiplication_application,
                                            parse_expr, standard_transformations)
    tr = standard_transformations + (implicit_multiplication_application,)
    return parse_expr(str(expr_str), local_dict={"x": _X}, transformations=tr, evaluate=True)


def tangent_slope(expr_str: str, x0: float) -> float:
    """f'(x0), computed symbolically — the derivative as the tangent's slope."""
    expr = _parse(expr_str)
    return float(sp.diff(expr, _X).subs(_X, x0))


def definite_integral(expr_str: str, a: float, b: float) -> float:
    """∫_a^b f(x) dx — symbolic when sympy can, else a numerical fallback (np.trapz)."""
    expr = _parse(expr_str)
    try:
        val = float(sp.integrate(expr, (_X, a, b)).evalf())
        if np.isfinite(val):
            return val
    except (TypeError, ValueError, sp.SympifyError):
        pass
    f = sp.lambdify(_X, expr, "numpy")
    xs = np.linspace(float(a), float(b), 400)
    return float(np.trapezoid(np.asarray(f(xs), dtype=float), xs))


def _samples(expr: sp.Expr, xmin: float, xmax: float, n: int = 241):
    f = sp.lambdify(_X, expr, "numpy")
    xs = np.linspace(xmin, xmax, n)
    with np.errstate(all="ignore"):
        ys = np.asarray(f(xs) * np.ones_like(xs), dtype=float)
    ys[~np.isfinite(ys)] = np.nan          # asymptotes/domain gaps → break the line
    return xs, ys


def _de(v: float) -> str:
    """German decimal-comma number; integers without a trailing ',0'."""
    v = round(float(v), 2)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _finite(arr) -> tuple[float, float]:
    a = arr[np.isfinite(arr)]
    return (float(a.min()), float(a.max())) if a.size else (0.0, 1.0)


# --- shared scene scaffolding ------------------------------------------------
def _base(expr, xmin, xmax, *, ymin=None, ymax=None, include_zero=False, extra_y=()):
    """Sample the curve, decide the y-window + frame, and return (Scene, expr, f, xs, ys)."""
    xs, ys = _samples(expr, xmin, xmax)
    ylo, yhi = _finite(ys)
    for v in extra_y:                       # keep tangent endpoints / the point in view
        ylo, yhi = min(ylo, v), max(yhi, v)
    if include_zero:
        ylo, yhi = min(ylo, 0.0), max(yhi, 0.0)
    pad = (yhi - ylo) * 0.12 or 1.0
    ylo = ymin if ymin is not None else ylo - pad
    yhi = ymax if ymax is not None else yhi + pad
    frame = "center" if (xmin <= 0 <= xmax and ylo <= 0 <= yhi) else "lb"
    sc = Scene(canvas=Canvas(figsize=(5.4, 4.4), frame=frame, grid=True,
                             xlim=(xmin, xmax), ylim=(ylo, yhi)))
    if frame == "lb" and ylo <= 0 <= yhi:   # ensure a visible x-axis baseline for the area
        sc.add(Line((xmin, 0), (xmax, 0), role="muted", width=0.9, z=1))
    return sc, xs, ys, (ylo, yhi)


def _curve(xs, ys, *, label=None) -> list:
    layers = [Polyline(list(zip(xs.tolist(), ys.tolist())), role="ink", width=2.2, z=4)]
    if label:                               # name the curve near its right end
        i = np.where(np.isfinite(ys))[0]
        if i.size:
            layers.append(Label((float(xs[i[-1]]), float(ys[i[-1]])), label, role="ink",
                                size=10, ha="left", va="bottom", halo=True))
    return layers


# --- the three recipes -------------------------------------------------------
def function_scene(expr_str: str, xmin: float = -5, xmax: float = 5, **opts) -> Scene:
    """Just f(x) over [xmin, xmax] — the base analysis figure (an arbitrary function, which the
    old `function_graph` line/point recipe cannot draw)."""
    expr = _parse(expr_str)
    sc, xs, ys, _ = _base(expr, xmin, xmax, ymin=opts.get("ymin"), ymax=opts.get("ymax"))
    sc.add(*_curve(xs, ys, label=opts.get("label", "f")))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc


def integral_scene(expr_str: str, a: float, b: float, xmin=None, xmax=None, *,
                   show_value: bool = True, **opts) -> Scene:
    """f(x) with the area under it on [a, b] shaded — the definite integral, value computed."""
    expr = _parse(expr_str)
    a, b = float(a), float(b)
    if xmin is None:
        xmin = a - 0.25 * (b - a) - 0.5
    if xmax is None:
        xmax = b + 0.25 * (b - a) + 0.5
    sc, xs, ys, (ylo, yhi) = _base(expr, xmin, xmax, ymin=opts.get("ymin"),
                                   ymax=opts.get("ymax"), include_zero=True)
    f = sp.lambdify(_X, expr, "numpy")
    xr = np.linspace(a, b, 90)
    yr = np.asarray(f(xr) * np.ones_like(xr), dtype=float)
    region = [(a, 0.0), *zip(xr.tolist(), yr.tolist()), (b, 0.0)]
    sc.add(Region(region, role="focus", alpha=0.20, z=1))
    sc.add(Line((a, 0), (a, float(yr[0])), role="focus", width=0.9, z=2),
           Line((b, 0), (b, float(yr[-1])), role="focus", width=0.9, z=2))
    sc.add(*_curve(xs, ys, label=opts.get("label", "f")))
    tick = ylo - (yhi - ylo) * 0.03
    sc.add(Label((a, tick), "a", role="muted", size=8.5, va="top"),
           Label((b, tick), "b", role="muted", size=8.5, va="top"))
    area = definite_integral(expr_str, a, b)
    txt = f"A = {_de(area)}" if show_value else "A = ?"
    sc.add(Label(((a + b) / 2, max(0.0, ylo) + (yhi - ylo) * 0.10), txt, role="focus",
                 size=fs.TYPE.annot, bold=True))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc


def tangent_scene(expr_str: str, x0: float, xmin=None, xmax=None, *,
                  show_slope: bool = True, slope_triangle: bool = True, **opts) -> Scene:
    """f(x) with the tangent at x0 — the derivative as slope, k = f'(x0) computed."""
    expr = _parse(expr_str)
    x0 = float(x0)
    span = 3.0 if xmin is None or xmax is None else (xmax - xmin) / 2
    if xmin is None:
        xmin = x0 - span
    if xmax is None:
        xmax = x0 + span
    f = sp.lambdify(_X, expr, "numpy")
    y0 = float(f(x0))
    k = tangent_slope(expr_str, x0)
    t = (xmax - xmin) * 0.30                 # tangent half-length
    tx0, tx1 = x0 - t, x0 + t
    sc, xs, ys, (ylo, yhi) = _base(expr, xmin, xmax, ymin=opts.get("ymin"),
                                   ymax=opts.get("ymax"),
                                   extra_y=(y0 + k * t, y0 - k * t, y0))
    sc.add(*_curve(xs, ys, label=opts.get("label", "f")))
    sc.add(Line((tx0, y0 + k * (tx0 - x0)), (tx1, y0 + k * (tx1 - x0)),
                role="focus", width=1.7, z=4))
    if slope_triangle:                        # Steigungsdreieck: run 1, rise k
        run = min(1.0, (xmax - xmin) * 0.18)
        sc.add(Line((x0, y0), (x0 + run, y0), role="muted", width=1.0, z=3),
               Line((x0 + run, y0), (x0 + run, y0 + k * run), role="muted", width=1.0, z=3))
        sc.add(Label((x0 + run / 2, y0 - (yhi - ylo) * 0.03), _de(run), role="muted",
                     size=8, va="top"),
               Label((x0 + run * 1.06, y0 + k * run / 2), _de(k * run), role="muted",
                     size=8, ha="left"))
    sc.add(PointMark((x0, y0), label="P", role="focus", size=6.5,
                     label_offset=(-0.05, (yhi - ylo) * 0.05), bold=True, z=6))
    sc.add(Label((tx1, y0 + k * (tx1 - x0)), f"k = {_de(k)}" if show_slope else "k = ?",
                 role="focus", size=fs.TYPE.annot, ha="left", va="center", bold=True))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc


def riemann_sum(expr_str: str, a: float, b: float, n: int, mode: str = "left") -> float:
    """Σ f(xᵢ)·h — the Riemann sum with n rectangles (left · right · mid sample point)."""
    f = sp.lambdify(_X, _parse(expr_str), "numpy")
    a, b, n = float(a), float(b), int(n)
    h = (b - a) / n
    off = {"left": 0.0, "right": 1.0, "mid": 0.5}.get(mode, 0.0)
    return float(sum(float(f(a + (i + off) * h)) for i in range(n)) * h)


def riemann_scene(expr_str: str, a: float, b: float, n: int = 6, mode: str = "left",
                  xmin=None, xmax=None, **opts) -> Scene:
    """The definite integral approximated by n rectangles — motivates ∫ (Ober-/Untersumme). The
    sum AND the exact value are computed, so the approximation error is visible."""
    expr = _parse(expr_str)
    a, b, n = float(a), float(b), int(n)
    if xmin is None:
        xmin = a - 0.3 * (b - a) - 0.4
    if xmax is None:
        xmax = b + 0.3 * (b - a) + 0.4
    sc, xs, ys, (ylo, yhi) = _base(expr, xmin, xmax, include_zero=True, ymin=opts.get("ymin"),
                                   ymax=opts.get("ymax"))
    f = sp.lambdify(_X, expr, "numpy")
    h = (b - a) / n
    off = {"left": 0.0, "right": 1.0, "mid": 0.5}.get(mode, 0.0)
    for i in range(n):
        xi = a + i * h
        hi = float(f(xi + off * h))
        sc.add(Region([(xi, 0), (xi, hi), (xi + h, hi), (xi + h, 0)], role="focus", alpha=0.22,
                      edge_role="ink", edge_width=0.7, z=1))
    sc.add(*_curve(xs, ys, label=opts.get("label", "f")))
    ssum = riemann_sum(expr_str, a, b, n, mode)
    exact = definite_integral(expr_str, a, b)
    sc.add(Label(((a + b) / 2, yhi - (yhi - ylo) * 0.07), f"S ≈ {_de(ssum)}  (n = {n})",
                 role="focus", size=fs.TYPE.annot, bold=True),
           Label(((a + b) / 2, yhi - (yhi - ylo) * 0.15), f"exakt: A = {_de(exact)}",
                 role="muted", size=fs.TYPE.tick))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc


def _critical_points(expr: sp.Expr, xmin: float, xmax: float) -> list[float]:
    """Real solutions of f'(x)=0 in [xmin, xmax] — symbolic, with a sign-change fallback."""
    fp = sp.diff(expr, _X)
    pts: set[float] = set()
    try:
        for s in sp.solve(fp, _X):
            if s.is_real and xmin <= float(s) <= xmax:
                pts.add(round(float(s), 6))
    except (TypeError, ValueError, NotImplementedError):
        pass
    if not pts:                                # numerical: sign changes of f'
        f = sp.lambdify(_X, fp, "numpy")
        gx = np.linspace(xmin, xmax, 400)
        with np.errstate(all="ignore"):
            gv = np.asarray(f(gx) * np.ones_like(gx), dtype=float)
        for i in range(len(gx) - 1):
            if np.isfinite(gv[i]) and np.isfinite(gv[i + 1]) and gv[i] * gv[i + 1] < 0:
                pts.add(round(float((gx[i] + gx[i + 1]) / 2), 4))
    return sorted(pts)


def extrema_scene(expr_str: str, xmin: float = -5, xmax: float = 5, **opts) -> Scene:
    """f(x) with its local extrema marked (Hochpunkt H / Tiefpunkt T), each with a horizontal
    tangent — computed from f'(x)=0 and classified by f''(x)."""
    expr = _parse(expr_str)
    sc, xs, ys, (ylo, yhi) = _base(expr, xmin, xmax, ymin=opts.get("ymin"), ymax=opts.get("ymax"))
    sc.add(*_curve(xs, ys, label=opts.get("label", "f")))
    f = sp.lambdify(_X, expr, "numpy")
    fpp = sp.diff(expr, _X, 2)
    t = (xmax - xmin) * 0.09
    for xc in _critical_points(expr, xmin, xmax):
        yc = float(f(xc))
        second = float(fpp.subs(_X, xc))
        kind = "T" if second > 0 else ("H" if second < 0 else "W")
        sc.add(Line((xc - t, yc), (xc + t, yc), role="focus", width=1.4, z=4))
        dy = (yhi - ylo) * 0.06 * (-1 if second > 0 else 1)
        sc.add(PointMark((xc, yc), label=kind, role="focus", size=6,
                         label_offset=(0.0, dy), bold=True, z=6))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc


def area_between_scene(expr_str: str, expr2_str: str, a=None, b=None, xmin=None, xmax=None,
                       *, show_value: bool = True, **opts) -> Scene:
    """The area between two curves f and g over [a, b] (default: between their outer
    intersections) — A = ∫|f−g| dx, computed."""
    fe, ge = _parse(expr_str), _parse(expr2_str)
    if a is None or b is None:
        try:
            roots = sorted(float(s) for s in sp.solve(fe - ge, _X) if s.is_real)
        except (TypeError, ValueError, NotImplementedError):
            roots = []
        a = roots[0] if (a is None and roots) else (0.0 if a is None else a)
        b = roots[-1] if (b is None and roots) else (3.0 if b is None else b)
    a, b = float(a), float(b)
    if xmin is None:
        xmin = a - 0.3 * (b - a) - 0.4
    if xmax is None:
        xmax = b + 0.3 * (b - a) + 0.4
    f = sp.lambdify(_X, fe, "numpy")
    g = sp.lambdify(_X, ge, "numpy")
    xs = np.linspace(xmin, xmax, 241)
    fy = np.asarray(f(xs) * np.ones_like(xs), dtype=float)
    gy = np.asarray(g(xs) * np.ones_like(xs), dtype=float)
    ylo, yhi = _finite(np.concatenate([fy, gy]))
    pad = (yhi - ylo) * 0.12 or 1.0
    ylo, yhi = min(ylo, 0.0) - pad, yhi + pad
    frame = "center" if (xmin <= 0 <= xmax and ylo <= 0 <= yhi) else "lb"
    sc = Scene(canvas=Canvas(figsize=(5.4, 4.4), frame=frame, grid=True,
                             xlim=(xmin, xmax), ylim=(ylo, yhi)))
    xr = np.linspace(a, b, 90)
    poly = [*zip(xr.tolist(), (f(xr) * np.ones_like(xr)).tolist()),
            *zip(xr[::-1].tolist(), (g(xr[::-1]) * np.ones_like(xr)).tolist())]
    sc.add(Region(poly, role="focus", alpha=0.20, z=1))
    sc.add(Polyline(list(zip(xs.tolist(), fy.tolist())), role="ink", width=2.2, z=4),
           Polyline(list(zip(xs.tolist(), gy.tolist())), role="primary", width=2.0, z=4))
    gr = np.linspace(a, b, 400)
    area = float(np.trapezoid(np.abs((f(gr) * np.ones_like(gr)) - (g(gr) * np.ones_like(gr))), gr))
    txt = f"A = {_de(area)}" if show_value else "A = ?"
    sc.add(Label(((a + b) / 2, (ylo + yhi) / 2), txt, role="focus", size=fs.TYPE.annot, bold=True))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc


def distribution_scene(mu: float = 0, sigma: float = 1, *, a=None, b=None, mode: str = "between",
                       show_value: bool = True, **opts) -> Scene:
    """A normal density N(μ,σ) with a probability region shaded (P(X≤a) · P(X≥a) · P(a≤X≤b)) —
    area = probability, computed. The stochastics face of 'area under a curve' (WS strand)."""
    mu, sigma = float(mu), float(sigma)
    dens = f"exp(-((x-{mu})**2)/(2*({sigma})**2))/(({sigma})*sqrt(2*pi))"
    expr = _parse(dens)
    xmin, xmax = mu - 4 * sigma, mu + 4 * sigma
    sc, xs, ys, (ylo, yhi) = _base(expr, xmin, xmax, include_zero=True, ymin=0)
    f = sp.lambdify(_X, expr, "numpy")
    if mode == "le":
        lo, hi, P, ptxt = xmin, float(a), definite_integral(dens, mu - 8 * sigma, a), f"P(X ≤ {_de(a)})"
    elif mode == "ge":
        lo, hi, P, ptxt = float(a), xmax, definite_integral(dens, a, mu + 8 * sigma), f"P(X ≥ {_de(a)})"
    else:
        lo, hi = float(a), float(b)
        P, ptxt = definite_integral(dens, a, b), f"P({_de(a)} ≤ X ≤ {_de(b)})"
    xr = np.linspace(lo, hi, 120)
    yr = np.asarray(f(xr) * np.ones_like(xr), dtype=float)
    sc.add(Region([(lo, 0.0), *zip(xr.tolist(), yr.tolist()), (hi, 0.0)], role="focus",
                  alpha=0.25, z=1))
    sc.add(*_curve(xs, ys, label=None))
    txt = f"{ptxt} = {_de(P)}" if show_value else f"{ptxt} = ?"
    sc.add(Label((mu, yhi * 0.45), txt, role="focus", size=fs.TYPE.annot, bold=True))
    if opts.get("title"):
        sc.canvas.title = str(opts["title"])
    return sc
