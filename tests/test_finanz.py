"""Offline tests for the Finanzführerschein pack.

Covers the whole seam: the curated legal tables (`grounding/finanz.py`), the three shared-
registry recipes + the anchor-honest worksheet builder (`pipeline/finanz.py`), and the VPI
fetch parser (`tools/fetch_statistik_austria_vpi.py`, exercised on a fixture — no network).

The legal-table ground truths are the SME-critical part: the hand-computed net wages for
fixed gross inputs MUST be exact (a wrong bracket bound or SV rate surfaces here). They were
verified 2026-07 against the published Lohnsteuertarif 2026 + the ASVG Angestellte DN-Anteil.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest

from teachersaid.grounding import finanz as gf
from teachersaid.pipeline import finanz as pf
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.parametrize import instantiate, make_variants
from teachersaid.pipeline.verify import verify
from teachersaid.library.templates import find_template
from teachersaid.rendering._document import build_pdf
from tools import fetch_statistik_austria_vpi as vpi

TODAY = date(2026, 7, 11)
SHEETS = ("lohnzettel", "inflation", "handyvertrag")
SHEETS_TEMPLATES = ("fin-lohnzettel", "fin-inflation", "fin-handyvertrag")


def _first_euro(text: str) -> Decimal:
    """The first '2.400,00 €' amount in a string → Decimal('2400.00')."""
    m = re.search(r"([\d.]+),(\d{2}) €", text)
    assert m, f"no euro amount in {text!r}"
    return Decimal(m.group(1).replace(".", "") + "." + m.group(2))


# --- 1. legal-table ground truths (SME-critical: these MUST be exact) --------
@pytest.mark.parametrize("brutto,sv,bemess_y,lst_y,lst_m,netto", [
    # 20 %-Stufe (band 1)
    (1500, "271.05", "14747.40", "241.68", "20.14", "1208.81"),
    # 30 %-Stufe (band 2)
    (3000, "542.10", "29494.80", "3941.44", "328.45", "2129.45"),
    # 40 %-Stufe (band 3)
    (4500, "813.15", "44242.20", "9144.08", "762.01", "2924.84"),
])
def test_lohnzettel_ground_truth(brutto, sv, bemess_y, lst_y, lst_m, netto):
    c = pf._lohn_chain(Decimal(brutto))
    assert c["sv_m"] == Decimal(sv)
    assert c["bemess_year"] == Decimal(bemess_y)
    assert c["lst_year"] == Decimal(lst_y)
    assert c["lst_m"] == Decimal(lst_m)
    assert c["netto_m"] == Decimal(netto)


def test_tarif_reproduces_published_cumulative_amounts():
    """The 2026 tariff must hit the published cumulative tax at every bracket start."""
    for bemess, cum in [("21992", "1690.60"), ("36458", "6030.40"), ("70365", "19593.20"),
                        ("104859", "36150.32"), ("1000000", "483720.82")]:
        assert gf.lohnsteuer_jahr(Decimal(bemess)) == Decimal(cum)


def test_grundstufe_is_tax_free():
    assert gf.lohnsteuer_jahr(Decimal("13539")) == Decimal("0.00")
    assert gf.lohnsteuer_jahr(Decimal("9000")) == Decimal("0.00")


def test_sv_components_sum_to_published_rate():
    assert gf.SV_DIENSTNEHMER_RATE_2026 == Decimal("0.1807")
    assert sum(gf.SV_COMPONENTS_2026.values()) == gf.SV_DIENSTNEHMER_RATE_2026


def test_sv_capped_at_hoechstbeitragsgrundlage():
    cap = gf.SV_HOECHSTBEITRAGSGRUNDLAGE_MONAT_2026
    capped = gf.sv_dienstnehmer(Decimal("10000"), cap=cap)
    assert capped == gf._cent(cap * gf.SV_DIENSTNEHMER_RATE_2026)
    # below the cap the base is the full gross
    assert gf.sv_dienstnehmer(Decimal("3000"), cap=cap) == Decimal("542.10")


def test_euro_formatting_austrian_convention():
    assert gf.euro(Decimal("2129.45")) == "2.129,45 €"
    assert gf.euro(Decimal("542.1")) == "542,10 €"
    assert gf.euro(Decimal("1000000")) == "1.000.000,00 €"
    assert gf.prozent(gf.SV_DIENSTNEHMER_RATE_2026) == "18,07 %"


# --- 2. VPI parser fixture (offline; no network) ----------------------------
VPI_FIXTURE = "\n".join([
    "C-VPIZR-0;C-VPI1-0;F-VPIMZBM",
    "VPIZR-199501;VPI-0;347,90000",   # a MONTHLY code → must be ignored
    "VPIZR-1995;VPI-0;350,20000",     # annual average, Gesamtindex → kept
    "VPIZR-2024;VPI-0;673,90000",
    "VPIZR-2024;VPI-1;12,34000",      # a different index classification → ignored
    "VPIZR-2025;VPI-0;697,60000",
])


def test_vpi_parser_keeps_only_annual_gesamtindex():
    assert vpi.parse_annual_index(VPI_FIXTURE) == {1995: 350.2, 2024: 673.9, 2025: 697.6}


def test_vpi_parser_raises_on_empty_result():
    with pytest.raises(SystemExit):
        vpi.parse_annual_index("C-VPIZR-0;C-VPI1-0;F-VPIMZBM\nVPIZR-202401;VPI-0;1,0")


def test_vpi_dataset_committed_and_loads():
    """The recipe depends on the committed dataset (offline) — it must be present + real."""
    from teachersaid.grounding import data_store as ds
    d = ds.get_dataset(pf.VPI_DATASET_ID)
    assert d is not None and "CC BY 4.0" in (d.source.licence or "")
    idx = dict(zip(d.series["jahresindex"]["years"], d.series["jahresindex"]["index"]))
    assert idx[1995] == 350.2 and idx[2024] == 673.9   # real Statistik-Austria values


# --- 3. recipe determinism + distinctness -----------------------------------
def test_recipes_deterministic_per_seed():
    for tid in ("fin-lohnzettel", "fin-inflation", "fin-handyvertrag"):
        t = find_template(tid)
        a, b = instantiate(t, 7), instantiate(t, 7)
        assert str(a.prompt) == str(b.prompt) and str(a.answer_key) == str(b.answer_key)


def test_recipes_produce_distinct_variants():
    for tid in SHEETS_TEMPLATES:
        prompts = {str(b.prompt) for b in make_variants(find_template(tid), 6)}
        assert len(prompts) >= 4, tid


def test_lohnzettel_ramp_spans_all_bands():
    blocks = make_variants(find_template("fin-lohnzettel"), 6, ramp=True)
    assert {b.difficulty for b in blocks} == {1, 2, 3}


def test_lohnzettel_recipe_matches_ground_truth_chain():
    """The recipe's answer must equal the pure Brutto→Netto chain for its own drawn gross."""
    for seed in range(20):
        blk = instantiate(find_template("fin-lohnzettel"), seed)
        c = pf._lohn_chain(_first_euro(str(blk.prompt)))
        assert gf.euro(c["netto_m"]) in str(blk.answer_key)


