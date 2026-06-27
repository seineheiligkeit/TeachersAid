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


class Instance(BaseModel):
    """What a recipe produces for one seed: slot values + the derived answer + steps."""
    model_config = ConfigDict(extra="forbid")
    params: dict                       # slot name -> display value (fills the prompt template)
    answer: RichText                   # the derived answer (correct by construction)
    steps: list[SolutionStep] = Field(default_factory=list)   # the worked Rechenweg


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
