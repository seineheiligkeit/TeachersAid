"""Three-tier anchoring: competence | ÜT | honest Horizont."""
from __future__ import annotations

from pydantic import ValidationError
import pytest

from teachersaid.grounding import lehrplan_store as ls
from teachersaid.llm.prompts import build_system, build_user
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.generate import generate_body
from teachersaid.pipeline.plan import plan
from teachersaid.pipeline.resolve import resolve
from teachersaid.pipeline.verify import verify
from teachersaid.schema import AnchorMode
from teachersaid.schema.blocks import TaskBlock
from teachersaid.schema.worksheet import (
    Baustein, BundleRequest, WorksheetContent, WorksheetMeta,
)
from teachersaid.schema.generation_views import GenWorksheetBody

SUBJECT = "Geographie und wirtschaftliche Bildung"
KLASSE = 4


def _task(*, serves=()) -> TaskBlock:
    return TaskBlock(
        id="a.t1", kind="open_response",
        prompt="Begründe deine Entscheidung anhand der Angaben.",
        response={"mode": "lines", "n": 3},
        cognitive_level="evaluate", dimensions=["UK"],
        serves=list(serves), est_minutes=10,
        answer_key="Eine nachvollziehbar begründete Entscheidung.",
    )


def _content(mode: AnchorMode, *, uet: int | None = None, serves=()) -> WorksheetContent:
    return WorksheetContent(
        meta=WorksheetMeta(
            title="Verankerung prüfen", subject=SUBJECT, stufe="Unterstufe", klasse=KLASSE,
            fassung=ls.get_fassung(), lehrplan_label="wird aus dem Modus ehrlich gerendert",
        ),
        subject_model=ls.get_subject_model(SUBJECT),
        anchor_mode=mode, anchor_uet=uet,
        sections=[Baustein(id="a", title="Entscheiden", blocks=[_task(serves=serves)])],
    )


def test_existing_content_defaults_to_competence_on_old_json_roundtrip():
    original = _content(AnchorMode.COMPETENCE)
    payload = original.model_dump(mode="json")
    payload.pop("anchor_mode")
    payload.pop("anchor_uet")
    restored = WorksheetContent.model_validate(payload)
    assert restored.anchor_mode == AnchorMode.COMPETENCE
    assert restored.anchor_uet is None


def test_anchor_schema_rejects_incoherent_uet_fields():
    with pytest.raises(ValidationError, match="requires anchor_uet"):
        _content(AnchorMode.UET)
    with pytest.raises(ValidationError, match="only valid"):
        _content(AnchorMode.HORIZONT, uet=13)
    with pytest.raises(ValidationError):
        _content(AnchorMode.UET, uet=14)


def test_uet_resolution_and_plan_use_exact_legal_hook_without_fake_serves():
    request = BundleRequest(
        subject=SUBJECT, klasse=KLASSE, topic_raw="Finanzführerschein",
        anchor_mode=AnchorMode.UET, anchor_uet=13,
    )
    resolution = resolve(request)
    assert resolution.grade_check is True
    assert resolution.competences
    assert all(13 in c.uebergreifende_themen for c in resolution.competences)
    worksheet_plan = plan(
        resolution, topic=request.topic_raw,
        anchor_mode=request.anchor_mode, anchor_uet=request.anchor_uet,
    )
    assert worksheet_plan.anchor_mode == AnchorMode.UET
    assert worksheet_plan.section_specs
    assert all(bs.serves_competence_id is None
               for sec in worksheet_plan.section_specs for bs in sec.block_specs)
    assert "Primär über ÜT 13" in " ".join(worksheet_plan.notes)
    assert "serves: []" in build_system(ls.get_subject_model(SUBJECT), AnchorMode.UET)
    assert "ÜT 13" in build_user(worksheet_plan, resolution)


def test_uet_nachweis_names_verbatim_hook_and_has_no_full_coverage_gaps():
    request = BundleRequest(
        subject=SUBJECT, klasse=KLASSE, topic_raw="Finanzführerschein",
        anchor_mode="uet", anchor_uet=13,
    )
    resolution = resolve(request)
    content = _content(AnchorMode.UET, uet=13)
    assemble(content, resolution)
    report = verify(content, resolution)
    assert report.problems == []
    assert content.nachweis.anchor_mode == AnchorMode.UET
    assert content.nachweis.anchor_label == (
        "ÜT 13: Wirtschafts-, Finanz- und Verbraucher/innenbildung"
    )
    assert "verbatim Lehrplan-Hook" in content.nachweis.statement
    assert content.nachweis.competence_coverage == []
    assert content.nachweis.gaps == []


