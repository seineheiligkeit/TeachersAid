"""The Sachverhalt content / exposition layer — curated structured Sachwissen.

The third grounding/provenance sibling (next to the grounded-facts data layer and the
annotated texts; design: `Documents/sachverhalt-content-layer-design.md`). Where the data
layer tracks fact-provenance for NUMBERS and `AnnotatedText` tracks rights-provenance for
whole TEXTS, a `Sachverhalt` is a curated module of structured *Sachwissen* about one
topic — the didactic content layer the engine was missing (measured: it is task-generative
and prose-thin everywhere, while the Lehrplan's Sachkompetenz pillar demands the opposite).

The honest reconciliation with *select, never author* is a split (see `invariants.md` §3):

* **structured facts are facts** — a date, an actor's role, a cause→effect link, a Begriff.
  These are curatable and sourced exactly like the data layer's numbers (copyright protects
  expression, not facts) and fact-checked at the HITL gate.
* **the connective Darstellung is authored-then-vetted** — but only ever a *projection over
  the frozen fact-set* (the same shape as the rendering layer), guarded by a deterministic
  entity-lint (`pipeline/sachverhalt_lint.py`) so the authoring itself is correct-by-
  construction. *"Select the facts, author the expression."*

One `Sachverhalt` → three projections (`pipeline/sachverhalt.py`): a Darstellung learn-text,
DERIVED figures (timeline ← `timeline`, Wirkungsgefüge ← `causes`), and several
correct-by-construction Sachkompetenz tasks (order the real events, match cause→effect,
Begriff-Zuordnung) — then the usual `assemble`/`verify`/`render` path, so nothing downstream
changes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .provenance import BlockProvenance, ProvenanceSource
from .richtext import RichText

# the role a causal link plays in the Wirkungsgefüge (drives ordering/colour later)
CausalKind = Literal["voraussetzung", "ursache", "verlauf", "folge", "wirkung"]


class TimelinePhase(BaseModel):
    """One curated Periodisierung band on the Zeitband (institutional phases under the axis —
    "EGKS" / "EWG / EG" / "Europäische Union"). `from_`/`to` are numeric years (JSON key `from`);
    the `label` is the phase name. Additive (Zeitband redesign, 18 Jul 2026): old JSON has no
    `timeline_phases`, so nothing loads differently."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    from_: int = Field(alias="from")
    to: int
    label: str


class HistEvent(BaseModel):
    """A dated event → the timeline figure + chronology tasks. `at` is numeric where it
    can be (it drives the timeline axis); a string allows "um 1500" / an ISO date.

    Zeitband redesign (18 Jul 2026, all additive — old JSON loads unchanged): `to` makes the
    event a Zeitraum rendered as a bar `at`..`to` (a string end year is carried through for
    display but does not place on the axis); `zaesur` marks a turning point drawn as a quiet
    dashed full-height rule; `strand` assigns the event to one of the module's two
    `timeline_strands` (Synchronoptik lanes) — validated at the Sachverhalt ingest gate
    (`pipeline/sachverhalt_lint.py`), never a silent default."""
    model_config = ConfigDict(extra="forbid")
    at: int | str
    label: str
    text: RichText = ""              # one-line description (teacher/context, not the axis)
    to: int | str | None = None      # Zeitraum end → a bar (a numeric end places on the axis)
    zaesur: bool = False             # a turning point → a dashed full-height rule
    strand: str | None = None        # one of the module's timeline_strands (Synchronoptik lane)
    source_ref: str | None = None    # optional key into sources[]
    entity_id: str | None = None     # optional link into the entity registry (grounding/entities)
    # — additive, backward-compatible: existing JSON without it loads unchanged. The registry is
    # the single source of truth (`grounding/entities.py`); `pipeline/entity_lint.py` checks that a
    # linked event's `at` does not contradict the registry's date range (Wave C2).


class Actor(BaseModel):
    """Who, and their role in the Sachverhalt (Akteur:innen → structure_overview tasks)."""
    model_config = ConfigDict(extra="forbid")
    name: str
    role: RichText
    source_ref: str | None = None
    entity_id: str | None = None     # optional link into the entity registry (grounding/entities)
    # — additive, backward-compatible (Wave C2): a person/place actor may point at a canonical
    # registry entity so the corpus-global lint can spot conflicting facts and `verwandte_module`
    # can find every module that shares this entity.


class CausalLink(BaseModel):
    """A cause→effect link → the Wirkungsgefüge figure + cause_effect_match tasks."""
    model_config = ConfigDict(extra="forbid")
    cause: str
    effect: str
    kind: CausalKind = "folge"
    source_ref: str | None = None


class Concept(BaseModel):
    """A Begriff → concept_match tasks (term ↔ definition)."""
    model_config = ConfigDict(extra="forbid")
    term: str
    definition: RichText
    source_ref: str | None = None


class ProcessStep(BaseModel):
    """One step of a PROCESS or CYCLE — the Phase-2 fact-type a content-heavy science needs
    (Biology, e.g. the Blutkreislauf) where History had a dated `timeline`. The authored LIST
    ORDER is the correct sequence (the ordering task's answer is computed from it); for a
    `process_cyclic` Sachverhalt the last step loops back to the first. → a process-flow figure
    (`matplotlib:process_flow`) + a process-ordering task (kind `ordering`)."""
    model_config = ConfigDict(extra="forbid")
    name: str
    text: RichText = ""              # one-line description (teacher/context)
    source_ref: str | None = None


