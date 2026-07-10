"""The physics vector scenes — vector addition (Kräfteaddition) + the free-body diagram
(Kräfteplan), the third scene-engine recipe family.

Locks the correct-by-construction guarantee the physics needs: the resultant is COMPUTED from
the component sum (matched against hand-computed ground truth — 3-4-5 and 5-12-13 triples),
never authored; the value label is maskable (the task/solution split); a masked *force*
resultant draws NO arrow (a to-scale arrow would leak the magnitude to a ruler) while a masked
vector-addition resultant keeps its construction arrow (only the number hides); the scenes
render through build_asset; the recipes are in the generation vocabulary; and no labels overlap.
Offline.
"""
from __future__ import annotations

import math

import pytest

from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.figtext import overlap_pairs
from teachersaid.pipeline.physics_scenes import (force_diagram_scene, resultant,
                                                 vector_addition_scene, vector_components)
from teachersaid.pipeline.scene import Arrow, Label, Line, render_scene
from teachersaid.schema.assets import Asset


# --- helpers -----------------------------------------------------------------
def _texts(scene) -> list[str]:
    """Every rendered text — standalone Labels plus the labels carried on Arrows."""
    out: list[str] = []
    for L in scene.layers:
        if isinstance(L, Label):
            out.append(L.text)
        elif isinstance(L, Arrow) and L.label:
            out.append(L.label)
    return out


def _arrows(scene) -> list[Arrow]:
    return [L for L in scene.layers if isinstance(L, Arrow)]


def _focus_arrows(scene) -> list[Arrow]:
    """The resultant arrow(s) — role 'focus' (the forces are 'primary')."""
    return [L for L in _arrows(scene) if L.role == "focus"]


def _overlaps(scene) -> list:
    """Faithful render (same figsize / house style as scene_to_png) → overlapping label pairs."""
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


# --- the computed core -------------------------------------------------------
def test_vector_components_normalises_every_form():
    assert vector_components({"dx": 3, "dy": -4}) == (3.0, -4.0)
    dx, dy = vector_components({"magnitude": 2, "angle_deg": 90})     # straight up
    assert abs(dx) < 1e-9 and abs(dy - 2) < 1e-9
    dx, dy = vector_components({"magnitude": 5, "angle_deg": 0})      # straight right
    assert abs(dx - 5) < 1e-9 and abs(dy) < 1e-9
    assert vector_components((1.5, 2.5)) == (1.5, 2.5)               # a bare (dx, dy) pair


def test_negative_or_zero_magnitude_is_rejected():
    # a negative magnitude is a hidden direction flip — the author must say what they mean
    for bad in (-3, 0):
        with pytest.raises(ValueError):
            vector_components({"magnitude": bad, "angle_deg": 0})


def test_resultant_is_exactly_the_component_sum():
    # hand-computed ground truth — the correctness core of both recipes
    assert resultant([{"dx": 3, "dy": 0}, {"dx": 0, "dy": 4}]) == (3.0, 4.0)
    rx, ry = resultant([{"dx": 1, "dy": 1}, {"dx": 2, "dy": -3}, {"dx": -1, "dy": 0}])
    assert (rx, ry) == (2.0, -2.0)
    # from magnitude/angle: 3 N east + 4 N north → (3, 4), |·| = 5
    rx, ry = resultant([{"magnitude": 3, "angle_deg": 0}, {"magnitude": 4, "angle_deg": 90}])
    assert abs(rx - 3) < 1e-9 and abs(ry - 4) < 1e-9
    assert abs(math.hypot(rx, ry) - 5) < 1e-9


# --- vector addition ---------------------------------------------------------
def test_vector_addition_resultant_label_is_the_computed_magnitude():
    # 3-4-5: the drawn resultant reports |F_R| = 5 N (the number is computed, not authored)
    sc = vector_addition_scene([{"magnitude": 3, "angle_deg": 0},
                                {"magnitude": 4, "angle_deg": 90}])
    assert any("= 5 N" in t for t in _texts(sc))


def test_vector_addition_masks_the_number_but_keeps_the_construction():
    vecs = [{"magnitude": 3, "angle_deg": 0}, {"magnitude": 4, "angle_deg": 90}]
    shown = vector_addition_scene(vecs, show_value=True)
    masked = vector_addition_scene(vecs, show_value=False)
    assert any("= 5 N" in t for t in _texts(shown)) and not any("?" in t for t in _texts(shown))
    assert any("= ?" in t for t in _texts(masked))
    # the resultant ARROW stays in both — the tip-to-tail construction IS the method; only the
    # numeric answer hides (unlike a free-body resultant, which is the answer itself)
    assert _focus_arrows(shown) and _focus_arrows(masked)


def test_show_resultant_false_draws_only_the_given_vectors():
    sc = vector_addition_scene([{"magnitude": 3, "angle_deg": 0},
                                {"magnitude": 4, "angle_deg": 90}], show_resultant=False)
    assert _focus_arrows(sc) == []                        # no resultant drawn
    assert len(_arrows(sc)) == 2                           # just the two inputs


def test_parallelogram_needs_exactly_two_vectors():
    with pytest.raises(ValueError):
        vector_addition_scene([{"dx": 1, "dy": 0}, {"dx": 0, "dy": 1}, {"dx": 1, "dy": 1}],
                              method="parallelogram")


