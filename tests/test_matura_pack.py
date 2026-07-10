"""Matura-Nachfrage-Pack: exponential model (FA) + Boxplot & Baumdiagramm (WS).

The three highest-frequency SRDP demands from the corpus scan (Documents/matura-math-
coverage.md), each a correct-by-construction sympy recipe. This locks:
* the answer AND the worked Rechenweg are COMPUTED, verified here against independent
  ground truth (a hand-checked five-number summary; exact tree fractions; the recovered
  growth factor);
* `Unsuitable` rejects a degenerate draw and `make_variants` resamples;
* variants are deterministic per seed and distinct where the draw space allows;
* every template assembles + verifies + RENDERS (the render test is what catches the
  mathtext-subset slips assemble/verify can't — \\frac/\\cdot/\\sqrt/\\ln/\\mid/subscripts).
"""

from __future__ import annotations

import re
from datetime import date

import pytest
import sympy

from teachersaid.library.templates import find_template, variant_worksheet
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.parametrize import (
    Unsuitable, _RECIPES, _de_num, instantiate, make_variants,
)
from teachersaid.pipeline.verify import verify

IN_WINDOW = date(2026, 3, 1)
PACK_IDS = ["mat-fa-exponentialmodell", "mat-ws-boxplot", "mat-ws-baumdiagramm"]


def _text(rt) -> str:
    """Flatten a RichText (str | list[InlineRun]) to plain text."""
    if isinstance(rt, str):
        return rt
    return "".join(getattr(r, "text", "") for r in rt)


# --- registration + anchoring ------------------------------------------------
def test_recipes_registered():
    assert {"exponential_model", "boxplot_from_data", "probability_tree"} <= set(_RECIPES)


def test_templates_anchored_to_real_oberstufe_competences():
    served = {t: find_template(t).serves[0].competence_id for t in PACK_IDS}
    assert served == {
        "mat-fa-exponentialmodell": "MAT.OS.6.REE.10",   # Reelle Funktionen — Exponentialf. anwenden
        "mat-ws-boxplot": "MAT.OS.6.BES.01",             # beschreibende Statistik — Kennzahlen
        "mat-ws-baumdiagramm": "MAT.OS.6.BES.04",        # Baumdiagramme; Additions-/Multiplikationsregel
    }
    for tid in PACK_IDS:
        t = find_template(tid)
        assert t.klasse == 6 and t.subject == "Mathematik"
        assert t.dimensions == ["FO"]                    # ⊆ Oberstufe-MAT {DM,FO,ID,KA}
    # non-"mat-os-" ids: the locked test_oberstufe exact-set assertions stay green
    assert not any(tid.startswith("mat-os-") for tid in PACK_IDS)


# --- exponential model: correctness vs independent ground truth ---------------
def test_exponential_rate_recovers_the_factor_exactly():
    """The find-the-rate variant is correct by construction: N1 = N0·q² is a whole number
    and q = √(N1/N0) recovers exactly. Re-derive q independently and check the answer."""
    seen = 0
    for seed in range(60):
        blk = instantiate(find_template("mat-fa-exponentialmodell"), seed)
        prompt, answer = _text(blk.prompt), _text(blk.answer_key)
        if "Bestimme den Faktor q" not in prompt:
            continue
        seen += 1
        n0, n1 = (int(x) for x in re.search(
            r"beträgt er (\d+), nach 2 Zeiteinheiten (\d+)", prompt).groups())
        q = sympy.sqrt(sympy.Rational(n1, n0))
        assert q.is_rational, (seed, n0, n1)          # a clean recovery, not a surd
        assert f"q = {_de_num(float(q))}" in answer, (seed, answer)
    assert seen >= 3


