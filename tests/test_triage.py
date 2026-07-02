"""Track 1 #3c — the review-triage layer: the deterministic attention heuristic, the
feedback-informed `attention` combination, the queue's attention-first ordering, and
the verdict ingest (triage ranks, the SME decides)."""

from __future__ import annotations

from teachersaid.pipeline.triage import attention, heuristic
from teachersaid.schema.worksheet import BundleRequest
from teachersaid.store.arrangementstore import ArrangementStore
from teachersaid.store.assetstore import AssetStore
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.datasetstore import DatasetStore
from teachersaid.store.feedbackstore import FeedbackEntry, FeedbackStore
from teachersaid.store.models import ReviewItem
from teachersaid.store.repository import ReviewStore
from teachersaid.store.reviewqueue import queue
from teachersaid.store.sachverhaltstore import SachverhaltStore
from teachersaid.store.textstore import TextStore
from tools.ingest_triage import ingest


def _entry(**kw) -> dict:
    """A minimal queue-envelope dict (the shape `reviewqueue._entry` emits)."""
    base = dict(kind="item", id="c0001", title="Testblatt", subject="Physik", klasse=4,
                status="pending", tier="voll", updated_at="2026-07-01T00:00:00+00:00",
                warnings=[], n_warnings=0, n_tasks=5)
    base.update(kw)
    return base


def _item(title="Blatt", topic="T", **kw) -> ReviewItem:
    return ReviewItem(
        id="", stage="content", status="pending", title=title,
        request=BundleRequest(subject="Physik", klasse=4, topic_raw=topic,
                              envelope="doppelstunde"), **kw)


def _stores(tmp_path) -> dict:
    return dict(
        items=ReviewStore(tmp_path / "store"), blocks=BlockStore(tmp_path / "blocks"),
        assets=AssetStore(tmp_path / "assets"), datasets=DatasetStore(tmp_path / "ds"),
        texts=TextStore(tmp_path / "texts"),
        sachverhalte=SachverhaltStore(tmp_path / "sach"),
        arrangements=ArrangementStore(tmp_path / "arr"))


# --- the deterministic heuristic ---------------------------------------------

def test_heuristic_monotone_in_warnings_and_capped():
    s0, _ = heuristic(_entry())
    s2, r2 = heuristic(_entry(n_warnings=2, warnings=["a", "b"]))
    s9, _ = heuristic(_entry(n_warnings=9))
    assert s0 < s2 < s9
    assert any("Prüf-Hinweise" in r for r in r2)
    assert s9 == heuristic(_entry(n_warnings=4))[0]   # +10 per warning, capped at +40


def test_heuristic_tier_ordering():
    scores = {t: heuristic(_entry(tier=t))[0]
              for t in ("bestaetigen", "quelle", "sprache", "voll")}
    assert scores["voll"] > scores["sprache"] > scores["quelle"] > scores["bestaetigen"]
    _, reasons = heuristic(_entry(tier="voll"))
    assert "Stufe: voll lesen" in reasons


def test_heuristic_flags_empty_and_incomplete_and_clamps():
    base = heuristic(_entry())[0]
    s_empty, r = heuristic(_entry(n_tasks=0))
    assert s_empty == base + 30 and "keine Aufgaben" in r
    _, r2 = heuristic(_entry(subject=None))
    assert "unvollständige Metadaten" in r2
    s_max, _ = heuristic(_entry(n_warnings=99, n_tasks=0, subject=None, klasse=None))
    assert s_max == 100   # 40 + 20 + 30 + 10, clamped to the 0–100 band


# --- attention: heuristic + the latest triage verdict -------------------------

def test_attention_combines_latest_triage_feedback(tmp_path):
    fs = FeedbackStore(tmp_path / "fb")
    base = attention(_entry(), fs)
    assert base["rating"] is None and base["score"] == heuristic(_entry())[0]

    fs.add(FeedbackEntry(target_kind="item", target_id="c0001", rating=1,
                         comment="Triage: schwach", tags=["triage"], revise=True))
    a = attention(_entry(), fs)
    assert a["rating"] == 1
    assert a["score"] == base["score"] + (3 - 1) * 10 + 25   # bubbles up
    assert "Triage: überarbeiten empfohlen" in a["reasons"]

    # a later, good verdict supersedes (latest wins) and sinks the score
    fs.add(FeedbackEntry(target_kind="item", target_id="c0001", rating=5,
                         tags=["triage"]))
    a5 = attention(_entry(), fs)
    assert a5["rating"] == 5
    assert a5["score"] == max(0, base["score"] + (3 - 5) * 10)

    # non-triage feedback is ignored by triage
    fs.add(FeedbackEntry(target_kind="item", target_id="c0002", rating=1,
                         tags=["unklar"]))
    assert attention(_entry(id="c0002"), fs)["rating"] is None


