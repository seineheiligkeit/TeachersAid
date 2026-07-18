"""Zeitband — the computed Schulbuch-Zeitleiste family (design: `Documents/zeitleiste-design.md`).

The successor to the flat `matplotlib:timeline` recipe: a *didactic recipe COMPUTES a `Scene`* from
a small correct-by-construction spec, the established two-tier pattern (`constructions.py`,
`optics.py`) — the LLM never authors the layout. Four forms in one visual language (mockups in
`tools/zeitleiste_mockup.py`):

  M1 Zeitband        short Stichwort labels alternating above/below · decade/century ticks +
                     Zeitpfeil arrowhead · phase band (Periodisierung) · Zäsur rule · focus event
  M2 Synchronoptik   two curated semantic lanes (`strands`): `[0]` above, `[1]` below, captioned —
                     the above/below GEOMETRY carries the split (B/W-safe), not hue alone
  M3 Lupe            a full-span main band + a shaded detail window expanded into a second,
                     internally-linear zoom band (explicit connectors), auto-triggered on clustering
  M4 Arbeitsobjekt   the student work-object projection: year chips on the axis + an Ereignis-
                     Kärtchen bank with blank lines ("trage das passende Jahr ein")

**Measured, never guessed** (the discipline of the mockup and the shipped `_timeline` fix): label
widths are measured against the FINAL horizontal frame (`figtext.measure_widths`), lanes packed
(`figtext.lane_pack`), and the figure is laid out **inch-true** — the axes fill the whole figure
(`add_axes([0,0,1,1])`) and `ylim` spans exactly the figure height in inches, so one data-y unit ==
one inch and a lane is exactly as tall as its measured text. (We render inch-true rather than through
the constrained-layout `scene_to_png`, for the same reason `_timeline` avoids it: constrained layout
would perturb the axes box and break the measured vertical layout.)

The resolved ► decisions (SME, 18 Jul 2026): ►1 axis labels are Stichwörter ≤ 32 chars, an over-long
one auto-demotes to a numbered chip + a legend line (no ingest rejection); ►3 the Lupe auto-triggers
deterministically on clustering; ►4 the Arbeitsobjekt is a projection capability, default off, sharing
ONE computed layout with the solved band; ►6 strands are free curated 2-name pairs.

Pure: imports only the scene primitives + figstyle + figtext + stdlib. `matplotlib:zeitband` in
`assets.py` wraps `zeitband_scene`.
"""
from __future__ import annotations

import math
import textwrap
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import figstyle as fs  # noqa: E402
from .figtext import lane_pack, measure_widths  # noqa: E402
from .scene import (Arrow, Canvas, Label, Line, Node, PointMark,  # noqa: E402
                    Polyline, Region, Scene, render_scene)

LABEL_BOUND = 32          # ►1: axis-label Stichwort bound; a longer label auto-demotes to a chip
W_IN = 9.0                # figure width in inches (matches the 8.8–9.0 mockups)
_NAME_WRAP = 16           # wrap a Stichwort to keep the label block narrow


# --------------------------------------------------------------------------- events
@dataclass
class _Ev:
    at: object
    label: str
    to: object = None
    zaesur: bool = False
    strand: str | None = None
    focus: bool = False
    # derived
    at_num: float | None = None
    to_num: float | None = None
    year_str: str = ""
    name_wrapped: str = ""
    demoted: bool = False
    chip_no: int | None = None
    x: float = 0.0            # scene x of the mark (span → midpoint)


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _sort_key(e: _Ev):
    return (0, e.at_num, "") if e.at_num is not None else (1, 0.0, str(e.at))


def _year_str(at, to) -> str:
    """The printed year: a point "1494", a Zeitraum "1904–08" / "1884–85" (short end within the
    same century) / "1898–1902". Years print as plain integers — NEVER `fmt_de` (which would insert
    a thousands dot, "1.494")."""
    a = f"{int(at)}" if isinstance(at, (int, float)) else str(at)
    if to is None or to == "":
        return a
    if isinstance(at, (int, float)) and isinstance(to, (int, float)):
        ai, ti = int(at), int(to)
        if ti > ai and ti // 100 == ai // 100:
            return f"{ai}–{ti % 100:02d}"
        return f"{ai}–{ti}"
    return f"{a}–{to}"


