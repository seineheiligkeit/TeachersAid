"""The Zeitband engine (`pipeline/zeitleiste.py`) — the computed Schulbuch-Zeitleiste family.

Defining-property tests, offline + deterministic (the house style): measured layout never overlaps
(the c0213/c0214 regression is structurally closed), over-long labels demote to chips + a legend
(►1), spans render as bars, the Synchronoptik strand split is validated + geometric, the Lupe
auto-triggers deterministically (►3), and the Arbeitsobjekt is a second projection of ONE computed
layout (►4). The legacy `matplotlib:timeline` recipe stays alive beside it.
"""

from __future__ import annotations

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline import zeitleiste as zl
from teachersaid.pipeline.figtext import overlap_pairs
from teachersaid.pipeline.scene import Label, Line, Node, PointMark
from teachersaid.pipeline.zeitleiste import _year_str, zeitband_figure, zeitband_scene

PNG = b"\x89PNG\r\n\x1a\n"

# --- the real dense specs (byte-faithful transcriptions of runs/store/c0213 · c0214) ----------
C0214_SHORT = [                                    # the SME Stichwörter (sentences → Darstellung)
    {"at": 1951, "label": "Montanunion (EGKS)"},
    {"at": 1957, "label": "Römische Verträge"},
    {"at": 1993, "label": "Vertrag von Maastricht"},
    {"at": 1995, "label": "EU-Beitritt Österreichs"},
    {"at": 2002, "label": "Euro-Bargeld"},
    {"at": 2004, "label": "Osterweiterung"},
    {"at": 2009, "label": "Vertrag von Lissabon"},
    {"at": 2020, "label": "Brexit"},
]
C0213_SENTENCES = [                                # the real revise-flagged sentence labels
    {"at": 1494, "label": "Vertrag von Tordesillas: Aufteilung der überseeischen Welt "
                          "zwischen Spanien und Portugal"},
    {"at": 1602, "label": "Gründung der Niederländischen Ostindien-Kompanie (VOC)"},
    {"at": 1834, "label": "Abschaffung der Sklaverei im Britischen Empire"},
    {"at": 1857, "label": "Aufstand gegen die britische Herrschaft in Indien"},
    {"at": 1884, "label": "Berliner Konferenz: Regeln für die Aufteilung Afrikas (bis 1885)"},
    {"at": 1904, "label": "Kolonialkrieg gegen Herero und Nama in Deutsch-Südwestafrika (bis 1908)"},
    {"at": 1919, "label": "Neuverteilung der Kolonien als Völkerbundmandate nach dem "
                          "Ersten Weltkrieg"},
]


def _overlaps(scene):
    """Overlapping label pairs on the REAL rendered figure (`figtext.overlap_pairs`), captured
    under the house style so the font matches the measured layout."""
    with plt.rc_context(fs.house_rc()):
        fig, _ax = zeitband_figure(scene)
        fig.canvas.draw()
        try:
            return overlap_pairs(fig)
        finally:
            plt.close(fig)


def _labels(scene, *, group=None):
    return [L for L in scene.layers if isinstance(L, Label)
            and (group is None or L.group == group)]


# --- 1) no label overlaps (the structurally-closed regression) --------------------------------
def test_no_overlap_short_labels():
    assert _overlaps(zeitband_scene({"events": C0214_SHORT, "title": "Europa", "lupe": "off"})) == []


def test_no_overlap_sentence_labels_demote():
    # the c0213 regression: sentence labels demote to chips; the band stays legible
    assert _overlaps(zeitband_scene({"events": C0213_SENTENCES, "lupe": "off"})) == []
    assert _overlaps(zeitband_scene({"events": C0213_SENTENCES, "lupe": "auto"})) == []


