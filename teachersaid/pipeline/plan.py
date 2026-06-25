"""Plan (mostly deterministic) — schema §7 step 2.

Turns a resolution + time envelope into a block-spec skeleton that targets a
DepthTarget ladder (predict → reason-with-data → evaluate-claims → transfer).
The plan IS the idea-stage review artifact: threads + specs + target, no prose
yet, so a human can approve direction before any generation spends tokens.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..schema.derived import DepthTarget
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
    serves_competence_id: str
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
    kernfrage: str
    competence_ids: list[str] = Field(default_factory=list)
    dimensions_targeted: list[str] = Field(default_factory=list)
    threads: list[str] = Field(default_factory=list)  # creative idea seeds
    depth_target: DepthTarget = Field(default_factory=DepthTarget)
    section_specs: list[SectionSpec] = Field(default_factory=list)
    minutes_budget: int = 100
    notes: list[str] = Field(default_factory=list)


def plan(
    resolution: LehrplanResolution, envelope: str = "doppelstunde", *, topic: str = ""
) -> WorksheetPlan:
    budget = _ENVELOPE_MINUTES.get(envelope, 100)
    comps = resolution.competences
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
        primary_dim = comp.dimensions[0] if comp.dimensions else "W"
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

    depth_target = DepthTarget(
        min_at_or_above={"level": "analyze", "count": 2},
        require_resource_independent_minutes=max(1, int(0.6 * budget)),
        dimensions_required=dims_targeted,
    )
    kernfrage = f"Was sollte man über '{topic}' wirklich verstehen?"
    notes = list(resolution.notes)
    if not comps:
        notes.append("Keine Kompetenzen aufgelöst — Plan ist leer (Demo-Grenze).")

    return WorksheetPlan(
        subject=resolution.subject,
        klasse=resolution.klasse,
        topic=topic,
        kernfrage=kernfrage,
        competence_ids=[c.id for c in comps],
        dimensions_targeted=dims_targeted,
        threads=threads,
        depth_target=depth_target,
        section_specs=section_specs,
        minutes_budget=budget,
        notes=notes,
    )