def _parse_events(spec: dict) -> list[_Ev]:
    """Normalise the spec into a sorted `_Ev` list + resolve demotion numbering — the ONE computed
    layout shared by the solved band and the Arbeitsobjekt projection (►4: no forked content)."""
    raw = spec.get("events") or []
    if not raw and spec.get("categories") and spec.get("values"):     # legacy timeline shape
        raw = [{"at": v, "label": c}
               for c, v in zip(spec["categories"], spec["values"])]
    focus_label = spec.get("focus")
    evs: list[_Ev] = []
    for e in raw:
        lab = str(e.get("label", ""))
        evs.append(_Ev(at=e.get("at"), label=lab, to=e.get("to"),
                       zaesur=bool(e.get("zaesur")), strand=e.get("strand"),
                       focus=bool(e.get("focus")) or (focus_label is not None
                                                      and lab == str(focus_label))))
    # numeric scale iff every placing coordinate is numeric; else fall back to an ordinal axis
    ok = all(_num(e.at) is not None and (e.to is None or _num(e.to) is not None) for e in evs)
    for i, e in enumerate(evs):
        e.at_num = _num(e.at) if ok else float(i)
        e.to_num = _num(e.to) if (ok and e.to is not None) else None
        e.year_str = _year_str(e.at, e.to)
        # keep whole words intact (a mid-word break reads worse than a slightly wider block —
        # lane_pack absorbs the width); hyphenated compounds stay together.
        e.name_wrapped = "\n".join(textwrap.wrap(
            e.label, _NAME_WRAP, break_long_words=False, break_on_hyphens=False)) or e.label
        e.x = (e.at_num + e.to_num) / 2 if e.to_num is not None else e.at_num
    evs.sort(key=_sort_key)
    # ►1 demotion: a Stichwort over the bound becomes a numbered chip; numbering is chronological
    # over the demoted (non-Zäsur) events, and the legend is built from the same order.
    demoted = sorted((e for e in evs if not e.zaesur and len(e.label) > LABEL_BOUND),
                     key=_sort_key)
    for i, e in enumerate(demoted, 1):
        e.demoted, e.chip_no = True, i
    return evs


def _n_lines(e: _Ev) -> int:
    """Text lines in a label block: year + wrapped Stichwort, or year + chip (demoted)."""
    return 2 if e.demoted else 1 + (e.name_wrapped.count("\n") + 1)


def _meas_str(e: _Ev) -> str:
    return e.year_str if e.demoted else f"{e.year_str}\n{e.name_wrapped}"


# --------------------------------------------------------------------------- geometry helpers
def _lh(size: float) -> float:
    """Inches per text line at `size` (incl. leading) — one data-y unit == one inch (inch-true)."""
    return size / 72.0 * 1.30


def _nice_step(span: float, target: int = 8) -> int:
    """A round tick step (decades / half-centuries / centuries by span) giving ~`target` ticks —
    equal spacing = equal duration, made visible."""
    if span <= 0:
        return 1
    raw = span / target
    for s in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 2500, 5000):
        if raw <= s:
            return s
    return 10000


def _ticks(x0: float, x1: float, step: int) -> list[int]:
    start = math.ceil(x0 / step) * step
    return list(range(start, int(x1) + 1, step))


def _lupe_window(evs: list[_Ev], spec: dict) -> tuple[int, int] | None:
    """►3: at most ONE detail window. Explicit `{"from","to"}` wins; "off" suppresses; "auto"
    (default) fires when there are ≥ 5 events AND the densest half of them (⌈n/2⌉ consecutive)
    spans ≤ a quarter of the full span — the minimal such window, snapped OUT to round years."""
    mode = spec.get("lupe", "auto")
    if isinstance(mode, dict) and mode.get("from") is not None:
        return int(mode["from"]), int(mode["to"])
    if mode == "off":
        return None
    pts = sorted(e.at_num for e in evs if e.at_num is not None and not e.zaesur)
    n = len(pts)
    if n < 5:
        return None
    full = pts[-1] - pts[0]
    if full <= 0:
        return None
    k = (n + 1) // 2                                   # ⌈n/2⌉
    best = None                                        # (span, lo, hi) — the densest ⌈n/2⌉-window
    for i in range(0, n - k + 1):
        lo, hi = pts[i], pts[i + k - 1]
        if best is None or (hi - lo) < best[0]:
            best = (hi - lo, lo, hi)
    if best is None or best[0] > full / 4:
        return None
    _, lo, hi = best
    step = max(_nice_step(hi - lo, target=6), 5)
    return int(math.floor(lo / step) * step), int(math.ceil(hi / step) * step)


