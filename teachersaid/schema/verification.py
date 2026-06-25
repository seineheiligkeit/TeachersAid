"""Carried forward from v0.2 (signatures): verification + thread/rack layer."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .competence import DimensionRef
from .richtext import RichText


class VerificationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str
    confidence: Literal["low", "medium", "high"] = "medium"
    status: Literal["unverified", "verified", "refuted"] = "unverified"
    source: str | None = None


class Thread(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    kompetenzbereich: str
    title: str
    hook: RichText | None = None
    anchors: list[str] = Field(default_factory=list)
    lens: str | None = None
    depth_band: str | None = None
    dimensions: list[DimensionRef] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    watch_out: str | None = None
    verification: list[VerificationItem] = Field(default_factory=list)
    cross_links: list[str] = Field(default_factory=list)


class CoveragePerCompetence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    competence_id: str
    threads: list[str] = Field(default_factory=list)


class CoverageReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    per_competence: list[CoveragePerCompetence] = Field(default_factory=list)
    thin_spots: list[str] = Field(default_factory=list)


class ThreadRack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kompetenzbereich: str
    fassung: dict
    threads: list[Thread] = Field(default_factory=list)
    coverage: CoverageReport | None = None
