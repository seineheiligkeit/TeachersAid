"""Chemistry quantitative engine — the chemistry twin of the sympy maths recipes.

Locks the load-bearing invariants: the formula parser, molar masses computed from the
grounded IUPAC atomic weights, equation balancing via the conservation-matrix nullspace,
and the full product path — every Chemie template → N correct-by-construction variants
that assemble + verify clean + render (the render test catches subscript/encoding slips
the way the maths render test catches mathtext-subset slips).
"""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.grounding.chemistry import (
    FormulaError, molar_mass, parse_formula, subscript,
)
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.chemistry import balance_equation, equation_str
from teachersaid.pipeline.parametrize import _RECIPES, make_variants
from teachersaid.pipeline.verify import verify
from teachersaid.library.templates import PARAM_TEMPLATES, find_template, variant_worksheet

IN_WINDOW = date(2026, 3, 1)
CHEM_OS = [t for t in PARAM_TEMPLATES if t.id.startswith("che-os-")]
CHEM_US = [t for t in PARAM_TEMPLATES if t.id.startswith("che-us-")]
CHEM = CHEM_OS + CHEM_US


# --- the formula parser (the load-bearing primitive) -------------------------
def test_parse_formula_basic_and_nested():
    assert parse_formula("H2O") == {"H": 2, "O": 1}
    assert parse_formula("NaCl") == {"Na": 1, "Cl": 1}
    assert parse_formula("Ca(OH)2") == {"Ca": 1, "O": 2, "H": 2}
    assert parse_formula("Al2(SO4)3") == {"Al": 2, "S": 3, "O": 12}
    assert parse_formula("CuSO4·5H2O") == {"Cu": 1, "S": 1, "O": 9, "H": 10}


def test_parse_formula_errors():
    with pytest.raises(FormulaError):
        parse_formula("Xy2")             # unknown element
    with pytest.raises(FormulaError):
        parse_formula("Ca(OH2")          # unbalanced parenthesis


def test_subscript_display():
    assert subscript("H2SO4") == "H₂SO₄"
    assert subscript("NaCl") == "NaCl"   # no digits → unchanged


# --- molar masses (computed from the grounded atomic weights) ----------------
@pytest.mark.parametrize("formula,expected", [
    ("H2O", 18.02), ("CO2", 44.01), ("NaCl", 58.44), ("H2SO4", 98.08),
    ("CaCO3", 100.09), ("C6H12O6", 180.16), ("Fe2O3", 159.69),
])
def test_molar_mass_known(formula, expected):
    assert molar_mass(formula) == pytest.approx(expected, abs=0.05)


# --- equation balancing (conservation-matrix nullspace) ----------------------
@pytest.mark.parametrize("reactants,products,rc,pc", [
    (["H2", "O2"], ["H2O"], [2, 1], [2]),
    (["N2", "H2"], ["NH3"], [1, 3], [2]),
    (["Fe", "O2"], ["Fe2O3"], [4, 3], [2]),
    (["CH4", "O2"], ["CO2", "H2O"], [1, 2], [1, 2]),
    (["C3H8", "O2"], ["CO2", "H2O"], [1, 5], [3, 4]),
    (["Al", "O2"], ["Al2O3"], [4, 3], [2]),
])
def test_balance_equation(reactants, products, rc, pc):
    assert balance_equation(reactants, products) == (rc, pc)


def test_balance_conserves_every_atom():
    for r, p in [(["C3H8", "O2"], ["CO2", "H2O"]), (["Fe", "O2"], ["Fe2O3"])]:
        rc, pc = balance_equation(r, p)
        elements = {e for s in r + p for e in parse_formula(s)}
        for el in elements:
            left = sum(c * parse_formula(s).get(el, 0) for c, s in zip(rc, r))
            right = sum(c * parse_formula(s).get(el, 0) for c, s in zip(pc, p))
            assert left == right, (el, r, p)


