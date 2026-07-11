"""Wave C3 — fächerübergreifende Projektwoche bundles (übergreifende-Themen).

Locks the two halves: `resolve_uet` (the catalog side — competences carrying a ÜT across
subjects) and `compose_uet` (the corpus side — approved blocks → a cross-subject
Lernarrangement, or an honest gap under two subjects). Plus the real seeded flagship and
the API seam.
"""

from __future__ import annotations

from datetime import date

from teachersaid.config import REPO_ROOT
from teachersaid.grounding import lehrplan_store as ls
from teachersaid.pipeline.arrange import assemble_arrangement, verify_arrangement
from teachersaid.pipeline.compose_uet import MIN_SUBJECTS, compose_uet
from teachersaid.pipeline.resolve import resolve_uet
from teachersaid.store.blockstore import BlockStore

IN = date(2026, 3, 1)
REAL_BLOCKS = REPO_ROOT / "runs" / "blocks"       # the git-tracked approved corpus


# --- resolve_uet: catalog ground truth ---------------------------------------
def test_resolve_uet_spans_subjects_verbatim():
    """ÜT 11 (Umweltbildung) at Kl 4 resolves competences across ≥2 subjects, each verbatim
    carrying the ÜT, with the Fassung stamped."""
    res = resolve_uet(11, 4, today=IN)
    assert res.grade_check and res.competences
    subjects = set()
    for c in res.competences:
        assert 11 in c.uebergreifende_themen, c.id
        m = ls.competence_meta(c.id)
        assert m is not None
        subjects.add(m["subject_code"])
    assert len(subjects) >= 2
    # the sciences + geography + technik all carry Umweltbildung at Kl 4 (catalog truth)
    assert {"PHY", "GWB", "TED", "BIO"} <= subjects
    assert res.fassung.doknr == ls.get_fassung().doknr


def test_resolve_uet_unknown_theme_is_honest():
    res = resolve_uet(999, 4, today=IN)
    assert not res.grade_check and res.competences == []
    assert any("nicht definiert" in n for n in res.notes)


def test_resolve_uet_matches_catalog_exactly():
    """Every competence a subject carries with the ÜT is present — no more, no less."""
    res = resolve_uet(11, 4, today=IN)
    got = {c.id for c in res.competences}
    expect = set()
    for subject in ls.list_subjects("Unterstufe"):
        for c in ls.competences_for(subject, 4, "Unterstufe"):
            if 11 in c.uebergreifende_themen:
                expect.add(c.id)
    assert got == expect


# --- compose_uet: corpus side (fixture store) --------------------------------
def _uet_block(bid, subject, cid, dim, *, level="understand", mins=8):
    """An approved task block serving a real ÜT-carrying competence."""
    from teachersaid.library.block import LibraryBlock
    from teachersaid.schema.blocks import Serves, TaskBlock
    from teachersaid.schema.response import LinesResponse
    task = TaskBlock(
        id=bid, kind="open_response", prompt=f"Erkläre einen Aspekt von {cid}.",
        response=LinesResponse(n=3), cognitive_level=level, dimensions=[dim],
        serves=[Serves(competence_id=cid, relation="exercises")], est_minutes=mins,
        answer_key="Musterlösung.")
    return LibraryBlock(
        id=f"fix.{bid}", block=task, role="task", kind="open_response", subject=subject,
        klasse=4, kompetenzbereich=None, competences=[cid], cognitive_level=level,
        dimensions=[dim], scope="standard", status="approved")


def _fixture_store(tmp_path, monkeypatch, blocks):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    bs = BlockStore(tmp_path / "blocks")
    for b in blocks:
        bs.upsert(b)
    return bs


GWB = "Geographie und wirtschaftliche Bildung"


def test_compose_uet_builds_verifiable_cross_subject_arrangement(tmp_path, monkeypatch):
    """≥2 subjects with approved ÜT blocks → a Lernarrangement whose every role verifies as a
    worksheet (each against its OWN subject resolution), with a shared-product anchor covering a
    ÜT competence NO printable role task reaches (the v0.5 payoff)."""
    bs = _fixture_store(tmp_path, monkeypatch, [
        _uet_block("phy1", "Physik", "PHY.US.4.WET.02", "W"),
        _uet_block("phy2", "Physik", "PHY.US.4.WET.04", "W", level="apply"),
        _uet_block("gwb1", GWB, "GWB.US.4.MEN.01", "OK"),
    ])
    res = compose_uet(11, 4, "doppelstunde", block_store=bs, today=IN)
    assert res.ok, res.gap
    assert set(res.subjects) == {"Physik", GWB}
    arr = res.arrangement
    assert arr.meta.format == "stations" and len(arr.roles) == 2

    # verifies as an arrangement (each role checked against its OWN subject resolution)
    rep = verify_arrangement(arr, res.resolution, role_resolutions=res.role_resolutions)
    assert rep.problems == [], rep.problems

    # assemble fills the DERIVED fields (compose_uet builds, staging assembles) — per-role
    # Nachweise are subject-scoped (not polluted with the other subject's competences)
    assemble_arrangement(arr, res.resolution, role_resolutions=res.role_resolutions)
    for role in arr.roles:
        assert role.material.nachweis is not None
        prefixes = {c.competence_id.split(".")[0]
                    for c in role.material.nachweis.competence_coverage}
        assert prefixes == {role.id.upper()}, prefixes  # subject-scoped, not cross-polluted

    # the v0.5 payoff: the shared-product anchor is a ÜT competence covered ONLY via the anchor
    assert len(arr.competence_anchors) == 1
    anchor = arr.competence_anchors[0]
    assert anchor.served_by == "shared_product"
    cov = {c.competence_id: c for c in arr.nachweis.competence_coverage}
    a = cov[anchor.competence_id]
    assert a.covered and a.exercised_by and all(e.startswith("anchor:") for e in a.exercised_by)
    assert "verankert" in arr.nachweis.statement
    assert 11 in arr.nachweis.uebergreifende_themen


