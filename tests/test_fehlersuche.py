"""The Fehlersuche engine — worked solutions with exactly one PLANTED, catalogued error.

Locks the load-bearing guarantees of `pipeline/fehlersuche.py`:
  * the planted step's value ≠ the correct step's value, and the flawed final answer ≠ the
    correct final answer (both checked on the FORMATTED display strings, and independently
    recomputed from the drawn numbers — a distractor value that is genuinely the misconception
    applied, not a random number);
  * the flawed chain is internally consistent (a student following the flawed step reproduces
    the shown numbers);
  * deterministic per seed;
  * the Fehlermuster are SELECTED from the curated catalog (`grounding/misconceptions.py`);
  * audience split: the flawed chain is on the STUDENT (+ homework) sheet; the correct chain,
    the located wrong step + the Fehlermuster name stay TEACHER-only — the student sheet reveals
    neither the correct answer nor which step is wrong;
  * the full product path: every template → variants that assemble + verify clean, kind
    open_response (write-space to name + correct the error).
"""

from __future__ import annotations

import random
import re
from datetime import date
from fractions import Fraction

import pytest

from teachersaid.grounding import misconceptions as cat
from teachersaid.library.templates import PARAM_TEMPLATES, find_template, variant_worksheet
from teachersaid.pipeline import fehlersuche as fs
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.parametrize import _RECIPES, instantiate, make_variants
from teachersaid.pipeline.verify import verify

IN_WINDOW = date(2026, 3, 1)

FEHLERSUCHE_RECIPES = [
    "fehlersuche_linear_equation", "fehlersuche_fraction_add", "fehlersuche_percentage",
]
FEHLERSUCHE_TEMPLATE_IDS = [
    "mat-fehlersuche-lineare-gleichung", "mat-fehlersuche-bruch-addition",
    "mat-fehlersuche-prozent",
]


def _flat(rt) -> str:
    return rt if isinstance(rt, str) else "".join(getattr(r, "text", "") for r in rt)


def _final_int(expr: str) -> int:
    """The trailing integer of an expr like 'x = \\frac{20}{5} = 4' → 4."""
    return int(re.findall(r"(-?\d+)", expr)[-1])


def _frac_of(expr: str) -> Fraction:
    """The last fraction in an expr: '= \\frac{5}{6}' → 5/6; '= 3' → 3/1."""
    fracs = re.findall(r"\\frac\{(-?\d+)\}\{(-?\d+)\}", expr)
    if fracs:
        p, q = fracs[-1]
        return Fraction(int(p), int(q))
    return Fraction(_final_int(expr), 1)


# ============================================================================
# registration + catalog reuse
# ============================================================================
def test_recipes_registered():
    assert set(FEHLERSUCHE_RECIPES) <= set(_RECIPES)


def test_reused_fehlermuster_are_in_the_curated_catalog():
    """The engine SELECTS its Fehlermuster from grounding/misconceptions (select, never author);
    every referenced id is a real catalog entry (also enforced at import in fehlersuche.py)."""
    for mid in fs._USED_FEHLERMUSTER:
        assert mid in cat.CATALOG, mid
        m = cat.get(mid)
        assert m.name and m.source and "http" not in m.source.lower()


def test_templates_exist_and_are_error_analysis_open_response():
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        assert t is not None, tid
        assert t.kind == "open_response", tid            # affords write-space (name + correct)
        assert t.cognitive_level == "analyze", tid       # Fehleranalyse is AFB-II/III
        assert t.recipe in FEHLERSUCHE_RECIPES, tid


def test_templates_appended_to_param_templates():
    ids = {t.id for t in PARAM_TEMPLATES}
    assert set(FEHLERSUCHE_TEMPLATE_IDS) <= ids


def test_flawed_solution_absent_from_generation_view():
    """The flawed chain is DERIVED, never LLM-authored — like solution_steps/scaffold it is
    absent from the generation view, so the model literally cannot emit it."""
    from teachersaid.schema.generation_views import GenTaskBlock
    assert "flawed_solution" not in GenTaskBlock.model_fields


# ============================================================================
# the correct-by-construction guarantees (across a wide seed sweep)
# ============================================================================
def test_every_variant_has_a_flawed_and_a_correct_chain():
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        for seed in range(1, 120):
            b = instantiate(t, seed)
            assert b.flawed_solution, (tid, seed, "no flawed chain")
            assert b.solution_steps, (tid, seed, "no correct chain")
            assert b.answer_key, (tid, seed, "no teacher answer_key")


