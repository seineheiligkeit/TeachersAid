"""The History asset-class flagship: GPB 'Der Wiener Kongress' (3. Kl.).

Locks the curated worked example the way test_library locks the MINT seeds: it builds,
resolves (by grade — GPB's KBs are strands), assembles and verifies CLEAN, and exercises
both provenance paths on real content — original-from-Wikipedia-facts (clean for students,
facts record teacher-only) and a real PD primary source quoted under Zitatrecht (attributed)."""

from __future__ import annotations

from datetime import date

from teachersaid.library import gpb_wiener_kongress as wk
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.orchestrator import _check_provenance_rights
from teachersaid.pipeline.prose_lint import lint_content as prose_lint
from teachersaid.pipeline.resolve import resolve_grade
from teachersaid.pipeline.verify import verify
from teachersaid.rendering import reportlab_base as rb
from teachersaid.rendering.blocks_to_flowables import block_flowables
from teachersaid.schema.provenance import SHORT_QUOTE_MAX_CHARS

TODAY = date(2026, 3, 1)


def _built():
    c = wk.build_content()
    res = resolve_grade(wk.SUBJECT, 3, today=TODAY)
    assemble(c, res)
    return c, res


def test_builds_and_verifies_clean():
    c, res = _built()
    rep = verify(c, res)
    assert rep.problems == [], rep.problems
    assert rep.warnings == [], rep.warnings          # the flagship is the quality bar — fully clean
    # it actually serves real GPB.US.3.* competences across the methoden/orientation strands
    served = {s.competence_id for b in c.iter_blocks() for s in getattr(b, "serves", [])}
    assert {"GPB.US.3.ALL.01", "GPB.US.3.ALL.02", "GPB.US.3.ALL.04"} <= served


def test_prose_gate_and_rights_gate_are_clean():
    c, _ = _built()
    assert prose_lint(c) == ([], [])                 # every fact block records its facts-source
    assert _check_provenance_rights(c, TODAY.year) == []  # the quoted PD source is clear


def test_both_provenance_paths_present():
    c, _ = _built()
    i1 = next(b for b in c.iter_blocks() if b.id == "wk.i1")
    assert i1.provenance.expression_origin == "original"
    assert i1.provenance.facts_sources()[0].url.endswith("oldid=267935028")
    assert i1.provenance.attribution_required is False        # original → clean for students

    q1 = next(b for b in c.iter_blocks() if b.id == "wk.q1")
    assert q1.provenance.expression_origin == "quoted"
    assert q1.provenance.attribution_required is True         # a quote is attributed…
    assert q1.provenance.share_alike_applies is False         # …but PD, so no ShareAlike
    assert len(wk._BUNDESAKTE_QUOTE) <= SHORT_QUOTE_MAX_CHARS  # rides Zitatrecht


def _text(block, projection):
    S = rb.styles()
    flat, stack = [], list(block_flowables(block, projection, S, 400, {}, number=1))
    while stack:
        f = stack.pop()
        inner = getattr(f, "_content", None)
        if inner:
            stack.extend(inner)
        else:
            getp = getattr(f, "getPlainText", None)
            if getp:
                flat.append(getp())
    return "\n".join(flat)


def test_projection_hides_facts_source_shows_quote_attribution():
    c, _ = _built()
    i1 = next(b for b in c.iter_blocks() if b.id == "wk.i1")
    q1 = next(b for b in c.iter_blocks() if b.id == "wk.q1")

    # the original learn block: students never see the Wikipedia facts record…
    s_i1 = _text(i1, "student")
    assert "Wikipedia" not in s_i1 and "Quelle" not in s_i1
    # …but the teacher does, to fact-check it
    assert "Wikipedia" in _text(i1, "teacher") and "Fakten" in _text(i1, "teacher")

    # the quoted primary source IS attributed to students (Quellenkritik is curriculum)
    s_q1 = _text(q1, "student")
    assert "Quelle" in s_q1 and "Bundesakte" in s_q1


def test_harvest_preserves_provenance():
    from teachersaid.library.block import harvest
    c, _ = _built()
    blocks = {lb.id.split(".", 1)[1]: lb for lb in harvest(c, example_key="wk")}
    assert blocks["wk.i1"].block.provenance.facts_sources()       # facts record survives
    assert blocks["wk.q1"].block.provenance.expression_origin == "quoted"


def test_seed_history_stages_clean(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.library import seed_history
    from teachersaid.store.repository import ReviewStore

    items = seed_history(ReviewStore(tmp_path / "store"), today=TODAY)
    assert len(items) == 1
    it = items[0]
    assert it.error is None and it.verify_problems == [] and it.status == "pending"
    assert it.artifacts and it.artifacts.student_pdf  # rendered for the Vorschau
