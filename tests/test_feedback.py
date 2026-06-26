"""The HITL feedback loop: rich feedback (rating + comment + tags), decoupled from
approve/reject, aggregated into a digest the AI consumes."""

from __future__ import annotations

from teachersaid.store.feedbackstore import FeedbackEntry, FeedbackStore


def test_store_add_for_target_and_digest(tmp_path):
    fs = FeedbackStore(tmp_path / "fb")
    fs.add(FeedbackEntry(target_kind="block", target_id="b1", subject="Physik",
                         label="t1", rating=2, comment="zu leicht", tags=["zu leicht"]))
    fs.add(FeedbackEntry(target_kind="block", target_id="b1", subject="Physik",
                         label="t1", rating=5, comment="jetzt top"))
    fs.add(FeedbackEntry(target_kind="item", target_id="c1", subject="Biologie",
                         label="Zelle", revise=True, comment="bitte überarbeiten"))

    assert len(fs.for_target("block", "b1")) == 2
    d = fs.digest()
    assert d["total"] == 3 and d["avg_rating"] == 3.5      # (2+5)/2
    # attention = low rating OR revise OR attention-tag
    att = {(e["target_id"], e["revise"]) for e in d["attention"]}
    assert ("b1", False) in att and ("c1", True) in att
    assert any(e["target_id"] == "b1" and e["rating"] == 5 for e in d["praise"])
    assert dict(d["tags"]).get("zu leicht") == 1
    subj = {s["subject"]: s for s in d["by_subject"]}
    assert subj["Physik"]["avg_rating"] == 3.5 and subj["Biologie"]["n"] == 1


def test_api_feedback_roundtrip_and_digest(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    from teachersaid.library import seed_blocks
    from teachersaid.store.blockstore import BlockStore
    from teachersaid.store.feedbackstore import FeedbackStore

    appmod.BLOCKS = BlockStore(tmp_path / "blocks")
    appmod.STORE = type(appmod.STORE)(tmp_path / "store")
    appmod.FEEDBACK = FeedbackStore(tmp_path / "fb")
    seed_blocks(appmod.BLOCKS)
    client = TestClient(appmod.app)

    bid = appmod.BLOCKS.list()[0].id
    r = client.post("/api/feedback", json={"target_kind": "block", "target_id": bid,
                                           "rating": 2, "comment": "Beispiel fehlt",
                                           "tags": ["unklar"]}).json()
    assert r["rating"] == 2 and r["subject"]      # subject denormalised from the block

    got = client.get(f"/api/feedback?target_kind=block&target_id={bid}").json()
    assert len(got) == 1 and got[0]["comment"] == "Beispiel fehlt"

    # bad inputs are rejected
    assert client.post("/api/feedback", json={"target_kind": "bogus", "target_id": "x"}).status_code == 400
    assert client.post("/api/feedback", json={"target_kind": "block", "target_id": "x",
                                              "rating": 9}).status_code == 400

    d = client.get("/api/feedback/digest").json()
    assert d["total"] == 1 and any(e["target_id"] == bid for e in d["attention"])  # rating 2 + 'unklar'
    assert "tags" in client.get("/api/feedback/tags").json()
