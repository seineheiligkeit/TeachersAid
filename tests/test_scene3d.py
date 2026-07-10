"""The 3D scene engine — solids projected to 2D Schrägbilder (roadmap A7).

Locks the correct-by-construction guarantees the promotion rests on: the fixed axonometric map on
hand-computed ℝ³ points; closed-form hidden-line classification on a Quader in general position (the
KNOWN answer — exactly 3 hidden edges, and WHICH ones); the same for prism/pyramid/cylinder/cone;
the riss-pair correspondence (Grundriss = (x,−y), Aufriss = (x,z), shared x across the Rissachse);
maskable measures (task vs. solution); the render smoke for every recipe × solid through
build_asset; the generation vocabulary; and the convexity/occlusion boundary the design doc draws
(non-convex → NotConvex). Offline, no API key.
"""
from __future__ import annotations

import math

import numpy as np

from teachersaid.pipeline import scene3d as s3
from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.scene import Label, Line, Polyline, Scene
from teachersaid.schema.assets import Asset

_ALL_SOLIDS = ("quader", "prism", "pyramid", "cylinder", "cone")


# --- the projection: a fixed linear map, verified on hand-computed points -----
def test_schraegriss_maps_the_unit_axes_as_specified():
    """Kabinettprojektion: ŷ horizontal (1,0), ẑ vertical (0,1), x̂ (depth) at 45° lower-left,
    foreshortened ½ (length 0.5). These six numbers ARE the projection — pin them."""
    assert s3.project((0, 1, 0)) == (1.0, 0.0)          # ŷ → horizontal
    assert s3.project((0, 0, 1)) == (0.0, 1.0)          # ẑ → vertical
    px, py = s3.project((1, 0, 0))                       # x̂ → 45° lower-left, half-length
    assert math.isclose(math.hypot(px, py), 0.5, abs_tol=1e-9)
    assert px < 0 and py < 0 and math.isclose(px, py)   # exactly on the −45° diagonal


def test_projection_is_linear():
    """One linear map ⇒ project(αP + βQ) = α·project(P) + β·project(Q) (the parallel-projection
    property the whole design leans on)."""
    P, Q = (1.0, 2.0, 3.0), (-2.0, 0.5, 4.0)
    lhs = np.array(s3.project((2 * P[0] - Q[0], 2 * P[1] - Q[1], 2 * P[2] - Q[2])))
    rhs = 2 * np.array(s3.project(P)) - np.array(s3.project(Q))
    assert np.allclose(lhs, rhs)


def test_view_direction_is_the_projection_nullspace():
    """The collapsed direction: two points differing only along `view_direction` project to the
    SAME screen point, and it faces the camera (positive z)."""
    d = s3.view_direction()
    p0 = (0.5, -1.0, 0.3)
    p1 = tuple(np.array(p0) + 2.7 * d)
    assert np.allclose(s3.project(p0), s3.project(p1), atol=1e-9)
    assert d[2] > 0


# --- hidden-line determination on a Quader (the known answer) ----------------
def test_quader_has_exactly_three_hidden_edges_at_the_back_corner():
    """A box in general Schrägriss shows exactly 3 hidden edges — the three meeting at the single
    fully-occluded back corner (the origin corner under this view). This is THE reference figure of
    the whole recipe; the closed-form back-face test must reproduce it exactly."""
    q = s3.quader(4, 3, 2.5)
    cls = s3.classify_edges(q, s3.view_direction())
    hidden = sorted(e for e, visible in cls.items() if not visible)
    assert len(cls) == 12                                # a box has 12 edges
    assert len(hidden) == 3
    # the three hidden edges are exactly the ones incident to vertex 0 = (0,0,0)
    assert hidden == [(0, 1), (0, 3), (0, 4)]
    hidden_corner = {v for e in hidden for v in e}
    # every hidden edge touches vertex 0; the other endpoints are its three neighbours
    assert 0 in set.intersection(*[set(e) for e in hidden])
    assert hidden_corner == {0, 1, 3, 4}


def test_a_cube_is_a_quader():
    """a=b=c is a Würfel — same 3-hidden-edge signature."""
    cube = s3.build_solid("wuerfel", a=3, b=3, c=3)
    hidden = [e for e, v in s3.classify_edges(cube, s3.view_direction()).items() if not v]
    assert len(hidden) == 3


