"""Electric-circuit schematics as computed scenes — the fourth scene-engine recipe family,
completing the MINT trio (geometry · analysis · optics · circuits).

A typed netlist (a nested series/parallel tree of resistors) → the COMPUTED electrical values
(Ersatzwiderstand, every branch current, every element voltage) → a schematic drawn from scene
primitives in the DIN/European school symbol set. The two-tier rule holds: the LLM never draws a
schematic (it could mis-wire a branch or leak an answer) — it declares the netlist + source, and
code both SOLVES it (sympy, exact rationals — the same linear-algebra machinery `balance_equation`
proved) and LAYS OUT the schematic. Every printed value is computed, never authored; labels are
maskable — GLOBALLY (`show_value=False` → everything "?", the teacher-solution twin) or
SELECTIVELY (`mask=["R₂", "Rers"]` → exactly those read "?" while the Angaben stay visible: the
canonical "gegeben U, R₁, R₃ und I — berechne R₂" task shape). The ASKED quantity carries the
`focus` role (`ask`, orthogonal to masking — typically the asked element is also in `mask`).

The physics, exactly (Kirchhoff on a series/parallel tree — no full mesh solve needed):
  series node  — one current through all children; the node voltage SPLITS across them
                 (Uᵢ = I·Rᵢ); ΣUᵢ = U_node  (Maschenregel)
  parallel node — one voltage across all children; the node current SPLITS among them
                 (Iᵢ = U/Rᵢ); ΣIᵢ = I_node  (Knotenregel)
Reduction: R_series = ΣRᵢ, 1/R_parallel = Σ1/Rᵢ. Distribution recurses from (U_total, I_total) at
the root down to each leaf; the consistency identities are asserted (see `solve_network`).

Symbols (Austrian/DIN Schulbuch): resistor = rectangle (Rechteck), battery/source = a long +
short parallel line pair, lamp = a circle with a diagonal cross (electrically a resistor), wires =
orthogonal Polylines on a computed grid. Layout is honest for arbitrary series/parallel TREES:
series → a horizontal chain, parallel → stacked branches joined by vertical bus wires, the whole
network closed into the classic rectangular loop by the source on the left.

Pure: imports only the scene primitives + numpy + sympy. The Asset generator
(`assets.matplotlib:circuit`) wraps this for the engine.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from .scene import Canvas, CircleShape, Label, Line, Polyline, Scene

_RESISTIVE = ("resistor", "lamp")            # a lamp is electrically a resistor


# --- the solver (exact, sympy Rationals) -------------------------------------
def _R(node: dict) -> sp.Rational:
    """The Ersatzwiderstand of a subtree, exact — R_series = ΣRᵢ, 1/R_parallel = Σ1/Rᵢ."""
    t = node.get("type")
    if t in _RESISTIVE:
        ohm = sp.Rational(str(node["ohm"]))
        if ohm <= 0:
            raise ValueError(f"resistor value must be positive, got {node['ohm']}")
        return ohm
    kids = node.get("children") or []
    if not kids:
        raise ValueError(f"{t!r} node has no children")
    parts = [_R(k) for k in kids]
    if t == "series":
        return sum(parts, sp.Integer(0))
    if t == "parallel":
        return 1 / sum((1 / p for p in parts), sp.Integer(0))
    raise ValueError(f"unknown node type {t!r} (expected series|parallel|resistor|lamp)")


def equivalent_resistance(net: dict) -> float:
    """The total Ersatzwiderstand of the netlist, as a float (exact internally)."""
    return float(_R(net))


def _distribute(node: dict, U: sp.Rational, I: sp.Rational, out: list) -> None:
    """Recurse (U across, I through) this subtree down to the leaves, recording each element's
    (U, I) in `out`. Asserts Kirchhoff at every node (exact rationals)."""
    t = node.get("type")
    if t in _RESISTIVE:
        out.append({"node": node, "U": U, "I": I, "R": _R(node)})
        return
    kids = node["children"]
    if t == "series":
        # same current through all; voltage splits ∝ R.  ΣUᵢ == U (Maschenregel)
        parts = [_R(k) for k in kids]
        Us = [I * r for r in parts]
        assert sum(Us, sp.Integer(0)) == U, "series voltage split violates ΣU = U_node"
        for k, u in zip(kids, Us):
            _distribute(k, u, I, out)
    elif t == "parallel":
        # same voltage across all; current splits ∝ 1/R.  ΣIᵢ == I (Knotenregel)
        Is = [U / _R(k) for k in kids]
        assert sum(Is, sp.Integer(0)) == I, "parallel current split violates ΣI = I_node"
        for k, i in zip(kids, Is):
            _distribute(k, U, i, out)
    else:
        raise ValueError(f"unknown node type {t!r}")


def solve_network(net: dict, volt: float) -> dict:
    """Solve the whole circuit at source voltage `volt`. Returns the Ersatzwiderstand, the total
    current, and per-element (U, I, R) — all exact (sympy), floats mirrored for display. Validates
    the netlist (≥1 resistor, positive values) and asserts Kirchhoff consistency in `_distribute`."""
    U0 = sp.Rational(str(volt))
    if U0 <= 0:
        raise ValueError(f"source voltage must be positive, got {volt}")
    Rtot = _R(net)                                   # raises on a malformed / empty net
    if not _has_resistor(net):
        raise ValueError("netlist has no resistor/lamp")
    Itot = U0 / Rtot
    elems: list = []
    _distribute(net, U0, Itot, elems)
    return dict(R_total=float(Rtot), I_total=float(Itot), U_source=float(U0),
                R_total_exact=Rtot, I_total_exact=Itot, elements=elems)


def _has_resistor(node: dict) -> bool:
    if node.get("type") in _RESISTIVE:
        return True
    return any(_has_resistor(k) for k in node.get("children") or [])


# --- layout (assign a grid box to every subtree) -----------------------------
# Grid units: one "cell" of horizontal length per element in a series chain; one "lane" of
# vertical height per branch in a parallel block. Real coordinates scale these.
_CELL = 3.0          # horizontal length allotted to one leaf element (incl. its wires)
_LANE = 2.2          # vertical spacing between parallel branches


def _extent(node: dict) -> tuple[float, float]:
    """(width, height) of a subtree in grid units. series: widths add, height = max child;
    parallel: heights add, width = max child. A leaf is 1×1."""
    t = node.get("type")
    if t in _RESISTIVE:
        return 1.0, 1.0
    kids = node["children"]
    ws, hs = zip(*(_extent(k) for k in kids))
    if t == "series":
        return sum(ws), max(hs)
    return max(ws), sum(hs)                            # parallel


def _mask_fn(show_value: bool, mask):
    """The masking rule for value labels, as a predicate `token → bool`.

    An explicit `mask` WINS when given: exactly the listed tokens mask (element labels like "R₂"
    and/or the totals "U" / "I" / "Rers") and every OTHER value shows — the gegeben→gesucht task
    shape, where the givens must stay visible. Without `mask`, `show_value=False` masks everything
    (back-compat, the original all-or-nothing switch) and True (default) shows everything.
    A bare string is tolerated as a one-element list (hand-written JSON robustness)."""
    if mask is not None:
        tokens = {str(t) for t in ([mask] if isinstance(mask, str) else mask)}
        return lambda token: token in tokens
    return lambda token: not show_value


def _leaf_symbol(node: dict, x0: float, x1: float, y: float, *, focus: bool,
                 is_masked) -> list:
    """Draw one element (resistor rectangle or lamp circle-cross) centred on the wire segment
    [x0,x1] at height y, with leader wires to the ends. Label above (name + value; reads
    "name = ?" when `is_masked(name)`)."""
    role = "focus" if focus else "ink"
    mid = (x0 + x1) / 2
    body = min(1.15, (x1 - x0) * 0.5)                 # symbol body length
    bx0, bx1 = mid - body / 2, mid + body / 2
    layers = [Line((x0, y), (bx0, y), role="ink", width=1.3, z=3),      # lead-in wire
              Line((bx1, y), (x1, y), role="ink", width=1.3, z=3)]      # lead-out wire
    if node.get("type") == "lamp":
        r = 0.42
        layers.append(CircleShape((mid, y), r, role=role, width=1.6, z=4))
        d = r / np.sqrt(2)                              # the diagonal cross (Lampensymbol)
        layers += [Line((mid - d, y - d), (mid + d, y + d), role=role, width=1.4, z=5),
                   Line((mid - d, y + d), (mid + d, y - d), role=role, width=1.4, z=5)]
        # connect the circle to the leads
        layers += [Line((bx0, y), (mid - r, y), role="ink", width=1.3, z=3),
                   Line((mid + r, y), (bx1, y), role="ink", width=1.3, z=3)]
    else:                                              # resistor rectangle
        h = 0.5
        rect = [(bx0, y - h / 2), (bx1, y - h / 2), (bx1, y + h / 2), (bx0, y + h / 2)]
        layers.append(Polyline(rect, role=role, width=1.7, closed=True, z=4))
    # label: name + value above the symbol
    name = str(node.get("label") or ("L" if node.get("type") == "lamp" else "R"))
    ohm = node["ohm"]
    val = _de(float(ohm)) + " Ω"
    txt = f"{name} = ?" if is_masked(name) else f"{name} = {val}"
    layers.append(Label((mid, y + 0.62), txt, role=role, size=9,
                        va="bottom", bold=focus))
    return layers


def _layout(node: dict, x0: float, x1: float, yc: float, *, focus_id, is_masked,
            leftx: float, rightx: float) -> list:
    """Recursively draw a subtree spanning horizontally [x0,x1] centred vertically at yc.
    `leftx`/`rightx` are the entry/exit x of the enclosing wire (for parallel bus joins)."""
    t = node.get("type")
    if t in _RESISTIVE:
        return _leaf_symbol(node, x0, x1, yc, focus=(id(node) == focus_id),
                            is_masked=is_masked)
    kids = node["children"]
    layers: list = []
    if t == "series":
        # split [x0,x1] into child cells proportional to each child's grid width
        ws = [_extent(k)[0] for k in kids]
        total = sum(ws)
        cx = x0
        for k, w in zip(kids, ws):
            seg = (x1 - x0) * (w / total)
            layers += _layout(k, cx, cx + seg, yc, focus_id=focus_id, is_masked=is_masked,
                              leftx=cx, rightx=cx + seg)
            cx += seg
        return layers
    # parallel: stack branches vertically, each spanning the full [x0,x1]; join with bus wires
    hs = [_extent(k)[1] for k in kids]
    total_h = sum(hs) * _LANE
    top = yc + total_h / 2
    ys = []
    cursor = top
    for h in hs:
        band = h * _LANE
        ys.append(cursor - band / 2)                  # branch centre
        cursor -= band
    for k, by in zip(kids, ys):
        layers += _layout(k, x0, x1, by, focus_id=focus_id, is_masked=is_masked,
                          leftx=x0, rightx=x1)
    # the two vertical bus wires joining all branch ends, plus stubs into the enclosing wire
    ytop, ybot = ys[0], ys[-1]
    layers += [Line((x0, ybot), (x0, ytop), role="ink", width=1.3, z=3),
               Line((x1, ybot), (x1, ytop), role="ink", width=1.3, z=3)]
    # connect the enclosing entry/exit (at yc) into the bus
    layers += [Line((leftx, yc), (x0, yc), role="ink", width=1.3, z=3),
               Line((x1, yc), (rightx, yc), role="ink", width=1.3, z=3)]
    return layers


def _de(v: float) -> str:
    """German decimal-comma number (integers bare; up to 2 decimals, trailing zeros stripped)."""
    v = round(float(v), 2)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")


# --- the schematic scene -----------------------------------------------------
def circuit_scene(net: dict, volt: float = 12.0, *, show_value: bool = True,
                  mask: list[str] | str | None = None, ask: str | None = None,
                  title: str | None = None) -> Scene:
    """The circuit schematic: the source on the left closes a rectangular loop whose top edge
    carries the resistor network. All values are COMPUTED (`solve_network`) and maskable.

    Masking (see `_mask_fn`): `mask` lists exactly the tokens to hide — element labels ("R₂")
    and/or "U" / "I" / "Rers" — while every other value (the Angaben) stays visible; when `mask`
    is absent, `show_value=False` masks ALL values (back-compat). `ask` names the focus element
    (its `label`, e.g. "R₂", or "U"/"I") — drawn in the `focus` role, orthogonal to masking;
    for a student task the asked quantity is typically also masked. `volt` is the
    Quellenspannung. Raises on a malformed/degenerate netlist."""
    sol = solve_network(net, volt)                    # validates + asserts Kirchhoff
    focus_id = _find_by_label(net, ask) if ask else None
    is_masked = _mask_fn(show_value, mask)

    w_units, h_units = _extent(net)
    net_w = max(w_units * _CELL, _CELL)               # real width of the network span
    net_h = max((h_units - 1) * _LANE, 0.0)           # extra vertical spread of parallels

    # loop geometry: network along the top edge; left/right verticals down to the source
    x_left, x_right = 0.0, net_w
    y_top = 0.0                                        # the network sits at y = 0 (its centre band)
    y_bot = -(net_h / 2 + 2.2)                        # bottom rail below the widest parallel block

    sc = Scene(canvas=Canvas(figsize=(7.0, 4.8), frame="off"))

    # the network on the top edge
    sc.add(*_layout(net, x_left, x_right, y_top, focus_id=focus_id, is_masked=is_masked,
                    leftx=x_left, rightx=x_right))

    # the rectangular loop: down the right side, along the bottom (through the source), up the left
    sc.add(Line((x_right, y_top), (x_right, y_bot), role="ink", width=1.3, z=3),
           Line((x_left, y_top), (x_left, y_bot), role="ink", width=1.3, z=3),
           Line((x_left, y_bot), (x_right, y_bot), role="ink", width=1.3, z=3))

    # the source (battery symbol) on the bottom wire: long line = +, short line = −
    sx = (x_left + x_right) / 2
    src_focus = ask is not None and (ask or "").upper() in ("U", "I")
    _battery(sc, sx, y_bot, focus=src_focus)
    utxt = "U = ?" if is_masked("U") else f"U = {_de(sol['U_source'])} V"
    itxt = "I = ?" if is_masked("I") else f"I = {_de(sol['I_total'])} A"
    src_role = "focus" if src_focus else "ink"
    sc.add(Label((sx, y_bot - 0.55), utxt, role=src_role, size=9.5, va="top", bold=src_focus))
    # the loop current I: a direction arrow on the (always-clean) right vertical wire, pointing
    # DOWN (technical direction + → −: current leaves the network, flows down to the − terminal),
    # with the value beside it. Focus when I is the asked quantity.
    icol = "focus" if (ask or "").upper() == "I" else "muted"
    ymid = (y_top + y_bot) / 2
    sc.add(*_arrow((x_right, ymid + 0.45), (x_right, ymid - 0.45), role=icol))
    sc.add(Label((x_right + 0.18, ymid), itxt, role=icol, size=9,
                 ha="left", va="center", bold=(icol == "focus")))

    # Ersatzwiderstand annotation (mask token "Rers") — centred under the source so it never
    # collides with the right-wire current label.
    rtxt = ("Ersatzwiderstand  Rₑᵣₛ = ?" if is_masked("Rers")
            else f"Ersatzwiderstand  Rₑᵣₛ = {_de(sol['R_total'])} Ω")
    sc.add(Label((sx, y_bot - 1.15), rtxt, role="muted", size=8.5, ha="center", va="top"))

    if title:
        sc.canvas.title = str(title)

    # frame with padding around everything
    pad = 1.4
    sc.canvas.xlim = (x_left - pad - 0.8, x_right + pad + 1.4)
    sc.canvas.ylim = (y_bot - pad - 0.6, y_top + max(net_h / 2, 0.0) + pad)
    return sc


def _battery(sc: Scene, x: float, y: float, *, focus: bool) -> None:
    """A battery symbol straddling the bottom wire at x: a long line (+) and a short line (−)."""
    role = "focus" if focus else "ink"
    gap = 0.34
    # break the wire around the symbol
    sc.add(Line((x - 0.55, y), (x - gap / 2, y), role="ink", width=1.3, z=3),
           Line((x + gap / 2, y), (x + 0.55, y), role="ink", width=1.3, z=3))
    sc.add(Line((x - gap / 2, y - 0.55), (x - gap / 2, y + 0.55), role=role, width=1.8, z=5),  # +
           Line((x + gap / 2, y - 0.30), (x + gap / 2, y + 0.30), role=role, width=3.0, z=5))  # −
    sc.add(Label((x - gap / 2 - 0.16, y + 0.6), "+", role=role, size=10, ha="center", va="bottom"),
           Label((x + gap / 2 + 0.16, y + 0.6), "–", role=role, size=11, ha="center", va="bottom"))


def _arrow(p, q, *, role="muted") -> list:
    """A tiny direction arrow p→q (segment + head), for the current-direction indicator."""
    p = np.asarray(p, float)
    q = np.asarray(q, float)
    d = q - p
    n = np.linalg.norm(d)
    if n == 0:
        return []
    d = d / n
    perp = np.array([-d[1], d[0]])
    head = q - d * 0.22
    wings = 0.13
    return [Line(tuple(p), tuple(q), role=role, width=1.2, z=6),
            Line(tuple(q), tuple(head + perp * wings), role=role, width=1.2, z=6),
            Line(tuple(q), tuple(head - perp * wings), role=role, width=1.2, z=6)]


def _find_by_label(node: dict, label: str):
    """The id() of the first leaf whose `label` matches (for the focus role)."""
    if node.get("type") in _RESISTIVE and str(node.get("label")) == str(label):
        return id(node)
    for k in node.get("children") or []:
        found = _find_by_label(k, label)
        if found is not None:
            return found
    return None


# public API — mirrors constructions.construction_scene / calculus.*_scene / optics.lens_construction
def circuit_construction(net: dict, volt: float = 12.0, *, show_value: bool = True,
                         mask: list[str] | str | None = None, ask: str | None = None,
                         title: str | None = None) -> Scene:
    """Build the schematic Scene for a netlist — the public entry point. `net` is the nested
    series/parallel resistor tree, `volt` the source voltage. Masking: `mask=["R₂","Rers"]` hides
    exactly those values (Angaben stay visible — the gegeben→gesucht task); without `mask`,
    `show_value=False` masks everything (back-compat). `ask` names the focus element
    ("R₂"/"U"/"I"), orthogonal to masking."""
    return circuit_scene(net, volt, show_value=show_value, mask=mask, ask=ask, title=title)
