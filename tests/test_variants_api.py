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


def test_variants_endpoint_accepts_p1_mixer_profile(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    summary = client.post("/api/variants", json={
        "template_id": "mat-prozent-mc",
        "n": 6,
        "mixer_profile": {"umfang": "kompakt", "offenheit": "offen"},
    }).json()
    item = client.get(f"/api/items/{summary['id']}").json()
    content = item["content"]
    assert len(content["sections"][0]["blocks"]) == 4
    assert content["mixer_profile"]["offenheit"] == "offen"
    assert content["mixer_lint"]["passed"] is True
    assert all(block["kind"] == "open_response"
               for block in content["sections"][0]["blocks"])


def test_variants_endpoint_accepts_p2_geruest_profile(tmp_path, monkeypatch):
    # P4 owns the dashboard; the API must accept the extended typed profile unchanged.
    client, _ = _client(tmp_path, monkeypatch)
    summary = client.post("/api/variants", json={
        "template_id": "phy-us-ohm-mc",
        "n": 3,
        "mixer_profile": {"geruest": "gestuetzt"},
    }).json()
    item = client.get(f"/api/items/{summary['id']}").json()
    content = item["content"]
    assert content["mixer_profile"]["geruest"] == "gestuetzt"
    assert content["mixer_lint"]["passed"] is True
    assert any(m["fader"] == "geruest" for m in content["mixer_lint"]["movements"])
    tasks = [b for b in content["sections"][0]["blocks"] if b["role"] == "task"]
    assert tasks and all(b["scaffold"] is not None for b in tasks)


def test_variants_endpoint_accepts_p3_textlast_profile(tmp_path, monkeypatch):
    # P4 owns the dashboard; the API must accept the extended typed profile unchanged.
    client, _ = _client(tmp_path, monkeypatch)
    summary = client.post("/api/variants", json={
        "template_id": "fin-lohnzettel",
        "n": 4,
        "mixer_profile": {"textlast": "einfach"},
    }).json()
    item = client.get(f"/api/items/{summary['id']}").json()
    content = item["content"]
    assert content["mixer_profile"]["textlast"] == "einfach"
    assert content["mixer_lint"]["passed"] is True
    assert any(m["fader"] == "textlast" and m["high_value"] < m["low_value"]
               for m in content["mixer_lint"]["movements"])
    assert content["glossary"]                       # Wortschatz selected onto the worksheet
    tasks = [b for b in content["sections"][0]["blocks"] if b["role"] == "task"]
    assert tasks and all("bleibt davon netto" in str(b["prompt"]) for b in tasks)


def test_variants_endpoint_rejects_unknown_template_and_bad_count(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    assert client.post("/api/variants", json={"template_id": "nope", "n": 3}).status_code == 404
    assert client.post("/api/variants", json={"template_id": "mat-prozent", "n": 0}).status_code == 422
    assert client.post("/api/variants", json={"template_id": "mat-prozent", "n": 31}).status_code == 422