def test_visible_and_hidden_edges_partition_the_edge_set():
    """Every edge is classified exactly once as visible or hidden (no edge left unlabelled)."""
    for kind in ("quader", "prism", "pyramid"):
        solid = s3.build_solid(kind)
        cls = s3.classify_edges(solid, s3.view_direction())
        assert all(isinstance(v, bool) for v in cls.values())
        # at least one visible and one hidden edge (a solid seen in Schrägriss always has both)
        assert any(cls.values()) and not all(cls.values())


def test_prism_and_pyramid_classify_and_stay_convex():
    """The other polyhedra classify (some edges hidden) and are convex (the occlusion
    precondition)."""
    for kind, exp_verts in (("prism", 12), ("pyramid", 5)):
        solid = s3.build_solid(kind)
        assert s3._is_convex(solid)
        assert len(solid.verts) == exp_verts
        hidden = [e for e, v in s3.classify_edges(solid, s3.view_direction()).items() if not v]
        assert hidden                                    # a right prism/pyramid hides its back base


def test_triangular_prism_hides_its_back_vertical_and_base_edges():
    """A triangular prism (n=3): the single back vertical edge + the two back base/top edges are
    hidden. Locks that n is honoured and the classification is per-face-normal, not hard-coded."""
    tri = s3.build_solid("prism", n=3, r=2.0, h=3.0)
    assert len(tri.verts) == 6                            # 3 bottom + 3 top
    cls = s3.classify_edges(tri, s3.view_direction())
    hidden = [e for e, v in cls.items() if not v]
    assert 1 <= len(hidden) <= 4                          # a thin back sliver is hidden, not the front


# --- the occlusion boundary (the design-doc rule, enforced) ------------------
def test_nonconvex_solid_is_refused_for_hidden_line():
    """The design doc bounds many-body / non-convex occlusion AWAY (it is the classical
    hidden-surface problem). classify_edges must RAISE NotConvex rather than draw a wrong dashing —
    a clear error at the boundary, per the brief."""
    import pytest
    # an L-shaped (non-convex) solid: a unit cube with a notch vertex pulled inward
    v = np.array([[0, 0, 0], [2, 0, 0], [2, 2, 0], [1, 2, 0], [1, 1, 0], [0, 1, 0],
                  [0, 0, 1], [2, 0, 1], [2, 2, 1], [1, 2, 1], [1, 1, 1], [0, 1, 1]], float)
    faces = [(0, 1, 2, 3, 4, 5), (6, 7, 8, 9, 10, 11)]   # the concave L cap top & bottom
    notch = s3.Solid(verts=v, faces=faces, kind="L-notch")
    assert not s3._is_convex(notch)
    with pytest.raises(s3.NotConvex):
        s3.classify_edges(notch, s3.view_direction())


def test_face_normals_point_outward():
    """Every school-solid face's computed normal points AWAY from the solid's centroid — the
    winding convention the back-face test relies on."""
    for kind in _ALL_SOLIDS:
        solid = s3.build_solid(kind)
        centroid = solid.verts.mean(axis=0)
        for face in solid.faces:
            n = s3._face_normal(solid, face)
            face_center = solid.verts[list(face)].mean(axis=0)
            assert np.dot(n, face_center - centroid) > -1e-6   # outward (or tangential)


# --- riss_pair correspondence (the defining property) ------------------------
def test_riss_pair_shares_x_across_the_rissachse():
    """Grund- und Aufriss are zugeordnet: a vertex's x-coordinate is IDENTICAL in both Risse (the
    Ordnungslinie), the Grundriss sits below the Rissachse (y<0) and the Aufriss above it (y>0),
    both at the same measurement scale. Build the scene and check the Ordnungslinien connect equal
    x-columns spanning both halves."""
    sc = s3.riss_pair_scene("quader", a=4, b=3, c=2.5)
    ord_lines = [L for L in sc.layers if isinstance(L, Line) and L.role == "grid"]
    assert ord_lines, "no Ordnungslinien drawn"
    for L in ord_lines:
        assert math.isclose(L.p[0], L.q[0])              # vertical (constant x = the projector)
        assert L.p[1] < 0 < L.q[1] or L.q[1] < 0 < L.p[1]  # spans both Risse (crosses the axis)


