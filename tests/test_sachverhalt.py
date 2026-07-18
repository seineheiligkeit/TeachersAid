"""Sachverhalt content layer (Phase 1) — schema, derivation, computed answers, figures,
entity-lint, and projection-purity render. The proof that one curated module → three
trustworthy projections, with the answers COMPUTED from the fact-set (never authored)."""

from __future__ import annotations

import re

import fitz  # PyMuPDF
import pytest

from teachersaid.library.sachverhalt_blutkreislauf import build_sachverhalt as build_bk
from teachersaid.library.sachverhalt_bundeslaender import build_sachverhalt as build_gwb
from teachersaid.library.sachverhalt_wiener_kongress import build_sachverhalt
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.sachverhalt import build_worksheet
from teachersaid.pipeline.sachverhalt_lint import lint
from teachersaid.pipeline.verify import verify
from teachersaid.rendering.student_sheet import render_student_sheet
from teachersaid.rendering.teacher_guide import render_teacher_guide
from teachersaid.schema.sachverhalt import Sachverhalt


def _task(content, kind):
    return next(b for b in content.iter_blocks() if getattr(b, "kind", "") == kind)


def test_schema_roundtrip():
    sv = build_sachverhalt()
    assert Sachverhalt.model_validate(sv.model_dump()) == sv


def test_build_and_verify_clean():
    content, res = build_worksheet(build_sachverhalt())
    assemble(content, res)
    report = verify(content, res)
    assert report.ok, report.problems
    kinds = {b.kind for b in content.iter_blocks() if b.role.value == "task"}
    assert {"ordering", "cause_effect_match", "concept_match", "content_comprehension",
            "structure_overview", "position_argument"} <= kinds


def test_anforderungs_spread():
    """A real cognitive ladder (not all one band) — the depth contract."""
    content, _ = build_worksheet(build_sachverhalt())
    levels = {b.cognitive_level for b in content.iter_blocks() if b.role.value == "task"}
    assert {"remember", "analyze", "evaluate"} <= levels


def test_chronology_answer_is_computed_not_authored():
    sv = build_sachverhalt()
    content, _ = build_worksheet(sv)
    task = _task(content, "ordering")
    # the answer is the timeline sorted by `at` — strictly increasing years
    years = [int(y) for y in re.findall(r"\d{4}", task.answer_key)]
    assert years == sorted(years) and len(years) == len(sv.timeline)
    # the DISPLAYED order is not already chronological → it is a real task
    chrono_labels = [e.label for e in sorted(sv.timeline, key=lambda e: e.at)]
    assert task.payload.items != chrono_labels


def test_matches_are_drawn_from_the_factset():
    sv = build_sachverhalt()
    content, _ = build_worksheet(sv)
    ce = _task(content, "cause_effect_match")
    assert ce.payload.left == [c.cause for c in sv.causes]
    for c in sv.causes:                       # every real pairing is in the key
        assert f"{c.cause} → {c.effect}" in ce.answer_key
    cm = _task(content, "concept_match")
    assert cm.payload.left == [c.term for c in sv.concepts]
    for c in sv.concepts:
        assert c.term in cm.answer_key


def test_derived_figures_present_and_build(tmp_path):
    content, _ = build_worksheet(build_sachverhalt())
    gens = {a.generator for a in content.assets}
    assert {"matplotlib:zeitband", "matplotlib:cause_effect"} <= gens
    # both recipes actually render (proves the new cause_effect recipe)
    for a in content.assets:
        p = build_asset(a, outdir=tmp_path / "assets")
        assert p.exists() and p.stat().st_size > 1000


def test_projection_purity_render(tmp_path):
    """Student + teacher render from the ONE content object; teacher shows reasoning the
    student sheet hides (the projection-purity guarantee)."""
    content, res = build_worksheet(build_sachverhalt())
    assemble(content, res)
    assets = {a.id: build_asset(a, outdir=tmp_path / "assets") for a in content.assets}
    sp = render_student_sheet(content, tmp_path / "s.pdf", assets)
    tp = render_teacher_guide(content, tmp_path / "t.pdf", assets)

    def text_of(pdf):
        with fitz.open(pdf) as doc:
            return "".join(page.get_text() for page in doc)

    s_text, t_text = text_of(sp), text_of(tp)
    assert "Wiener Kongress" in s_text and "Wiener Kongress" in t_text
    # acceptable_reasoning is strictly teacher-only
    assert "bewertet wird die Begründung" in t_text
    assert "bewertet wird die Begründung" not in s_text


