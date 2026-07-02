"""Track 2 #4/#5 — the delivery loop: vetted sheet › composed › honest gap,
read-only against the corpus, LLM-free (invariants §10)."""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library import seed_blocks
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.compose import compose
from teachersaid.pipeline.deliver import deliver
from teachersaid.schema.worksheet import BundleRequest
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.demandstore import DemandStore
from teachersaid.store.models import ReviewItem
from teachersaid.store.repository import ReviewStore

IN = date(2026, 3, 1)
TOPIC = "Strahlung und Radioaktivität"


@pytest.fixture
def stores(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    bs = BlockStore(tmp_path / "blocks")
    seed_blocks(bs)
    return ReviewStore(tmp_path / "store"), bs, DemandStore(tmp_path / "demand")


def test_composed_fallback_is_deterministic_and_read_only(stores):
    rs, bs, ds = stores
    r = deliver("Physik", 4, TOPIC, "doppelstunde",
                review_store=rs, block_store=bs, demand_store=ds, today=IN)
    assert r.mode == "composed" and r.content is not None
    assert r.n_tasks >= 1 and r.est_minutes > 0
    # delivery is read-only on success: nothing staged, no wish recorded
    assert rs.list() == [] and ds.list() == []


def test_vetted_library_worksheet_preferred(stores):
    rs, bs, ds = stores
    content, res = compose("Physik", 4, TOPIC, block_store=bs, today=IN)
    assemble(content, res)
    item = rs.create(ReviewItem(
        id="", stage="content", status="approved", title=TOPIC,
        request=BundleRequest(subject="Physik", klasse=4, topic_raw=TOPIC,
                              envelope="doppelstunde"),
        content=content))
    r = deliver("Physik", 4, TOPIC, "doppelstunde",
                review_store=rs, block_store=bs, demand_store=ds, today=IN)
    assert r.mode == "library" and r.item_id == item.id and r.n_tasks >= 1


def test_gap_records_a_demand_wish(stores):
    rs, bs, ds = stores
    r = deliver("Physik", 2, "Quantencomputer im Ozean", "doppelstunde",
                review_store=rs, block_store=bs, demand_store=ds, today=IN)
    assert r.mode == "gap" and r.demand_id
    rec = ds.get(r.demand_id)
    assert rec is not None and rec.status == "open"
    assert rec.subject == "Physik" and rec.klasse == 2 and rec.note
    # the honest note names the async corpus-loop fulfillment, not live generation
    assert "Lücke" in r.note
