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

from .assets import Asset
from .datasets import DataRef
from .blocks import (
    ContentFlags,
    InfoBlock,
    RubricCriterion,
    Serves,
    TaskBlock,
    TaskPayload,
)
from .enums import CalloutRole, InfoKind, Role
from .response import ResponseSpec
from .worksheet import Baustein, TeacherOverview, WorksheetContent


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
    difficulty: int | None = None  # 1/2/3 author estimate (optional; 3d)
    dimensions: list[str] = Field(default_factory=list)
    content_area: str | None = None
    serves: list[Serves] = Field(default_factory=list)
    est_minutes: int = 0
    answer_key: str | None = None
    acceptable_reasoning: str | None = None
    rubric: list[RubricCriterion] = Field(default_factory=list)  # teacher: criterion + levels
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
    talking_points: list[str] = Field(default_factory=list)  # teacher: discussion anchors
    extensions: list[str] = Field(default_factory=list)  # teacher: going-further ideas
    timing_notes: str | None = None
    differentiation: str | None = None
    blocks: list[GenBlock] = Field(default_factory=list)


class GenAsset(BaseModel):
    """A code-generated asset the LLM may REQUEST (a figure from the recipe library):
    `generator` is a recipe id, `spec` its parameters; blocks point at it via asset_refs."""
    model_config = ConfigDict(extra="forbid")
    id: str
    role: str = "figure"
    generator: str
    spec: dict = Field(default_factory=dict)
    data_source: DataRef | None = None       # references a vetted dataset (b) — cited
    illustrative: bool = False               # schematic/example data (c) — not real
    caption: str | None = None


class GenDataFigure(BaseModel):
    """A data figure declared by INTENT, not chart type: the model says what the data
    *is* (trend / comparison / relationship / composition / distribution / scale) and the
    data; `chart_choose.choose_representation` picks the appropriate chart + renders it
    correct-by-construction. This is how we escape 'everything is a bar chart'."""
    model_config = ConfigDict(extra="forbid")
    id: str
    intent: str                                          # see chart_choose.INTENTS
    title: str | None = None
    xlabel: str | None = None
    ylabel: str | None = None
    categories: list[str] = Field(default_factory=list)  # comparison / composition / trend / scale
    values: list[float] = Field(default_factory=list)
    points: list[list[float]] = Field(default_factory=list)  # relationship / numeric trend
    male: list[float] = Field(default_factory=list)      # demographic: men per age band
    female: list[float] = Field(default_factory=list)    # demographic: women per age band
    months: list[str] = Field(default_factory=list)      # climate: month labels (12)
    temp: list[float] = Field(default_factory=list)      # climate: monthly temperature
    precip: list[float] = Field(default_factory=list)    # climate: monthly precipitation
    events: list[dict] = Field(default_factory=list)     # timeline: [{at, label}]
    log: bool = False
    fit: bool = False                                    # scatter: draw a linear trend line
    data_source: DataRef | None = None                  # references a vetted dataset (b) — cited
    illustrative: bool = False                           # schematic/example data (c) — not real
    caption: str | None = None


def data_figure_to_asset(g: GenDataFigure) -> Asset:
    """Compile an intent-declared figure to a concrete code-gen Asset via the chooser."""
    from .chart_choose import choose_representation
    gen, spec = choose_representation(g.intent, {
        "title": g.title, "xlabel": g.xlabel, "ylabel": g.ylabel,
        "categories": g.categories or None, "values": g.values or None,
        "points": g.points or None, "log": g.log, "fit": g.fit,
        "age_groups": g.categories or None, "male": g.male or None, "female": g.female or None,
        "months": g.months or None, "temp": g.temp or None, "precip": g.precip or None,
        "events": g.events or None,
    })
    return Asset(id=g.id, role="figure", generator=gen, spec=spec,
                 data_source=g.data_source, illustrative=g.illustrative, caption=g.caption)


class GenWorksheetBody(BaseModel):
    """What the LLM generates: intro + sections + any requested assets. Meta/subject_model/
    fassung come from the pipeline (resolution + plan), not the model. `data_figures` are
    declared by intent (preferred for data charts); `assets` are concrete recipe requests."""

    model_config = ConfigDict(extra="forbid")
    intro: list[GenBlock] = Field(default_factory=list)
    sections: list[GenBaustein] = Field(default_factory=list)
    assets: list[GenAsset] = Field(default_factory=list)
    data_figures: list[GenDataFigure] = Field(default_factory=list)


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
        difficulty=g.difficulty,
        dimensions=g.dimensions,
        content_area=g.content_area,
        serves=g.serves,
        est_minutes=g.est_minutes,
        answer_key=g.answer_key,
        acceptable_reasoning=g.acceptable_reasoning,
        rubric=g.rubric,
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
    return Baustein(
        id=g.id,
        title=g.title,
        teacher_overview=TeacherOverview(
            throughline=g.throughline or None,
            talking_points=g.talking_points,
            extensions=g.extensions,
            differentiation=g.differentiation,
            timing_notes=g.timing_notes,
        ),
        blocks=[_block_to_canonical(b) for b in g.blocks],
    )


