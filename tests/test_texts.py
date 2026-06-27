"""Annotated authentic texts (the Deutsch asset class): rights gate, the annotation→task
engine, line-numbered rendering, the store, and the HITL surface."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library.texts import ANNOTATED_TEXTS, LORELEY, RABE_FUCHS, find_text
from teachersaid.schema.texts import AnnotatedText, Annotation, TextSourceRef

TODAY = date(2026, 3, 1)


# --- rights gate (select-never-author for copyright) -------------------------
def test_rights_gate():
    assert LORELEY.source.is_clear(2026)[0]                    # Heine d. 1856 → PD
    cc = TextSourceRef(author="X", title="Y", rights_basis="cc_by", repository="R", attribution="a")
    assert cc.is_clear(2026)[0]
    recent = TextSourceRef(author="Z", title="Y", author_death_year=2000,
                           rights_basis="public_domain_pma", repository="R", attribution="a")
    ok, reasons = recent.is_clear(2026)
    assert not ok and reasons                                  # only 26 years p.m.a.
    nodeath = TextSourceRef(author="Z", title="Y", rights_basis="public_domain_pma",
                            repository="R", attribution="a")
    assert not nodeath.is_clear(2026)[0]


# --- the annotation → task engine (answers from annotations) -----------------
def test_build_worksheet_derives_tasks_from_annotations():
    from teachersaid.pipeline.text_tasks import build_worksheet
    content, res = build_worksheet(LORELEY, today=TODAY)
    blocks = list(content.iter_blocks())
    # the authentic text is present as a line-numbered source_text block
    assert any(b.role == "info" and b.kind == "source_text" for b in blocks)
    tasks = [b for b in blocks if b.role == "task"]
    assert tasks and all(t.answer_key for t in tasks)         # every task carries the vetted answer
    # an answer equals its source annotation (not authored at task time)
    comp = next(a for a in LORELEY.annotations if a.kind == "comprehension")
    assert any(comp.answer in (t.answer_key or "") for t in tasks if isinstance(t.answer_key, str)) \
        or any(t.answer_key == comp.answer for t in tasks)


def test_both_flagship_texts_verify_clean():
    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.text_tasks import build_worksheet
    from teachersaid.pipeline.verify import verify
    assert len(ANNOTATED_TEXTS) >= 2
    for at in ANNOTATED_TEXTS:
        content, res = build_worksheet(at, today=TODAY)
        assemble(content, res)
        report = verify(content, res)
        assert not report.problems, f"{at.id}: {report.problems}"


def test_media_text_has_persuasion_annotations():
    kinds = {a.kind for a in RABE_FUCHS.annotations}
    assert "media_technique" in kinds and "argument_move" in kinds


# --- rendering: the line-numbered source text -------------------------------
def test_source_text_renders_with_line_numbers(tmp_path):
    import fitz

    from teachersaid.pipeline.assemble import assemble
    from teachersaid.pipeline.text_tasks import build_worksheet
    from teachersaid.rendering.student_sheet import render_student_sheet
    content, res = build_worksheet(LORELEY, today=TODAY)
    assemble(content, res)
    pdf = render_student_sheet(content, tmp_path / "s.pdf", {})
    text = "".join(p.get_text() for p in fitz.open(pdf))
    assert "Ich weiß nicht, was soll es bedeuten" in text     # the real text is printed
    assert "Quelle: Heinrich Heine" in text                   # cited


# --- store + ingest gate -----------------------------------------------------
def test_text_store_roundtrip_and_status_preserve(tmp_path):
    from teachersaid.store.textstore import TextRecord, TextStore
    store = TextStore(tmp_path)
    store.upsert(TextRecord(id=LORELEY.id, text=LORELEY))
    assert store.get(LORELEY.id).status == "in_review"
    store.set_status(LORELEY.id, "approved")
    store.upsert(TextRecord(id=LORELEY.id, text=LORELEY))      # re-seed
    assert store.get(LORELEY.id).status == "approved"          # not un-approved


def test_ingest_text_rights_gate(tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.textstore import TextStore
    store = TextStore(tmp_path)
    rec = orch.ingest_text(store, LORELEY, today=TODAY)
    assert rec.status == "in_review"
    bad = AnnotatedText(id="bad", title="T", klasse=3, text="x",
                        source=TextSourceRef(author="A", title="T", author_death_year=2010,
                                             rights_basis="public_domain_pma",
                                             repository="R", attribution="a"))
    with pytest.raises(ValueError, match="rights"):
        orch.ingest_text(store, bad, today=TODAY)


def test_seed_and_find():
    assert find_text("deu-loreley") is LORELEY
    assert find_text("nope") is None


# --- HITL surface ------------------------------------------------------------
def test_api_texts(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    from teachersaid.store.repository import ReviewStore
    from teachersaid.store.textstore import TextStore
    appmod.TEXTS = TextStore(tmp_path / "texts")
    appmod.STORE = ReviewStore(tmp_path / "store")
    appmod.orch.seed_texts(appmod.TEXTS, today=TODAY)
    client = TestClient(appmod.app)

    lst = client.get("/api/texts").json()
    assert lst and any(t["id"] == "deu-loreley" for t in lst)
    d = client.get("/api/texts/deu-loreley").json()
    assert "Ich weiß nicht" in d["text"] and d["annotations"]
    # derive a worksheet → lands in Inhalte, verify-clean
    r = client.post("/api/texts/deu-loreley/compose").json()
    assert r["error"] is None and not r["problems"]
    assert client.post("/api/texts/deu-loreley/approve").json()["status"] == "approved"


def test_feedback_accepts_text_kind():
    from teachersaid.store.feedbackstore import TARGET_KINDS
    assert "text" in TARGET_KINDS