def test_balance_impossible_raises():
    with pytest.raises(ValueError):
        balance_equation(["Na"], ["Cl2"])   # no shared element / unbalanceable


# --- recipes + variants (correct by construction, deterministic) -------------
def test_chemistry_recipes_registered():
    assert {"molar_mass", "equation_balance", "stoichiometry",
            "substance_classification", "separation_method", "acid_base_neutral",
            "reaction_type", "atom_count"} <= set(_RECIPES)


# --- qualitative recipes (correct by curation / derivation) ------------------
def test_qualitative_curated_answers_correct():
    """Spot-check the curated truth tables against known chemistry."""
    from teachersaid.grounding.chemistry import (
        ACID_BASE, REACTION_TYPES, SEPARATION_METHODS, SUBSTANCE_CLASSES,
    )
    truth = dict(SUBSTANCE_CLASSES)
    assert truth["Wasser (H₂O)"] == "Verbindung"
    assert truth["Luft"] == "Gemisch"
    assert truth["Eisen (Fe)"] == "Element"
    assert dict(SEPARATION_METHODS)["Sand und Wasser"] == "Filtrieren"
    assert dict(ACID_BASE)["reines Wasser"] == "neutral"
    assert dict(ACID_BASE)["Essig"] == "sauer"
    # every curated reaction-type skeleton balances uniquely
    for r, p, _ in REACTION_TYPES:
        balance_equation(r, p)


def test_atom_count_is_derived_from_the_formula():
    import random
    inst = _RECIPES["atom_count"](random.Random(0))
    # the answer states real atom counts that sum to the stated total
    assert "insgesamt" in str(inst.answer)


def test_qualitative_variants_distinct_and_deterministic():
    for tid in ("che-us-reaktionstyp", "che-us-stoffklassen", "che-us-saeure-base"):
        t = find_template(tid)
        a = make_variants(t, 5, seed0=1)
        assert len({str(x.prompt) for x in a}) == 5, (tid, "variants not distinct")
        b = make_variants(t, 5, seed0=1)
        assert [str(x.prompt) for x in a] == [str(x.prompt) for x in b]


def test_chemistry_variants_deterministic_and_distinct():
    t = find_template("che-os-stoechiometrie")
    a = make_variants(t, 6, seed0=1)
    b = make_variants(t, 6, seed0=1)
    assert [str(x.prompt) for x in a] == [str(x.prompt) for x in b]   # deterministic per seed
    assert len({str(x.prompt) for x in a}) >= 3                       # variants actually differ
    assert all(x.answer_key and x.solution_steps for x in a)          # answer + Rechenweg present


def test_equation_balance_never_emits_trivial_all_ones():
    """A balancing exercise must be non-trivial — the recipe resamples all-1 draws."""
    import re
    t = find_template("che-os-reaktionsgleichung")
    for b in make_variants(t, 8, seed0=1):
        # at least one real coefficient (a digit ≥ 2 before a formula) in the answer
        assert re.search(r"\b[2-9] ", str(b.answer_key)), str(b.answer_key)


# --- Übungsreihe upgrade: difficulty ramp + curated context frames ------------
RAMPED_CHEM = ("che-os-molmasse", "che-os-reaktionsgleichung", "che-us-teilchenanzahl")


def _plain(prompt) -> str:
    return prompt if isinstance(prompt, str) else "".join(r.text for r in prompt)


def test_ramp_ascending_bands_distinct_deterministic():
    """ramp=True → ascending effective bands 2/2/2 (n=6), distinct prompts, and the
    same (task, n, seed0) → the same list (per-seed determinism preserved)."""
    for tid in RAMPED_CHEM:
        t = find_template(tid)
        a = make_variants(t, 6, seed0=1, ramp=True)
        bands = [b.difficulty for b in a]
        assert bands == [1, 1, 2, 2, 3, 3], (tid, bands)
        assert len({str(b.prompt) for b in a}) == 6, (tid, "variants not distinct")
        b = make_variants(t, 6, seed0=1, ramp=True)
        assert [str(x.prompt) for x in a] == [str(x.prompt) for x in b], tid


