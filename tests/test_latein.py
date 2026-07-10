"""Latein track — the empirical SRDP operator catalog + the Wortbildung engine.

Locks the load-bearing invariants: (1) the LATEIN operator catalog covers exactly the
operator set harvested from the 41-exam Klausur corpus (Documents/matura-latein-coverage.md)
and routes for the LAT code — which is the canonical code in BOTH Stufen — instead of the
generic DEFAULT palette; (2) the curated Wortbildung grounding is structurally sound —
every entry's attested surface form IS its (assimilated) prefix + base surface, so no
invented Latin can hide in the table; (3) recipe answers are READ from the curated table
(fixed-seed ground truth), variants are distinct + deterministic; (4) the full product
path — every Latein template assembles, verifies clean and renders (the render test
guards the „…“-quote/Umlaut path exactly as the chemistry render test guards subscripts).
"""

from __future__ import annotations

import random
import re
from datetime import date

from teachersaid.grounding import lehrplan_store as ls
from teachersaid.grounding import operators as ops
from teachersaid.grounding.latin import BASE_VERBS, DERIVED_WORDS, PREFIXES
from teachersaid.library.templates import PARAM_TEMPLATES, find_template, variant_worksheet
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.parametrize import _RECIPES, make_variants
from teachersaid.pipeline.verify import verify

IN_WINDOW = date(2026, 3, 1)
LAT_TEMPLATES = [t for t in PARAM_TEMPLATES if t.id.startswith("lat-us-")]

# The empirically-harvested operator set (Documents/matura-latein-coverage.md): the ÜT
# operator + the 9 absent-from-any-catalog IT operators + the 5 generic-palette hits.
UT_OPERATOR = "übersetzen"
NOVEL_9 = ["finden", "trennen", "zuordnen", "ergänzen", "verfassen", "gliedern",
           "ankreuzen", "belegen", "auseinandersetzen"]
GENERIC_5 = ["angeben", "vergleichen", "analysieren", "benennen", "beschreiben"]


def _has_form(verb: str) -> bool:
    """The catalog carries the verb — as the whole form or with a qualifier
    ("trennen (Wortbildung)")."""
    return any(o.forms == verb or o.forms.startswith(verb + " (") for o in ops.LATEIN)


# --- operator catalog --------------------------------------------------------
def test_latein_catalog_complete_and_well_formed():
    assert len(ops.LATEIN) == 15                     # ÜT + 14 observed IT operators
    for verb in [UT_OPERATOR] + NOVEL_9 + GENERIC_5:
        assert _has_form(verb), verb
    for o in ops.LATEIN:
        assert isinstance(o, ops.Operator) and o.forms
        # empirical catalog: every definition is authored-then-vetted → must exist
        assert o.definition, o.forms
        assert o.afb and all(b in (1, 2, 3) for b in o.afb), o.forms
    assert ops.is_banded(ops.LATEIN)


def test_latein_routing_both_stufen():
    """LAT routes to LATEIN, not DEFAULT (mirrors the AMT wiring test). One entry covers
    both Stufen because 'Latein' resolves to the canonical code LAT in BOTH catalogs."""
    for subject in ("Latein", "latein", "LAT"):
        assert ops.operator_set(subject) is ops.LATEIN, subject
        assert ops.is_authoritative(subject), subject
    assert ls._code_for("Latein", "Unterstufe") == "LAT"
    assert ls._code_for("Latein", "Oberstufe") == "LAT"
    assert ops.operator_set("Latein") is not ops.DEFAULT


def test_latein_brief_shape():
    brief = ops.format_operators_brief("Latein")
    assert "pending" not in brief                    # no longer the flagged fallback
    assert "übersetzen" in brief and "trennen (Wortbildung)" in brief
    assert all(ops.AFB_LABEL[b] in brief for b in (1, 2, 3))


def test_latein_operators_for_level():
    reflexion = [o.forms for o in ops.operators_for_level("evaluate", "Latein")]
    assert "auseinandersetzen" in reflexion and "verfassen" in reflexion
    repro = [o.forms for o in ops.operators_for_level("remember", "Latein")]
    assert "finden" in repro and "ankreuzen (Auswahl)" in repro


# --- Wortbildung grounding (the curated table) --------------------------------
def test_wortbildung_entries_structurally_sound():
    assert 25 <= len(DERIVED_WORDS) <= 40
    words = [e.word for e in DERIVED_WORDS]
    assert len(set(words)) == len(words)             # every word curated once
    pairs = {(e.prefix, e.base) for e in DERIVED_WORDS}
    assert len(pairs) == len(DERIVED_WORDS)          # one curated word per combination
    for e in DERIVED_WORDS:
        assert e.prefix in PREFIXES and e.base in BASE_VERBS, e.word
        assert e.meaning, e.word
        # the correct-by-curation identity: the attested surface form IS the
        # (assimilated) prefix + the base surface — no invented Latin can hide
        assert e.word == e.surface_prefix() + e.surface_base(), e.word
        assert e.word.startswith(e.surface_prefix()), e.word


