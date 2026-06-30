"""Realien — CEFR-leveled communicative reading for modern FS (Documents/realien-design.md).

Phase 1 flagship: an A2 English "At the station" Realie. These lock the simplified model end to
end: a CONSTRUCTED text needs no source and rides no rights gate; the derivation produces the
communicative-first task layer (scan warm-up · write-a-message · an oral Sprechkarte with NO
write-space); the internal-consistency lint passes but catches an answer the board can't support;
and all three projections render. The facts are fiction — what the gate protects is consistency
(here) and the language (the SME, not testable).
"""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library.realie_bahnhof import BAHNHOF
from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.realie_lint import lint
from teachersaid.pipeline.text_tasks import build_worksheet
from teachersaid.pipeline.verify import verify

IN = date(2026, 3, 1)


def _build():
    content, res = build_worksheet(BAHNHOF, today=IN)
    assemble(content, res)
    return content, res


# --- schema: constructed-is-default, source optional ------------------------

def test_constructed_realie_has_no_source_and_is_the_default():
    assert BAHNHOF.origin == "constructed"
    assert BAHNHOF.source is None          # constructed fiction → no source/rights gate
    assert BAHNHOF.cefr == "A2" and BAHNHOF.scene == "Am Bahnhof"
    assert BAHNHOF.facts and all(f.value for f in BAHNHOF.facts)


# --- derivation: the communicative-first task layer -------------------------

def test_derivation_builds_scan_write_and_oral_tasks():
    content, _ = _build()
    tasks = [b for b in content.iter_blocks() if b.role.value == "task"]
    by_kind = {}
    for t in tasks:
        by_kind.setdefault(t.kind, []).append(t)
    # scan warm-up (Lesen), a written-communicative task (Schreiben), an oral Sprechkarte (Sprechen)
    assert len(by_kind["open_response"]) == 3 and all(t.dimensions == ["LES"] for t in by_kind["open_response"])
    assert by_kind["text_production"][0].dimensions == ["SCH"]
    assert by_kind["text_production"][0].response.mode == "box"
    rp = by_kind["speaking_task"][0]
    assert rp.dimensions == ["SPR"]
    assert rp.response.mode == "none"                  # oral — served in the room, not on paper
    assert rp.payload is not None and rp.payload.kind == "role_play" and len(rp.payload.cues) == 2
    # each task is anchored to the matching FS1 skill competence
    serves = {s.competence_id for t in tasks for s in t.serves}
    assert {"FS1.US.2.LES.02", "FS1.US.2.SCH.03", "FS1.US.2.SPR.02"} <= serves


def test_realie_renders_as_a_card_not_numbered_text():
    """A Realie reads as a real ARTIFACT (no line numbers → a material card); an authentic text
    keeps its line numbers (tasks reference "Zeile N")."""
    content, _ = _build()
    src = next(b for b in content.iter_blocks() if getattr(b, "kind", None) == "source_text")
    assert src.numbered is False                 # the departure board → a material card
    from teachersaid.library.texts import LORELEY
    poem, _ = build_worksheet(LORELEY, today=IN)
    psrc = next(b for b in poem.iter_blocks() if getattr(b, "kind", None) == "source_text")
    assert psrc.numbered is True                 # the poem keeps line numbers


def test_worksheet_is_verify_clean():
    content, res = _build()
    report = verify(content, res)
    assert report.problems == [], report.problems


def test_roleplay_adds_no_writespace():
    """The Sprechkarte IS the surface — the renderer adds no generic write-space (an oral task)."""
    from unittest import mock

    from teachersaid.rendering import blocks_to_flowables as bf
    from teachersaid.rendering import reportlab_base as rb
    S = rb.styles()
    content, _ = _build()
    rp = next(b for b in content.iter_blocks()
              if getattr(getattr(b, "payload", None), "kind", None) == "role_play")
    with mock.patch.object(rb, "ruled_lines", wraps=rb.ruled_lines) as ml, \
            mock.patch.object(rb, "answer_box", wraps=rb.answer_box) as mb:
        bf._task_flowables(rp, "student", S, 400, {}, 5)
        assert ml.call_count + mb.call_count == 0      # cue cards only, no lines/box


# --- the internal-consistency lint (NOT world-grounding) --------------------

def test_lint_clean_on_flagship():
    assert lint(BAHNHOF) == ([], [])


def test_lint_catches_an_answer_the_board_cannot_support():
    bad = BAHNHOF.model_copy(deep=True)
    # a scan answer that cites a departure time absent from the board → internal inconsistency
    next(a for a in bad.annotations if a.kind == "comprehension").answer = "At 07:00, from Platform 9."
    problems, _ = lint(bad)
    assert any("07:00" in p for p in problems), problems


# --- rights: constructed rides no gate; sourced still does ------------------

