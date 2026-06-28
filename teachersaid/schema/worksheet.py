"""The renderer-independent content object (schema §5/§6) + request/resolution.

`WorksheetContent` exists BEFORE any document; renderers are pure projections of
it. `nachweis`/`depth_profile` are optional here and populated by assemble(); they
are never authored by the LLM (see generation_views).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .assets import Asset
from .blocks import Block
from .competence import SubjectCompetenceModel, SubjectCompetenceModelRef
from .derived import DepthProfile, Nachweis
from .richtext import RichText
from .verification import ThreadRack


class FassungRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kurztitel: str
    bgbl: str
    doknr: str
    valid_from: str
    valid_to: str


class TeacherOverview(BaseModel):
    """The teacher-facing 'rough guide' for a section — never shown to students.

    Authored (or LLM-generated), not derived. `throughline` is the Roter Faden;
    `talking_points` are discussion anchors / questions to pose; `extensions` are
    going-further ideas. `differentiation`/`timing_notes` are optional logistics.
    """
    model_config = ConfigDict(extra="forbid")
    throughline: str | None = None
    talking_points: list[str] = Field(default_factory=list)
    extensions: list[str] = Field(default_factory=list)
    differentiation: str | None = None
    timing_notes: str | None = None


class Baustein(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    teacher_overview: TeacherOverview = Field(default_factory=TeacherOverview)
    blocks: list[Block] = Field(default_factory=list)


class WorksheetMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    subtitle: str | None = None
    subject: str
    stufe: str
    klasse: int
    kernfrage: RichText | None = None
    fassung: FassungRef
    lehrplan_label: str
    content_language: str = "de"  # v0.4 A5
    # v0.4 B5: cross-curricular worksheets cite >1 subject model (primary first).
    subject_models: list[SubjectCompetenceModelRef] = Field(default_factory=list)


class WorksheetContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meta: WorksheetMeta
    subject_model: SubjectCompetenceModel  # pins dimensions & kinds
    intro: list[Block] = Field(default_factory=list)
    sections: list[Baustein] = Field(default_factory=list)
    assets: list[Asset] = Field(default_factory=list)
    nachweis: Nachweis | None = None  # DERIVED at assemble
    depth_profile: DepthProfile | None = None  # DERIVED at assemble
    rack: ThreadRack | None = None

    def iter_blocks(self):
        """All blocks across intro + sections, in document order."""
        yield from self.intro
        for section in self.sections:
            yield from section.blocks


# --- request / resolution (carried from v0.2) --------------------------------
class BundleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str
    klasse: int
    stufe: str = "Unterstufe"
    schulform: str | None = None
    topic_raw: str
    envelope: str = "doppelstunde"  # einzelstunde | doppelstunde | block | custom
    options: dict = Field(default_factory=dict)


class ResolvedCompetence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    kompetenzbereich: str
    klasse: int
    text: str  # verbatim
    source_ref: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    uebergreifende_themen: list[int] = Field(default_factory=list)
    # Oberstufe (Sek II) is semesterised into Kompetenzmodule; these stay None for the
    # Unterstufe. `kind` distinguishes the grade-independent Kompetenzmodell competences
    # ("descriptor") from the per-semester Inhaltsbereiche ("lehrstoff").
    semester: list[int] | None = None
    kompetenzmodul: int | None = None
    kind: str | None = None


class LehrplanResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fassung: FassungRef
    subject: str
    klasse: int
    matched_kompetenzbereiche: list[str] = Field(default_factory=list)
    grade_check: bool = False  # the trust feature
    competences: list[ResolvedCompetence] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)  # honest gaps live here


class Bundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request: BundleRequest
    resolution: LehrplanResolution
    content: WorksheetContent
    generated_at: str
