"""Chart legibility + representation sanity (review pass).

Correct numbers aren't enough: the recipe must render legibly (long labels, wide
ranges) and the linter must flag representations that mislead (0/1 'classification'
bars; orders-of-magnitude ranges on a linear scale)."""

from __future__ import annotations

from types import SimpleNamespace

from teachersaid.pipeline.assets import build_asset
from teachersaid.pipeline.chart_lint import lint_content
from teachersaid.schema.assets import Asset

PNG = b"\x89PNG\r\n\x1a\n"


def _bar(aid, vals, **spec):
    return Asset(id=aid, role="figure", generator="matplotlib:bar_chart",
                 spec={"categories": [f"c{i}" for i in range(len(vals))], "values": vals, **spec})


def _content(*assets):
    return SimpleNamespace(assets=list(assets))


def test_lint_flags_binary_classification_bars():
    _, w = lint_content(_content(_bar("b", [1, 1, 0, 1, 0])))
    assert any("Klassifikation" in x for x in w)


def test_lint_flags_wide_range_unless_log():
    _, w = lint_content(_content(_bar("r", [0.017, 40, 5000])))      # ~294000x
    assert any(("unsichtbar" in x or "log" in x) for x in w)
    _, w2 = lint_content(_content(_bar("rl", [0.017, 40, 5000], log=True)))
    assert not w2                                                    # log → honest
    _, w3 = lint_content(_content(_bar("ok", [10, 12, 9, 11])))
    assert not w3                                                    # tight range → fine


def test_chooser_maps_intent_to_representation():
    from teachersaid.schema.chart_choose import choose_representation
    assert choose_representation("trend", {"categories": ["2010", "2020"], "values": [1, 2]})[0] == "matplotlib:line"
    assert choose_representation("relationship", {"points": [[1, 2], [3, 4]]})[0] == "matplotlib:scatter"
    assert choose_representation("distribution", {"values": [1, 2, 3, 4]})[0] == "matplotlib:histogram"
    assert choose_representation("scale", {"categories": ["Wasser"], "values": [7]})[0] == "matplotlib:number_line"
    assert choose_representation("comparison", {"categories": ["a", "b"], "values": [1, 2]})[0] == "matplotlib:bar_chart"


def test_data_figure_compiles_and_flows_through_to_canonical():
    from teachersaid.grounding import lehrplan_store as ls
    from teachersaid.schema.generation_views import (
        GenDataFigure,
        GenWorksheetBody,
        body_to_canonical,
        data_figure_to_asset,
    )
    from teachersaid.schema.worksheet import WorksheetMeta
    a = data_figure_to_asset(GenDataFigure(id="f", intent="relationship",
                                           points=[[1, 2], [3, 4]], fit=True))
    assert a.generator == "matplotlib:scatter" and a.spec["points"] == [[1, 2], [3, 4]]
    meta = WorksheetMeta(title="t", subject="Physik", stufe="Unterstufe", klasse=4,
                         fassung=ls.get_fassung(), lehrplan_label="x")
    body = GenWorksheetBody(data_figures=[GenDataFigure(id="df", intent="trend",
                                                        categories=["2000", "2010"], values=[1, 2])])
    content = body_to_canonical(body, meta=meta, subject_model=ls.get_subject_model("Physik"))
    assert any(a.id == "df" and a.generator == "matplotlib:line" for a in content.assets)


def test_new_recipes_render(tmp_path):
    for gen, spec in {
        "matplotlib:line": {"categories": ["a", "b", "c"], "values": [1, 2, 3], "title": "L"},
        "matplotlib:scatter": {"points": [[1, 2], [2, 3], [3, 5]], "fit": True},
        "matplotlib:histogram": {"values": [1, 2, 2, 3, 3, 3, 4], "title": "H"},
    }.items():
        p = build_asset(Asset(id="x", role="figure", generator=gen, spec=spec), outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 800


def test_lint_flags_wrong_chart_type():
    num = Asset(id="n", role="figure", generator="matplotlib:bar_chart",
                spec={"categories": ["100", "200", "300", "400"], "values": [4.5, 3.8, 3.2, 2.9]})
    _, w = lint_content(_content(num))
    assert any("Zusammenhang" in x or "Streu" in x for x in w)
    yrs = Asset(id="t", role="figure", generator="matplotlib:bar_chart",
                spec={"categories": ["1990", "2010", "2024"], "values": [29, 36, 43]})
    _, w2 = lint_content(_content(yrs))
    assert any("Zeitreihe" in x for x in w2)


def test_bar_chart_renders_long_labels_and_log(tmp_path):
    long = Asset(id="long", role="figure", generator="matplotlib:bar_chart",
                 spec={"categories": ["Ein sehr langer Kategoriename", "kurz",
                                      "noch ein längerer Name hier"],
                       "values": [1, 2, 3], "ylabel": "x"})        # auto-horizontal
    logc = _bar("logc", [0.1, 100, 9000], log=True, ylabel="Ω")
    for a in (long, logc):
        p = build_asset(a, outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 800