def test_compose_uet_honest_gap_under_two_subjects(tmp_path, monkeypatch):
    """A single subject's ÜT blocks cannot make a fächerübergreifendes bundle → an honest gap,
    not a thin one-subject arrangement."""
    bs = _fixture_store(tmp_path, monkeypatch, [
        _uet_block("phy1", "Physik", "PHY.US.4.WET.02", "W"),
        _uet_block("phy2", "Physik", "PHY.US.4.WET.04", "W"),
    ])
    res = compose_uet(11, 4, "doppelstunde", block_store=bs, today=IN)
    assert not res.ok and res.arrangement is None
    assert res.subjects == ["Physik"]
    assert res.gap and str(MIN_SUBJECTS) in res.gap


def test_compose_uet_gap_for_uncurated_theme(tmp_path, monkeypatch):
    bs = _fixture_store(tmp_path, monkeypatch, [
        _uet_block("phy1", "Physik", "PHY.US.4.WET.02", "W"),
    ])
    res = compose_uet(999, 4, block_store=bs, today=IN)
    assert not res.ok and res.gap


# --- the real seeded flagship + staging --------------------------------------
def test_seeded_uet_flagship_stages_and_verifies(tmp_path, monkeypatch):
    """The real Wave-C3 flagship: ÜT 11 × Kl 4 composed from the approved corpus, staged
    verify-clean with ≥2 subject roles and its shared-product anchor."""
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from pathlib import Path

    from teachersaid.library import seed_uet_arrangements
    from teachersaid.store.arrangementstore import ArrangementStore

    arr_store = ArrangementStore(tmp_path / "arrangements")
    out = seed_uet_arrangements(arr_store, BlockStore(REAL_BLOCKS), today=IN)[0]
    assert out["mode"] == "staged", out
    rec = arr_store.get("uet-umweltbildung-4")
    assert rec is not None and rec.verify_problems == [], rec.verify_problems
    s = rec.summary()
    assert s["n_roles"] >= MIN_SUBJECTS and s["n_anchors"] == 1
    assert s["format"] == "stations"
    # the run-guide + every role sheet rendered
    assert Path(rec.artifacts.orchestration).exists()
    assert rec.artifacts.roles and all(
        Path(r["student"]).exists() and Path(r["teacher"]).exists() for r in rec.artifacts.roles)

    # idempotent re-seed preserves an approval
    arr_store.set_status("uet-umweltbildung-4", "approved")
    seed_uet_arrangements(arr_store, BlockStore(REAL_BLOCKS), today=IN)
    assert arr_store.get("uet-umweltbildung-4").status == "approved"


def test_api_compose_uet(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    from teachersaid.store.arrangementstore import ArrangementStore
    from teachersaid.store.demandstore import DemandStore

    appmod.BLOCKS = BlockStore(REAL_BLOCKS)          # the real approved corpus
    appmod.ARRANGEMENTS = ArrangementStore(tmp_path / "arrangements")
    appmod.DEMAND = DemandStore(tmp_path / "demand")
    client = TestClient(appmod.app)

    # the legend endpoint feeds the compose form
    leg = client.get("/api/uebergreifende-themen?klasse=4").json()["uebergreifende_themen"]
    assert any(t["nr"] == 11 and "Umwelt" in t["label"] for t in leg)

    r = client.post("/api/compose-uet", json={"uet": 11, "klasse": 4}).json()
    assert r["mode"] == "staged" and r["n_roles"] >= MIN_SUBJECTS and r["problems"] == []
    lst = client.get("/api/arrangements").json()
    assert any(a["id"] == r["id"] for a in lst)
    assert client.get(f"/api/arrangements/{r['id']}/pdf/orchestration").status_code == 200

    # an uncurated ÜT gaps into the Wunschliste instead
    g = client.post("/api/compose-uet", json={"uet": 999, "klasse": 4}).json()
    assert g["mode"] == "gap" and g["demand_id"]
    assert any(d["id"] == g["demand_id"] for d in client.get("/api/demand").json())