def test_wortbildung_assimilation_recorded():
    by_word = {e.word: e for e in DERIVED_WORDS}
    assert by_word["auferre"].prefix == "ab-" and by_word["auferre"].surface_prefix() == "au"
    assert by_word["amittere"].surface_prefix() == "a"
    assert by_word["accipere"].surface_prefix() == "ac"
    assert by_word["accipere"].surface_base() == "cipere"     # capere → -cipere
    assert by_word["redire"].surface_prefix() == "red"        # re- → red- vor Vokal
    assert by_word["succedere"].surface_prefix() == "suc"     # sub- → suc- vor c
    assert by_word["componere"].surface_prefix() == "com"     # con- → com- vor p
    # non-compositional school meanings are flagged (excluded from the erschließen ask)
    assert by_word["amittere"].transparent is False           # verlieren ≠ „wegschicken“
    assert by_word["decipere"].transparent is False           # täuschen ≠ „wegfangen“
    assert by_word["abducere"].transparent is True


# --- recipes: answers come FROM the table -------------------------------------
def test_latin_recipes_registered():
    assert {"wortbildung_decompose", "wortbildung_meaning",
            "wortbildung_matching"} <= set(_RECIPES)


def test_decompose_answer_read_from_table():
    for seed in range(8):
        inst = _RECIPES["wortbildung_decompose"](random.Random(seed))
        e = next(x for x in DERIVED_WORDS if x.word == inst.params["wort"])
        answer = str(inst.answer)
        assert e.meaning in answer and e.prefix in answer and e.base in answer
        assert inst.steps                                     # worked decomposition


def test_meaning_recipe_transparent_only_and_reads_table():
    by_word = {e.word: e for e in DERIVED_WORDS}
    for seed in range(10):
        inst = _RECIPES["wortbildung_meaning"](random.Random(seed))
        word = str(inst.answer).split(" — ")[0]
        e = by_word[word]                                     # the word IS a curated entry
        assert e.transparent                                  # never a trick question
        assert e.meaning in str(inst.answer)
        assert inst.params["basis"].startswith(e.base)
        assert inst.params["praefix"].startswith(e.prefix)


def test_matching_pairing_is_the_curated_truth():
    by_word = {e.word: e.meaning for e in DERIVED_WORDS}
    for seed in (0, 1, 5):
        inst = _RECIPES["wortbildung_matching"](random.Random(seed))
        left, right = inst.params["liste"].split(" — ", 1)
        words = re.findall(r"\d\)\s+(\S+)", left)
        meanings = dict(re.findall(r"([A-H])\)\s(.+?)(?=\s{3}|$)", right))
        pairing = dict(re.findall(r"(\d)\s*→\s*([A-H])", str(inst.answer)))
        assert len(words) == 4 and len(meanings) == 4 and len(pairing) == 4
        for i, w in enumerate(words, start=1):
            # the answer key maps every word to exactly its curated meaning
            assert meanings[pairing[str(i)]] == by_word[w], (w, seed)


def test_variants_distinct_and_deterministic():
    for tid in ("lat-us-wortbildung", "lat-us-wortbildung-bedeutung",
                "lat-us-wortbildung-zuordnung"):
        t = find_template(tid)
        a = make_variants(t, 5, seed0=1)
        assert len({str(x.prompt) for x in a}) == 5, (tid, "variants not distinct")
        b = make_variants(t, 5, seed0=1)
        assert [str(x.prompt) for x in a] == [str(x.prompt) for x in b]
        assert all(x.answer_key and x.solution_steps for x in a)


# --- the full product path -----------------------------------------------------
def test_latein_pack_anchors_and_dimensions():
    assert {t.id for t in LAT_TEMPLATES} == {
        "lat-us-wortbildung", "lat-us-wortbildung-bedeutung", "lat-us-wortbildung-zuordnung",
    }
    assert all(t.subject == "Latein" for t in LAT_TEMPLATES)
    assert all(t.klasse in (3, 4) for t in LAT_TEMPLATES)     # Latein starts in the 3. Kl.
    assert all(d in {"SPR", "INH"} for t in LAT_TEMPLATES for d in t.dimensions)
    assert all(c.competence_id.startswith("LAT.US.")
               for t in LAT_TEMPLATES for c in t.serves)


def test_latein_templates_build_assemble_verify():
    """Every Latein template → N variants that assemble + verify clean, with the Nachweis
    binding the served LAT competence (the trust feature)."""
    for t in LAT_TEMPLATES:
        content, res = variant_worksheet(t, n=3, today=IN_WINDOW)
        content = assemble(content, res)
        rep = verify(content, res)
        assert rep.ok, (t.id, rep.problems)
        assert content.meta.stufe == "Unterstufe"
        blocks = content.sections[0].blocks
        assert len(blocks) == 3 and all(b.answer_key and b.solution_steps for b in blocks)
        dim_ids = content.subject_model.dimension_ids()
        assert all(set(b.dimensions) <= dim_ids for b in blocks)
        served = t.serves[0].competence_id
        cov = {c.competence_id: c.covered for c in content.nachweis.competence_coverage}
        assert cov.get(served) is True, (t.id, served, "not covered in Nachweis")


def test_latein_renders(tmp_path):
    """Render exercises the renderer on every Latein variant — guards the typographic
    quotes („…“) + Umlaut path end to end (assemble/verify don't render)."""
    from teachersaid.rendering.student_sheet import render_student_sheet
    from teachersaid.rendering.teacher_guide import render_teacher_guide
    for t in LAT_TEMPLATES:
        content, res = variant_worksheet(t, n=2, today=IN_WINDOW)
        content = assemble(content, res)
        for render in (render_student_sheet, render_teacher_guide):
            out = render(content, tmp_path / f"{t.id}_{render.__name__}.pdf")
            assert out.exists() and out.stat().st_size > 1000, (t.id, render.__name__)
