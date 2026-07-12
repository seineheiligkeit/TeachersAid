"""The block model (schema §4) + v0.4 A4 rubric / B5 cross-curricular dims.

InfoBlock = information to learn FROM. TaskBlock = an exercise. Blocks are the
atom; a Baustein holds a depth-bounded list of them (no self-recursion).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .competence import DimensionRef
from .enums import CalloutRole, CoverageRelation, InfoKind, Role
from .provenance import BlockProvenance
from .response import ResponseSpec
from .richtext import RichText, collapse


class ContentFlags(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contested: bool = False
    freshness_decay: bool = False
    equipment_dependent: bool = False
    local: bool = False
    historical_fact: bool = False  # opt-in: a prose block asserting real historical claims —
    # the cross-subject hook (GWB local history, KUG art history) that puts non-GPB blocks under
    # the prose-provenance gate (which is GPB ∪ historical_fact). See provenance.py.


class BlockBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    optional: bool = False
    modality: str = "printable"  # default printable
    flags: ContentFlags | None = None
    asset_refs: list[str] = Field(default_factory=list)
    provenance: BlockProvenance | None = None  # expression provenance (History/GPB asset class);
    # absent on the common case (math, wholly-original prose). DERIVED obligation booleans live on it.


# --- A: information to learn from --------------------------------------------
class InfoBlock(BlockBase):
    role: Literal[Role.INFO] = Role.INFO
    kind: InfoKind
    content: RichText
    callout_role: CalloutRole | None = None
    teacher_note: RichText | None = None  # teacher-projection only
    watch_outs: list[str] = Field(default_factory=list)
    numbered: bool = True  # source_text: line numbers (poems/fables, so tasks ref "Zeile N").
    # False = a real-artifact card (a Realie menu/board reads as itself, not an exercise text).
    # File-backed, SME-approved atmosphere for that card. It never replaces task-bearing text.
    backdrop_asset_ref: str | None = None

    @field_validator("content", "teacher_note")
    @classmethod
    def _collapse(cls, v):
        return collapse(v) if v is not None else v


# --- B: task payloads (discriminated on `kind`) ------------------------------
class _PayloadBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MatchingPayload(_PayloadBase):
    kind: Literal["matching"] = "matching"
    left: list[str]
    right: list[str] | None = None


class OrderingPayload(_PayloadBase):
    kind: Literal["ordering"] = "ordering"
    items: list[str]


class MultipleChoicePayload(_PayloadBase):
    kind: Literal["multiple_choice"] = "multiple_choice"
    options: list[str]
    select: Literal["one", "many"]


class TrueFalseJustifyPayload(_PayloadBase):
    kind: Literal["true_false_justify"] = "true_false_justify"
    statements: list[str]


class TableFillPayload(_PayloadBase):
    kind: Literal["table_fill"] = "table_fill"
    columns: list[str]
    rows: list[list[str | None]]  # null = blank for the student


class DataInterpretationPayload(_PayloadBase):
    kind: Literal["data_interpretation"] = "data_interpretation"
    asset_ref: str


class DecisionScenarioPayload(_PayloadBase):
    kind: Literal["decision_scenario"] = "decision_scenario"
    stem: RichText


class RolePlayPayload(_PayloadBase):
    # a Sprechkarte: one cue per partner (A, B, …). The activity is ORAL — the cards ARE
    # the response surface (no write-space; cf. _SELF_CONTAINED_PAYLOADS). Used by Realien
    # role-play tasks (the speaking competence is served in-room, not on paper).
    kind: Literal["role_play"] = "role_play"
    cues: list[str]


class OtherPayload(_PayloadBase):
    # open/extension kinds: the prompt carries the content; optional data bag.
    kind: Literal["other"] = "other"
    data: dict = Field(default_factory=dict)


TaskPayload = Annotated[
    MatchingPayload
    | OrderingPayload
    | MultipleChoicePayload
    | TrueFalseJustifyPayload
    | TableFillPayload
    | DataInterpretationPayload
    | DecisionScenarioPayload
    | RolePlayPayload
    | OtherPayload,
    Field(discriminator="kind"),
]


class RubricCriterion(BaseModel):  # v0.4 A4
    model_config = ConfigDict(extra="forbid")
    criterion: str
    levels: list[str]  # e.g. ["nicht erreicht", "teilweise", "erreicht"]


class SolutionStep(BaseModel):
    """One line of the worked solution (Rechenweg). DERIVED by the parametric engine
    (sympy), never hand-authored as the answer — so the maths is correct by construction.
    Teacher-guide only."""
    model_config = ConfigDict(extra="forbid")
    text: RichText                  # what happens in this step
    expr: str | None = None         # optional LaTeX for the line of working


class SolutionPath(BaseModel):
    """An ALTERNATIVE worked solution (roadmap A4 solution graphs): a named school strategy
    + its own step sequence, reaching the SAME answer as the primary `solution_steps` by a
    different route (Gleichsetzungs- vs. Einsetzungsverfahren; Dreisatz vs. Prozentoperator).
    Like `SolutionStep`, DERIVED by the parametric engine (sympy) — never hand- or
    LLM-authored — and equally teacher-guide only. Lives here (not in parametric.py) so the
    import direction stays parametric→blocks and TaskBlock can carry it."""
    model_config = ConfigDict(extra="forbid")
    strategy: str                   # the German strategy name (Austrian school register)
    steps: list[SolutionStep] = Field(default_factory=list)   # the worked path, same style
    note: str | None = None         # optional one line: when this strategy is particularly
    # natural / unnatural for THESE drawn numbers


class TaskScaffold(BaseModel):
    """Gerüst (P2 Tiefenregler): STUDENT-FACING scaffolding, DERIVED from the instance's
    computed/curated data — never authored by hand or LLM (absent from generation views, like
    `solution_steps`). Populated only by the Gerüst fader (`pipeline/scaffold.py`).

    Unlike the teacher-only Rechenweg, this renders on the STUDENT AND HOMEWORK sheets — the
    whole point of whole-class scaffolding the teacher dialled in. It therefore carries only
    material that can NEVER leak the answer: a leak-guarded worked FIRST step (never the full
    Rechenweg, never the result), a misconception warning naming the trap category (never the
    answer), and curated Formulierungshilfen. `hint_categories` is the teacher-facing list of
    the Fehlermuster names the hint covers (so the teacher guide can name what was scaffolded;
    rendering stays pure — no catalog lookup at render time)."""
    model_config = ConfigDict(extra="forbid")
    first_step: RichText | None = None                 # worked first step (text + inline math)
    hint: str | None = None                            # student misconception warning
    hint_categories: list[str] = Field(default_factory=list)  # Fehlermuster names (teacher line)
    sentence_starters: list[str] = Field(default_factory=list)  # Formulierungshilfen (curated)

    @field_validator("first_step")
    @classmethod
    def _collapse(cls, v):
        return collapse(v) if v is not None else v


class Gloss(BaseModel):
    """Textlast (P3 Tiefenregler): one curated Wortschatz entry — a Fachbegriff and a short
    German explanation. CURATED content (lives on `ParametricTask.glossary`, SME-vetted like
    the prompt itself), SELECTED by the Textlast fader at the `einfach` endpoint and rendered
    as a student-facing Wortschatz-Kasten. A gloss explains a TERM, never a value — it must
    stay term-definitional so it can never leak a per-variant computed answer (a constant
    template gloss cannot contain a per-seed answer by construction; locked by a no-leak test).
    """
    model_config = ConfigDict(extra="forbid")
    term: str
    explanation: str


class Serves(BaseModel):
    model_config = ConfigDict(extra="forbid")
    competence_id: str
    relation: CoverageRelation


class TaskBlock(BlockBase):
    role: Literal[Role.TASK] = Role.TASK
    kind: str  # core kind or a subject task_kind_extension (validated at assemble)
    prompt: RichText
    payload: TaskPayload | None = None
    response: ResponseSpec
    cognitive_level: str  # CognitiveLevel value (the depth contract)
    difficulty: int | None = None  # 1 leicht · 2 mittel · 3 anspruchsvoll — an author/SME
    # ESTIMATE (never measured: we collect no student data), orthogonal to cognitive_level;
    # None ⇒ derived from the Anforderungsbereich of cognitive_level (see pipeline/difficulty.py)
    dimensions: list[DimensionRef] = Field(default_factory=list)  # primary first
    content_area: str | None = None  # subject content axis where it exists (Math)
    serves: list[Serves] = Field(default_factory=list)
    est_minutes: int = 0
    answer_key: RichText | None = None  # knowledge side
    acceptable_reasoning: RichText | None = None  # judgement side — the RANGE
    rubric: list[RubricCriterion] = Field(default_factory=list)  # v0.4 A4
    solution_steps: list[SolutionStep] = Field(default_factory=list)  # primary Rechenweg (derived)
    solution_paths: list[SolutionPath] = Field(default_factory=list)  # alternative strategies
    # (derived; teacher-only) — the "Alternative Lösungswege" the LLM can NEVER emit (absent
    # from GenTaskBlock, like solution_steps). Empty unless a recipe has divergent strategies.
    solution_asset_refs: list[str] = Field(default_factory=list)  # teacher-only solution figures
    # (A5 Rätsel engine): the SOLVED grid of a puzzle. Renders ONLY in the teacher projection —
    # the student sheet shows the empty grid via `asset_refs`. DERIVED/curated, never LLM-authored.
    watch_outs: list[str] = Field(default_factory=list)
    self_check: RichText | None = None  # homework: no teacher present
    scaffold: TaskScaffold | None = None  # Gerüst (P2 Tiefenregler) — student-facing, DERIVED;
    # populated only by pipeline/scaffold.py, never by hand or LLM (absent from generation views)

    @field_validator("prompt", "answer_key", "acceptable_reasoning", "self_check")
    @classmethod
    def _collapse(cls, v):
        return collapse(v) if v is not None else v

    @field_validator("difficulty")
    @classmethod
    def _difficulty_range(cls, v):
        if v is not None and v not in (1, 2, 3):
            raise ValueError("difficulty must be 1, 2 or 3 (leicht/mittel/anspruchsvoll)")
        return v


Block = Annotated[InfoBlock | TaskBlock, Field(discriminator="role")]