# --- 4. tariff internal consistency (Realien discipline) --------------------
def test_handyvertrag_answer_derivable_from_shown_tariffs():
    """Internal consistency: the recommended total is the minimum recomputed straight from
    the tariff data SHOWN in the task prompt (Grundgebühr·24 + Aktivierung)."""
    tarif_re = re.compile(
        r"(Tarif \w+): (\d+) €/Monat, \d+ GB, (?:(\d+) € Aktivierung|keine Aktivierungskosten)")
    for seed in range(30):
        blk = instantiate(find_template("fin-handyvertrag"), seed)
        prompt, answer = str(blk.prompt), str(blk.answer_key)
        tarife = tarif_re.findall(prompt)
        assert len(tarife) >= 2
        totals = {name: int(g) * 24 + (int(a) if a else 0) for name, g, a in tarife}
        best_name = min(totals, key=totals.get)
        assert best_name in answer                      # recommends the true cheapest
        assert gf.euro(Decimal(totals[best_name])) in answer   # with its exact total
        assert len(set(totals.values())) == len(totals)        # unique cheapest guaranteed


def test_handyvertrag_no_real_provider_names():
    text = " ".join(str(instantiate(find_template("fin-handyvertrag"), s).prompt)
                    for s in range(15))
    for brand in ("A1", "Magenta", "Drei", "Yesss", "Spusu", "HoT", "Bob"):
        assert brand not in text


# --- 5. full assemble → verify → render -------------------------------------
@pytest.mark.parametrize("sid", SHEETS)
def test_sheet_verifies_clean_and_renders(sid, tmp_path):
    content, res = pf.build_worksheet(sid, today=TODAY)
    assemble(content, res)
    report = verify(content, res)
    assert report.problems == [], report.problems          # advisory warnings are allowed
    for proj in ("student", "teacher", "homework"):
        out = build_pdf(content, proj, tmp_path / f"{sid}-{proj}.pdf")
        assert out.exists() and out.stat().st_size > 0


# --- 6. honest anchoring -----------------------------------------------------
def test_lohnzettel_anchored_uet_13_no_false_competence_claim():
    content, res = pf.build_worksheet("lohnzettel", today=TODAY)
    assemble(content, res)
    assert content.anchor_mode == "uet" and content.anchor_uet == 13
    nw = content.nachweis
    assert nw.anchor_mode == "uet" and "13" in nw.anchor_label
    assert nw.gaps == []                                    # ÜT makes no completeness/gap claim
    assert all(not getattr(b, "serves", []) for b in content.iter_blocks())


def test_inflation_anchored_ent09_competence():
    content, res = pf.build_worksheet("inflation", today=TODAY)
    assemble(content, res)
    assert content.anchor_mode == "competence"
    served = {s.competence_id for b in content.iter_blocks() for s in getattr(b, "serves", [])}
    assert served == {"GWB.US.3.ENT.09"}


def test_handyvertrag_anchored_ent04_competence():
    content, res = pf.build_worksheet("handyvertrag", today=TODAY)
    served = {s.competence_id for b in content.iter_blocks() for s in getattr(b, "serves", [])}
    assert served == {"GWB.US.3.ENT.04"}


def test_didactic_simplification_stated_on_sheet():
    content, _ = pf.build_worksheet("lohnzettel", today=TODAY)
    intro = " ".join(str(getattr(b, "content", "")) for b in content.intro)
    assert "18,07" in intro                     # the SV rate is disclosed
    assert "13.539" in intro                    # the tax-free Grundstufe
    assert "13./14." in intro                   # the 13th/14th-salary exclusion is stated


def test_inflation_cites_statistik_austria_in_steps():
    content, _ = pf.build_worksheet("inflation", today=TODAY)
    steps = " ".join(s.text for b in content.iter_blocks()
                     for s in getattr(b, "solution_steps", []) or [])
    assert "Statistik Austria" in steps
