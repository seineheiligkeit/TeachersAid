"""HITL pipeline end-to-end (offline): brainstorm → flesh out → content → library."""

from __future__ import annotations

import pytest

from teachersaid.pipeline import orchestrator as orch
from teachersaid.store.repository import ReviewStore


@pytest.fixture(autouse=True)
def _no_key(monkeypatch):
    # Force the offline master-library fallback so the loop runs without network.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture
def store(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    return ReviewStore(tmp_path / "store")


def test_brainstorm_to_library_loop(store):
    bs = orch.submit_brainstorm(store, "Physik", 4, "Strahlung und Radioaktivität",
                                "Energie entscheidet über Gefahr", source="user")
    assert bs.stage == "brainstorm" and bs.status == "pending" and bs.note

    orch.approve_brainstorm(store, bs.id)
    assert store.get(bs.id).status == "approved"

    # flesh out -> a content item (offline hero), rendered + derived
    content = orch.flesh_out(store, bs.id)
    assert content.stage == "content"
    assert content.error is None, content.error
    assert content.content.nachweis is not None
    assert content.artifacts.student_pdf and content.artifacts.teacher_pdf
    assert content.parent_id == bs.id
    # the deliberate STR.01 gap surfaces
    assert any(g.startswith("PHY.US.4.STR.01") for g in content.content.nachweis.gaps)

    approved = orch.approve_content(store, content.id)
    assert approved.status == "approved"
    assert len(store.library()) == 1


def test_request_changes_requeues_content(store):
    bs = orch.submit_brainstorm(store, "Physik", 4, "Strahlung und Radioaktivität")
    orch.approve_brainstorm(store, bs.id)
    content = orch.flesh_out(store, bs.id)
    updated = orch.request_changes(store, content.id, "Bitte Aufgabe 6 vereinfachen.")
    assert updated.id == content.id  # same item, regenerated
    assert any(f.decision == "request-changes" for f in updated.feedback)
    assert updated.status == "pending"


def test_suggest_from_catalog_walks_kompetenzbereiche(store):
    items = orch.suggest_from_catalog(store, "Physik", 4)
    # Physik 4. Kl.: Wetter und Klima + Strahlung und Radioaktivität
    assert len(items) == 2
    assert all(i.stage == "brainstorm" and i.source == "ai" for i in items)
    topics = {i.request.topic_raw for i in items}
    assert "Strahlung und Radioaktivität" in topics and "Wetter und Klima" in topics
    # idempotent: a second call adds nothing (already represented)
    assert orch.suggest_from_catalog(store, "Physik", 4) == []


def test_api_endpoints(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient
    from teachersaid.api import app as appmod

    appmod.STORE = ReviewStore(tmp_path / "store")
    client = TestClient(appmod.app)

    assert client.get("/").status_code == 200
    bs = client.post("/api/brainstorm", json={"subject": "Physik", "klasse": 4,
                                              "topic": "Strahlung und Radioaktivität"}).json()
    client.post(f"/api/items/{bs['id']}/approve")           # approve brainstorm
    content = client.post(f"/api/items/{bs['id']}/flesh-out").json()  # -> content
    cid = content["id"]

    item = client.get(f"/api/items/{cid}").json()
    assert item["content"]["nachweis"]["gaps"]              # STR.01 gap present
    assert item["content"]["sections"]                      # full blocks served for the Blöcke view
    assert client.get(f"/api/items/{cid}/pdf/student").status_code == 200
    assert client.get(f"/api/items/{cid}/pdf/teacher").status_code == 200

    client.post(f"/api/items/{cid}/approve")                # gate 2 -> library
    assert client.get("/api/status").json()["library_size"] == 1
    st = client.get("/api/stats").json()
    assert st["totals"]["worksheets"] == 1 and "subjects" in st
