"""Phase 3e: the optional LLM coherence/framing pass over a composed worksheet.

Injected (mock) generator → a coherent Kernfrage + intro + per-task lead-ins are added
AROUND the vetted blocks; the TaskBlocks themselves are untouched (no-drift). Offline
(no generator) → unchanged template framing.
"""

from __future__ import annotations

from datetime import date

import pytest

from teachersaid.library import seed_blocks
from teachersaid.pipeline import orchestrator as orch
from teachersaid.pipeline.assemble import assemble
from teachersaid.pipeline.compose import compose
from teachersaid.pipeline.frame import frame_composition
from teachersaid.pipeline.verify import verify
from teachersaid.schema.enums import Role
from teachersaid.schema.generation_views import GenComposeFraming, GenTransition
from teachersaid.store.blockstore import BlockStore
from teachersaid.store.repository import ReviewStore

IN = date(2026, 3, 1)
PHY = "Strahlung und Radioaktivität"


@pytest.fixture
def stores(tmp_path, monkeypatch):
    import teachersaid.config as cfg
    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path)
    bs = BlockStore(tmp_path / "blocks")
    seed_blocks(bs)
    return ReviewStore(tmp_path / "store"), bs


def _rt(v):
    return "".join(getattr(r, "text", "") for r in v) if isinstance(v, list) else v


class _Framer:
    """A fake StructuredGenerator returning a fixed framing for the given task ids."""
    def __init__(self, kernfrage, intro, task_ids):
        self.k, self.i, self.ids = kernfrage, intro, task_ids

    def parse(self, system, user, schema):
        return GenComposeFraming(
            kernfrage=self.k, intro=self.i,
            transitions=[GenTransition(block_id=t, text=f"Übergang zu {t}.") for t in self.ids])


def test_frame_adds_coherent_framing_without_touching_tasks(stores):
    _, bs = stores
    content, res = compose("Physik", 4, PHY, kompetenzbereich=PHY, block_store=bs, today=IN)
    tids = [b.id for b in content.iter_blocks() if b.role == Role.TASK]
    before = {b.id: _rt(b.prompt) for b in content.iter_blocks() if b.role == Role.TASK}

    frame_composition(content, generator=_Framer("Was macht Strahlung gefährlich?",
                                                 "Strahlung begegnet dir überall.", tids))

    assert content.meta.kernfrage == "Was macht Strahlung gefährlich?"
    intro_b = next(b for b in content.intro if getattr(b, "id", None) == "cmp.intro")
    assert intro_b.content == "Strahlung begegnet dir überall."
    sec = content.sections[0]
    leads = [b for b in sec.blocks if b.role == Role.INFO and b.id.startswith("cmp.lead.")]
    assert len(leads) == len(tids)                                  # one lead-in per task
    assert [b.id for b in sec.blocks if b.role == Role.TASK] == tids  # tasks intact + ordered
    assert {b.id: _rt(b.prompt) for b in content.iter_blocks() if b.role == Role.TASK} == before
    assemble(content, res)
    assert verify(content, res).problems == []                      # framing breaks nothing


def test_frame_is_noop_without_generator(stores):
    _, bs = stores
    content, _ = compose("Physik", 4, PHY, kompetenzbereich=PHY, block_store=bs, today=IN)
    kf = content.meta.kernfrage
    frame_composition(content, generator=None)
    assert content.meta.kernfrage == kf                             # template framing stands
    assert not any(getattr(b, "id", "").startswith("cmp.lead.") for b in content.iter_blocks())


def test_compose_worksheet_applies_framing_when_generator_given(stores):
    rs, bs = stores

    class M:
        def parse(self, system, user, schema):
            return GenComposeFraming(kernfrage="Geframte Kernfrage?",
                                     intro="Geframter Einstieg.", transitions=[])

    item = orch.compose_worksheet(rs, bs, "Physik", 4, PHY, generator=M(), today=IN)
    assert item.error is None, item.error
    assert item.content.meta.kernfrage == "Geframte Kernfrage?"