def test_no_overlap_strands_and_lupe_dense():
    events = [{"at": y, "label": f"E{y}", "strand": "A" if y % 2 else "B"}
              for y in (1951, 1957, 1972, 1989, 1990, 1993, 1995, 1996, 1998, 2002, 2004, 2009)]
    spec = {"events": events, "strands": ["A", "B"], "lupe": "auto", "title": "Dicht"}
    assert _overlaps(zeitband_scene(spec)) == []


# --- 2) demotion → chip + exactly one legend line (►1) ----------------------------------------
def test_demotion_produces_chip_and_one_legend_line():
    long = "Ein wirklich viel zu langer Ereignistitel, der nicht auf die Achse passt"
    assert len(long) > zl.LABEL_BOUND
    spec = {"events": [{"at": 1900, "label": long}, {"at": 1950, "label": "Kurz"},
                       {"at": 2000, "label": "Auch kurz"}], "lupe": "off"}
    sc = zeitband_scene(spec)
    axis_chips = [L for L in sc.layers if isinstance(L, Node) and L.group == "labels"]
    legend_lines = _labels(sc, group="legend")
    assert len(axis_chips) == 1                                 # exactly the one long label demoted
    assert axis_chips[0].text == "1"                            # numbered chip
    assert len(legend_lines) == 1 and legend_lines[0].text == long   # legend = full original label


def test_short_labels_produce_no_legend():
    sc = zeitband_scene({"events": [{"at": 1900, "label": "Kurz"},
                                    {"at": 2000, "label": "Ebenso kurz"}], "lupe": "off"})
    assert _labels(sc, group="legend") == []
    assert [L for L in sc.layers if isinstance(L, Node) and L.group == "labels"] == []


# --- 3) spans render as bars; the printed year is "A–B" ---------------------------------------
def test_year_string_format():
    assert _year_str(1494, None) == "1494"
    assert _year_str(1884, 1885) == "1884–85"                   # short end within the century
    assert _year_str(1904, 1908) == "1904–08"
    assert _year_str(1898, 1902) == "1898–1902"                 # crosses a century → full end


def test_span_renders_as_bar_not_dot():
    sc = zeitband_scene({"events": [{"at": 1884, "to": 1885, "label": "Berliner Konferenz"},
                                    {"at": 1900, "label": "Punkt"}], "lupe": "off"})
    bars = [L for L in sc.layers if isinstance(L, Line) and L.group == "marks"
            and L.p == (1884.0, 0.0) and L.q == (1885.0, 0.0)]
    assert len(bars) == 1                                       # the Zeitraum is a bar
    # no dot marks the span (the bar IS the mark); the point event keeps its dot
    dots_at_span = [L for L in sc.layers if isinstance(L, PointMark) and abs(L.p[0] - 1884.5) < 1]
    assert dots_at_span == []
    assert any(isinstance(L, PointMark) and L.p == (1900.0, 0.0) for L in sc.layers)
    assert any(isinstance(L, Label) and L.text == "1884–85" for L in sc.layers)


# --- 4) strand validation (ingest gate) + geometric above/below placement (►2, ►6) ------------
def _sv(**kw):
    from teachersaid.schema.sachverhalt import Sachverhalt
    base = dict(id="sv-t", subject="Geschichte und politische Bildung", klasse_range=(3, 4),
                topic="Test")
    base.update(kw)
    return Sachverhalt(**base)


def _lint(sv):
    from teachersaid.pipeline.sachverhalt_lint import lint
    return lint(sv)


