"""Curated historical image sources and their Bildquellenkritik ladder.

``ImageSource`` is the visual sibling of :class:`AnnotatedText`: the pixels are
selected from a rights-cleared source, while every task answer is selected from
a curated annotation.  Rights are deliberately split in two.  A public-domain
work does not by itself clear the photograph/scan that reproduces it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .blocks import Serves
from .richtext import RichText

ImageAnnotationKind = Literal["beschreibung", "analyse", "interpretation"]
WorkRightsBasis = Literal[
    "public_domain_pma", "public_domain_mark", "cc0", "cc_by", "cc_by_sa", "cleared"
]
ReproductionRightsBasis = Literal[
    "public_domain_mark", "cc0", "cc_by", "cc_by_sa", "cleared"
]


class WorkRights(BaseModel):
    """Copyright status of the depicted work, independent of its reproduction."""

    model_config = ConfigDict(extra="forbid")
    basis: WorkRightsBasis
    creator: str
    creator_death_year: int | None = None
    licence: str | None = None
    evidence: str

    def is_clear(self, today_year: int) -> tuple[bool, list[str]]:
        if not self.evidence.strip():
            return False, ["work: missing rights evidence"]
        if self.basis in {"cc0", "cc_by", "cc_by_sa", "cleared"}:
            return True, []
        if self.basis == "public_domain_mark":
            if not self.licence or "public domain mark" not in self.licence.casefold():
                return False, ["work: public_domain_mark without a recorded Public Domain Mark"]
            return True, []
        if self.creator_death_year is None:
            return False, ["work: public_domain_pma without creator_death_year"]
        if today_year - self.creator_death_year < 70:
            return False, [
                f"work: creator died {self.creator_death_year}; not yet 70 Jahre p.m.a."
            ]
        return True, []


class ReproductionRights(BaseModel):
    """Rights of the exact digital file (scan/photograph), not of the work."""

    model_config = ConfigDict(extra="forbid")
    basis: ReproductionRightsBasis
    licence: str
    licence_url: str | None = None
    attribution_required: bool
    evidence: str

    def is_clear(self) -> tuple[bool, list[str]]:
        if not self.evidence.strip():
            return False, ["reproduction: missing rights evidence"]
        folded = self.licence.casefold()
        if self.basis == "public_domain_mark":
            if "public domain mark" not in folded:
                return False, [
                    "reproduction: public_domain_mark without a recorded Public Domain Mark"
                ]
        elif self.basis == "cc0":
            if "cc0" not in folded and "creative commons zero" not in folded:
                return False, ["reproduction: cc0 basis but licence is not recorded verbatim"]
        elif self.basis in {"cc_by", "cc_by_sa"}:
            if "cc by" not in folded and "creative commons attribution" not in folded:
                return False, ["reproduction: CC basis but licence is not recorded verbatim"]
            if self.basis == "cc_by_sa" and "sharealike" not in folded and "by-sa" not in folded:
                return False, ["reproduction: cc_by_sa basis without ShareAlike in licence"]
            if not self.attribution_required:
                return False, ["reproduction: CC BY must require attribution"]
        return True, []


class ImageSourceRef(BaseModel):
    """Machine-auditable provenance for one exact image file."""

    model_config = ConfigDict(extra="forbid")
    creator: str
    title: str
    work_date: str | None = None
    repository: str
    description_url: str
    file_url: str
    retrieved: str
    attribution: str
    mime: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    sha1: str = Field(min_length=40, max_length=40, pattern=r"^[0-9a-f]{40}$")
    work_rights: WorkRights
    reproduction_rights: ReproductionRights
    # The exact Commons ``extmetadata`` values.  Storing these verbatim makes a
    # future audit possible even if the description page later changes.
    rights_metadata: dict[str, str | bool | None] = Field(default_factory=dict)

    def is_clear(self, today_year: int) -> tuple[bool, list[str]]:
        work_ok, work_reasons = self.work_rights.is_clear(today_year)
        repro_ok, repro_reasons = self.reproduction_rights.is_clear()
        return work_ok and repro_ok, work_reasons + repro_reasons


class ImageAnnotation(BaseModel):
    """One vetted rung of Beschreibung -> Analyse -> Interpretation."""

    model_config = ConfigDict(extra="forbid")
    kind: ImageAnnotationKind
    question: str
    answer: RichText
    focus: str | None = None
    cognitive_level: str
    dimensions: list[str] = Field(default_factory=lambda: ["HME"])


class ImageSource(BaseModel):
    """A rights-cleared image plus the curated ladder that licenses its tasks."""

    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    subject: str = "Geschichte und politische Bildung"
    klasse: int
    image_asset_id: str
    source: ImageSourceRef
    annotations: list[ImageAnnotation]
    serves: list[Serves] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    related_sachverhalt_id: str | None = None
    related_text_id: str | None = None

    @model_validator(mode="after")
    def _complete_ordered_ladder(self) -> "ImageSource":
        order = {"beschreibung": 0, "analyse": 1, "interpretation": 2}
        kinds = [a.kind for a in self.annotations]
        if set(kinds) != set(order):
            raise ValueError(
                "ImageSource needs all three annotation rungs: "
                "beschreibung, analyse, interpretation"
            )
        if [order[k] for k in kinds] != sorted(order[k] for k in kinds):
            raise ValueError("ImageSource annotations must follow Beschreibung -> Analyse -> Interpretation")
        return self
