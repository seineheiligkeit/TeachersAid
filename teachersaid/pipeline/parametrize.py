"""Parametric variant + solution engine (Maths) — schema/parametric.py in action.

A `ParametricTask` references a `recipe` registered here (like an asset `@_generator`).
A recipe OWNS sampling + solving: given a seeded RNG it returns an `Instance` (slot values
+ derived answer + worked steps), using **sympy** so the maths is exact and computed, never
authored — `make_variants(task, n)` therefore yields N correct variants, each with its
Rechenweg. Deterministic: the same seed → the same instance. A recipe raises `Unsuitable`
to reject a degenerate draw (e.g. a non-integer solution) and be resampled.

Difficulty knob (Übungsreihe ramp): a recipe MAY accept an optional `difficulty` (1–3)
keyword where a real hardness ladder exists (`linear_equation` by coefficient size + sign
handling; the chemistry recipes by item structure — see `pipeline/chemistry.py`). Recipes
without the parameter simply ignore a ramp request: `instantiate` inspects the signature
and never passes the knob to a recipe that lacks it, and only a recipe that actually
delivered a band stamps `Instance.difficulty` (an ignored request must not fake a spread).
`make_variants(..., ramp=True)` requests ascending bands (n=6 → 2·leicht/2·mittel/2·schwer).

Context frames: a recipe may also set `Instance.context` — a curated, digit-free sentence
keyed to the DRAWN item (selected from grounding, never authored) — which `instantiate`
prefixes to the prompt.
"""

from __future__ import annotations

import inspect
import math
import random
import re

from sympy import (
    Eq, Integer, Matrix, N, Rational, acos, binomial, diff, integrate, latex,
    linsolve, pi, solve, sqrt, symbols,
)

from ..schema.blocks import MultipleChoicePayload, SolutionStep, TaskBlock
from ..schema.parametric import Instance, MCSpec, ParametricTask
from ..schema.response import ChoicesResponse, LinesResponse
from ..schema.richtext import InlineRun, RichText

_RECIPES: dict = {}

# Option letters for a multiple_choice variant (A, B, C, …).
_MC_LETTERS = "ABCDEFGH"


def _recipe(rid: str):
    def reg(fn):
        _RECIPES[rid] = fn
        return fn
    return reg


class Unsuitable(Exception):
    """A recipe rejects this draw (degenerate) → resample with the next RNG state."""


def _math(latex_str: str) -> InlineRun:
    return InlineRun(text=latex_str, math=True)


_MATH_SPAN = re.compile(r"\$(.+?)\$")


def _template_to_richtext(filled: str) -> RichText:
    """Split a filled prompt on `$…$` spans → inline math runs; the rest is plain text."""
    parts: list[InlineRun] = []
    i = 0
    for m in _MATH_SPAN.finditer(filled):
        if m.start() > i:
            parts.append(InlineRun(text=filled[i:m.start()]))
        parts.append(_math(m.group(1).strip()))
        i = m.end()
    if i < len(filled):
        parts.append(InlineRun(text=filled[i:]))
    if not parts:
        return ""
    if len(parts) == 1 and not parts[0].math:
        return parts[0].text
    return parts


def _accepts_difficulty(recipe) -> bool:
    return "difficulty" in inspect.signature(recipe).parameters


def _mc_fields(inst: Instance, rng: random.Random) -> dict:
    """Build the multiple_choice TaskBlock fields from a recipe's `Instance.mc` request.

    Runs the misconception engine (`pipeline/misconceive`): each distractor is COMPUTED by
    applying a catalogued misconception to the SAME drawn numbers, guaranteed ≠ the correct
    answer, deduped, plausibility-gated; the correct option is shuffled in deterministically
    (using `rng`, whose state is fixed by the seed). Sets `payload` (labelled options) +
    `response` (`choices`), the `answer_key` naming the correct letter, and — the payoff —
    one `watch_out` per distractor naming which misconception it probes ("B prüft:
    Vorzeichenfehler"). Mutates `inst.mc_distractors` with the derived records. Raises
    `Unsuitable` if the engine could not build a valid MC (→ the seed is resampled)."""
    from ..grounding import misconceptions as _cat
    from . import misconceive as _mis

    spec = inst.mc
    try:
        res = _mis.build_distractors(spec, rng)
    except ValueError as exc:                          # degenerate MC → resample this seed
        raise Unsuitable from exc

    n = len(res.options)
    letters = _MC_LETTERS[:n]
    options = [f"{letters[i]}) {opt}" for i, opt in enumerate(res.options)]
    correct_letter = letters[res.correct_index]

    # record the derived distractors in the DISPLAYED option order (with their letters)
    text_to_letter = {opt: letters[i] for i, opt in enumerate(res.options)}
    inst.mc_distractors = list(res.distractors)

    # the teacher-guide "which misconception each distractor probes" lines (the payoff).
    # One per distractor, in option order: the curated German name + a short source tag
    # ("B prüft: Vorzeichenfehler (Radatz)"). The full description stays in the catalog.
    watch_outs: list[str] = []
    for d in res.distractors:
        m = _cat.get(d.misconception_id)
        # the source's lead author(s) — the text before the first "(" year, trimmed
        src = m.source.split("(")[0].strip().rstrip(",") or m.source
        letter = text_to_letter[d.text]
        watch_outs.append(f"{letter} prüft: {m.name} ({src})")

    answer_key = f"{correct_letter}) {res.options[res.correct_index]} (richtig)"
    return {
        "payload": MultipleChoicePayload(options=options, select=spec.select),
        "response": ChoicesResponse(options=list(letters), select=spec.select),
        "answer_key": answer_key,
        "watch_outs": watch_outs,
    }


