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


def test_bar_chart_renders_long_labels_and_log(tmp_path):
    long = Asset(id="long", role="figure", generator="matplotlib:bar_chart",
                 spec={"categories": ["Ein sehr langer Kategoriename", "kurz",
                                      "noch ein längerer Name hier"],
                       "values": [1, 2, 3], "ylabel": "x"})        # auto-horizontal
    logc = _bar("logc", [0.1, 100, 9000], log=True, ylabel="Ω")
    for a in (long, logc):
        p = build_asset(a, outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 800
