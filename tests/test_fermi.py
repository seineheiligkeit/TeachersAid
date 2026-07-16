"""Offline tests for the Fermi-Werkstatt (estimation / decomposition-chain modelling).

Covers the whole seam: the curated anchors + problems (`grounding/fermi.py`), the computed
chain / point estimate / propagated acceptable range (`pipeline/fermi.py`), and the honest
projection split (the student/homework sheet leaks neither the point estimate, nor the range,
nor the to-be-estimated anchor quantities; the teacher guide carries all three).

The SME-critical parts: every anchor carries provenance and honest bounds, the dataset-backed
anchors are locked against the live dataset (anti-rot), the chain arithmetic reproduces the
point estimate exactly, and the range propagation is correct + monotone (wider anchor bands ⇒
wider range).
"""

from __future__ import annotations

import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import fitz
import pytest

from teachersaid.grounding import data_store
from teachersaid.grounding import fermi as gf
from teachersaid.pipeline import fermi as pf
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.verify import verify
from teachersaid.rendering._document import build_pdf
from teachersaid.schema.fermi import (
    ChainStep,
    FermiAnchor,
    FermiEstimate,
    FermiProblem,
)

TODAY = date(2026, 7, 16)
PROBLEM_IDS = [p.id for p in gf.list_problems()]


# --- reference evaluator (independent cross-check of the chain + interval) ---
def _ref_eval(problem: FermiProblem, anchors) -> tuple[Decimal, Decimal, Decimal]:
    pt = lo = hi = Decimal(1)
    for s in problem.chain:
        a = anchors[s.anchor_id]
        if s.op == "multiply":
            pt *= a.value; lo *= a.low; hi *= a.high
        elif s.op == "divide":
            pt /= a.value; lo, hi = lo / a.high, hi / a.low
        elif s.op == "add":
            pt += a.value; lo += a.low; hi += a.high
    return pt, lo, hi


# --- 1. anchor invariants (SME-critical: bounds + provenance) ---------------
def test_every_anchor_has_ordered_positive_bounds():
    for a in gf.ANCHORS.values():
        assert a.low <= a.value <= a.high, a.id
        assert a.low > 0, a.id


def test_every_anchor_carries_provenance():
    for a in gf.ANCHORS.values():
        p = a.provenance
        assert p.kind in ("dataset", "cited", "estimate"), a.id
        if p.kind == "estimate":
            assert p.rationale.strip(), f"{a.id}: vetted estimate needs a rationale"
        elif p.kind == "cited":
            assert p.source.attribution.strip(), a.id
        elif p.kind == "dataset":
            assert data_store.get_dataset(p.dataset_id) is not None, \
                f"{a.id}: dataset '{p.dataset_id}' missing"


def test_exact_conversions_have_zero_width():
    for aid in ("minuten_pro_tag", "tage_pro_jahr", "schultage_woche"):
        a = gf.get_anchor(aid)
        assert a.is_exact() and a.low == a.value == a.high


# --- 2. dataset-backed anchors locked against the live dataset (anti-rot) ---
def test_wien_population_matches_dataset():
    ds = data_store.get_dataset("statistik_austria_bundeslaender_2024")
    s = ds.series["bevoelkerung"]
    wien = Decimal(str(s["counts"][s["groups"].index("Wien")]))
    assert gf.get_anchor("einwohner_wien").value == wien


def test_life_expectancy_within_cited_dataset_band():
    ds = data_store.get_dataset("statistik_austria_lebenserwartung_2002_2024")
    m, w = (Decimal(str(v)) for v in ds.series["vergleich_aktuell"]["values"])
    a = gf.get_anchor("lebenserwartung_at")
    # the anchor value is the rounded mean of the cited m/w figures; the band covers both
    assert m <= a.value <= w
    assert a.low <= m and a.high >= w


# --- 3. chain arithmetic reproduces the point estimate ----------------------
def test_point_estimate_matches_independent_recompute():
    for p in gf.list_problems():
        sol = pf.evaluate_chain(p)
        pt, lo, hi = _ref_eval(p, gf.ANCHORS)
        assert sol.point == pt, p.id
        assert (sol.low, sol.high) == (lo, hi), p.id


def test_heartbeats_hand_computed():
    """70/min · 1440 min/day · 365 day/yr · 82 yr — an exact integer product."""
    sol = pf.evaluate_chain(gf.get_problem("herzschlaege_leben"))
    assert sol.point == Decimal(70 * 1440 * 365 * 82) == Decimal("3016944000")
    # propagated interval endpoints are also exact (puls 60–90, life expectancy 79–85)
    assert sol.low == Decimal(60 * 1440 * 365 * 79)
    assert sol.high == Decimal(90 * 1440 * 365 * 85)


def test_piano_tuners_in_the_expected_tens():
    sol = pf.evaluate_chain(gf.get_problem("klavierstimmer_wien"))
    assert 10 <= float(sol.point) <= 60          # the classic "a few dozen"
    assert sol.low < sol.point < sol.high


# --- 4. range propagation is correct + monotone -----------------------------
def test_point_estimate_lies_inside_propagated_range():
    for p in gf.list_problems():
        sol = pf.evaluate_chain(p)
        assert sol.low <= sol.point <= sol.high, p.id


def test_wider_anchor_band_widens_the_range_monotonically():
    p = gf.get_problem("schulwasser")
    base = pf.evaluate_chain(p)
    # widen exactly one participating anchor's band (value unchanged)
    widened = dict(gf.ANCHORS)
    a = widened["wasser_pro_person_schultag"]
    widened["wasser_pro_person_schultag"] = a.model_copy(
        update={"low": Decimal("5"), "high": Decimal("40")})
    wide = pf.evaluate_chain(p, anchors=widened)
    assert wide.point == base.point               # only bounds moved
    assert wide.low < base.low                     # strictly wider (anchor participates)
    assert wide.high > base.high