def test_entity_lint_clean_on_flagship():
    problems, _warnings = lint(build_sachverhalt())
    assert problems == [], problems


def test_entity_lint_catches_out_of_set_year():
    sv = build_sachverhalt()
    # plant the classic 1815→1851 garble in a Darstellung section
    sv.darstellung[3].body = sv.darstellung[3].body.replace("1815", "1851")
    problems, _ = lint(sv)
    assert any("1851" in p for p in problems), problems


# --- Stage B: the HITL surface (store · ingest gates · seed · API) -----------
def test_store_roundtrip_and_status_preserve(tmp_path):
    from teachersaid.store.sachverhaltstore import SachverhaltRecord, SachverhaltStore
    store = SachverhaltStore(tmp_path)
    sv = build_sachverhalt()
    store.upsert(SachverhaltRecord(id=sv.id, sachverhalt=sv))
    assert store.get(sv.id).status == "in_review"
    store.set_status(sv.id, "approved")
    store.upsert(SachverhaltRecord(id=sv.id, sachverhalt=sv))      # re-seed
    assert store.get(sv.id).status == "approved"                  # never un-approved


def test_ingest_facts_and_entity_gates(tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.sachverhaltstore import SachverhaltStore
    store = SachverhaltStore(tmp_path)
    assert orch.ingest_sachverhalt(store, build_sachverhalt()).status == "in_review"
    # facts gate — no role="facts" source
    no_facts = build_sachverhalt().model_copy(update={"sources": []})
    with pytest.raises(ValueError, match="facts"):
        orch.ingest_sachverhalt(store, no_facts)
    # entity gate — an out-of-set year in the Darstellung blocks staging
    bad = build_sachverhalt().model_copy(deep=True)
    bad.darstellung[3].body = bad.darstellung[3].body.replace("1815", "1851")
    with pytest.raises(ValueError, match="Entity-Lint"):
        orch.ingest_sachverhalt(store, bad)


def test_seed_sachverhalte(tmp_path):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.store.sachverhaltstore import SachverhaltStore
    store = SachverhaltStore(tmp_path)
    recs = orch.seed_sachverhalte(store)
    assert recs and store.list(status="in_review")
    store.set_status(recs[0].id, "approved")
    assert store.approved()


def test_feedback_accepts_sachverhalt_kind():
    from teachersaid.store.feedbackstore import TARGET_KINDS
    assert "sachverhalt" in TARGET_KINDS


def test_api_sachverhalte(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    from teachersaid.store.repository import ReviewStore
    from teachersaid.store.sachverhaltstore import SachverhaltStore
    appmod.SACHVERHALTE = SachverhaltStore(tmp_path / "sv")
    appmod.STORE = ReviewStore(tmp_path / "store")
    appmod.orch.seed_sachverhalte(appmod.SACHVERHALTE)
    client = TestClient(appmod.app)

    lst = client.get("/api/sachverhalte").json()
    assert lst and any(s["id"] == "sv-wiener-kongress" for s in lst)
    d = client.get("/api/sachverhalte/sv-wiener-kongress").json()
    assert d["timeline"] and d["darstellung"] and d["facts_sources"]
    # derive a worksheet → lands in Inhalte, verify-clean
    r = client.post("/api/sachverhalte/sv-wiener-kongress/compose").json()
    assert r["error"] is None and not r["problems"]
    assert client.post("/api/sachverhalte/sv-wiener-kongress/approve").json()["status"] == "approved"


# --- Phase 2: the container generalises to Biology (a process/cycle, not a timeline) ---------
def test_bio_has_process_not_timeline_and_verifies_clean():
    sv = build_bk()
    assert not sv.timeline and len(sv.process) >= 4 and sv.process_cyclic   # undated cycle
    content, res = build_worksheet(sv)
    assemble(content, res)
    report = verify(content, res)
    assert report.ok, report.problems


def test_bio_process_figure_and_computed_ordering(tmp_path):
    sv = build_bk()
    content, _ = build_worksheet(sv)
    gens = {a.generator for a in content.assets}
    assert "matplotlib:process_flow" in gens and "matplotlib:zeitband" not in gens
    proc = next(a for a in content.assets if a.generator == "matplotlib:process_flow")
    assert build_asset(proc, outdir=tmp_path).stat().st_size > 1000        # the new recipe renders
    task = _task(content, "ordering")
    assert task.answer_key.split(" → ")[0] == sv.process[0].name           # computed, authored order
    assert "zurück zum Anfang" in task.answer_key                          # cyclic marker
    assert task.payload.items != [s.name for s in sv.process]              # displayed shuffled


def test_bio_strand_correct_anchoring():
    """The judgment task falls back to core open_response (Bio has no position_argument) and
    serves the S strand; the Sachkompetenz tasks serve the W strand. Dims are strand-correct."""
    content, _ = build_worksheet(build_bk())
    tasks = [b for b in content.iter_blocks() if b.role.value == "task"]
    urteil = next(b for b in tasks if b.cognitive_level == "evaluate")
    assert urteil.kind == "open_response"
    assert urteil.serves[0].competence_id == "BIO.US.x.STA.02" and urteil.dimensions == ["S"]
    sach = [b for b in tasks if b.cognitive_level != "evaluate"]
    assert sach and all(b.dimensions == ["W"] for b in sach)
    assert all(s.competence_id.startswith("BIO.US.x.WIS") for b in sach for s in b.serves)


def test_bio_entity_lint_clean():
    problems, _ = lint(build_bk())
    assert problems == [], problems


# --- Phase 2 (Geography): the container generalises to a spatial subject + a MAP -------------
def test_gwb_choropleth_with_cited_values_verifies_clean(tmp_path):
    sv = build_gwb()
    assert sv.regions and sv.geo_id and not sv.timeline and not sv.process   # the spatial fact-type
    content, res = build_worksheet(sv)
    assemble(content, res)
    assert verify(content, res).ok, verify(content, res).problems
    m = next(a for a in content.assets if a.generator == "matplotlib:choropleth_map")
    # the fill VALUES are pulled from the cited dataset (select-never-author), not authored
    assert len(m.spec["values"]) == 9
    assert m.data_source.dataset_id == "statistik_austria_bundeslaender_2024"
    assert build_asset(m, outdir=tmp_path).stat().st_size > 1000             # the map renders


def test_gwb_rank_by_value_computed_and_strand_correct():
    content, _ = build_worksheet(build_gwb())
    rank = _task(content, "ordering")
    assert rank.answer_key.startswith("Wien")                               # largest first (computed)
    assert "Burgenland" in rank.answer_key.rsplit(">", 1)[-1]               # smallest last
    tasks = [b for b in content.iter_blocks() if b.role.value == "task"]
    sach = [b for b in tasks if b.cognitive_level != "evaluate"]
    assert sach and all(b.dimensions == ["OK"] for b in sach)               # Orientierungskompetenz
    urteil = next(b for b in tasks if b.cognitive_level == "evaluate")
    assert urteil.kind == "position_argument" and urteil.dimensions == ["UK"]


def test_gwb_entity_lint_clean():
    assert lint(build_gwb())[0] == []


def test_name_lint_conservative_but_catches_real_names():
    sv = build_gwb()
    base = len(lint(sv)[1])
    sv.darstellung[0].body += " Die Karte und das Diagramm zeigen es deutlich."
    assert len(lint(sv)[1]) == base                                          # function-word nouns: not flagged
    sv.darstellung[0].body += " Erfunden: Kaiser Wilhelm von Hohenzollern."
    assert any("Hohenzollern" in w for w in lint(sv)[1])                     # a real proper name IS flagged


def test_geo_store_and_fetch_validator():
    from teachersaid.grounding import geo_store
    b = geo_store.load_boundaries("at_bundeslaender")
    assert len(b) == 9 and "Wien" in b
    assert "CC BY" in geo_store.citation("at_bundeslaender")
    # the fetch tool's validator is a pure function (offline, no network)
    import json

    from tools.fetch_geo_boundaries import BOUNDARIES, validate
    cfg = BOUNDARIES["at_bundeslaender"]
    good = json.dumps({"type": "FeatureCollection", "features": [
        {"properties": {"name": n}, "geometry": {"type": "Polygon",
         "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}} for n in cfg["expected_names"]]})
    assert validate(good.encode(), cfg)["type"] == "FeatureCollection"
    with pytest.raises(ValueError):
        validate(json.dumps({"type": "FeatureCollection", "features": []}).encode(), cfg)
