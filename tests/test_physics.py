"""Physics parametric engine — the physics twin of the sympy maths + chemistry recipes.

Locks the load-bearing invariants: the curated constants/densities (select-never-author),
the recipes computing every answer FROM sympy.physics.units (so it is correct by
construction AND dimensionally verified), per-seed determinism, the `Unsuitable`
resampling discipline, and the full product path — every phy-* template → N distinct
correct variants that assemble + verify clean + render (the render test catches the
mathtext-subset slips the way the maths/chemistry render tests do — e.g. \\tfrac).

The headline feature gets its own NEGATIVE test: `_assert_dimension` must actually FAIL on
a deliberately wrong-unit computation (proving the guard guards, not that it is vacuous).
"""

from __future__ import annotations

import random
from datetime import date

import pytest
from sympy import Rational
from sympy.physics import units as u

from teachersaid.grounding.physics import (
    AIR_DENSITY, MATERIAL_DENSITIES, STANDARD_GRAVITY, density_material_for,
)
from teachersaid.pipeline import physics as phys
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.parametrize import _RECIPES, make_variants
from teachersaid.pipeline.verify import verify
from teachersaid.library.templates import PARAM_TEMPLATES, find_template, variant_worksheet

IN_WINDOW = date(2026, 3, 1)
# The open-answer physics pack (the dimensionally-verified recipes). The multiple_choice
# misconception templates (phy-*-mc, roadmap A3) are covered in test_misconceptions.py and
# excluded here so this pack's set/answer assertions stay about the open-answer recipes.
PHY = [t for t in PARAM_TEMPLATES if t.id.startswith("phy-") and not t.id.endswith("-mc")]
PHY_US = [t for t in PHY if t.id.startswith("phy-us-")]
PHY_OS = [t for t in PHY if t.id.startswith("phy-os-")]

RECIPES = ["uniform_motion", "density", "ohm", "resistors", "lever", "energy_power"]


def _draw(rid: str, seed: int):
    """Draw one Instance from a recipe with the engine's own resampling (skip Unsuitable)."""
    rng = random.Random(seed)
    for _ in range(500):
        try:
            return _RECIPES[rid](rng)
        except phys.Unsuitable:
            continue
    raise AssertionError(f"{rid}: no valid instance in 500 tries")


def _num_de(s: str) -> float:
    """Parse a German-formatted number ('12,5' → 12.5)."""
    return float(s.replace(".", "").replace(",", "."))


# ============================================================================
# the headline guard: dimensional verification actually verifies
# ============================================================================
def test_recipes_registered():
    assert set(RECIPES) <= set(_RECIPES)


def test_assert_dimension_accepts_correct_dimension():
    """A quantity with the right physical dimension passes (regardless of surface form:
    R·I reduces to volt through the SI dimension system)."""
    phys._assert_dimension(220 * u.ohm * Rational(1, 2) * u.ampere, u.volt)
    phys._assert_dimension(100 * u.meter / (8 * u.second), u.meter / u.second)
    phys._assert_dimension(2 * u.kilogram / (Rational(1, 1000) * u.meter**3),
                           u.kilogram / u.meter**3)


def test_assert_dimension_rejects_wrong_unit():
    """The guard MUST raise on a genuine unit-category error — the proof it guards.
    A power is not an energy; s·t is not a velocity; U/R is a current, not a resistance."""
    with pytest.raises(phys.DimensionError):
        phys._assert_dimension(60 * u.watt, u.joule)             # forgot ·t
    with pytest.raises(phys.DimensionError):
        phys._assert_dimension(100 * u.meter * 8 * u.second, u.meter / u.second)  # ·t not /t
    with pytest.raises(phys.DimensionError):
        phys._assert_dimension(10 * u.volt / (2 * u.ohm), u.ohm)  # that's a current


def test_every_recipe_answer_carries_verified_dimension():
    """Every drawn instance ran its `_assert_dimension` internally (it would have raised
    otherwise) — so reaching an Instance at all is the dimensional guarantee. Smoke a
    spread of seeds per recipe to exercise all solve-for branches."""
    for rid in RECIPES:
        for seed in range(1, 25):
            inst = _draw(rid, seed)
            assert inst.answer and inst.steps                    # complete item