def instantiate(task: ParametricTask, seed: int, *,
                difficulty: int | None = None) -> TaskBlock:
    """Build one concrete TaskBlock for `seed` (deterministic). `difficulty` (1–3) is
    passed only to recipes that declare the knob; others are drawn unchanged (the ramp
    request is honestly ignored — see the module docstring). The block's `difficulty`
    comes from what the recipe DELIVERED (`Instance.difficulty`), never the request.

    If the recipe's Instance carries an `mc` request, the block is emitted as a
    `multiple_choice` task with correct-by-construction misconception distractors (see
    `_mc_fields`); otherwise it is the ordinary open/lines task."""
    rng = random.Random(seed)
    recipe = _RECIPES.get(task.recipe)
    if recipe is None:
        raise ValueError(f"unknown parametric recipe {task.recipe!r}")
    pass_difficulty = difficulty is not None and _accepts_difficulty(recipe)
    inst = None
    for _ in range(500):
        try:
            inst = recipe(rng, difficulty=difficulty) if pass_difficulty else recipe(rng)
            if inst.mc is not None:                    # MC path: may reject a degenerate draw
                mc = _mc_fields(inst, rng)
            else:
                mc = None
            break
        except Unsuitable:
            inst = None
            continue
    if inst is None:
        raise RuntimeError(f"recipe {task.recipe}: no valid instance in 500 tries")
    filled = task.prompt_template.format(**inst.params)
    if inst.context:                               # curated, digit-free item context
        filled = f"{inst.context} {filled}"
    prompt = _template_to_richtext(filled)
    fields = dict(
        id=f"{task.id}#{seed}", kind=task.kind, prompt=prompt,
        response=task.response or LinesResponse(n=2),
        cognitive_level=task.cognitive_level, dimensions=list(task.dimensions),
        content_area=task.content_area, serves=list(task.serves),
        est_minutes=task.est_minutes, answer_key=inst.answer, solution_steps=inst.steps,
        difficulty=inst.difficulty,
    )
    if mc is not None:                                 # override for the MC projection
        fields.update(mc)
    return TaskBlock(**fields)