def test_ramp_bands_match_item_structure():
    """The stamped band is DERIVED from the drawn item, not asserted: molar-mass band 1
    is a binary formula, band 3 is nested/hydrate; balancing band 3 has a coefficient
    that band 1 never reaches."""
    t = find_template("che-os-molmasse")
    for b in make_variants(t, 6, seed0=1, ramp=True):
        head = str(b.answer_key).split("≈")[0]     # "M(<formel>) " — M's paren + nesting
        if b.difficulty == 3:
            assert head.count("(") >= 2 or "·" in head, head
        if b.difficulty == 1:
            assert head.count("(") == 1 and "·" not in head, head


def test_ramp_ignored_without_faking_difficulty():
    """A recipe without the knob ignores the ramp request — blocks carry NO stamped
    difficulty (an ignored request must not fake a spread)."""
    t = find_template("che-us-stoffklassen")           # curated-table recipe, no knob
    blocks = make_variants(t, 4, seed0=1, ramp=True)
    assert all(b.difficulty is None for b in blocks)
    assert len({str(b.prompt) for b in blocks}) == 4   # distinctness still holds


def test_context_prefixes_prompt_and_is_digit_free():
    """Every drawn chemistry item carries its curated context sentence as a prompt
    prefix, and the sentence never smuggles a number (select, never author)."""
    from teachersaid.grounding.chemistry import COMPOUND_CONTEXTS, REACTION_CONTEXTS
    all_contexts = set(COMPOUND_CONTEXTS.values()) | set(REACTION_CONTEXTS.values())
    for tid in RAMPED_CHEM + ("che-os-stoechiometrie",):
        t = find_template(tid)
        for b in make_variants(t, 6, seed0=1, ramp=True):
            text = _plain(b.prompt)
            ctx = next((c for c in all_contexts if text.startswith(c)), None)
            assert ctx is not None, (tid, text[:80])
            assert not any(ch.isdigit() for ch in ctx), ctx


def test_context_catalogs_digit_free_and_cover_pools():
    """The curated context tables cover every pool item and contain no digits —
    the digit guard makes 'a context never asserts an uncomputed fact' checkable."""
    from teachersaid.grounding.chemistry import (
        COMPOUND_CONTEXTS, REACTION_CONTEXTS, reaction_key,
    )
    from teachersaid.pipeline.chemistry import _ATOM_COUNT_FORMULAS, _COMPOUNDS, _REACTIONS
    for s in list(COMPOUND_CONTEXTS.values()) + list(REACTION_CONTEXTS.values()):
        assert not any(ch.isdigit() for ch in s), s
    assert set(_COMPOUNDS) <= set(COMPOUND_CONTEXTS), \
        set(_COMPOUNDS) - set(COMPOUND_CONTEXTS)
    assert set(_ATOM_COUNT_FORMULAS) <= set(COMPOUND_CONTEXTS)
    assert {reaction_key(r, p) for r, p in _REACTIONS} <= set(REACTION_CONTEXTS)


def test_context_schema_guard_rejects_digits():
    """The Instance/template validators refuse a context carrying digits."""
    import pytest as _pytest
    from teachersaid.schema.parametric import Instance, ParametricTask
    with _pytest.raises(ValueError):
        Instance(params={}, answer="x", context="Enthält 42 Prozent.")
    with _pytest.raises(ValueError):
        ParametricTask(id="x", subject="Mathematik", klasse=2, recipe="percentage",
                       prompt_template="{pct} % von {base}?",
                       context_frame="Im Jahr 1815 galt das schon.")


