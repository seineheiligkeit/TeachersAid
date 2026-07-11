"""Wahl-Werkstatt — d'Hondt seat allocation + coalition arithmetic (GPB, Politische Bildung).

Locks the load-bearing guarantees:
* the seat allocation is COMPUTED (d'Hondt), verified against a HAND-computed ground truth
  (the divisor table is worked out in the comment) — and reproduces the official 2024 seats;
* coalition arithmetic is COMPUTED (exhaustive minimal-winning-coalition search), verified
  against a hand truth and the real 2024 Nationalrat;
* the fetch parser is fixture-tested offline; the licence check is fail-closed;
* variants are deterministic per seed and distinct; every worksheet assembles → verifies →
  RENDERS;
* honest anchoring (competence mode, real GPB competences) + the simplification note ON the
  sheet (never present the computed seats as the official Mandatsverteilung).
Everything offline (the dataset is committed; no network).
"""

from __future__ import annotations

from datetime import date

import pytest

from tools import fetch_nrw_results as fnr
from teachersaid.grounding import data_store as ds
from teachersaid.pipeline import wahl
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.parametrize import _RECIPES, instantiate, make_variants
from teachersaid.pipeline.verify import verify
from teachersaid.pipeline.wahl import find_wahl_template as find_template

IN_WINDOW = date(2026, 3, 1)
SAMPLED = ["gpb-wahl-mandate", "gpb-wahl-koalition"]
REAL = ["gpb-wahl-mandate-nrw", "gpb-wahl-koalition-nrw"]
ALL_TEMPLATES = SAMPLED + REAL


def _text(rt) -> str:
    if isinstance(rt, str):
        return rt
    return "".join(getattr(r, "text", "") for r in rt)


# =====================================================================================
# d'Hondt — HAND-computed ground truth
# =====================================================================================
def test_dhondt_hand_computed_ground_truth():
    """Votes A=100000, B=61000, C=39000, D=17000; 10 Mandate. Höchstzahlen (Stimmen ÷ k),
    the ten largest across all parties (worked by hand):
        1) 100000 A/1   2) 61000 B/1   3) 50000 A/2   4) 39000 C/1   5) 33333 A/3
        6) 30500 B/2    7) 25000 A/4   8) 20333 B/3   9) 20000 A/5  10) 19500 C/2
        (next: 17000 D/1)  → A=5, B=3, C=2, D=0."""
    votes = {"A": 100000, "B": 61000, "C": 39000, "D": 17000}
    alloc, ranked = wahl.dhondt(votes, 10)
    assert alloc == {"A": 5, "B": 3, "C": 2, "D": 0}
    assert sum(alloc.values()) == 10
    assert ranked[0][1] == "A"          # 1st seat
    assert ranked[3][1] == "C"          # 4th seat (C/1 = 39000)
    assert ranked[9][1] == "C"          # 10th (last) seat (C/2 = 19500)


def test_dhondt_totals_and_monotonicity():
    votes = {"X": 51000, "Y": 30000, "Z": 19000}
    for seats in range(1, 20):
        alloc, _ = wahl.dhondt(votes, seats)
        assert sum(alloc.values()) == seats           # every seat is awarded exactly once
    # the largest party never has fewer seats than a smaller one
    alloc, _ = wahl.dhondt(votes, 12)
    assert alloc["X"] >= alloc["Y"] >= alloc["Z"]


def test_votes_needed_for_next_seat_hand_check():
    """D (17000, 0 seats) needs to overtake the cut = 19500 (C/2). D's divisor is 1, so it
    needs > 19500 votes → 19501, i.e. 2501 more than 17000."""
    votes = {"A": 100000, "B": 61000, "C": 39000, "D": 17000}
    assert wahl.votes_needed_for_next_seat(votes, 10, "D") == 2501