def test_strand_validation_hard_at_gate():
    from teachersaid.schema.sachverhalt import HistEvent
    # a valid 2-strand module passes (no strand problems)
    ok = _sv(timeline_strands=["Reich", "Land"],
             timeline=[HistEvent(at=1866, label="a", strand="Reich"),
                       HistEvent(at=1871, label="b", strand="Land")])
    assert _lint(ok)[0] == [], _lint(ok)[0]
    # an unassigned dated event → hard problem
    unassigned = _sv(timeline_strands=["Reich", "Land"],
                     timeline=[HistEvent(at=1866, label="a", strand="Reich"),
                               HistEvent(at=1871, label="b")])
    assert any("fehlt eine Bahn" in p for p in _lint(unassigned)[0])
    # an undeclared strand → hard problem
    undeclared = _sv(timeline_strands=["Reich", "Land"],
                     timeline=[HistEvent(at=1866, label="a", strand="Fremd")])
    assert any("keine der deklarierten" in p for p in _lint(undeclared)[0])
    # a strand on an event with no declared strands → hard problem
    orphan = _sv(timeline=[HistEvent(at=1866, label="a", strand="X")])
    assert any("keine der deklarierten" in p for p in _lint(orphan)[0])
    # exactly two strands required
    one = _sv(timeline_strands=["Nur eine"], timeline=[HistEvent(at=1866, label="a", strand="Nur eine")])
    assert any("genau ZWEI" in p for p in _lint(one)[0])


def test_over_long_label_is_advisory_only():
    from teachersaid.schema.sachverhalt import HistEvent
    long = "Dieser kuratierte Ereignistitel ist bewusst deutlich zu lang für die Achse"
    sv = _sv(timeline=[HistEvent(at=1900, label=long), HistEvent(at=1950, label="kurz")])
    problems, warnings = _lint(sv)
    assert problems == []                                       # advisory, never blocks ingest
    assert any("Zeichen" in w and "1900" in w for w in warnings)


def test_strands_place_above_and_below():
    spec = {"strands": ["Oben", "Unten"],
            "events": [{"at": 1900, "label": "AA", "strand": "Oben"},
                       {"at": 1950, "label": "BB", "strand": "Unten"}], "lupe": "off"}
    sc = zeitband_scene(spec)
    y = {L.text: L.p[1] for L in sc.layers if isinstance(L, Label) and L.text in ("1900", "1950")}
    assert y["1900"] > 0 and y["1950"] < 0                      # strand[0] above the axis, [1] below


# --- 5) Lupe trigger determinism (►3) ---------------------------------------------------------
def test_lupe_fires_on_cluster_deterministically():
    evs = zl._parse_events({"events": C0213_SENTENCES})
    assert zl._lupe_window(evs, {"lupe": "auto"}) == (1840, 1920)      # deterministic window


def test_lupe_does_not_fire_on_even_spread():
    evs = zl._parse_events({"events": [{"at": y, "label": f"E{y}"} for y in range(1900, 2001, 20)]})
    assert zl._lupe_window(evs, {"lupe": "auto"}) is None


def test_lupe_off_suppresses():
    evs = zl._parse_events({"events": C0213_SENTENCES})
    assert zl._lupe_window(evs, {"lupe": "off"}) is None
    # and the rendered scene has no Lupe window group when suppressed
    sc = zeitband_scene({"events": C0213_SENTENCES, "lupe": "off"})
    assert not any(getattr(L, "group", None) == "lupe" for L in sc.layers)
    sc_auto = zeitband_scene({"events": C0213_SENTENCES, "lupe": "auto"})
    assert any(getattr(L, "group", None) == "lupe" for L in sc_auto.layers)


# --- 6) Arbeitsobjekt: two projections of ONE computed layout (►4) ----------------------------
def test_arbeitsobjekt_masks_names_solved_shows_them():
    spec = {"events": C0214_SHORT, "title": "Europa", "lupe": "off"}
    names = {e["label"] for e in C0214_SHORT}
    years = {str(e["at"]) for e in C0214_SHORT}

    solved = zeitband_scene(spec)
    # the solved band shows the names (Stichwörter, wrapped to keep the block narrow → collapse \n)
    solved_texts = {L.text.replace("\n", " ") for L in solved.layers if isinstance(L, Label)}
    assert names <= solved_texts

    arb = zeitband_scene({**spec, "variant": "arbeitsobjekt"})
    # the axis side carries YEAR CHIPS (Node), not name labels
    chips = {L.text for L in arb.layers if isinstance(L, Node) and L.group == "chips"}
    assert chips == years
    # event names live ONLY in the bank — never as a label anywhere off the bank
    non_bank_names = [L.text for L in arb.layers if isinstance(L, Label)
                      and L.group != "bank" and L.text in names]
    assert non_bank_names == []
    bank_names = {L.text for L in arb.layers if isinstance(L, Label) and L.group == "bank"}
    assert names <= bank_names
    # ONE computed layout: the years the chips carry are exactly the solved band's event years
    assert chips == {L.text for L in solved.layers if isinstance(L, Label) and L.text in years}


