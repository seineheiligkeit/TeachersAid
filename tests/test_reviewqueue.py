"""Track 1 #3 — the unified review queue: tier classification, aggregation, and
the worksheet→blocks approval cascade."""

from __future__ import annotations

from teachersaid.pipeline import orchestrator as orch
from teachersaid.schema.blocks import TaskBlock
from teachersaid.schema.enums import Role
from teachersaid.schema.worksheet import BundleRequest
from teachersaid.store.arrangementstore import ArrangementStore
from teachersaid.store.assetstore import AssetStore
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.datasetstore import DatasetStore
from teachersaid.store.models import ReviewItem
from teachersaid.store.repository import ReviewStore
from teachersaid.store.reviewqueue import TIERS, queue, tier_for_block
from teachersaid.store.sachverhaltstore import SachverhaltStore
from teachersaid.store.textstore import TextStore
from teachersaid.library.block import LibraryBlock


def _task(**kw) -> TaskBlock:
    base = dict(id="t1", kind="open_response", prompt="Frage?",
                response={"mode": "lines", "n": 2}, cognitive_level="understand",
                est_minutes=5)
    base.update(kw)
    return TaskBlock(**base)


def _lb(block, block_id="b1", **kw) -> LibraryBlock:
    base = dict(id=block_id, block=block, role="task", kind=block.kind,
                subject="Physik", klasse=4, status="in_review",
                provenance="harvested:c9999")
    base.update(kw)
    return LibraryBlock(**base)


def test_block_tiers():
    assert tier_for_block(_lb(_task())) == "voll"
    solved = _task(solution_steps=[{"text": "Schritt 1: rechnen."}])
    assert tier_for_block(_lb(solved)) == "bestaetigen"


def _stores(tmp_path):
    return dict(
        items=ReviewStore(tmp_path / "store"), blocks=BlockStore(tmp_path / "blocks"),
        assets=AssetStore(tmp_path / "assets"), datasets=DatasetStore(tmp_path / "ds"),
        texts=TextStore(tmp_path / "texts"),
        sachverhalte=SachverhaltStore(tmp_path / "sach"),
        arrangements=ArrangementStore(tmp_path / "arr"))


def test_queue_aggregates_kinds_and_lanes(tmp_path):
    s = _stores(tmp_path)
    s["items"].create(ReviewItem(
        id="", stage="content", status="pending", title="Testblatt",
        request=BundleRequest(subject="Physik", klasse=4, topic_raw="T",
                              envelope="doppelstunde")))
    s["blocks"].upsert(_lb(_task()))
    q = queue(**s)
    assert q["total"] == 2 and {e["kind"] for e in q["entries"]} == {"item", "block"}
    assert sum(q["lanes"].values()) == q["total"]
    assert set(q["lanes"]) == set(TIERS)


def test_worksheet_approval_cascades_to_harvested_blocks(tmp_path):
    rs = ReviewStore(tmp_path / "store")
    bs = BlockStore(tmp_path / "blocks")
    item = rs.create(ReviewItem(
        id="c9999", stage="content", status="pending", title="Blatt",
        request=BundleRequest(subject="Physik", klasse=4, topic_raw="T",
                              envelope="doppelstunde")))
    bs.upsert(_lb(_task(), block_id="b1"))
    bs.upsert(_lb(_task(id="t2"), block_id="b2"))
    bs.upsert(_lb(_task(id="t3"), block_id="b3", provenance="harvested:other"))
    orch.approve_content(rs, item.id, block_store=bs)
    assert {b.id: b.status for b in bs.list()} == {
        "b1": "approved", "b2": "approved", "b3": "in_review"}


def test_worksheet_rejection_cascades_too(tmp_path):
    rs = ReviewStore(tmp_path / "store")
    bs = BlockStore(tmp_path / "blocks")
    item = rs.create(ReviewItem(
        id="c9999", stage="content", status="pending", title="Blatt",
        request=BundleRequest(subject="Physik", klasse=4, topic_raw="T",
                              envelope="doppelstunde")))
    bs.upsert(_lb(_task(), block_id="b1"))
    orch.reject(rs, item.id, "zu flach", block_store=bs)
    assert bs.get("b1").status == "rejected"


def test_pruefen_card_detail_endpoints(tmp_path, monkeypatch):
    """The Prüfen focus card renders every kind inline from EXISTING detail endpoints
    (block/dataset/text/sachverhalt/arrangement) — smoke: each returns 200 for cheap
    seeded records. (The arrangement's orchestration-PDF iframe is covered by
    test_arrangement.py::test_arrangement_pdf_self_heals_stale_path.)"""
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    from teachersaid.demo import gwb_standort
    from teachersaid.library.sachverhalt_wiener_kongress import build_sachverhalt
    from teachersaid.library.texts import LORELEY
    from teachersaid.schema.datasets import Dataset, SourceRef
    from teachersaid.store.arrangementstore import ArrangementRecord
    from teachersaid.store.datasetstore import DatasetRecord
    from teachersaid.store.sachverhaltstore import SachverhaltRecord
    from teachersaid.store.textstore import TextRecord

    s = _stores(tmp_path)
    appmod.BLOCKS = s["blocks"]
    appmod.DATASETS = s["datasets"]
    appmod.TEXTS = s["texts"]
    appmod.SACHVERHALTE = s["sachverhalte"]
    appmod.ARRANGEMENTS = s["arrangements"]

    appmod.BLOCKS.upsert(_lb(_task()))
    appmod.DATASETS.upsert(DatasetRecord(id="toy", dataset=Dataset(
        id="toy", title="Toy", unit="x",
        source=SourceRef(publisher="P", title="T", redistributable=True,
                         attribution="Quelle X", licence="CC BY 4.0"),
        series={"a": {"label": "A", "groups": ["x", "y"], "counts": [1, 2]}})))
    appmod.TEXTS.upsert(TextRecord(id=LORELEY.id, text=LORELEY))
    sv = build_sachverhalt()
    appmod.SACHVERHALTE.upsert(SachverhaltRecord(id=sv.id, sachverhalt=sv))
    appmod.ARRANGEMENTS.upsert(ArrangementRecord(
        id="arr1", arrangement=gwb_standort.build_arrangement(), title="Hero"))

    client = TestClient(appmod.app)
    for ep in ["/api/blocks/b1", "/api/datasets/toy", f"/api/texts/{LORELEY.id}",
               f"/api/sachverhalte/{sv.id}", "/api/arrangements/arr1"]:
        assert client.get(ep).status_code == 200, ep
    # the card's dataset figure preview (the same endpoint the Datensätze view embeds)
    r = client.get("/api/datasets/toy/figure", params={"series": "a"})
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"