# --- queue: attention-first ordering ------------------------------------------

def test_queue_sorts_warned_item_first(tmp_path):
    s = _stores(tmp_path)
    s["items"].create(_item(title="Sauber", topic="A"))
    s["items"].create(_item(title="Mit Hinweisen", topic="B",
                            verify_warnings=["W1", "W2"]))
    q = queue(**s)
    assert [e["title"] for e in q["entries"]] == ["Mit Hinweisen", "Sauber"]
    assert all("triage" in e for e in q["entries"])
    assert q["entries"][0]["triage"]["score"] > q["entries"][1]["triage"]["score"]


def test_queue_feedback_kwarg_reranks(tmp_path):
    s = _stores(tmp_path)
    a = s["items"].create(_item(title="A", topic="A"))
    s["items"].create(_item(title="B", topic="B"))
    fs = FeedbackStore(tmp_path / "fb")
    fs.add(FeedbackEntry(target_kind="item", target_id=a.id, rating=1, tags=["triage"]))
    q = queue(**s, feedback=fs)
    assert q["entries"][0]["id"] == a.id                     # the weak verdict bubbles up
    assert q["entries"][0]["triage"]["rating"] == 1
    assert q["entries"][1]["triage"]["rating"] is None


# --- the triage brief ----------------------------------------------------------

def test_brief_carries_item_tasks(tmp_path):
    from teachersaid.demo import strahlung
    from tools.triage_prompt import render_brief
    s = _stores(tmp_path)
    s["items"].create(_item(title="Strahlung", topic="Strahlung",
                            content=strahlung.build_content()))
    brief = render_brief(queue(**s), s["items"])
    assert "strenge" in brief and "verdicts.json" in brief   # role + output contract
    assert "gibst NICHTS frei" in brief                      # triage only, SME is the gate
    assert "Kernfrage:" in brief and "Lösung:" in brief      # item content made it in


# --- verdict ingest -------------------------------------------------------------

def test_ingest_validates_and_writes_feedback(tmp_path):
    s = _stores(tmp_path)
    it = s["items"].create(_item())
    entries = queue(**s)["entries"]
    fs = FeedbackStore(tmp_path / "fb")
    verdicts = [
        {"kind": "item", "id": it.id, "rating": 2, "attention": "hoch",
         "reasons": ["Leiter flach", "Lösung t3 passt nicht"],
         "watch": "answer_key von t3 lesen"},
        {"kind": "item", "id": "c9999", "rating": 3, "attention": "mittel"},   # unknown id
        {"kind": "item", "id": it.id, "rating": 9, "attention": "hoch"},       # bad rating
        {"kind": "item", "id": it.id, "rating": 3, "attention": "sofort"},     # bad attention
    ]
    assert ingest(verdicts, entries, fs) == (1, 3)
    got = fs.for_target("item", it.id)
    assert len(got) == 1
    e = got[0]
    assert e.rating == 2 and e.tags == ["triage"] and e.revise is True
    assert e.comment == "Triage: Leiter flach; Lösung t3 passt nicht — answer_key von t3 lesen"
    assert e.subject == "Physik" and e.label == "Blatt"      # denormalised from the envelope

    # dry-run validates but writes nothing
    assert ingest(verdicts, entries, fs, dry_run=True) == (1, 3)
    assert len(fs.for_target("item", it.id)) == 1

    # attention "mittel"/"niedrig" record without the revise flag
    ingest([{"kind": "item", "id": it.id, "rating": 4, "attention": "niedrig",
             "reasons": ["solide"]}], entries, fs)
    solid = [e for e in fs.for_target("item", it.id) if e.rating == 4]
    assert len(solid) == 1 and solid[0].revise is False
