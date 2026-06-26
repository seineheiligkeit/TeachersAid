"""The block model (schema §4) + v0.4 A4 rubric / B5 cross-curricular dims.

InfoBlock = information to learn FROM. TaskBlock = an exercise. Blocks are the
atom; a Baustein holds a depth-bounded list of them (no self-recursion).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .competence import DimensionRef
from .enums import CalloutRole, CoverageRelation, InfoKind, Role
from .response import ResponseSpec
from .richtext import RichText, collapse


class ContentFlags(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contested: bool = False
    freshness_decay: bool = False
    equipment_dependent: bool = False
    local: bool = False


class BlockBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    optional: bool = False
    modality: str = "printable"  # default printable
    flags: ContentFlags | None = None
    asset_refs: list[str] = Field(default_factory=list)


# --- A: information to learn from --------------------------------------------
class InfoBlock(BlockBase):
    role: Literal[Role.INFO] = Role.INFO
    kind: InfoKind
    content: RichText
    callout_role: CalloutRole | None = None
    teacher_note: RichText | None = None  # teacher-projection only
    watch_outs: list[str] = Field(default_factory=list)

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
    | OtherPayload,
    Field(discriminator="kind"),
]


class RubricCriterion(BaseModel):  # v0.4 A4
    model_config = ConfigDict(extra="forbid")
    criterion: str
    levels: list[str]  # e.g. ["nicht erreicht", "teilweise", "erreicht"]


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
    watch_outs: list[str] = Field(default_factory=list)
    self_check: RichText | None = None  # homework: no teacher present

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
