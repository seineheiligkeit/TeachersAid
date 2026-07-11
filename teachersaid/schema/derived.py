"""DERIVED + planning types (schema §5).

`Nachweis` and `DepthProfile` are COMPUTED by pipeline/derive.py — never authored
by hand or by the LLM. `DepthTarget` is an INPUT to planning (set the bar up front).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .enums import AnchorMode


class DepthTarget(BaseModel):  # an INPUT to planning
    model_config = ConfigDict(extra="forbid")
    min_at_or_above: dict | None = None  # {"level": "analyze", "count": 2}
    require_resource_independent_minutes: int | None = None
    dimensions_required: list[str] = Field(default_factory=list)


class DepthProfile(BaseModel):  # DERIVED over all TaskBlocks
    model_config = ConfigDict(extra="forbid")
    by_level: dict[str, int] = Field(default_factory=dict)
    by_dimension: dict[str, int] = Field(default_factory=dict)
    by_difficulty: dict[str, int] = Field(default_factory=dict)  # Anforderungsband 1/2/3 (3d)
    minutes_total: int = 0
    minutes_resource_independent: int = 0


class CompetenceCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    competence_id: str
    exercised_by: list[str] = Field(default_factory=list)  # block ids
    prerequisite_by: list[str] = Field(default_factory=list)
    covered: bool = False


class Nachweis(BaseModel):  # DERIVED — deriveNachweis(content)
    model_config = ConfigDict(extra="forbid")
    fassung: dict
    anchor_mode: AnchorMode = AnchorMode.COMPETENCE
    anchor_label: str = "Lehrplan-Kompetenzen"
    statement: str = ""
    competence_coverage: list[CompetenceCoverage] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)  # competences with zero exercise
    zentrale_konzepte: list[str] = Field(default_factory=list)
    uebergreifende_themen: list[int] = Field(default_factory=list)