def test_riss_pair_grundriss_and_aufriss_use_consistent_scale():
    """The Quader's Aufriss width and Grundriss width are the same value a (the shared x-extent),
    proving one measurement scale across the pair. Measured from the drawn edges — each Riss
    independently spans exactly a in x."""
    a, b, c = 5.0, 3.0, 2.0
    sc = s3.riss_pair_scene("quader", a=a, b=b, c=c)
    edges = [L for L in sc.layers if isinstance(L, Line) and L.role in ("ink", "muted")]
    gr = [L for L in edges if L.p[1] < 0 and L.q[1] < 0]      # Grundriss (below the Rissachse)
    au = [L for L in edges if L.p[1] > 0 and L.q[1] > 0]      # Aufriss (above it)

    def xspan(lines):
        xs = [L.p[0] for L in lines] + [L.q[0] for L in lines]
        return max(xs) - min(xs)

    assert gr and au
    assert math.isclose(xspan(gr), a, abs_tol=1e-6)
    assert math.isclose(xspan(au), a, abs_tol=1e-6)


def test_riss_pair_has_a_rissachse_and_captions():
    """The pair is labelled the Austrian way: a Rissachse line + 'Grundriss'/'Aufriss' captions."""
    sc = s3.riss_pair_scene("pyramid")
    texts = {L.text.strip() for L in sc.layers if isinstance(L, Label)}
    assert "Grundriss" in texts and "Aufriss" in texts
    assert any("Rissachse" in t for t in texts)


def test_riss_pair_smooth_body_declutters_ordnungslinien():
    """A cylinder/cone is sampled as a fine polygon; its riss must NOT draw dozens of Ordnungslinien
    (the clutter the brief warns of) — only the two silhouette extents + the centre axis (≤3)."""
    sc = s3.riss_pair_scene("cone")
    ord_lines = [L for L in sc.layers if isinstance(L, Line) and L.role == "grid"]
    assert 1 <= len(ord_lines) <= 3


# --- maskable measures (the task/solution split) -----------------------------
def _labels(scene: Scene) -> list[str]:
    return [L.text for L in scene.layers if isinstance(L, Label)]


def test_measures_are_maskable_for_a_task():
    """show_measures=False turns every dimension into '<key> = ?' (the student task); True shows the
    key. Same computed scene, two projections — the maths-engine masking pattern."""
    shown = s3.axonometric_solid_scene("quader", show_measures=True)
    masked = s3.axonometric_solid_scene("quader", show_measures=False)
    assert {"a", "b", "c"} <= set(_labels(shown))
    assert {"a = ?", "b = ?", "c = ?"} <= set(_labels(masked))
    # a given label overrides both (e.g. "a = 4 cm")
    given = s3.axonometric_solid_scene("quader", labels={"a": "a = 4 cm"})
    assert "a = 4 cm" in _labels(given)


def test_pyramid_and_cylinder_expose_their_measure_keys():
    """Each solid family surfaces its own measures: pyramid/cone → r,h; cylinder/prism → r,h."""
    for kind, keys in (("pyramid", {"r", "h"}), ("cylinder", {"r", "h"}), ("cone", {"r", "h"})):
        masked = _labels(s3.axonometric_solid_scene(kind, show_measures=False))
        assert {f"{k} = ?" for k in keys} <= set(masked)


# --- render smoke: every recipe × every solid through build_asset ------------
def test_axonometric_solid_renders_every_solid(tmp_path):
    for kind in _ALL_SOLIDS:
        a = Asset(id=f"axo_{kind}", role="figure", generator="matplotlib:axonometric_solid",
                  spec={"kind": kind})
        p = build_asset(a, outdir=tmp_path)
        assert p.exists() and p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and p.stat().st_size > 1500


def test_riss_pair_renders_every_solid(tmp_path):
    for kind in _ALL_SOLIDS:
        a = Asset(id=f"riss_{kind}", role="figure", generator="matplotlib:riss_pair",
                  spec={"kind": kind})
        p = build_asset(a, outdir=tmp_path)
        assert p.exists() and p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and p.stat().st_size > 1500