# =====================================================================================
# coalition arithmetic — HAND truth + the real Nationalrat 2024
# =====================================================================================
def test_minimal_winning_coalitions_hand_truth():
    """Seats A=5,B=4,C=3,D=2 (14 total), majority 8. Winning pairs: A+B(9), A+C(8). The only
    other minimal winner is B+C+D(9) — winning, and losing if any member leaves. A+B+C etc.
    all contain a winning pair, so they are NOT minimal."""
    seats = {"A": 5, "B": 4, "C": 3, "D": 2}
    mwc = wahl.minimal_winning_coalitions(seats, 8)
    got = {frozenset(c) for c in mwc}
    assert got == {frozenset("AB"), frozenset("AC"), frozenset("BCD")}
    # every reported coalition is winning and truly minimal
    for c in mwc:
        assert sum(seats[p] for p in c) >= 8
        assert all(sum(seats[p] for p in c - {p}) < 8 for p in c)


def test_coalitions_real_nationalrat_2024():
    """The real 2024 Nationalrat (FPÖ57 ÖVP51 SPÖ41 NEOS18 GRÜNE16, majority 92) has exactly
    three minimal winning coalitions — the three pairs among the big three."""
    seats = {"FPÖ": 57, "ÖVP": 51, "SPÖ": 41, "NEOS": 18, "GRÜNE": 16}
    mwc = {frozenset(c) for c in wahl.minimal_winning_coalitions(seats, 92)}
    assert mwc == {frozenset({"FPÖ", "ÖVP"}), frozenset({"FPÖ", "SPÖ"}),
                   frozenset({"ÖVP", "SPÖ"})}
    # the actual ÖVP+SPÖ+NEOS government is winning but NOT minimal (ÖVP+SPÖ alone wins)
    assert sum(seats[p] for p in ("ÖVP", "SPÖ", "NEOS")) >= 92
    assert frozenset({"ÖVP", "SPÖ", "NEOS"}) not in mwc


# =====================================================================================
# the REAL cited slice — Nationalratswahl 2024 (BMI dataset, CC BY 4.0)
# =====================================================================================
def test_real_dhondt_reproduces_official_party_seat_totals():
    """Federal d'Hondt on the five parties over the 4-%-Hürde reproduces the official party
    seat totals (FPÖ57 ÖVP51 SPÖ41 NEOS18 GRÜNE16) — the didactic simplification's key fact."""
    votes, totals = wahl._nrw_bund_votes()
    alloc, _ = wahl.dhondt(votes, totals["mandate_gesamt"])
    assert alloc == totals["mandate_amtlich"]
    assert sum(alloc.values()) == 183


def test_four_percent_threshold_deviation_is_a_real_teaching_moment():
    """d'Hondt on ALL parties (ignoring the 4-%-Hürde) hands seats to sub-threshold parties
    (KPÖ, BIER) — the concrete deviation the 'warum weicht ab?' task rests on."""
    dataset = ds.get_dataset(wahl.NRW_DATASET)
    all_votes = dict(zip(dataset.series["bund"]["categories"], dataset.series["bund"]["values"]))
    nr = dataset.totals["nr_parteien"]
    alloc_all, _ = wahl.dhondt(all_votes, 183)
    intruders = {p: alloc_all[p] for p in all_votes if p not in nr and alloc_all[p] > 0}
    assert intruders, "without the threshold, sub-4% parties would win seats"
    assert {"KPÖ", "BIER"} <= set(intruders)          # both cleared d'Hondt but not the 4-%-Hürde


def test_dataset_licence_verdict_and_structure():
    """The BMI dataset is redistributable CC BY 4.0, with the curated official-seat totals."""
    src = ds.source_ref_for(wahl.NRW_DATASET)
    assert src.licence == "CC BY 4.0"
    assert src.licence_url == "https://creativecommons.org/licenses/by/4.0/"
    assert src.redistributable is True
    assert "BMI" in src.attribution and "data.gv.at" in src.attribution
    dataset = ds.get_dataset(wahl.NRW_DATASET)
    assert dataset.totals["mandate_amtlich"] == {"FPÖ": 57, "ÖVP": 51, "SPÖ": 41,
                                                 "NEOS": 18, "GRÜNE": 16}
    assert dataset.totals["mehrheit"] == 92
    assert "bund" in dataset.series and "bund_hauptparteien" in dataset.series


