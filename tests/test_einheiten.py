"""Einheiten-Detektiv — dimensional-analysis puzzles by INVERTING the units guard.

Locks the load-bearing guarantee: every distractor's computed dimension differs from the
target (or, for the additive slip, its summands are dimensionally inhomogeneous), while the
one correct option matches. Plus: no accidental dimensional coincidence survives, determinism
per seed, options deduped, the transform-catalog discipline, the honest open_response shape
(the Begründung needs write-space), verbatim PHY anchors, and the full product path —
assemble + verify + RENDER (the render test catches a text/format slip the way the physics
render test does; assemble/verify never render).
"""

from __future__ import annotations

import random
from datetime import date

import pytest

from teachersaid.pipeline import einheiten as E
from teachersaid.pipeline.dimensions import _base_dims, _assert_dimension
from teachersaid.pipeline.parametrize import _RECIPES, make_variants
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.verify import verify
from teachersaid.library.templates import find_template, variant_worksheet

IN_WINDOW = date(2026, 3, 1)
RECIPES = ["einheiten_bewegung", "einheiten_elektrik", "einheiten_energie"]
TEMPLATES = ["phy-einheiten-bewegung", "phy-einheiten-elektrik", "phy-einheiten-energie"]


# ============================================================================
# the headline guarantee: distractors are dimensionally impossible, by construction
# ============================================================================
def test_recipes_registered():
    assert set(RECIPES) <= set(_RECIPES)


def test_catalog_correct_formulas_are_dimensionally_right():
    """Every curated correct formula's composed unit equals its target's dimension (the guard,
    not inverted — the import-time check re-asserted here)."""
    for spec in E.FORMULAS:
        _assert_dimension(E._mono_unit(spec.factors), spec.target.unit)   # raises otherwise


def test_every_distractor_is_dimensionally_impossible():
    """THE guarantee. Over many seeds and every spec: exactly one correct option whose
    dimension matches the target, and every other option PROVEN impossible — a `mono`
    distractor reduces to a different base dimension, a `sum` distractor is inhomogeneous."""
    for spec in E.FORMULAS:
        for seed in range(250):
            cands, ci = E.build_item(spec, random.Random(seed))
            assert 3 <= len(cands) <= 4
            correct = cands[ci]
            assert correct.transform_id is None and correct.factors == spec.factors
            assert E._same_dim(correct.factors, spec.target.unit)      # correct is correct
            n_correct = 0
            for j, c in enumerate(cands):
                if j == ci:
                    n_correct += 1
                    continue
                assert c.transform_id is not None
                assert E._prove_wrong(c, spec.target.unit)             # PROVEN wrong
                if c.kind == "mono":
                    assert not E._same_dim(c.factors, spec.target.unit)
                else:
                    a, b = c.addends
                    assert _base_dims(a.unit) != _base_dims(b.unit)    # unlike units added
            assert n_correct == 1                                      # exactly one correct


def test_prove_wrong_rejects_a_dimensional_coincidence():
    """The guard both ways: the correct formula is NOT judged wrong (so a transform that
    happened to reproduce the target dimension would be rejected by build_item), while a
    genuine unit-category slip IS judged wrong."""
    spec = next(s for s in E.FORMULAS if s.target.symbol == "v")       # v = s/t → m/s
    correct = E.Candidate("mono", "v", factors=spec.factors)
    assert E._prove_wrong(correct, spec.target.unit) is False          # coincidence → rejected
    wrong = E.Candidate("mono", "v", factors=((E._S, 1), (E._T, 1)))   # v = s·t → m·s
    assert E._prove_wrong(wrong, spec.target.unit) is True


def test_options_are_deduped_within_item():
    for spec in E.FORMULAS:
        for seed in range(200):
            cands, _ = E.build_item(spec, random.Random(seed))
            displays = [E.formula_display(c) for c in cands]
            assert len(displays) == len(set(displays))


def test_determinism_per_seed():
    for rid in RECIPES:
        for seed in (1, 7, 42, 99):
            a = _RECIPES[rid](random.Random(seed))
            b = _RECIPES[rid](random.Random(seed))
            assert a.params == b.params and str(a.answer) == str(b.answer)
            assert [s.text for s in a.steps] == [s.text for s in b.steps]


