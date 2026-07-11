"""The "Beschrifte die Teile" labelled-diagram recipe.

Locks the guarantee that matters for a labelling task: numbering, leader targets and the
solution names are all DERIVED from one `parts` list, so the numbered student figure and the
named teacher solution cannot drift apart — masking (`show_names=False`) is a projection,
exactly like `show_value=False` in the physics scenes. Plus: one marker + one leader per part,
an unknown shape kind is surfaced (never silently skipped), the scene renders through
build_asset, the recipe is in the generation vocabulary, and no callout labels overlap. Offline.
"""
from __future__ import annotations

import pytest

from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.figtext import overlap_pairs
from teachersaid.pipeline.labeled_diagram import VULKAN_SPEC, labeled_parts_scene
from teachersaid.pipeline.scene import Label, Line, PointMark, RasterImage, render_scene
from teachersaid.schema.assets import Asset


# a minimal spec with no line-shapes, so leader Lines are the ONLY Lines (exact counts)
SIMPLE: dict = {
    "title": "Test",
    "figsize": (6.0, 4.4),
    "shapes": [{"kind": "region", "points": [[0, 0], [5, 0], [5, 4], [0, 4]], "color": "surface"}],
    "parts": [{"at": [1.2, 1.0], "name": "Alpha", "side": "left"},
              {"at": [3.8, 3.0], "name": "Beta", "side": "right"}],
}


def _labels(scene) -> list[str]:
    return [L.text for L in scene.layers if isinstance(L, Label)]


def _overlaps(scene) -> list:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context(fs.house_rc()):
        fig, ax = plt.subplots(figsize=scene.canvas.figsize, layout="constrained")
        render_scene(scene, ax)
        fig.canvas.draw()
        pairs = overlap_pairs(fig)
        plt.close(fig)
    return pairs


# --- the task / solution split ------------------------------------------------
def test_numbered_student_vs_named_teacher_projection():
    named = _labels(labeled_parts_scene(VULKAN_SPEC, show_names=True))
    numbered = _labels(labeled_parts_scene(VULKAN_SPEC, show_names=False))
    assert any("Magmakammer" in t for t in named)          # teacher solution carries the names
    assert not any("Magmakammer" in t for t in numbered)   # student sheet is numbers only
    n = len(VULKAN_SPEC["parts"])
    assert set(numbered) == {str(i) for i in range(1, n + 1)}


def test_numbering_and_names_share_one_source():
    # correct-by-construction: the named label for part i is "{i+1}  {name}", the numbered is
    # "{i+1}" — one parts list drives both, so figure and answer key cannot disagree.
    named = _labels(labeled_parts_scene(VULKAN_SPEC, show_names=True))
    for i, part in enumerate(VULKAN_SPEC["parts"]):
        assert any(t.startswith(str(i + 1)) and part["name"] in t for t in named)


def test_show_names_defaults_from_spec():
    # spec default is show_names=True (the learn/solution figure); the arg overrides it
    assert any("Magmakammer" in t for t in _labels(labeled_parts_scene(VULKAN_SPEC)))
    spec = {**VULKAN_SPEC, "show_names": False}
    assert not any("Magmakammer" in t for t in _labels(labeled_parts_scene(spec)))
    assert any("Magmakammer" in t for t in _labels(labeled_parts_scene(spec, show_names=True)))


# --- structure: one marker + one leader per part ------------------------------
def test_one_marker_and_one_leader_per_part():
    sc = labeled_parts_scene(SIMPLE, show_names=False)
    n = len(SIMPLE["parts"])
    assert sum(isinstance(L, PointMark) for L in sc.layers) == n   # a dot ON each part
    assert sum(isinstance(L, Line) for L in sc.layers) == n        # a leader FROM each part


def test_flagship_volcano_marks_all_six_parts():
    sc = labeled_parts_scene(VULKAN_SPEC, show_names=True)
    assert sum(isinstance(L, PointMark) for L in sc.layers) == 6


def test_unknown_shape_kind_raises():
    # surface the mistake — never silently skip a shape the author asked for
    with pytest.raises(ValueError):
        labeled_parts_scene({"shapes": [{"kind": "trapezoid", "points": [[0, 0], [1, 1]]}],
                             "parts": []})


def test_vetted_raster_background_keeps_code_authored_callouts(tmp_path):
    from PIL import Image

    source = tmp_path / "flower.png"
    Image.new("RGB", (80, 60), (236, 231, 218)).save(source)
    spec = {
        "figsize": (5.5, 4.0),
        "background": {"path": str(source), "extent": [0, 8, 0, 6]},
        "parts": [
            {"at": [2.0, 3.0], "name": "Kronblatt", "side": "left"},
            {"at": [5.5, 3.0], "name": "Staubblatt", "side": "right"},
        ],
    }
    scene = labeled_parts_scene(spec, show_names=False)
    assert sum(isinstance(layer, RasterImage) for layer in scene.layers) == 1
    assert _labels(scene) == ["1", "2"]
    assert sum(isinstance(layer, PointMark) for layer in scene.layers) == 2
    assert sum(isinstance(layer, Line) for layer in scene.layers) == 2
    render_scene(scene, __import__("matplotlib.pyplot").pyplot.subplots()[1])


def test_raster_background_requires_explicit_extent_and_resolved_path():
    with pytest.raises(ValueError, match="extent"):
        labeled_parts_scene({"background": {"path": "x.png"}, "parts": []})
    with pytest.raises(ValueError, match="resolved"):
        labeled_parts_scene({"background": {"extent": [0, 1, 0, 1]}, "parts": []})


# --- integration: build_asset, vocabulary, layout -----------------------------
def test_renders_through_build_asset(tmp_path):
    # explicit named/numbered specs + the empty-spec fallback to the curated volcano flagship
    specs = [{"show_names": True}, {"show_names": False}, {}]
    for i, spec in enumerate(specs):
        a = Asset(id=f"lp{i}", role="figure", generator="matplotlib:labeled_parts", spec=spec)
        p = build_asset(a, outdir=tmp_path)
        assert p.exists() and p.stat().st_size > 0


def test_recipe_in_generation_vocabulary():
    assert "matplotlib:labeled_parts" in GENERATION_RECIPES


def test_no_label_overlaps():
    # both projections of the flagship (long names) and the minimal spec must place cleanly
    for spec in (VULKAN_SPEC, SIMPLE):
        for show in (True, False):
            assert _overlaps(labeled_parts_scene(spec, show_names=show)) == []
