"""Lernarrangement (schema v0.5) — the GWB Gemeinderat hero.

Locks the v0.5 payoff: each role's material is a real worksheet that verifies
clean, and the arrangement-level Nachweis covers competences NO single worksheet
reaches (ENT.05 via the debate, ENT.01 via the shared council decision).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from teachersaid.demo import gwb_standort
from teachersaid.pipeline.arrange import assemble_arrangement, verify_arrangement
from teachersaid.pipeline.resolve import resolve_grade
from teachersaid.schema.arrangement import CompetenceAnchor, Lernarrangement
from teachersaid.schema.enums import Role

IN = date(2026, 3, 1)


def _resolved():
    arr = gwb_standort.build_arrangement()
    res = resolve_grade(gwb_standort.SUBJECT, gwb_standort.KLASSE, today=IN)
    assert res.grade_check is True  # GWB grade 3 is catalog-valid
    assemble_arrangement(arr, res)
    return arr, res


def test_hero_assembles_and_verifies_clean():
    arr, res = _resolved()
    rep = verify_arrangement(arr, res)
    assert rep.problems == [], rep.problems
    assert len(arr.roles) == 4
    assert arr.nachweis is not None and arr.depth_profile is not None
    assert arr.total_minutes() == 80


def test_each_role_material_is_a_verified_worksheet():
    arr, _ = _resolved()
    for role in arr.roles:
        assert role.material.nachweis is not None
        assert role.material.depth_profile is not None


def test_nachweis_covers_anchor_only_competences():
    """The crux of v0.5: ENT.05 and ENT.01 are covered ONLY through the arrangement
    layer (interaction / shared product), never by a printable role task."""
    arr, _ = _resolved()
    cov = {c.competence_id: c for c in arr.nachweis.competence_coverage}

    # role worksheets exercise these (a real block id, not an anchor marker)
    for cid in ["GWB.US.3.ENT.03", "GWB.US.3.ENT.06", "GWB.US.3.ENT.07", "GWB.US.3.ZEN.03"]:
        assert cov[cid].covered, cid
        assert any(not e.startswith("anchor:") for e in cov[cid].exercised_by), cid

    # anchors: covered, but ONLY via the arrangement (no role task touches them)
    for cid in ["GWB.US.3.ENT.05", "GWB.US.3.ENT.01"]:
        assert cov[cid].covered, cid
        assert cov[cid].exercised_by and all(e.startswith("anchor:") for e in cov[cid].exercised_by), cid

    assert "verankert" in arr.nachweis.statement  # statement names the anchor-only count


def test_depth_profile_aggregates_all_role_tasks():
    arr, _ = _resolved()
    dp = arr.depth_profile
    task_min = sum(b.est_minutes for r in arr.roles
                   for b in r.material.iter_blocks() if b.role == Role.TASK)
    assert sum(dp.by_level.values()) == 8  # 4 roles × 2 tasks
    assert dp.minutes_total == task_min
    assert dp.by_dimension.get("OK") and dp.by_dimension.get("UK")  # GWB dims aggregated


def test_roundtrip_and_format():
    arr, _ = _resolved()
    again = Lernarrangement.model_validate(arr.model_dump())
    assert again.meta.title == arr.meta.title
    assert again.meta.format == "simulation_game" and len(again.roles) == 4


def test_render_arrangement_bundle(tmp_path):
    """5b: the run-guide renders + rasterises, and every role yields a student handout
    and a teacher copy (renderArrangement = orchestration + roles.map(studentSheet))."""
    from teachersaid.pipeline.arrange import render_arrangement
    from teachersaid.rendering.qa_raster import rasterise

    arr, _ = _resolved()
    out = render_arrangement(arr, tmp_path)

    orch = Path(out["orchestration"])
    assert orch.exists() and orch.stat().st_size > 1500
    assert len(out["roles"]) == 4
    for r in out["roles"]:
        assert Path(r["student"]).exists() and Path(r["teacher"]).exists()
    # the run-guide is a valid, multi-page PDF
    pages = rasterise(orch, out_dir=tmp_path / "raster")
    assert len(pages) >= 2 and all(p.exists() for p in pages)


def test_verify_catches_bad_anchor_and_grouping():
    arr, res = _resolved()
    arr.competence_anchors.append(
        CompetenceAnchor(competence_id="GWB.US.9.XXX.99", dimension="UK", served_by="interaction"))
    arr.phases[0].grouping = "bogus"
    rep = verify_arrangement(arr, res)
    assert any("unknown competence" in p for p in rep.problems)
    assert any("invalid grouping" in p for p in rep.problems)


def test_stage_and_store_roundtrip(tmp_path, monkeypatch):
    """5c: stage_arrangement assembles + verifies + renders + stores; upsert preserves
    review status (re-seeding never un-approves)."""
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.pipeline.arrange import stage_arrangement
    from teachersaid.store.arrangementstore import ArrangementStore

    store = ArrangementStore(tmp_path / "arrangements")
    rec = stage_arrangement(store, gwb_standort.build_arrangement(),
                            arr_id="gwb", source="curated", today=IN)
    assert rec.status == "in_review" and rec.verify_problems == []
    assert rec.artifacts.orchestration and Path(rec.artifacts.orchestration).exists()
    assert len(rec.artifacts.roles) == 4
    s = rec.summary()
    assert s["n_roles"] == 4 and s["n_anchors"] == 2 and s["covered"] >= 6

    store.set_status("gwb", "approved")
    rec2 = stage_arrangement(store, gwb_standort.build_arrangement(), arr_id="gwb", today=IN)
    assert rec2.status == "approved"  # idempotent re-stage preserves status


def test_api_arrangements(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod
    from teachersaid.pipeline.arrange import stage_arrangement
    from teachersaid.store.arrangementstore import ArrangementStore

    appmod.ARRANGEMENTS = ArrangementStore(tmp_path / "arrangements")
    stage_arrangement(appmod.ARRANGEMENTS, gwb_standort.build_arrangement(),
                      arr_id="gwb", source="curated", today=IN)
    client = TestClient(appmod.app)

    lst = client.get("/api/arrangements").json()
    assert lst and lst[0]["id"] == "gwb" and lst[0]["n_roles"] == 4
    rec = client.get("/api/arrangements/gwb").json()
    assert rec["arrangement"]["meta"]["format"] == "simulation_game"
    # the run-guide + role sheets serve as PDFs
    assert client.get("/api/arrangements/gwb/pdf/orchestration").status_code == 200
    assert client.get("/api/arrangements/gwb/pdf/gem/student").status_code == 200
    assert client.get("/api/arrangements/gwb/pdf/gem/teacher").status_code == 200
    assert client.get("/api/arrangements/gwb/pdf/nope/student").status_code == 404
    assert client.post("/api/arrangements/gwb/approve").json()["status"] == "approved"


def _gen_arr_body():
    """A minimal-but-real generated GWB grade-3 arrangement body (catalog ids)."""
    def material(pfx, cid, dim):
        return {
            "intro": [{"role": "info", "id": pfx + "i", "kind": "prose",
                       "content": "Lies dein Rollenblatt und kläre deine Interessen."}],
            "sections": [{"id": pfx + "s", "title": "Fraktionsarbeit", "throughline": "x",
                          "talking_points": ["?"], "extensions": [], "blocks": [
                {"role": "task", "id": pfx + "t1", "kind": "open_response",
                 "prompt": "Stelle deine Position dar und begründe sie.",
                 "response": {"mode": "lines", "n": 3}, "cognitive_level": "understand",
                 "dimensions": [dim], "serves": [{"competence_id": cid, "relation": "exercises"}],
                 "est_minutes": 7, "answer_key": "Position mit Begründung."}]}],
            "assets": [],
        }
    return {
        "common_material": [{"role": "info", "id": "case", "kind": "prose",
                             "content": "Eine Gemeinde streitet über ein Bauprojekt."}],
        "roles": [
            {"id": "pro", "label": "Befürworter:innen",
             "material": material("p", "GWB.US.3.ENT.03", "OK")},
            {"id": "con", "label": "Gegner:innen",
             "material": material("c", "GWB.US.3.ZEN.03", "OK")},
        ],
        "phases": [{"id": "ph1", "label": "Debatte", "grouping": "plenary", "minutes": 20,
                    "what_happens": "Moderierte Debatte mit Statements und Repliken."}],
        "shared_product": {"description": "Ein begründeter Beschluss.",
                           "rubric": [{"criterion": "Begründung", "levels": ["schwach", "stark"]}]},
        "debrief": [{"role": "info", "id": "db", "kind": "prose",
                     "content": "Reflexion: Welcher Konflikt war am schwersten?"}],
        "competence_anchors": [{"competence_id": "GWB.US.3.ENT.05", "dimension": "UK",
                                "served_by": "interaction"}],
    }


def test_ingest_arrangement_seam(tmp_path, monkeypatch):
    """5d: a generated arrangement body up-converts → assembles → verifies clean, with
    the anchor (ENT.05) covered only through the interaction."""
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.pipeline.arrange import ingest_arrangement
    from teachersaid.store.arrangementstore import ArrangementStore

    store = ArrangementStore(tmp_path / "arrangements")
    rec = ingest_arrangement(
        store, "Geographie und wirtschaftliche Bildung", 3, title="Test-Debatte",
        kernfrage="Soll gebaut werden?", format="role_debate",
        body=_gen_arr_body(), arr_id="t", today=IN)
    assert rec.verify_problems == [], rec.verify_problems
    assert len(rec.arrangement.roles) == 2 and rec.artifacts.orchestration
    cov = {c.competence_id: c for c in rec.arrangement.nachweis.competence_coverage}
    assert cov["GWB.US.3.ENT.05"].covered
    assert all(e.startswith("anchor:") for e in cov["GWB.US.3.ENT.05"].exercised_by)