# --------------------------------------------------------------------------- measurement
def _measure(strings: list[str], xlim: tuple[float, float], size: float) -> list[float]:
    """Widths (in data-x units) under the FINAL horizontal frame — a probe figure identical in
    width geometry to the render (axes fill the figure, same figsize width + xlim), so the measured
    layout reproduces exactly. Width is dpi-independent, so the probe dpi is irrelevant."""
    if not strings:
        return []
    with plt.rc_context(fs.house_rc()):
        fig = plt.figure(figsize=(W_IN, 6.0))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(*xlim)
        ax.set_ylim(0, 6.0)
        ax.axis("off")
        widths = measure_widths(ax, strings, fontsize=size)
        plt.close(fig)
    return widths


# --------------------------------------------------------------------------- band placement
def _emit_band(evs: list[_Ev], axis_y: float, xlim: tuple[float, float],
               side_of, role_of, widths: dict[int, float], size: float,
               *, up_base: float | None = None, down_base: float | None = None,
               group: str = "labels") -> tuple[list, float, float]:
    """Place a set of block-events around a horizontal axis at `axis_y`: a dot (Ereignis) or bar
    (Zeitraum) on the axis, a measured + lane-packed label block (year hugging the axis side in its
    role colour, Stichwort in ink — or a numbered chip when demoted), and a jogged stem. Above-blocks
    stack up from `up_base`, below-blocks stack down from `down_base` (absolute y anchors — the below
    anchor is set past the phase band so the stems cross it, exactly as the mockup). Returns
    (layers, up, down): the outermost block extent above / below in inches."""
    lh = _lh(size)
    x0, x1 = xlim
    gap = (x1 - x0) * 0.012
    up_base = axis_y + 1.1 * lh if up_base is None else up_base
    down_base = axis_y - 1.1 * lh if down_base is None else down_base
    layers: list = []
    up = down = axis_y
    for side in (1, -1):
        se = [e for e in evs if side_of(e) == side]
        if not se:
            continue
        xs = [e.x for e in se]
        wsz = [widths[id(e)] for e in se]
        cx = [min(max(x, x0 + w / 2 + gap), x1 - w / 2 - gap) for x, w in zip(xs, wsz)]
        lanes = lane_pack(cx, wsz, gap=gap)
        max_lines = max(_n_lines(e) for e in se)
        lane_h = (max_lines * 1.16 + 0.55) * lh
        anchor = up_base if side > 0 else down_base
        for e, x, xcc, lane in zip(se, xs, cx, lanes):
            role = role_of(e)
            if e.to_num is not None:                   # a Zeitraum → a bar; an Ereignis → a dot
                layers.append(Line((e.at_num, axis_y), (e.to_num, axis_y), role=role,
                                   width=6.0, z=3, group="marks"))
            else:
                layers.append(PointMark((x, axis_y), role=role, size=6.5, bold=False, z=4,
                                        group="marks"))
            y_lab = anchor + side * lane * lane_h
            # stem: axis → block, with a jog when the block centre was clamped
            layers.append(Polyline([(x, axis_y + side * 0.10 * lh),
                                    (x, y_lab - side * 0.95 * lh),
                                    (xcc, y_lab - side * 0.28 * lh)],
                                   role="muted", width=fs.STROKE.leader, z=1, group=group))
            va = "bottom" if side > 0 else "top"
            layers.append(Label((xcc, y_lab), e.year_str, role=role, size=size, ha="center",
                                va=va, bold=True, z=6, group=group))
            second_y = y_lab + side * 1.16 * lh
            if e.demoted:
                layers.append(Node((xcc, second_y), str(e.chip_no), face_role="surface",
                                   edge_role="ink", text_role="ink", pad=0.26, size=size,
                                   z=6, group=group))
            else:
                layers.append(Label((xcc, second_y), e.name_wrapped, role="ink", size=size,
                                    ha="center", va=va, z=6, group=group))
            reach = (1.0 + 1.20 * (_n_lines(e) - 1)) * lh + 0.35 * lh
            if side > 0:
                up = max(up, y_lab + reach)
            else:
                down = min(down, y_lab - reach)
    return layers, up, down


