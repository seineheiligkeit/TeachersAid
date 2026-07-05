"""Locks for the figure-engine port onto `figstyle` (roadmap A1).

The port moved the ~25 legacy matplotlib recipes off scattered hex literals and onto the
semantic ROLES in `pipeline/figstyle.py` (drawn through scoped `house_rc()`), and moved the
polygon-shaped geometry recipes onto scene composition. These tests keep the debt from creeping
back: no hard-coded `#RRGGBB` in `assets.py`, the semantic roles the recipes rely on exist, the
house font actually renders small text, and the intentionally-flawed twin stays flawed.
"""

from __future__ import annotations

import re
from pathlib import Path

import teachersaid.pipeline.assets as assets
import teachersaid.pipeline.figstyle as fs

_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")


def test_no_hardcoded_hex_in_assets():
    """The load-bearing lock: NO 6-digit hex colour literal survives in assets.py. Every colour
    must come from a semantic role in figstyle (PALETTE / c() / cat() / edge() / SVG). Where an
    SVG string default needs a literal, it lives in `figstyle.SVG`, not here."""
    src = Path(assets.__file__).read_text(encoding="utf-8")
    offenders = sorted(set(_HEX.findall(src)))
    assert offenders == [], (
        f"hard-coded hex colours left in assets.py: {offenders} — route them through "
        "figstyle semantic roles (PALETTE/c()/cat()/edge()/SVG)")


def test_no_hardcoded_hex_in_scene_recipes():
    """The scene-engine recipe modules (constructions/calculus/optics/circuits) must also carry
    NO hex literals: they draw exclusively through the scene primitives' semantic ROLES + the
    figstyle ramps (families → line_kind, focus/ink/muted). Keeps the A2 physics families on the
    same discipline the A1 port established."""
    import teachersaid.pipeline.circuits as circuits
    import teachersaid.pipeline.optics as optics
    for mod in (optics, circuits):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        offenders = sorted(set(_HEX.findall(src)))
        assert offenders == [], (
            f"hard-coded hex colours left in {Path(mod.__file__).name}: {offenders} — use the "
            "scene primitives' roles/families, never a literal colour")


def test_figstyle_exposes_the_roles_the_port_relies_on():
    for role in ("ink", "muted", "grid", "primary", "secondary", "focus", "positive",
                 "negative", "surface", "surface_warm", "no_data", "paper"):
        assert isinstance(getattr(fs.PALETTE, role), str) and fs.c(role).startswith("#")
    # the helpers the recipes call
    assert fs.cat(0) == fs.PALETTE.primary            # slot 0 == primary (single/first-of-many agree)
    assert fs.edge("primary").startswith("#") and fs.edge("primary") != fs.PALETTE.primary
    # the SVG (decorative) defaults are the house colours, expressed as strings
    for k in ("ink", "primary", "accent", "paper"):
        assert getattr(fs.SVG, k).startswith("#")


def test_house_font_renders_small_text():
    """The house font must actually rasterise a small label — the guard that rejected the
    buggy Windows Calibri build (which drops most glyphs at ~9 pt under Agg) and fell through to
    a font that works. Without this, the small-label recipes (number line, timeline) silently
    blanked. `FONT_FAMILY` is whatever survived the probe."""
    assert fs._renders_small(fs.FONT_FAMILY)
    # DejaVu Sans is the guaranteed-present, always-rendering floor.
    assert fs._renders_small("DejaVu Sans")


def _capture(monkeypatch, tmp_path, generator, spec):
    captured: dict = {}
    monkeypatch.setattr(assets.plt, "close", lambda f=None: captured.setdefault("fig", f))
    from teachersaid.schema.assets import Asset
    assets.build_asset(Asset(id="t", role="figure", generator=generator, spec=spec),
                       outdir=tmp_path)
    fig = captured["fig"]
    fig.canvas.draw()
    return fig


def test_small_label_recipes_render_their_labels(tmp_path, monkeypatch):
    """number_line + timeline actually draw their (small) labels — a regression guard for the
    font-glyph-drop bug. Assert the label strings are present as text artists AND that they ink
    enough columns to prove the glyphs really rasterised (a dropped-glyph render is near-blank)."""
    import numpy as np

    def _rendered_texts(fig) -> list[str]:
        return [t.get_text() for ax in fig.axes for t in ax.texts if t.get_text().strip()]

    nl = _capture(monkeypatch, tmp_path, "matplotlib:number_line",
                  {"min": 0, "max": 14, "step": 2,
                   "marks": [{"at": 2, "label": "Zitronensaft"}, {"at": 11.5, "label": "Ammoniak"}]})
    try:
        assert "Zitronensaft" in _rendered_texts(nl) and "Ammoniak" in _rendered_texts(nl)
        buf = np.frombuffer(nl.canvas.buffer_rgba(), dtype=np.uint8).reshape(
            nl.canvas.get_width_height()[::-1] + (4,))
        cols_inked = int((buf[..., :3].sum(axis=2) < 400).any(axis=0).sum())
        assert cols_inked > 120        # dropped-glyph render would ink only a handful of columns
    finally:
        import matplotlib.pyplot as plt
        plt.close(nl)

    tl = _capture(monkeypatch, tmp_path, "matplotlib:timeline",
                  {"events": [{"at": 1918, "label": "Republik"}, {"at": 1955, "label": "Staatsvertrag"}]})
    try:
        joined = " ".join(_rendered_texts(tl))
        assert "Republik" in joined and "Staatsvertrag" in joined
    finally:
        import matplotlib.pyplot as plt
        plt.close(tl)


def test_geometry_recipes_are_scene_composed(tmp_path):
    """The polygon-shaped geometry recipes became computed Scenes rendered by `render_scene`;
    confirm they still build a valid PNG and, for right_triangle, that the unknown is masked
    (spec-provided 'c = ?', never the answer)."""
    from teachersaid.schema.assets import Asset
    PNG = b"\x89PNG\r\n\x1a\n"
    for gen, spec in {
        "matplotlib:right_triangle": {"a": 4, "b": 3, "label_c": "c = ?"},
        "matplotlib:rectangle": {"length": 6, "width": 4, "label_l": "6 cm"},
        "matplotlib:polygon": {"points": [[0, 0], [5, 0], [2, 3]], "vertex_labels": ["A", "B", "C"],
                               "side_labels": ["c", "a", "b"]},
    }.items():
        p = assets.build_asset(Asset(id="g", role="figure", generator=gen, spec=spec), outdir=tmp_path)
        assert p.read_bytes()[:8] == PNG and p.stat().st_size > 1500


def test_misleading_twin_keeps_its_flaw(tmp_path, monkeypatch):
    """The intentionally-flawed truncated_axis must STILL truncate its y-axis (never 'fixed'):
    the misleading twin is drawn in the `negative` role, the honest twin in `positive`, and the
    truncated one's y-axis does NOT start at 0 — the flaw IS the teaching point."""
    data = {"categories": ["Jän", "Feb", "Mär"], "values": [102, 108, 115], "ylabel": "Stück"}
    trunc = _capture(monkeypatch, tmp_path, "matplotlib:truncated_axis", data)
    try:
        assert trunc.axes[0].get_ylim()[0] > 50       # zoomed axis preserved (not zero-based)
    finally:
        import matplotlib.pyplot as plt
        plt.close(trunc)
    honest = _capture(monkeypatch, tmp_path, "matplotlib:honest_axis", data)
    try:
        assert honest.axes[0].get_ylim()[0] == 0       # the honest twin is zero-based
    finally:
        import matplotlib.pyplot as plt
        plt.close(honest)
