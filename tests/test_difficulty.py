"""Phase 3d: difficulty as an honest, bounded estimate + composer calibration.

difficulty (1-3) is an author/SME estimate (never measured); when unset it falls back
to the Anforderungsbereich of cognitive_level. Surfaced in DepthProfile.by_difficulty,
checked by verify (flat-spectrum warning), and used by compose to span the bands.
"""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library.block import LibraryBlock
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.compose import compose
from teachersaid.pipeline.difficulty import effective_difficulty
from teachersaid.pipeline.plan import _ENVELOPE_MINUTES
from teachersaid.pipeline.resolve import resolve_kompetenzbereich
from teachersaid.pipeline.verify import verify
from teachersaid.schema.blocks import Serves, TaskBlock
from teachersaid.schema.enums import Role
from teachersaid.schema.response import LinesResponse

IN = date(2026, 3, 1)
PHY_KB = "Strahlung und Radioaktivität"


def _task(bid, level, difficulty=None):
    return TaskBlock(id=bid, kind="open_response", prompt="Aufgabe.", response=LinesResponse(n=2),
                     cognitive_level=level, difficulty=difficulty, dimensions=["S"],
                     serves=[Serves(competence_id="PHY.US.4.STR.02", relation="exercises")],
                     est_minutes=15)


def _lb(bid, level, difficulty=None):
    t = _task(bid, level, difficulty)
    return LibraryBlock(id=f"d.{bid}", block=t, role="task", kind="open_response", subject="Physik",
                        klasse=4, kompetenzbereich=PHY_KB, competences=["PHY.US.4.STR.02"],
                        cognitive_level=level, dimensions=["S"], status="approved")


def test_effective_difficulty_fallback_and_override():
    assert effective_difficulty(_task("a", "remember")) == 1      # Reproduktion
    assert effective_difficulty(_task("b", "analyze")) == 2       # Transfer
    assert effective_difficulty(_task("c", "create")) == 3        # Reflexion
    # an explicit author/SME estimate overrides the cognitive-derived default
    assert effective_difficulty(_task("d", "remember", difficulty=3)) == 3


def test_difficulty_field_validates_range():
    _task("ok", "remember", difficulty=2)  # fine
    with pytest.raises(Exception):
        _task("bad", "remember", difficulty=5)


def _store(tmp_path, monkeypatch, blocks):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    from teachersaid.store.blockstore import BlockStore
    bs = BlockStore(tmp_path / "blocks")
    for b in blocks:
        bs.upsert(b)
    return bs


def test_compose_calibration_keeps_a_stretch_under_tight_budget(tmp_path, monkeypatch):
    """The real 3d value: with a budget too small for all blocks, four easy (band-1)
    blocks would crowd out the one stretch under plain greedy-from-easy. Calibration
    seeds one block per band, so the stretch survives."""
    bs = _store(tmp_path, monkeypatch,
                [_lb(f"easy{i}", "understand") for i in range(4)] + [_lb("stretch", "evaluate")])
    content, _ = compose("Physik", 4, "Strahlung", kompetenzbereich=PHY_KB,
                         envelope="einzelstunde", block_store=bs, today=IN)
    tasks = [b for b in content.iter_blocks() if b.role == Role.TASK]
    assert "evaluate" in {t.cognitive_level for t in tasks}      # the stretch survived
    assert len(tasks) < 5                                        # budget did exclude some


def test_flat_difficulty_warns_and_profile_populated(tmp_path, monkeypatch):
    """A sheet of only band-1 tasks → DepthProfile.by_difficulty {'1': n} + a verify
    warning (advisory, not a problem)."""
    bs = _store(tmp_path, monkeypatch, [_lb(f"r{i}", "remember") for i in range(3)])
    content, res = compose("Physik", 4, "Strahlung", kompetenzbereich=PHY_KB,
                           envelope="block", block_store=bs, today=IN)
    assemble(content, res)
    assert content.depth_profile.by_difficulty == {"1": 3}
    report = verify(content, res)
    assert report.problems == []                                # advisory only
    assert any("flach" in w for w in report.warnings)


def test_varied_difficulty_no_flat_warning(tmp_path, monkeypatch):
    bs = _store(tmp_path, monkeypatch,
                [_lb("r", "remember"), _lb("a", "analyze"), _lb("e", "evaluate")])
    content, res = compose("Physik", 4, "Strahlung", kompetenzbereich=PHY_KB,
                           envelope="block", block_store=bs, today=IN)
    assemble(content, res)
    assert set(content.depth_profile.by_difficulty) == {"1", "2", "3"}
    assert not any("flach" in w for w in verify(content, res).warnings)