def test_masked_task_variant_renders(tmp_path):
    """The student-task variant (measures masked) renders as a real PNG."""
    a = Asset(id="task", role="figure", generator="matplotlib:axonometric_solid",
              spec={"kind": "cylinder", "show_measures": False})
    p = build_asset(a, outdir=tmp_path)
    assert p.exists() and p.stat().st_size > 1500


def test_both_recipes_in_generation_vocabulary():
    for gen in ("matplotlib:axonometric_solid", "matplotlib:riss_pair"):
        assert gen in GENERATION_RECIPES


# --- degenerate specs rejected ----------------------------------------------
def test_unknown_solid_kind_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        s3.build_solid("dodekaeder")                     # not a school solid we generate
    with pytest.raises(ValueError):
        s3.axonometric_solid_scene("tesseract")


def test_axonometric_recipe_defaults_to_quader(tmp_path):
    """An empty spec is not degenerate — it builds the default Quader (a sensible request)."""
    a = Asset(id="d", role="figure", generator="matplotlib:axonometric_solid", spec={})
    p = build_asset(a, outdir=tmp_path)
    assert p.exists() and p.stat().st_size > 1500


# --- Sichtbarkeit corrections (visibility must be right, not just present) ----
def test_smooth_body_base_rim_back_arc_is_dashed():
    """A Drehzylinder/Drehkegel base circle is only half-visible in Schrägriss: the near (front)
    arc is solid, the far (back) arc is occluded by the lateral surface and must be DASHED (strict
    GZ Sichtbarkeit). Regression: the base rim used to be one solid ellipse."""
    for kind in ("cylinder", "cone"):
        sc = s3.axonometric_solid_scene(kind)
        polylines = [L for L in sc.layers if isinstance(L, Polyline)]
        dashed = [L for L in polylines if L.dash != "solid"]
        solid_arcs = [L for L in polylines if L.dash == "solid"]
        assert len(dashed) == 1, f"{kind}: expected exactly one dashed back-rim arc"
        assert dashed[0].role == "muted" and not dashed[0].closed
        assert solid_arcs, f"{kind}: expected a solid front arc"
        # the front arc sits LOWER on screen (smaller mean y) than the occluded back arc
        front = min(solid_arcs, key=lambda L: sum(p[1] for p in L.points) / len(L.points))
        fy = sum(p[1] for p in front.points) / len(front.points)
        by = sum(p[1] for p in dashed[0].points) / len(dashed[0].points)
        assert fy < by


def test_pyramid_grundriss_slant_edges_are_visible_solid():
    """Seen from directly above, a pyramid's slant edges lie on the visible upper surface — SOLID,
    not dashed. Regression: the old riss code dashed every interior (non-hull) edge."""
    sc = s3.riss_pair_scene("pyramid")
    gr_lines = [L for L in sc.layers if isinstance(L, Line) and L.role in ("ink", "muted")
                and L.p[1] < 0 and L.q[1] < 0]                 # Grundriss sits below the Rissachse
    assert any(L.role == "ink" for L in gr_lines)              # the diagonals are drawn…
    assert [L for L in gr_lines if L.dash != "solid"] == []    # …and none of them dashed


def test_hex_prism_aufriss_interior_verticals_are_visible_solid():
    """In the Aufriss each interior vertical is a coinciding pair (front visible + back hidden at the
    same x); the GZ coincidence rule draws it SOLID. Regression: previously dashed."""
    sc = s3.riss_pair_scene("prism", n=6, r=2.2, h=3.5)
    au_lines = [L for L in sc.layers if isinstance(L, Line) and L.role in ("ink", "muted")
                and L.p[1] > 0 and L.q[1] > 0]                 # Aufriss sits above the Rissachse
    xs = [L.p[0] for L in au_lines] + [L.q[0] for L in au_lines]
    xmin, xmax = min(xs), max(xs)
    interior_v = [L for L in au_lines if abs(L.p[0] - L.q[0]) < 1e-6      # vertical…
                  and xmin + 1e-3 < L.p[0] < xmax - 1e-3]                 # …strictly inside the outline
    assert interior_v, "expected interior vertical edges in the hex-prism Aufriss"
    assert all(L.dash == "solid" and L.role == "ink" for L in interior_v)
