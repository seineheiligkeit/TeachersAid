"""Coherence & framing pass for a composed worksheet (Phase 3e) — OPTIONAL, LLM.

The composer (pipeline/compose.py) is deliberately no-LLM: it selects vetted blocks
and frames them with a fixed template + generic Kernfrage. This optional pass asks an
LLM to write the *connective* framing — a coherent Kernfrage, an orienting intro, and a
one-line lead-in before each task — so the sheet reads as a lesson rather than a pile of
on-target tasks.

Crucially it writes only the framing AROUND the blocks: the vetted TaskBlocks (prompts,
answers, competences) are never touched, so the no-drift guarantee is preserved. With no
generator (offline / no API key) it is a no-op — the deterministic template framing stands.
"""
from __future__ import annotations

from ..llm.client import StructuredGenerator
from ..llm.prompts import build_framing_system, build_framing_user
from ..schema.blocks import InfoBlock
from ..schema.enums import Role
from ..schema.generation_views import GenComposeFraming
from ..schema.worksheet import WorksheetContent


def frame_composition(
    content: WorksheetContent, *, generator: StructuredGenerator | None
) -> WorksheetContent:
    """Apply an LLM framing pass to a composed worksheet (in place) and return it.
    No generator ⇒ unchanged (template framing)."""
    if generator is None:
        return content

    framing: GenComposeFraming = generator.parse(
        build_framing_system(), build_framing_user(content), GenComposeFraming
    )

    # 1) the driving question
    if framing.kernfrage.strip():
        content.meta.kernfrage = framing.kernfrage.strip()

    # 2) the orienting intro — replace the composer's template prose, keep other intro
    #    blocks (figures / readable infos) in place
    if framing.intro.strip():
        replaced = False
        for b in content.intro:
            if b.role == Role.INFO and b.id == "cmp.intro":
                b.content = framing.intro.strip()
                replaced = True
                break
        if not replaced:
            content.intro.insert(0, InfoBlock(id="cmp.intro", kind="prose",
                                              content=framing.intro.strip()))

    # 3) a connective lead-in before each named task (a prose InfoBlock; the task itself
    #    is untouched — no-drift). Unknown block_ids are ignored.
    leadin = {t.block_id: t.text.strip() for t in framing.transitions if t.text.strip()}
    for sec in content.sections:
        rebuilt = []
        for b in sec.blocks:
            if b.role == Role.TASK and b.id in leadin:
                rebuilt.append(InfoBlock(id=f"cmp.lead.{b.id}", kind="prose",
                                         content=leadin[b.id]))
            rebuilt.append(b)
        sec.blocks = rebuilt

    return content