def body_to_canonical(
    body: GenWorksheetBody, *, meta, subject_model, assets=None, rack=None
) -> WorksheetContent:
    """Merge generated body with pipeline-supplied meta/subject_model/assets.

    Returns a WorksheetContent WITHOUT derived fields; pipeline.assemble() fills
    nachweis/depth_profile.
    """
    gen_assets = [
        Asset(id=a.id, role=a.role, generator=a.generator, spec=a.spec,
              data_source=a.data_source, illustrative=a.illustrative, caption=a.caption)
        for a in body.assets
    ]
    gen_assets += [data_figure_to_asset(g) for g in body.data_figures]  # intent → chosen chart
    return WorksheetContent(
        meta=meta,
        subject_model=subject_model,
        intro=[_block_to_canonical(b) for b in body.intro],
        sections=[_baustein_to_canonical(s) for s in body.sections],
        assets=gen_assets + list(assets or []),
        rack=rack,
    )


# --- Lernarrangement generation view (v0.5) ----------------------------------
class GenArrangementRole(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    share: str | int = "all"
    private: bool = False
    material: GenWorksheetBody          # each role's sheet IS a worksheet body


class GenArrangementPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    grouping: str                       # individual | role_group | home_group | plenary
    minutes: int
    what_happens: str


class GenSharedProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str
    rubric: list[RubricCriterion] = Field(default_factory=list)


class GenCompetenceAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    competence_id: str
    dimension: str
    served_by: str                      # interaction | debrief | shared_product | role:<id>


class GenArrangementBody(BaseModel):
    """What the LLM generates for a Lernarrangement (the `body`). Meta (title/subject/
    klasse/fassung/format) is supplied by the pipeline from the wrapper, NOT in the body;
    common_material/debrief are info blocks."""
    model_config = ConfigDict(extra="forbid")
    common_material: list[GenInfoBlock] = Field(default_factory=list)
    roles: list[GenArrangementRole] = Field(default_factory=list)
    phases: list[GenArrangementPhase] = Field(default_factory=list)
    shared_product: GenSharedProduct | None = None
    debrief: list[GenInfoBlock] = Field(default_factory=list)
    competence_anchors: list[GenCompetenceAnchor] = Field(default_factory=list)


class GenTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    block_id: str
    text: str


class GenComposeFraming(BaseModel):
    """Phase 3e: the connective FRAMING an LLM writes AROUND already-vetted, fixed
    composed blocks — a coherent Kernfrage + orienting intro + a per-task lead-in.
    Never new tasks/facts (the blocks carry the content); applied by pipeline/frame.py,
    nothing is up-converted, so the no-drift guarantee holds."""
    model_config = ConfigDict(extra="forbid")
    kernfrage: str
    intro: str
    transitions: list[GenTransition] = Field(default_factory=list)


def arrangement_body_to_canonical(body: GenArrangementBody, *, meta, subject_model):
    """Up-convert a generated arrangement body to a `Lernarrangement` (DERIVED fields
    left empty; pipeline.assemble_arrangement fills them). Each role's material reuses
    `body_to_canonical`; its WorksheetMeta is derived from the arrangement meta."""
    from .arrangement import (
        ArrangementPhase,
        ArrangementRole,
        CompetenceAnchor,
        Lernarrangement,
        SharedProduct,
    )
    from .worksheet import WorksheetMeta

    def _role_meta(label: str) -> WorksheetMeta:
        return WorksheetMeta(
            title=label, subject=meta.subject, stufe=meta.stufe, klasse=meta.klasse,
            kernfrage=meta.kernfrage, fassung=meta.fassung, lehrplan_label=meta.lehrplan_label,
        )

    roles = [
        ArrangementRole(
            id=r.id, label=r.label, share=r.share, private=r.private,
            material=body_to_canonical(r.material, meta=_role_meta(r.label),
                                       subject_model=subject_model),
        )
        for r in body.roles
    ]
    return Lernarrangement(
        meta=meta,
        common_material=[_info_to_canonical(b) for b in body.common_material],
        roles=roles,
        phases=[ArrangementPhase(id=p.id, label=p.label, grouping=p.grouping,
                                 minutes=p.minutes, what_happens=p.what_happens)
                for p in body.phases],
        shared_product=(SharedProduct(description=body.shared_product.description,
                                      rubric=body.shared_product.rubric)
                        if body.shared_product else None),
        debrief=[_info_to_canonical(b) for b in body.debrief],
        competence_anchors=[CompetenceAnchor(competence_id=a.competence_id,
                                             dimension=a.dimension, served_by=a.served_by)
                            for a in body.competence_anchors],
    )