# ============================================================================
# curated constants + densities (select, never author)
# ============================================================================
def test_standard_gravity_value():
    assert STANDARD_GRAVITY == 9.80665                            # defined value (CGPM 1901)


def test_material_densities_have_source_and_are_ordered_sane():
    from teachersaid.grounding.physics import DENSITY_SOURCE, GRAVITY_SOURCE
    assert DENSITY_SOURCE.attribution and DENSITY_SOURCE.publisher
    assert GRAVITY_SOURCE.attribution
    # water is the 1000 kg/m³ reference; cork floats, lead is heaviest solid here
    assert MATERIAL_DENSITIES["Wasser"] == 1000.0
    assert MATERIAL_DENSITIES["Kork"] < MATERIAL_DENSITIES["Wasser"] < MATERIAL_DENSITIES["Blei"]
    assert AIR_DENSITY < MATERIAL_DENSITIES["Kork"]              # a gas is far lighter


def test_density_reverse_lookup_is_curated_and_unambiguous():
    """Each curated density maps back to its own material within tolerance (the
    'welcher Stoff?' answer is the curated truth, never invented)."""
    for name, rho in MATERIAL_DENSITIES.items():
        assert density_material_for(rho) == name
    assert density_material_for(5000.0) is None                  # nothing curated near 5,0 g/cm³


# ============================================================================
# answers verified INDEPENDENTLY (recompute in the test, not via the recipe)
# ============================================================================
def test_uniform_motion_answer_is_correct():
    """Recompute v/s/t from the two givens in the prompt and match the answer (the physics
    must close: v·t = s), independently of the recipe's own arithmetic."""
    import re
    t = find_template("phy-us-bewegung")
    for b in make_variants(t, 12, seed0=1):
        text = "".join(r.text for r in b.prompt) if not isinstance(b.prompt, str) else b.prompt
        ans = str(b.answer_key)
        if ans.startswith("v ="):                                 # given: t (in ... s), s (Strecke)
            t_s = _num_de(re.search(r"in ([\d,]+) s", text).group(1))
            s_m = _num_de(re.search(r"Strecke von ([\d,]+) m", text).group(1))
            v = _num_de(re.search(r"v = ([\d,]+)", ans).group(1))
            assert v == pytest.approx(s_m / t_s, rel=1e-6)
        elif ans.startswith("s ="):                               # given: v, t (dauert ... s)
            v = _num_de(re.search(r"beträgt ([\d,]+) m/s", text).group(1))
            t_s = _num_de(re.search(r"dauert ([\d,]+) s", text).group(1))
            s = _num_de(re.search(r"s = ([\d,]+)", ans).group(1))
            assert s == pytest.approx(v * t_s, rel=1e-6)
        else:                                                     # t: given v, s (Strecke)
            v = _num_de(re.search(r"beträgt ([\d,]+) m/s", text).group(1))
            s_m = _num_de(re.search(r"Strecke von ([\d,]+) m", text).group(1))
            t_s = _num_de(re.search(r"t = ([\d,]+)", ans).group(1))
            assert t_s == pytest.approx(s_m / v, rel=1e-6)


def test_ohm_answer_is_correct():
    """U=R·I closes for every variant, recomputed from the two given quantities."""
    import re
    t = find_template("phy-us-ohm")
    for b in make_variants(t, 15, seed0=1):
        text = "".join(r.text for r in b.prompt) if not isinstance(b.prompt, str) else b.prompt
        ans = str(b.answer_key)
        if ans.startswith("U ="):
            R = _num_de(re.search(r"Widerstand von ([\d,]+) Ω", text).group(1))
            I = _num_de(re.search(r"Strom von ([\d,]+) A", text).group(1))
            U = _num_de(re.search(r"U = ([\d,]+)", ans).group(1))
            assert U == pytest.approx(R * I, rel=1e-6)
        elif ans.startswith("R ="):
            U = _num_de(re.search(r"Spannung ([\d,]+) V", text).group(1))
            I = _num_de(re.search(r"Strom\D*von ([\d,]+) A", text).group(1))
            R = _num_de(re.search(r"R = ([\d,]+)", ans).group(1))
            assert R == pytest.approx(U / I, rel=1e-6)
        else:  # I
            U = _num_de(re.search(r"Spannung ([\d,]+) V", text).group(1))
            R = _num_de(re.search(r"Widerstand von ([\d,]+) Ω", text).group(1))
            I = _num_de(re.search(r"I = ([\d,]+)", ans).group(1))
            assert I == pytest.approx(U / R, rel=1e-6)


