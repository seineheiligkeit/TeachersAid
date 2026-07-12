"""Typed profile + derived evidence for the parametric Tiefenregler (P1 + P2 + P3).

The profile is a teacher request.  The lint report is computed from the same seeded
parametric master and records whether every enabled control has a measurable effect.
The controls are those derivable without authored twins — scope, alternative computed
solution paths, code-generated figures, misconception-generated multiple choice (P1), and
the Gerüst scaffold (P2) — plus P3 Textlast, the ONE control that SELECTS between two
CURATED prose fields (the master prompt and its approved simplified twin + glosses); its
movement is measured with the Wiener Sachtextformel (`pipeline/readability`).  Every control
either derives from computed data or selects a curated, SME-vetted field — never freshly
authored at fader time.
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


class Textlast(StrEnum):
    """P3 Textlast (text load) fader — two endpoints only.

    ``voll`` is the unchanged master (full register); ``einfach`` SELECTS the template's
    APPROVED simplified prose twin (``ParametricTask.prompt_simple``, same {slots} → same
    computed values by construction) and, where curated, renders a student-facing
    Wortschatz-Kasten from ``ParametricTask.glossary``.  The fader SELECTS between two curated
    fields; it never rewrites, never simplifies verbatim source text, and never touches a
    factual value.  A template supports Textlast only when it carries an approved twin, whose
    student-facing prompt prose must measurably lower the Wiener Sachtextformel Schulstufe
    (`pipeline/readability`); otherwise the fader HARD-FAILS.  No middle setting is admitted
    until a computed, measurable register between the two curated endpoints exists (§5)."""
    VOLL = "voll"
    EINFACH = "einfach"


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
    textlast: Textlast | None = None


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
    wstf: float | None = None          # Wiener Sachtextformel Schulstufe over the student-facing
    # task prompt prose (P3 Textlast); None when there is too little prose to measure (< the
    # readability MIN_WORDS threshold) or every task is verbatim-exempt
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
    """Derived Regler-Lint (P1 controls + the P2 Gerüst endpoint movement + the P3 Textlast
    WSTF movement, ONE report — never a parallel lint result)."""

    model_config = ConfigDict(extra="forbid")
    passed: bool
    output: MixerMetricSnapshot
    movements: list[FaderMovement] = Field(default_factory=list)
