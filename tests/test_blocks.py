"""The block library: harvest, store, idempotent re-seed, coverage stats, API."""

from __future__ import annotations

import pytest

from teachersaid.library import EXAMPLES, seed_blocks
from teachersaid.library.block import harvest
from teachersaid.stats import compute_stats
from teachersaid.store.blockstore import BlockStore


@pytest.fixture
def blockstore(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)  # isolate both stores
    return BlockStore(tmp_path / "blocks")


def test_harvest_tags_blocks_from_catalog():
    total = 0
    for ex in EXAMPLES:
        blocks = harvest(ex.build(), example_key=ex.key)
        assert blocks
        total += len(blocks)
        ids = [b.id for b in blocks]
        assert len(ids) == len(set(ids))  # unique
        for lb in blocks:
            assert lb.id.startswith(ex.key) and lb.role in ("task", "info")
            assert lb.scope == "standard" and lb.subject == ex.subject
            if lb.role == "task":
                assert lb.cognitive_level and lb.competences
                # competence id -> Kompetenzbereich was tagged from the catalog
                assert lb.kompetenzbereich
    assert total >= 15  # ~21 across the three examples


def test_blockstore_upsert_preserves_review_status(blockstore):
    lb = harvest(EXAMPLES[0].build(), example_key=EXAMPLES[0].key)[0]
    blockstore.upsert(lb)
    assert blockstore.get(lb.id).status == "in_review"
    blockstore.set_status(lb.id, "approved")
    # re-seeding the same block must NOT un-approve it
    blockstore.upsert(harvest(EXAMPLES[0].build(), example_key=EXAMPLES[0].key)[0])
    assert blockstore.get(lb.id).status == "approved"


def test_seed_blocks_then_coverage_stats(blockstore):
    seed_blocks(blockstore, status="in_review")  # test the in-review -> approve flow
    allb = blockstore.list()
    assert len(allb) >= 15 and all(b.status == "in_review" for b in allb)

    # nothing approved yet -> zero coverage, but everything in review
    s0 = compute_stats(blockstore)
    assert s0["totals"]["covered_competences"] == 0
    assert s0["totals"]["in_review"] == len(allb)

    # approve the Physik task blocks -> Physik coverage appears
    for b in blockstore.list(subject="Physik", role="task"):
        blockstore.set_status(b.id, "approved")
    s1 = compute_stats(blockstore)
    phy = next(r for r in s1["subjects"] if r["code"] == "PHY")
    assert phy["task_blocks"] >= 3 and phy["covered_competences"] >= 1
    assert phy["coverage_pct"] > 0 and phy["by_level"]


def test_api_block_endpoints(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient
    from teachersaid.api import app as appmod

    appmod.BLOCKS = BlockStore(tmp_path / "blocks")
    appmod.STORE = type(appmod.STORE)(tmp_path / "store")
    seed_blocks(appmod.BLOCKS)
    client = TestClient(appmod.app)

    blocks = client.get("/api/blocks?role=task").json()
    assert blocks and all(b["role"] == "task" for b in blocks)
    bid = blocks[0]["id"]
    assert client.get(f"/api/blocks/{bid}").json()["block"]  # full block served
    assert client.post(f"/api/blocks/{bid}/approve").json()["status"] == "approved"

    st = client.get("/api/stats").json()
    assert st["totals"]["covered_competences"] >= 1
    assert "by_level" in st["subjects"][0]


def test_api_asset_preview_and_gallery(tmp_path, monkeypatch):
    """Phase 4 #2: a block's figure builds + serves on demand, and the gallery
    aggregates every figure (deduped by generator+spec) with a working preview."""
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient
    from teachersaid.api import app as appmod
    from teachersaid.pipeline import orchestrator as orch

    appmod.BLOCKS = BlockStore(tmp_path / "blocks")
    appmod.STORE = type(appmod.STORE)(tmp_path / "store")
    seed_blocks(appmod.BLOCKS)

    # also stage a figure-bearing worksheet ITEM, so the gallery's content branch
    # + the item-asset endpoint are exercised (assets must load from disk as Assets,
    # not dicts — the bug this test would otherwise miss with an empty store)
    from datetime import date
    asset_body = {
        "intro": [],
        "sections": [{"id": "s1", "title": "T", "throughline": "x",
            "talking_points": ["?"], "extensions": [],
            "blocks": [{"role": "task", "id": "t1", "kind": "open_response",
                "prompt": "Lies den Wert ab.", "response": {"mode": "lines", "n": 2},
                "cognitive_level": "understand", "dimensions": ["W"],
                "serves": [{"competence_id": "PHY.US.4.STR.03", "relation": "exercises"}],
                "est_minutes": 5, "answer_key": "A liegt bei 4.", "asset_refs": ["abb1"]}]}],
        "assets": [{"id": "abb1", "role": "figure", "generator": "matplotlib:number_line",
            "spec": {"min": 0, "max": 10, "marks": [{"at": 4, "label": "A"}]}}],
    }
    item, _ = orch.ingest_generated(
        appmod.STORE, appmod.BLOCKS, "Physik", 4,
        kompetenzbereich="Strahlung und Radioaktivität", title="Mit Abbildung",
        kernfrage="Was zeigt der Zahlenstrahl?", body=asset_body, today=date(2026, 3, 1))
    assert item.error is None, item.error

    client = TestClient(appmod.app)

    # a curated block carries a figure spec (3c) — it builds + serves as a PNG
    with_asset = next(b for b in appmod.BLOCKS.list() if b.assets)
    aid = with_asset.assets[0].id
    r = client.get(f"/api/blocks/{with_asset.id}/asset/{aid}")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n" and len(r.content) > 200

    # the item's figure also serves (loaded from disk as a real Asset, not a dict)
    ri = client.get(f"/api/items/{item.id}/asset/abb1")
    assert ri.status_code == 200 and ri.content[:8] == b"\x89PNG\r\n\x1a\n"

    # the gallery lists both sources, each with a preview URL that resolves to a PNG
    gallery = client.get("/api/assets").json()
    assert gallery and all(e["generator"] for e in gallery)
    mine = next(e for e in gallery if any(b["id"] == with_asset.id for b in e["blocks"]))
    assert mine["n_blocks"] >= 1 and client.get(mine["preview"]).status_code == 200
    assert any(e["n_items"] >= 1 for e in gallery)  # the item branch produced an entry

    # unknown asset/block -> 404, not a 500
    assert client.get(f"/api/blocks/{with_asset.id}/asset/nope").status_code == 404
    assert client.get("/api/blocks/nope/asset/x").status_code == 404
    assert client.get(f"/api/items/{item.id}/asset/nope").status_code == 404