def test_lever_answer_satisfies_the_law():
    """F₁·a₁ = F₂·a₂ holds for the completed set (recompute the fourth from the answer)."""
    import re
    t = find_template("phy-us-hebel")
    for b in make_variants(t, 15, seed0=1):
        text = "".join(r.text for r in b.prompt) if not isinstance(b.prompt, str) else b.prompt
        ans = str(b.answer_key)
        vals = {}
        for key, pat in (("F1", r"F₁ = ([\d,]+)"), ("a1", r"a₁ = ([\d,]+)"),
                         ("F2", r"F₂ = ([\d,]+)"), ("a2", r"a₂ = ([\d,]+)")):
            m = re.search(pat, text) or re.search(pat, ans)
            assert m, (key, text, ans)
            vals[key] = _num_de(m.group(1))
        assert vals["F1"] * vals["a1"] == pytest.approx(vals["F2"] * vals["a2"], rel=1e-6)


def test_resistors_series_and_parallel_correct():
    """Series = sum; parallel = harmonic. Recompute from the listed resistor values."""
    import re
    t = find_template("phy-os-ersatzwiderstand")
    saw_series = saw_parallel = False
    for b in make_variants(t, 30, seed0=1):
        text = "".join(r.text for r in b.prompt) if not isinstance(b.prompt, str) else b.prompt
        ans = str(b.answer_key)
        vals = [float(x) for x in re.findall(r"(\d+) Ω", text)]
        rges = _num_de(re.search(r"R_ges = ([\d,]+) Ω", ans).group(1))
        if "Reihenschaltung" in text:
            saw_series = True
            assert rges == pytest.approx(sum(vals), rel=1e-6)
        else:
            saw_parallel = True
            expected = 1.0 / sum(1.0 / v for v in vals)
            assert rges == pytest.approx(expected, rel=1e-6)
    assert saw_series and saw_parallel                            # both modes actually occur


def test_density_answer_and_material_identification():
    """ρ = m/V closes; the material-ID variant names the curated stuff whose density matches."""
    import re
    t = find_template("phy-os-dichte")
    saw_material = False
    for b in make_variants(t, 30, seed0=1):
        text = "".join(r.text for r in b.prompt) if not isinstance(b.prompt, str) else b.prompt
        ans = str(b.answer_key)
        if "→" in ans:                                            # material-identification variant
            saw_material = True
            m = _num_de(re.search(r"Masse ([\d,]+) g", text).group(1))
            V = _num_de(re.search(r"Volumen ([\d,]+) cm³", text).group(1))
            rho = _num_de(re.search(r"ρ = ([\d,]+) g/cm³", ans).group(1))
            assert rho == pytest.approx(m / V, rel=1e-3)
            name = ans.split("→")[1].strip()
            assert name in MATERIAL_DENSITIES
            # the named material's density matches the computed one (curated truth)
            assert density_material_for(rho * 1000) == name       # g/cm³ → kg/m³
    assert saw_material


def test_energy_power_work_and_epot_correct():
    """W = P·t (J or kWh) and E_pot = m·g·h close, recomputed independently."""
    import re
    t = find_template("phy-us-arbeit-leistung")
    saw_j = saw_kwh = saw_epot = False
    for b in make_variants(t, 30, seed0=1):
        text = "".join(r.text for r in b.prompt) if not isinstance(b.prompt, str) else b.prompt
        ans = str(b.answer_key)
        if "kWh" in ans:
            saw_kwh = True
            P = _num_de(re.search(r"Leistung ([\d,]+) kW", text).group(1))
            h = _num_de(re.search(r"läuft ([\d,]+) h", text).group(1))
            W = _num_de(re.search(r"W = ([\d,]+) kWh", ans).group(1))
            assert W == pytest.approx(P * h, rel=1e-6)
        elif ans.startswith("W ="):
            saw_j = True
            P = _num_de(re.search(r"Leistung ([\d,]+) W", text).group(1))
            sec = _num_de(re.search(r"([\d,]+) s lang", text).group(1))
            W = _num_de(re.search(r"W = ([\d,]+) J", ans).group(1))
            assert W == pytest.approx(P * sec, rel=1e-6)
        else:  # E_pot
            saw_epot = True
            m = _num_de(re.search(r"Masse beträgt ([\d,]+) kg", text).group(1))
            h = _num_de(re.search(r"Höhe ([\d,]+) m", text).group(1))
            E = _num_de(re.search(r"E_pot ≈ ([\d,]+) J", ans).group(1))
            assert E == pytest.approx(m * STANDARD_GRAVITY * h, rel=1e-3)
    assert saw_j and saw_kwh and saw_epot


