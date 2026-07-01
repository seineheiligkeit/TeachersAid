"""The analysis scene recipes (function plot · integral area · tangent).

Locks the correct-by-construction guarantee: the slope and the area are COMPUTED (sympy) and
match ground truth; the scenes render through build_asset; the value label is maskable (the
task/solution split); and the recipes are in the generation vocabulary. Offline.
"""
from __future__ import annotations

import math

from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.calculus import (_critical_points, _parse, area_between_scene,
                                           definite_integral, distribution_scene, integral_scene,
                                           riemann_sum, tangent_scene, tangent_slope)
from teachersaid.pipeline.scene import Label
from teachersaid.schema.assets import Asset


def test_tangent_slope_is_the_derivative():
    assert tangent_slope("x**2", 2) == 4.0          # f'(x)=2x → 4
    assert tangent_slope("x**3", 1) == 3.0          # f'(x)=3x² → 3
    assert abs(tangent_slope("sin(x)", 0) - 1.0) < 1e-9   # cos(0)=1


def test_definite_integral_matches_ground_truth():
    assert abs(definite_integral("x**2", 0, 1) - 1 / 3) < 1e-6
    assert abs(definite_integral("x", 0, 2) - 2.0) < 1e-9
    assert abs(definite_integral("sin(x)", 0, math.pi) - 2.0) < 1e-6


def test_implicit_multiplication_parses():
    # "2x" must mean 2*x (a common LLM/teacher spelling)
    assert tangent_slope("2x", 0) == 2.0


def _labels(scene) -> list[str]:
    return [L.text for L in scene.layers if isinstance(L, Label)]


def test_value_label_is_maskable_for_a_task():
    shown = integral_scene("x**2", 0, 2, show_value=True)
    masked = integral_scene("x**2", 0, 2, show_value=False)
    assert any(t.startswith("A =") and "?" not in t for t in _labels(shown))
    assert "A = ?" in _labels(masked)
    # the tangent slope label masks too
    assert "k = ?" in _labels(tangent_scene("x**2", 1, show_slope=False))


def test_scenes_render_through_build_asset(tmp_path):
    assets = [
        Asset(id="f", role="figure", generator="matplotlib:function_plot",
              spec={"expr": "0.25*x**2-1", "xmin": -4, "xmax": 4}),
        Asset(id="i", role="figure", generator="matplotlib:integral_area",
              spec={"expr": "0.2*x**2+1", "a": 1, "b": 4}),
        Asset(id="t", role="figure", generator="matplotlib:tangent",
              spec={"expr": "0.2*x**2+1", "x0": 3}),
    ]
    for a in assets:
        p = build_asset(a, outdir=tmp_path)
        assert p.exists() and p.stat().st_size > 0


def test_recipes_in_generation_vocabulary():
    for gen in ("matplotlib:function_plot", "matplotlib:integral_area", "matplotlib:tangent"):
        assert gen in GENERATION_RECIPES


# --- the rest of the wishlist ------------------------------------------------
def test_riemann_sum_values_and_convergence():
    assert riemann_sum("x", 0, 4, 4, "mid") == 8.0        # midpoint of a line = exact (∫₀⁴x = 8)
    assert riemann_sum("x", 0, 4, 4, "left") == 6.0
    assert riemann_sum("x", 0, 4, 4, "right") == 10.0
    assert abs(riemann_sum("x**2", 0, 3, 2000, "mid") - 9.0) < 0.01   # → ∫₀³x² = 9


def test_extrema_are_the_critical_points():
    # f = x³ − 3x → f' = 3x² − 3 = 0 at x = ±1
    assert _critical_points(_parse("x**3 - 3*x"), -5, 5) == [-1.0, 1.0]


def test_area_between_value_is_computed():
    # ∫₀¹ (x − x²) dx = 1/6 ≈ 0,17
    labels = [L.text for L in area_between_scene("x**2", "x", 0, 1).layers if isinstance(L, Label)]
    assert any("0,17" in t for t in labels)


def test_distribution_probability_is_computed():
    def labels(sc):
        return [L.text for L in sc.layers if isinstance(L, Label)]
    assert any("0,5" in t for t in labels(distribution_scene(0, 1, a=0, mode="le")))   # median
    assert any("0,68" in t for t in labels(distribution_scene(0, 1, a=-1, b=1)))       # ±1σ ≈ 0,6827


def test_wishlist_recipes_render_and_are_in_vocab(tmp_path):
    specs = [
        ("matplotlib:riemann_sum", {"expr": "0.2*x**2+1", "a": 1, "b": 4, "n": 6}),
        ("matplotlib:extrema", {"expr": "x**3-3*x", "xmin": -3, "xmax": 3}),
        ("matplotlib:area_between", {"expr": "x**2", "expr2": "x", "a": 0, "b": 1}),
        ("matplotlib:distribution", {"mu": 0, "sigma": 1, "a": 1, "mode": "ge"}),
    ]
    for gen, spec in specs:
        assert gen in GENERATION_RECIPES
        p = build_asset(Asset(id=gen.split(":")[1], role="figure", generator=gen, spec=spec),
                        outdir=tmp_path)
        assert p.exists() and p.stat().st_size > 0