# --- 7) chart_choose maps the timeline intent to the Zeitband ---------------------------------
def test_chart_choose_timeline_maps_to_zeitband():
    from teachersaid.schema.chart_choose import choose_representation
    gen, spec = choose_representation("timeline", {"events": [{"at": 1900, "label": "x"}]})
    assert gen == "matplotlib:zeitband"
    assert spec["events"] == [{"at": 1900, "label": "x"}]


# --- 8) the legacy matplotlib:timeline recipe stays alive beside the Zeitband ------------------
def test_legacy_timeline_and_zeitband_coexist(tmp_path):
    from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
    from teachersaid.schema.assets import Asset
    assert {"matplotlib:timeline", "matplotlib:zeitband"} <= set(GENERATION_RECIPES)
    events = [{"at": 1918, "label": "Republik"}, {"at": 1955, "label": "Staatsvertrag"}]
    for gen in ("matplotlib:timeline", "matplotlib:zeitband"):
        p = build_asset(Asset(id=gen.split(":")[1], role="figure", generator=gen,
                              spec={"events": events, "title": "AT"}), outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1500


def test_zeitband_asset_renders_via_registry(tmp_path):
    from teachersaid.pipeline.assets import build_asset
    from teachersaid.schema.assets import Asset
    for spec in ({"events": C0214_SHORT, "lupe": "off"},
                 {"events": C0213_SENTENCES, "lupe": "auto"},
                 {"events": C0214_SHORT, "variant": "arbeitsobjekt"}):
        p = build_asset(Asset(id="z", role="figure", generator="matplotlib:zeitband", spec=spec),
                        outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 2000


# --- inch-true layout (one data-y unit == one inch) -------------------------------------------
def test_layout_is_inch_true():
    sc = zeitband_scene({"events": C0214_SHORT, "title": "Europa", "lupe": "off"})
    y0, y1 = sc.canvas.ylim
    assert sc.canvas.figsize[1] == pytest.approx(y1 - y0, abs=1e-6)


# --- the derivation passes strands + phases through to the Zeitband spec -----------------------
def test_sachverhalt_derivation_emits_zeitband_with_strands_and_phases(tmp_path):
    from teachersaid.library.sachverhalt_wiener_kongress import build_sachverhalt
    from teachersaid.pipeline.assets import build_asset
    from teachersaid.pipeline.sachverhalt import build_worksheet
    from teachersaid.schema.sachverhalt import TimelinePhase

    sv = build_sachverhalt().model_copy(deep=True, update={
        "timeline_strands": ["Reich", "Länder"],
        "timeline_phases": [TimelinePhase(from_=1806, to=1815, label="Napoleonische Kriege")]})
    for e in sv.timeline:
        e.strand = "Reich"
    content, _res = build_worksheet(sv)
    zb = next(a for a in content.assets if a.generator == "matplotlib:zeitband")
    assert zb.spec["strands"] == ["Reich", "Länder"]
    assert zb.spec["phases"][0] == {"from": 1806, "to": 1815, "label": "Napoleonische Kriege"}
    assert zb.spec["lupe"] == "auto"
    assert build_asset(zb, outdir=tmp_path).read_bytes()[:8] == PNG      # it renders
