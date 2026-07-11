"""The deterministic "Varianten erzeugen" API and staging surface."""
from __future__ import annotations

from fastapi.testclient import TestClient

from teachersaid.store.repository import ReviewStore


def _client(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    from teachersaid.api import app as appmod

    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    appmod.STORE = ReviewStore(tmp_path / "store")
    return TestClient(appmod.app), appmod


def test_templates_endpoint_lists_curated_anchors(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    rows = client.get("/api/templates").json()
    assert rows and len({row["id"] for row in rows}) == len(rows)
    quader = next(row for row in rows if row["id"] == "mat-quader-oberflaeche")
    assert quader == {
        "id": "mat-quader-oberflaeche",
        "subject": "Mathematik",
        "klasse": 1,
        "title": "Quadernetz: Oberflächeninhalt",
        "anchor": ["MAT.US.1.FIG.03"],
        "kompetenzbereich": "3: Figuren und Körper",
        "recipe": "quader_oberflaeche",
    }


def test_create_figure_variants_stages_verify_clean_preview_item(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    response = client.post("/api/variants", json={
        "template_id": "mat-quader-oberflaeche", "n": 3, "ramp": False,
    })
    assert response.status_code == 200
    summary = response.json()
    assert summary["stage"] == "content" and summary["status"] == "pending"
    assert summary["source"] == "variants" and summary["error"] is None

    item = client.get(f"/api/items/{summary['id']}").json()
    assert item["verify_problems"] == []
    assert len(item["content"]["assets"]) == 3
    assert all(asset["generator"] == "matplotlib:solid_net"
               for asset in item["content"]["assets"])
    for kind in ("student", "teacher", "homework"):
        pdf = client.get(f"/api/items/{summary['id']}/pdf/{kind}")
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_ramp_reaches_ascending_difficulty_bands(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    summary = client.post("/api/variants", json={
        "template_id": "mat-lineare-gleichung", "n": 3, "ramp": True,
    }).json()
    item = client.get(f"/api/items/{summary['id']}").json()
    blocks = item["content"]["sections"][0]["blocks"]
    assert [block["difficulty"] for block in blocks if block["role"] == "task"] == [1, 2, 3]
    assert "ansteigend" in item["title"]
    assert item["verify_problems"] == []


def test_variants_endpoint_rejects_unknown_template_and_bad_count(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    assert client.post("/api/variants", json={"template_id": "nope", "n": 3}).status_code == 404
    assert client.post("/api/variants", json={"template_id": "mat-prozent", "n": 0}).status_code == 422
    assert client.post("/api/variants", json={"template_id": "mat-prozent", "n": 31}).status_code == 422
