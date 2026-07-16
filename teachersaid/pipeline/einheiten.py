"""Einheiten-Detektiv — dimensional-analysis puzzles by INVERTING the units validator.

The physics engine (`pipeline/physics.py`) computes with `sympy.physics.units` and, before
formatting, `_assert_dimension`s the result against its expected unit — a structural guard
that a unit-category error cannot survive. This module **inverts** that guard into a
teaching object: instead of *proving a formula right*, it presents a target quantity with a
handful of candidate formulas — exactly one dimensionally correct, the rest dimensionally
WRONG — and asks the student to be the detective: *"Welche Formel kann nicht stimmen — und
warum?"*, justified over the units.

**Correct by construction, both ways.** The one correct candidate is the school formula; its
composed unit is asserted EQUAL to the target's dimension (`_assert_dimension`, the same
guard physics.py uses). Every wrong candidate is produced by a CATALOGUED transform applied
to that correct formula (a factor swapped, a ratio inverted, a product summed, a quantity
squared or dropped — the `TRANSFORM_CATALOG` below, each entry named + didactically
motivated in the discipline of `grounding/misconceptions`) and is **PROVEN wrong at build
time**: its composed dimension is computed with `sympy.physics.units` and asserted to DIFFER
from the target's (`_base_dims`, reused from physics.py). A transform that — for some draw —
happened to reproduce the target dimension is rejected, so no accidental dimensional
coincidence ever ships as a "wrong" option. The additive slip (`sum_for_product`) is proven
wrong by a different but equally rigorous route: its two summands carry DIFFERENT base
dimensions, so the sum is dimensionally inhomogeneous — it is not a well-defined quantity at
all, let alone the target one.

**The answer and the Begründung are DERIVED, never authored.** The set of impossible
formulas is `{candidate : dim(candidate) ≠ dim(target)}` — computed. The per-formula
reasoning shown to the teacher ("[s·t] = m·s, aber gesucht ist m/s → kann nicht stimmen") is
built from the SAME computed unit chain, never written by hand or model.

**Task kind — open_response (honest fit, no engine change).** The candidates are listed,
lettered, in the prompt itself (so every seed's prompt differs — the variant engine dedups
on the prompt, and a payload-only design would collapse same-quantity draws to one). The
response is ruled lines: the student crosses out the impossible formulas AND justifies each
over the units — the justification genuinely needs write-space, which `multiple_choice`
(a self-contained tick-box) cannot give and `true_false_justify` would only give by moving
the varying content off the prompt. See `Documents/einheiten-detektiv-design.md`.

Recipes register into the shared `_RECIPES` registry (like physics/chemistry), so
`make_variants` / templates / the dashboard drive the Einheiten-Detektiv uniformly.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from sympy import Integer
from sympy.physics import units as _u

from ..schema.blocks import SolutionStep
from ..schema.parametric import Instance
# Reuse the EXACT validator we are inverting (the shared dimensional guard physics.py also
# builds on): base-SI dimension reduction + the assertion. `_base_dims(a) == _base_dims(b)` is
# dimensional equality regardless of surface form (Ω·A reduces to volt); `_assert_dimension`
# raises on a category error. Imported from `dimensions`, not `physics`, so there is no cycle.
from .dimensions import _assert_dimension, _base_dims
from .parametrize import Unsuitable, _recipe

# --- unit aliases (all simple-symbol units so composed unit strings read cleanly) --------
_m, _s, _kg = _u.meter, _u.second, _u.kilogram
_A, _V, _Ohm = _u.ampere, _u.volt, _u.ohm
_N, _J, _W = _u.newton, _u.joule, _u.watt


# ============================================================================
# the quantity + formula model (a school formula = a product/quotient of givens)
# ============================================================================
@dataclass(frozen=True)
class Quantity:
    """A physical quantity as it appears on the sheet: a display symbol, a display unit
    string (a simple unit symbol so composed units stay legible), and the matching
    `sympy.physics.units` expression the dimension check computes with."""
    symbol: str          # e.g. "s"
    unit_key: str        # e.g. "m"  (what the student reads)
    unit: object         # e.g. _m   (what _base_dims reduces)


@dataclass(frozen=True)
class FormulaSpec:
    """One curated school formula for a target quantity: target = ∏ givenᵢ^expᵢ.

    `factors` is the correct right-hand side as (Quantity, exponent) pairs (exponent ±1 in
    every curated spec). The composed unit ∏ unitᵢ^expᵢ is asserted dimensionally EQUAL to
    `target.unit` at import time (`_assert_dimension`) — the correct option is correct by
    construction, checked by the very guard this module inverts."""
    quantity: str                                   # German name, e.g. "Geschwindigkeit"
    target: Quantity                                # v, "m/s", _m/_s
    factors: tuple[tuple[Quantity, int], ...]       # ((s,+1), (t,-1))
    topic: str                                      # groups specs into a recipe/template


# --- the curated givens ------------------------------------------------------------------
_S = Quantity("s", "m", _m)          # Strecke / Weg
_T = Quantity("t", "s", _s)          # Zeit
_V_ = Quantity("v", "m/s", _m / _s)  # Geschwindigkeit (as a given, e.g. in s = v·t)
_R = Quantity("R", "Ω", _Ohm)        # Widerstand
_I = Quantity("I", "A", _A)          # Stromstärke
_U = Quantity("U", "V", _V)          # Spannung
_F = Quantity("F", "N", _N)          # Kraft
_P = Quantity("P", "W", _W)          # Leistung
_WORK = Quantity("W", "J", _J)       # Arbeit (W = F·s — no Watt unit on that sheet, so no clash)
_ENERGY = Quantity("E", "J", _J)     # Energie (symbol E keeps clear of the Watt unit "W")


# --- the formula catalog (curated, school-level; each given has a simple unit symbol) ----
# Symbols are chosen so a quantity symbol never coincides with a UNIT symbol on the same
# sheet — e.g. the Leistung/Energie specs use E (Energie), never W (Arbeit), so the Watt unit
# "W" can never be misread as a quantity.
FORMULAS: tuple[FormulaSpec, ...] = (
    # Mechanik / Bewegung (v = s/t and its rearrangements)
    FormulaSpec("Geschwindigkeit", _V_, ((_S, 1), (_T, -1)), "bewegung"),
    FormulaSpec("Strecke", _S, ((_V_, 1), (_T, 1)), "bewegung"),
    FormulaSpec("Zeit", _T, ((_S, 1), (_V_, -1)), "bewegung"),
    # Elektrizität (Ohm: U = R·I and its rearrangements)
    FormulaSpec("Spannung", _U, ((_R, 1), (_I, 1)), "elektrik"),
    FormulaSpec("Widerstand", _R, ((_U, 1), (_I, -1)), "elektrik"),
    FormulaSpec("Stromstärke", _I, ((_U, 1), (_R, -1)), "elektrik"),
    # Energie / Arbeit / Leistung (W = F·s, E = P·t, P = E/t)
    FormulaSpec("Arbeit", _WORK, ((_F, 1), (_S, 1)), "energie"),
    FormulaSpec("Energie", _ENERGY, ((_P, 1), (_T, 1)), "energie"),
    FormulaSpec("Leistung", _P, ((_ENERGY, 1), (_T, -1)), "energie"),
)

# German definite article per target quantity, so the prompt reads grammatically
# ("der Widerstand", "die Geschwindigkeit"). Der/die/das is a fixed property of each noun.
_ARTICLE: dict[str, str] = {
    "Geschwindigkeit": "die", "Strecke": "die", "Zeit": "die", "Spannung": "die",
    "Widerstand": "der", "Stromstärke": "die", "Arbeit": "die", "Energie": "die",
    "Leistung": "die",
}


# ============================================================================
# candidate formulas (mono = product/quotient · sum = the additive slip)
# ============================================================================
@dataclass(frozen=True)
class Candidate:
    """One formula shown to the student. `mono` candidates are ∏ givenᵢ^expᵢ; the single
    `sum` candidate (the additive slip) is given₁ + given₂. `transform_id` is None for the
    one correct formula and a `TRANSFORM_CATALOG` id for every wrong one (the teacher guide
    names which slip each probes)."""
    kind: str                                       # "mono" | "sum"
    symbol: str
    factors: tuple[tuple[Quantity, int], ...] = ()  # for kind == "mono"
    addends: tuple[Quantity, ...] = ()              # for kind == "sum"
    transform_id: str | None = None


_SUP = {2: "²", 3: "³"}


def _pow_str(base: str, e: int) -> str:
    """`base` raised to a positive exponent, rendered with a Unicode superscript."""
    return base if e == 1 else base + _SUP.get(e, f"^{e}")


def _rhs(parts: list[tuple[str, int]]) -> str:
    """A product/quotient right-hand side from (label, exponent) pairs → 'a · b / c'.
    Denominators with more than one factor are parenthesised so the meaning is unambiguous."""
    num = [_pow_str(lab, e) for lab, e in parts if e > 0]
    den = [_pow_str(lab, -e) for lab, e in parts if e < 0]
    head = " · ".join(num) if num else "1"
    if not den:
        return head
    tail = " · ".join(den)
    return f"{head} / {tail}" if len(den) == 1 else f"{head} / ({tail})"


def formula_display(cand: Candidate) -> str:
    """The student-facing formula string, e.g. 'v = s / t' or 'U = R + I'."""
    if cand.kind == "sum":
        return f"{cand.symbol} = " + " + ".join(q.symbol for q in cand.addends)
    return f"{cand.symbol} = " + _rhs([(q.symbol, e) for q, e in cand.factors])


def unit_display(cand: Candidate) -> str:
    """The composed UNIT string of a candidate, e.g. 'm / s', 'm · s', 'Ω / A', 'm² / s'.
    For the additive slip it is 'N + m' — deliberately, to make the inhomogeneity visible."""
    if cand.kind == "sum":
        return " + ".join(q.unit_key for q in cand.addends)
    return _rhs([(q.unit_key, e) for q, e in cand.factors])


def _unit_matches_target(cand: Candidate, spec: FormulaSpec) -> bool:
    """True iff the candidate's composed unit equals the target unit modulo spacing (so the
    correct 'm / s' is recognised as 'm/s') — avoids a redundant '… = m/s' on the correct line
    while still showing the informative 'N · m = J' where the composed unit has a named form."""
    return unit_display(cand).replace(" ", "") == spec.target.unit_key.replace(" ", "")


def _mono_unit(factors: tuple[tuple[Quantity, int], ...]):
    """The `sympy.physics.units` expression ∏ unitᵢ^expᵢ — what `_base_dims` reduces."""
    expr = Integer(1)
    for q, e in factors:
        expr = expr * q.unit ** e
    return expr


def _same_dim(factors: tuple[tuple[Quantity, int], ...], target) -> bool:
    """True iff the composed unit has the SAME base-SI dimension as `target` (the physics
    guard's equality, so Ω·A compares equal to volt)."""
    return _base_dims(_mono_unit(factors)) == _base_dims(target)


# ============================================================================
# the transform catalog — the correct-by-construction WRONGNESS layer (my module)
# ============================================================================
# Mirrors the discipline of `grounding/misconceptions`: each transform is a NAMED,
# didactically-motivated way a student mis-assembles a formula, with a curated German label
# + one-line description (teacher-guide register) + a provenance note. The transform COMPUTES
# a wrong candidate from the correct factors; the recipe then PROVES it dimensionally wrong.
# `grounding/misconceptions.py` is owned by another track this session, so this catalog lives
# here (the Einheiten-Detektiv's wrongness is dimensional, a different axis from the numeric
# Fehlermuster there).

@dataclass(frozen=True)
class Transform:
    id: str
    name: str                                       # German display name (teacher guide)
    short: str                                      # one-line German description
    source: str                                     # curation provenance (didactic note)
    build: Callable[[FormulaSpec, random.Random], "Candidate | None"]


def _t_ratio_inverted(spec: FormulaSpec, rng: random.Random) -> Candidate | None:
    """Zähler und Nenner vertauscht: a genuine ratio is turned upside down (v = t/s for
    v = s/t). Applies only when the correct formula HAS both a numerator and a denominator."""
    pos = [f for f in spec.factors if f[1] > 0]
    neg = [f for f in spec.factors if f[1] < 0]
    if not pos or not neg:
        return None
    flipped = tuple((q, -e) for q, e in spec.factors)
    return Candidate("mono", spec.target.symbol, factors=flipped, transform_id="ratio_inverted")


def _t_product_for_quotient(spec: FormulaSpec, rng: random.Random) -> Candidate | None:
    """Mal statt geteilt: a division is carried out as a multiplication (v = s·t for
    v = s/t). Applies only when the correct formula contains a division."""
    if not any(e < 0 for _, e in spec.factors):
        return None
    prod = tuple((q, abs(e)) for q, e in spec.factors)
    return Candidate("mono", spec.target.symbol, factors=prod,
                     transform_id="product_for_quotient")


def _t_quotient_for_product(spec: FormulaSpec, rng: random.Random) -> Candidate | None:
    """Geteilt statt mal: a multiplication is carried out as a division (U = R/I for
    U = R·I). Applies only to a pure product of ≥ 2 givens; one factor moves to the
    denominator."""
    if any(e < 0 for _, e in spec.factors) or len(spec.factors) < 2:
        return None
    i = rng.randrange(len(spec.factors))
    flipped = tuple((q, -e if j == i else e) for j, (q, e) in enumerate(spec.factors))
    return Candidate("mono", spec.target.symbol, factors=flipped,
                     transform_id="quotient_for_product")


def _t_sum_for_product(spec: FormulaSpec, rng: random.Random) -> Candidate | None:
    """Plus statt mal: two multiplied quantities are ADDED (F = m + g for F = m·g). Applies
    only to a pure product of exactly two givens with DIFFERENT units — the sum is then
    dimensionally inhomogeneous (you may not add unlike units), which is the whole lesson."""
    if len(spec.factors) != 2 or any(e != 1 for _, e in spec.factors):
        return None
    (q1, _), (q2, _) = spec.factors
    if _base_dims(q1.unit) == _base_dims(q2.unit):
        return None                                  # same units → the sum would be defined
    return Candidate("sum", spec.target.symbol, addends=(q1, q2),
                     transform_id="sum_for_product")


def _t_factor_dropped(spec: FormulaSpec, rng: random.Random) -> Candidate | None:
    """Eine Größe vergessen: a factor is dropped entirely (v = s for v = s/t). Applies to any
    formula with ≥ 2 factors; the remaining composed unit no longer matches the target."""
    if len(spec.factors) < 2:
        return None
    neg = [j for j, (_, e) in enumerate(spec.factors) if e < 0]
    i = rng.choice(neg) if neg else rng.randrange(len(spec.factors))  # drop a denominator first
    kept = tuple(f for j, f in enumerate(spec.factors) if j != i)     # → 'v = s', not 'v = 1/t'
    return Candidate("mono", spec.target.symbol, factors=kept, transform_id="factor_dropped")


def _t_wrongly_squared(spec: FormulaSpec, rng: random.Random) -> Candidate | None:
    """Größe fälschlich quadriert: one factor is raised to the power two (v = s²/t for
    v = s/t) — a unit-power slip. Applies to any factor; the composed dimension gains one
    extra power of that unit."""
    i = rng.randrange(len(spec.factors))
    squared = tuple((qq, (ee + (1 if ee > 0 else -1)) if j == i else ee)
                    for j, (qq, ee) in enumerate(spec.factors))
    return Candidate("mono", spec.target.symbol, factors=squared,
                     transform_id="wrongly_squared")


TRANSFORM_CATALOG: tuple[Transform, ...] = (
    Transform(
        "ratio_inverted", "Zähler und Nenner vertauscht",
        "Bei einem Bruch werden Zähler und Nenner vertauscht — die Größe wird verkehrt "
        "herum geteilt (t/s statt s/t).",
        "Physikdidaktik (Größen und Einheiten — Fehlvorstellungen zur Formelrichtung).",
        _t_ratio_inverted),
    Transform(
        "product_for_quotient", "Mal statt geteilt",
        "Es wird multipliziert, wo dividiert werden müsste (s·t statt s/t) — die Formel "
        "nicht umgestellt.",
        "Physikdidaktik (Fehlvorstellungen zum Umgang mit Formeln — falsche Rechenoperation).",
        _t_product_for_quotient),
    Transform(
        "quotient_for_product", "Geteilt statt mal",
        "Es wird dividiert, wo multipliziert werden müsste (R/I statt R·I).",
        "Physikdidaktik (Fehlvorstellungen zum Umgang mit Formeln — falsche Rechenoperation).",
        _t_quotient_for_product),
    Transform(
        "sum_for_product", "Plus statt mal (Einheiten ungleich)",
        "Zwei Größen werden addiert statt multipliziert — man darf aber nur Größen mit "
        "gleicher Einheit addieren, hier passen die Einheiten nicht zusammen.",
        "Physikdidaktik (Einheitenbetrachtung — nur gleichartige Größen sind addierbar).",
        _t_sum_for_product),
    Transform(
        "factor_dropped", "Eine Größe vergessen",
        "Eine der benötigten Größen fehlt in der Formel — die Einheit passt dann nicht mehr.",
        "Physikdidaktik (Größen und Einheiten — unvollständige Formel).",
        _t_factor_dropped),
    Transform(
        "wrongly_squared", "Größe fälschlich quadriert",
        "Eine Größe wird quadriert, obwohl sie nur einfach vorkommt — die Einheit erhält "
        "eine zusätzliche Potenz.",
        "Physikdidaktik (Einheitenbetrachtung — Potenzfehler bei Größen).",
        _t_wrongly_squared),
)

_TRANSFORMS_BY_ID = {t.id: t for t in TRANSFORM_CATALOG}


def get_transform(tid: str) -> Transform:
    """The catalogued transform for `tid` (a candidate names a real one), or raise."""
    try:
        return _TRANSFORMS_BY_ID[tid]
    except KeyError:
        raise KeyError(f"unknown Einheiten-Detektiv transform id {tid!r}")


# --- import-time sanity: every curated correct formula really is dimensionally correct ----
for _spec in FORMULAS:
    _assert_dimension(_mono_unit(_spec.factors), _spec.target.unit)


# ============================================================================
# the builder + the topic recipes
# ============================================================================
def _prove_wrong(cand: Candidate, target) -> bool:
    """True iff `cand` is DIMENSIONALLY IMPOSSIBLE for `target` — the guarantee every
    distractor must satisfy. A `mono` candidate must reduce to a DIFFERENT base dimension
    (an accidental coincidence with the target returns False → the caller rejects it). A
    `sum` candidate is impossible when its two summands carry different base dimensions
    (an inhomogeneous sum is not a well-defined quantity)."""
    if cand.kind == "sum":
        a, b = cand.addends
        return _base_dims(a.unit) != _base_dims(b.unit)
    return not _same_dim(cand.factors, target)


def build_item(spec: FormulaSpec, rng: random.Random) -> tuple[list[Candidate], int]:
    """Build one detective item for `spec`: the shuffled candidate list + the index of the
    single correct option. 2–3 wrong candidates, each from a distinct catalogued transform,
    each PROVEN dimensionally impossible; deduped by display; the correct formula asserted
    dimensionally right. Raises `Unsuitable` if fewer than two valid distractors survive."""
    correct = Candidate("mono", spec.target.symbol, factors=spec.factors, transform_id=None)
    _assert_dimension(_mono_unit(correct.factors), spec.target.unit)   # the guard, not inverted

    want = rng.choice([2, 3])
    order = list(TRANSFORM_CATALOG)
    rng.shuffle(order)
    seen = {formula_display(correct)}
    wrong: list[Candidate] = []
    for tr in order:
        if len(wrong) >= want:
            break
        cand = tr.build(spec, rng)
        if cand is None:
            continue
        if not _prove_wrong(cand, spec.target.unit):      # reject a dimensional coincidence
            continue
        disp = formula_display(cand)
        if disp in seen:                                  # dedupe identical displays
            continue
        seen.add(disp)
        wrong.append(cand)
    if len(wrong) < 2:
        raise Unsuitable                                  # need a real line-up → resample

    candidates = [correct, *wrong]
    rng.shuffle(candidates)
    correct_index = candidates.index(correct)
    return candidates, correct_index


_LETTERS = "ABCDEF"


def _reason_step(letter: str, cand: Candidate, spec: FormulaSpec,
                 correct: bool) -> SolutionStep:
    """One derived reasoning line for the teacher guide: substitute the units and compare
    with the target. The verdict is COMPUTED (from the dimension check), never authored."""
    tgt = spec.target.unit_key
    if correct:
        units = unit_display(cand)
        shown = units if _unit_matches_target(cand, spec) else f"{units} = {tgt}"
        return SolutionStep(
            text=f"{letter}) {formula_display(cand)}: Einheiten einsetzen → {shown}. "
                 f"Das ist die gesuchte Einheit {tgt} → kann stimmen.")
    if cand.kind == "sum":
        a, b = cand.addends
        return SolutionStep(
            text=f"{letter}) {formula_display(cand)}: {a.symbol} hat die Einheit "
                 f"{a.unit_key}, {b.symbol} die Einheit {b.unit_key} — verschiedene "
                 f"Einheiten kann man nicht addieren → kann nicht stimmen.")
    return SolutionStep(
        text=f"{letter}) {formula_display(cand)}: Einheiten einsetzen → {unit_display(cand)}, "
             f"gesucht ist aber {tgt} → kann nicht stimmen.")


def _build(rng: random.Random, topic: str) -> Instance:
    """Draw one Einheiten-Detektiv item for `topic` and assemble the open-response Instance
    (the whole item lives in the prompt so each variant's prompt differs; the answer + the
    per-formula Begründung are derived from the computed unit chain)."""
    specs = [s for s in FORMULAS if s.topic == topic]
    spec = rng.choice(specs)
    candidates, correct_index = build_item(spec, rng)

    letters = _LETTERS[:len(candidates)]
    listing = "; ".join(f"{letters[i]}) {formula_display(c)}"
                        for i, c in enumerate(candidates))
    givens = ", ".join(f"{q.symbol} (in {q.unit_key})" for q, _ in spec.factors)
    article = _ARTICLE.get(spec.quantity, "die")
    aufgabe = (
        f"Einheiten-Detektiv: Gesucht ist {article} {spec.quantity} {spec.target.symbol} "
        f"(Einheit: {spec.target.unit_key}). Gegeben sind {givens}. Zur Auswahl stehen: "
        f"{listing}. Welche Formeln können nicht stimmen? Streiche sie durch und begründe "
        f"jede Entscheidung über die Einheiten (setze die Einheiten ein und vergleiche mit "
        f"{spec.target.unit_key})."
    )

    correct = candidates[correct_index]
    correct_letter = letters[correct_index]
    wrong_letters = [letters[i] for i in range(len(candidates)) if i != correct_index]
    correct_units = unit_display(correct)
    unit_phrase = (correct_units if _unit_matches_target(correct, spec)
                   else f"{correct_units} = {spec.target.unit_key}")
    answer = (
        f"Nur {correct_letter}) {formula_display(correct)} kann stimmen "
        f"(Einheit {unit_phrase}). "
        f"{', '.join(wrong_letters)} scheiden über die Einheiten aus."
    )
    steps = [_reason_step(letters[i], c, spec, i == correct_index)
             for i, c in enumerate(candidates)]
    return Instance(params={"aufgabe": aufgabe}, answer=answer, steps=steps)


@_recipe("einheiten_bewegung")
def _einheiten_bewegung(rng: random.Random) -> Instance:
    """Einheiten-Detektiv: gleichförmige Bewegung (v = s/t und Umstellungen)."""
    return _build(rng, "bewegung")


@_recipe("einheiten_elektrik")
def _einheiten_elektrik(rng: random.Random) -> Instance:
    """Einheiten-Detektiv: Ohm'sches Gesetz (U = R·I und Umstellungen)."""
    return _build(rng, "elektrik")


@_recipe("einheiten_energie")
def _einheiten_energie(rng: random.Random) -> Instance:
    """Einheiten-Detektiv: elektrische Arbeit und Leistung (W = F·s, W = P·t, P = W/t)."""
    return _build(rng, "energie")