def _time_axis(x0: float, x1: float, axis_y: float, step: int, *, arrow: bool = True,
               group: str = "axis") -> tuple[list, float]:
    """The Zeitpfeil: a heavy line + a filled arrowhead (time flows →) and round-year ticks with
    muted labels. Returns (layers, tick_label_bottom) — the y below the tick labels."""
    lh = _lh(fs.TYPE.tick)
    tick_len = 0.55 * lh
    layers: list = [Line((x0, axis_y), (x1, axis_y), role="ink", width=2.6, z=2, group=group)]
    if arrow:
        pad = (x1 - x0) * 0.02
        layers.append(Arrow((x1, axis_y), (x1 + pad, axis_y), role="ink", width=2.2, z=2,
                            group=group))
    dy = tick_len + 0.30 * lh
    for t in _ticks(x0, x1, step):
        layers.append(Line((t, axis_y - tick_len), (t, axis_y), role="ink", width=1.0, z=2,
                           group=group))
        layers.append(Label((t, axis_y - dy), f"{t:g}", role="muted", size=fs.TYPE.tick,
                            ha="center", va="top", halo=False, z=2, group=group))
    return layers, axis_y - dy - lh


def _phase_band(phases: list[dict], y0: float, y1: float, group="phases") -> list:
    """Institutional phases as a quiet alternating-tint band under the axis (Periodisierung)."""
    layers: list = []
    base = fs.PALETTE.primary
    for i, ph in enumerate(phases):
        a, b = float(ph.get("from")), float(ph.get("to"))
        box = [(a, y0), (b, y0), (b, y1), (a, y1)]
        layers.append(Region(box, role=fs.lighten(base, 0.82 if i % 2 else 0.68), alpha=1.0,
                             edge_role=fs.lighten(base, 0.45), edge_width=0.7, z=1, group=group))
        layers.append(Label(((a + b) / 2, (y0 + y1) / 2), str(ph.get("label", "")),
                            role=fs.darken(base, 0.25), size=7.6, halo=False, z=2, group=group))
    return layers


def _add_zaesur(sc: Scene, e: _Ev, xlim, y0: float, y1: float, group="marks") -> None:
    """A turning point: a quiet dashed full-height rule + a small italic caption at the top."""
    x = e.at_num if e.at_num is not None else 0.0
    sc.add(Line((x, y0), (x, y1), role="muted", width=1.1, dash=(0, (4, 3)), z=1, group=group))
    cap = e.label if len(e.label) <= 40 else e.label[:38] + "…"
    dx = (xlim[1] - xlim[0]) * 0.004
    sc.add(Label((x - dx, y1), f"{e.year_str} · {cap}", role="muted", size=7.6, ha="right",
                 va="top", italic=True, halo=True, z=7, group=group))


def _add_legend(sc: Scene, demoted: list[_Ev], xlim, top: float) -> float:
    """The numbered legend under the band (►1): each demoted event's chip number + its full original
    label (the sentence too long for the axis). Returns the new bottom y."""
    lh = _lh(fs.TYPE.annot)
    x0 = xlim[0] + (xlim[1] - xlim[0]) * 0.01
    chip_w = (xlim[1] - xlim[0]) * 0.026
    y = top - 1.1 * lh
    for e in demoted:
        sc.add(Node((x0 + chip_w * 0.5, y), str(e.chip_no), face_role="surface", edge_role="ink",
                    text_role="ink", pad=0.24, size=fs.TYPE.annot, z=6, group="legend"))
        text = e.label if e.to is None else f"{e.label} ({e.year_str})"
        sc.add(Label((x0 + chip_w * 1.35, y), text, role="ink", size=fs.TYPE.annot, ha="left",
                     va="center", halo=False, z=6, group="legend"))
        y -= 1.32 * lh
    return y - 0.3 * lh