def ramp_bands(n: int) -> list[int]:
    """Ascending difficulty bands for an n-variant Übungsreihe, as even as possible:
    n=6 → [1,1,2,2,3,3]; n=4 → [1,1,2,3]. Deterministic in n."""
    return [1 + (3 * i) // n for i in range(n)]


def make_variants(task: ParametricTask, n: int, *, seed0: int = 1,
                  ramp: bool = False) -> list[TaskBlock]:
    """N variants of one template, preferring distinct prompts. Recipes with a small
    finite draw space (e.g. the qualitative chemistry tables) can repeat across
    independent seeds; we skip a seed whose prompt duplicates an earlier one, then top
    up with repeats if the pool is genuinely smaller than n. Deterministic: same
    (task, n, seed0, ramp) → same list.

    `ramp=True` requests ascending difficulty bands (see `ramp_bands`) from recipes
    that support the knob — the Übungsreihe form: start leicht, end anspruchsvoll.
    Recipes without the knob ignore the request, so ramp is safe on any template."""
    out: list[TaskBlock] = []
    seen: set[str] = set()
    seed = seed0
    bands: list[int | None] = list(ramp_bands(n)) if ramp else [None] * n
    budget = seed0 + max(n * 20, 40)              # bounded search for distinct prompts
    for band in bands:
        while seed < budget:                      # find a distinct prompt for this slot
            blk = instantiate(task, seed, difficulty=band)
            seed += 1
            key = str(blk.prompt)
            if key not in seen:
                seen.add(key)
                out.append(blk)
                break
        else:                                     # pool exhausted → allow a repeat
            out.append(instantiate(task, seed, difficulty=band))
            seed += 1
    return out


# --- recipes (sympy: exact, with a worked Rechenweg) -------------------------
@_recipe("linear_equation")
def _linear_equation(rng: random.Random, difficulty: int | None = None) -> Instance:
    """Solve a·x + b = c for x; coefficients chosen so x is a whole number.

    Difficulty knob (coefficient size + sign handling): 1 = small positive
    coefficients, positive solution; 2/None = the classic mixed-sign draw;
    3 = larger coefficients AND a negative solution or constant (sign work)."""
    x = symbols("x")
    if difficulty == 1:
        a = rng.randint(2, 5)
        xs = rng.randint(1, 9)
        b = rng.randint(1, 9)
    elif difficulty == 3:
        a = rng.randint(6, 14)
        xs = rng.randint(-12, 12)
        b = rng.randint(-25, 25)
        if xs == 0 or (xs > 0 and b >= 0):
            raise Unsuitable                      # band 3 must involve sign handling
    else:
        a = rng.randint(2, 9)
        xs = rng.randint(-9, 9)
        if xs == 0:
            raise Unsuitable
        b = rng.randint(-12, 12)
    c = a * xs + b
    steps = [
        SolutionStep(text="Ausgangsgleichung", expr=latex(Eq(a * x + b, c))),
        SolutionStep(text="den konstanten Term auf die rechte Seite bringen",
                     expr=latex(Eq(a * x, c - b))),
        SolutionStep(text="durch den Koeffizienten dividieren",
                     expr=latex(Eq(x, Rational(c - b, a)))),
    ]
    return Instance(params={"eq": latex(Eq(a * x + b, c))},
                    answer=[_math(latex(Eq(x, Integer(xs))))], steps=steps,
                    difficulty=difficulty)


@_recipe("percentage")
def _percentage(rng: random.Random) -> Instance:
    """Wie viel sind p % von G? — Prozentrechnung (Grundwert → Prozentwert)."""
    base = rng.choice([40, 50, 60, 80, 120, 150, 200, 240, 300, 400, 500])
    pct = rng.choice([5, 10, 15, 20, 25, 30, 40, 50, 75])
    res = Rational(base * pct, 100)
    steps = [
        SolutionStep(text=f"{pct} % als Bruch schreiben",
                     expr=latex(Eq(symbols("p"), Rational(pct, 100)))),
        SolutionStep(text="mit dem Grundwert multiplizieren",
                     expr=f"{latex(Rational(pct, 100))} \\cdot {base} = {latex(res)}"),
    ]
    return Instance(params={"pct": pct, "base": base},
                    answer=[_math(latex(res))], steps=steps)


@_recipe("linear_equation_both_sides")
def _linear_both(rng: random.Random) -> Instance:
    """Solve a·x + b = c·x + d (variable on both sides) for x; whole-number solution."""
    x = symbols("x")
    a, c = rng.randint(2, 8), rng.randint(1, 7)
    if a == c:
        raise Unsuitable
    xs = rng.randint(-8, 8)
    if xs == 0:
        raise Unsuitable
    b = rng.randint(-10, 10)
    d = (a - c) * xs + b
    eq = Eq(a * x + b, c * x + d)
    steps = [
        SolutionStep(text="Ausgangsgleichung", expr=latex(eq)),
        SolutionStep(text="Variablen auf eine, Zahlen auf die andere Seite",
                     expr=latex(Eq((a - c) * x, d - b))),
        SolutionStep(text="durch den Koeffizienten dividieren",
                     expr=latex(Eq(x, Rational(d - b, a - c)))),
    ]
    return Instance(params={"eq": latex(eq)},
                    answer=[_math(latex(Eq(x, Integer(xs))))], steps=steps)


@_recipe("percentage_rate")
def _percentage_rate(rng: random.Random) -> Instance:
    """Welcher Prozentsatz? — X von Y sind wie viel %? (the Prozentsatz case)."""
    base = rng.choice([20, 25, 40, 50, 80, 200, 400, 500])
    rate = rng.choice([5, 10, 15, 20, 25, 40, 50, 75])
    part = base * rate
    if part % 100:
        raise Unsuitable
    part //= 100
    steps = [
        SolutionStep(text="Anteil als Bruch", expr=f"\\frac{{{part}}}{{{base}}}"),
        SolutionStep(text="in Prozent umrechnen (mit 100 multiplizieren)",
                     expr=f"\\frac{{{part}}}{{{base}}} \\cdot 100 = {rate}"),
    ]
    return Instance(params={"part": part, "base": base},
                    answer=f"{rate} %", steps=steps)


@_recipe("proportion")
def _proportion(rng: random.Random) -> Instance:
    """Direkte Proportionalität (Dreisatz): n1 Einheiten kosten v1 €, was kosten n2?"""
    einheit = rng.choice(["kg Äpfel", "Hefte", "Liter Saft", "m Stoff", "Packungen"])
    unit = rng.randint(2, 9)
    n1, n2 = rng.randint(2, 6), rng.randint(2, 9)
    if n1 == n2:
        raise Unsuitable
    v1, result = unit * n1, unit * n2
    steps = [
        SolutionStep(text=f"Preis für 1 ({einheit}): durch {n1} dividieren",
                     expr=f"\\frac{{{v1}}}{{{n1}}} = {unit}"),
        SolutionStep(text=f"Preis für {n2}: mit {n2} multiplizieren",
                     expr=f"{unit} \\cdot {n2} = {result}"),
    ]
    return Instance(params={"n1": n1, "v1": v1, "n2": n2, "einheit": einheit},
                    answer=f"{result} €", steps=steps)


_TRIPLES = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15),
            (7, 24, 25), (20, 21, 29), (9, 40, 41), (12, 16, 20)]


@_recipe("pythagoras")
def _pythagoras(rng: random.Random) -> Instance:
    """Hypotenuse aus zwei Katheten (pythagoräische Tripel → ganzzahlig)."""
    a, b, c = rng.choice(_TRIPLES)
    if rng.random() < 0.5:
        a, b = b, a
    steps = [
        SolutionStep(text="Satz des Pythagoras", expr="c^2 = a^2 + b^2"),
        SolutionStep(text="Katheten einsetzen",
                     expr=f"c^2 = {a}^2 + {b}^2 = {a * a + b * b}"),
        SolutionStep(text="Wurzel ziehen", expr=f"c = \\sqrt{{{a * a + b * b}}} = {c}"),
    ]
    return Instance(params={"a": a, "b": b},
                    answer=[_math(f"c = {c}")], steps=steps)


@_recipe("rectangle")
def _rectangle(rng: random.Random) -> Instance:
    """Flächeninhalt und Umfang eines Rechtecks."""
    length = rng.randint(4, 20)
    width = rng.randint(2, length - 1)
    area, peri = length * width, 2 * (length + width)
    steps = [
        SolutionStep(text="Flächeninhalt = Länge · Breite (in cm²)",
                     expr=f"A = {length} \\cdot {width} = {area}"),
        SolutionStep(text="Umfang = 2 · (Länge + Breite) (in cm)",
                     expr=f"u = 2 \\cdot ({length} + {width}) = {peri}"),
    ]
    return Instance(params={"l": length, "w": width},
                    answer=f"A = {area} cm², u = {peri} cm", steps=steps)