def test_ingest_constructed_realie_stages_without_a_rights_gate(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.store.textstore import TextStore
    store = TextStore(tmp_path / "texts")
    rec = orch.ingest_text(store, BAHNHOF, today=IN)   # source=None must NOT raise
    assert rec.id == BAHNHOF.id and store.get(BAHNHOF.id) is not None


def test_ingest_rejects_an_internally_inconsistent_realie(tmp_path):
    from teachersaid.store.textstore import TextStore
    bad = BAHNHOF.model_copy(deep=True)
    next(a for a in bad.annotations if a.kind == "comprehension").answer = "At 06:00."
    with pytest.raises(ValueError, match="Inkonsistenz"):
        orch.ingest_text(TextStore(tmp_path / "t"), bad, today=IN)


def test_lint_exempts_a_shown_sum_but_catches_a_bare_wrong_price():
    """Café genre: a price shown in a SUM (£2.00 + £3.00 = £5.00) is a computation over the menu
    (exempt — the £5.00 isn't on the menu); a BARE wrong price is still an inconsistency."""
    from teachersaid.library.realie_cafe import CAFE
    assert lint(CAFE) == ([], [])                    # the "= £5.00" order-total task is clean
    bare = CAFE.model_copy(deep=True)
    next(a for a in bare.annotations if a.kind == "comprehension").answer = "£9.99."
    problems, _ = lint(bare)
    assert any("£9.99" in p for p in problems), problems


def test_lint_counts_the_task_prompt_so_a_stated_constraint_is_consistent():
    """Richer tasks introduce a constraint in their OWN prompt (a 09:00 deadline); an answer that
    references it is consistent. A time that is nowhere (board/facts/prompt) is still caught."""
    from teachersaid.schema.texts import AnnotatedText, Annotation
    base = dict(id="x", title="t", subject="Erste lebende Fremdsprache", klasse=2,
                scene="Am Bahnhof", cefr="A2", text="08:14 to London — Platform 3")
    ok = AnnotatedText(**base, annotations=[Annotation(
        kind="comprehension", dimensions=["LES"],
        label="Be in London before 09:00. Which train, and why not a later one?",
        answer="The 08:14 train; a later one would arrive after 09:00.")])
    assert lint(ok) == ([], [])                       # 09:00 comes from the prompt → consistent
    bad = AnnotatedText(**base, annotations=[Annotation(
        kind="comprehension", dimensions=["LES"], label="Which train?",
        answer="The 07:30 train.")])                  # 07:30 is nowhere → flagged
    assert any("07:30" in p for p in lint(bad)[0])


def test_richer_tasks_give_a_real_cognitive_spread():
    """Lever 1: the flagships are no longer flat lookups — they span understand→analyze→evaluate."""
    content, _ = _build()
    levels = {b.cognitive_level for b in content.iter_blocks() if b.role.value == "task"}
    assert {"understand", "analyze"} <= levels and len(levels) >= 3


def test_cafe_second_genre_builds_clean():
    """The engine isn't timetable-locked: the café menu derives the same communicative-first
    layer (scan · write-an-order · Sprechkarte) and verifies clean."""
    from teachersaid.library.realie_cafe import CAFE
    content, res = build_worksheet(CAFE, today=IN)
    assemble(content, res)
    assert verify(content, res).problems == []
    kinds = {b.kind for b in content.iter_blocks() if b.role.value == "task"}
    assert {"open_response", "text_production", "speaking_task"} <= kinds
    assert CAFE.cefr == "A2" and CAFE.origin == "constructed" and CAFE.source is None


# --- Phase 2b: the arrangement wrap (the worksheet + arrangement engines compose) ----

def _wrap(at):
    from teachersaid.pipeline.arrange import assemble_arrangement, verify_arrangement
    from teachersaid.pipeline.realie_arrange import build_arrangement
    from teachersaid.pipeline.resolve import resolve_grade
    arr = build_arrangement(at, today=IN)
    res = resolve_grade(arr.meta.subject, arr.meta.klasse, today=IN)
    assemble_arrangement(arr, res)
    return arr, verify_arrangement(arr, res)


def test_realie_wraps_as_a_verify_clean_arrangement():
    from teachersaid.library.realie_cafe import CAFE
    arr, rep = _wrap(CAFE)
    assert rep.problems == [], rep.problems
    assert arr.meta.format == "simulation_game"
    assert len(arr.phases) == 3 and arr.total_minutes() == 30
    assert len(arr.roles) == 1 and arr.roles[0].material.sections   # the Realie worksheet is the material


def test_speaking_is_an_anchor_only_competence_the_sheet_cannot_reach():
    """The v0.5 payoff: a Sprechen competence covered ONLY by the interaction, no printable task."""
    from teachersaid.library.realie_bahnhof import BAHNHOF
    arr, _ = _wrap(BAHNHOF)
    assert arr.competence_anchors and arr.competence_anchors[0].served_by == "interaction"
    anchor_id = arr.competence_anchors[0].competence_id
    cov = {e.competence_id: e for e in arr.nachweis.competence_coverage}
    assert cov[anchor_id].covered and cov[anchor_id].exercised_by == ["anchor:interaction"]
    served = {s.competence_id for r in arr.roles for b in r.material.iter_blocks()
              if b.role.value == "task" for s in b.serves}
    assert anchor_id not in served                  # no task serves it — only the interaction does


def test_arrangement_bundle_renders(tmp_path):
    from teachersaid.pipeline.arrange import render_arrangement
    from teachersaid.library.realie_cafe import CAFE
    arr, rep = _wrap(CAFE)
    assert rep.problems == []
    bundle = render_arrangement(arr, tmp_path / "arr")   # reuses the worksheet renderers, no new one
    assert bundle["orchestration"] and bundle["roles"]


def test_sourced_text_still_runs_the_rights_gate(tmp_path):
    """The simplified gate didn't weaken the sourced path: a not-yet-PD source still raises."""
    from teachersaid.schema.texts import AnnotatedText, TextSourceRef
    from teachersaid.store.textstore import TextStore
    sourced = AnnotatedText(
        id="x-sourced", title="X", subject="Deutsch", klasse=3, text="Ein Satz.",
        origin="sourced",
        source=TextSourceRef(author="Lebende Autorin", title="X", author_death_year=2010,
                             rights_basis="public_domain_pma", repository="—", attribution="—"))
    with pytest.raises(ValueError, match="rights"):
        orch.ingest_text(TextStore(tmp_path / "t"), sourced, today=IN)
