"""Zeitleiste redesign mockups — the four candidate forms over the REAL content of the two
revise-flagged sheets (c0213 Kolonialismus, c0214 Europäische Integration). Design companion
to `Documents/zeitleiste-design.md` (the ► decisions live there); nothing here is imported by
the engine — like `tools/plane3d_specimen.py`, this is a kept prototype awaiting promotion.

    python -m tools.zeitleiste_mockup     # -> runs/specimens/zeitleiste/m{1..4}_*.png

  m1_zeitband.png      the Schulbuch-Zeitband default: Stichwort labels, decade ticks,
                       phase band, Zäsur, focus event                      (c0214 data)
  m2_synchronoptik.png two semantic lanes: Europa above / Österreich below (c0214 +
                       curated additions — the 1955/1972/1989/1994 events are mockup-only
                       and need SME vetting; in production they come from the fact-set)
  m3_lupe.png          the detail-window answer to clustered history; spans as bars
                       (c0213 data)
  m4_arbeitsobjekt.png the student work-object projection: year chips + Kärtchen-bank
                       (c0214 data; teacher projection = m1)

Layout discipline (what the promoted recipe must keep): ylim is FIXED before measuring,
label widths are measured (`figtext.measure_widths`), lanes packed (`figtext.lane_pack`),
and every vertical offset is a multiple of the MEASURED line height under the final ylim.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from teachersaid.config import RUNS_DIR
from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.figtext import lane_pack, measure_widths

fs.use_house_style()
OUT = RUNS_DIR / "specimens" / "zeitleiste"

INK, MUT = fs.PALETTE.ink, fs.PALETTE.muted
PRIM, SEC, FOC = fs.PALETTE.primary, fs.PALETTE.secondary, fs.PALETTE.focus


# --------------------------------------------------------------------------- helpers
def line_h(ax, fontsize: float) -> float:
    """Data-units height of one text line at `fontsize` — valid once ylim is FINAL."""
    fig = ax.figure
    h_in = ax.get_position().height * fig.get_size_inches()[1]
    span = ax.get_ylim()[1] - ax.get_ylim()[0]
    return (fontsize / 72.0) * 1.30 / h_in * span


def time_axis(ax, x0, x1, ticks, *, y=0.0, minor=(), arrow=True, tick_labels=None):
    """The Zeitpfeil: a heavy line with an arrowhead (time flows ->) and regular ticks —
    equal spacing = equal duration, made visible. `tick_labels` overrides the printed
    labels (for a mapped zoom band). Returns the y of the tick-label bottom."""
    lht = line_h(ax, fs.TYPE.tick)
    tick_len = 0.55 * lht
    ax.plot([x0, x1], [y, y], color=INK, lw=2.6, zorder=2, solid_capstyle="butt")
    if arrow:
        pad = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.018
        ax.annotate("", xy=(x1 + pad, y), xytext=(x1, y), zorder=2,
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=2.2,
                                    shrinkA=0, shrinkB=0))
    for t in minor:
        ax.plot([t, t], [y - tick_len * 0.5, y], color=MUT, lw=0.7, zorder=2)
    dy = tick_len + 0.25 * lht
    labels = tick_labels or [f"{t:g}" for t in ticks]
    for t, lab in zip(ticks, labels):
        ax.plot([t, t], [y - tick_len, y], color=INK, lw=1.0, zorder=2)
        ax.text(t, y - dy, str(lab), ha="center", va="top",
                fontsize=fs.TYPE.tick, color=MUT)
    return y - dy - 1.05 * lht


def place_events(ax, events, *, side=1, y_base, y_axis=0.0, gap_years=None,
                 name_size=None):
    """Measured, lane-packed event labels. `events`: dicts with
      at        year (dot position; spans use the midpoint of at..to)
      to        optional end year -> drawn as a bar on the axis (Zeitraum, not Ereignis)
      year      the printed year string (default str(at))
      name      short Stichwort, may contain \\n  (NEVER a sentence)
      color     semantic colour (strand); focus for the highlighted event
    side=+1 above the axis, -1 below.  The year always hugs the axis side of the block."""
    name_size = name_size or fs.TYPE.annot
    x0, x1 = ax.get_xlim()
    lh = line_h(ax, name_size)
    gap = gap_years if gap_years is not None else (x1 - x0) * 0.012

    xs = [(e["at"] + e.get("to", e["at"])) / 2 for e in events]
    blocks = [f'{e.get("year", e["at"])}\n{e["name"]}' for e in events]
    widths = measure_widths(ax, blocks, fontsize=name_size)
    # clamp block centres inside the frame, then pack with the clamped centres
    cx = [min(max(x, x0 + w / 2 + gap), x1 - w / 2 - gap) for x, w in zip(xs, widths)]
    lanes = lane_pack(cx, widths, gap=gap)

    n_lines = [b.count("\n") + 1 for b in blocks]
    lane_h = max(n_lines) * 1.16 * lh + 0.55 * lh

    for e, x, xc, lane in zip(events, xs, cx, lanes):
        col = e.get("color", PRIM)
        y_lab = y_base + side * lane * lane_h
        # marker: a dot for an Ereignis, a rounded bar for a Zeitraum
        if e.get("to"):
            ax.plot([e["at"], e["to"]], [y_axis, y_axis], color=col, lw=7,
                    solid_capstyle="round", zorder=3)
        else:
            ax.plot([x], [y_axis], "o", color=col, ms=7.5, zorder=3,
                    markeredgecolor="white", markeredgewidth=1.0)
        # stem: axis -> just short of the block, with a jog when the block was clamped
        y_stop = y_lab - side * 0.28 * lh
        y_jog = y_lab - side * 0.95 * lh
        ax.plot([x, x, xc], [y_axis + side * 0.10, y_jog, y_stop],
                color=MUT, lw=fs.STROKE.leader, zorder=1)
        yr = str(e.get("year", e["at"]))
        if side > 0:      # year = bottom line of the block (nearest the axis)
            ax.text(xc, y_lab, yr, ha="center", va="bottom", fontsize=name_size,
                    color=col, weight="bold", zorder=4)
            ax.text(xc, y_lab + 1.16 * lh, e["name"], ha="center", va="bottom",
                    fontsize=name_size, color=INK, zorder=4, linespacing=1.16)
        else:             # below the axis: year = top line
            ax.text(xc, y_lab, yr, ha="center", va="top", fontsize=name_size,
                    color=col, weight="bold", zorder=4)
            ax.text(xc, y_lab - 1.16 * lh, e["name"], ha="center", va="top",
                    fontsize=name_size, color=INK, zorder=4, linespacing=1.16)


def phase_band(ax, phases, y0, y1, *, color=None):
    """Institutional phases as a quiet band under the axis (Periodisierung)."""
    color = color or PRIM
    for i, (a, b, lab) in enumerate(phases):
        ax.add_patch(Rectangle((a, y0), b - a, y1 - y0, zorder=1,
                               facecolor=fs.lighten(color, 0.82 if i % 2 else 0.68),
                               edgecolor=fs.lighten(color, 0.45), lw=0.7))
        ax.text((a + b) / 2, (y0 + y1) / 2, lab, ha="center", va="center",
                fontsize=7.6, color=fs.darken(color, 0.25), zorder=2)


def zaesur(ax, x, y0, y1, label):
    """A turning point: a quiet dashed rule across the whole band."""
    ax.plot([x, x], [y0, y1], color=MUT, lw=1.1, ls=(0, (4, 3)), zorder=1)
    ax.text(x - 1.2, y1, label, ha="right", va="top", fontsize=7.6,
            style="italic", color=MUT, zorder=2)


def new_fig(w, h, ylim, xlim, title):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.03)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    ax.set_title(title, fontsize=fs.TYPE.title, color=INK, pad=12)
    return fig, ax


# ------------------------------------------------------------------- M1: Zeitband
def m1():
    fig, ax = new_fig(8.8, 3.9, (-5.2, 4.1), (1942, 2028),
                      "Europäische Integration 1951–2020")
    lh = line_h(ax, fs.TYPE.annot)

    ticks_bottom = time_axis(ax, 1945, 2024, ticks=range(1950, 2021, 10))
    band_top = ticks_bottom - 0.35 * lh
    band_bot = band_top - 1.35 * lh
    zaesur(ax, 1989, band_top, 3.9, "1989 · Fall des Eisernen Vorhangs")
    phase_band(ax, [(1951, 1957, "EGKS"), (1957, 1993, "EWG / EG"),
                    (1993, 2028, "Europäische Union")], band_bot, band_top)

    above = [
        dict(at=1951, name="Montanunion\n(EGKS)"),
        dict(at=1993, name="Vertrag von\nMaastricht"),
        dict(at=2002, name="Euro-Bargeld"),
        dict(at=2009, name="Vertrag von\nLissabon"),
    ]
    below = [
        dict(at=1957, name="Römische\nVerträge"),
        dict(at=1995, name="EU-Beitritt\nÖsterreichs", color=FOC),
        dict(at=2004, name="Osterweiterung"),
        dict(at=2020, name="Brexit"),
    ]
    place_events(ax, above, side=1, y_base=1.5 * lh)
    place_events(ax, below, side=-1, y_base=band_bot - 1.5 * lh)
    fig.savefig(OUT / "m1_zeitband.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# -------------------------------------------------------------- M2: Synchronoptik
def m2():
    fig, ax = new_fig(8.8, 5.4, (-6.4, 6.0), (1942, 2028),
                      "Europäische Integration und Österreichs Weg in die EU")
    lh = line_h(ax, fs.TYPE.annot)

    ticks_bottom = time_axis(ax, 1945, 2024, ticks=range(1950, 2021, 10))

    europa = [
        dict(at=1951, name="Montanunion\n(EGKS)"),
        dict(at=1957, name="Römische\nVerträge"),
        dict(at=1993, name="Vertrag von\nMaastricht"),
        dict(at=2002, name="Euro-Bargeld"),
        dict(at=2004, name="Osterweiterung"),
        dict(at=2009, name="Vertrag von\nLissabon"),
        dict(at=2020, name="Brexit"),
    ]
    oesterreich = [
        dict(at=1955, name="Staatsvertrag\nund Neutralität", color=SEC),
        dict(at=1972, name="Freihandels-\nabkommen (EWG)", color=SEC),
        dict(at=1989, name="EG-Beitritts-\nansuchen", color=SEC),
        dict(at=1994, name="Volksabstimmung\n(66,6 % Ja)", color=SEC),
        dict(at=1995, name="EU-Beitritt", color=FOC),
    ]
    place_events(ax, europa, side=1, y_base=1.5 * lh)
    place_events(ax, oesterreich, side=-1, y_base=ticks_bottom - 1.2 * lh)

    ax.text(1943, 5.7, "EUROPÄISCHE EBENE", fontsize=8.2, color=PRIM,
            weight="bold", ha="left", va="top")
    ax.text(1943, -6.1, "ÖSTERREICH", fontsize=8.2, color=SEC,
            weight="bold", ha="left", va="bottom")
    fig.savefig(OUT / "m2_synchronoptik.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- M3: die Lupe
def m3():
    fig, ax = new_fig(8.8, 5.0, (-4.2, 6.1), (1442, 1985),
                      "Kolonialismus und Imperialismus 1494–1919")
    lh = line_h(ax, fs.TYPE.annot)
    y_main = 3.35

    # main band: the full, honest span with a shaded Lupen-Fenster over the cluster
    time_axis(ax, 1450, 1945, ticks=range(1500, 1901, 100), y=y_main,
              minor=range(1450, 1951, 50))
    win_h = 1.15 * lh
    ax.add_patch(Rectangle((1830, y_main - win_h), 90, 2 * win_h, zorder=1,
                           facecolor=fs.PALETTE.surface, edgecolor=MUT,
                           lw=0.9, ls=(0, (3, 2))))
    for yr in (1834, 1857, 1884, 1904, 1919):        # honest density preview
        ax.plot([yr], [y_main], "o", color=PRIM, ms=3.4, zorder=3)
    place_events(ax, [dict(at=1494, name="Vertrag von\nTordesillas"),
                      dict(at=1602, name="Gründung\nder VOC")],
                 side=1, y_base=y_main + 1.5 * lh, y_axis=y_main)

    # the zoom band: same linearity INSIDE, the mapping made explicit by the connectors
    zx0, zx1 = 1450, 1945          # zoom band drawn across the full frame width
    za, zb = 1830, 1920            # …showing this window

    def Z(t):                      # window year -> zoom-band x
        return zx0 + (t - za) / (zb - za) * (zx1 - zx0)

    ax.plot([1830, zx0], [y_main - win_h, 0.06], color=MUT, lw=0.8,
            ls=(0, (3, 2)), zorder=1)
    ax.plot([1920, zx1], [y_main - win_h, 0.06], color=MUT, lw=0.8,
            ls=(0, (3, 2)), zorder=1)
    ticks_bottom = time_axis(ax, zx0, zx1, ticks=[Z(t) for t in range(1830, 1911, 20)],
                             tick_labels=[str(t) for t in range(1830, 1911, 20)],
                             minor=[Z(t) for t in range(1830, 1921, 10)], arrow=False)

    zoom_events = [
        dict(at=Z(1834), name="Abschaffung\nder Sklaverei", year=1834),
        dict(at=Z(1857), name="Aufstand\nin Indien", year=1857),
        dict(at=Z(1884), to=Z(1885), name="Berliner\nKonferenz", year="1884–85"),
        dict(at=Z(1904), to=Z(1908), name="Krieg gegen\nHerero und Nama",
             year="1904–08", color=FOC),
        dict(at=Z(1919), name="Völkerbund-\nmandate", year=1919),
    ]
    place_events(ax, zoom_events, side=-1, y_base=ticks_bottom - 1.2 * lh)
    ax.text(zx0, y_main - win_h - 0.5 * lh, "Lupe: 1830–1920", fontsize=7.6,
            style="italic", color=MUT, ha="left", va="top")
    fig.savefig(OUT / "m3_lupe.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------- M4: das Arbeitsblatt-Objekt
def m4():
    fig, ax = new_fig(8.8, 4.6, (-6.3, 3.6), (1942, 2028),
                      "Europäische Integration – Ordne zu")
    lh = line_h(ax, fs.TYPE.annot)

    time_axis(ax, 1945, 2024, ticks=range(1950, 2021, 10))

    years = [1951, 1957, 1993, 1995, 2002, 2004, 2009, 2020]
    # year chips (rounded boxes), lane-packed so the 1993–2009 cluster staggers cleanly
    widths = measure_widths(ax, [str(y) for y in years], fontsize=8.5)
    widths = [w * 1.45 for w in widths]              # + the chip box padding
    lanes = lane_pack(years, widths, gap=1.2)
    y0_chip = 2.0 * lh
    lane_step = 2.1 * lh
    for yr, lane in zip(years, lanes):
        y_chip = y0_chip + lane * lane_step
        ax.plot([yr], [0], "o", color=INK, ms=6, zorder=3,
                markeredgecolor="white", markeredgewidth=1.0)
        ax.plot([yr, yr], [0.10, y_chip - 0.65 * lh], color=MUT,
                lw=fs.STROKE.leader, zorder=1)
        ax.text(yr, y_chip, str(yr), ha="center", va="center", fontsize=8.5,
                color=INK, weight="bold", zorder=4,
                bbox=dict(boxstyle="round,pad=0.32", facecolor="white",
                          edgecolor=INK, linewidth=1.1))
    top_chip = y0_chip + max(lanes) * lane_step
    ax.text(1985, top_chip + 2.2 * lh,
            "Trage bei jedem Ereignis das passende Jahr ein.",
            fontsize=8.4, style="italic", color=MUT, ha="center", va="bottom")

    # the Kärtchen-Bank (shuffled alphabetically — deterministic)
    bank = ["Brexit", "EU-Beitritt Österreichs", "Euro-Bargeld", "Montanunion (EGKS)",
            "Osterweiterung", "Römische Verträge", "Vertrag von Lissabon",
            "Vertrag von Maastricht"]
    row_h = 1.75 * lh
    bx0, bx1 = 1948, 2021
    by1 = -3.4 * lh - 1.0
    by0 = by1 - 2.2 * lh - 4 * row_h
    ax.add_patch(Rectangle((bx0, by0), bx1 - bx0, by1 - by0,
                           facecolor=fs.PALETTE.surface, edgecolor=MUT, lw=0.9,
                           zorder=1))
    ax.text(bx0 + 2, by1 - 0.55 * lh, "Ereignis-Kärtchen", fontsize=8.6,
            weight="bold", color=INK, ha="left", va="top", zorder=2)
    col_x = (bx0 + 3.5, bx0 + 39.5)
    for i, label in enumerate(bank):
        cxx = col_x[i // 4]
        cyy = by1 - 2.2 * lh - (i % 4) * row_h
        ax.plot([cxx, cxx + 7.5], [cyy - 0.15 * lh, cyy - 0.15 * lh],
                color=MUT, lw=1.0, zorder=2)
        ax.text(cxx + 9.0, cyy, label, fontsize=8.6, color=INK, ha="left",
                va="center", zorder=2)
    fig.savefig(OUT / "m4_arbeitsobjekt.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    m1()
    m2()
    m3()
    m4()
    return OUT


if __name__ == "__main__":
    print(render())
