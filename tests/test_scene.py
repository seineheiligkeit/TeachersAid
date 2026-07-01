"""The scene engine + the first construction recipe.

Locks: the triangle geometry is correct-by-construction (the centres satisfy their defining
properties — circumcentre equidistant, incircle tangent, Euler collinearity); every stage
builds a non-empty scene and renders; the recipe is wired into build_asset + the generation
vocabulary; and every scene primitive renders. Offline, no API key.
"""
from __future__ import annotations

import numpy as np

from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.constructions import construction_scene, triangle_geometry
from teachersaid.pipeline.scene import (Arc, Canvas, CircleShape, Label, Line, PointMark,
                                        Polyline, Region, Scene, scene_to_png)
from teachersaid.schema.assets import Asset

_VERTS = ((0.0, 0.0), (8.0, 0.0), (1.5, 4.0))


def _d(p, q) -> float:
    return float(np.hypot(p[0] - q[0], p[1] - q[1]))


def test_triangle_geometry_is_correct_by_construction():
    g = triangle_geometry(*_VERTS)
    A, B, C, U, R, S, H, I, r = (g[k] for k in ("A", "B", "C", "U", "R", "S", "H", "I", "r"))
    # circumcentre is equidistant (= R) from all three vertices
    assert max(abs(_d(U, P) - R) for P in (A, B, C)) < 1e-6
    # centroid is the vertex mean; orthocentre satisfies the Euler relation
    assert np.allclose(S, (A + B + C) / 3)
    assert np.allclose(H, A + B + C - 2 * U)
    # U, S, H are collinear (the Eulergerade) — zero cross product
    assert abs((S[0] - U[0]) * (H[1] - U[1]) - (S[1] - U[1]) * (H[0] - U[0])) < 1e-6
    # incircle: radius = area/s, and the incentre is r from every side
    a, b, c = g["a"], g["b"], g["c"]
    area = 0.5 * abs((B[0] - A[0]) * (C[1] - A[1]) - (C[0] - A[0]) * (B[1] - A[1]))
    assert abs(r - area / ((a + b + c) / 2)) < 1e-9

    def dist_to_line(P, Q, X):
        dseg = Q - P
        nrm = np.array([-dseg[1], dseg[0]])
        nrm = nrm / np.hypot(*nrm)
        return abs(np.dot(X - P, nrm))
    assert max(abs(dist_to_line(P, Q, I) - r) for P, Q in ((A, B), (B, C), (C, A))) < 1e-6


def test_geometry_rederives_when_a_vertex_moves():
    """Move a vertex → the circumradius changes (nothing is hand-placed)."""
    g1 = triangle_geometry(*_VERTS)
    g2 = triangle_geometry((0.0, 0.0), (8.0, 0.0), (1.5, 5.5))
    assert abs(g1["R"] - g2["R"]) > 1e-3


def test_each_construction_stage_builds_a_scene():
    g = triangle_geometry(*_VERTS)
    for stage in range(1, 7):
        sc = construction_scene(g, stage)
        assert isinstance(sc, Scene) and sc.layers
        assert sc.canvas.xlim and sc.canvas.ylim


def test_later_stages_accumulate_layers():
    g = triangle_geometry(*_VERTS)
    # stage 6 (all four families' results + Euler + Feuerbach) has more than stage 1 (triangle)
    assert len(construction_scene(g, 6).layers) > len(construction_scene(g, 1).layers)


def test_recipe_renders_through_build_asset(tmp_path):
    for stage in range(1, 7):
        a = Asset(id=f"tri{stage}", role="figure", generator="matplotlib:triangle_construction",
                  spec={"vertices": [list(v) for v in _VERTS], "stage": stage})
        p = build_asset(a, outdir=tmp_path)
        assert p.exists() and p.stat().st_size > 0


def test_recipe_in_generation_vocabulary():
    assert "matplotlib:triangle_construction" in GENERATION_RECIPES


def test_every_scene_primitive_renders(tmp_path):
    sc = Scene(canvas=Canvas(aspect="equal", frame="off"))
    sc.add(
        Polyline([(0, 0), (2, 0), (0, 2)], closed=True),
        Line((0, 0), (2, 2), family=2),
        CircleShape((1, 1), 1.0, role="primary"),
        Arc((0, 0), 0.4, 0, 90, label="α"),
        Region([(0, 0), (2, 0), (0, 2)], role="focus"),
        PointMark((1, 1), label="P", leader=True),
        Label((0.3, 1.5), "Text"),
    )
    p = scene_to_png(sc, tmp_path / "scene.png")
    assert p.exists() and p.stat().st_size > 0