class Region(BaseModel):
    """A spatial unit — the Geography fact-type (the geographic analogue of `HistEvent`/
    `ProcessStep`). The `name` keys into a SOURCED boundary set (`geo_id`) for the choropleth;
    the fill value comes from a CITED dataset (`region_dataset`/`region_series`), never authored.
    The optional `note` is curated (what's notable about this region)."""
    model_config = ConfigDict(extra="forbid")
    name: str
    note: RichText = ""
    source_ref: str | None = None


class DarstellungSection(BaseModel):
    """One section of the authored-then-vetted narrative, grounded in the fact-set.

    `grounded_by` lists the fact keys this paragraph rests on (event label / Begriff /
    actor name) — the checkability audit. `provenance` is normally left None: the
    derivation attaches the module's `role="facts"` sources as an
    `expression_origin="original"` `BlockProvenance`, so the prose-provenance gate
    (`prose_lint`) passes by construction and the curator cannot forget the facts record.
    Set it explicitly only for the rare section that embeds a quote."""
    model_config = ConfigDict(extra="forbid")
    heading: str
    body: RichText
    grounded_by: list[str] = Field(default_factory=list)
    provenance: BlockProvenance | None = None


class Sachverhalt(BaseModel):
    """A curated module of structured Sachwissen about one topic (the in-repo record,
    HITL-reviewed). The substance (`timeline`/`actors`/`causes`/`concepts`/`bedeutung`/
    `gegenwartsbezug`) is *selected/sourced*; the `darstellung` is *authored over the frozen
    fact-set* (entity-lint guarded). The skeleton is generic — only the fact mix shifts by
    subject (Phase 2+ adds Bio/Geo fact-types behind the same container)."""
    model_config = ConfigDict(extra="forbid")
    id: str
    subject: str
    klasse_range: tuple[int, int]
    topic: str
    leitfrage: RichText = ""
    # --- discovery tags (cf. Dataset.subjects/keywords/competences) — NOT facts ---
    kompetenzbereiche: list[str] = Field(default_factory=list)
    competences: list[str] = Field(default_factory=list)   # especially-relevant ids
    keywords: list[str] = Field(default_factory=list)
    # --- authoring policy ---
    sensitive: bool = False          # → conservative authoring + mandatory SME pass (§12-Q1)
    sources: list[ProvenanceSource] = Field(default_factory=list)  # role="facts" mandatory
    # --- the structured substance (facts) ---
    timeline: list[HistEvent] = Field(default_factory=list)
    # Zeitband redesign (18 Jul 2026, additive): the Synchronoptik lane split — when non-empty
    # EXACTLY two curated lane names (`[0]` renders above the axis, `[1]` below), and every dated
    # event must carry a `strand` from this pair (validated at the ingest gate, not silently
    # defaulted). A curated Periodisierung band under the axis (`timeline_phases`).
    timeline_strands: list[str] = Field(default_factory=list)
    timeline_phases: list[TimelinePhase] = Field(default_factory=list)
    actors: list[Actor] = Field(default_factory=list)
    causes: list[CausalLink] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)
    # a process/cycle (Phase 2 — content-heavy sciences): ordered steps, the undated sibling of
    # `timeline`. → a process-flow figure + a process-ordering task. `process_cyclic` loops it.
    process_name: str = ""
    process: list[ProcessStep] = Field(default_factory=list)
    process_cyclic: bool = False
    # a spatial fact set (Phase 2 — Geography): regions of a sourced boundary set, filled by a
    # CITED dataset → a choropleth map + a rank-by-value task. Names match geo_id + the dataset.
    regions: list[Region] = Field(default_factory=list)
    geo_id: str = ""                  # the boundary set in grounding/geo/, e.g. "at_bundeslaender"
    region_dataset: str | None = None  # the cited dataset id for the fill values
    region_series: str | None = None   # the series within it
    region_value_label: str = ""       # the colorbar label, e.g. "Einwohner:innen"
    bedeutung: RichText = ""          # significance / Nachwirkung
    gegenwartsbezug: RichText = ""    # the present-day link (Lehrplan-mandated)
    urteilsfrage: RichText = ""       # optional judgment prompt → a high-band Urteils-task.
    # Multiperspektivität/Kontroversität lives HERE (the Urteils layer), never in the factual
    # Darstellung (§12) — and it gives the worksheet a real Anforderungs-spread.
    # subject Sachkompetenz dimension code (e.g. GPB "HSA"); a fallback when a served
    # competence resolves without its own dimension — see pipeline/sachverhalt.py.
    # (GPB.US.3.* resolve with empty dims, so this is required, not cosmetic.)
    sach_dimension: str | None = None
    urteil_dimension: str | None = None   # the judgment task's dim (e.g. GPB "HOR", BIO "S");
    # falls back to sach_dimension — an Urteils-task is Orientierungs-/Urteils-/Bewertungs-, not Sach-
    urteil_competence: str | None = None  # the competence the Urteils-task serves, where ids encode
    # the strand (e.g. BIO STA.* for S); falls back to the Sachkompetenz pool (fine for GPB's ALL ids).
    actor_label: str = "Akteure"          # the noun for the structure_overview prompt:
    # "Akteure" (history) · "Strukturen"/"Bestandteile" (a Bio Sachverhalt — Herz, Arterien, …)
    # --- the authored-then-vetted narrative, grounded in the above ---
    darstellung: list[DarstellungSection] = Field(default_factory=list)

    def facts_sources(self) -> list[ProvenanceSource]:
        return [s for s in self.sources if s.role == "facts"]

    def default_klasse(self) -> int:
        """The grade a worksheet is built for by default — the lower bound of the range."""
        return self.klasse_range[0]
