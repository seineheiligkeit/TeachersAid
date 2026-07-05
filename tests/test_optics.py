"""The optics ray-construction recipe (Bildkonstruktion an dünnen Linsen).

Locks the correct-by-construction guarantee: the image position obtained from the RAY GEOMETRY
(the intersection of the principal rays, derived here independently) equals the thin-lens formula
result the recipe computes — two independent derivations agree (THE defining property). The
regimes (reell/virtuell/Grenzfall, Zerstreuungslinse) classify correctly; the magnification is
right; stages accumulate layers; the value label is maskable; the scenes render. Offline.
"""
from __future__ import annotations

import numpy as np

from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.optics import (OpticsSpec, image_geometry, lens_construction, ray_scene)
from teachersaid.pipeline.scene import Label, Scene
from teachersaid.schema.assets import Asset


def _ray_intersection_b(f_signed: float, g: float, G: float) -> float:
    """The image abscissa b from the GEOMETRY of two principal rays — derived independently of
    image_geometry's formula, to cross-check it.

    Parallelstrahl (out through F′=(f,0), entering at height G): y = G − (G/f)·x
    Mittelpunktstrahl (straight through the centre from P=(−g,G)): y = −(G/g)·x
    Their intersection abscissa is the Bildweite b."""
    # −(G/g)x = G − (G/f)x  →  x·(1/f − 1/g) = 1  →  x = 1/(1/f − 1/g)
    m_center = -G / g
    m_parallel = -G / f_signed
    # G − (G/f)x = m_center·x  →  G = (m_center + G/f)x
    x = G / (m_center + G / f_signed)
    return float(x)


def test_image_position_from_rays_equals_thin_lens_formula():
    """The defining property: the ray-intersection image position == the Abbildungsgleichung
    result, across the regimes."""
    for kind, f, g, G in [("sammellinse", 3.0, 6.0, 2.0),      # reell, 1:1 (g = 2f)
                          ("sammellinse", 3.0, 9.0, 2.0),      # reell, verkleinert
                          ("sammellinse", 3.5, 2.0, 2.0),      # virtuell (Lupe, g < f)
                          ("zerstreuungslinse", 3.0, 6.0, 2.0)]:
        geo = image_geometry(OpticsSpec(kind=kind, f=f, g=g, G=G))
        b_ray = _ray_intersection_b(geo["f"], g, G)            # geo["f"] is the SIGNED focal length
        assert abs(b_ray - geo["b"]) < 1e-9, (kind, f, g, geo["b"], b_ray)
        # and the image height follows the same ray geometry: B = −(G/g)·b
        assert abs(geo["B"] - (-(G / g) * geo["b"])) < 1e-9


def test_regimes_classified_correctly():
    real = image_geometry(OpticsSpec("sammellinse", f=3, g=6, G=2))
    assert real["real"] and not real["upright"] and real["regime"] == "reell"
    lupe = image_geometry(OpticsSpec("sammellinse", f=3.5, g=2, G=2))
    assert (not lupe["real"]) and lupe["upright"] and lupe["enlarged"] and lupe["regime"] == "virtuell"
    zerst = image_geometry(OpticsSpec("zerstreuungslinse", f=3, g=6, G=2))
    assert (not zerst["real"]) and zerst["upright"] and (not zerst["enlarged"])
    grenz = image_geometry(OpticsSpec("sammellinse", f=3, g=3, G=2))
    assert grenz["b"] is None and grenz["regime"] == "grenzfall"


def test_magnification_and_sign_convention():
    # g = 2f ⇒ V = −1 (real, inverted, same size); the Zerstreuungslinse carries a negative f
    assert abs(image_geometry(OpticsSpec("sammellinse", f=3, g=6, G=2))["V"] + 1.0) < 1e-9
    zerst = image_geometry(OpticsSpec("zerstreuungslinse", f=3, g=6, G=2))
    assert zerst["f"] < 0 and 0 < zerst["V"] < 1                    # verkleinert, aufrecht


def test_lens_type_flips_the_focal_sign():
    assert image_geometry(OpticsSpec("sammellinse", f=3, g=6, G=2))["f"] == 3.0
    assert image_geometry(OpticsSpec("zerstreuungslinse", f=3, g=6, G=2))["f"] == -3.0


def _n_layers(kind, f, g, G, stage):
    return len(ray_scene(OpticsSpec(kind, f=f, g=g, G=G), stage=stage).layers)


def test_stages_monotonically_accumulate_layers():
    """Each stage adds construction (never removes) — the step-by-step ladder."""
    counts = [_n_layers("sammellinse", 3, 6, 2, s) for s in range(1, 7)]
    assert all(counts[i] <= counts[i + 1] for i in range(len(counts) - 1)), counts
    assert counts[-1] > counts[0]                                   # stage 6 richer than stage 1


def _labels(scene: Scene) -> list[str]:
    return [L.text for L in scene.layers if isinstance(L, Label)]


def test_image_and_measures_are_maskable():
    shown = lens_construction("sammellinse", f=3, g=9, G=2, stage=6, show_value=True)
    masked = lens_construction("sammellinse", f=3, g=9, G=2, stage=6, show_value=False)
    assert any(t.startswith("B′") and "?" not in t for t in _labels(shown))
    assert "B′ = ?" in _labels(masked)
    assert "b = ?" in _labels(masked) and "g = ?" in _labels(masked)
    assert any(t.startswith("b =") and "?" not in t for t in _labels(shown))


def test_scene_renders_through_build_asset(tmp_path):
    PNG = b"\x89PNG\r\n\x1a\n"
    for kind, f, g, G in [("sammellinse", 3, 6, 2), ("sammellinse", 3.5, 2, 2),
                          ("sammellinse", 3, 3, 2), ("zerstreuungslinse", 3, 6, 2)]:
        for stage in (1, 3, 6):
            a = Asset(id=f"o{kind}{stage}", role="figure", generator="matplotlib:optics_ray",
                      spec={"kind": kind, "f": f, "g": g, "G": G, "stage": stage})
            p = build_asset(a, outdir=tmp_path)
            assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1500


def test_recipe_in_generation_vocabulary():
    assert "matplotlib:optics_ray" in GENERATION_RECIPES


def test_degenerate_specs_rejected():
    for bad in (OpticsSpec("spiegel", f=3, g=6, G=2),          # unimplemented kind (mirror)
                OpticsSpec("sammellinse", f=0, g=6, G=2),      # non-positive f
                OpticsSpec("sammellinse", f=3, g=-6, G=2),     # non-positive g
                OpticsSpec("sammellinse", f=3, g=6, G=0)):     # non-positive G
        try:
            image_geometry(bad)
            assert False, f"expected ValueError for {bad}"
        except ValueError:
            pass


def test_determinism():
    a = lens_construction("sammellinse", f=3, g=7, G=2, stage=6)
    b = lens_construction("sammellinse", f=3, g=7, G=2, stage=6)
    assert _labels(a) == _labels(b) and len(a.layers) == len(b.layers)