# ============================================================================
# the transform catalog — the correct-by-construction WRONGNESS layer
# ============================================================================
def test_transform_catalog_discipline():
    """Every catalog entry carries the curated German fields; every transform id a candidate
    can carry is catalogued (get_transform resolves it, an unknown id raises)."""
    assert len(E.TRANSFORM_CATALOG) >= 5
    for t in E.TRANSFORM_CATALOG:
        assert t.id and t.name and t.short and t.source
        assert E.get_transform(t.id) is t
    with pytest.raises(KeyError):
        E.get_transform("nope")

    emitted: set[str] = set()
    for spec in E.FORMULAS:
        for seed in range(120):
            cands, ci = E.build_item(spec, random.Random(seed))
            for j, c in enumerate(cands):
                if j != ci:
                    emitted.add(c.transform_id)
    assert emitted <= {t.id for t in E.TRANSFORM_CATALOG}
    assert len(emitted) >= 4                                           # real variety of slips


def test_additive_slip_appears_and_is_inhomogeneous():
    """A pure-product formula must produce the 'plus statt mal' distractor somewhere — the
    single strongest unit lesson: two quantities with unlike units cannot be added."""
    spec = next(s for s in E.FORMULAS if s.target.symbol == "U")       # U = R·I
    seen = False
    for seed in range(200):
        cands, _ = E.build_item(spec, random.Random(seed))
        for c in cands:
            if c.kind == "sum":
                seen = True
                a, b = c.addends
                assert c.transform_id == "sum_for_product"
                assert _base_dims(a.unit) != _base_dims(b.unit)
    assert seen


def test_reasoning_matches_the_computed_verdict():
    """Each solution step's verdict is DERIVED from the dimension check: the correct option's
    line says 'kann stimmen', every distractor's says 'kann nicht stimmen'."""
    for rid in RECIPES:
        for seed in range(60):
            inst = _RECIPES[rid](random.Random(seed))
            can_stimmen = [s for s in inst.steps if "kann stimmen" in s.text]
            cannot = [s for s in inst.steps if "kann nicht stimmen" in s.text]
            assert len(can_stimmen) == 1                               # exactly one correct
            assert len(cannot) == len(inst.steps) - 1
            assert str(inst.answer).startswith("Nur ")


# ============================================================================
# variants, anchors, and the full product path
# ============================================================================
def test_variants_distinct_and_deterministic():
    for tid in TEMPLATES:
        t = find_template(tid)
        vs = make_variants(t, 5, seed0=1)
        assert len({str(b.prompt) for b in vs}) == 5, (tid, "variants not distinct")
        vs2 = make_variants(t, 5, seed0=1)
        assert [str(b.prompt) for b in vs2] == [str(b.prompt) for b in vs], tid


def test_open_response_shape_gives_writespace():
    """The honest task shape: open_response (a core kind — no subject-model change), ruled
    lines for the Begründung, and the candidates listed IN the prompt."""
    for tid in TEMPLATES:
        t = find_template(tid)
        for b in make_variants(t, 4, seed0=1):
            assert b.kind == "open_response"
            assert b.response.mode == "lines" and b.response.n >= 4
            text = b.prompt if isinstance(b.prompt, str) else "".join(r.text for r in b.prompt)
            assert "Zur Auswahl stehen" in text and "Einheiten" in text
            assert b.answer_key and b.solution_steps


def test_anchors_are_verbatim_phy_competences():
    templ = [find_template(t) for t in TEMPLATES]
    assert {t.serves[0].competence_id for t in templ} == {
        "PHY.US.3.MEC.01", "PHY.US.3.ELE.01", "PHY.US.3.ENE.01"}
    assert all(t.subject == "Physik" and t.klasse == 3 for t in templ)
    assert all(t.cognitive_level == "analyze" for t in templ)
    assert all(d in {"W", "E", "S"} for t in templ for d in t.dimensions)


def test_templates_assemble_and_verify_clean():
    """Every template → N variants that assemble + verify clean, the served PHY competence
    bound in the Nachweis (the trust feature)."""
    for tid in TEMPLATES:
        t = find_template(tid)
        content, res = variant_worksheet(t, n=4, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert rep.ok, (tid, rep.problems)
        blocks = content.sections[0].blocks
        assert len(blocks) == 4 and all(b.answer_key and b.solution_steps for b in blocks)
        served = t.serves[0].competence_id
        cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
        assert cov.get(served) is True, (tid, served, "not covered in Nachweis")


def test_templates_render(tmp_path):
    """Render student + teacher for every variant — guards the whole text/format path end to
    end (a SolutionStep formatting slip would surface here, not in assemble/verify)."""
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    for tid in TEMPLATES:
        t = find_template(tid)
        content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
        content = assemble(content, res)
        for render in (render_student_sheet, render_teacher_guide):
            out = render(content, tmp_path / f"{tid}_{render.__name__}.pdf")
            assert out.exists() and out.stat().st_size > 1000, (tid, render.__name__)
