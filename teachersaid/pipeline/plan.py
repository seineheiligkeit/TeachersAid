"""Plan (mostly deterministic) — schema §7 step 2.

Turns a resolution + time envelope into a block-spec skeleton that targets a
DepthTarget ladder (predict → reason-with-data → evaluate-claims → transfer).
The plan IS the idea-stage review artifact: threads + specs + target, no prose
yet, so a human can approve direction before any generation spends tokens.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..grounding import lehrplan_store as store
from ..schema.derived import DepthTarget
from ..schema.enums import AnchorMode
from ..schema.worksheet import LehrplanResolution

# Minutes budget per time envelope.
_ENVELOPE_MINUTES = {
    "einzelstunde": 50,
    "doppelstunde": 100,
    "block": 150,
    "custom": 100,
}

# A small ladder of (cognitive_level, intent template) climbing in demand.
_LADDER = [
    ("understand", "Grundidee in eigenen Worten erklären"),
    ("apply", "das Konzept auf eine neue Alltagssituation anwenden"),
    ("analyze", "zwei Fälle gegenüberstellen und den Unterschied begründen"),
    ("evaluate", "eine Aussage/These prüfen und begründet bewerten"),
]


class BlockSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    suggested_id: str
    kind: str  # a core kind or subject extension
    cognitive_level: str
    dimension: str  # primary DimensionRef
    serves_competence_id: str | None = None
    est_minutes: int
    intent: str  # short, words-free brief for the generator


class SectionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    throughline: str
    block_specs: list[BlockSpec] = Field(default_factory=list)


class WorksheetPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str
    klasse: int
    topic: str
    anchor_mode: AnchorMode = AnchorMode.COMPETENCE
    anchor_uet: int | None = None
    kernfrage: str
    competence_ids: list[str] = Field(default_factory=list)
    dimensions_targeted: list[str] = Field(default_factory=list)
    threads: list[str] = Field(default_factory=list)  # creative idea seeds
    depth_target: DepthTarget = Field(default_factory=DepthTarget)
    section_specs: list[SectionSpec] = Field(default_factory=list)
    minutes_budget: int = 100
    notes: list[str] = Field(default_factory=list)


def plan(
    resolution: LehrplanResolution, envelope: str = "doppelstunde", *, topic: str = "",
    anchor_mode: AnchorMode = AnchorMode.COMPETENCE, anchor_uet: int | None = None,
) -> WorksheetPlan:
    budget = _ENVELOPE_MINUTES.get(envelope, 100)
    comps = resolution.competences if anchor_mode == AnchorMode.COMPETENCE else []
    # Fall back to the subject model's first dimension (not a hardcoded "W") so
    # non-science subjects without a per-competence dimension stay valid for verify.
    _model = store.get_subject_model(resolution.subject)
    default_dim = _model.dimensions[0].id if _model and _model.dimensions else "W"
    topic = topic or (
        resolution.matched_kompetenzbereiche[0]
        if resolution.matched_kompetenzbereiche
        else resolution.subject
    )

    dims_targeted: list[str] = []
    section_specs: list[SectionSpec] = []
    threads: list[str] = []
    spent = 0
    spec_n = 0

    for comp in comps:
        primary_dim = comp.dimensions[0] if comp.dimensions else default_dim
        if primary_dim not in dims_targeted:
            dims_targeted.append(primary_dim)
        # one block-spec per competence, climbing the ladder by index
        level, intent_tpl = _LADDER[len(section_specs) % len(_LADDER)]
        spec_n += 1
        est = 10
        bs = BlockSpec(
            suggested_id=f"{comp.id.split('.')[-1].lower()}.b{spec_n}",
            kind="open_response",
            cognitive_level=level,
            dimension=primary_dim,
            serves_competence_id=comp.id,
            est_minutes=est,
            intent=f"{intent_tpl} (Bezug: {comp.kompetenzbereich})",
        )
        section_specs.append(
            SectionSpec(
                id=f"sec.{spec_n}",
                title=comp.kompetenzbereich,
                throughline=comp.text.strip(),
                block_specs=[bs],
            )
        )
        threads.append(f"{comp.id}: {comp.text.strip()[:70]}…")
        spent += est

    if anchor_mode != AnchorMode.COMPETENCE:
        # ÜT/Horizont are not failed competence resolutions. They get a useful,
        # domain-shaped skeleton without fabricating `serves` ids; dimensions still
        # come from the real subject model and remain structurally verified.
        dimensions = [d.id for d in (_model.dimensions if _model else [])] or [default_dim]
        dims_targeted = dimensions[:2]
        generic = []
        for i, (level, intent) in enumerate((_LADDER[0], _LADDER[1], _LADDER[3]), 1):
            generic.append(BlockSpec(
                suggested_id=f"anchor.b{i}", kind="open_response",
                cognitive_level=level, dimension=dims_targeted[(i - 1) % len(dims_targeted)],
                serves_competence_id=None, est_minutes=12,
                intent=f"{intent}; strikt im Thema „{topic}“, ohne Kompetenzbehauptung",
            ))
        label = (f"ÜT {anchor_uet}" if anchor_mode == AnchorMode.UET else "Horizont")
        section_specs = [SectionSpec(
            id="sec.anchor", title=topic, throughline=f"{label}: {topic}", block_specs=generic,
        )]
        threads = [f"{label}: ehrliche Verankerung ohne erfundene Kompetenzzuordnung"]
        spent = sum(b.est_minutes for b in generic)

    depth_target = DepthTarget(
        min_at_or_above={"level": "analyze", "count": 2 if anchor_mode == AnchorMode.COMPETENCE else 1},
        require_resource_independent_minutes=max(1, int(0.6 * budget)),
        dimensions_required=dims_targeted,
    )
    kernfrage = f"Was sollte man über '{topic}' wirklich verstehen?"
    notes = list(resolution.notes)
    if not comps and anchor_mode == AnchorMode.COMPETENCE:
        notes.append("Keine Kompetenzen aufgelöst — Plan ist leer (Demo-Grenze).")
    elif anchor_mode == AnchorMode.UET:
        notes.append(f"Primär über ÜT {anchor_uet} verankert; Block-Specs tragen kein `serves`.")
    elif anchor_mode == AnchorMode.HORIZONT:
        notes.append("Horizont: freiwillige Vertiefung; Block-Specs tragen kein `serves`.")

    return WorksheetPlan(
        subject=resolution.subject,
        klasse=resolution.klasse,
        topic=topic,
        anchor_mode=anchor_mode,
        anchor_uet=anchor_uet,
        kernfrage=kernfrage,
        competence_ids=[c.id for c in comps],
        dimensions_targeted=dims_targeted,
        threads=threads,
        depth_target=depth_target,
        section_specs=section_specs,
        minutes_budget=budget,
        notes=notes,
    )
