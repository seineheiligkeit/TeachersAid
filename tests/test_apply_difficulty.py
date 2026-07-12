"""The C4 difficulty-label loop: proposals (tools/propose_difficulty.py) + the SME-run
apply step (tools/apply_difficulty.py).

Covers, offline: the apply round-trip against a TEMP store (an accepted proposal sets
`block.difficulty` through the status-preserving upsert — never un-approves); idempotency
(a re-run applies nothing and appends no second provenance entry); the fail-fast
all-or-nothing validation (unknown block id, non-task target, band outside 1-3, a
non-boolean `accepted` edit slip — each aborts with ZERO writes); accepted=null/false are
skipped; --dry-run writes neither blocks nor provenance; and the shipped proposals
artifact in runs/difficulty/ (schema sanity, count consistency, ids resolve in the real
corpus, and — while the corpus still carries zero authored labels — the cue group equals
the live `stats.difficulty_review_cues` list, the anti-rot check).
"""

from __future__ import annotations

import json

import pytest

from teachersaid.config import RUNS_DIR
from teachersaid.library.block import LibraryBlock
from teachersaid.schema.blocks import InfoBlock, TaskBlock
from teachersaid.schema.response import LinesResponse
from teachersaid.store.blockstore import BlockStore
from tools import apply_difficulty as ad

PROPOSALS_PATH = RUNS_DIR / "difficulty" / "difficulty_proposals.json"


# --- fixtures ------------------------------------------------------------------------------

def _task(bid="t1", level="apply"):
    return TaskBlock(id=bid, kind="open_response", prompt="Erkläre den Wasserkreislauf.",
                     response=LinesResponse(n=2), cognitive_level=level,
                     dimensions=["S"], est_minutes=10)


def _lb(bid, *, status="approved", role="task"):
    if role == "task":
        block = _task()
        kind = "open_response"
    else:
        block = InfoBlock(id="i1", kind="prose", content="Ein Lerntext.")
        kind = "prose"
    return LibraryBlock(id=bid, block=block, role=role, kind=kind,
                        subject="Physik", klasse=4, status=status)


@pytest.fixture()
def store(tmp_path):
    bs = BlockStore(tmp_path / "blocks")
    bs.upsert(_lb("blk-approved", status="approved"))
    bs.upsert(_lb("blk-review", status="in_review"))
    bs.upsert(_lb("blk-info", role="info"))
    return bs


def _doc(*props):
    return {"version": 1, "proposals": list(props)}


def _prop(bid, band, accepted=True):
    return {"block_id": bid, "proposed_difficulty": band, "accepted": accepted}


# --- the apply round-trip -------------------------------------------------------------------

def test_apply_sets_difficulty_and_stamps_provenance(store):
    doc = _doc(_prop("blk-approved", 2))
    summary = ad.apply_proposals(doc, store)
    assert summary["applied"] == ["blk-approved"]
    assert summary["already_set"] == []
    assert store.get("blk-approved").block.difficulty == 2
    # provenance the light way: applied_at on the proposal + one applications log entry
    assert doc["proposals"][0]["applied_at"]
    assert len(doc["applications"]) == 1 and doc["applications"][0]["applied"] == 1
    assert summary["doc_changed"] is True


def test_apply_preserves_status_and_created_at(store):
    before = store.get("blk-approved")
    assert before.status == "approved"
    ad.apply_proposals(_doc(_prop("blk-approved", 3)), store)
    after = store.get("blk-approved")
    assert after.status == "approved"            # never un-approved
    assert after.created_at == before.created_at  # upsert discipline
    assert after.block.difficulty == 3
    # an in_review block keeps its status too
    ad.apply_proposals(_doc(_prop("blk-review", 1)), store)
    assert store.get("blk-review").status == "in_review"


def test_apply_is_idempotent(store):
    doc = _doc(_prop("blk-approved", 2))
    ad.apply_proposals(doc, store)
    first_stamp = doc["proposals"][0]["applied_at"]
    summary2 = ad.apply_proposals(doc, store)
    assert summary2["applied"] == []
    assert summary2["already_set"] == ["blk-approved"]
    assert summary2["doc_changed"] is False
    assert doc["proposals"][0]["applied_at"] == first_stamp   # first application date kept
    assert len(doc["applications"]) == 1                      # no second log entry


def test_accepted_null_and_false_are_skipped(store):
    doc = _doc(_prop("blk-approved", 2, accepted=None),
               _prop("blk-review", 2, accepted=False))
    summary = ad.apply_proposals(doc, store)
    assert summary["applied"] == [] and summary["already_set"] == []
    assert summary["skipped_null"] == 1 and summary["rejected"] == 1
    assert store.get("blk-approved").block.difficulty is None
    assert store.get("blk-review").block.difficulty is None
    assert "applications" not in doc                          # nothing applied → no log


# --- fail-fast validation (all-or-nothing) ---------------------------------------------------

def test_unknown_block_id_hard_fails_and_nothing_is_applied(store):
    doc = _doc(_prop("blk-approved", 2), _prop("blk-nonexistent", 2))
    with pytest.raises(ad.ApplyError, match="unknown block id"):
        ad.apply_proposals(doc, store)
    # atomic: the VALID proposal in the same file was not applied either
    assert store.get("blk-approved").block.difficulty is None
    assert "applications" not in doc