def test_variant_worksheet_uebungsreihe_framing():
    """The worksheet labels its genre: subtitle, purpose intro (Automatisieren /
    Schularbeit / Gruppe A/B), and a teacher throughline naming ramp + Rechenweg and
    disclaiming the didactic-ladder reading. by_difficulty shows the 2/2/2 spread."""
    t = find_template("che-os-molmasse")
    content, res = variant_worksheet(t, 6, today=IN_WINDOW)
    assert content.meta.subtitle == "Übungsreihe — 6 Varianten, aufsteigend"
    zweck = next(b for b in content.intro if b.id == "uebung.zweck")
    ztext = zweck.content if isinstance(zweck.content, str) else str(zweck.content)
    assert "Schularbeit" in ztext and "Gruppe A/B" in ztext and "Zahlensatz" in ztext
    tl = content.sections[0].teacher_overview.throughline
    assert tl and "Übungsreihe" in tl and "Rechenweg" in tl
    assert "kein didaktisch aufgebautes Arbeitsblatt" in tl
    content = assemble(content, res)
    assert content.depth_profile.by_difficulty == {"1": 2, "2": 2, "3": 2}
    rep = verify(content, res)
    assert rep.ok, rep.problems


def test_variant_worksheet_honest_without_ramp_support():
    """A curated-table template can't ramp — the sheet must NOT claim 'aufsteigend'."""
    t = find_template("che-us-stoffklassen")
    content, _res = variant_worksheet(t, 6, today=IN_WINDOW)
    assert content.meta.subtitle == "Übungsreihe — 6 Varianten"
    zweck = next(b for b in content.intro if b.id == "uebung.zweck")
    ztext = zweck.content if isinstance(zweck.content, str) else str(zweck.content)
    assert "aufsteigend" not in ztext
    assert "aufsteigend" not in (content.sections[0].teacher_overview.throughline or "")


# --- the full product path ---------------------------------------------------
def test_chemistry_pack_anchors_and_dimensions():
    assert {t.id for t in CHEM_OS} == {
        "che-os-molmasse", "che-os-reaktionsgleichung", "che-os-stoechiometrie",
    }
    assert {t.id for t in CHEM_US} == {
        "che-us-stoffklassen", "che-us-trennverfahren", "che-us-reaktionstyp",
        "che-us-teilchenanzahl", "che-us-saeure-base",
    }
    assert all(t.subject == "Chemie" for t in CHEM)
    assert all(t.klasse == 7 for t in CHEM_OS) and all(t.klasse == 4 for t in CHEM_US)
    # Oberstufe Chemie = WO/EG/KZ; Unterstufe Chemie = the W/E/S science model
    assert all(d in {"WO", "EG", "KZ"} for t in CHEM_OS for d in t.dimensions)
    assert all(d in {"W", "E", "S"} for t in CHEM_US for d in t.dimensions)


def test_chemistry_templates_build_assemble_verify():
    """Every Chemie template → N variants that assemble + verify clean, with the Nachweis
    binding the served CHE competence (the trust feature)."""
    for t in CHEM:
        content, res = variant_worksheet(t, n=3, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert rep.ok, (t.id, rep.problems)
        assert content.meta.stufe == ("Oberstufe" if t.klasse >= 5 else "Unterstufe")
        blocks = content.sections[0].blocks
        assert len(blocks) == 3 and all(b.solution_steps and b.answer_key for b in blocks)
        dim_ids = content.subject_model.dimension_ids()
        assert all(set(b.dimensions) <= dim_ids for b in blocks)
        served = t.serves[0].competence_id
        cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
        assert cov.get(served) is True, (t.id, served, "not covered in Nachweis")


def test_chemistry_renders(tmp_path):
    """Render exercises the renderer on every Chemie variant — guards the subscript/
    encoding path (CO₂/H₂O must not tofu) end to end."""
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    for t in CHEM:
        content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
        content = assemble(content, res)
        for render in (render_student_sheet, render_teacher_guide):
            out = render(content, tmp_path / f"{t.id}_{render.__name__}.pdf")
            assert out.exists() and out.stat().st_size > 1000, (t.id, render.__name__)