def test_flawed_final_differs_from_correct_final_post_formatting():
    """The last step of the flawed chain and of the correct chain format to DIFFERENT text —
    the planted error genuinely changes the answer (checked on the formatted display strings,
    the same discipline as the MC engine)."""
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        for seed in range(1, 120):
            b = instantiate(t, seed)
            flawed_final = _flat(b.flawed_solution[-1].expr or b.flawed_solution[-1].text)
            correct_final = _flat(b.solution_steps[-1].expr or b.solution_steps[-1].text)
            assert flawed_final != correct_final, (tid, seed, flawed_final)


def test_planted_step_differs_from_the_correct_step():
    """At least one step of the flawed chain differs from the correct chain (the error is
    actually planted, not a no-op) — compared as (text, expr) pairs."""
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        for seed in range(1, 60):
            b = instantiate(t, seed)
            flawed = [(_flat(s.text), s.expr) for s in b.flawed_solution]
            correct = [(_flat(s.text), s.expr) for s in b.solution_steps]
            assert flawed != correct, (tid, seed)


def test_linear_equation_flaw_is_the_computed_misconception():
    """Independently recompute: the flawed final is EXACTLY the Fehlermuster applied to the drawn
    a,b,c — sign_error x=(c+b)/a (Schritt 2) or inverse_operation x=(c-b)·a (Schritt 3) — and the
    correct chain genuinely solves a·x+b=c. Not a random wrong number."""
    t = find_template("mat-fehlersuche-lineare-gleichung")
    saw_sign = saw_inverse = False
    for seed in range(1, 120):
        b = instantiate(t, seed)
        a, bb, c = (int(x) for x in re.findall(r"(-?\d+)", b.flawed_solution[0].expr)[:3])
        correct = (c - bb) // a
        assert a * correct + bb == c                       # the correct answer solves the equation
        assert _final_int(b.solution_steps[-1].expr) == correct
        flawed_final = _final_int(b.flawed_solution[-1].expr)
        ak = str(b.answer_key)
        if cat.get("sign_error").name in ak:
            saw_sign = True
            assert "Schritt 2" in ak
            assert flawed_final == (c + bb) // a            # sign slip: added instead of subtracted
        else:
            saw_inverse = True
            assert cat.get("inverse_operation").name in ak
            assert "Schritt 3" in ak
            assert flawed_final == (c - bb) * a             # multiplied instead of dividing
        assert flawed_final != correct
    assert saw_sign and saw_inverse                          # both Fehlermuster occur (location varies)


def test_fraction_flaw_is_add_across_and_consistent():
    """The flawed chain is exactly (a+c)/(b+d) over the SHOWN (reduced) fractions, ≠ the true
    sum a/b+c/d — and the shown fractions and the arithmetic agree (honest propagation)."""
    t = find_template("mat-fehlersuche-bruch-addition")
    for seed in range(1, 120):
        b = instantiate(t, seed)
        (a, den1), (c, den2) = re.findall(r"\\frac\{(\d+)\}\{(\d+)\}", b.flawed_solution[0].expr)
        a, den1, c, den2 = int(a), int(den1), int(c), int(den2)
        total = Fraction(a, den1) + Fraction(c, den2)
        wrong = Fraction(a + c, den1 + den2)
        assert wrong != total                                # add-across changes the value
        assert _frac_of(b.flawed_solution[-1].expr) == wrong
        assert _frac_of(b.solution_steps[-1].expr) == total
        assert cat.get("fraction_add_across").name in str(b.answer_key)
        assert "Schritt 2" in str(b.answer_key)


def test_percentage_flaw_is_power_of_ten_and_consistent():
    """The flawed value is exactly 10× the correct one (÷10 instead of ÷100), and the shown
    multiplication reproduces it."""
    t = find_template("mat-fehlersuche-prozent")
    for seed in range(1, 120):
        b = instantiate(t, seed)
        pct, base = (int(x) for x in re.findall(r"(\d+)", _flat(b.prompt))[:2])
        w = base * pct // 100
        w_wrong = base * pct // 10
        assert w_wrong == 10 * w and w_wrong != w
        assert _final_int(b.solution_steps[-1].text) == w
        assert _final_int(b.flawed_solution[-1].text) == w_wrong
        assert cat.get("unit_power_ten").name in str(b.answer_key)
        assert "Schritt 2" in str(b.answer_key)


