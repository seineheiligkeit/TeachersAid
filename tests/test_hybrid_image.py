from __future__ import annotations

from pathlib import Path

import pytest

from teachersaid.library import bio_bluete_hybrid as flower
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.labeled_diagram import FLOWER_HYBRID_SPEC, labeled_parts_scene
from teachersaid.pipeline.scene import Label, RasterImage
from teachersaid.schema.assets import Asset
from teachersaid.store.assetstore import AssetStore

# The flower cutaway is an AI-generated, file-backed depictive asset: its PNG is git-ignored
# (persistence policy) and — unlike code-gen figures — cannot self-heal on a clone (no seed,
# diffusion backend offline). build_asset resolves the background via AssetStore().get(...).file,
# so guard the build-dependent test on that exact path: it runs where the SME generated the
# binary and skips on a fresh remote clone (mirrors the ANNO scan-crop guard).
_flower_record = AssetStore().get("img-bio-flower-cutaway")
_FLOWER_BINARY_PRESENT = bool(
    _flower_record and _flower_record.file and Path(_flower_record.file).is_file())
needs_flower_binary = pytest.mark.skipif(
    not _FLOWER_BINARY_PRESENT,
    reason="flower cutaway binary absent (git-ignored, AI-generated with no seed — "
           "present only where it was generated)")


def test_hybrid_spec_keeps_pixels_and_task_meaning_separate():
    spec = {**FLOWER_HYBRID_SPEC, "background": {
        **FLOWER_HYBRID_SPEC["background"], "path": __file__}}
    scene = labeled_parts_scene(spec, show_names=False)
    assert sum(isinstance(layer, RasterImage) for layer in scene.layers) == 1
    assert {layer.text for layer in scene.layers if isinstance(layer, Label)} == {
        str(i) for i in range(1, 8)}


def test_flagship_student_teacher_share_parts_and_only_teacher_has_names():
    content = flower.build_content()
    student, teacher = content.assets
    assert student.spec["parts"] == teacher.spec["parts"]
    assert student.spec["show_names"] is False
    assert teacher.spec["show_names"] is True
    assert student.spec["background"]["asset_id"] == "img-bio-flower-cutaway"
    assert content.sections[0].blocks[0].answer_key.startswith("1 Kronblatt")


@needs_flower_binary
def test_hybrid_build_resolves_the_stored_candidate(tmp_path):
    asset = flower.build_content().assets[0]
    path = build_asset(asset, outdir=tmp_path)
    assert path.exists() and path.stat().st_size > 0


def test_content_approval_waits_for_independent_asset_review(tmp_path, monkeypatch):
    from teachersaid.pipeline import orchestrator as orch
    from teachersaid.pipeline.resolve import resolve_grade
    from teachersaid.store.assetstore import AssetStore, LibraryAsset
    from teachersaid.store.repository import ReviewStore

    store = ReviewStore(tmp_path / "review")
    # Inject an ISOLATED asset store so the test never depends on the machine's live
    # review state (an SME approving the flower asset in the dashboard must not flip
    # this test — the earlier global-store version did exactly that).
    assets = AssetStore(tmp_path / "assets")
    dep_id = "img-bio-flower-cutaway"
    assets.upsert(LibraryAsset(
        id=dep_id, klass="depictive", status="in_review",
        asset=Asset(id=dep_id, role="source", generator="file:raster",
                    spec={"path": "flower.png"})))
    monkeypatch.setattr(orch, "_render_all", lambda *_: None)
    item = orch.stage_worksheet(
        store, flower.build_content(), resolve_grade("Biologie", 1), source="curated")

    # The dependency is only in_review → content approval must BLOCK.
    with pytest.raises(ValueError, match="separate SME approval"):
        orch.approve_content(store, item.id, asset_store=assets)

    # Once the asset is independently approved, the content approval goes through.
    assets.set_status(dep_id, "approved")
    approved = orch.approve_content(store, item.id, asset_store=assets)
    assert approved.status == "approved"
