"""P1 Tiefenregler: pure derivations over one parametric master."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library.templates import find_template, variant_worksheet
from teachersaid.pipeline.parametrize import instantiate
from teachersaid.schema.mixer import Offenheit, ParametricMixerProfile


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
