"""Layout legibility lint — figures don't overlap their labels; tables don't overflow their frame.

The legibility analogue of `figure_lint`/`chart_lint`: *measure, don't assume*. Turns the
"overlapping labels / text past the table border" class (SME feedback, 30 Jun 2026) into a
detected, regression-proof invariant. Covers the worst cases reported: a clustered timeline, the
Wien-in-Niederösterreich choropleth enclave, and over-long table cells.
"""

from __future__ import annotations

from teachersaid.pipeline.figtext import overlap_pairs


def _label_overlaps(monkeypatch, tmp_path, generator: str, spec: dict):
    """Build a figure recipe and return the overlapping label pairs (the legibility invariant).
    Captures the figure before the recipe closes it (monkeypatching plt.close)."""
    import teachersaid.pipeline.assets as A
    from teachersaid.schema.assets import Asset

    captured: dict = {}
    monkeypatch.setattr(A.plt, "close", lambda f=None: captured.setdefault("fig", f))
    A.build_asset(Asset(id="t", role="figure", generator=generator, spec=spec), outdir=tmp_path)
    fig = captured["fig"]
    try:
        return overlap_pairs(fig)
    finally:
        import matplotlib.pyplot as plt
        plt.close(fig)


def test_timeline_no_overlap_when_dates_cluster(tmp_path, monkeypatch):
    # five long-labelled events inside five years — the worst case from the SME feedback
    spec = {"events": [{"at": y, "label": f"Ein Ereignis mit deutlich längerem Namen {y}"}
                       for y in (1813, 1814, 1815, 1816, 1817)],
            "title": "Geballte Zeitleiste"}
    assert _label_overlaps(monkeypatch, tmp_path, "matplotlib:timeline", spec) == []


def test_timeline_no_overlap_with_tall_label_towers(tmp_path, monkeypatch):
    # the c0213 regression (SME revise, 18 Jul 2026): sentence-length labels wrap to 4–6
    # lines AND five of seven events cluster at the end of a 425-year span, forcing many
    # lanes. The old fixed lane constant collapsed here (text is sized in points, so the
    # widened y-range shrank the lanes but not the text) — labels printed over each other.
    spec = {"events": [
        {"at": 1494, "label": "Vertrag von Tordesillas: Aufteilung der überseeischen Welt "
                              "zwischen Spanien und Portugal"},
        {"at": 1602, "label": "Gründung der Niederländischen Ostindien-Kompanie (VOC)"},
        {"at": 1834, "label": "Abschaffung der Sklaverei im Britischen Empire"},
        {"at": 1857, "label": "Aufstand gegen die britische Herrschaft in Indien"},
        {"at": 1884, "label": "Berliner Konferenz: Regeln für die Aufteilung Afrikas (bis 1885)"},
        {"at": 1904, "label": "Kolonialkrieg gegen Herero und Nama in Deutsch-Südwestafrika "
                              "(bis 1908)"},
        {"at": 1919, "label": "Neuverteilung der Kolonien als Völkerbundmandate nach dem "
                              "Ersten Weltkrieg"},
    ], "title": "Kolonialismus und Imperialismus – Stationen 1494–1919"}
    assert _label_overlaps(monkeypatch, tmp_path, "matplotlib:timeline", spec) == []


def test_choropleth_no_overlap_with_enclave(tmp_path, monkeypatch):
    from teachersaid.grounding import data_store as ds
    dset = ds.get_dataset("statistik_austria_bundeslaender_2024")
    series = dset.series["bevoelkerung"]
    spec = {"geo_id": "at_bundeslaender",
            "values": dict(zip(series["groups"], series["counts"])),
            "value_label": "Einwohner:innen", "title": "Bundesländer"}
    assert _label_overlaps(monkeypatch, tmp_path, "matplotlib:choropleth_map", spec) == []


def test_house_font_renders_glyphs_at_every_size():
    """Embedded-bitmap strikes (Windows Calibri ships EBDT/EBLC) make FreeType select a
    bitmap at exactly the strike ppem sizes, and Agg then draws EMPTY outlines — the text
    vanishes while still *measuring* (so the overlap lint can't see it). figstyle strips
    the strikes at registration; this locks it: every size of the type scale (plus the
    choropleth's font-fit range) must produce visible glyphs at asset (150) and scene
    (165) dpi."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from teachersaid.pipeline import figstyle as fs

    sizes = sorted({*vars(fs.TYPE).values(), 6.0, 6.5, 7.5, 8.0})
    for dpi in (150, 165):
        for size in sizes:
            with plt.rc_context(fs.house_rc()):
                fig = plt.figure(figsize=(2.2, 0.6), dpi=dpi)
                fig.text(0.05, 0.35, "Wq19 Übung", fontsize=size)
                fig.canvas.draw()
                rgba = np.asarray(fig.canvas.buffer_rgba()).copy()
                plt.close(fig)
            assert (rgba[..., :3].min(axis=-1) < 128).any(), \
                f"{size} pt at {dpi} dpi rendered no glyphs (embedded-bitmap strike?)"


def test_overlap_lint_actually_detects_a_collision():
    # sanity: the lint is not vacuous — two labels at the same spot must be flagged
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.5, "Overlapping label one", ha="center")
    ax.text(0.5, 0.5, "Overlapping label two", ha="center")
    try:
        assert overlap_pairs(fig)
    finally:
        plt.close(fig)


def test_grid_table_never_exceeds_frame():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm

    from teachersaid.rendering import reportlab_base as rb
    width = A4[0] - 40 * mm
    huge = "Ein extrem langer Begriff der weit breiter ist als eine Spalte und umbrechen muss " * 3
    for t in (rb.grid_table([[f"1.  {huge}", f"a)  {huge}"]], width, header=False, weights=[1, 1]),
              rb.connect_blocks([huge, huge], [huge, huge], width)):
        w, _h = t.wrap(width, 10_000)
        assert w <= width + 0.5        # wrapped Paragraph cells → can never overflow the frame


def test_self_contained_payloads_get_no_redundant_writespace():
    """ordering / matching / multiple_choice render their OWN interaction surface, so the renderer
    adds no generic write-space (the redundant lines the SME flagged); open_response still does."""
    from unittest import mock

    import teachersaid.schema.blocks as B
    from teachersaid.rendering import blocks_to_flowables as bf
    from teachersaid.rendering import reportlab_base as rb
    from teachersaid.schema.response import BoxResponse, LinesResponse
    S = rb.styles()

    def _writespace_calls(task) -> int:
        with mock.patch.object(rb, "ruled_lines", wraps=rb.ruled_lines) as ml, \
                mock.patch.object(rb, "answer_box", wraps=rb.answer_box) as mb:
            bf._task_flowables(task, "student", S, 400, {}, 1)
            return ml.call_count + mb.call_count

    ordering = B.TaskBlock(id="o", kind="ordering", prompt="P", cognitive_level="remember",
                           payload=B.OrderingPayload(items=["a", "b"]), response=LinesResponse(n=2))
    matching = B.TaskBlock(id="m", kind="matching", prompt="P", cognitive_level="understand",
                           payload=B.MatchingPayload(left=["x", "y"], right=["p", "q"]),
                           response=LinesResponse(n=2))
    open_resp = B.TaskBlock(id="r", kind="open_response", prompt="P", cognitive_level="understand",
                            response=BoxResponse(min_height_mm=40))
    assert _writespace_calls(ordering) == 0       # numbers go in the payload's blanks
    assert _writespace_calls(matching) == 0       # drawn on the connect-blocks
    assert _writespace_calls(open_resp) == 1      # an open answer DOES need a box