# --------------------------------------------------------------------------- role / side
def _role_of(strands: list[str]):
    """Semantic role for an event: `focus` when highlighted; else the strand's role (above =
    primary, below = secondary) or plain `primary` in the M1 alternating form."""
    def role(e: _Ev) -> str:
        if e.focus:
            return "focus"
        if strands:
            return "primary" if e.strand == strands[0] else "secondary"
        return "primary"
    return role


def _alternating_side(block_evs: list[_Ev]):
    order = {id(e): i for i, e in enumerate(block_evs)}

    def side(e: _Ev) -> int:
        return 1 if order[id(e)] % 2 == 0 else -1
    return side


def _strand_side(strands: list[str]):
    def side(e: _Ev) -> int:
        return 1 if e.strand == strands[0] else -1
    return side


def _xlim_for(evs: list[_Ev]) -> tuple[tuple[float, float], float, float, float]:
    nums = [e.at_num for e in evs if e.at_num is not None]
    nums += [e.to_num for e in evs if e.to_num is not None]
    dmin, dmax = (min(nums), max(nums)) if nums else (0.0, 1.0)
    span = (dmax - dmin) or 1.0
    xpad = span * 0.08
    return (dmin - xpad, dmax + xpad + span * 0.03), dmin, dmax, span


# --------------------------------------------------------------------------- the solved band (M1/M2)
def _solved_scene(spec: dict, evs: list[_Ev]) -> Scene:
    strands = list(spec.get("strands") or [])
    phases = list(spec.get("phases") or [])
    lupe = _lupe_window(evs, spec)
    block_evs = [e for e in evs if not e.zaesur]
    zaesur_evs = [e for e in evs if e.zaesur]
    xlim, dmin, dmax, span = _xlim_for(evs)
    step = _nice_step(span)
    role_of = _role_of(strands)
    widths = {id(e): w for e, w in zip(block_evs,
                                       _measure([_meas_str(e) for e in block_evs], xlim,
                                                fs.TYPE.annot))}

    if lupe:
        return _lupe_scene(spec, evs, block_evs, zaesur_evs, strands, role_of,
                           xlim, dmin, dmax, step, widths)

    lh = _lh(fs.TYPE.annot)
    side_of = _strand_side(strands) if strands else _alternating_side(block_evs)
    axis_layers, tick_bottom = _time_axis(dmin, dmax, 0.0, step)

    phase_layers: list = []
    down_base = tick_bottom - 0.8 * lh
    if phases:
        band_top = tick_bottom - 0.30 * lh
        band_bot = band_top - 1.35 * lh
        phase_layers = _phase_band(phases, band_bot, band_top)
        down_base = band_bot - 0.9 * lh

    layers, up, down = _emit_band(block_evs, 0.0, xlim, side_of, role_of, widths, fs.TYPE.annot,
                                  up_base=1.1 * lh, down_base=down_base)

    sc = Scene(canvas=Canvas(figsize=(W_IN, 1.0), aspect="auto", frame="off", xlim=xlim))
    sc.add(*axis_layers, *phase_layers, *layers)

    for e in zaesur_evs:
        _add_zaesur(sc, e, xlim, down, up, group="marks")

    legend_bottom = down
    if any(e.demoted for e in block_evs):
        legend_bottom = _add_legend(sc, sorted((e for e in block_evs if e.demoted),
                                               key=lambda e: e.chip_no), xlim, down)

    y_top = up
    if spec.get("title"):
        y_top = up + 1.0 * lh
        sc.add(Label(((dmin + dmax) / 2, y_top), str(spec["title"]), role="ink",
                     size=fs.TYPE.title, va="bottom", bold=True, halo=False, z=8))
        y_top += _lh(fs.TYPE.title)

    if strands:
        sc.add(Label((xlim[0] + span * 0.01, up + 0.2 * lh), strands[0].upper(), role="primary",
                     size=fs.TYPE.annot, ha="left", va="bottom", bold=True, halo=False, z=8))
        sc.add(Label((xlim[0] + span * 0.01, legend_bottom + 0.1 * lh), strands[1].upper(),
                     role="secondary", size=fs.TYPE.annot, ha="left", va="bottom", bold=True,
                     halo=False, z=8))

    _finish(sc, xlim, legend_bottom, y_top)
    return sc


