"""Fermi-Werkstatt data model — estimation problems as a curated decomposition chain.

A **Fermi problem** ("Wie viele Klavierstimmer:innen gibt es in Wien?") is solved by
*decomposing* the unknown into a short chain of quantities that are each easier to estimate,
then combining them arithmetically. This module holds the typed, curated INPUT model; the
computation (the worked chain, the point estimate, the propagated acceptable range) lives in
`pipeline/fermi.py`, and the curated instances (anchors + problems) in `grounding/fermi.py`.

The load-bearing honesty discipline (invariants §3 — *select the facts, author the
expression*, and §4 — *grounding is real, gaps are honest*):

* A **`FermiAnchor`** is a single quantity with a value, HONEST uncertainty bounds
  `[low, high]`, a unit, and — crucially — a **`provenance`** that is exactly one of:
  - `FermiDatasetRef`  — the value is SELECTED from one of our curated `grounding/data/`
    datasets (e.g. the Wien population); the citation rides the dataset's `SourceRef`.
  - `FermiCitation`    — an everyday quantity with a real external published source
    (a `SourceRef`), e.g. the average Austrian household size.
  - `FermiEstimate`    — an **authored-then-vetted** plausibility estimate (there is no
    dataset for "sheets of paper per pupil per day"); it carries a `rationale` making the
    range defensible, and is explicitly MARKED as an estimate rather than dressed as a fact.
  There is **no bare invented fact**: every anchor either cites or is flagged as a
  vetted estimate with its plausibility rationale (the SME fact-checks the rationales).

* A **`FermiProblem`** is the question + an ORDERED `chain` of `ChainStep`s. Each step
  references an anchor by id and combines it into the running value by a **typed operation**
  (`multiply` / `divide` / `add`) — never prose. Each step also records whether the anchor is
  **`given`** on the student sheet or **estimated by the student** (a per-problem curated
  choice — the same anchor may be given in one problem, estimated in another). That split is
  what the sheet's leak-guard rests on: given values may appear student-facing; to-be-estimated
  values (and the point estimate / range) are teacher-only.

Nothing here is derived; the derivation (interval arithmetic → the acceptable range) is in
`pipeline/fermi.py` and is teacher-judgment SUPPORT, not a grading engine.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .datasets import SourceRef


# --- anchor provenance (exactly one of three; every anchor carries one) ------
class FermiDatasetRef(BaseModel):
    """The anchor value is SELECTED from a curated `grounding/data/` dataset — the citation
    is the dataset's own `SourceRef` (resolved by `grounding.data_store`). `note` describes
    the slice/derivation (e.g. "Mittel aus m/w 2024, gerundet"); a drift test locks the
    anchor value against the live dataset so a refresh can't silently rot it."""
    model_config = ConfigDict(extra="forbid")
    kind: Literal["dataset"] = "dataset"
    dataset_id: str
    series: str | None = None
    note: str = ""


class FermiCitation(BaseModel):
    """An everyday quantity with a real, published external source (the data analogue of a
    `role="facts"` citation): a `SourceRef` naming the authority. The value is a fact we
    select, not invent — but it may still be placed on the *estimated* side of a problem (the
    student estimates it; the citation is our defensible ground truth for the teacher range)."""
    model_config = ConfigDict(extra="forbid")
    kind: Literal["cited"] = "cited"
    source: SourceRef


class FermiEstimate(BaseModel):
    """An **authored-then-vetted** plausibility estimate — the honest marker for a quantity
    that has no dataset ("Blätter pro Schüler:in und Schultag"). It is NOT dressed as a fact:
    `rationale` states why the value and its `[low, high]` band are defensible, and the SME
    fact-checks it. An exact definitional conversion (1440 min/day) is modelled here too, with
    `low == high == value` and a rationale that says so."""
    model_config = ConfigDict(extra="forbid")
    kind: Literal["estimate"] = "estimate"
    rationale: str


