"""The node-link scene family + the first-class stage/density selector.

Locks: the three consolidated recipes (tree_diagram · cause_effect · process_flow) still render
through build_asset with their frozen spec contracts and the right structure (the tree's p-labels,
the cause→effect fan-out, the cyclic process closing its loop); `Scene.select` keeps untagged
layers + named groups in order; the migrated triangle construction reproduces the legacy per-stage
layer counts; the new Node/Arrow primitives render; and a dense tree has no label overlaps. Offline.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.constructions import construction_scene, triangle_geometry
from teachersaid.pipeline.figtext import overlap_pairs
from teachersaid.pipeline.nodelink import cause_effect_scene, process_scene, tree_scene
from teachersaid.pipeline.scene import (Arrow, Canvas, Line, Node, PointMark, Polyline, Scene,
                                        render_scene)
from teachersaid.schema.assets import Asset

PNG = b"\x89PNG\r\n\x1a\n"

_TREE = {"title": "Zweistufig", "branches": [
    {"label": "A", "p": "0,3", "children": [{"label": "T", "p": "0,8"}, {"label": "K", "p": "0,2"}]},
    {"label": "B", "p": "0,7", "children": [{"label": "T", "p": "0,5"}, {"label": "K", "p": "0,5"}]}]}


def _render(asset_id, generator, spec, tmp_path):
    p = build_asset(Asset(id=asset_id, role="figure", generator=generator, spec=spec),
                    outdir=tmp_path)
    return p


def _layers(scene, kind):
    return [L for L in scene.layers if isinstance(L, kind)]


# --- spec-contract parity for the three consolidated recipes -----------------
def test_tree_diagram_renders_and_carries_its_p_labels(tmp_path):
    p = _render("tr", "matplotlib:tree_diagram", _TREE, tmp_path)
    assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1500
    # every branch probability is present as a chip (spec-provided; never invented)
    chips = {n.text for n in _layers(tree_scene(_TREE), Node)}
    assert {"0,3", "0,7", "0,8", "0,2", "0,5"} <= chips
    # a chip per p-bearing edge (2 roots + 4 children = 6 edges, all with p)
    assert len(_layers(tree_scene(_TREE), Node)) == 6
    assert len(_layers(tree_scene(_TREE), Line)) == 6                 # one edge per branch


def test_cause_effect_renders_and_fans_out(tmp_path):
    # one cause driving two effects → one cause box, two effect boxes, two arrows (the fan-out)
    spec = {"title": "W", "links": [{"cause": "X", "effect": "Y1"}, {"cause": "X", "effect": "Y2"}]}
    p = _render("ce", "matplotlib:cause_effect", spec, tmp_path)
    assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1000
    sc = cause_effect_scene(spec)
    assert len(_layers(sc, Node)) == 3 and len(_layers(sc, Arrow)) == 2
    # distinct causes/effects only (a repeated cause is not duplicated)
    spec2 = {"links": [{"cause": "X", "effect": "Y"}, {"cause": "X", "effect": "Y"}]}
    assert len(_layers(cause_effect_scene(spec2), Node)) == 2          # 1 cause + 1 effect


def test_process_cyclic_closes_the_loop(tmp_path):
    steps = [{"name": f"S{i}"} for i in range(5)]
    spec = {"steps": steps, "cyclic": True, "title": "Kreis"}
    p = _render("pc", "matplotlib:process_flow", spec, tmp_path)
    assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1500
    sc = process_scene(spec)
    arrows, nodes = _layers(sc, Arrow), _layers(sc, Node)
    assert len(nodes) == 5
    assert len(arrows) == 5                                            # n arrows for n steps: it loops
    # the last arrow returns to the first node's position (the loop is closed)
    assert arrows[-1].q == nodes[0].p
    assert any(a.curve for a in arrows)                               # the cyclic arrows are curved


def test_process_linear_and_short_cyclic(tmp_path):
    lin = {"steps": [{"name": "A"}, {"name": "B"}, {"name": "C"}], "cyclic": False}
    p = _render("pl", "matplotlib:process_flow", lin, tmp_path)
    assert p.read_bytes()[:8] == PNG and p.stat().st_size > 800
    sc = process_scene(lin)
    assert len(_layers(sc, Node)) == 3 and len(_layers(sc, Arrow)) == 2   # n-1, no loop
    # a short cyclic process (n<3 → linear layout) still gets a curved loop-back arrow
    short = process_scene({"steps": [{"name": "A"}, {"name": "B"}], "cyclic": True})
    arrows = _layers(short, Arrow)
    assert len(arrows) == 2 and any(a.curve for a in arrows)          # 1 step + 1 loop-back
    # an empty process degrades to a blank scene, not a crash
    assert process_scene({"steps": []}).layers == []


# --- Scene.select: the first-class stage/density selector --------------------
def test_select_keeps_untagged_and_named_in_order():
    sc = Scene(canvas=Canvas())
    sc.add(Line((0, 0), (1, 1)),                    # untagged — always kept
           Line((0, 0), (2, 2), group="a"),
           Line((0, 0), (3, 3), group="b"),
           Line((0, 0), (4, 4), group="a"))
    sel = sc.select("a")
    assert [L.group for L in sel.layers] == [None, "a", "a"]          # untagged + only group "a"
    assert sc.select().layers == [sc.layers[0]]                      # no groups → only untagged
    assert len(sc.select("a", "b").layers) == 4                      # both groups → all four
    # order is preserved (the untagged base stays first, groups interleave in original order)
    assert sel.layers[0] is sc.layers[0] and sel.layers[1] is sc.layers[1]
    # select does not mutate the source scene
    assert len(sc.layers) == 4


# --- the migrated triangle construction reproduces the legacy per-stage counts ---
def test_construction_stage_layer_counts_match_legacy():
    g = triangle_geometry((0.0, 0.0), (8.0, 0.0), (1.5, 4.0))
    counts = {s: len(construction_scene(g, s).layers) for s in range(1, 7)}
    # the exact counts the hand-rolled stage 1–6 if-chain produced (before the select migration)
    assert counts == {1: 10, 2: 9, 3: 10, 4: 10, 5: 11, 6: 13}


def test_construction_untagged_base_survives_every_stage():
    """The triangle + its three vertices are UNTAGGED, so `select` keeps them at every stage."""
    g = triangle_geometry((0.0, 0.0), (8.0, 0.0), (1.5, 4.0))
    for stage in range(1, 7):
        sc = construction_scene(g, stage)
        assert len(_layers(sc, Polyline)) == 1                       # the triangle outline
        verts = [m for m in _layers(sc, PointMark) if m.label in {"A", "B", "C"} and m.group is None]
        assert len(verts) == 3
        assert sc.canvas.xlim and sc.canvas.ylim                     # framed on the circumcircle


# --- the new primitives render + a dense tree stays legible -------------------
def test_node_and_arrow_primitives_render(tmp_path):
    sc = Scene(canvas=Canvas(frame="off", xlim=(0, 4), ylim=(0, 3)))
    sc.add(Node((1, 1.5), "Ursache", face_role="surface", edge_role="ink"),
           Node((3, 1.5), "Folge", face_role="surface_warm", edge_role="focus"),
           Arrow((1.6, 1.5), (2.4, 1.5), curve=0.0),
           Arrow((1.6, 2.5), (2.4, 2.5), curve=0.3))
    with plt.rc_context(fs.house_rc()):
        fig, ax = plt.subplots(figsize=(4, 3), layout="constrained")
        render_scene(sc, ax)
        # the arrows are empty-text annotations → not counted as label overlaps
        assert overlap_pairs(fig) == []
        plt.close(fig)


def test_dense_tree_has_no_label_overlaps():
    # a denser tree (3 first-stage branches × 2 outcomes = 6 leaves), the case that stresses
    # label collisions — the measured legibility guard (figtext.overlap_pairs)
    dense = {"branches": [
        {"label": s, "p": "0,3", "children": [{"label": "T", "p": "0,6"}, {"label": "K", "p": "0,4"}]}
        for s in ("A", "B", "C")]}
    sc = tree_scene(dense)
    with plt.rc_context(fs.house_rc()):
        fig, ax = plt.subplots(figsize=sc.canvas.figsize, layout="constrained")
        render_scene(sc, ax)
        pairs = overlap_pairs(fig)
        plt.close(fig)
    assert pairs == [], pairs
