"""Generation views: the flattened models the LLM emits, + to_canonical().

These are the single seam between "what the model produces" and "what the system
stores". Differences from canonical models, all to satisfy Anthropic structured
outputs and to keep derived data un-authorable:

* RichText fields are plain `str` (no string|array union, no inline marks/refs) —
  the strictly simpler shape; canonical RichText accepts a bare string.
* No `nachweis` / `depth_profile` — those are DERIVED at assemble, never generated.
* `kind` / `cognitive_level` stay plain strings; the allowed set is injected into
  the prompt and validated during up-conversion, not as a closed JSON enum.
* Reuses the canonical `ResponseSpec` / `TaskPayload` unions (one-level, JSON-safe).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from .blocks import (
    ContentFlags,
    InfoBlock,
    Serves,
    TaskBlock,
    TaskPayload,
)
from .enums import CalloutRole, InfoKind, Role
from .response import ResponseSpec
from .worksheet import Baustein, WorksheetContent


class GenInfoBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["info"] = "info"
    id: str
    kind: InfoKind
    content: str
    callout_role: CalloutRole | None = None
    teacher_note: str | None = None
    watch_outs: list[str] = Field(default_factory=list)
    optional: bool = False
    modality: str = "printable"
    asset_refs: list[str] = Field(default_factory=list)
    flags: ContentFlags | None = None


class GenTaskBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["task"] = "task"
    id: str
    kind: str
    prompt: str
    payload: TaskPayload | None = None
    response: ResponseSpec
    cognitive_level: str
    dimensions: list[str] = Field(default_factory=list)
    content_area: str | None = None
    serves: list[Serves] = Field(default_factory=list)
    est_minutes: int = 0
    answer_key: str | None = None
    acceptable_reasoning: str | None = None
    watch_outs: list[str] = Field(default_factory=list)
    self_check: str | None = None
    optional: bool = False
    modality: str = "printable"
    asset_refs: list[str] = Field(default_factory=list)
    flags: ContentFlags | None = None


GenBlock = Annotated[GenInfoBlock | GenTaskBlock, Field(discriminator="role")]


class GenBaustein(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    throughline: str = ""
    timing_notes: str | None = None
    differentiation: str | None = None
    blocks: list[GenBlock] = Field(default_factory=list)


class GenWorksheetBody(BaseModel):
    """What the LLM generates: intro + sections. Meta/subject_model/assets/fassung
    come from the pipeline (resolution + plan), not the model."""

    model_config = ConfigDict(extra="forbid")
    intro: list[GenBlock] = Field(default_factory=list)
    sections: list[GenBaustein] = Field(default_factory=list)


# --- up-conversion -----------------------------------------------------------
def _info_to_canonical(g: GenInfoBlock) -> InfoBlock:
    return InfoBlock(
        id=g.id,
        kind=g.kind,
        content=g.content,
        callout_role=g.callout_role,
        teacher_note=g.teacher_note,
        watch_outs=g.watch_outs,
        optional=g.optional,
        modality=g.modality,
        asset_refs=g.asset_refs,
        flags=g.flags,
    )


def _task_to_canonical(g: GenTaskBlock) -> TaskBlock:
    return TaskBlock(
        id=g.id,
        kind=g.kind,
        prompt=g.prompt,
        payload=g.payload,
        response=g.response,
        cognitive_level=g.cognitive_level,
        dimensions=g.dimensions,
        content_area=g.content_area,
        serves=g.serves,
        est_minutes=g.est_minutes,
        answer_key=g.answer_key,
        acceptable_reasoning=g.acceptable_reasoning,
        watch_outs=g.watch_outs,
        self_check=g.self_check,
        optional=g.optional,
        modality=g.modality,
        asset_refs=g.asset_refs,
        flags=g.flags,
    )


def _block_to_canonical(g: GenBlock):
    return _info_to_canonical(g) if g.role == Role.INFO else _task_to_canonical(g)


def _baustein_to_canonical(g: GenBaustein) -> Baustein:
    overview = {"throughline": g.throughline}
    if g.timing_notes:
        overview["timing_notes"] = g.timing_notes
    if g.differentiation:
        overview["differentiation"] = g.differentiation
    return Baustein(
        id=g.id,
        title=g.title,
        teacher_overview=overview,
        blocks=[_block_to_canonical(b) for b in g.blocks],
    )


def body_to_canonical(
    body: GenWorksheetBody, *, meta, subject_model, assets=None, rack=None
) -> WorksheetContent:
    """Merge generated body with pipeline-supplied meta/subject_model/assets.

    Returns a WorksheetContent WITHOUT derived fields; pipeline.assemble() fills
    nachweis/depth_profile.
    """
    return WorksheetContent(
        meta=meta,
        subject_model=subject_model,
        intro=[_block_to_canonical(b) for b in body.intro],
        sections=[_baustein_to_canonical(s) for s in body.sections],
        assets=assets or [],
        rack=rack,
    )
