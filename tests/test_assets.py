"""Phase 4: the parameterized, pluggable code-generator library."""

from __future__ import annotations

import pytest

from teachersaid.pipeline.assets import _GENERATORS, build_asset
from teachersaid.schema.assets import Asset, IntentionallyFlawed


def _asset(gid: str, spec=None) -> Asset:
    return Asset(id="a_" + gid.split(":")[-1], role="figure", generator=gid, spec=spec or {})


@pytest.mark.parametrize("gid, spec", [
    ("matplotlib:number_line", {"min": 0, "max": 20, "step": 2, "marks": [{"at": 7, "label": "hier"}]}),
    ("matplotlib:bar_chart", {"categories": ["A", "B", "C"], "values": [3, 7, 5], "title": "Test", "ylabel": "n"}),
    ("matplotlib:function_graph", {"xmin": -3, "xmax": 3, "m": 2, "b": 1}),
    ("matplotlib:math_formula", {"latex": r"\frac{a}{b} = \sqrt{x^2 + 1}"}),
])
def test_recipe_builds_from_spec(gid, spec, tmp_path):
    p = build_asset(_asset(gid, spec), outdir=tmp_path)
    assert p.exists() and p.stat().st_size > 500  # a real PNG, not empty


def test_bespoke_generators_still_build(tmp_path):
    for gid in ("matplotlib:em_spectrum", "matplotlib:truncated_axis", "matplotlib:honest_axis"):
        assert build_asset(_asset(gid), outdir=tmp_path).exists()


def test_unknown_generator_raises(tmp_path):
    with pytest.raises(ValueError):
        build_asset(_asset("matplotlib:does_not_exist"), outdir=tmp_path)


def test_flawed_guard(tmp_path):
    # marking the CORRECT spectrum generator as flawed is a contradiction -> error
    bad = Asset(id="x", role="figure", generator="matplotlib:em_spectrum",
                intentionally_flawed=IntentionallyFlawed(what="axis truncated"))
    with pytest.raises(ValueError):
        build_asset(bad, outdir=tmp_path)
    # the geschönte-Kurve asset is flawed ON PURPOSE via its own generator -> fine
    ok = Asset(id="y", role="figure", generator="matplotlib:truncated_axis",
               intentionally_flawed=IntentionallyFlawed(what="truncated axis on purpose"))
    assert build_asset(ok, outdir=tmp_path).exists()


def test_registry_holds_the_recipes():
    for gid in ("matplotlib:number_line", "matplotlib:bar_chart",
                "matplotlib:function_graph", "matplotlib:math_formula"):
        assert gid in _GENERATORS