# --------------------------------------------------------------------------- the Lupe (M3)
def _lupe_scene(spec, evs, block_evs, zaesur_evs, strands, role_of, xlim, dmin, dmax, step,
                widths) -> Scene:
    """Main full-span band on top (non-windowed events labelled + windowed events as preview dots),
    a shaded dashed window, explicit connectors, and a second internally-linear zoom band below with
    its own round-year ticks (labels BELOW) — the M3 form."""
    win_lo, win_hi = _lupe_window(evs, spec)
    lh = _lh(fs.TYPE.annot)
    inside = [e for e in block_evs if e.at_num is not None and win_lo <= e.at_num <= win_hi]
    outside = [e for e in block_evs if e not in inside]
    zx0, zx1 = dmin, dmax

    def Z(t: float) -> float:                          # window year → zoom-band x (linear)
        return zx0 + (t - win_lo) / (win_hi - win_lo) * (zx1 - zx0)

    # --- zoom band at y=0 (labels below) ---
    zoom_evs: list[_Ev] = []
    for e in inside:
        z = _Ev(at=e.at, label=e.label, to=e.to, strand=e.strand, focus=e.focus)
        z.at_num, z.to_num = Z(e.at_num), (Z(e.to_num) if e.to_num is not None else None)
        z.year_str, z.name_wrapped = e.year_str, e.name_wrapped
        z.demoted, z.chip_no = e.demoted, e.chip_no
        z.x = (z.at_num + z.to_num) / 2 if z.to_num is not None else z.at_num
        widths[id(z)] = widths[id(e)]
        zoom_evs.append(z)
    ztick_len = 0.55 * _lh(fs.TYPE.tick)
    ztick_bottom = -ztick_len - 1.3 * _lh(fs.TYPE.tick)
    zoom_layers, _zu, zoom_bottom = _emit_band(zoom_evs, 0.0, xlim, lambda e: -1, role_of, widths,
                                               fs.TYPE.annot, down_base=ztick_bottom - 0.5 * lh)
    zaxis: list = [Line((zx0, 0.0), (zx1, 0.0), role="ink", width=2.6, z=2, group="axis")]
    zstep = max(_nice_step(win_hi - win_lo, 5), 5)
    for t in _ticks(win_lo, win_hi, zstep):
        zt = Z(t)
        zaxis.append(Line((zt, -ztick_len), (zt, 0.0), role="ink", width=1.0, z=2, group="axis"))
        zaxis.append(Label((zt, -ztick_len - 0.30 * _lh(fs.TYPE.tick)), f"{t:g}", role="muted",
                           size=fs.TYPE.tick, ha="center", va="top", halo=False, z=2,
                           group="axis"))

    # --- main band above the zoom band ---
    win_h = 1.15 * lh
    y_main = -zoom_bottom + 2.4 * lh
    main_layers, up, _dn = _emit_band(outside, y_main, xlim, lambda e: 1, role_of, widths,
                                      fs.TYPE.annot, up_base=y_main + 1.1 * lh)
    axis_layers, _tb = _time_axis(dmin, dmax, y_main, step)
    preview = [PointMark((e.x, y_main), role="primary", size=3.4, bold=False, z=3, group="marks")
               for e in inside]
    window_box = Region([(win_lo, y_main - win_h), (win_hi, y_main - win_h),
                         (win_hi, y_main + win_h), (win_lo, y_main + win_h)],
                        role=fs.PALETTE.surface, alpha=1.0, edge_role="muted", edge_width=0.9,
                        z=1, group="lupe")
    conn = [Line((win_lo, y_main - win_h), (zx0, 0.06), role="muted", width=0.8, dash=(0, (3, 2)),
                 z=1, group="lupe"),
            Line((win_hi, y_main - win_h), (zx1, 0.06), role="muted", width=0.8, dash=(0, (3, 2)),
                 z=1, group="lupe")]
    caption = Label((zx0, ztick_bottom - 0.3 * lh), f"Lupe: {win_lo}–{win_hi}", role="muted",
                    size=7.6, ha="left", va="top", italic=True, halo=False, z=6, group="lupe")

    sc = Scene(canvas=Canvas(figsize=(W_IN, 1.0), aspect="auto", frame="off", xlim=xlim))
    sc.add(window_box, *conn, *zaxis, *zoom_layers, caption, *axis_layers, *preview, *main_layers)

    top_all = y_main + up if outside else y_main + 1.5 * lh
    for e in zaesur_evs:
        _add_zaesur(sc, e, xlim, zoom_bottom, top_all, group="marks")

    legend_bottom = min(zoom_bottom, ztick_bottom - 1.4 * lh)
    if any(e.demoted for e in block_evs):
        legend_bottom = _add_legend(sc, sorted((e for e in block_evs if e.demoted),
                                               key=lambda e: e.chip_no), xlim, legend_bottom)

    y_top = top_all
    if spec.get("title"):
        y_top = top_all + 1.0 * lh
        sc.add(Label(((dmin + dmax) / 2, y_top), str(spec["title"]), role="ink",
                     size=fs.TYPE.title, va="bottom", bold=True, halo=False, z=8))
        y_top += _lh(fs.TYPE.title)

    _finish(sc, xlim, legend_bottom, y_top)
    return sc


