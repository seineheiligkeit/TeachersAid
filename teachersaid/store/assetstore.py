"""JSON-file-backed store for the reusable asset library (Phase 4 #4).

The asset-as-reviewed-library for the two classes whose **durable artifact is a
file**: *decorative* (content-free, reusable — svg/code now, diffusion later) and
*sourced* (external + provenance). It runs parallel to the block library:
`AssetStore` mirrors `BlockStore` (one JSON per entry under RUNS_DIR/assets_lib/,
idempotent `upsert` preserving review status, status filters). The file itself
lives under .../files/.

Code-generated *content* assets are NOT here — they stay as `{generator, spec}`
specs on blocks (rebuilt on demand). This store is for the file-backed classes
that the media-policy gate routes to human review (`Documents/schema-roadmap`).
"""

from __future__ import annotations

from datetime import date as Date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..schema.assets import Asset, ImageLintReport
from .base import JsonStore

KLASSES = ("decorative", "depictive", "sourced")


class GenerationRecord(BaseModel):
    """Honest provenance for an agent-time generated file."""
    model_config = ConfigDict(extra="forbid")
    origin: Literal["synthetic"] = "synthetic"
    generator: str = Field(min_length=1)
    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    negative_prompt: str | None = None
    style_prefix: str = Field(min_length=1)
    date: str
    reproducibility_parameters: dict = Field(default_factory=dict)
    replayable: bool = False

    @field_validator("date", mode="before")
    @classmethod
    def _iso_date(cls, value):
        if isinstance(value, Date):
            value = value.isoformat()
        Date.fromisoformat(str(value))
        return str(value)

    @model_validator(mode="after")
    def _honest_replayability(self):
        if "seed" not in self.reproducibility_parameters:
            self.replayable = False
        return self


class LibraryAsset(BaseModel):
    """An asset whose durable artifact is a file, plus library metadata for review
    and reuse (tags). Wraps the schema `Asset` (role/medium/generator/spec/
    provenance/caption) the same way `LibraryBlock` wraps a `Block`."""
    model_config = ConfigDict(extra="forbid")
    id: str
    asset: Asset
    klass: str                          # "decorative" | "depictive" | "sourced"
    tags: list[str] = Field(default_factory=list)  # for reuse/search
    file: str | None = None             # path to the durable artifact (raster/svg/source)
    generation: GenerationRecord | None = None
    preflight: ImageLintReport | None = None
    candidate_set_id: str | None = None
    candidate_index: int | None = None
    status: str = "in_review"           # in_review | approved | rejected
    source: str = "ai"                  # ai | user | curated
    created_at: str = ""
    updated_at: str = ""

    @model_validator(mode="after")
    def _candidate_fields_travel_together(self):
        if (self.candidate_set_id is None) != (self.candidate_index is None):
            raise ValueError("candidate_set_id and candidate_index must be set together")
        if self.candidate_index is not None and self.candidate_index < 1:
            raise ValueError("candidate_index is 1-based")
        return self

    def summary(self) -> dict:
        a = self.asset
        return {
            "id": self.id, "klass": self.klass, "role": a.role,
            "medium": str(a.medium), "generator": a.generator, "tags": self.tags,
            "caption": a.caption, "status": self.status, "source": self.source,
            "has_file": bool(self.file), "updated_at": self.updated_at,
            "lane": a.lane, "intended_claim": a.intended_claim,
            "provenance": a.provenance.model_dump() if a.provenance else None,
            "generation": self.generation.model_dump(mode="json") if self.generation else None,
            "preflight": self.preflight.model_dump() if self.preflight else None,
            "candidate_set_id": self.candidate_set_id,
            "candidate_index": self.candidate_index,
        }


class AssetStore(JsonStore[LibraryAsset]):
    model = LibraryAsset
    subdir = "assets_lib"

    def __init__(self, root: Path | None = None):
        super().__init__(root)
        self.files_dir = self.root / "files"   # the durable artifacts live here
        self.files_dir.mkdir(parents=True, exist_ok=True)

    def upsert(self, rec: LibraryAsset) -> LibraryAsset:
        """Store a record while keeping each candidate set one coherent request."""
        if rec.candidate_set_id:
            for sibling in self.list():
                if sibling.candidate_set_id != rec.candidate_set_id or sibling.id == rec.id:
                    continue
                if sibling.candidate_index == rec.candidate_index:
                    raise ValueError("candidate_index must be unique within a candidate set")
                if (sibling.asset.lane, sibling.asset.intended_claim) != (
                    rec.asset.lane, rec.asset.intended_claim
                ):
                    raise ValueError(
                        "all candidates in a set must share lane and intended_claim")
        return super().upsert(rec)

    def list(self, *, klass: str | None = None, status: str | None = None,
             tag: str | None = None) -> list[LibraryAsset]:
        return self._list(
            where=lambda a: (klass is None or a.klass == klass)
            and (status is None or a.status == status)
            and (tag is None or tag in a.tags),
            sort_key=lambda a: (a.klass, a.asset.role, a.id))

    def approved(self, *, tag: str | None = None) -> list[LibraryAsset]:
        """Approved, reusable assets — the kit the composer/teacher can draw on."""
        return self.list(status="approved", tag=tag)

    def select_candidate(self, asset_id: str) -> LibraryAsset:
        """Approve one best-of-N candidate and reject every sibling."""
        chosen = self.get(asset_id)
        if chosen is None:
            raise KeyError(asset_id)
        if chosen.preflight is not None and not chosen.preflight.passed:
            codes = ", ".join(f.code for f in chosen.preflight.findings
                              if f.severity == "error")
            raise ValueError(f"preflight errors must be resolved before approval: {codes}")
        if not chosen.candidate_set_id:
            return self.set_status(asset_id, "approved")
        for candidate in self.list():
            if candidate.candidate_set_id == chosen.candidate_set_id:
                candidate.status = "approved" if candidate.id == asset_id else "rejected"
                self.save(candidate)
        selected = self.get(asset_id)
        assert selected is not None
        return selected

    def reject_candidate_set(self, asset_id: str) -> LibraryAsset:
        """Reject an entire request in one action (the best-of-N 'none' choice)."""
        anchor = self.get(asset_id)
        if anchor is None:
            raise KeyError(asset_id)
        if not anchor.candidate_set_id:
            return self.set_status(asset_id, "rejected")
        for candidate in self.list():
            if candidate.candidate_set_id == anchor.candidate_set_id:
                candidate.status = "rejected"
                self.save(candidate)
        rejected = self.get(asset_id)
        assert rejected is not None
        return rejected
