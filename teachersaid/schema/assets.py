"""Assets and media policy (schema §6 + v0.4 A3/B3/B4).

Content-bearing visuals are code-generated (correct by construction); decorative
may be diffusion; the boundary is per-subject (MediaPolicy). `intentionally_flawed`
(v0.4 B3) marks an asset that is wrong ON PURPOSE — the pipeline must NOT fix it.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from .datasets import DataRef
from .enums import Medium


# The visual claim lane is orthogonal to how a file was produced.  ``None`` is
# retained on Asset for backwards compatibility; media_policy deterministically
# infers the lane from the role for older corpus records.
AssetLane: TypeAlias = Literal["decorative", "depictive", "content"]


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


class ImageLintFinding(BaseModel):
    """One deterministic raster pre-review finding."""
    model_config = ConfigDict(extra="forbid")
    code: str
    severity: Literal["warning", "error"] = "warning"
    message: str


class ImageLintReport(BaseModel):
    """Stored pre-review evidence; factual image review remains human."""
    model_config = ConfigDict(extra="forbid")
    width: int
    height: int
    mode: str
    grayscale_span: int
    grayscale_stddev: float
    findings: list[ImageLintFinding] = Field(default_factory=list)
    text_check: str = "manual_required"

    @property
    def passed(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)


class Asset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    role: str  # e.g. "figure", "dataset"
    lane: AssetLane | None = None
    intended_claim: str | None = None  # required for depictive assets
    medium: Medium = Medium.VISUAL  # v0.4 B4
    generator: str | None = None  # e.g. "matplotlib:em_spectrum"
    spec: dict = Field(default_factory=dict)  # generator-specific parameters
    correctness_surface: str | None = None  # what makes it correct-by-construction
    misleading_in_isolation: bool = False  # correct-but-risky-out-of-context
    intentionally_flawed: IntentionallyFlawed | None = None  # wrong on purpose
    machine_generatable: bool = True  # music audio etc. -> False
    provenance: AssetProvenance | None = None  # FILE provenance (sourced photos/art)
    # Grounded-facts label: a content figure's data is exactly one of —
    #   data_source set  → (b) vetted-sourced + cited (real numbers from a dataset), or
    #   illustrative=True → (c) explicitly schematic/example (clearly not a real figure).
    # A real-looking, unlabelled figure is a verify finding (see pipeline/figure_lint).
    data_source: DataRef | None = None
    illustrative: bool = False
    caption: str | None = None


class MediaPolicyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    medium: Medium
    diffusion_ok: list[str] = Field(default_factory=list)
    depictive_ok: list[str] = Field(default_factory=list)
    must_be_code: list[str] = Field(default_factory=list)
    must_be_sourced: list[str] = Field(default_factory=list)
    machine_generatable: bool = True


class MediaPolicy(BaseModel):  # v0.4 A3 — generalises SubjectVisualPolicy
    model_config = ConfigDict(extra="forbid")
    subject: str
    per_medium: list[MediaPolicyEntry] = Field(default_factory=list)