def test_parallelogram_completes_with_two_helper_lines():
    sc = vector_addition_scene([{"magnitude": 5, "angle_deg": 20},
                                {"magnitude": 4, "angle_deg": 80}], method="parallelogram")
    # the two muted dashes closing the parallelogram (each input tip → the diagonal end)
    assert sum(isinstance(L, Line) for L in sc.layers) == 2
    assert len(_focus_arrows(sc)) == 1                    # the diagonal resultant


def test_empty_vector_list_is_rejected():
    with pytest.raises(ValueError):
        vector_addition_scene([])


# --- free-body diagram -------------------------------------------------------
def test_force_diagram_resultant_is_computed():
    # 5-12-13: |(12, -5)| = 13
    sc = force_diagram_scene([{"magnitude": 12, "angle_deg": 0},
                              {"magnitude": 5, "angle_deg": 270}], show_resultant=True)
    assert any("= 13 N" in t for t in _texts(sc))


def test_force_diagram_equilibrium_renders_zero_and_no_arrow():
    # equal + opposite → F_res = 0 N, drawn honestly as a label with NO arrow
    eq = force_diagram_scene([{"magnitude": 15, "angle_deg": 90},
                              {"magnitude": 15, "angle_deg": 270}], show_resultant=True)
    assert any("= 0 N" in t for t in _texts(eq))
    assert _focus_arrows(eq) == []


def test_masked_force_resultant_draws_no_arrow():
    # the load-bearing anti-leak: arrows are true to scale, so a masked resultant arrow would
    # betray its magnitude to a ruler — masking must drop the arrow, keeping only "F_res = ?"
    forces = [{"magnitude": 12, "angle_deg": 0}, {"magnitude": 5, "angle_deg": 270}]
    shown = force_diagram_scene(forces, show_resultant=True, show_value=True)
    masked = force_diagram_scene(forces, show_resultant=True, show_value=False)
    assert len(_focus_arrows(shown)) == 1                 # the computed resultant is drawn
    assert _focus_arrows(masked) == []                    # masked → NO arrow
    assert any("= ?" in t for t in _texts(masked))
    assert not any("?" in t for t in _texts(shown))


def test_force_arrows_are_true_to_scale():
    # a force twice as large is drawn twice as long (the honesty rule for diagrams)
    sc = force_diagram_scene([{"magnitude": 10, "angle_deg": 0},
                              {"magnitude": 5, "angle_deg": 90}])
    forces = [L for L in _arrows(sc) if L.role == "primary"]
    lengths = {round(math.hypot(L.q[0] - L.p[0], L.q[1] - L.p[1]), 6) for L in forces}
    assert len(forces) == 2 and len(lengths) == 2         # different magnitudes → different lengths
    assert max(lengths) == pytest.approx(2 * min(lengths))  # 10 N is exactly twice as long as 5 N


def test_empty_force_list_is_rejected():
    with pytest.raises(ValueError):
        force_diagram_scene([])


# --- integration: build_asset, vocabulary, layout ----------------------------
def test_scenes_render_through_build_asset(tmp_path):
    assets = [
        Asset(id="va", role="figure", generator="matplotlib:vector_addition",
              spec={"vectors": [{"magnitude": 3, "angle_deg": 0},
                                {"magnitude": 4, "angle_deg": 90}]}),
        Asset(id="vp", role="figure", generator="matplotlib:vector_addition",
              spec={"vectors": [{"magnitude": 5, "angle_deg": 20},
                                {"magnitude": 4, "angle_deg": 80}], "method": "parallelogram"}),
        Asset(id="fd", role="figure", generator="matplotlib:force_diagram",
              spec={"forces": [{"magnitude": 12, "angle_deg": 0},
                               {"magnitude": 5, "angle_deg": 270}], "show_resultant": True}),
    ]
    for a in assets:
        p = build_asset(a, outdir=tmp_path)
        assert p.exists() and p.stat().st_size > 0


def test_recipes_in_generation_vocabulary():
    for gen in ("matplotlib:vector_addition", "matplotlib:force_diagram"):
        assert gen in GENERATION_RECIPES


def test_no_label_overlaps():
    scenes = [
        vector_addition_scene([{"magnitude": 3, "angle_deg": 0, "label": "F_1"},
                               {"magnitude": 4, "angle_deg": 90, "label": "F_2"}]),
        vector_addition_scene([{"magnitude": 5, "angle_deg": 20},
                               {"magnitude": 4, "angle_deg": 80}], method="parallelogram"),
        vector_addition_scene([{"magnitude": 2, "angle_deg": 30}, {"magnitude": 3, "angle_deg": 100},
                               {"magnitude": 2.5, "angle_deg": 200}]),
        force_diagram_scene([{"magnitude": 12, "angle_deg": 0, "label": "F_Zug"},
                             {"magnitude": 5, "angle_deg": 270, "label": "F_G"}],
                            show_resultant=True),
        force_diagram_scene([{"magnitude": 15, "angle_deg": 90, "label": "F_N"},
                             {"magnitude": 15, "angle_deg": 270, "label": "F_G"}],
                            body_label="m", show_resultant=True),
    ]
    for sc in scenes:
        assert _overlaps(sc) == []