def test_uet_may_report_only_a_genuinely_hooked_secondary_competence():
    served = [{"competence_id": "GWB.US.4.EIG.01", "relation": "exercises"}]
    request = BundleRequest(
        subject=SUBJECT, klasse=KLASSE, topic_raw="Finanzführerschein",
        anchor_mode="uet", anchor_uet=13,
    )
    resolution = resolve(request)
    content = _content(AnchorMode.UET, uet=13, serves=served)
    assemble(content, resolution)
    assert verify(content, resolution).problems == []
    assert [c.competence_id for c in content.nachweis.competence_coverage] == [
        "GWB.US.4.EIG.01"
    ]
    assert "kein Vollständigkeitsanspruch" in content.nachweis.statement


def test_uet_rejects_a_number_not_carried_by_the_subject_at_that_grade():
    # ÜT 1 exists in the legend, but GWB does not carry it at this grade.
    request = BundleRequest(
        subject=SUBJECT, klasse=KLASSE, topic_raw="Test", anchor_mode="uet", anchor_uet=1,
    )
    resolution = resolve(request)
    assert resolution.grade_check is False
    content = _content(AnchorMode.UET, uet=1)
    report = verify(content, resolution)
    assert any("nicht als verbatim Hook" in p for p in report.problems)


def test_horizont_is_explicit_and_cannot_smuggle_a_competence_claim():
    request = BundleRequest(
        subject=SUBJECT, klasse=KLASSE, topic_raw="Sternkarten",
        anchor_mode=AnchorMode.HORIZONT,
    )
    resolution = resolve(request)
    assert resolution.grade_check is True and resolution.competences == []
    content = _content(AnchorMode.HORIZONT)
    assemble(content, resolution)
    assert verify(content, resolution).problems == []
    assert content.nachweis.competence_coverage == []
    assert "kein Lehrplan-Kompetenzbezug" in content.nachweis.statement

    content_with_claim = _content(
        AnchorMode.HORIZONT,
        serves=[{"competence_id": "GWB.US.4.EIG.01", "relation": "exercises"}],
    )
    report = verify(content_with_claim, resolution)
    assert any("Horizont darf keinen" in p for p in report.problems)


def test_teacher_nachweis_renders_mode_and_honest_label(tmp_path):
    import fitz
    from teachersaid.rendering.teacher_guide import render_teacher_guide

    request = BundleRequest(
        subject=SUBJECT, klasse=KLASSE, topic_raw="Finanzführerschein",
        anchor_mode="uet", anchor_uet=13,
    )
    content = _content(AnchorMode.UET, uet=13)
    assemble(content, resolve(request))
    pdf = render_teacher_guide(content, tmp_path / "uet.pdf")
    text = "\n".join(page.get_text() for page in fitz.open(pdf))
    assert "Verankerungsmodus: Übergreifendes Thema (ÜT)" in text
    assert "ÜT 13: Wirtschafts-, Finanz- und Verbraucher/innenbildung" in text
    assert "LÜCKE" not in text


def test_noncompetence_generation_seam_emits_anchor_and_empty_serves():
    class Fake:
        def parse(self, system, user, schema):
            assert "Every task MUST emit `serves: []`" in system
            assert "Horizont" in user
            return GenWorksheetBody.model_validate({
                "sections": [{
                    "id": "h", "title": "Horizont", "throughline": "Staunen und prüfen.",
                    "blocks": [{
                        "role": "task", "id": "h.t1", "kind": "open_response",
                        "prompt": "Begründe deine Vermutung.",
                        "response": {"mode": "lines", "n": 3},
                        "cognitive_level": "analyze", "dimensions": ["UK"],
                        "serves": [], "est_minutes": 10,
                    }],
                }],
            })

    request = BundleRequest(
        subject=SUBJECT, klasse=KLASSE, topic_raw="Sternkarten",
        anchor_mode=AnchorMode.HORIZONT,
    )
    resolution = resolve(request)
    worksheet_plan = plan(
        resolution, topic=request.topic_raw, anchor_mode=request.anchor_mode,
    )
    content = generate_body(worksheet_plan, resolution, generator=Fake())
    assert content.anchor_mode == AnchorMode.HORIZONT
    assert content.anchor_uet is None
    assert content.sections[0].blocks[0].serves == []
    assert "Horizont" in content.meta.lehrplan_label


def test_brainstorm_api_carries_anchor_mode(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from teachersaid.api import app as appmod
    from teachersaid.store.repository import ReviewStore

    appmod.STORE = ReviewStore(tmp_path / "store")
    client = TestClient(appmod.app)
    created = client.post("/api/brainstorm", json={
        "subject": SUBJECT, "klasse": KLASSE, "topic": "Sternkarten",
        "anchor_mode": "horizont",
    })
    assert created.status_code == 200
    assert created.json()["anchor_mode"] == "horizont"
    bad = client.post("/api/brainstorm", json={
        "subject": SUBJECT, "klasse": KLASSE, "topic": "Finanzen",
        "anchor_mode": "uet",
    })
    assert bad.status_code == 422
