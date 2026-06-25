"""M5 verification: two-stage HITL loop end-to-end (offline) + API surface."""

from __future__ import annotations

import os

import pytest

from teachersaid.pipeline import orchestrator as orch
from teachersaid.schema.worksheet import BundleRequest
from teachersaid.store.repository import ReviewStore


@pytest.fixture(autouse=True)
def _no_key(monkeypatch):
    # Force the offline hero fallback so the loop runs without network.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture
def store(tmp_path, monkeypatch):
    # Point RUNS_DIR at tmp so renders/store land in the sandbox.
    import teachersaid.config as cfg

    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    return ReviewStore(tmp_path / "store")


def test_full_two_stage_loop_offline(store):
    req = BundleRequest(subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität")
    idea = orch.submit_on_demand(store, req)
    assert idea.stage == "idea" and idea.status == "pending"
    assert idea.plan.competence_ids  # idea-stage artifact present

    # Gate 1 approve -> generates content (offline hero), renders, derives.
    content = orch.approve_idea(store, idea.id)
    assert content.stage == "content"
    assert content.error is None, content.error
    assert content.content.nachweis is not None
    assert content.artifacts.student_pdf and content.artifacts.teacher_pdf
    # the deliberate STR.01 gap surfaces in the dashboard data
    assert any(g.startswith("PHY.US.4.STR.01") for g in content.content.nachweis.gaps)

    # Gate 2 approve -> enters library.
    approved = orch.approve_content(store, content.id)
    assert approved.status == "approved"
    assert len(store.library()) == 1


def test_request_changes_requeues_content(store):
    req = BundleRequest(subject="Physik", klasse=4, topic_raw="Strahlung und Radioaktivität")
    idea = orch.submit_on_demand(store, req)
    content = orch.approve_idea(store, idea.id)
    updated = orch.request_changes(store, content.id, "Bitte Aufgabe 6 vereinfachen.")
    assert updated.id == content.id  # same item, regenerated
    assert any(f.decision == "request-changes" for f in updated.feedback)
    assert updated.status == "pending"


def test_batch_walks_competence_map(store):
    items = orch.submit_batch(store, "Physik", 4)
    # Physik 4. Kl. has two Kompetenzbereiche in the full catalog:
    # "Wetter und Klima" and "Strahlung und Radioaktivität".
    assert len(items) == 2
    assert all(it.stage == "idea" and it.source == "batch" for it in items)
    titles = {it.title for it in items}
    assert any(t.endswith("Strahlung und Radioaktivität") for t in titles)
    assert any(t.endswith("Wetter und Klima") for t in titles)


def test_api_endpoints(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import teachersaid.config as cfg

    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod

    # rebind the module store to the tmp dir
    appmod.STORE = ReviewStore(tmp_path / "store")
    client = TestClient(appmod.app)

    assert client.get("/").status_code == 200  # dashboard serves
    r = client.post("/api/generate", json={"subject": "Physik", "klasse": 4,
                                           "topic": "Strahlung und Radioaktivität"})
    assert r.status_code == 200
    idea_id = r.json()["id"]

    # approve idea -> background fill runs synchronously under TestClient
    r = client.post(f"/api/items/{idea_id}/approve")
    assert r.status_code == 200
    content_id = r.json()["content_item"]["id"]

    item = client.get(f"/api/items/{content_id}").json()
    assert item["content"]["nachweis"]["gaps"]  # STR.01 gap present
    # PDFs are served
    assert client.get(f"/api/items/{content_id}/pdf/student").status_code == 200
    assert client.get(f"/api/items/{content_id}/pdf/teacher").status_code == 200

    # gate 2 approve -> library grows
    client.post(f"/api/items/{content_id}/approve")
    assert client.get("/api/status").json()["library_size"] == 1