def test_deterministic_per_seed():
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        for seed in (1, 7, 42, 99):
            a = instantiate(t, seed)
            b = instantiate(t, seed)
            assert _flat(a.prompt) == _flat(b.prompt)
            assert [(s.text, s.expr) for s in a.flawed_solution] == \
                   [(s.text, s.expr) for s in b.flawed_solution]
            assert [(s.text, s.expr) for s in a.solution_steps] == \
                   [(s.text, s.expr) for s in b.solution_steps]
            assert str(a.answer_key) == str(b.answer_key)


def test_variants_mostly_distinct():
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        vs = make_variants(t, 6, seed0=1)
        assert len({_flat(v.prompt) for v in vs}) >= 4, tid
        assert all(v.flawed_solution and v.solution_steps for v in vs), tid


# ============================================================================
# the full product path: assemble + verify clean
# ============================================================================
def test_templates_build_assemble_verify_clean():
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        content, res = variant_worksheet(t, 4, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert rep.ok, (tid, rep.problems)
        tasks = [b for b in content.iter_blocks() if b.role == "task"]
        assert len(tasks) == 4
        for blk in tasks:
            assert blk.kind == "open_response"
            assert blk.flawed_solution and blk.solution_steps and blk.answer_key
        served = t.serves[0].competence_id
        cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
        assert cov.get(served) is True, (tid, served, "not covered in Nachweis")


def test_open_response_gets_write_space_not_self_contained():
    """The kind honestly affords naming + correcting the error: open_response is NOT a
    self-contained payload, so the student projection renders write-space beneath it."""
    from teachersaid.rendering.blocks_to_flowables import _SELF_CONTAINED_PAYLOADS
    b = instantiate(find_template("mat-fehlersuche-prozent"), 5)
    assert b.kind == "open_response"
    assert b.payload is None
    assert "open_response" not in _SELF_CONTAINED_PAYLOADS
    assert b.response.mode == "lines" and b.response.n >= 3


# ============================================================================
# audience split — RENDER test (assemble/verify don't render; a new math path needs one)
# ============================================================================
def test_student_and_homework_hide_the_answer_teacher_shows_it(tmp_path):
    """Render all three projections. Student + homework show the flawed chain ('Vorgelegte
    Lösung') but NEVER the located step / Fehlermuster ('Gepflanzter Fehler') nor the correct
    Rechenweg. The teacher guide names the Fehlermuster + shows the correct chain."""
    import fitz
    from teachersaid.rendering.homework import render_homework
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide

    names = {m.name for m in cat.CATALOG.values()}
    for tid in FEHLERSUCHE_TEMPLATE_IDS:
        t = find_template(tid)
        content, res = variant_worksheet(t, 3, today=IN_WINDOW)
        content = assemble(content, res)
        sp = render_student_sheet(content, tmp_path / f"{tid}_s.pdf")
        hp = render_homework(content, tmp_path / f"{tid}_h.pdf")
        tp = render_teacher_guide(content, tmp_path / f"{tid}_t.pdf")
        stud = "".join(p.get_text() for p in fitz.open(sp))
        home = "".join(p.get_text() for p in fitz.open(hp))
        teach = "".join(p.get_text() for p in fitz.open(tp))

        for sheet, label in ((stud, "student"), (home, "homework")):
            assert "Vorgelegte Lösung" in sheet, (tid, label, "flawed chain missing")
            assert "Gepflanzter Fehler" not in sheet, (tid, label, "error location leaked")
            assert "Rechenweg" not in sheet, (tid, label, "correct chain leaked")

        assert "Vorgelegte Lösung" in teach                   # teacher sees the same artifact
        assert "Gepflanzter Fehler" in teach                  # …and where the error is
        assert "Rechenweg" in teach                           # …and the correct chain
        assert any(n in teach for n in names)                 # …named as a catalogued Fehlermuster


def test_all_param_templates_still_verify_clean_with_fehlersuche():
    """The registry-wide invariant still holds with the new templates: every ParametricTask →
    4 variants that assemble + verify clean, each with a worked correct chain (solution_steps)."""
    for t in PARAM_TEMPLATES:
        content, res = variant_worksheet(t, 4, today=IN_WINDOW)
        assemble(content, res)
        rep = verify(content, res)
        assert not rep.problems, (t.id, rep.problems)
        tasks = [b for b in content.iter_blocks() if b.role == "task"]
        assert len(tasks) == 4 and all(b.solution_steps for b in tasks), t.id
