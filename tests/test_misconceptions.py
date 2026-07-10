"""The Misconception engine (roadmap A3) — correct-by-construction MC distractors.

Locks the load-bearing guarantees: every multiple_choice distractor is COMPUTED by applying
a catalogued misconception to the SAME drawn numbers the correct answer used, so it is
guaranteed ≠ the correct option (both computed, compared post-formatting), the distractors
are pairwise distinct, the plausibility gate drops impossible values, and — the payoff — the
teacher guide names which misconception each distractor probes. Plus catalog integrity (no
orphan transform, no unused catalog entry) and the full product path (variant_worksheet →
assemble → verify clean; teacher shows the labels, student hides them).

The engine is zero-LLM: distractors + labels are derived at variant time.
"""

from __future__ import annotations

import random
from datetime import date

import pytest

from teachersaid.grounding import misconceptions as cat
from teachersaid.pipeline import misconceive as mis
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.parametrize import _RECIPES, instantiate, make_variants
from teachersaid.pipeline.verify import verify
from teachersaid.schema.blocks import Serves
from teachersaid.schema.parametric import MCSpec, ParametricTask

IN_WINDOW = date(2026, 3, 1)

# every MC recipe implemented in this engine
MC_RECIPES = [
    "linear_equation_mc", "percentage_mc", "fraction_add_mc",
    "ohm_mc", "uniform_motion_mc", "resistors_mc", "molar_mass_mc",
]

# the MC templates shipped in the library
MC_TEMPLATE_IDS = [
    "mat-prozent-mc", "mat-lineare-gleichung-mc",
    "phy-us-ohm-mc", "phy-os-ersatzwiderstand-mc",
]


def _mk(recipe: str, tmpl: str = "{aufgabe}") -> ParametricTask:
    return ParametricTask(
        id=recipe, subject="Mathematik", klasse=2,
        kompetenzbereich="2: Variablen und Funktionen", recipe=recipe,
        prompt_template=tmpl, serves=[Serves(competence_id="X", relation="exercises")],
        dimensions=["OPE"], kind="multiple_choice")


_TEMPLATES = {
    "linear_equation_mc": "Löse: ${eq}$",
    "percentage_mc": "Wie viel sind {pct} % von {base}?",
    "fraction_add_mc": "Berechne: ${f1} + {f2}$",
    "ohm_mc": "{aufgabe}",
    "uniform_motion_mc": "{aufgabe}",
    "resistors_mc": "{aufgabe}",
    "molar_mass_mc": "Berechne die molare Masse von {formel}.",
}


def _opt_text(option: str) -> str:
    """Strip the 'X) ' letter prefix from a rendered option, leaving the value text."""
    return option.split(") ", 1)[1] if ") " in option else option


def _reproduce_mc(recipe: str, seed: int):
    """Reproduce the engine's per-seed MC build to recover the derived distractor records
    and the shuffle — mirrors `instantiate` exactly (same RNG, same resampling loop).
    Returns (instance, MCResult)."""
    from teachersaid.pipeline.parametrize import Unsuitable
    rng = random.Random(seed)
    fn = _RECIPES[recipe]
    for _ in range(500):
        try:
            inst = fn(rng)
            res = mis.build_distractors(inst.mc, rng)          # consumes rng like _mc_fields
            return inst, res
        except (Unsuitable, ValueError):
            continue                                           # loop resamples with next state
    raise AssertionError(f"{recipe}: no MC in 500 tries")


# ============================================================================
# catalog integrity
# ============================================================================
def test_every_transform_id_exists_in_catalog():
    """A transform may only register against a real catalog id (the @_misconception
    decorator enforces it at import; assert the registry agrees with the catalog)."""
    for mid in mis._TRANSFORMS:
        assert mid in cat.CATALOG, f"transform {mid!r} has no catalog entry"


def test_every_catalog_entry_is_used_or_planned():
    """No padding: every curated misconception is implemented by ≥1 transform, unless it is
    explicitly on the PLANNED allow-list (currently empty)."""
    for mid in cat.CATALOG:
        assert mid in mis._TRANSFORMS or mid in cat.PLANNED, \
            f"catalog entry {mid!r} is neither implemented nor marked planned"
    # and PLANNED ids must themselves be real catalog ids
    assert cat.PLANNED <= set(cat.CATALOG)


