"""The geometric-optics recipes (rectilinear light: Lochkamera + Schattenraum).

Locks the correct-by-construction guarantees. Lochkamera: the image is inverted BY CONSTRUCTION
(both rays are collinear through the single hole) and the height obeys the similar-triangle law
B = G·b/a. Schattenraum: the two boundary rays are geometrically TANGENT to the sphere
(perpendicular distance from the centre equals r), a point source gives one sharp edge per side,
and the umbra straddles the axis and diverges. Both render through build_asset. Offline.
"""
from __future__ import annotations

import numpy as np

from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.geometric_optics import (PinholeSpec, ShadowSpec, pinhole_construction,
                                                   pinhole_geometry, shadow_construction,
                                                   shadow_geometry)
from teachersaid.pipeline.scene import CircleShape, Line, Region, Scene
from teachersaid.schema.assets import Asset

PNG = b"\x89PNG\r\n\x1a\n"


def _collinear(p, q, r) -> float:
    """Twice the signed area of triangle p-q-r (0 ⇒ collinear)."""
    (x0, y0), (x1, y1), (x2, y2) = p, q, r
    return abs((x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0))


# --- Lochkamera --------------------------------------------------------------
def test_pinhole_image_inverted_and_similar_triangles():
    """B = G·b/a (similar triangles) and the image is inverted (tip below the axis)."""
    for G, a, b in [(3.0, 6.0, 4.0), (2.0, 5.0, 5.0), (4.0, 8.0, 3.0), (1.5, 3.0, 9.0)]:
        geo = pinhole_geometry(PinholeSpec(G=G, a=a, b=b))
        assert abs(geo["B"] - G * b / a) < 1e-12, (G, a, b, geo["B"])
        assert abs(geo["B"] / geo["G"] - b / a) < 1e-12          # B/G == b/a
        assert geo["img_tip"][1] < 0 < geo["obj_tip"][1]         # inverted (tip below axis)


def test_pinhole_both_rays_pass_through_the_hole():
    """The single aperture forces BOTH rays through it: object tip, hole, image tip are collinear
    (and likewise base→hole→image base) — the crossing that makes the image kopfstehend."""
    geo = pinhole_geometry(PinholeSpec(G=3, a=6, b=4))
    hole = geo["hole"]
    assert hole == (0.0, 0.0)
    assert _collinear(geo["obj_tip"], hole, geo["img_tip"]) < 1e-12
    assert _collinear(geo["obj_base"], hole, geo["img_base"]) < 1e-12


def test_pinhole_rejects_nonpositive():
    for bad in (PinholeSpec(G=0, a=6, b=4), PinholeSpec(G=3, a=-6, b=4),
                PinholeSpec(G=3, a=6, b=0)):
        try:
            pinhole_geometry(bad)
            assert False, f"expected ValueError for {bad}"
        except ValueError:
            pass


def test_pinhole_mask_hides_only_the_sought_height():
    from teachersaid.pipeline.scene import Label
    shown = [L.text for L in pinhole_construction(3, 6, 4, show_value=True).layers
             if isinstance(L, Label)]
    masked = [L.text for L in pinhole_construction(3, 6, 4, show_value=False).layers
              if isinstance(L, Label)]
    assert "B" in shown and "B = ?" not in shown
    assert "B = ?" in masked and "B" not in masked
    # the given object height letter stays in both
    assert "G" in shown and "G" in masked


# --- Schattenraum ------------------------------------------------------------
def test_shadow_boundary_rays_are_tangent():
    """Each boundary ray is geometrically TANGENT: the perpendicular distance from the sphere
    centre to the line source→tangent-point equals r, and the radius meets the ray at 90°."""
    for spec in (ShadowSpec(source=(-6.5, 0.0), center=(0.0, 0.0), r=1.5),
                 ShadowSpec(source=(-7.0, 1.0), center=(0.5, -0.3), r=1.2),
                 ShadowSpec(source=(-4.0, 0.0), center=(0.0, 0.0), r=1.8)):
        geo = shadow_geometry(spec)
        S = np.asarray(geo["S"]); C = np.asarray(geo["C"]); r = geo["r"]
        for T in geo["tangents"]:
            T = np.asarray(T)
            # T is on the sphere
            assert abs(np.linalg.norm(T - C) - r) < 1e-9
            # perpendicular distance from C to the line S–T equals r (2D cross → scalar)
            u, v = T - S, C - S
            d = abs(u[0] * v[1] - u[1] * v[0]) / np.linalg.norm(u)
            assert abs(d - r) < 1e-9, (spec, d, r)
            # radius CT ⟂ tangent TS
            assert abs(float(np.dot(T - C, S - T))) < 1e-9


def test_shadow_diverges_and_straddles_axis():
    """On-axis point source: the two tangent points are mirror-symmetric, and the umbra on the
    screen is wider than the sphere (a point source casts a DIVERGING cone) and straddles the axis."""
    sc = shadow_construction(source=(-6.5, 0.0), center=(0.0, 0.0), r=1.5, screen_x=6.5)
    # the shaded Kernschatten region exists and straddles the axis
    regions = [L for L in sc.layers if isinstance(L, Region)]
    assert regions, "no Kernschatten region"
    ys = [p[1] for p in regions[0].points]
    assert min(ys) < 0 < max(ys)                                  # straddles the axis
    assert max(ys) > 1.5                                          # wider than the sphere radius
    assert any(isinstance(L, CircleShape) for L in sc.layers)     # the Kugel is drawn


def test_shadow_requires_external_point_source():
    try:
        shadow_geometry(ShadowSpec(source=(0.5, 0.0), center=(0.0, 0.0), r=1.5))
        assert False, "expected ValueError for a source inside the sphere"
    except ValueError:
        pass


# --- both render + are in the generation vocabulary --------------------------
def test_recipes_in_generation_vocabulary():
    assert "matplotlib:pinhole_camera" in GENERATION_RECIPES
    assert "matplotlib:shadow_cone" in GENERATION_RECIPES


def test_scenes_render_through_build_asset(tmp_path):
    jobs = [
        Asset(id="p", role="figure", generator="matplotlib:pinhole_camera",
              spec={"G": 3, "a": 6, "b": 4}),
        Asset(id="pm", role="figure", generator="matplotlib:pinhole_camera",
              spec={"G": 3, "a": 6, "b": 4, "show_value": False, "title": "Lochkamera"}),
        Asset(id="s", role="figure", generator="matplotlib:shadow_cone", spec={"r": 1.5}),
        Asset(id="sn", role="figure", generator="matplotlib:shadow_cone",
              spec={"r": 1.4, "screen_x": None, "source": [-7, 0], "center": [0, 0]}),
    ]
    for a in jobs:
        p = build_asset(a, outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1500


def test_determinism():
    a = shadow_construction(r=1.5)
    b = shadow_construction(r=1.5)
    assert len(a.layers) == len(b.layers)
    pa = pinhole_construction(3, 6, 4)
    pb = pinhole_construction(3, 6, 4)
    assert len(pa.layers) == len(pb.layers)
