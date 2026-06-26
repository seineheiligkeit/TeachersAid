"""Lernarrangement (schema v0.5) — a composite sibling that *contains* worksheets.

The relation is **has-a**: each role's material IS a `WorksheetContent`, so the
worksheet stays the modeled primitive and a plain worksheet is just the n=1 case
(one role, one phase, no interaction). We don't tax the 90% case with roles/phases.

The payoff is `competence_anchors`: the **oral / social / enactive** competences a
printable worksheet structurally can't reach (a debate's *analysieren von
Interessenskonflikten*, GWB's *Handlungskompetenz*) — served by the interaction,
the debrief, or the shared product, not by any single sheet. `nachweis` /
`depth_profile` are DERIVED (pipeline/arrange.py), never authored — exactly as for
a worksheet. Rendering reuses the worksheet path entirely (no second renderer):
renderArrangement = renderTeacherOrchestration + roles.map(renderStudentSheet).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .blocks import Block, RubricCriterion
from .competence import DimensionRef
from .derived import DepthProfile, Nachweis
from .richtext import RichText
from .worksheet import FassungRef, WorksheetContent

# the formats we name explicitly; the set is open (plain str also accepted)
ARRANGEMENT_FORMATS = (
    "role_debate", "mystery", "jigsaw", "simulation_game", "stations",
)
GROUPINGS = ("individual", "role_group", "home_group", "plenary")
# how an arrangement-level competence is served (besides "role:<id>")
SERVED_BY = ("interaction", "debrief", "shared_product")


class ArrangementRole(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    share: str | int = "all"            # "all" | n learners | "fraction"
    private: bool = False               # asymmetric info (jigsaw / mystery)
    material: WorksheetContent          # the role's sheet IS a worksheet


class ArrangementPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    grouping: str                       # GROUPINGS
    minutes: int
    what_happens: RichText


class SharedProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: RichText
    rubric: list[RubricCriterion] = Field(default_factory=list)


class CompetenceAnchor(BaseModel):
    """An arrangement-level competence reached by the interaction / debrief /
    shared product / a role — NOT by a single printable task."""
    model_config = ConfigDict(extra="forbid")
    competence_id: str
    dimension: DimensionRef             # dimension code into the subject model
    served_by: str                      # interaction | debrief | shared_product | role:<id>


class ArrangementMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    subtitle: str | None = None
    subject: str
    stufe: str = "Unterstufe"
    klasse: int
    kernfrage: RichText | None = None
    fassung: FassungRef
    format: str                         # ARRANGEMENT_FORMATS (open)
    lehrplan_label: str = ""


class Lernarrangement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meta: ArrangementMeta
    common_material: list[Block] = Field(default_factory=list)  # shared briefing
    roles: list[ArrangementRole] = Field(default_factory=list)
    phases: list[ArrangementPhase] = Field(default_factory=list)
    shared_product: SharedProduct | None = None
    debrief: list[Block] = Field(default_factory=list)          # social/oral lands here
    competence_anchors: list[CompetenceAnchor] = Field(default_factory=list)
    nachweis: Nachweis | None = None            # DERIVED (⋃ role Nachweise + anchors)
    depth_profile: DepthProfile | None = None   # DERIVED (aggregate over role tasks)

    def total_minutes(self) -> int:
        return sum(p.minutes for p in self.phases)
