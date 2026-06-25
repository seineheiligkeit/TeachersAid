"""Subject competence model (schema §2, v0.4 A1/A2).

The competence axis is subject-parameterized: the *slot* is universal, its
*values* are supplied per subject. Modality lives at the dimension level (v0.4
A2) so `printable_coverage` becomes computable before generating anything.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .enums import Modality

# A DimensionRef is an id into the worksheet's SubjectCompetenceModel.dimensions.
DimensionRef = str


class CompetenceDimension(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str
    note: str | None = None
    # v0.4 A2: default printable (a v0.3 worksheet is all-printable).
    modality: Modality = Modality.PRINTABLE


class SubjectCompetenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str
    stufe: str
    dimensions: list[CompetenceDimension]
    # only where the Lehrplan has an explicit content axis (Mathematik)
    content_areas: list[CompetenceDimension] = Field(default_factory=list)
    task_kind_extensions: list[str] = Field(default_factory=list)

    def dimension_ids(self) -> set[str]:
        return {d.id for d in self.dimensions}


class SubjectCompetenceModelRef(BaseModel):  # v0.4 A1
    model_config = ConfigDict(extra="forbid")
    ref: str
    label_overrides: dict[str, str] = Field(default_factory=dict)


def printable_coverage(model: SubjectCompetenceModel) -> float:
    """v0.4 A2 derived metric: fraction of dimensions a worksheet can address."""
    if not model.dimensions:
        return 0.0
    printable = sum(1 for d in model.dimensions if d.modality == Modality.PRINTABLE)
    return printable / len(model.dimensions)
