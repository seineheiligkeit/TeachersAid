"""Typed profile + derived evidence for the parametric Tiefenregler (P1 + P2).

The profile is a teacher request.  The lint report is computed from the same seeded
parametric master and records whether every enabled control has a measurable effect.
The controls are only those that can be derived without authored twins: scope,
alternative computed solution paths, code-generated figures, misconception-generated
multiple choice (P1), and the Gerüst scaffold (P2 — a leak-guarded worked first step,
misconception-fed hints, and curated Formulierungshilfen, all over the SAME seeded master).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Umfang(StrEnum):
    KOMPAKT = "kompakt"
    STANDARD = "standard"
    ERWEITERT = "erweitert"


class Tiefe(StrEnum):
    UEBEN = "ueben"
    STRATEGIEN_VERGLEICHEN = "strategien_vergleichen"


class Abstraktion(StrEnum):
    ANSCHAULICH = "anschaulich"
    FORMAL = "formal"


class Offenheit(StrEnum):
    GESCHLOSSEN = "geschlossen"
    OFFEN = "offen"


class Geruest(StrEnum):
    """P2 Gerüst (scaffold) fader — two endpoints only.

    ``ohne`` is the bare master; ``gestuetzt`` projects the SAME seeded instances plus a
    student-facing scaffold DERIVED from computed/curated data (a leak-guarded worked first
    step from ``solution_steps``, a misconception warning where the recipe carries ``MCSpec``,
    and curated Formulierungshilfen for prose response surfaces).  No middle ``geführt`` label
    is admitted until its own computed response scaffold exists (tiefenregler-design §5)."""
    OHNE = "ohne"
    GESTUETZT = "gestuetzt"


class ParametricMixerProfile(BaseModel):
    """P1 + P2 faders for one parametric master.

    ``None`` means that the corresponding control is not applied.  This matters because
    capabilities are template-specific: a sheet without a computed figure must not grow a
    decorative abstraction knob, and a recipe without misconception data cannot promise MC.
    Umfang is universal and therefore always has a value.
    """

    model_config = ConfigDict(extra="forbid")
    umfang: Umfang = Umfang.STANDARD
    tiefe: Tiefe | None = None
    abstraktion: Abstraktion | None = None
    offenheit: Offenheit | None = None
    geruest: Geruest | None = None


class MixerMetricSnapshot(BaseModel):
    """Small, stable measurement surface used by Regler-Lint."""

    model_config = ConfigDict(extra="forbid")
    task_count: int = 0
    minutes_total: int = 0
    afb_mix: dict[str, int] = Field(default_factory=dict)
    figure_tasks: int = 0
    multiple_choice_tasks: int = 0
    open_response_tasks: int = 0
    scaffolded_tasks: int = 0          # tasks carrying any Gerüst scaffold element (P2)
    scaffold_elements: int = 0         # total scaffold elements across all tasks (P2)
    c4_mean: float | None = None
    coverage_ids: list[str] = Field(default_factory=list)


class FaderMovement(BaseModel):
    """Evidence for the two endpoints of one enabled fader."""

    model_config = ConfigDict(extra="forbid")
    fader: str
    low_label: str
    high_label: str
    metric: str
    low_value: float
    high_value: float
    moved: bool
    coverage_intact: bool


class MixerLintReport(BaseModel):
    """Derived Regler-Lint (P1 controls + the P2 Gerüst endpoint movement, one report);
    WSTF/text evidence joins this same model in P3 — never a parallel lint result."""

    model_config = ConfigDict(extra="forbid")
    passed: bool
    output: MixerMetricSnapshot
    movements: list[FaderMovement] = Field(default_factory=list)
