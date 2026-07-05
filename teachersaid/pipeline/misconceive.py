"""The misconception transform registry — correct-by-construction MC distractors.

Roadmap A3. A `multiple_choice` parametric recipe declares an `MCSpec` (schema/parametric)
of what it drew + the correct value + which catalogued misconceptions apply. This module
turns that into concrete distractors: for each applicable misconception, a registered
transform (`@_misconception("<id>")`) COMPUTES the wrong value that misconception produces
for exactly those numbers. Both the correct answer and every distractor are computed from
the same magnitudes — so the teacher guide can name precisely which error each distractor
probes ("B prüft: Vorzeichenfehler").

This is `intentionally_flawed` generalised into a theory: a wrong option built on purpose,
from a *named* cause in the curated `grounding/misconceptions` catalog, deduped, and
plausibility-gated. The engine — not the LLM, not a human — writes it.

The three guarantees (all here, all deterministic):
  * **≠ correct** — a distractor whose formatted text equals the correct option is dropped
    (compared AFTER the same rounding/formatting, so a value that merely rounds to the
    answer is caught, not just an exact numeric match).
  * **pairwise distinct** — distractors that format to the same text collapse to one.
  * **plausibility** — a value the recipe declared impossible (`nonneg` → negative) is
    dropped. The gate is deliberately simple and principled; a recipe opts in per quantity.

`Transform` signature (the seam you own): `fn(mags: dict[str, float], correct: float) ->
float | None`. It reads the drawn magnitudes, returns the wrong value the misconception
yields, or `None` to decline (the error doesn't produce a distinct value for this draw —
e.g. an inverse-operation slip where the coefficient is 1). Returning a value that happens
to equal `correct`, or an implausible one, is fine — the gates below handle it.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Callable

from ..grounding import misconceptions as _cat
from ..schema.parametric import Distractor, MCSpec

# id -> transform. Registered like recipes / asset generators (@_misconception).
Transform = Callable[[dict, float], "float | None"]
_TRANSFORMS: dict[str, Transform] = {}


def _misconception(mid: str):
    """Register a transform for catalog id `mid` (which must exist in the catalog)."""
    def reg(fn: Transform) -> Transform:
        if mid not in _cat.CATALOG:
            raise KeyError(f"@_misconception({mid!r}): not in grounding/misconceptions catalog")
        _TRANSFORMS[mid] = fn
        return fn
    return reg


# --- German number + unit formatting (the shared answer-style formatter) ------
def _fmt_de(value: float, dp: int) -> str:
    """German decimal formatting (comma), trailing zeros trimmed; whole numbers print
    without a decimal part (`_fmt_de(5.0, 2)` → '5', `_fmt_de(2.5, 2)` → '2,5')."""
    f = float(value)
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    s = f"{f:.{dp}f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _fmt_fraction(value: float) -> str:
    """A value as an exact reduced fraction 'p/q' (integer if q == 1). The recipe works
    with proper fractions of small denominators, so `limit_denominator` recovers the exact
    rational (float round-trip is lossless at this scale)."""
    fr = Fraction(value).limit_denominator(1000)
    return str(fr.numerator) if fr.denominator == 1 else f"{fr.numerator}/{fr.denominator}"


def format_value(value: float, spec: MCSpec) -> str:
    """Format a value EXACTLY as the recipe formats its correct answer — prefix + number +
    spaced unit (or an exact reduced fraction when `spec.as_fraction`). Used for the correct
    option AND every distractor, so they are stylistically indistinguishable (style parity is
    a correctness property here: a distractor that looks different from the answer would be a
    giveaway)."""
    body = _fmt_fraction(value) if spec.as_fraction else _fmt_de(value, spec.dp)
    if spec.unit:
        body = f"{body} {spec.unit}"
    return f"{spec.prefix}{body}"


# --- the transforms (compute the WRONG value from the drawn magnitudes) -------
# Each reads `mags` (the recipe's drawn numbers) and returns the value the named
# misconception produces. `correct` is passed for the transforms that are most naturally
# expressed relative to the right answer, but the value is always genuinely computed.

@_misconception("sign_error")
def _sign_error(mags: dict, correct: float) -> float | None:
    """a·x + b = c solved as if b were ADDED to the RHS instead of subtracted:
    x = (c + b) / a  (the classic transposition sign slip; should be (c - b)/a)."""
    a, b, c = mags.get("a"), mags.get("b", 0.0), mags.get("c")
    if a in (None, 0) or c is None:
        return None
    return (c + b) / a


@_misconception("inverse_operation")
def _inverse_operation(mags: dict, correct: float) -> float | None:
    """The rearrangement inverse is confused: instead of dividing by the coefficient a, the
    student MULTIPLIES — x = (c - b) · a (should be (c - b)/a). A documented equation-solving
    slip (Malle)."""
    a, b, c = mags.get("a"), mags.get("b", 0.0), mags.get("c")
    if a in (None, 0) or c is None:
        return None
    if a == 1:
        return None                                    # ·1 vs /1 identical — no distinct value
    return (c - b) * a


@_misconception("percent_base_confusion")
def _percent_base_confusion(mags: dict, correct: float) -> float | None:
    """Prozentwert asked (p % of G). The base confusion divides by the percent instead of
    multiplying by p/100: G / p · 100 … here modelled as the common inversion G / (p/100)
    = G·100/p (treating the percentage as a divisor of the base)."""
    base, pct = mags.get("base"), mags.get("pct")
    if not base or not pct:
        return None
    return base * 100.0 / pct                           # should be base·pct/100


@_misconception("fraction_add_across")
def _fraction_add_across(mags: dict, correct: float) -> float | None:
    """The persistent fraction error: a/b + c/d computed as (a+c)/(b+d) instead of over a
    common denominator. `mags` carries a,b,c,d; the value is the wrong sum."""
    a, b, c, d = mags.get("a"), mags.get("b"), mags.get("c"), mags.get("d")
    if None in (a, b, c, d) or (b + d) == 0:
        return None
    return (a + c) / (b + d)


@_misconception("fraction_keep_numerators")
def _fraction_keep_numerators(mags: dict, correct: float) -> float | None:
    """LCD found correctly but the numerators are NOT adjusted: (a + c) / lcd, where the
    student forgot to scale a and c to the common denominator. `mags` carries a, c and the
    lcd (`lcm`)."""
    a, c, lcd = mags.get("a"), mags.get("c"), mags.get("lcm")
    if None in (a, c, lcd) or lcd == 0:
        return None
    return (a + c) / lcd


@_misconception("unit_power_ten")
def _unit_power_ten(mags: dict, correct: float) -> float | None:
    """An off-by-a-power-of-ten unit slip: the correct value is reported ten times too
    large (a decimal-point / unit-prefix error). A distinct, plausible-looking wrong value
    on exactly the right figure."""
    return correct * 10.0


@_misconception("formula_not_rearranged")
def _formula_not_rearranged(mags: dict, correct: float) -> float | None:
    """Plugging into the un-rearranged product formula. For a quantity that should be a
    QUOTIENT of the two givens (t = s/v, I = U/R), the student multiplies them instead:
    value = g1 · g2. `mags` carries the two given magnitudes as g1, g2."""
    g1, g2 = mags.get("g1"), mags.get("g2")
    if g1 is None or g2 is None:
        return None
    return g1 * g2


@_misconception("parallel_as_series")
def _parallel_as_series(mags: dict, correct: float) -> float | None:
    """Parallel resistors added like a series: R = ΣRᵢ instead of the harmonic sum.
    `mags['sum']` carries the plain sum of the drawn resistor values."""
    s = mags.get("sum")
    return s


@_misconception("subscript_ignored")
def _subscript_ignored(mags: dict, correct: float) -> float | None:
    """Molar mass with every subscript read as 1 (H₂O counted as H·O). `mags['flat']`
    carries the molar mass computed with all atom counts set to 1."""
    return mags.get("flat")


# --- the builder: run transforms → guarantee → shuffle ------------------------
class MCResult:
    """The built MC: shuffled option strings, the correct option's index, and the derived
    distractor records (text + which misconception each probes) in option order."""

    __slots__ = ("options", "correct_index", "distractors")

    def __init__(self, options: list[str], correct_index: int,
                 distractors: list[Distractor]):
        self.options = options
        self.correct_index = correct_index
        self.distractors = distractors


def build_distractors(spec: MCSpec, rng, *, want: int = 3) -> MCResult:
    """Compute up to `want` correct-by-construction distractors for `spec`, apply the three
    guarantees, then deterministically shuffle the correct option in among them.

    Deterministic in `rng` (the same seed → the same shuffle), so a variant is reproducible.
    `rng` is a `random.Random`. Returns an `MCResult`; raises `ValueError` if fewer than one
    distractor survives (the recipe declared a degenerate MC — the caller resamples)."""
    correct_text = format_value(spec.correct, spec)
    seen = {correct_text}                              # ≠-correct + pairwise-distinct in one set
    kept: list[Distractor] = []
    for mid in spec.applicable:
        if len(kept) >= want:
            break
        fn = _TRANSFORMS.get(mid)
        if fn is None:                                 # a spec named an id with no transform
            raise KeyError(f"no transform registered for misconception {mid!r}")
        value = fn(dict(spec.magnitudes), spec.correct)
        if value is None:
            continue                                   # the error yields no distinct value here
        if spec.nonneg and value < 0:
            continue                                   # plausibility gate: impossible value
        text = format_value(value, spec)
        if text in seen:                               # == correct, or duplicate distractor
            continue
        seen.add(text)
        kept.append(Distractor(text=text, misconception_id=mid))

    if not kept:
        raise ValueError("no valid distractor survived the ≠/dedupe/plausibility gates")

    # deterministically place the correct option among the distractors
    options = [d.text for d in kept]
    correct_index = rng.randint(0, len(options))
    options.insert(correct_index, correct_text)
    return MCResult(options=options, correct_index=correct_index, distractors=kept)
