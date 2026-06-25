"""Phase 2: composing a worksheet from approved library blocks."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library import seed_blocks
from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.compose import compose
from teachersaid.pipeline.verify import verify
from teachersaid.schema.enums import Role
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.repository import ReviewStore

IN = date(2026, 3, 1)


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


def test_compose_respects_time_envelope(stores):
    _, bs = stores
    short, _ = compose("Physik", 4, "Strahlung und Radioaktivität", "einzelstunde", block_store=bs, today=IN)
    long, _ = compose("Physik", 4, "Strahlung und Radioaktivität", "block", block_store=bs, today=IN)
    smin = sum(t.est_minutes for t in _tasks(short))
    lmin = sum(t.est_minutes for t in _tasks(long))
    assert len(_tasks(short)) <= len(_tasks(long))
    assert smin <= lmin


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
