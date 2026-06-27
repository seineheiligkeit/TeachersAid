"""Parametric variant + solution engine (Maths) — schema/parametric.py in action.

A `ParametricTask` references a `recipe` registered here (like an asset `@_generator`).
A recipe OWNS sampling + solving: given a seeded RNG it returns an `Instance` (slot values
+ derived answer + worked steps), using **sympy** so the maths is exact and computed, never
authored — `make_variants(task, n)` therefore yields N correct variants, each with its
Rechenweg. Deterministic: the same seed → the same instance. A recipe raises `Unsuitable`
to reject a degenerate draw (e.g. a non-integer solution) and be resampled.
"""

from __future__ import annotations

import random
import re

from sympy import Eq, Integer, Rational, latex, symbols

from ..schema.blocks import SolutionStep, TaskBlock
from ..schema.parametric import Instance, ParametricTask
from ..schema.response import LinesResponse
from ..schema.richtext import InlineRun, RichText

_RECIPES: dict = {}


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


def instantiate(task: ParametricTask, seed: int) -> TaskBlock:
    """Build one concrete TaskBlock for `seed` (deterministic)."""
    rng = random.Random(seed)
    recipe = _RECIPES.get(task.recipe)
    if recipe is None:
        raise ValueError(f"unknown parametric recipe {task.recipe!r}")
    inst = None
    for _ in range(500):
        try:
            inst = recipe(rng)
            break
        except Unsuitable:
            continue
    if inst is None:
        raise RuntimeError(f"recipe {task.recipe}: no valid instance in 500 tries")
    prompt = _template_to_richtext(task.prompt_template.format(**inst.params))
    return TaskBlock(
        id=f"{task.id}#{seed}", kind=task.kind, prompt=prompt,
        response=task.response or LinesResponse(n=2),
        cognitive_level=task.cognitive_level, dimensions=list(task.dimensions),
        content_area=task.content_area, serves=list(task.serves),
        est_minutes=task.est_minutes, answer_key=inst.answer, solution_steps=inst.steps,
    )


def make_variants(task: ParametricTask, n: int, *, seed0: int = 1) -> list[TaskBlock]:
    """N distinct, correct-by-construction variants of one template."""
    return [instantiate(task, seed0 + i) for i in range(n)]


# --- recipes (sympy: exact, with a worked Rechenweg) -------------------------
@_recipe("linear_equation")
def _linear_equation(rng: random.Random) -> Instance:
    """Solve a·x + b = c for x; coefficients chosen so x is a whole number."""
    x = symbols("x")
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
                    answer=[_math(latex(Eq(x, Integer(xs))))], steps=steps)


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