# =====================================================================================
# the fetch tool — offline parser fixture + fail-closed licence check
# =====================================================================================
_CSV_FIXTURE = (
    ";Gebietsname;Wahlberechtigte;Abgegebene;Ungültige;Gültige;ÖVP;SPÖ;FPÖ;GRÜNE;NEOS;"
    "BIER;MFG;BGE;LMP;GAZA;KPÖ;KEINE;\n"
    "G00000;Österreich;1000;900;10;890;300;200;250;60;50;20;5;1;2;1;1;0;\n"
    "G10000;Burgenland;100;90;1;89;30;25;20;5;4;2;;;;;2;1;\n"
    "G1A000;Burgenland Nord;50;45;0;45;15;12;10;3;2;1;;;;;1;1;\n"   # a Regionalwahlkreis — skipped
)


def test_fetch_parser_fixture_offline():
    parsed = fnr.parse_wahl_csv(_CSV_FIXTURE)
    assert set(parsed) == {"Österreich", "Burgenland"}            # only the Gxx000 aggregates
    bund = parsed["Österreich"]
    assert bund["gkz"] == "G00000" and bund["gueltige"] == 890
    assert bund["votes"]["ÖVP"] == 300 and bund["votes"]["FPÖ"] == 250
    # an empty cell (party not standing in the region) parses as 0
    assert parsed["Burgenland"]["votes"]["BGE"] == 0
    assert parsed["Burgenland"]["votes"]["KPÖ"] == 2


def test_fetch_build_dataset_shapes():
    parsed = fnr.parse_wahl_csv(_CSV_FIXTURE)
    d = fnr.build_dataset(parsed, retrieved="2026-07-11")
    assert d["id"] == "bmi_nrw_2024"
    assert d["source"]["licence"] == "CC BY 4.0" and d["source"]["redistributable"] is True
    assert d["series"]["bund"]["categories"] == fnr.PARTIES
    # bund_hauptparteien keeps only parties ≥ 2 % of valid votes (890 → ≥ 17.8)
    haupt = d["series"]["bund_hauptparteien"]["categories"]
    assert "ÖVP" in haupt and "FPÖ" in haupt and "BGE" not in haupt


def test_licence_check_is_fail_closed():
    assert fnr.verify_licence({"license": "https://creativecommons.org/licenses/by/4.0/"})
    assert fnr.verify_licence({"rights": "Creative Commons Attribution 4.0 International"})
    # ShareAlike / NonCommercial / missing → refuse (fail closed)
    assert not fnr.verify_licence({"license": "https://creativecommons.org/licenses/by-sa/4.0/"})
    assert not fnr.verify_licence({"license": "CC BY-NC 4.0"})
    assert not fnr.verify_licence({})


# =====================================================================================
# recipes — registration, determinism, distinctness, both real + sampled
# =====================================================================================
def test_recipes_registered():
    assert {"mandate_dhondt", "koalitions_arithmetik",
            "mandate_dhondt_nrw", "koalitions_nrw"} <= set(_RECIPES)


@pytest.mark.parametrize("tid", ALL_TEMPLATES)
def test_variants_deterministic_and_distinct(tid):
    t = find_template(tid)
    a = make_variants(t, 6, seed0=1)
    b = make_variants(t, 6, seed0=1)
    assert [_text(x.prompt) for x in a] == [_text(x.prompt) for x in b]     # deterministic
    assert len({_text(x.prompt) for x in a}) >= 4                           # distinct
    assert all(x.answer_key for x in a)                                     # every one answered


def test_sampled_and_real_both_supported():
    """The core recipe logic runs on clean sampled numbers AND on the real cited slice."""
    sampled = instantiate(find_template("gpb-wahl-mandate"), 3)
    assert _text(sampled.answer_key)                                        # computed answer
    real = instantiate(find_template("gpb-wahl-mandate-nrw"), 3)
    real_ans = _text(real.answer_key)
    # the real variant is the actual 2024 result (a party's real seat count)
    assert any(f"{p}" in real_ans for p in ("FPÖ", "ÖVP", "SPÖ", "NEOS", "GRÜNE"))


