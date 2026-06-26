"""Breadth-push backbone: ingest an LLM-generated body through the real seam.

A subagent emits a GenWorksheetBody; ingest_generated validates it against the
catalog / subject model / verify rules and stages it for review. Clean bodies
harvest blocks; bodies with an invented kind/dimension do NOT.
"""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.pipeline import orchestrator as orch
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.repository import ReviewStore

IN = date(2026, 3, 1)
KB = "Strahlung und Radioaktivität"


def _body(kind="open_response"):
    """A minimal-but-real Physik grade-4 body (catalog ids + W/E/S dims)."""
    return {
        "intro": [
            {"role": "info", "id": "i1", "kind": "prose",
             "content": "Strahlung ist nicht gleich Strahlung — die Energie entscheidet."},
        ],
        "sections": [{
            "id": "s1",
            "title": "Energie entscheidet",
            "throughline": "Energie, nicht Durchdringung, bestimmt die Wirkung.",
            "talking_points": ["Warum ist UV gefährlicher als Radiowellen?"],
            "extensions": ["Anwendungen recherchieren: PET, C-14-Datierung."],
            "blocks": [
                {"role": "task", "id": "t1", "kind": "open_response",
                 "prompt": "Erkläre den radioaktiven Zerfall als Zufallsprozess.",
                 "response": {"mode": "lines", "n": 3},
                 "cognitive_level": "understand", "dimensions": ["W"],
                 "serves": [{"competence_id": "PHY.US.4.STR.03", "relation": "exercises"}],
                 "est_minutes": 6, "answer_key": "Einzelner Zerfall unvorhersehbar, viele statistisch.",
                 "watch_outs": ["'Zufall' ≠ 'ohne Gesetz' — Halbwertszeit ist exakt."]},
                {"role": "task", "id": "t2", "kind": kind,
                 "prompt": "Beurteile: WLAN ist gefährlicher als Röntgen, weil es ständig da ist.",
                 "response": {"mode": "lines", "n": 4},
                 "cognitive_level": "evaluate", "dimensions": ["S"],
                 "serves": [{"competence_id": "PHY.US.4.STR.02", "relation": "exercises"}],
                 "est_minutes": 8, "answer_key": "Nein — Röntgen ist ionisierend, WLAN nicht.",
                 "watch_outs": ["Dauer ≠ Energie."]},
            ],
        }],
    }


@pytest.fixture
def stores(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    return ReviewStore(tmp_path / "store"), BlockStore(tmp_path / "blocks")


def test_ingest_clean_body_stages_item_and_harvests_blocks(stores):
    store, blocks = stores
    item, n = orch.ingest_generated(
        store, blocks, "Physik", 4, kompetenzbereich=KB,
        title="Strahlung: gefährlich oder nicht?",
        kernfrage="Was macht Strahlung gefährlich?", body=_body(), today=IN,
    )
    assert item.error is None, item.error
    assert item.verify_problems == [], item.verify_problems
    assert item.stage == "content" and item.source == "generated"
    assert item.content.nachweis is not None and item.artifacts.student_pdf
    # blocks harvested into the library as pending review
    assert n >= 2
    staged = blocks.list()
    assert staged and all(b.status == "in_review" for b in staged)
    assert any(b.role == "task" for b in staged)


def test_ingest_invalid_kind_is_caught_and_harvests_nothing(stores):
    store, blocks = stores
    item, n = orch.ingest_generated(
        store, blocks, "Physik", 4, kompetenzbereich=KB,
        title="Kaputt", kernfrage="?", body=_body(kind="quiztime"), today=IN,
    )
    # an invented kind must NOT silently become a library block
    assert n == 0
    assert item.error is not None or item.verify_problems
    assert blocks.list() == []


def _body_with_asset(generator="matplotlib:number_line"):
    b = _body()
    b["assets"] = [{"id": "abb1", "role": "figure", "generator": generator,
                    "spec": {"min": 0, "max": 10, "marks": [{"at": 4, "label": "A"}]}}]
    b["sections"][0]["blocks"][0]["asset_refs"] = ["abb1"]   # first task references the figure
    return b


def test_ingest_asset_bearing_body(stores):
    """Phase 4 #1: a generated body may request a figure; it builds, travels with the block,
    and the worksheet stays verify-clean."""
    store, blocks = stores
    item, n = orch.ingest_generated(
        store, blocks, "Physik", 4, kompetenzbereich=KB,
        title="Mit Abbildung", kernfrage="Was zeigt der Zahlenstrahl?",
        body=_body_with_asset(), today=IN,
    )
    assert item.error is None, item.error
    assert item.verify_problems == []
    assert item.content.assets and item.content.assets[0].generator == "matplotlib:number_line"
    # the harvested task block carries the asset spec (3c)
    with_asset = [b for b in blocks.list() if b.role == "task" and b.assets]
    assert with_asset and with_asset[0].assets[0].id == "abb1"


def test_ingest_rejects_disallowed_asset_generator(stores):
    """An LLM may only request the parameterized recipe library — a bespoke/invented
    generator is caught, and nothing is harvested."""
    store, blocks = stores
    item, n = orch.ingest_generated(
        store, blocks, "Physik", 4, kompetenzbereich=KB, title="Verboten", kernfrage="?",
        body=_body_with_asset(generator="matplotlib:em_spectrum"), today=IN,
    )
    assert item.error is not None and n == 0


def test_ingest_whole_grade_for_strand_subject(stores):
    """Biologie's KBs are W/E/S strands, so ingest resolves the whole grade — a task
    serving any real grade-4 Bio competence verifies clean."""
    store, blocks = stores
    body = {
        "intro": [],
        "sections": [{
            "id": "s1", "title": "Vererbung", "throughline": "DNA trägt die Erbinformation.",
            "talking_points": ["Warum ähneln Kinder ihren Eltern?"], "extensions": [],
            "blocks": [
                {"role": "task", "id": "t1", "kind": "open_response",
                 "prompt": "Beschreibe, wie Merkmale von Eltern an Kinder weitergegeben werden.",
                 "response": {"mode": "lines", "n": 4},
                 "cognitive_level": "understand", "dimensions": ["W"],
                 "serves": [{"competence_id": "BIO.US.x.WIS.01", "relation": "exercises"}],
                 "est_minutes": 7, "answer_key": "Über die DNA / Gene in den Keimzellen.",
                 "watch_outs": ["Nicht 'Blut mischt sich' — es sind Gene."]},
            ],
        }],
    }
    item, n = orch.ingest_generated(
        store, blocks, "Biologie", 4, scope_label="Vererbung und Genetik",
        title="Vererbung", kernfrage="Wie werden Merkmale weitergegeben?", body=body, today=IN,
    )
    assert item.error is None and item.verify_problems == [], item.verify_problems
    assert n >= 1 and item.content.nachweis is not None