# ============================================================================
# determinism + Unsuitable resampling + distinctness
# ============================================================================
def test_recipes_deterministic_per_seed():
    for rid in RECIPES:
        for seed in (1, 7, 42):
            a = _draw(rid, seed)
            b = _draw(rid, seed)
            assert str(a.answer) == str(b.answer) and a.params == b.params


def test_unsuitable_resampling_yields_valid_instances():
    """Recipes that raise `Unsuitable` on ugly draws (density, resistors-parallel, lever)
    still produce a valid instance for every seed — the engine resamples."""
    for rid in ("density", "resistors", "lever"):
        for seed in range(1, 40):
            inst = _draw(rid, seed)                                # would raise if it never resolved
            assert inst.answer


def test_variants_distinct_across_seeds():
    """make_variants prefers distinct prompts; each recipe's draw space is wide enough."""
    for t in PHY:
        vs = make_variants(t, 5, seed0=1)
        assert len({str(b.prompt) for b in vs}) == 5, (t.id, "variants not distinct")


def test_variants_deterministic():
    for t in PHY:
        a = make_variants(t, 6, seed0=1)
        b = make_variants(t, 6, seed0=1)
        assert [str(x.prompt) for x in a] == [str(x.prompt) for x in b], t.id


# ============================================================================
# the full product path — anchors, assemble, verify, render
# ============================================================================
def test_physics_pack_anchors_and_dimensions():
    assert {t.id for t in PHY_US} == {
        "phy-us-bewegung", "phy-us-ohm", "phy-us-hebel", "phy-us-arbeit-leistung",
    }
    assert {t.id for t in PHY_OS} == {
        "phy-os-dichte", "phy-os-ersatzwiderstand", "phy-os-arbeit-leistung",
    }
    assert all(t.subject == "Physik" for t in PHY)
    # US physics starts in Kl. 2; the pack anchors in Kl. 3 (Mechanik/Elektrizität/Energie)
    assert all(t.klasse == 3 for t in PHY_US)
    assert all(t.klasse in (5, 6) for t in PHY_OS)
    # Physik = the W/E/S science model (Unterstufe and Oberstufe share it)
    assert all(d in {"W", "E", "S"} for t in PHY for d in t.dimensions)


def test_physics_templates_build_assemble_verify():
    """Every Physik template → N variants that assemble + verify clean, with the Nachweis
    binding the served PHY competence (the trust feature)."""
    for t in PHY:
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


def test_all_templates_still_instantiate_and_verify_clean():
    """Adding the physics pack must not break the existing maths/chemistry templates —
    the whole PARAM_TEMPLATES set stays verify-clean."""
    for t in PARAM_TEMPLATES:
        content, res = variant_worksheet(t, 4, today=IN_WINDOW)
        assemble(content, res)
        report = verify(content, res)
        assert not report.problems, f"{t.id}: {report.problems}"


def test_physics_renders(tmp_path):
    """Render exercises the renderer on every Physik variant — guards the math/unit path
    end to end (the teacher guide renders the SolutionStep exprs; \\tfrac would tofu/raise
    here, which is how that slip was caught during development)."""
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    for t in PHY:
        content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
        content = assemble(content, res)
        for render in (render_student_sheet, render_teacher_guide):
            out = render(content, tmp_path / f"{t.id}_{render.__name__}.pdf")
            assert out.exists() and out.stat().st_size > 1000, (t.id, render.__name__)