def test_exponential_evaluate_and_time_match_recomputation():
    """The evaluate and doubling/half-life variants: re-run the maths independently from
    the numbers the Rechenweg states and confirm the answer."""
    got_wert = got_zeit = 0
    for seed in range(60):
        blk = instantiate(find_template("mat-fa-exponentialmodell"), seed)
        answer = _text(blk.answer_key)
        steps = [(_text(s.text), s.expr or "") for s in blk.solution_steps]
        joined = " ".join(t for t, _ in steps)
        if answer.startswith("N("):                    # evaluate N(t)
            got_wert += 1
            t, n0 = (int(x) for x in re.search(
                r"N\((\d+)\) = (\d+)", steps[0][1]).groups())
            q = float(re.search(r"mit q = ([\d,]+)", joined).group(1).replace(",", "."))
            reported = int(re.search(r"≈ (\d+)", answer).group(1))
            assert abs(reported - n0 * q ** t) < 1.0, (seed, reported, n0, q, t)
        elif "halbiert" in answer or "verdoppelt" in answer:   # solve t via log
            got_zeit += 1
            k, q = (float(x.replace(",", ".")) for x in re.search(
                r"k = ([\d,]+), q = ([\d,]+)", joined).groups())
            t_reported = float(re.search(r"t ≈ ([\d,]+)", answer).group(1).replace(",", "."))
            t_true = float(sympy.log(sympy.Rational(str(k))) / sympy.log(sympy.Rational(str(q))))
            assert abs(t_reported - round(t_true, 1)) < 0.05, (seed, t_reported, t_true)
    assert got_wert >= 3 and got_zeit >= 3


