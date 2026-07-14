"""The Homologie-Schema recipe (curated vertebrate limb comparison).

Locks the invariant that carries the didactic message: EVERY animal shows exactly two
forelimbs and two hindlimbs ("genau zwei Gliedmaßenpaare"), the forelimb pair is drawn in
ONE consistent role and the hindlimb pair in ANOTHER — the SAME two colours on every animal,
which is what makes "gleicher Bauplan, verschiedene Werkzeuge" (homologe Gliedmaßen →
gemeinsame Abstammung) read at a glance. Plus: unpaired parts never borrow a pair colour
(so the count stays honest), the scene renders through build_asset (a RENDER test — assemble/
verify don't render), and the recipe is in the generation vocabulary. Offline.
"""
from __future__ import annotations

from teachersaid.pipeline import figstyle as fs
from teachersaid.pipeline.assets import GENERATION_RECIPES, build_asset
from teachersaid.pipeline.homology import (ANIMALS, FORE_ROLE, HIND_ROLE,
                                           homology_scene)
from teachersaid.pipeline.scene import Region, render_scene
from teachersaid.schema.assets import Asset


def _limb_fills(scene, group: str) -> list[Region]:
    return [L for L in scene.layers if isinstance(L, Region) and L.group == group]


# --- the "genau zwei Paare" invariant -----------------------------------------
def test_each_animal_declares_exactly_two_fore_and_two_hind_limbs():
    assert ANIMALS, "the curated animal set must not be empty"
    for a in ANIMALS:
        assert len(a["fore"]) == 2, f"{a['name']} must have exactly 2 forelimbs"
        assert len(a["hind"]) == 2, f"{a['name']} must have exactly 2 hindlimbs"
        # a limb is a non-empty list of polygons (a bent leg = thigh + shin)
        for limb in a["fore"] + a["hind"]:
            assert limb and all(len(poly) >= 3 for poly in limb)


def test_every_animal_names_its_two_limb_forms():
    # the label under each animal is its name + the FORM each pair takes (Flossen/Beine/Flügel)
    for a in ANIMALS:
        assert a["name"] and a["fore_form"] and a["hind_form"]


# --- colour consistency: fore == focus, hind == primary, on EVERY animal -------
def test_pair_colours_are_consistent_across_all_animals():
    sc = homology_scene()
    fore = _limb_fills(sc, "forelimb")
    hind = _limb_fills(sc, "hindlimb")
    # every forelimb piece is the SAME role, every hindlimb piece the SAME (other) role —
    # that constancy across all four animals IS the homology message
    assert fore and {L.role for L in fore} == {FORE_ROLE}
    assert hind and {L.role for L in hind} == {HIND_ROLE}
    assert FORE_ROLE != HIND_ROLE


def test_limb_fill_counts_match_the_curated_spec():
    # no unpaired part (fish Rücken-/Schwanzflosse, eyes, bodies) is drawn in a pair colour:
    # the count of pair-coloured fills equals exactly the curated limb polygons, nothing more.
    sc = homology_scene()
    exp_fore = sum(len(poly_list) for a in ANIMALS for poly_list in a["fore"])
    exp_hind = sum(len(poly_list) for a in ANIMALS for poly_list in a["hind"])
    assert len(_limb_fills(sc, "forelimb")) == exp_fore
    assert len(_limb_fills(sc, "hindlimb")) == exp_hind


def test_unpaired_parts_never_use_a_pair_colour():
    # the neutral (non-limb, non-legend) fills — bodies, fish fins — must avoid focus/primary
    sc = homology_scene()
    for L in sc.layers:
        if isinstance(L, Region) and L.group not in ("forelimb", "hindlimb", "legend"):
            assert L.role not in (FORE_ROLE, HIND_ROLE)


# --- rendering + vocabulary ---------------------------------------------------
def test_scene_renders_without_error():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sc = homology_scene()
    with plt.rc_context(fs.house_rc()):
        fig, ax = plt.subplots(figsize=sc.canvas.figsize, layout="constrained")
        render_scene(sc, ax)
        fig.canvas.draw()
        plt.close(fig)


def test_animal_subset_spec_renders():
    sc = homology_scene({"animals": [ANIMALS[0]], "title": "nur der Fisch"})
    assert len(_limb_fills(sc, "forelimb")) == sum(len(p) for p in ANIMALS[0]["fore"])
    assert sc.canvas.title == "nur der Fisch"


def test_renders_through_build_asset(tmp_path):
    a = Asset(id="hom", role="content", generator="matplotlib:homology_schema",
              spec={}, illustrative=True)
    p = build_asset(a, outdir=tmp_path)
    assert p.exists() and p.stat().st_size > 0


def test_recipe_in_generation_vocabulary():
    assert "matplotlib:homology_schema" in GENERATION_RECIPES