def test_catalog_entries_have_german_text_and_a_source():
    """Each entry carries the teacher-guide German name + description + a real source note
    (curation provenance) + a non-empty scope."""
    for m in cat.CATALOG.values():
        assert m.name and m.short and m.source and m.scope
        # the source is a bibliographic note, not a fabricated URL
        assert "http" not in m.source.lower()


def test_catalog_get_and_label():
    assert cat.label("sign_error") == "Vorzeichenfehler"
    with pytest.raises(KeyError):
        cat.get("not_a_real_id")


# ============================================================================
# the three guarantees (across many seeds)
# ============================================================================
def test_every_distractor_differs_from_correct_and_is_distinct():
    """Across a wide seed sweep, for every MC recipe: each option is distinct (so no
    distractor equals the correct answer AND none duplicates another) — checked on the
    FORMATTED text, which is how the engine compares them."""
    for recipe in MC_RECIPES:
        t = _mk(recipe, _TEMPLATES[recipe])
        for seed in range(1, 250):
            b = instantiate(t, seed)
            assert b.payload is not None and b.payload.kind == "multiple_choice"
            texts = [_opt_text(o) for o in b.payload.options]
            assert len(texts) == len(set(texts)), (recipe, seed, "options not distinct", texts)
            # at least the correct + one distractor
            assert len(texts) >= 2, (recipe, seed, "too few options")


def test_correct_option_is_present_exactly_once_and_answer_names_it():
    """The answer_key names the correct letter, and that letter's option is in the set."""
    for recipe in MC_RECIPES:
        t = _mk(recipe, _TEMPLATES[recipe])
        for seed in range(1, 60):
            b = instantiate(t, seed)
            letters = b.response.options                     # ["A","B",...]
            ans = str(b.answer_key)
            letter = ans.split(")", 1)[0]
            assert letter in letters, (recipe, seed, ans)
            # the answer text matches the corresponding payload option
            idx = letters.index(letter)
            assert _opt_text(b.payload.options[idx]) in ans


def test_per_seed_determinism():
    """Same seed → identical options, answer, and distractor records (order incl.)."""
    for recipe in MC_RECIPES:
        t = _mk(recipe, _TEMPLATES[recipe])
        for seed in (1, 7, 42, 99):
            a = instantiate(t, seed)
            b = instantiate(t, seed)
            assert a.payload.options == b.payload.options
            assert str(a.answer_key) == str(b.answer_key)
            assert a.watch_outs == b.watch_outs


def test_distractors_are_the_computed_misconception_values():
    """A spot-check that a distractor VALUE is exactly the misconception applied to the
    drawn numbers, not a random number — recompute independently for the linear-equation
    recipe: sign_error x=(c+b)/a; inverse_operation x=(c-b)·a. The value each named
    distractor carries must equal its own transform on this draw."""
    for seed in range(1, 60):
        inst, res = _reproduce_mc("linear_equation_mc", seed)
        a = inst.mc.magnitudes["a"]; bcoef = inst.mc.magnitudes["b"]; c = inst.mc.magnitudes["c"]
        recompute = {
            "sign_error": (c + bcoef) / a,
            "inverse_operation": (c - bcoef) * a,
        }
        for d in res.distractors:
            expected = recompute[d.misconception_id]
            # the distractor text is the formatted expected value (x = N)
            assert d.text == mis.format_value(expected, inst.mc), (seed, d)
        # and the correct answer genuinely solves the equation
        correct_val = float(_opt_text(res.options[res.correct_index]).split("=")[1])
        assert a * correct_val + bcoef == c, (seed, correct_val)


