"""Assets and media policy (schema §6 + v0.4 A3/B3/B4).

Content-bearing visuals are code-generated (correct by construction); decorative
may be diffusion; the boundary is per-subject (MediaPolicy). `intentionally_flawed`
(v0.4 B3) marks an asset that is wrong ON PURPOSE — the pipeline must NOT fix it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .enums import Medium


class AssetProvenance(BaseModel):  # v0.4 B4
    model_config = ConfigDict(extra="forbid")
    source: str
    rights: Literal[
        "public_domain", "licensed", "cleared", "original", "unverified"
    ]
    note: str | None = None


class IntentionallyFlawed(BaseModel):  # v0.4 B3
    model_config = ConfigDict(extra="forbid")
    what: str  # what is wrong, and why it must stay wrong


class Asset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    role: str  # e.g. "figure", "dataset"
    medium: Medium = Medium.VISUAL  # v0.4 B4
    generator: str | None = None  # e.g. "matplotlib:em_spectrum"
    spec: dict = Field(default_factory=dict)  # generator-specific parameters
    correctness_surface: str | None = None  # what makes it correct-by-construction
    misleading_in_isolation: bool = False  # correct-but-risky-out-of-context
    intentionally_flawed: IntentionallyFlawed | None = None  # wrong on purpose
    machine_generatable: bool = True  # music audio etc. -> False
    provenance: AssetProvenance | None = None
    caption: str | None = None


class MediaPolicyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    medium: Medium
    diffusion_ok: list[str] = Field(default_factory=list)
    must_be_code: list[str] = Field(default_factory=list)
    must_be_sourced: list[str] = Field(default_factory=list)
    machine_generatable: bool = True


class MediaPolicy(BaseModel):  # v0.4 A3 — generalises SubjectVisualPolicy
    model_config = ConfigDict(extra="forbid")
    subject: str
    per_medium: list[MediaPolicyEntry] = Field(default_factory=list)