def test_exact_only_chain_has_zero_width_from_conversions():
    """An exact anchor (low==high) contributes no width — narrowing intuition check."""
    # herzschlaege: only the puls is uncertain; the three conversions add no width beyond it
    sol = pf.evaluate_chain(gf.get_problem("herzschlaege_leben"))
    puls = gf.get_anchor("puls_ruhe")
    leb = gf.get_anchor("lebenserwartung_at")
    # width comes only from the two uncertain anchors (puls, life expectancy); the minute/day
    # and day/year factors are exact (low==high) and add none.
    assert sol.low == puls.low * Decimal(1440 * 365) * leb.low
    assert sol.high == puls.high * Decimal(1440 * 365) * leb.high


# --- 5. schema guards --------------------------------------------------------
def test_anchor_rejects_unordered_bounds():
    with pytest.raises(ValueError):
        FermiAnchor(id="x", label="x", value=Decimal("5"), low=Decimal("6"),
                    high=Decimal("10"), provenance=FermiEstimate(rationale="r"))


def test_problem_first_step_must_be_multiply():
    with pytest.raises(ValueError):
        FermiProblem(id="x", title="x", question="q?",
                     chain=[ChainStep(anchor_id="a", op="divide")])


def test_all_chain_anchor_ids_resolve():
    for p in gf.list_problems():
        for s in p.chain:
            assert s.anchor_id in gf.ANCHORS, f"{p.id}: {s.anchor_id}"


# --- 6. assemble → verify → render (all clean) ------------------------------
@pytest.mark.parametrize("pid", PROBLEM_IDS)
def test_worksheet_verifies_clean_and_renders(pid, tmp_path):
    content, res = pf.build_worksheet(pid, today=TODAY)
    assemble(content, res)
    report = verify(content, res)
    assert report.problems == [], report.problems      # advisory warnings allowed
    for proj in ("student", "teacher", "homework"):
        out = build_pdf(content, proj, tmp_path / f"{pid}-{proj}.pdf")
        assert out.exists() and out.stat().st_size > 0


# --- 7. honest anchoring (verbatim MAT competence, MOD dimension) -----------
@pytest.mark.parametrize("pid", PROBLEM_IDS)
def test_anchored_to_verbatim_mat_competence(pid):
    p = gf.get_problem(pid)
    content, res = pf.build_worksheet(pid, today=TODAY)
    assemble(content, res)
    assert content.anchor_mode == "competence"
    served = {s.competence_id for b in content.iter_blocks() for s in getattr(b, "serves", [])}
    assert served == {p.competence_id}
    assert p.competence_id in {c.id for c in res.competences}    # exists in the resolution
    dims = {d for b in content.iter_blocks() for d in getattr(b, "dimensions", [])}
    assert dims == {"MOD"}                                        # Modellieren und Problemlösen
    kinds = {b.kind for b in content.iter_blocks() if b.role.value == "task"}
    assert "modelling_task" in kinds


# --- 8. the leak guard: student/homework hide, teacher shows ----------------
def _pdf_text(content, proj: str, tmp: Path) -> str:
    out = build_pdf(content, proj, tmp / f"{proj}.pdf")
    doc = fitz.open(out)
    text = " ".join(pg.get_text() for pg in doc)
    doc.close()
    return " ".join(text.split())                    # normalise whitespace (undo line wraps)


@pytest.mark.parametrize("pid", PROBLEM_IDS)
def test_student_and_homework_do_not_leak_estimate_range_or_hidden_anchors(pid):
    p = gf.get_problem(pid)
    content, res = pf.build_worksheet(pid, today=TODAY)
    assemble(content, res)
    sol = pf.evaluate_chain(p)
    point = sol.point_str(p.sig)
    lo = pf.human_de(sol.low, sol.unit, sig=p.sig)
    hi = pf.human_de(sol.high, sol.unit, sig=p.sig)
    hidden_labels = [gf.get_anchor(a).label for a in p.estimated_ids()]
    secrets = [point, lo, hi] + hidden_labels

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        teacher = _pdf_text(content, "teacher", tmp)
        student = _pdf_text(content, "student", tmp)
        homework = _pdf_text(content, "homework", tmp)

    # teacher carries the point estimate, the range AND every to-be-estimated quantity
    for s in secrets:
        assert s in teacher, f"{pid}: teacher missing {s!r}"
    # neither student-facing projection leaks any of them
    for proj_name, txt in (("student", student), ("homework", homework)):
        for s in secrets:
            assert s not in txt, f"{pid}: {proj_name} LEAKED {s!r}"


@pytest.mark.parametrize("pid", PROBLEM_IDS)
def test_given_anchors_are_shown_on_the_student_sheet(pid):
    """The given/estimated split: given facts DO appear student-facing (their labels)."""
    p = gf.get_problem(pid)
    given_ids = p.given_ids()
    if not given_ids:
        pytest.skip("no given anchors for this problem")
    content, res = pf.build_worksheet(pid, today=TODAY)
    assemble(content, res)
    with tempfile.TemporaryDirectory() as d:
        student = _pdf_text(content, "student", Path(d))
    for aid in given_ids:
        assert gf.get_anchor(aid).label in student, f"{pid}: given {aid} not shown"


# --- 9. seed function is importable (NOT executed — no store side effects) ---
def test_seed_function_importable():
    from teachersaid.library import seed_fermi
    assert callable(seed_fermi)