# =====================================================================================
# worksheets — honest anchoring, simplification note, assemble → verify → render
# =====================================================================================
def test_uebungsblatt_anchors_real_gpb_competence():
    content, res = wahl.wahl_uebungsblatt("gpb-wahl-mandate", 6, today=IN_WINDOW)
    content = assemble(content, res)
    assert verify(content, res).ok
    assert content.anchor_mode.value == "competence"
    cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
    assert cov.get("GPB.US.4.ALL.07") is True          # genuine politische Sachkompetenz


def test_nrw_showcase_covers_sach_and_urteil_and_cites_bmi():
    content, res = wahl.nrw_werkstatt_worksheet(today=IN_WINDOW)
    content = assemble(content, res)
    assert verify(content, res).ok
    cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
    assert cov.get("GPB.US.4.ALL.07") is True          # Sachkompetenz (Wahlsystem)
    assert cov.get("GPB.US.4.ALL.09") is True          # Urteilskompetenz (compare-and-discuss)
    # dimensional spread (not flat): HSA + PME + PUR
    dims = {d for b in content.sections[0].blocks for d in b.dimensions}
    assert {"HSA", "PME", "PUR"} <= dims
    # the real data carries the BMI citation via the figure's resolved data_source
    fig = next(a for a in content.assets if a.id == "nrw.stimmen")
    assert "BMI" in fig.data_source.citation() and "CC BY 4.0" in fig.data_source.citation()


def test_simplification_note_is_on_the_sheet_and_seats_not_claimed_official():
    """The didactic-simplification note is student-visible; the computed seats are never
    presented as the official Mandatsverteilung (the teacher watch-out says so)."""
    assert "dreistufig" in wahl.HONESTY_NOTE and "vereinfacht" in wahl.HONESTY_NOTE
    assert "nicht die amtliche Mandatsverteilung" in wahl.HONESTY_NOTE
    content, res = wahl.nrw_werkstatt_worksheet(today=IN_WINDOW)
    mandate = next(b for b in content.sections[0].blocks if b.id == "nrw.t1")
    assert any("amtliche Mandatsverteilung" in w for w in mandate.watch_outs)


def _render(content, res, tmp_path, name):
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    content = assemble(content, res)
    assets = {a.id: build_asset(a, outdir=tmp_path / "assets")
              for a in content.assets if a.generator}
    student = render_student_sheet(content, tmp_path / f"{name}_s.pdf", assets)
    teacher = render_teacher_guide(content, tmp_path / f"{name}_t.pdf", assets)
    assert student.stat().st_size > 1000 and teacher.stat().st_size > 1000
    return content, student, teacher


@pytest.mark.parametrize("tid", SAMPLED)
def test_uebungsblaetter_render(tid, tmp_path):
    content, res = wahl.wahl_uebungsblatt(tid, 4, today=IN_WINDOW)
    _render(content, res, tmp_path, tid)


def test_nrw_showcase_renders_with_figure_and_note(tmp_path):
    import fitz
    content, res = wahl.nrw_werkstatt_worksheet(today=IN_WINDOW)
    content, student, teacher = _render(content, res, tmp_path, "nrw")
    text = "\n".join(p.get_text() for p in fitz.open(student))
    assert "vereinfacht" in text and "dreistufig" in text     # honesty note on the student sheet
    assert "Quelle" in text and "BMI" in text                 # the cited real data
    # the figure image was embedded (student PDF is materially larger with the raster)
    assert student.stat().st_size > 40_000


def test_stage_wahl_werkstatt_stages_clean(tmp_path):
    from teachersaid.store.repository import ReviewStore
    store = ReviewStore(tmp_path / "store")
    items = wahl.stage_wahl_werkstatt(store, n=4, today=IN_WINDOW)
    assert len(items) == 3
    for it in items:
        assert it.error is None, (it.title, it.error)
        assert it.status == "pending"
        assert it.verify_problems == []