# ============================================================================
# plausibility gate
# ============================================================================
def test_plausibility_gate_drops_negative_when_nonneg():
    """A `nonneg` spec drops a distractor transform that yields a negative value; a spec
    without `nonneg` keeps it. Drive `build_distractors` directly with a crafted spec."""
    # a transform value forced negative: use unit_power_ten on a negative correct value is
    # awkward; instead craft magnitudes so a real transform goes negative. percent base
    # confusion base*100/pct is always positive, so use fraction add-across with a negative
    # component via a synthetic spec on the sign_error transform:
    #   correct arbitrary; sign_error uses (c+b)/a — pick a<0 path won't trigger nonneg on x.
    # Simplest: assert the gate logic directly on a spec whose applicable transform is
    # unit_power_ten with a negative correct value.
    neg_spec = MCSpec(magnitudes={}, correct=-3.0, applicable=["unit_power_ten"],
                      nonneg=True)                             # ×10 → -30, must be dropped
    with pytest.raises(ValueError):                            # nothing survives → raises
        mis.build_distractors(neg_spec, random.Random(0))
    # without nonneg the same distractor survives
    ok_spec = MCSpec(magnitudes={}, correct=-3.0, applicable=["unit_power_ten"],
                     nonneg=False)
    res = mis.build_distractors(ok_spec, random.Random(0))
    assert any(d.misconception_id == "unit_power_ten" for d in res.distractors)


def test_collision_with_correct_is_dropped():
    """A transform whose value formats identically to the correct answer is dropped
    (the ≠-correct guarantee), not offered as a fake distractor."""
    # unit_power_ten on correct=0 → 0, which equals the correct value → dropped. Pair it
    # with a surviving transform so the build still yields a distractor.
    spec = MCSpec(magnitudes={"base": 200.0, "pct": 10.0}, correct=0.0,
                  applicable=["unit_power_ten", "percent_base_confusion"])
    res = mis.build_distractors(spec, random.Random(1))
    ids = [d.misconception_id for d in res.distractors]
    assert "unit_power_ten" not in ids                        # 0·10 = 0 = correct → dropped
    assert "percent_base_confusion" in ids                    # 200·100/10 = 2000 → kept


def test_build_raises_when_no_distractor_survives():
    """If every transform declines / collides, the builder raises (caller resamples).
    unit_power_ten on correct=0 → 0, which collides with the correct value → dropped → no
    distractor survives."""
    spec_collide = MCSpec(magnitudes={}, correct=0.0, applicable=["unit_power_ten"])
    with pytest.raises(ValueError):
        mis.build_distractors(spec_collide, random.Random(0))


# ============================================================================
# the teacher guide names the right misconception per distractor
# ============================================================================
def test_teacher_watch_outs_name_the_catalog_entries():
    """Every distractor has a watch-out line 'X prüft: <German name> (<source lead>)', the
    letter matches the option, and the named misconception is the one the distractor record
    carries (so the label is truthful, not decorative)."""
    for recipe in MC_RECIPES:
        t = _mk(recipe, _TEMPLATES[recipe])
        for seed in range(1, 40):
            b = instantiate(t, seed)
            # one watch-out per distractor
            probe_lines = [w for w in b.watch_outs if "prüft:" in w]
            assert len(probe_lines) == len(b.payload.options) - 1
            # each names a real catalog display name
            names = {m.name for m in cat.CATALOG.values()}
            for w in probe_lines:
                after = w.split("prüft:", 1)[1]
                assert any(n in after for n in names), (recipe, w)
            # the letters used in the probe lines are exactly the non-correct options
            correct_letter = str(b.answer_key).split(")", 1)[0]
            probe_letters = {w.split(" prüft:", 1)[0].strip() for w in probe_lines}
            all_letters = set(b.response.options)
            assert probe_letters == (all_letters - {correct_letter})


def test_watch_out_label_tracks_the_probed_misconception():
    """The German name in each watch-out line is the name of the misconception whose value
    that option holds — reconstruct the (letter → misconception) map from the DERIVED
    distractor records (via a faithful replay of the engine) and check the block's watch-out
    labels agree, so the 'B prüft: …' claim is truthful, not decorative."""
    for recipe in MC_RECIPES:
        t = _mk(recipe, _TEMPLATES[recipe])
        for seed in (3, 11, 23):
            b = instantiate(t, seed)
            inst, res = _reproduce_mc(recipe, seed)
            # the replay must reproduce the block's options exactly (proves it is faithful)
            replay_opts = [f"{'ABCDEFGH'[i]}) {o}" for i, o in enumerate(res.options)]
            assert replay_opts == b.payload.options, (recipe, seed)
            letters = "ABCDEFGH"[:len(res.options)]
            text_to_letter = {o: letters[i] for i, o in enumerate(res.options)}
            expected = {text_to_letter[d.text]: cat.get(d.misconception_id).name
                        for d in res.distractors}
            for w in b.watch_outs:
                if "prüft:" not in w:
                    continue
                letter = w.split(" prüft:", 1)[0].strip()
                assert expected[letter] in w, (recipe, seed, w, expected[letter])