FermiProvenance = Annotated[
    FermiDatasetRef | FermiCitation | FermiEstimate,
    Field(discriminator="kind"),
]


class FermiAnchor(BaseModel):
    """One quantity in the estimation chain: a value with HONEST bounds, a unit, and a
    provenance (dataset / citation / vetted estimate). Invariant: `low <= value <= high`
    (a value outside its own honest band would make the propagated range meaningless)."""
    model_config = ConfigDict(extra="forbid")
    id: str
    label: str                         # the German quantity name ("Wasserverbrauch pro Person …")
    value: Decimal                     # the best / point estimate
    low: Decimal                       # honest lower bound
    high: Decimal                      # honest upper bound
    unit: str = ""                     # "L", "km", "Personen", "" (dimensionless share/count)
    provenance: FermiProvenance = Field(discriminator="kind")

    @model_validator(mode="after")
    def _bounds_ordered(self):
        if not (self.low <= self.value <= self.high):
            raise ValueError(
                f"FermiAnchor '{self.id}': low <= value <= high violated "
                f"({self.low} <= {self.value} <= {self.high})")
        if self.low <= 0:
            # every Fermi quantity is strictly positive (interval division/OOM assume it)
            raise ValueError(f"FermiAnchor '{self.id}': low must be > 0 (got {self.low})")
        return self

    def is_exact(self) -> bool:
        """A definitional conversion / known count carries no estimation width (low==high)."""
        return self.low == self.high


class ChainStep(BaseModel):
    """One step of the decomposition chain: apply `anchor_id` to the running value via `op`.
    The FIRST step must be `multiply` (it seeds the running value from 1). `given` marks
    whether this anchor's value is printed on the student sheet (a known/given fact) or is one
    of the quantities the student must estimate themselves (then it is teacher-only)."""
    model_config = ConfigDict(extra="forbid")
    anchor_id: str
    op: Literal["multiply", "divide", "add"] = "multiply"
    given: bool = False
    # optional override of how this step reads in the worked Rechenweg (else the anchor label)
    as_label: str | None = None


class FermiProblem(BaseModel):
    """A curated estimation problem: the question + an ordered arithmetic decomposition chain.

    `result_unit`/`result_label` name the final quantity ("Liter pro Jahr"); `sig` is how many
    significant figures the presented point estimate and range are rounded to (Fermi answers are
    honest to ~1–2 sig figs — precision beyond that is fake). `klasse` + `competence_id` +
    `kompetenzbereich` anchor it to a verbatim MAT competence (the modelling dimension is MOD).
    `given_intro` is optional extra framing for the "das weißt du schon" box."""
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    question: str                      # the Fermi question (student-facing Kernfrage/prompt)
    chain: list[ChainStep]
    result_unit: str = ""
    result_label: str = ""             # "Liter Trinkwasser pro Jahr"
    sig: int = 2                        # significant figures for the presented estimate/range
    klasse: int = 3
    competence_id: str = ""            # the verbatim MAT competence id it exercises
    kompetenzbereich: str = ""         # the KB display name (for resolve_kompetenzbereich)
    dimension: str = "MOD"             # Modellieren und Problemlösen (the Fermi handlungsdim.)
    context_note: str = ""             # optional extra student-facing framing (constructed scenario)

    @model_validator(mode="after")
    def _chain_starts_multiply(self):
        if not self.chain:
            raise ValueError(f"FermiProblem '{self.id}': empty chain")
        if self.chain[0].op != "multiply":
            raise ValueError(
                f"FermiProblem '{self.id}': the first chain step must be 'multiply' "
                f"(it seeds the running value from 1), got {self.chain[0].op!r}")
        return self

    def given_ids(self) -> list[str]:
        return [s.anchor_id for s in self.chain if s.given]

    def estimated_ids(self) -> list[str]:
        return [s.anchor_id for s in self.chain if not s.given]