# --------------------------------------------------------------------------- Arbeitsobjekt (M4)
def _arbeitsobjekt_scene(spec: dict, evs: list[_Ev]) -> Scene:
    """The student work-object projection (►4): year chips (Node boxes) lane-packed ABOVE the axis
    and an Ereignis-Kärtchen bank (blank lines to fill the year in) BELOW — the chronology-ordering
    task fused into the figure. Shares the SAME computed layout (`_parse_events`) as the solved band;
    only the decoration differs (no name labels next to the marks — the names live in the bank). The
    years-masked harder variant is OUT (a follow-up)."""
    block_evs = [e for e in evs if not e.zaesur and e.at_num is not None]
    xlim, dmin, dmax, span = _xlim_for(block_evs)
    step = _nice_step(span)
    lh = _lh(fs.TYPE.annot)

    # year chips lane-packed above the axis (box padding widens the measured year width)
    ws = [w * 1.5 for w in _measure([e.year_str for e in block_evs], xlim, fs.TYPE.annot)]
    gap = span * 0.012
    x0, x1 = xlim
    xs = [e.x for e in block_evs]
    cx = [min(max(x, x0 + w / 2 + gap), x1 - w / 2 - gap) for x, w in zip(xs, ws)]
    lanes = lane_pack(cx, ws, gap=gap)
    chip_lh, base = 2.0 * lh, 1.4 * lh

    sc = Scene(canvas=Canvas(figsize=(W_IN, 1.0), aspect="auto", frame="off", xlim=xlim))
    axis_layers, tick_bottom = _time_axis(dmin, dmax, 0.0, step)
    sc.add(*axis_layers)
    top = 0.0
    for e, x, xcc, lane in zip(block_evs, xs, cx, lanes):
        y_chip = base + lane * chip_lh
        if e.to_num is not None:
            sc.add(Line((e.at_num, 0.0), (e.to_num, 0.0), role="ink", width=6.0, z=3,
                        group="marks"))
        else:
            sc.add(PointMark((x, 0.0), role="ink", size=6.0, bold=False, z=4, group="marks"))
        sc.add(Polyline([(x, 0.10 * lh), (x, y_chip - 0.62 * lh)], role="muted",
                        width=fs.STROKE.leader, z=1, group="chips"))
        sc.add(Node((xcc, y_chip), e.year_str, face_role="paper", edge_role="ink",
                    text_role="ink", pad=0.32, size=fs.TYPE.annot, z=5, group="chips"))
        top = max(top, y_chip + 0.9 * lh)

    prompt_y = top + 1.2 * lh
    sc.add(Label(((dmin + dmax) / 2, prompt_y), "Trage bei jedem Ereignis das passende Jahr ein.",
                 role="muted", size=fs.TYPE.annot, va="bottom", italic=True, halo=False, z=6,
                 group="chips"))
    y_top = prompt_y + 1.2 * lh

    # the Ereignis-Kärtchen bank (full names + a blank line each), sorted alphabetically
    bank = sorted(block_evs, key=lambda e: e.label.casefold())
    ncol = 2 if len(bank) > 5 else 1
    rows = (len(bank) + ncol - 1) // ncol
    row_h = 1.9 * lh
    bx0, bx1 = dmin - span * 0.03, dmax + span * 0.03
    by1 = tick_bottom - 1.0 * lh
    by0 = by1 - (2.0 * lh + rows * row_h)
    sc.add(Region([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], role=fs.PALETTE.surface,
                  alpha=1.0, edge_role="muted", edge_width=0.9, z=1, group="bank"))
    sc.add(Label((bx0 + span * 0.02, by1 - 0.55 * lh), "Ereignis-Kärtchen", role="ink",
                 size=fs.TYPE.annot_lg, ha="left", va="top", bold=True, halo=False, z=2,
                 group="bank"))
    col_w = (bx1 - bx0) / ncol
    line_w = col_w * 0.15
    for i, e in enumerate(bank):
        col, row = i // rows, i % rows
        cxx = bx0 + span * 0.02 + col * col_w
        cyy = by1 - 2.0 * lh - row * row_h
        sc.add(Line((cxx, cyy - 0.20 * lh), (cxx + line_w, cyy - 0.20 * lh), role="muted",
                    width=1.0, z=2, group="bank"))
        sc.add(Label((cxx + line_w * 1.25, cyy), e.label, role="ink", size=fs.TYPE.annot,
                     ha="left", va="center", halo=False, z=2, group="bank"))

    y_top = _title_top(sc, spec, dmin, dmax, y_top, lh)
    _finish(sc, xlim, by0, y_top)
    return sc