@_recipe("mean_median")
def _mean_median(rng: random.Random) -> Instance:
    """Mittelwert, Median und Spannweite einer kleinen Datenreihe (ganzzahliger Mittelwert)."""
    k = 5
    vals = [rng.randint(1, 20) for _ in range(k)]
    vals[-1] -= sum(vals) % k          # nudge the last value so the mean is whole
    if vals[-1] < 1:
        vals[-1] += k
    total = sum(vals)
    mean = total // k
    ordered = sorted(vals)
    median = ordered[k // 2]
    spread = max(vals) - min(vals)
    steps = [
        SolutionStep(text="Mittelwert = Summe ÷ Anzahl",
                     expr=f"\\frac{{{total}}}{{{k}}} = {mean}"),
        SolutionStep(text=f"geordnet: {', '.join(map(str, ordered))} — Median = mittlerer Wert",
                     expr=f"{median}"),
        SolutionStep(text="Spannweite = größter − kleinster Wert",
                     expr=f"{max(vals)} - {min(vals)} = {spread}"),
    ]
    return Instance(params={"vals": ", ".join(map(str, vals))},
                    answer=f"Mittelwert = {mean}, Median = {median}, Spannweite = {spread}",
                    steps=steps)


@_recipe("fraction_multiply")
def _fraction_multiply(rng: random.Random) -> Instance:
    """Zwei echte Brüche multiplizieren und kürzen."""
    b = rng.choice([2, 3, 4, 5, 6, 8])
    d = rng.choice([2, 3, 4, 5, 6, 8])
    a = rng.randint(1, b - 1)
    c = rng.randint(1, d - 1)
    f1, f2 = Rational(a, b), Rational(c, d)
    prod = f1 * f2
    steps = [
        SolutionStep(text="Zähler mal Zähler, Nenner mal Nenner",
                     expr=f"{latex(f1)} \\cdot {latex(f2)} = \\frac{{{a} \\cdot {c}}}{{{b} \\cdot {d}}}"),
        SolutionStep(text="ausrechnen und kürzen",
                     expr=f"= \\frac{{{a * c}}}{{{b * d}}} = {latex(prod)}"),
    ]
    return Instance(params={"f1": latex(f1), "f2": latex(f2)},
                    answer=[_math(latex(prod))], steps=steps)


@_recipe("fraction_add")
def _fraction_add(rng: random.Random) -> Instance:
    """Add two proper fractions with different denominators; reduce the result."""
    b = rng.choice([2, 3, 4, 5, 6, 8])
    d = rng.choice([2, 3, 4, 5, 6, 8])
    if b == d:
        raise Unsuitable
    a = rng.randint(1, b - 1)
    c = rng.randint(1, d - 1)
    f1, f2 = Rational(a, b), Rational(c, d)
    total = f1 + f2
    common = b * d // __import__("math").gcd(b, d)
    n1, n2 = a * (common // b), c * (common // d)
    # build the expanded fractions by hand — sympy.Rational would auto-reduce 2/6 → 1/3
    expanded = f"\\frac{{{n1}}}{{{common}}} + \\frac{{{n2}}}{{{common}}}"
    steps = [
        SolutionStep(text="auf den gemeinsamen Nenner erweitern",
                     expr=f"{latex(f1)} + {latex(f2)} = {expanded}"),
        SolutionStep(text="Zähler addieren",
                     expr=f"= \\frac{{{n1 + n2}}}{{{common}}}"),
        SolutionStep(text="kürzen", expr=f"= {latex(total)}"),
    ]
    return Instance(params={"f1": latex(f1), "f2": latex(f2)},
                    answer=[_math(latex(total))], steps=steps)


# === Oberstufe (Sek II) recipes — Analysis, Stochastik, analytische Geometrie =========
# These are the parametric goldmine: the Oberstufe is dominated by symbolically-solvable
# procedures (Ableiten, Integrieren, Gleichungssysteme, Verteilungen, Vektoren), so each
# template → N correct-by-construction variants with an exact Rechenweg.

def _approx(expr, places: int = 2) -> str:
    """A rounded decimal string for a teacher-facing ≈ value (German comma)."""
    return f"{float(N(expr)):.{places}f}".rstrip("0").rstrip(".").replace(".", ",")


@_recipe("polynomial_curve")
def _polynomial_curve(rng: random.Random) -> Instance:
    """Kurvendiskussion einer Polynomfunktion 3. Grades: Extrem- und Wendepunkte.

    f' is built from two distinct, same-parity integer roots → f is an INTEGER-coefficient
    cubic whose extrema sit exactly at those roots and whose Wendestelle is integer; sympy
    then derives the answer from f (so it is correct by construction, not back-filled)."""
    x = symbols("x")
    r1, r2 = rng.randint(-4, 4), rng.randint(-4, 4)
    if r1 == r2 or (r1 + r2) % 2 != 0:
        raise Unsuitable
    if r1 > r2:
        r1, r2 = r2, r1
    c = rng.choice([-2, -1, 0, 1, 2])
    f = x**3 - (3 * (r1 + r2) // 2) * x**2 + 3 * r1 * r2 * x + c
    f1, f2 = diff(f, x), diff(f, x, 2)
    crit = sorted(solve(f1, x))
    pts = []  # (kind, x, y)
    for r in crit:
        kind = "Tiefpunkt" if f2.subs(x, r) > 0 else "Hochpunkt"
        pts.append((kind, r, f.subs(x, r)))
    wx = solve(f2, x)[0]
    wy = f.subs(x, wx)
    extrema_tex = ", \\; ".join(
        f"\\text{{{k[:1]}}}({latex(px)} \\mid {latex(py)})" for k, px, py in pts)
    steps = [
        SolutionStep(text="Funktion", expr=latex(Eq(symbols("f(x)"), f))),
        SolutionStep(text="1. Ableitung; Extremstellen aus f'(x) = 0",
                     expr=f"f'(x) = {latex(f1)} = 0 \\Rightarrow x \\in \\{{{', '.join(latex(r) for r in crit)}\\}}"),
        SolutionStep(text="2. Ableitung; Art über das Vorzeichen von f''",
                     expr=f"f''(x) = {latex(f2)}"),
        SolutionStep(text="Extrempunkte",
                     expr=";\\; ".join(f"\\text{{{k}}}\\,({latex(px)} \\mid {latex(py)})" for k, px, py in pts)),
        SolutionStep(text="Wendestelle aus f''(x) = 0",
                     expr=f"f''(x) = 0 \\Rightarrow x = {latex(wx)},\\quad W({latex(wx)} \\mid {latex(wy)})"),
    ]
    answer = [_math(extrema_tex + f", \\; W({latex(wx)} \\mid {latex(wy)})")]
    return Instance(params={"fx": latex(f)}, answer=answer, steps=steps)


@_recipe("definite_integral")
def _definite_integral(rng: random.Random) -> Instance:
    """Bestimmtes Integral einer Polynomfunktion über den Hauptsatz (Stammfunktion einsetzen)."""
    x = symbols("x")
    a2, a1, a0 = rng.randint(1, 3), rng.randint(-3, 3), rng.randint(-3, 3)
    f = a2 * x**2 + a1 * x + a0
    lo = rng.randint(-2, 2)
    hi = lo + rng.randint(1, 4)
    F = integrate(f, x)
    val = integrate(f, (x, lo, hi))
    steps = [
        SolutionStep(text="Stammfunktion bilden", expr=f"F(x) = {latex(F)}"),
        SolutionStep(text="Hauptsatz: F(obere Grenze) − F(untere Grenze)",
                     expr=f"\\int_{{{lo}}}^{{{hi}}} ({latex(f)})\\,dx = F({hi}) - F({lo})"),
        SolutionStep(text="einsetzen und berechnen",
                     expr=f"= {latex(F.subs(x, hi))} - ({latex(F.subs(x, lo))}) = {latex(val)}"),
    ]
    return Instance(params={"f": latex(f), "lo": lo, "hi": hi},
                    answer=[_math(f"\\int_{{{lo}}}^{{{hi}}} ({latex(f)})\\,dx = {latex(val)}")],
                    steps=steps)


@_recipe("linear_system_2")
def _linear_system_2(rng: random.Random) -> Instance:
    """Lineares Gleichungssystem in zwei Variablen (eindeutig lösbar, ganzzahlige Lösung)."""
    x, y = symbols("x y")
    x0, y0 = rng.randint(-5, 5), rng.randint(-5, 5)
    a1, b1 = rng.randint(-4, 4), rng.randint(-4, 4)
    a2, b2 = rng.randint(-4, 4), rng.randint(-4, 4)
    if a1 * b2 - a2 * b1 == 0 or (a1 == 0 and b1 == 0) or (a2 == 0 and b2 == 0):
        raise Unsuitable  # det ≠ 0 → genau eine Lösung
    c1, c2 = a1 * x0 + b1 * y0, a2 * x0 + b2 * y0
    eq1, eq2 = Eq(a1 * x + b1 * y, c1), Eq(a2 * x + b2 * y, c2)
    sol = list(linsolve([eq1, eq2], [x, y]))[0]
    steps = [
        SolutionStep(text="Gleichungssystem (I, II)", expr=f"{latex(eq1)};\\quad {latex(eq2)}"),
        SolutionStep(text="z. B. mit dem Eliminationsverfahren lösen",
                     expr=f"x = {latex(sol[0])},\\quad y = {latex(sol[1])}"),
    ]
    return Instance(params={"eq1": latex(eq1), "eq2": latex(eq2)},
                    answer=[_math(f"x = {latex(sol[0])},\\; y = {latex(sol[1])}")], steps=steps)


@_recipe("linear_system_3")
def _linear_system_3(rng: random.Random) -> Instance:
    """Lineares Gleichungssystem in drei Variablen (eindeutig lösbar, ganzzahlige Lösung)."""
    x, y, z = symbols("x y z")
    x0, y0, z0 = (rng.randint(-4, 4) for _ in range(3))
    A = Matrix(3, 3, lambda i, j: rng.randint(-3, 3))
    if A.det() == 0:
        raise Unsuitable
    rhs = A * Matrix([x0, y0, z0])
    eqs = [Eq(A[i, 0] * x + A[i, 1] * y + A[i, 2] * z, rhs[i]) for i in range(3)]
    sol = list(linsolve(eqs, [x, y, z]))[0]
    steps = [
        SolutionStep(text="Gleichungssystem (I, II, III)",
                     expr=";\\; ".join(latex(e) for e in eqs)),
        SolutionStep(text="mit dem Gauß-Verfahren stufenweise eliminieren und rücksubstituieren",
                     expr=f"x = {latex(sol[0])},\\; y = {latex(sol[1])},\\; z = {latex(sol[2])}"),
    ]
    return Instance(params={"eq1": latex(eqs[0]), "eq2": latex(eqs[1]), "eq3": latex(eqs[2])},
                    answer=[_math(f"x = {latex(sol[0])},\\; y = {latex(sol[1])},\\; z = {latex(sol[2])}")],
                    steps=steps)


@_recipe("binomial_distribution")
def _binomial_distribution(rng: random.Random) -> Instance:
    """Binomialverteilung: P(X=k), P(X≤k), Erwartungswert und Standardabweichung (exakt)."""
    n = rng.choice([5, 6, 8, 10])
    num, den = rng.choice([(1, 2), (1, 3), (1, 4), (1, 5), (2, 5), (3, 4), (3, 5)])
    p = Rational(num, den)
    k = rng.randint(1, n - 1)
    P = binomial(n, k) * p**k * (1 - p) ** (n - k)
    Pcum = sum(binomial(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))
    E = n * p
    sigma = sqrt(n * p * (1 - p))
    steps = [
        SolutionStep(text="Binomialformel",
                     expr=f"P(X=k) = \\binom{{n}}{{k}} p^k (1-p)^{{n-k}}"),
        SolutionStep(text=f"n = {n},\\; p = {latex(p)},\\; k = {k} einsetzen",
                     expr=f"P(X={k}) = \\binom{{{n}}}{{{k}}} \\left({latex(p)}\\right)^{{{k}}} "
                          f"\\left({latex(1 - p)}\\right)^{{{n - k}}} = {latex(P)} \\approx {_approx(P, 3)}"),
        SolutionStep(text="Erwartungswert und Standardabweichung",
                     expr=f"E(X) = n p = {latex(E)};\\quad \\sigma = \\sqrt{{n p (1-p)}} = {latex(sigma)} \\approx {_approx(sigma)}"),
    ]
    answer = [
        _math(f"P(X={k}) = {latex(P)} \\approx {_approx(P, 3)}"),
        InlineRun(text=";  "),
        _math(f"P(X \\leq {k}) = {latex(Pcum)} \\approx {_approx(Pcum, 3)}"),
        InlineRun(text=";  "),
        _math(f"E(X) = {latex(E)},\\; \\sigma \\approx {_approx(sigma)}"),
    ]
    return Instance(params={"n": n, "k": k, "p": latex(p)}, answer=answer, steps=steps)


@_recipe("vector_dot_angle")
def _vector_dot_angle(rng: random.Random) -> Instance:
    """Skalarprodukt zweier Vektoren in ℝ², Beträge und der eingeschlossene Winkel."""
    ax, ay = rng.randint(-5, 5), rng.randint(-5, 5)
    bx, by = rng.randint(-5, 5), rng.randint(-5, 5)
    if (ax == 0 and ay == 0) or (bx == 0 and by == 0):
        raise Unsuitable
    dot = ax * bx + ay * by
    na, nb = sqrt(ax**2 + ay**2), sqrt(bx**2 + by**2)
    cos_phi = Rational(dot) / (na * nb)
    phi_deg = _approx(acos(cos_phi) * 180 / pi, 1)
    # \binom renders a parenthesised column (mathtext-safe; \begin{pmatrix} is not).
    va = f"\\vec a = \\binom{{{ax}}}{{{ay}}}"
    vb = f"\\vec b = \\binom{{{bx}}}{{{by}}}"
    steps = [
        SolutionStep(text="Skalarprodukt: komponentenweise multiplizieren und addieren",
                     expr=f"\\vec a \\cdot \\vec b = {ax}\\cdot{bx} + {ay}\\cdot{by} = {dot}"),
        SolutionStep(text="Beträge der Vektoren",
                     expr=f"|\\vec a| = {latex(na)},\\quad |\\vec b| = {latex(nb)}"),
        SolutionStep(text="Winkel über das Skalarprodukt",
                     expr=f"\\cos\\varphi = \\frac{{\\vec a \\cdot \\vec b}}{{|\\vec a|\\,|\\vec b|}} "
                          f"= {latex(cos_phi)} \\Rightarrow \\varphi \\approx {phi_deg}^\\circ"),
    ]
    answer = [_math(f"\\vec a \\cdot \\vec b = {dot},\\; |\\vec a| = {latex(na)},\\; "
                    f"|\\vec b| = {latex(nb)},\\; \\varphi \\approx {phi_deg}^\\circ")]
    return Instance(params={"va": va, "vb": vb}, answer=answer, steps=steps)


# === Misconception-MC recipes (roadmap A3) ===========================================
# Each draws exactly like its open-answer twin, but ALSO declares an `MCSpec`: the drawn
# magnitudes + correct value + which catalogued misconceptions apply + the answer's own
# formatting. `instantiate` then emits a multiple_choice TaskBlock whose distractors are
# COMPUTED (pipeline/misconceive) by applying those misconceptions to the same numbers —
# correct-by-construction wrong options, each named in the teacher guide. These live here
# (not in chemistry.py/physics.py, which stay read-only) and read grounding directly.

# small German-number helpers local to the MC recipes (kept independent of physics.py)
def _de(value, dp: int = 2) -> str:
    """German decimal (comma), trailing zeros trimmed; whole numbers without a decimal."""
    f = float(value)
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    return f"{f:.{dp}f}".rstrip("0").rstrip(".").replace(".", ",")


def _M_de(value, dp: int = 2) -> str:
    """German decimal with a fixed dp (for molar masses in the Rechenweg)."""
    return f"{float(value):.{dp}f}".replace(".", ",")


@_recipe("linear_equation_mc")
def _linear_equation_mc(rng: random.Random) -> Instance:
    """Löse a·x + b = c — als Multiple-Choice mit Fehler-Distraktoren (Vorzeichenfehler,
    verwechselte Umkehroperation). x ganzzahlig; die falschen Optionen sind die Werte, die
    genau diese Fehler auf denselben Zahlen liefern."""
    x = symbols("x")
    a = rng.randint(2, 9)
    xs = rng.randint(-9, 9)
    if xs == 0:
        raise Unsuitable
    b = rng.randint(-12, 12)
    if b == 0:                                         # b=0 → sign error yields the same value
        raise Unsuitable
    c = a * xs + b
    steps = [
        SolutionStep(text="Ausgangsgleichung", expr=latex(Eq(a * x + b, c))),
        SolutionStep(text="den konstanten Term auf die rechte Seite bringen",
                     expr=latex(Eq(a * x, c - b))),
        SolutionStep(text="durch den Koeffizienten dividieren",
                     expr=latex(Eq(x, Rational(c - b, a)))),
    ]
    mc = MCSpec(magnitudes={"a": float(a), "b": float(b), "c": float(c)},
                correct=float(xs), applicable=["sign_error", "inverse_operation"],
                prefix="x = ", dp=2)
    return Instance(params={"eq": latex(Eq(a * x + b, c))},
                    answer=[_math(latex(Eq(x, Integer(xs))))], steps=steps, mc=mc)


@_recipe("percentage_mc")
def _percentage_mc(rng: random.Random) -> Instance:
    """Wie viel sind p % von G? — als Multiple-Choice mit Fehler-Distraktoren
    (Prozentbasis verwechselt, Einheitenfehler um eine Zehnerpotenz)."""
    base = rng.choice([40, 50, 60, 80, 120, 150, 200, 240, 300, 400, 500])
    pct = rng.choice([5, 10, 15, 20, 25, 30, 40, 50, 75])
    res = Rational(base * pct, 100)
    steps = [
        SolutionStep(text=f"{pct} % als Bruch schreiben",
                     expr=latex(Eq(symbols("p"), Rational(pct, 100)))),
        SolutionStep(text="mit dem Grundwert multiplizieren",
                     expr=f"{latex(Rational(pct, 100))} \\cdot {base} = {latex(res)}"),
    ]
    mc = MCSpec(magnitudes={"base": float(base), "pct": float(pct)},
                correct=float(res),
                applicable=["percent_base_confusion", "unit_power_ten"],
                dp=2, nonneg=True)
    return Instance(params={"pct": pct, "base": base},
                    answer=f"{latex(res)}", steps=steps, mc=mc)


@_recipe("fraction_add_mc")
def _fraction_add_mc(rng: random.Random) -> Instance:
    """a/b + c/d (verschiedene Nenner) — als Multiple-Choice mit den beiden klassischen
    Bruch-Additionsfehlern: Zähler+Zähler/Nenner+Nenner, und Zähler nicht miterweitert.
    Die richtige Option und die Distraktoren sind exakte Brüche."""
    b = rng.choice([2, 3, 4, 5, 6, 8])
    d = rng.choice([2, 3, 4, 5, 6, 8])
    if b == d:
        raise Unsuitable
    a = rng.randint(1, b - 1)
    c = rng.randint(1, d - 1)
    f1, f2 = Rational(a, b), Rational(c, d)
    total = f1 + f2
    lcm = b * d // math.gcd(b, d)
    n1, n2 = a * (lcm // b), c * (lcm // d)
    expanded = f"\\frac{{{n1}}}{{{lcm}}} + \\frac{{{n2}}}{{{lcm}}}"
    steps = [
        SolutionStep(text="auf den gemeinsamen Nenner erweitern",
                     expr=f"{latex(f1)} + {latex(f2)} = {expanded}"),
        SolutionStep(text="Zähler addieren", expr=f"= \\frac{{{n1 + n2}}}{{{lcm}}}"),
        SolutionStep(text="kürzen", expr=f"= {latex(total)}"),
    ]
    mc = MCSpec(magnitudes={"a": float(a), "b": float(b), "c": float(c),
                            "d": float(d), "lcm": float(lcm)},
                correct=float(total),
                applicable=["fraction_add_across", "fraction_keep_numerators"],
                as_fraction=True, nonneg=True)
    return Instance(params={"f1": latex(f1), "f2": latex(f2)},
                    answer=[_math(latex(total))], steps=steps, mc=mc)


@_recipe("ohm_mc")
def _ohm_mc(rng: random.Random) -> Instance:
    """Ohm'sches Gesetz, nach I gefragt (I = U/R) — als Multiple-Choice. Der Leit-Distraktor
    ist der klassische Fehler „Formel nicht umgestellt“: U·R statt U/R (dazu ein
    Zehnerpotenz-Einheitenfehler auf dem richtigen Wert)."""
    # choose clean U, R so I = U/R is tidy; ask for I (the quotient case, where the
    # un-rearranged-formula error U·R is a distinct wrong value).
    I_val = rng.choice([Rational(1, 4), Rational(1, 2), Integer(1), Integer(2), Integer(4)])
    R_val = rng.choice([5, 10, 20, 25, 50, 100, 200])
    U_val = R_val * I_val                              # exact
    if not (1 <= U_val <= 500):
        raise Unsuitable
    I_f = float(I_val)
    steps = [
        SolutionStep(text="Ohm'sches Gesetz nach I umstellen", expr="I = \\frac{U}{R}"),
        SolutionStep(text="Werte einsetzen",
                     expr=f"I = \\frac{{{_de(U_val)}\\,\\text{{V}}}}{{{_de(R_val)}\\,\\Omega}}"),
        SolutionStep(text="ausrechnen (V/Ω = A)", expr=f"I = {_de(I_f)}\\,\\text{{A}}"),
    ]
    given = (f"An einem Widerstand von {_de(R_val)} Ω liegt die Spannung {_de(U_val)} V. "
             f"Wie groß ist die Stromstärke I?")
    mc = MCSpec(magnitudes={"g1": float(U_val), "g2": float(R_val)},
                correct=I_f, applicable=["formula_not_rearranged", "unit_power_ten"],
                prefix="I = ", unit="A", dp=2, nonneg=True)
    return Instance(params={"aufgabe": given}, answer=f"I = {_de(I_f)} A",
                    steps=steps, mc=mc)


@_recipe("uniform_motion_mc")
def _uniform_motion_mc(rng: random.Random) -> Instance:
    """Gleichförmige Bewegung, nach t gefragt (t = s/v) — als Multiple-Choice. Leit-
    Distraktor: „Formel nicht umgestellt“ (s·v statt s/v), plus Zehnerpotenz-Fehler."""
    v_val = rng.choice([2, 3, 4, 5, 6, 8, 10])          # m/s
    t_val = rng.choice([4, 5, 6, 8, 10, 12, 15, 20])    # s
    s_val = v_val * t_val
    steps = [
        SolutionStep(text="Formel umstellen (nach t)", expr="t = \\frac{s}{v}"),
        SolutionStep(text="Werte einsetzen",
                     expr=f"t = \\frac{{{_de(s_val)}\\,\\text{{m}}}}{{{_de(v_val)}\\,\\frac{{\\text{{m}}}}{{\\text{{s}}}}}}"),
        SolutionStep(text="ausrechnen", expr=f"t = {_de(t_val)}\\,\\text{{s}}"),
    ]
    given = (f"Ein Körper bewegt sich gleichförmig mit {_de(v_val)} m/s und legt "
             f"{_de(s_val)} m zurück. Wie lange ist er unterwegs?")
    mc = MCSpec(magnitudes={"g1": float(s_val), "g2": float(v_val)},
                correct=float(t_val),
                applicable=["formula_not_rearranged", "unit_power_ten"],
                prefix="t = ", unit="s", dp=2, nonneg=True)
    return Instance(params={"aufgabe": given}, answer=f"t = {_de(t_val)} s",
                    steps=steps, mc=mc)


@_recipe("resistors_mc")
def _resistors_mc(rng: random.Random) -> Instance:
    """Ersatzwiderstand einer Parallelschaltung — als Multiple-Choice. DER klassische
    Fehler ist der Leit-Distraktor: parallel wie Reihe addiert (R = ΣRᵢ statt Kehrwerte).
    Draws are constrained so the true parallel value is tidy (≤ one decimal)."""
    pool = [2, 3, 4, 6, 10, 12, 20, 30, 60, 100, 200]
    n = rng.choice([2, 2, 3])
    vals = [rng.choice(pool) for _ in range(n)]
    inv = sum(Rational(1, v) for v in vals)
    Rges = 1 / inv                                      # exact Rational
    if (Rges * 10) != int(Rges * 10):                  # pedagogical-ugliness guard
        raise Unsuitable
    plain_sum = sum(vals)
    if Rges == plain_sum:                              # (can't happen for parallel, but guard)
        raise Unsuitable
    inv_terms = " + ".join(f"\\frac{{1}}{{{v}}}" for v in vals)
    steps = [
        SolutionStep(text="Parallelschaltung: die Kehrwerte addieren sich",
                     expr="\\frac{1}{R_{ges}} = " + inv_terms),
        SolutionStep(text="Kehrwert bilden", expr=f"R_{{ges}} = {_de(float(Rges))}\\,\\Omega"),
    ]
    listing = " und ".join(f"{_de(v)} Ω" for v in vals)
    given = (f"In einer Parallelschaltung liegen die Widerstände {listing}. "
             f"Berechne den Ersatzwiderstand R_ges.")
    mc = MCSpec(magnitudes={"sum": float(plain_sum)},
                correct=float(Rges),
                applicable=["parallel_as_series", "unit_power_ten"],
                prefix="R_ges = ", unit="Ω", dp=2, nonneg=True)
    return Instance(params={"aufgabe": given}, answer=f"R_ges = {_de(float(Rges))} Ω",
                    steps=steps, mc=mc)


@_recipe("molar_mass_mc")
def _molar_mass_mc(rng: random.Random) -> Instance:
    """Molare Masse einer Verbindung — als Multiple-Choice. Leit-Distraktor: die
    Indexzahlen der Summenformel werden ignoriert (H₂O als H·O gezählt). Reads the grounded
    IUPAC masses directly (grounding is fair game; chemistry.py stays untouched)."""
    from ..grounding import chemistry as chem
    # multi-atom formulas only, so ignoring subscripts produces a genuinely different mass
    pool = ["H2O", "CO2", "H2SO4", "CaCO3", "C6H12O6", "Fe2O3", "NH3", "CH4",
            "Al2O3", "Na2CO3", "HNO3"]
    formula = rng.choice(pool)
    counts = chem.parse_formula(formula)
    M = chem.molar_mass(formula)
    M_flat = sum(chem.ATOMIC_MASSES[el] for el in counts)   # each element counted once
    if round(M, 2) == round(M_flat, 2):
        raise Unsuitable                              # no distinct distractor (shouldn't occur)
    sub = chem.subscript(formula)
    rows = [SolutionStep(text=f"{chem.ELEMENT_NAMES.get(el, el)} ({el}): {n} · "
                              f"{_M_de(chem.molar_mass(el))} g/mol = "
                              f"{_M_de(chem.ATOMIC_MASSES[el] * n)} g/mol")
            for el, n in counts.items()]
    rows.append(SolutionStep(text=f"Summe: M = {_M_de(M)} g/mol"))
    mc = MCSpec(magnitudes={"flat": float(M_flat)}, correct=float(M),
                applicable=["subscript_ignored", "unit_power_ten"],
                unit="g/mol", dp=2, nonneg=True)
    return Instance(params={"formel": sub}, answer=f"M({sub}) ≈ {_M_de(M)} g/mol",
                    steps=rows, mc=mc)


# Chemistry recipes register into the same _RECIPES (so make_variants/templates drive
# them uniformly). Imported last so the names above are defined first (no import cycle).
from . import chemistry as _chemistry  # noqa: E402,F401
from . import physics as _physics  # noqa: E402,F401
