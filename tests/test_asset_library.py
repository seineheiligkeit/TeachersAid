"""Phase 4 #4: decorative kit (svg:), the diffusion: seam, and the asset library.

The asset file-store holds the file-backed classes (decorative + sourced) parallel
to the block library; ingest_asset gates each entry through the media policy.
"""

from __future__ import annotations

import pytest

from teachersaid.library.decorative import kit_assets, seed_assets
from teachersaid.pipeline import assets as A
from teachersaid.pipeline import orchestrator as orch
from teachersaid.schema.assets import Asset
from teachersaid.store.assetstore import AssetStore, LibraryAsset

PNG = b"\x89PNG\r\n\x1a\n"


def test_svg_kit_builds(tmp_path):
    for asset, _tags in kit_assets():
        p = A.build_asset(asset, outdir=tmp_path)
        assert p.exists() and p.read_bytes()[:8] == PNG


def test_diffusion_seam_unconfigured_then_configured(tmp_path):
    a = Asset(id="d", role="decoration", generator="diffusion:mascot", spec={"prompt": "owl"})
    with pytest.raises(A.DiffusionNotConfigured):
        A.build_asset(a, outdir=tmp_path)
    calls = []
    try:
        A.register_diffusion_backend(lambda asset, path: (
            calls.append(asset.id), A._svg_to_png(
                '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"></svg>', path)))
        p = A.build_asset(a, outdir=tmp_path)
        assert p.exists() and calls == ["d"]
    finally:
        A.register_diffusion_backend(None)


def test_asset_store_roundtrip_and_status_preserve(tmp_path):
    store = AssetStore(tmp_path)
    la = LibraryAsset(id="x", asset=Asset(id="x", role="decoration", generator="svg:motif"),
                      klass="decorative", tags=["motif"])
    store.upsert(la)
    assert store.get("x").status == "in_review"
    store.set_status("x", "approved")
    # re-seeding must not un-approve
    store.upsert(LibraryAsset(id="x", asset=Asset(id="x", role="decoration", generator="svg:motif"),
                              klass="decorative", tags=["motif"]))
    assert store.get("x").status == "approved"
    assert store.approved(tag="motif") and store.list(klass="decorative")


def test_ingest_asset_gates_and_stores(tmp_path):
    store = AssetStore(tmp_path)
    asset = Asset(id="kit-badge", role="decoration", generator="svg:badge",
                  spec={"label": "PHY"})
    la = orch.ingest_asset(store, asset, klass="decorative", tags=["badge"])
    assert la.status == "in_review" and la.file and la.tags == ["badge"]
    from pathlib import Path
    assert Path(la.file).exists()
    # a decorative asset that claims content is rejected by the gate
    bad = Asset(id="sneaky", role="decoration", generator="diffusion:x",
                correctness_surface="the real spectrum")
    with pytest.raises(ValueError, match="media policy"):
        orch.ingest_asset(store, bad, klass="decorative")
    # an unknown class is rejected
    with pytest.raises(ValueError, match="class"):
        orch.ingest_asset(store, Asset(id="z", role="decoration", generator="svg:motif"),
                          klass="bogus")


def test_seed_assets(tmp_path):
    store = AssetStore(tmp_path)
    seeded = seed_assets(store)
    assert len(seeded) == len(kit_assets())
    assert all(la.status == "in_review" and la.klass == "decorative" for la in seeded)
    assert store.list(tag="badge")  # subject badges are tagged for reuse


def test_api_asset_library(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from fastapi.testclient import TestClient

    from teachersaid.api import app as appmod

    appmod.ASSETS = AssetStore(tmp_path / "assets_lib")
    seed_assets(appmod.ASSETS)
    client = TestClient(appmod.app)

    lib = client.get("/api/asset-library").json()
    assert lib and all(a["klass"] == "decorative" for a in lib)
    aid = lib[0]["id"]
    # the file serves as an image
    r = client.get(f"/api/asset-library/{aid}/file")
    assert r.status_code == 200 and r.content[:8] == PNG
    # approve flips status; in_review filter then drops it
    assert client.post(f"/api/asset-library/{aid}/approve").json()["status"] == "approved"
    assert all(a["id"] != aid for a in client.get("/api/asset-library?status=in_review").json())
    assert client.get("/api/asset-library/nope/file").status_code == 404