def test_non_task_target_hard_fails(store):
    with pytest.raises(ad.ApplyError, match="not a task block"):
        ad.apply_proposals(_doc(_prop("blk-info", 2)), store)


def test_band_out_of_range_hard_fails(store):
    with pytest.raises(ad.ApplyError, match="not 1, 2 or 3"):
        ad.apply_proposals(_doc(_prop("blk-approved", 4)), store)


def test_non_boolean_accepted_hard_fails_not_silently_skipped(store):
    doc = _doc({"block_id": "blk-approved", "proposed_difficulty": 2, "accepted": "ja"})
    with pytest.raises(ad.ApplyError, match="not true/false/null"):
        ad.apply_proposals(doc, store)
    assert store.get("blk-approved").block.difficulty is None


def test_unknown_version_hard_fails(store):
    with pytest.raises(ad.ApplyError, match="version"):
        ad.apply_proposals({"version": 99, "proposals": []}, store)


# --- dry-run + the file round-trip -----------------------------------------------------------

def test_dry_run_writes_neither_blocks_nor_provenance(store, tmp_path):
    path = tmp_path / "props.json"
    path.write_text(json.dumps(_doc(_prop("blk-approved", 2))), encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    summary = ad.apply_file(path, store, dry_run=True)
    assert summary["applied"] == ["blk-approved"]             # the plan names it…
    assert store.get("blk-approved").block.difficulty is None  # …but nothing is written
    assert path.read_text(encoding="utf-8") == before
    assert summary["doc_changed"] is False


def test_apply_file_round_trip_and_rerun(store, tmp_path):
    path = tmp_path / "props.json"
    path.write_text(json.dumps(_doc(_prop("blk-approved", 2))), encoding="utf-8")
    s1 = ad.apply_file(path, store)
    assert s1["applied"] == ["blk-approved"]
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["proposals"][0]["applied_at"]              # provenance persisted
    assert len(on_disk["applications"]) == 1
    # idempotent re-run from the persisted file: nothing new, file byte-identical
    before = path.read_text(encoding="utf-8")
    s2 = ad.apply_file(path, store)
    assert s2["applied"] == [] and s2["already_set"] == ["blk-approved"]
    assert path.read_text(encoding="utf-8") == before


# --- the shipped proposals artifact -----------------------------------------------------------

REQUIRED_FIELDS = {
    "block_id", "group", "subject", "klasse", "kind", "cognitive_level", "status",
    "effective_band", "effective_source", "computed_band", "computed_score",
    "computed_drivers", "intrinsic_nudge", "direction", "proposed_difficulty",
    "agrees_with_fallback", "prompt_excerpt", "rationale_de", "accepted",
}


def test_shipped_proposals_schema_sanity():
    doc = json.loads(PROPOSALS_PATH.read_text(encoding="utf-8"))
    assert doc["version"] in ad.KNOWN_VERSIONS
    props = doc["proposals"]
    c = doc["counts"]
    assert c["total"] == len(props) == c["cues"] + c["sample"]
    assert 120 <= c["total"] <= 150                      # the agreed review budget
    ids = [p["block_id"] for p in props]
    assert len(ids) == len(set(ids))                     # no duplicate proposals
    store = BlockStore()
    for p in props:
        assert REQUIRED_FIELDS <= set(p)
        assert p["group"] in ("cue", "sample")
        assert p["proposed_difficulty"] in (1, 2, 3)
        assert p["effective_band"] in (1, 2, 3) and p["computed_band"] in (1, 2, 3)
        assert p["accepted"] in (True, False, None)
        assert p["rationale_de"].strip()                 # every proposal argues its band
        lb = store.get(p["block_id"])                    # stale file ⇒ regenerate (--force)
        assert lb is not None and lb.role == "task", p["block_id"]
    # a cue proposal may agree with the fallback (an explicit confirmation), but the cue
    # group must contain real divergence in BOTH directions — no manufactured uniformity
    cues = [p for p in props if p["group"] == "cue"]
    assert any(p["proposed_difficulty"] < p["effective_band"] for p in cues)
    assert any(p["proposed_difficulty"] > p["effective_band"] for p in cues)
    assert any(p["agrees_with_fallback"] for p in cues)
    # sample proposals confirm the (agreeing) two-signal band by construction
    assert all(p["agrees_with_fallback"] for p in props if p["group"] == "sample")


def test_shipped_cue_group_matches_live_review_cues():
    """Anti-rot: while the corpus carries no authored labels, the artifact's cue group is
    exactly the live C4 review-cue list. (Once the SME applies labels, the live cues shift
    by design — the check then gates itself off; a stale file before that fails loudly.)"""
    store = BlockStore()
    authored_any = any(
        getattr(lb.block, "difficulty", None) is not None
        for lb in store.list() if lb.role == "task")
    if authored_any:
        pytest.skip("authored labels present — the proposals artifact predates them by design")
    from teachersaid.stats import difficulty_review_cues
    live = {c["block_id"] for c in difficulty_review_cues(limit=10_000)["cues"]}
    doc = json.loads(PROPOSALS_PATH.read_text(encoding="utf-8"))
    in_file = {p["block_id"] for p in doc["proposals"] if p["group"] == "cue"}
    assert in_file == live