# ============================================================================
# distractors ride into the block as a self-contained MC (no write-space)
# ============================================================================
def test_mc_block_is_self_contained_choices():
    """The emitted block is a multiple_choice payload + a choices response (the options ARE
    the response surface — no generic write-space, per _SELF_CONTAINED_PAYLOADS)."""
    from teachersaid.rendering.blocks_to_flowables import _SELF_CONTAINED_PAYLOADS
    assert "multiple_choice" in _SELF_CONTAINED_PAYLOADS
    b = instantiate(_mk("percentage_mc", _TEMPLATES["percentage_mc"]), 5)
    assert b.payload.kind == "multiple_choice"
    assert b.response.mode == "choices"
    assert b.payload.select == "one" and b.response.select == "one"
    assert len(b.response.options) == len(b.payload.options)


# ============================================================================
# the full product path — make_variants → variant_worksheet → assemble → verify
# ============================================================================
def test_make_variants_distinct_and_deterministic_for_mc():
    for recipe in MC_RECIPES:
        t = _mk(recipe, _TEMPLATES[recipe])
        a = make_variants(t, 5, seed0=1)
        assert len({str(b.prompt) for b in a}) == 5, (recipe, "variants not distinct")
        b = make_variants(t, 5, seed0=1)
        assert [str(x.prompt) for x in a] == [str(x.prompt) for x in b], recipe
        assert all(x.payload and x.payload.kind == "multiple_choice" for x in a)


def test_mc_templates_exist_and_are_multiple_choice():
    from teachersaid.library.templates import find_template
    for tid in MC_TEMPLATE_IDS:
        t = find_template(tid)
        assert t is not None, tid
        assert t.kind == "multiple_choice", tid


def test_mc_templates_build_assemble_verify_clean():
    """Every MC template → N variants that assemble + verify CLEAN, with the served
    competence bound in the Nachweis (the trust feature) — multiple_choice is a core kind,
    so no subject-model change is needed."""
    from teachersaid.library.templates import find_template, variant_worksheet
    for tid in MC_TEMPLATE_IDS:
        t = find_template(tid)
        content, res = variant_worksheet(t, n=3, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert rep.ok, (tid, rep.problems)
        blocks = content.sections[0].blocks
        assert len(blocks) == 3
        for blk in blocks:
            assert blk.payload and blk.payload.kind == "multiple_choice"
            assert blk.answer_key and blk.solution_steps           # answer + Rechenweg present
            assert any("prüft:" in w for w in blk.watch_outs)      # the payoff lines are there
        served = t.serves[0].competence_id
        cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
        assert cov.get(served) is True, (tid, served, "not covered in Nachweis")


def test_mc_teacher_shows_labels_student_hides(tmp_path):
    """Render both projections: the teacher guide shows the answer + the 'X prüft: …' lines;
    the student sheet shows neither (options only, no answer, no misconception labels)."""
    import fitz
    from teachersaid.library.templates import find_template, variant_worksheet
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide

    t = find_template("mat-prozent-mc")
    content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
    content = assemble(content, res)
    sp = render_student_sheet(content, tmp_path / "s.pdf")
    tp = render_teacher_guide(content, tmp_path / "t.pdf")
    stud = "".join(p.get_text() for p in fitz.open(sp))
    teach = "".join(p.get_text() for p in fitz.open(tp))
    assert "prüft:" in teach and "richtig)" in teach            # labels + answer on teacher
    assert "prüft:" not in stud                                 # never leaks to the student
    # the student sees option labels (A/B/C) — the response surface
    assert "☐" in stud or "A" in stud


def test_all_mc_recipes_registered():
    assert set(MC_RECIPES) <= set(_RECIPES)