# --------------------------------------------------------------------------- finishing
def _title_top(sc: Scene, spec: dict, dmin: float, dmax: float, y_top: float, lh: float) -> float:
    if spec.get("title"):
        y_top = y_top + 0.4 * lh
        sc.add(Label(((dmin + dmax) / 2, y_top), str(spec["title"]), role="ink",
                     size=fs.TYPE.title, va="bottom", bold=True, halo=False, z=8))
        y_top += _lh(fs.TYPE.title)
    return y_top


def _finish(sc: Scene, xlim, y_min: float, y_max: float) -> None:
    """Set the inch-true Canvas: axes fill the figure, ylim spans exactly the figure height in
    inches, so one data-y unit == one inch (a lane is exactly as tall as its measured text)."""
    pad = 0.18
    sc.canvas.xlim = xlim
    sc.canvas.ylim = (y_min - pad, y_max + pad)
    sc.canvas.figsize = (W_IN, (y_max + pad) - (y_min - pad))


# --------------------------------------------------------------------------- public API
def zeitband_scene(spec: dict | None = None) -> Scene:
    """Compute the Zeitband `Scene` from a spec:
    {events:[{at, to?, label, zaesur?, strand?, focus?}], strands?:[a,b], phases?:[{from,to,label}],
     lupe?:"auto"|"off"|{from,to}, variant?:"solved"|"arbeitsobjekt", focus?:str, title?}.
    Over-long labels auto-demote to numbered chips + a legend (►1); the Lupe auto-triggers on
    clustering (►3); `variant="arbeitsobjekt"` returns the student work-object projection (►4)."""
    spec = dict(spec or {})
    evs = _parse_events(spec)
    if not evs:
        return Scene(canvas=Canvas(figsize=(W_IN, 1.2), frame="off"))
    if spec.get("variant") == "arbeitsobjekt":
        return _arbeitsobjekt_scene(spec, evs)
    return _solved_scene(spec, evs)


def zeitband_figure(scene: Scene):
    """Build the inch-true matplotlib figure for a Zeitband scene (axes fill the figure so one
    data-y unit == one inch). Returns (fig, ax) — the caller draws/saves/closes under
    `plt.rc_context(fs.house_rc())`. Shared by the recipe, the specimen, and the overlap tests."""
    fig = plt.figure(figsize=scene.canvas.figsize)
    ax = fig.add_axes([0, 0, 1, 1])
    render_scene(scene, ax)
    return fig, ax


def zeitband_to_png(scene: Scene, path, *, dpi: int = 150):
    """Render a Zeitband scene to a PNG (inch-true, house style scoped)."""
    with plt.rc_context(fs.house_rc()):
        fig, _ax = zeitband_figure(scene)
        fig.savefig(path, dpi=dpi)
        plt.close(fig)
    return path