# --- boxplot: the five-number summary (ground truth) -------------------------
def _summary_from_ordered(vals):
    """Independent five-number summary with the recipe's school convention (Q = median of
    each half, excluding the overall median; halves are odd-length so quartiles are single
    values)."""
    n = len(vals)
    half = n // 2
    lower, upper = vals[:half], vals[half + 1:]
    return (vals[0], lower[len(lower) // 2], vals[half],
            upper[len(upper) // 2], vals[-1])


def test_boxplot_summary_matches_independent_computation():
    for seed in range(40):
        blk = instantiate(find_template("mat-ws-boxplot"), seed)
        answer = _text(blk.answer_key)
        ordered = [int(x) for x in re.search(
            r"ordnen: ([\d, ]+)", _text(blk.solution_steps[0].text)).group(1).split(",")]
        assert ordered == sorted(ordered)             # the recipe really ordered them
        mn, q1, med, q3, mx = _summary_from_ordered(ordered)
        assert (f"Minimum = {mn}, Q₁ = {q1}, Median = {med}, Q₃ = {q3}, "
                f"Maximum = {mx}") in answer, (seed, answer)
        assert f"Spannweite = {mx - mn}" in answer
        assert f"Interquartilsabstand = {q3 - q1}" in answer


def test_boxplot_fixed_seed_ground_truth():
    """A hand-computed summary (n=11): sorted 5,7,8,14,17,25,29,31,32,37,42 →
    Q1 = 8 (median of 5,7,8,14,17), Median = 25, Q3 = 32 (median of 29,31,32,37,42)."""
    blk = instantiate(find_template("mat-ws-boxplot"), 1)
    assert _text(blk.answer_key) == (
        "Minimum = 5, Q₁ = 8, Median = 25, Q₃ = 32, Maximum = 42; "
        "Spannweite = 37; Interquartilsabstand = 24")


def test_boxplot_unsuitable_rejects_degenerate_draw_and_resamples():
    """A no-spread draw raises Unsuitable (the guard); make_variants still yields only
    non-degenerate variants (the resample)."""
    class _ConstRng:                                   # every value identical → spread 0
        def choice(self, seq):
            return seq[0]

        def randint(self, a, b):
            return 20

    with pytest.raises(Unsuitable):
        _RECIPES["boxplot_from_data"](_ConstRng())

    for blk in make_variants(find_template("mat-ws-boxplot"), 8, seed0=1):
        iqr = int(re.search(r"Interquartilsabstand = (\d+)", _text(blk.answer_key)).group(1))
        assert iqr >= 1                                # never a degenerate summary


# --- probability tree: exact fractions (ground truth) ------------------------
def _tree_probability(prompt: str):
    """Recompute the asked probability independently (exact sympy Rational) from the urn
    and the question type parsed out of the prompt."""
    r, b = (int(x) for x in re.search(r"(\d+) rote und (\d+) blaue", prompt).groups())
    n = r + b
    mit = "mit Zurücklegen" in prompt
    p_r, p_b = sympy.Rational(r, n), sympy.Rational(b, n)

    def st(first_red, want_red):
        if mit:
            return p_r if want_red else p_b
        red_left = r - 1 if first_red else r
        blue_left = b - 1 if not first_red else b
        return sympy.Rational(red_left if want_red else blue_left, n - 1)

    if "genau eine rote" in prompt:
        return p_r * st(True, False) + p_b * st(False, True)
    if "Die erste gezogene Kugel ist" in prompt:
        c1 = re.search(r"erste gezogene Kugel ist (rot|blau)", prompt).group(1)
        c2 = re.search(r"zweite Kugel (rot|blau)", prompt).group(1)
        return st(c1 == "rot", c2 == "rot")
    c1, c2 = re.search(r"zuerst (rot|blau) und dann (rot|blau)", prompt).groups()
    return (p_r if c1 == "rot" else p_b) * st(c1 == "rot", c2 == "rot")


def test_tree_probabilities_are_exact_and_match_recomputation():
    asks = set()
    for seed in range(40):
        blk = instantiate(find_template("mat-ws-baumdiagramm"), seed)
        prompt = _text(blk.prompt)
        P = _tree_probability(prompt)
        assert 0 < P < 1
        # the answer's leading run is the exact fraction (sympy latex)
        frac = blk.answer_key[0].text
        assert frac == sympy.latex(P), (seed, frac, sympy.latex(P))
        asks.add("genau" if "genau eine" in prompt else
                 "bedingt" if "bedingte" in prompt else "pfad")
    assert asks == {"pfad", "genau", "bedingt"}        # all three ask-types exercised


def test_tree_fixed_seed_exact_fractions():
    # seed 4: 3 rot / 4 blau, ohne Zurücklegen, P(rot dann rot) = 3/7·2/6 = 1/7
    assert instantiate(find_template("mat-ws-baumdiagramm"), 4).answer_key[0].text == r"\frac{1}{7}"
    # seed 3: 3 rot / 6 blau, ohne, P(2. blau | 1. rot) = 6/8 = 3/4
    assert instantiate(find_template("mat-ws-baumdiagramm"), 3).answer_key[0].text == r"\frac{3}{4}"


# --- determinism + distinctness ----------------------------------------------
@pytest.mark.parametrize("tid", PACK_IDS)
def test_variants_deterministic_and_distinct(tid):
    t = find_template(tid)
    a = make_variants(t, 6, seed0=1)
    b = make_variants(t, 6, seed0=1)
    assert [_text(x.prompt) for x in a] == [_text(x.prompt) for x in b]   # deterministic
    assert len({_text(x.prompt) for x in a}) >= 5                         # distinct
    assert all(x.answer_key and x.solution_steps for x in a)              # answer + Rechenweg


# --- the full product path: assemble → verify → RENDER ------------------------
def test_pack_assembles_verifies_and_covers_competence():
    for tid in PACK_IDS:
        t = find_template(tid)
        content, res = variant_worksheet(t, n=3, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert rep.ok, (tid, rep.problems)
        assert content.meta.stufe == "Oberstufe"
        blocks = content.sections[0].blocks
        assert len(blocks) == 3 and all(b.solution_steps and b.answer_key for b in blocks)
        dim_ids = content.subject_model.dimension_ids()
        assert all(set(b.dimensions) <= dim_ids for b in blocks)
        served = t.serves[0].competence_id
        cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
        assert cov.get(served) is True, (tid, served)


def test_pack_renders_student_and_teacher(tmp_path):
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    for tid in PACK_IDS:
        t = find_template(tid)
        content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
        content = assemble(content, res)
        for render in (render_student_sheet, render_teacher_guide):
            out = render(content, tmp_path / f"{tid}_{render.__name__}.pdf")
            assert out.exists() and out.stat().st_size > 1000, (tid, render.__name__)
