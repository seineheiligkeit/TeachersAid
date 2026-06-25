"""Phase 2: composing a worksheet from approved library blocks."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library import seed_blocks
from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.compose import compose
from teachersaid.pipeline.resolve import resolve, resolve_kompetenzbereich
from teachersaid.pipeline.verify import verify
from teachersaid.schema.enums import Role
from teachersaid.schema.worksheet import BundleRequest
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.repository import ReviewStore

IN = date(2026, 3, 1)
MAT_KB = "4: Daten und Zufall"  # a numbered content-area KB the title doesn't echo


@pytest.fixture
def stores(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    bs = BlockStore(tmp_path / "blocks")
    seed_blocks(bs)  # approved curated seed
    return ReviewStore(tmp_path / "store"), bs


def _tasks(content):
    return [b for b in content.iter_blocks() if b.role == Role.TASK]


def test_compose_from_approved_blocks_verifies_clean(stores):
    _, bs = stores
    content, res = compose("Physik", 4, "Strahlung und Radioaktivität",
                           "doppelstunde", block_store=bs, today=IN)
    tasks = _tasks(content)
    assert tasks, "composed worksheet must contain library task blocks"
    assert content.meta.subject == "Physik" and content.meta.kernfrage
    assemble(content, res)
    report = verify(content, res)
    assert report.problems == [], report.problems   # serves/dimensions/kinds all valid
    # composed tasks all serve competences resolved for the topic
    valid = {c.id for c in res.competences}
    assert all(any(s.competence_id in valid for s in t.serves) for t in tasks)


def test_compose_carries_figure_assets(stores):
    """Phase 3c: a figure block's asset travels into the composition (no longer skipped)."""
    _, bs = stores
    content, res = compose("Physik", 4, "Strahlung und Radioaktivität",
                           kompetenzbereich="Strahlung und Radioaktivität", block_store=bs, today=IN)
    assert content.assets, "composed sheet should carry the figure block's asset(s)"
    assert any(a.generator for a in content.assets)  # the code-generated spectrum figure
    assemble(content, res)
    assert verify(content, res).problems == []


def test_compose_respects_time_envelope(stores):
    _, bs = stores
    short, _ = compose("Physik", 4, "Strahlung und Radioaktivität", "einzelstunde", block_store=bs, today=IN)
    long, _ = compose("Physik", 4, "Strahlung und Radioaktivität", "block", block_store=bs, today=IN)
    smin = sum(t.est_minutes for t in _tasks(short))
    lmin = sum(t.est_minutes for t in _tasks(long))
    assert len(_tasks(short)) <= len(_tasks(long))
    assert smin <= lmin


def test_resolve_kompetenzbereich_is_deterministic():
    # A catchy worksheet title that doesn't echo the KB name fails the topic match …
    topic_res = resolve(
        BundleRequest(subject="Mathematik", klasse=4, topic_raw="Das unfaire Spiel"), today=IN
    )
    assert topic_res.competences == [] and topic_res.matched_kompetenzbereiche == []
    # … but targeting the Kompetenzbereich resolves its competences directly.
    kb_res = resolve_kompetenzbereich("Mathematik", 4, MAT_KB, today=IN)
    assert kb_res.matched_kompetenzbereiche == [MAT_KB]
    assert any(c.id == "MAT.US.4.DAT.02" for c in kb_res.competences)


def test_compose_by_kompetenzbereich_unblocks_mathematik(stores):
    _, bs = stores
    # By topic alone, "Das unfaire Spiel" can't compose (title doesn't match the KB) …
    with pytest.raises(ValueError):
        compose("Mathematik", 4, "Das unfaire Spiel", block_store=bs, today=IN)
    # … but targeting the Kompetenzbereich does; the topic stays the display title.
    content, res = compose("Mathematik", 4, "Das unfaire Spiel",
                           kompetenzbereich=MAT_KB, block_store=bs, today=IN)
    tasks = _tasks(content)
    assert tasks and content.meta.title == "Das unfaire Spiel"
    valid = {c.id for c in res.competences}
    assert all(any(s.competence_id in valid for s in t.serves) for t in tasks)
    assemble(content, res)
    assert verify(content, res).problems == []


def test_compose_without_blocks_raises(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    empty = BlockStore(tmp_path / "blocks")  # no blocks seeded
    with pytest.raises(ValueError):
        compose("Physik", 4, "Strahlung und Radioaktivität", block_store=empty, today=IN)


def test_compose_worksheet_creates_content_item(stores):
    rs, bs = stores
    item = orch.compose_worksheet(rs, bs, "Physik", 4, "Strahlung und Radioaktivität", today=IN)
    assert item.stage == "content" and item.source == "compose"
    assert item.error is None, item.error
    assert item.content and item.artifacts and item.artifacts.student_pdf
    assert item.content.nachweis is not None


def test_api_compose_and_approve_all(tmp_path, monkeypatch):
    monkeypatch.setattr(__import__("teachersaid.config", fromlist=["x"]), "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient
    from teachersaid.api import app as appmod

    appmod.BLOCKS = BlockStore(tmp_path / "blocks")
    appmod.STORE = ReviewStore(tmp_path / "store")
    seed_blocks(appmod.BLOCKS, status="in_review")
    client = TestClient(appmod.app)

    assert client.post("/api/blocks/approve-all").json()["approved"] >= 15
    r = client.post("/api/compose", json={"subject": "Physik", "klasse": 4,
                                          "topic": "Strahlung und Radioaktivität"}).json()
    assert r["stage"] == "content" and r["error"] is None
    item = client.get(f"/api/items/{r['id']}").json()
    assert item["content"]["sections"][0]["blocks"]


def test_api_kompetenzbereiche_and_compose_by_kb(tmp_path, monkeypatch):
    monkeypatch.setattr(__import__("teachersaid.config", fromlist=["x"]), "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient
    from teachersaid.api import app as appmod

    appmod.BLOCKS = BlockStore(tmp_path / "blocks")
    appmod.STORE = ReviewStore(tmp_path / "store")
    seed_blocks(appmod.BLOCKS)
    client = TestClient(appmod.app)

    kbs = client.get("/api/kompetenzbereiche?subject=Mathematik&klasse=4").json()["kompetenzbereiche"]
    assert MAT_KB in kbs
    # compose Mathematik by its Kompetenzbereich (the topic-only path would 404/error)
    r = client.post("/api/compose", json={"subject": "Mathematik", "klasse": 4,
                                          "topic": "Das unfaire Spiel",
                                          "kompetenzbereich": MAT_KB}).json()
    assert r["stage"] == "content" and r["error"] is None
    item = client.get(f"/api/items/{r['id']}").json()
    assert item["content"]["sections"][0]["blocks"]
