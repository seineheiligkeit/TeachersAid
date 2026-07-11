"""Wave B I1: generation provenance, raster preflight and best-of-N review."""

from __future__ import annotations

from datetime import date

import pytest
from PIL import Image

from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.image_lint import lint_image
from teachersaid.schema.assets import Asset
from teachersaid.store.assetstore import AssetStore, GenerationRecord, LibraryAsset
from tools.illustration_specimen import render as render_specimen


def _image(path, *, size=(800, 400), alpha=None, flat=False):
    mode = "RGBA" if alpha is not None else "RGB"
    colour = (128, 128, 128, alpha) if alpha is not None else (128, 128, 128)
    image = Image.new(mode, size, colour)
    if not flat:
        fill = (10, 20, 30, alpha) if alpha is not None else (10, 20, 30)
        for x in range(size[0] // 2):
            for y in range(size[1]):
                image.putpixel((x, y), fill)
    image.save(path)
    return path


def test_generation_record_is_honest_without_seed():
    record = GenerationRecord(
        generator="OpenAI image generation", model="gpt-image",
        prompt="full request", negative_prompt="no text", style_prefix="style-v1",
        date=date(2026, 7, 11), reproducibility_parameters={"size": "1536x1024"},
        replayable=True,
    )
    assert record.origin == "synthetic" and record.replayable is False
    seeded = record.model_copy(update={
        "reproducibility_parameters": {"seed": 42}, "replayable": True})
    assert seeded.replayable is True


def test_raster_preflight_flags_resolution_photocopy_and_alpha(tmp_path):
    small = _image(tmp_path / "small.png", size=(120, 80), flat=True)
    report = lint_image(small)
    assert {f.code for f in report.findings} >= {"resolution", "photocopy_contrast"}
    assert not report.passed

    translucent = _image(tmp_path / "alpha.png", alpha=120)
    report = lint_image(translucent, alpha_expectation="opaque")
    assert "stray_alpha" in {f.code for f in report.findings}
    assert report.text_check == "manual_required"


def test_agent_time_generation_ingests_with_claim_provenance_and_preflight(tmp_path):
    source = _image(tmp_path / "candidate.png")
    store = AssetStore(tmp_path / "store")
    asset = Asset(
        id="cafe-01", role="backdrop", lane="depictive",
        intended_claim="Shows an invented Central-European cafe interior without text",
        spec={"alpha_expectation": "opaque"},
    )
    generation = GenerationRecord(
        generator="OpenAI image generation", model="gpt-image",
        prompt="complete prompt", negative_prompt="no text", style_prefix="style-v1",
        date=date(2026, 7, 11), reproducibility_parameters={"size": "800x400"},
    )
    record = orch.ingest_asset(
        store, asset, klass="depictive", file=source, generation=generation,
        candidate_set_id="cafe-backdrop", candidate_index=1,
    )
    assert record.generation and record.generation.origin == "synthetic"
    assert record.preflight and record.preflight.width == 800
    assert record.preflight.text_check.startswith("edge_density:")
    assert record.summary()["intended_claim"].startswith("Shows")

    bad = Asset(id="chart-ai", role="chart", lane="content")
    try:
        orch.ingest_asset(store, bad, klass="depictive", file=source, generation=generation)
    except ValueError as exc:
        assert "depictive" in str(exc) or "media policy" in str(exc)
    else:  # pragma: no cover - documents the hard gate
        raise AssertionError("synthetic content entered the asset library")


def test_best_of_n_selection_approves_exactly_one(tmp_path):
    store = AssetStore(tmp_path)
    for index in range(1, 4):
        store.upsert(LibraryAsset(
            id=f"candidate-{index}",
            asset=Asset(id=f"candidate-{index}", role="decoration", lane="decorative"),
            klass="decorative", candidate_set_id="header-bio", candidate_index=index,
        ))
    selected = store.select_candidate("candidate-2")
    assert selected.status == "approved"
    assert {a.id for a in store.list(status="approved")} == {"candidate-2"}
    assert {a.id for a in store.list(status="rejected")} == {"candidate-1", "candidate-3"}


def test_candidate_set_must_describe_one_coherent_request(tmp_path):
    store = AssetStore(tmp_path)
    store.upsert(LibraryAsset(
        id="one", asset=Asset(id="one", role="depiction", lane="depictive",
                               intended_claim="Shows one leaf"),
        klass="depictive", candidate_set_id="leaf", candidate_index=1))
    with pytest.raises(ValueError, match="share lane"):
        store.upsert(LibraryAsset(
            id="two", asset=Asset(id="two", role="depiction", lane="depictive",
                                   intended_claim="Shows a railway station"),
            klass="depictive", candidate_set_id="leaf", candidate_index=2))


def test_resolution_error_blocks_approval(tmp_path):
    image = _image(tmp_path / "too-small.png", size=(80, 60))
    store = AssetStore(tmp_path / "assets")
    store.upsert(LibraryAsset(
        id="small", asset=Asset(id="small", role="decoration", lane="decorative"),
        klass="decorative", file=str(image), preflight=lint_image(image)))
    with pytest.raises(ValueError, match="preflight"):
        store.select_candidate("small")


def test_best_of_n_api_selection(tmp_path):
    from fastapi.testclient import TestClient
    from teachersaid.api import app as appmod

    store = AssetStore(tmp_path)
    for index in (1, 2):
        store.upsert(LibraryAsset(
            id=f"api-candidate-{index}",
            asset=Asset(id=f"api-candidate-{index}", role="decoration", lane="decorative"),
            klass="decorative", candidate_set_id="api-set", candidate_index=index,
        ))
    old_store = appmod.ASSETS
    try:
        appmod.ASSETS = store
        client = TestClient(appmod.app)
        response = client.post("/api/asset-library/api-candidate-1/select")
        assert response.status_code == 200 and response.json()["status"] == "approved"
        assert store.get("api-candidate-2").status == "rejected"
        response = client.post("/api/asset-library/api-candidate-1/reject-set")
        assert response.status_code == 200
        assert all(a.status == "rejected" for a in store.list())
    finally:
        appmod.ASSETS = old_store


def test_specimen_contact_sheet_uses_approved_assets_only(tmp_path):
    store = AssetStore(tmp_path / "assets")
    approved_file = _image(tmp_path / "approved.png")
    pending_file = _image(tmp_path / "pending.png")
    store.upsert(LibraryAsset(
        id="approved", asset=Asset(id="approved", role="decoration", lane="decorative"),
        klass="decorative", file=str(approved_file), status="approved"))
    store.set_status("approved", "approved")
    store.upsert(LibraryAsset(
        id="pending", asset=Asset(id="pending", role="decoration", lane="decorative"),
        klass="decorative", file=str(pending_file)))
    out = render_specimen(tmp_path / "specimen.png", store=store)
    assert out.exists()
    with Image.open(out) as image:
        assert image.width > 1000 and image.height >= 380
