"""Körpernetze: true face geometry, scene projection, and parametric surface tasks."""
from __future__ import annotations

from collections import Counter, defaultdict, deque
import re
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from teachersaid.library.templates import find_template, variant_worksheet
from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.figtext import overlap_pairs
from teachersaid.pipeline.nets import cuboid_net, solid_net_scene
from teachersaid.pipeline.parametrize import make_variants_with_assets
from teachersaid.pipeline.scene import Label, Line, Region, render_scene
from teachersaid.pipeline.verify import verify
from teachersaid.schema.assets import Asset

PNG = b"\x89PNG\r\n\x1a\n"
IN_WINDOW = date(2026, 3, 1)


def _layers(scene, kind):
    return [layer for layer in scene.layers if isinstance(layer, kind)]


def test_cuboid_net_has_the_true_six_face_dimensions_and_area():
    layout = cuboid_net(7, 5, 3)
    dims = Counter(tuple(sorted(face.dimensions)) for face in layout.faces)
    assert dims == Counter({("a", "b"): 2, ("a", "c"): 2, ("b", "c"): 2})
    assert Counter(face.area for face in layout.faces) == Counter({35: 2, 21: 2, 15: 2})
    assert sum(face.area for face in layout.faces) == 2 * (7 * 5 + 7 * 3 + 5 * 3)


def test_cuboid_net_fold_adjacencies_form_a_connected_tree():
    layout = cuboid_net(6, 4, 2)
    adj = layout.adjacencies()
    assert len(layout.faces) == 6 and len(layout.folds) == 5
    assert len(adj) == 5
    assert set(adj.values()) == set(layout.folds)  # every and only full shared edge is a fold

    graph: dict[str, set[str]] = defaultdict(set)
    for left, right in adj:
        graph[left].add(right)
        graph[right].add(left)
    seen = {"base"}
    todo = deque(seen)
    while todo:
        todo.extend(graph[todo.popleft()] - seen)
        seen |= set(todo)
    assert seen == {face.name for face in layout.faces}  # connected + |E|=|V|-1 → tree


def test_cube_net_is_six_congruent_squares():
    layout = cuboid_net(4, 4, 4)
    assert all(face.width == face.height == 4 for face in layout.faces)
    assert sum(face.area for face in layout.faces) == 6 * 4**2


def test_solid_net_scene_projects_faces_folds_and_spec_labels():
    spec = {"kind": "cuboid", "a": 6, "b": 4, "c": 3,
            "label_a": "a = 6 cm", "label_b": "b = 4 cm", "label_c": "c = 3 cm",
            "result_label": "O = ?", "title": "Quadernetz"}
    scene = solid_net_scene(spec)
    assert len(_layers(scene, Region)) == 6
    assert len(_layers(scene, Line)) == 5
    assert all(line.dash != "solid" for line in _layers(scene, Line))
    assert {label.text for label in _layers(scene, Label)} == {
        "a = 6 cm", "b = 4 cm", "c = 3 cm", "O = ?",
    }
    assert scene.canvas.aspect == "equal"


def test_cube_spec_uses_one_symbolic_side_label_by_default():
    labels = [label.text for label in _layers(solid_net_scene({"kind": "cube", "side": 3}), Label)]
    assert labels == ["a"]


def test_solid_net_is_registered_and_builds_a_real_png(tmp_path):
    assert "matplotlib:solid_net" in GENERATION_RECIPES
    asset = Asset(id="quader-netz", role="figure", generator="matplotlib:solid_net",
                  spec={"a": 5, "b": 4, "c": 2, "label_a": "a", "label_b": "b",
                        "label_c": "c", "result_label": "O = ?"})
    path = build_asset(asset, outdir=tmp_path)
    assert path.exists() and path.read_bytes()[:8] == PNG and path.stat().st_size > 1500


def test_solid_net_labels_do_not_overlap():
    # Includes the most elongated dimensions emitted by the parametric recipe.
    for a, b, c in ((2, 3, 8), (8, 7, 2), (7, 2, 6), (5, 4, 3)):
        scene = solid_net_scene({
            "a": a, "b": b, "c": c,
            "label_a": f"a = {a} cm", "label_b": f"b = {b} cm",
            "label_c": f"c = {c} cm", "result_label": "O = ?",
            "title": "Netz eines Quaders",
        })
        with plt.rc_context(fs.house_rc()):
            fig, ax = plt.subplots(figsize=scene.canvas.figsize, layout="constrained")
            render_scene(scene, ax)
            pairs = overlap_pairs(fig)
            plt.close(fig)
        assert pairs == [], ((a, b, c), pairs)


def test_quader_surface_recipe_is_derived_and_figure_masks_the_result():
    template = find_template("mat-quader-oberflaeche")
    assert template is not None
    assert template.klasse == 1
    assert template.serves[0].competence_id == "MAT.US.1.FIG.03"
    blocks, assets = make_variants_with_assets(template, 8, seed0=1)
    assert len(blocks) == len(assets) == 8
    by_id = {asset.id: asset for asset in assets}
    for block in blocks:
        asset = by_id[block.asset_refs[0]]
        assert asset.generator == "matplotlib:solid_net"
        a, b, c = (int(asset.spec[key]) for key in ("a", "b", "c"))
        result = 2 * (a * b + a * c + b * c)
        assert block.answer_key == f"O = {result} cm²"
        shown = " ".join(str(asset.spec.get(key, "")) for key in
                         ("label_a", "label_b", "label_c", "result_label", "title"))
        assert asset.spec["result_label"] == "O = ?"
        assert not re.search(rf"\b{result}\b", shown), (result, shown)


def test_quader_surface_worksheet_assembles_and_verifies_clean(tmp_path):
    template = find_template("mat-quader-oberflaeche")
    assert template is not None
    content, resolved = variant_worksheet(template, 3, today=IN_WINDOW)
    content = assemble(content, resolved)
    report = verify(content, resolved)
    assert not report.problems, report.problems
    paths = [build_asset(asset, outdir=tmp_path) for asset in content.assets]
    assert len(paths) == 3 and all(path.read_bytes()[:8] == PNG for path in paths)
