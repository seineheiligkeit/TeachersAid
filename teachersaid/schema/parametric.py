"""Parametric task templates (Maths variant + solution engine).

A `ParametricTask` is a curated template — a prompt with `{slots}` + a `recipe` id — that
the engine (`pipeline/parametrize.py`) instantiates into concrete `TaskBlock`s, one per
seed. The recipe (a registered Python function, like an asset `@_generator`) OWNS both the
parameter sampling (so constraints like "integer solution" are trivial) and the solving:
it returns an `Instance` carrying the slot values, the DERIVED answer, and the worked
solution steps (sympy → exact, correct by construction). The numbers are computed, never
authored — so N variants are all correct and each carries its Rechenweg.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .blocks import Serves, SolutionStep
from .response import ResponseSpec
from .richtext import RichText


def _no_digits(v: str | None) -> str | None:
    """Guard for curated context strings: a context frames the task, it never asserts a
    number — every digit must come from the computed instance (select, never author).
    `isdigit()` also catches super-/subscript digits, so a smuggled quantity can't hide."""
    if v is not None and any(ch.isdigit() for ch in v):
        raise ValueError(f"context must be digit-free (numbers are computed, never authored): {v!r}")
    return v


# --- Misconception-engine seam (roadmap A3) ----------------------------------
# The recipe→MC contract. A `multiple_choice` recipe declares WHAT it drew (magnitudes) +
# the correct value + which catalogued misconceptions apply + how the value is formatted.
# The engine (`pipeline/misconceive.py` + `pipeline/parametrize.py`) then COMPUTES each
# distractor by applying a transform to those magnitudes — so a distractor is
# correct-by-construction (a documented error over the same numbers, guaranteed ≠ the
# correct answer, deduped, plausibility-gated). Everything on `MCSpec` is a request the
# recipe fills; the derived options + which misconception each probes are computed and land
# on `Instance.mc_distractors` (never authored by hand or LLM — the engine writes them).
class MCSpec(BaseModel):
    """A recipe's declaration of how to build correct-by-construction MC distractors.

    `magnitudes` are the raw drawn numbers a transform needs (e.g. {"a":3,"b":5,"c":20});
    `correct` is the correct numeric value (a plain float); `applicable` names the catalog
    ids to try, in the order they should be offered; `unit`/`prefix`/`dp` reproduce the
    recipe's OWN German number+unit formatting so every distractor looks stylistically
    identical to the answer (a distractor that reads differently is a free giveaway);
    `nonneg` marks that a negative value is physically/mathematically impossible for this
    quantity and must be dropped (the plausibility gate)."""
    model_config = ConfigDict(extra="forbid")
    magnitudes: dict[str, float]
    correct: float
    applicable: list[str]              # misconception ids (order = option order before shuffle)
    unit: str = ""                     # e.g. "V", "Ω", "%", "m/s" (spaced after the number)
    prefix: str = ""                   # e.g. "x = ", "U = " (leads the formatted value)
    dp: int = 2                        # decimal places for the German formatter
    nonneg: bool = False               # drop a distractor whose value is < 0 (impossible)
    as_fraction: bool = False          # format values as an exact reduced fraction "p/q"
    # (fraction recipes) instead of a German decimal — recovered exactly via limit_denominator
    select: str = "one"               # MC selection mode ("one" — a single correct option)


class Distractor(BaseModel):
    """A DERIVED wrong option: its formatted text + the catalogued misconception it probes.
    Computed at variant time by the engine; never authored. Teacher-guide facing."""
    model_config = ConfigDict(extra="forbid")
    text: str                          # the formatted wrong option (same style as the answer)
    misconception_id: str              # a `grounding/misconceptions` catalog id


class Instance(BaseModel):
    """What a recipe produces for one seed: slot values + the derived answer + steps."""
    model_config = ConfigDict(extra="forbid")
    params: dict                       # slot name -> display value (fills the prompt template)
    answer: RichText                   # the derived answer (correct by construction)
    steps: list[SolutionStep] = Field(default_factory=list)   # the worked Rechenweg
    difficulty: int | None = None      # the band (1–3) the recipe ACTUALLY delivered — set only
    # by recipes with a difficulty knob / an intrinsic item band; never a requested-but-ignored value
    context: str | None = None         # curated, digit-free sentence keyed to the DRAWN item
    # (where the substance/reaction occurs); prefixes the prompt. Selected from grounding, never authored.
    mc: MCSpec | None = None           # a multiple_choice recipe's distractor-build request (see MCSpec)
    mc_distractors: list[Distractor] = Field(default_factory=list)  # DERIVED wrong options +
    # the misconception each probes — computed by the engine at variant time, never authored.
    # (`Instance` is a pipeline-internal artifact the LLM never emits — no generation view — so
    # these derived fields are derivation-safe by construction.)

    @field_validator("difficulty")
    @classmethod
    def _difficulty_range(cls, v):
        if v is not None and v not in (1, 2, 3):
            raise ValueError("difficulty must be 1, 2 or 3")
        return v

    @field_validator("context")
    @classmethod
    def _ctx_guard(cls, v):
        return _no_digits(v)


class ParametricTask(BaseModel):
    """A reusable template: prompt with {slots} + a recipe that generates+solves it."""
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str = ""                    # human label for the worksheet/dashboard
    subject: str
    klasse: int
    kompetenzbereich: str | None = None
    content_area: str | None = None
    recipe: str                        # a registered generator id (pipeline/parametrize)
    prompt_template: str               # German prompt with {slots}; $...$ spans typeset inline
    serves: list[Serves] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    cognitive_level: str = "apply"
    kind: str = "calculation"
    est_minutes: int = 5
    response: ResponseSpec | None = None
    context_frame: str | None = None   # neutral, digit-free per-template frame (numeric maths):
    # names where this SKILL is used, asserts no item fact. Rendered once in the worksheet intro
    # (not per prompt — item-keyed contexts vary, a template frame would repeat N times).

    @field_validator("context_frame")
    @classmethod
    def _frame_guard(cls, v):
        return _no_digits(v)
