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


# --- P4: German display labels for the Mischpult dashboard -------------------------------
# The controls are product-facing German (Austrian school register).  These map the profile
# field names + the endpoint enum VALUES to the labels the teacher sees.  They are pure
# presentation (UI copy); the accept/reject LOGIC is never encoded here — it is DISCOVERED by
# asking the mixer's own rejection paths (`pipeline/mixer.discover_capabilities`).

FADER_LABELS: dict[str, str] = {
    "umfang": "Umfang",
    "tiefe": "Tiefe",
    "abstraktion": "Abstraktion",
    "offenheit": "Offenheit",
    "geruest": "Gerüst",
    "textlast": "Textlast",
}

# endpoint enum value → German label (mostly identity; two carry an umlaut / a phrase)
ENDPOINT_LABELS: dict[str, str] = {
    "kompakt": "kompakt", "standard": "standard", "erweitert": "erweitert",
    "ueben": "üben", "strategien_vergleichen": "Strategien vergleichen",
    "anschaulich": "anschaulich", "formal": "formal",
    "geschlossen": "geschlossen", "offen": "offen",
    "ohne": "ohne", "gestuetzt": "gestützt",
    "voll": "voll", "einfach": "einfach",
}


class FaderOption(BaseModel):
    """One selectable endpoint of a fader: the enum value sent in the profile + its label."""

    model_config = ConfigDict(extra="forbid")
    value: str      # the enum value the dashboard puts into `mixer_profile`
    label: str      # the German display label


class FaderCapability(BaseModel):
    """Discovered capability of ONE fader for ONE parametric template (P4).

    ``supported`` is DERIVED by asking the mixer's own rejection code (never a hand table).
    ``optional`` distinguishes the five capability faders (which may be left unset → ``None``,
    the neutral default) from the universal Umfang (always sent, defaults to ``standard``).
    ``reason`` is a curated German explanation shown only when the fader is unsupported —
    presentation copy, not the decision; the decision is ``supported``.
    """

    model_config = ConfigDict(extra="forbid")
    fader: str                              # the ParametricMixerProfile field name
    label: str                              # German control label (FADER_LABELS)
    supported: bool
    optional: bool                          # may be left neutral (None); False only for umfang
    options: list[FaderOption] = Field(default_factory=list)  # selectable endpoints
    default: str | None = None              # neutral default: "standard" (umfang) or None
    reason: str | None = None               # German "warum nicht" — unsupported only


class TemplateCapabilities(BaseModel):
    """The full Mischpult capability report for one parametric template (P4 discovery)."""

    model_config = ConfigDict(extra="forbid")
    template_id: str
    subject: str
    klasse: int
    title: str
    capabilities: list[FaderCapability] = Field(default_factory=list)


# --- Lesson-purpose presets (curated bundles over the ONE typed profile) ------------------
# A preset is a lesson PURPOSE, not a student level (roadmap steer; tiefenregler-design §9).  It
# is a curated, SME-vetted PARTIAL `ParametricMixerProfile`: it pins Umfang plus only the
# OPTIONAL faders whose ACTIVE endpoint serves that purpose; every other fader stays neutral
# (None).  The dashboard applies a preset by SETTING the fader selects and then rebuilds the SAME
# typed profile from them — so a preset NEVER bypasses capability discovery: a fader the picked
# template does not support is simply not set (its honest "warum nicht" still shows), and the
# typed `mixer_profile` stays the only thing POSTed.  The table below is the single source of
# truth (served by `GET /api/mixer/presets`); the dashboard holds no copy of it.

class LessonPreset(BaseModel):
    """One curated lesson-purpose bundle of Mischpult fader settings (Austrian school register)."""

    model_config = ConfigDict(extra="forbid")
    id: str
    name: str                          # German display name = the lesson purpose
    description: str                   # one line: what this purpose wants didactically
    profile: ParametricMixerProfile    # the curated bundle (Umfang always; active faders only)

    def set_faders(self) -> dict[str, str]:
        """The faders this preset actively sets → {field: enum value}.  Umfang is always present
        (universal); an OPTIONAL fader appears only where the preset moves it off neutral.  This
        is exactly what the dashboard writes into the selects before intersecting with the
        template's discovered capabilities (client-side) — never a base/no-op endpoint."""
        dumped = self.profile.model_dump(mode="json")
        faders = {"umfang": dumped["umfang"]}
        for field in ("tiefe", "abstraktion", "offenheit", "geruest", "textlast"):
            if dumped[field] is not None:
                faders[field] = dumped[field]
        return faders


# The four lesson purposes.  Each sets ONLY the active endpoints its purpose needs; the rest stay
# neutral so the template's discovered capabilities decide what actually moves (rationales +
# "deliberately out" in tiefenregler-design §9 — the SME vets both the German and the didactics).
LESSON_PRESETS: list[LessonPreset] = [
    LessonPreset(
        id="wiederholung",
        name="Wiederholung vor der Schularbeit",
        description="Prüfungsnahe Wiederholung: mehr Varianten und offene Produktion mit "
                    "Rechenweg wie in der Schularbeit.",
        # rationale: tiefenregler-design §9 (rehearse in the exam's own format, more reps)
        profile=ParametricMixerProfile(umfang=Umfang.ERWEITERT, offenheit=Offenheit.OFFEN),
    ),
    LessonPreset(
        id="vertiefung",
        name="Vertiefungsstunde",
        description="Weniger Aufgaben, dafür tiefer: Strategien vergleichen, formal "
                    "darstellen und offen begründen.",
        # rationale: tiefenregler-design §9 (depth over breadth; supported subset activates)
        profile=ParametricMixerProfile(
            umfang=Umfang.KOMPAKT,
            tiefe=Tiefe.STRATEGIEN_VERGLEICHEN,
            abstraktion=Abstraktion.FORMAL,
            offenheit=Offenheit.OFFEN,
        ),
    ),
    LessonPreset(
        id="vertretung",
        name="Vertretungsstunde",
        description="Selbsttragende Stunde: viel Gerüst und vereinfachte Angabe, damit die "
                    "Klasse ohne Fachlehrkraft arbeiten kann.",
        # rationale: tiefenregler-design §9 (self-running; Offenheit stays neutral by design)
        profile=ParametricMixerProfile(
            umfang=Umfang.STANDARD,
            geruest=Geruest.GESTUETZT,
            textlast=Textlast.EINFACH,
        ),
    ),
    LessonPreset(
        id="hausuebung",
        name="Hausübung",
        description="Kurze, selbstständige Übung für daheim: kompakter Umfang mit Gerüst "
                    "zum Nicht-Steckenbleiben.",
        # rationale: tiefenregler-design §9 (short + scaffolded; full register kept)
        profile=ParametricMixerProfile(umfang=Umfang.KOMPAKT, geruest=Geruest.GESTUETZT),
    ),
]


def lesson_presets_payload() -> list[dict]:
    """The served preset table: id + German name/description + the PARTIAL fader bundle.
    The single source of truth for `GET /api/mixer/presets`; the dashboard applies these to the
    fader selects (intersecting with the discovered capabilities), never a hard-coded copy."""
    return [
        {"id": p.id, "name": p.name, "description": p.description, "faders": p.set_faders()}
        for p in LESSON_PRESETS
    ]
