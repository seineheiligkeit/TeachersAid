"""P1 Tiefenregler: pure derivations over one parametric master."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library.templates import PARAM_TEMPLATES, find_template, variant_worksheet
from teachersaid.pipeline.parametrize import instantiate
from teachersaid.pipeline.scaffold import _numeric_values
from teachersaid.schema.mixer import Geruest, Offenheit, ParametricMixerProfile, Textlast
from teachersaid.schema.richtext import plain_text


TODAY = date(2026, 3, 1)


def _tasks(content):
    return [b for b in content.iter_blocks() if b.role == "task"]


def test_umfang_derives_count_and_lint_without_changing_coverage():
    template = find_template("mat-prozent")
    compact, _ = variant_worksheet(
        template, 6, today=TODAY,
        mixer_profile=ParametricMixerProfile(umfang="kompakt"),
    )
    extended, _ = variant_worksheet(
        template, 6, today=TODAY,
        mixer_profile=ParametricMixerProfile(umfang="erweitert"),
    )
    assert len(_tasks(compact)) == 4
    assert len(_tasks(extended)) == 8
    assert compact.mixer_lint.passed and extended.mixer_lint.passed
    movement = compact.mixer_lint.movements[0]
    assert movement.fader == "umfang" and movement.low_value == 4
    assert movement.high_value == 8 and movement.coverage_intact
    assert compact.mixer_lint.output.coverage_ids == extended.mixer_lint.output.coverage_ids


def test_tiefe_uses_computed_solution_paths_and_moves_afb_and_c4():
    template = find_template("mat-prozent")
    practice, _ = variant_worksheet(
        template, 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(tiefe="ueben"),
    )
    deep, _ = variant_worksheet(
        template, 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(tiefe="strategien_vergleichen"),
    )
    p, d = _tasks(practice)[0], _tasks(deep)[0]
    assert str(p.prompt) != str(d.prompt)
    assert "Dreisatz" in str(d.prompt) and "Prozentoperator" in str(d.prompt)
    assert d.cognitive_level == "evaluate" and d.est_minutes > p.est_minutes
    assert d.response.mode == "lines" and d.response.n >= 6
    movement = next(m for m in deep.mixer_lint.movements if m.fader == "tiefe")
    assert movement.low_value == 2 and movement.high_value == 3
    assert deep.mixer_lint.output.c4_mean > practice.mixer_lint.output.c4_mean
    assert movement.coverage_intact


def test_abstraktion_removes_only_student_figures_from_same_tasks():
    template = find_template("mat-pythagoras")
    visual, _ = variant_worksheet(
        template, 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(abstraktion="anschaulich"),
    )
    formal, _ = variant_worksheet(
        template, 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(abstraktion="formal"),
    )
    assert [str(b.prompt) for b in _tasks(visual)] == [str(b.prompt) for b in _tasks(formal)]
    assert len(visual.assets) == 3 and not formal.assets
    assert all(b.asset_refs for b in _tasks(visual))
    assert all(not b.asset_refs for b in _tasks(formal))
    movement = next(m for m in formal.mixer_lint.movements if m.fader == "abstraktion")
    assert movement.low_value == 3 and movement.high_value == 0
    assert movement.coverage_intact


def test_offenheit_reprojects_one_mc_instance_with_clean_open_wording():
    template = find_template("mat-lineare-gleichung-mc")
    closed = instantiate(template, 7, openness=Offenheit.GESCHLOSSEN)
    opened = instantiate(template, 7, openness=Offenheit.OFFEN)
    assert closed.payload.kind == "multiple_choice" and opened.payload is None
    assert opened.kind == "open_response" and opened.response.mode == "lines"
    assert "Welche Lösung ist richtig" not in str(opened.prompt)
    assert "Notiere deinen Rechenweg" in str(opened.prompt)
    assert "(richtig)" in str(closed.answer_key) and "(richtig)" not in str(opened.answer_key)
    assert opened.watch_outs and all(w.startswith("Typischer Fehler:") for w in opened.watch_outs)

    content, _ = variant_worksheet(
        template, 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(offenheit="offen"),
    )
    assert "Multiple Choice" not in content.meta.title
    assert not any(b.id == "uebung.rahmen" for b in content.intro)
    movement = next(m for m in content.mixer_lint.movements if m.fader == "offenheit")
    assert movement.low_value == 3 and movement.high_value == 0
    assert movement.coverage_intact and content.mixer_lint.passed


@pytest.mark.parametrize(
    ("template_id", "profile", "needle"),
    [
        ("mat-lineare-gleichung", {"tiefe": "strategien_vergleichen"}, "solution paths"),
        ("mat-prozent", {"abstraktion": "formal"}, "student figure"),
        ("mat-prozent", {"offenheit": "offen"}, "misconception-backed"),
    ],
)
def test_unsupported_faders_fail_loudly(template_id, profile, needle):
    with pytest.raises(ValueError, match=needle):
        variant_worksheet(
            find_template(template_id), 3, today=TODAY,
            mixer_profile=ParametricMixerProfile(**profile),
        )


def test_profile_is_api_staged_and_stamped_only_on_teacher_pdf(tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.repository import ReviewStore

    item = orch.compose_variants(
        ReviewStore(tmp_path / "store"), "mat-prozent-mc", 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(umfang="kompakt", offenheit="offen"),
    )
    assert item.error is None and item.content.mixer_lint.passed
    assert len(_tasks(item.content)) == 2
    assert item.content.mixer_profile.offenheit == Offenheit.OFFEN

    import fitz
    teacher = "".join(p.get_text() for p in fitz.open(item.artifacts.teacher_pdf))
    student = "".join(p.get_text() for p in fitz.open(item.artifacts.student_pdf))
    assert "Mischpult-Profil" in teacher and "Regler-Lint: bestanden" in teacher
    assert "Mischpult-Profil" not in student


def test_mixed_projection_is_deterministic():
    profile = ParametricMixerProfile(umfang="erweitert", offenheit="offen")
    a, _ = variant_worksheet(
        find_template("mat-prozent-mc"), 4, today=TODAY, seed0=17,
        mixer_profile=profile,
    )
    b, _ = variant_worksheet(
        find_template("mat-prozent-mc"), 4, today=TODAY, seed0=17,
        mixer_profile=profile,
    )
    assert a.model_dump() == b.model_dump()


# --- P2 Gerüst (scaffold) fader ------------------------------------------------
def _scaffold_text(scaffold) -> str:
    parts = []
    if scaffold.first_step:
        parts.append(plain_text(scaffold.first_step))
    if scaffold.hint:
        parts.append(scaffold.hint)
    parts.extend(scaffold.sentence_starters)
    return "  ".join(parts)


def test_geruest_worked_first_step_derives_from_solution_steps_and_moves_lint():
    template = find_template("mat-prozent")
    bare, _ = variant_worksheet(
        template, 4, today=TODAY,
        mixer_profile=ParametricMixerProfile(geruest="ohne"),
    )
    scaffolded, _ = variant_worksheet(
        template, 4, today=TODAY,
        mixer_profile=ParametricMixerProfile(geruest="gestuetzt"),
    )
    # the requested endpoint is honoured on the applied sheet …
    assert all(t.scaffold is None for t in _tasks(bare))
    assert all(t.scaffold and t.scaffold.first_step for t in _tasks(scaffolded))
    # … and the worked step is the recipe's computed step 1 (the Prozentformel), not the answer
    first = plain_text(_tasks(scaffolded)[0].scaffold.first_step)
    assert "Prozentformel" in first and "\\frac{p}{100}" in first
    # the same report carries the geruest endpoint movement, coverage intact, on BOTH endpoints
    for content in (bare, scaffolded):
        mv = next(m for m in content.mixer_lint.movements if m.fader == "geruest")
        assert mv.metric == "scaffolded_tasks"
        assert mv.low_value == 0 and mv.high_value == 4
        assert mv.moved and mv.coverage_intact and content.mixer_lint.passed
    # competence-id set is identical at both endpoints (the lint's invariance rule)
    assert bare.mixer_lint.output.coverage_ids == scaffolded.mixer_lint.output.coverage_ids
    assert scaffolded.mixer_lint.output.scaffolded_tasks == 4


def test_geruest_hint_is_derived_from_the_misconception_catalog():
    from teachersaid.grounding import misconceptions as cat

    block = instantiate(find_template("phy-us-ohm-mc"), 7, scaffold=True)
    s = block.scaffold
    assert s and s.first_step and s.hint
    # the categories are curated catalog names, never authored in the fader
    known = {m.name for m in cat.CATALOG.values()}
    assert s.hint_categories and all(name in known for name in s.hint_categories)
    assert cat.get("formula_not_rearranged").name in s.hint
    # the hint names the trap category, never the answer value
    assert not (_numeric_values(block.answer_key) & _numeric_values(s.hint))


def test_geruest_formulierungshilfen_on_a_prose_response_surface():
    block = instantiate(find_template("phy-us-ohm"), 4, scaffold=True)
    assert block.kind == "open_response"
    assert block.scaffold and len(block.scaffold.sentence_starters) >= 2
    assert all(isinstance(x, str) and x for x in block.scaffold.sentence_starters)
    # a pure calculation gets no Formulierungshilfen (starters are for prose surfaces only)
    calc = instantiate(find_template("mat-prozent"), 4, scaffold=True)
    assert calc.scaffold and not calc.scaffold.sentence_starters


def test_geruest_projection_is_deterministic():
    profile = ParametricMixerProfile(geruest="gestuetzt", offenheit="offen")
    a, _ = variant_worksheet(find_template("phy-us-ohm-mc"), 4, today=TODAY, seed0=17,
                             mixer_profile=profile)
    b, _ = variant_worksheet(find_template("phy-us-ohm-mc"), 4, today=TODAY, seed0=17,
                             mixer_profile=profile)
    assert a.model_dump() == b.model_dump()


def _assert_no_leak(block, template_id, seed):
    text = _scaffold_text(block.scaffold)
    answer = plain_text(block.answer_key)
    answer_vals = _numeric_values(answer)
    if answer_vals:  # numeric answer: no answer VALUE may appear in the scaffold
        assert not (answer_vals & _numeric_values(text)), (template_id, seed, answer)
    else:            # pure-text answer: it never appears verbatim in the scaffold
        norm = " ".join(answer.split()).lower()
        assert norm and norm not in " ".join(text.split()).lower(), (template_id, seed)


def test_geruest_scaffold_never_leaks_the_answer():
    """Load-bearing: no scaffold element ever exposes the computed answer, across the corpus —
    for the closed projection AND the open (Offenheit) projection where it applies."""
    checked = 0
    for template in PARAM_TEMPLATES:
        for seed in range(1, 16):
            for openness in (None, Offenheit.OFFEN):
                try:
                    block = instantiate(template, seed, scaffold=True, openness=openness)
                except (ValueError, RuntimeError):
                    continue  # openness unsupported here, or degenerate draw
                if block.scaffold is None or not block.answer_key:
                    continue
                checked += 1
                _assert_no_leak(block, template.id, seed)
    assert checked > 200


def test_geruest_unsupported_template_fails_loudly():
    # rectangle: its first step already computes the area (the answer), it is a bare
    # calculation (no prose surface) and carries no misconception MC → nothing to scaffold.
    with pytest.raises(ValueError, match="Gerüst"):
        variant_worksheet(find_template("mat-rechteck"), 3, today=TODAY,
                          mixer_profile=ParametricMixerProfile(geruest="gestuetzt"))


def test_geruest_renders_student_teacher_homework_and_stamps_teacher_only(tmp_path):
    import fitz

    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.repository import ReviewStore

    item = orch.compose_variants(
        ReviewStore(tmp_path / "store"), "phy-us-ohm-mc", 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(geruest="gestuetzt"),
    )
    assert item.error is None and item.content.mixer_lint.passed
    assert all(t.scaffold for t in _tasks(item.content))

    texts = {}
    for kind in ("student", "teacher", "homework"):
        doc = fitz.open(getattr(item.artifacts, f"{kind}_pdf"))
        assert doc.page_count >= 1 and doc[0].get_pixmap().width > 0  # builds + rasterises
        texts[kind] = "".join(p.get_text() for p in doc)

    # the scaffold is student-facing: it reaches the student AND homework sheet
    assert "Hilfestellung" in texts["student"] and "Hilfestellung" in texts["homework"]
    assert "hier passieren oft Fehler" in texts["student"]
    # the teacher guide NAMES what the class received and stamps the profile teacher-only
    assert "Gerüst (Schülerhilfe)" in texts["teacher"]
    assert "Mischpult-Profil" in texts["teacher"] and "Mischpult-Profil" not in texts["student"]
    assert "Hilfestellung" not in texts["teacher"]


# --- P3 Textlast (simplified prose twin + glosses) fader -----------------------
def test_textlast_selects_the_twin_preserves_facts_and_moves_wstf():
    template = find_template("fin-lohnzettel")
    # per-seed: einfach SELECTS the curated twin (different register) but the SAME instance
    # (same computed answer, serves, minutes) — a selection, never a fact-changing rewrite.
    voll_i = instantiate(template, 3, textlast="voll")
    einfach_i = instantiate(template, 3, textlast="einfach")
    assert str(voll_i.prompt) != str(einfach_i.prompt)
    assert "Steuerbemessungsgrundlage" in plain_text(voll_i.prompt)
    assert "Steuerbemessungsgrundlage" not in plain_text(einfach_i.prompt)
    assert plain_text(voll_i.answer_key) == plain_text(einfach_i.answer_key)   # fact preserved
    assert voll_i.serves == einfach_i.serves and voll_i.est_minutes == einfach_i.est_minutes

    voll, _ = variant_worksheet(template, 4, today=TODAY,
                                mixer_profile=ParametricMixerProfile(textlast="voll"))
    einfach, _ = variant_worksheet(template, 4, today=TODAY,
                                   mixer_profile=ParametricMixerProfile(textlast="einfach"))
    # the WSTF movement joins the SAME report, coverage intact, on BOTH endpoints
    for content in (voll, einfach):
        mv = next(m for m in content.mixer_lint.movements if m.fader == "textlast")
        assert mv.metric == "wstf"
        assert mv.high_value < mv.low_value          # einfach strictly lowers the Schulstufe
        assert mv.moved and mv.coverage_intact and content.mixer_lint.passed
    assert einfach.mixer_lint.output.wstf < voll.mixer_lint.output.wstf
    # the Wortschatz is SELECTED onto the einfach worksheet only (student-facing aid)
    assert einfach.glossary and not voll.glossary
    assert any(g.term == "Sozialversicherung" for g in einfach.glossary)


def test_textlast_capability_rejected_without_a_twin():
    # mat-dreisatz carries no approved twin → the fader must HARD-FAIL, never a no-op knob,
    # at BOTH endpoints (einfach in _instantiate, voll in the mixer capability check).
    for endpoint in ("einfach", "voll"):
        with pytest.raises(ValueError, match="Textlast"):
            variant_worksheet(find_template("mat-dreisatz"), 3, today=TODAY,
                              mixer_profile=ParametricMixerProfile(textlast=endpoint))


def test_textlast_slot_set_equality_is_validated_at_construction():
    from teachersaid.schema.parametric import ParametricTask

    base = dict(id="probe", subject="Mathematik", klasse=2, recipe="percentage",
                prompt_template="Wie viel sind {pct} % von {base}?")
    with pytest.raises(ValueError, match="slot set"):        # a dropped slot is fact drift
        ParametricTask(**base, prompt_simple="Wie viel sind {pct} Prozent?")
    with pytest.raises(ValueError, match="slot set"):        # an added slot is fact drift
        ParametricTask(**base, prompt_simple="Wie viel sind {pct} % von {base} zu {rate}?")
    ok = ParametricTask(**base, prompt_simple="Wie viel Prozent? {pct} % von {base}.")
    assert ok.prompt_simple is not None                      # equal slot set is accepted


def test_textlast_verbatim_text_is_never_twinned():
    """Structural guard: the fader's WSTF pass excludes verbatim material — a `quoted`-
    provenance task block and a `source_text` block are not ours to simplify."""
    from teachersaid.pipeline import textlast as tl
    from teachersaid.schema.blocks import InfoBlock, TaskBlock
    from teachersaid.schema.provenance import BlockProvenance
    from teachersaid.schema.response import LinesResponse

    prose = "Dies ist ein langer authentischer Satz mit vielen einzelnen Wörtern darin. " * 3
    quoted = TaskBlock(id="q", kind="open_response", prompt=prose,
                       response=LinesResponse(n=2), cognitive_level="apply",
                       provenance=BlockProvenance(expression_origin="quoted"))
    plain = TaskBlock(id="p", kind="open_response", prompt=prose,
                      response=LinesResponse(n=2), cognitive_level="apply")
    source = InfoBlock(id="s", kind="source_text", content=prose)
    assert tl.student_prose([plain]) != "" and tl.measure_wstf([plain]) is not None
    assert tl.student_prose([quoted]) == "" and tl.measure_wstf([quoted]) is None
    assert tl.student_prose([source]) == ""            # an InfoBlock is not a twinnable task


def test_textlast_failing_twin_is_caught_by_the_lint():
    """A curated twin that does NOT lower the WSTF is a bad twin the SME must see — it lands
    in the same report as a non-moving fader and the lint fails (raises)."""
    from teachersaid.pipeline.mixer import make_mixed_variants
    from teachersaid.pipeline.parametrize import make_variants
    from teachersaid.pipeline.textlast import measure_wstf
    from teachersaid.schema.blocks import Serves
    from teachersaid.schema.parametric import ParametricTask

    bad = ParametricTask(
        id="bad-twin", subject="Mathematik", klasse=2, recipe="percentage",
        prompt_template="Berechne den Prozentwert: Wie viel sind {pct} Prozent von dem "
                        "Grundwert {base} Euro in dieser Aufgabe?",
        # a "twin" that is LONGER and harder (higher WSTF), not simpler → must be rejected
        prompt_simple="Bestimme approximativ den prozentualen Anteil {pct} Prozent bezüglich "
                      "des zugrundeliegenden Ausgangsbetrages {base} unter Berücksichtigung "
                      "sämtlicher Verhältnismäßigkeiten und Randbedingungen dieser Aufgabe.",
        serves=[Serves(competence_id="MAT.US.2.ZAH.04", relation="exercises")],
        dimensions=["OPE"], cognitive_level="apply", kind="calculation")
    v = measure_wstf(make_variants(bad, 6, textlast="voll"))
    e = measure_wstf(make_variants(bad, 6, textlast="einfach"))
    assert v is not None and e is not None and e > v        # the twin is HARDER, not simpler
    with pytest.raises(ValueError, match="Regler-Lint|textlast"):
        make_mixed_variants(bad, 6, ParametricMixerProfile(textlast="einfach"))


def test_textlast_keeps_competence_set_and_answers_invariant():
    template = find_template("mat-pythagoras")
    voll, _ = variant_worksheet(template, 5, today=TODAY,
                                mixer_profile=ParametricMixerProfile(textlast="voll"))
    einfach, _ = variant_worksheet(template, 5, today=TODAY,
                                   mixer_profile=ParametricMixerProfile(textlast="einfach"))
    assert voll.mixer_lint.output.coverage_ids == einfach.mixer_lint.output.coverage_ids
    assert einfach.mixer_lint.output.coverage_ids == ["MAT.US.4.FIG.01"]
    for b in _tasks(einfach):                         # per-task serves untouched
        assert [s.competence_id for s in b.serves] == ["MAT.US.4.FIG.01"]
    for seed in range(1, 8):                          # same seed → same computed answer
        assert (plain_text(instantiate(template, seed, textlast="voll").answer_key)
                == plain_text(instantiate(template, seed, textlast="einfach").answer_key))


def test_textlast_twin_and_glosses_are_answer_free():
    """No-leak: a curated gloss is term-definitional (digit-free, so it cannot carry a
    per-variant numeric answer) and the twin introduces no numeric fact the master lacked."""
    checked = 0
    for template in PARAM_TEMPLATES:
        if template.prompt_simple is None:
            continue
        for g in template.glossary:                   # glosses explain terms, never values
            assert not _numeric_values(g.term + " " + g.explanation), (template.id, g.term)
        for seed in range(1, 12):
            try:
                voll = instantiate(template, seed, textlast="voll")
                einfach = instantiate(template, seed, textlast="einfach")
            except (ValueError, RuntimeError):
                continue
            checked += 1
            # the twin adds no number the master prompt did not already carry (no fact drift)
            assert (_numeric_values(plain_text(einfach.prompt))
                    <= _numeric_values(plain_text(voll.prompt))), (template.id, seed)
            # a pure-text answer never appears verbatim inside a gloss explanation
            if einfach.answer_key and not _numeric_values(plain_text(einfach.answer_key)):
                ans = " ".join(plain_text(einfach.answer_key).split()).lower()
                for g in template.glossary:
                    assert ans not in " ".join(g.explanation.split()).lower(), (template.id, g.term)
    assert checked >= 40


def test_textlast_projection_is_deterministic():
    profile = ParametricMixerProfile(umfang="standard", textlast="einfach")
    a, _ = variant_worksheet(find_template("mat-pythagoras"), 4, today=TODAY, seed0=17,
                             mixer_profile=profile)
    b, _ = variant_worksheet(find_template("mat-pythagoras"), 4, today=TODAY, seed0=17,
                             mixer_profile=profile)
    assert a.model_dump() == b.model_dump()


def test_textlast_renders_student_teacher_homework_and_stamps_teacher_only(tmp_path):
    import fitz

    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.repository import ReviewStore

    item = orch.compose_variants(
        ReviewStore(tmp_path / "store"), "fin-lohnzettel", 3, today=TODAY,
        mixer_profile=ParametricMixerProfile(textlast="einfach"),
    )
    assert item.error is None and item.content.mixer_lint.passed
    assert item.content.glossary

    texts = {}
    for kind in ("student", "teacher", "homework"):
        doc = fitz.open(getattr(item.artifacts, f"{kind}_pdf"))
        assert doc.page_count >= 1 and doc[0].get_pixmap().width > 0  # builds + rasterises
        texts[kind] = "".join(p.get_text() for p in doc)

    # the simplified register + Wortschatz reach the student AND homework sheet …
    for kind in ("student", "homework"):
        assert "Wortschatz" in texts[kind]
        assert "Sozialversicherung" in texts[kind]           # a gloss term (also in the twin)
        assert "Steuerbemessungsgrundlage" not in texts[kind]  # the master-only word is gone
    # … and the teacher guide names the register in the profile stamp (teacher-only)
    assert "Textlast: einfach" in texts["teacher"]
    assert "Mischpult-Profil" in texts["teacher"] and "Mischpult-Profil" not in texts["student"]
