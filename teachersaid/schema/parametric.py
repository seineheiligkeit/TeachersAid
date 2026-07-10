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

from pydantic import BaseModel, ConfigDict, Field

from .blocks import Serves, SolutionStep
from .response import ResponseSpec
from .richtext import RichText


class FigureSpec(BaseModel):
    """An optional figure a recipe emits for one instance: a code-gen asset REQUEST
    (a `<backend>:<recipe>` generator id + its spec dict), computed correct-by-construction
    from the same sampled values the answer is. The recipe declares only WHAT to draw;
    `pipeline/parametrize.instantiate` assigns a unique per-variant asset id (so the PNGs
    never collide) and wires it onto the block's `asset_refs`. Labels MASK the asked unknown
    ("c = ?") so a figure never leaks the answer — the same select-intent / derive-representation
    seam as the LLM declaring a chart intent while code guarantees the legible figure."""
    model_config = ConfigDict(extra="forbid")
    generator: str                     # a registered code recipe, e.g. "matplotlib:right_triangle"
    spec: dict = Field(default_factory=dict)   # generator-specific parameters (labels are strings)


class Instance(BaseModel):
    """What a recipe produces for one seed: slot values + the derived answer + steps
    (+ an optional figure computed from the same values, e.g. a Pythagoras triangle)."""
    model_config = ConfigDict(extra="forbid")
    params: dict                       # slot name -> display value (fills the prompt template)
    answer: RichText                   # the derived answer (correct by construction)
    steps: list[SolutionStep] = Field(default_factory=list)   # the worked Rechenweg
    figure: FigureSpec | None = None   # optional per-instance figure (masks the asked unknown)


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
