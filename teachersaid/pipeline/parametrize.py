"""Parametric variant + solution engine (Maths) — schema/parametric.py in action.

A `ParametricTask` references a `recipe` registered here (like an asset `@_generator`).
A recipe OWNS sampling + solving: given a seeded RNG it returns an `Instance` (slot values
+ derived answer + worked steps), using **sympy** so the maths is exact and computed, never
authored — `make_variants(task, n)` therefore yields N correct variants, each with its
Rechenweg. Deterministic: the same seed → the same instance. A recipe raises `Unsuitable`
to reject a degenerate draw (e.g. a non-integer solution) and be resampled.
"""

from __future__ import annotations

import math
import random
import re

from sympy import (
    Eq, Integer, Matrix, N, Rational, acos, binomial, diff, integrate, latex,
    linsolve, pi, solve, sqrt, symbols,
)

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
    """N variants of one template, preferring distinct prompts. Recipes with a small
    finite draw space (e.g. the qualitative chemistry tables) can repeat across
    independent seeds; we skip a seed whose prompt duplicates an earlier one, then top
    up with repeats if the pool is genuinely smaller than n. Deterministic: same
    (task, n, seed0) → same list."""
    out: list[TaskBlock] = []
    seen: set[str] = set()
    seed = seed0
    budget = seed0 + max(n * 20, 40)              # bounded search for distinct prompts
    while len(out) < n and seed < budget:
        blk = instantiate(task, seed)
        seed += 1
        key = str(blk.prompt)
        if key not in seen:
            seen.add(key)
            out.append(blk)
    while len(out) < n:                           # pool exhausted → allow repeats
        out.append(instantiate(task, seed))
        seed += 1
    return out


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


# Chemistry recipes register into the same _RECIPES (so make_variants/templates drive
# them uniformly). Imported last so the names above are defined first (no import cycle).
from . import chemistry as _chemistry  # noqa: E402,F401


# === Matura-Nachfrage-Pack (FA + WS) ==================================================
# The highest-frequency SRDP demands the corpus scan exposed (Documents/matura-math-
# coverage.md): exponential growth/decay (FA, the #1 demand), and the two WS figures the
# accessible-Matura scan flagged — Boxplot and Baumdiagramm — now as parametric recipes
# with the quartiles / path-probabilities COMPUTED (sympy), never authored. Appended (not
# inserted) so parallel work on this file stays merge-clean.
#
# Load-bearing style rule followed here: the only content inside a `$…$` prompt span or a
# SolutionStep `expr` is DECIMAL-FREE LaTeX (symbolic / integer / fraction) — every German
# decimal comma lives in plain text, never in matplotlib mathtext (which spaces a bare
# comma oddly). This keeps the render test clean without fighting the mathtext subset.
from sympy import log  # natural logarithm — the exponential solve-for-t step


def _de_num(x, dp: int = 2) -> str:
    """German decimal string (comma). Trailing zeros are trimmed only AFTER a decimal
    point, so a whole number like 1700 stays '1700' — unlike `_approx`, whose rstrip('0')
    would eat the trailing zero of an integer result."""
    s = f"{float(x):.{dp}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


# growth/decay stories: (Satz mit {N0}+{p}, Mengeneinheit, Zeit-Dativ, N0-Auswahl, p%-Auswahl)
_EXP_GROWTH = [
    ("Ein Kapital von {N0} € wird jährlich mit {p} % verzinst (Zinseszins).",
     "€", "Jahren", [1000, 1500, 2000, 2500, 3000, 5000], [2, 3, 4, 5]),
    ("Eine Bakterienkultur beginnt mit {N0} Bakterien und wächst pro Stunde um {p} %.",
     "Bakterien", "Stunden", [2000, 4000, 5000, 8000, 10000], [10, 20, 25, 50]),
    ("Eine Stadt hat {N0} Einwohnerinnen und Einwohner; die Bevölkerung wächst pro Jahr um {p} %.",
     "Einwohner", "Jahren", [8000, 12000, 20000, 50000], [2, 3, 5]),
]
_EXP_DECAY = [
    ("Eine Probe enthält {N0} mg eines radioaktiven Stoffes, der pro Jahr um {p} % zerfällt.",
     "mg", "Jahren", [200, 400, 500, 800, 1000], [10, 15, 20, 25]),
    ("{N0} mg eines Medikaments befinden sich im Blut; pro Stunde werden {p} % abgebaut.",
     "mg", "Stunden", [200, 300, 400, 600], [15, 20, 25]),
    ("Ein Auto kostet neu {N0} €; sein Wert sinkt pro Jahr um {p} %.",
     "€", "Jahren", [15000, 20000, 25000, 30000], [10, 15, 20]),
]

# find-rate: N0 is a multiple of 400 (= lcm of the den² of every q below), so N1 = N0·q²
# is always a whole number and q = √(N1/N0) recovers exactly — correct by construction.
_EXP_RATE_Q = [Rational(3, 2), Rational(5, 4), Rational(6, 5),
               Rational(4, 5), Rational(1, 2), Rational(3, 4)]
_EXP_RATE_N0 = [400, 800, 1200, 1600, 2000, 2400]


@_recipe("exponential_model")
def _exponential_model(rng: random.Random) -> Instance:
    """Exponentielles Wachstum/Abnahme N(t) = N0·q^t (Zinseszins · Zerfall · Population).

    Drei Frage-Varianten: den Wert N(t) berechnen · über den Logarithmus die Verdopplungs-
    bzw. Halbwertszeit bestimmen · den Faktor q aus zwei Werten ermitteln. Alles exakt
    (sympy); die Rundung wird im Rechenweg genannt. Aus dem Modell lässt sich via
    matplotlib:function_plot ein Graph/eine Wertetabelle zeichnen (Figurenausgabe ist ein
    späterer Track)."""
    ask = rng.choice(["wert", "zeit", "rate"])

    if ask == "rate":
        q = rng.choice(_EXP_RATE_Q)
        n0 = rng.choice(_EXP_RATE_N0)
        t = 2
        n1 = n0 * q ** t                       # exact whole number
        ratio = Rational(int(n1), n0)
        pct = int((q - 1) * 100)
        richtung = "Zunahme" if q > 1 else "Abnahme"
        aufgabe = (
            "Ein Bestand ändert sich exponentiell nach dem Modell "
            "$N(t) = N_0 \\cdot q^t$. "
            f"Zum Zeitpunkt t = 0 beträgt er {n0}, nach {t} Zeiteinheiten {int(n1)}. "
            "Bestimme den Faktor q pro Zeiteinheit und die prozentuelle Änderung."
        )
        steps = [
            SolutionStep(text="das Modell für beide Zeitpunkte anschreiben und dividieren",
                         expr=f"q^{{{t}}} = \\frac{{{int(n1)}}}{{{n0}}} = {latex(ratio)}"),
            SolutionStep(text="die Wurzel ziehen",
                         expr=f"q = \\sqrt{{{latex(ratio)}}} = {latex(q)}"),
            SolutionStep(text=f"Deutung: q = {_de_num(float(q))} bedeutet eine {richtung} "
                              f"um {abs(pct)} % pro Zeiteinheit."),
        ]
        answer = f"q = {_de_num(float(q))} ({richtung} um {abs(pct)} % pro Zeiteinheit)"
        return Instance(params={"aufgabe": aufgabe}, answer=answer, steps=steps)

    growth = rng.random() < 0.5
    satz, einheit, zeit_dativ, n0s, ps = rng.choice(_EXP_GROWTH if growth else _EXP_DECAY)
    p = rng.choice(ps)
    n0 = rng.choice(n0s)
    q = Rational(100 + p, 100) if growth else Rational(100 - p, 100)
    q_disp = _de_num(float(q))
    lead = (satz.format(N0=n0, p=p)
            + " Für den Bestand gilt $N(t) = N_0 \\cdot q^t$ mit dem Faktor q = " + q_disp + ".")

    if ask == "wert":
        t = rng.randint(3, 8)
        val = float(N(q ** t * n0))
        rounded = round(val)
        aufgabe = lead + (f" Berechne den Bestand nach {t} {zeit_dativ} und runde auf eine "
                          "ganze Zahl.")
        steps = [
            SolutionStep(text="die Werte in das Modell einsetzen",
                         expr=f"N({t}) = {n0} \\cdot q^{{{t}}}"),
            SolutionStep(text=f"mit q = {q_disp} berechnen und runden: "
                              f"N({t}) ≈ {_de_num(val, 2)} ≈ {rounded} {einheit}"),
        ]
        return Instance(params={"aufgabe": aufgabe},
                        answer=f"N({t}) ≈ {rounded} {einheit}", steps=steps)

    # ask == "zeit": Verdopplungszeit (Wachstum) / Halbwertszeit (Abnahme)
    faktor = Rational(2, 1) if growth else Rational(1, 2)
    faktor_disp, ziel = ("2", "verdoppelt") if growth else ("0,5", "halbiert")
    t_val = float(N(log(faktor) / log(q)))
    aufgabe = lead + f" Nach welcher Zeit hat sich der Bestand {ziel} (auf eine Nachkommastelle)?"
    steps = [
        SolutionStep(text=f"Ansatz: der Bestand ist {ziel}", expr=f"q^t = {latex(faktor)}"),
        SolutionStep(text="beide Seiten logarithmieren und nach t auflösen",
                     expr="t = \\frac{\\ln k}{\\ln q}"),
        SolutionStep(text=f"einsetzen (k = {faktor_disp}, q = {q_disp}): der Bestand ist nach "
                          f"etwa {_de_num(t_val, 1)} {zeit_dativ} {ziel}"),
    ]
    answer = f"Der Bestand ist nach etwa {_de_num(t_val, 1)} {zeit_dativ} {ziel} " \
             f"(t ≈ {_de_num(t_val, 1)})."
    return Instance(params={"aufgabe": aufgabe}, answer=answer, steps=steps)


@_recipe("boxplot_from_data")
def _boxplot_from_data(rng: random.Random) -> Instance:
    """Fünf-Punkte-Zusammenfassung (Minimum · Q1 · Median · Q3 · Maximum) + Spannweite +
    Interquartilsabstand einer kleinen Datenliste.

    Die Anzahl ist UNGERADE (n = 11 oder 15), damit die Quartile nach der Schulmethode
    (Median der jeweiligen Hälfte OHNE den Gesamtmedian; beide Hälften sind dann ungerade
    lang) eindeutig einzelne Datenwerte sind — keine Mittelung, saubere Ergebnisse. Aus der
    berechneten Zusammenfassung zeichnet matplotlib:boxplot die Lösung (Figurenausgabe ist
    ein späterer Track)."""
    n = rng.choice([11, 15])
    vals = sorted(rng.randint(1, 45) for _ in range(n))
    if vals[-1] - vals[0] < 6:
        raise Unsuitable                       # zu wenig Streuung → uninteressant
    half = n // 2
    lower, upper = vals[:half], vals[half + 1:]
    mn, mx, med = vals[0], vals[-1], vals[half]
    q1, q3 = lower[len(lower) // 2], upper[len(upper) // 2]
    if q3 - q1 == 0:
        raise Unsuitable                       # entarteter Interquartilsabstand
    spann, iqr = mx - mn, q3 - q1
    daten = ", ".join(str(v) for v in rng.sample(vals, n))   # ungeordnet vorlegen
    steps = [
        SolutionStep(text="die Daten der Größe nach ordnen: " + ", ".join(map(str, vals))),
        SolutionStep(text=f"Minimum = {mn}, Maximum = {mx}; "
                          f"Spannweite = {mx} − {mn} = {spann}"),
        SolutionStep(text=f"Median = mittlerer der {n} Werte (Position {half + 1}) = {med}"),
        SolutionStep(text="Quartile nach der Schulmethode: Q₁ = Median der unteren Hälfte "
                          f"(ohne den Gesamtmedian) = {q1}; Q₃ = Median der oberen Hälfte = {q3}"),
        SolutionStep(text=f"Interquartilsabstand = Q₃ − Q₁ = {q3} − {q1} = {iqr}"),
    ]
    answer = (f"Minimum = {mn}, Q₁ = {q1}, Median = {med}, Q₃ = {q3}, Maximum = {mx}; "
              f"Spannweite = {spann}; Interquartilsabstand = {iqr}")
    return Instance(params={"daten": daten}, answer=answer, steps=steps)


@_recipe("probability_tree")
def _probability_tree(rng: random.Random) -> Instance:
    """Zweistufiger Urnenversuch (mit/ohne Zurücklegen) mit EXAKTEN Wahrscheinlichkeiten
    (sympy Rational).

    Gefragt wird eine Pfadwahrscheinlichkeit, eine Summe von Pfaden (genau eine rote Kugel)
    oder eine bedingte Wahrscheinlichkeit (dann ohne Zurücklegen, damit sie nicht trivial
    mit der unbedingten zusammenfällt). Rechenweg = Stufenwahrscheinlichkeiten + Pfad-/
    Additionsregel. Der gezogene Baum lässt sich via matplotlib:tree_diagram darstellen
    (Figurenausgabe ist ein späterer Track)."""
    r, b = rng.randint(2, 6), rng.randint(2, 6)
    n = r + b
    ask = rng.choice(["pfad", "genau_eine", "bedingt"])
    mit = False if ask == "bedingt" else (rng.random() < 0.5)
    ziehung = "mit Zurücklegen" if mit else "ohne Zurücklegen"
    lead = (f"In einer Urne liegen {r} rote und {b} blaue Kugeln. Es werden nacheinander "
            f"zwei Kugeln {ziehung} gezogen.")
    p_r, p_b = Rational(r, n), Rational(b, n)

    def stage2(first_red: bool, want_red: bool) -> Rational:
        if mit:
            return p_r if want_red else p_b
        red_left = r - 1 if first_red else r
        blue_left = b - 1 if not first_red else b
        return Rational(red_left if want_red else blue_left, n - 1)

    if ask == "pfad":
        c1_red, c2_red = rng.random() < 0.5, rng.random() < 0.5
        c1, c2 = ("rot" if c1_red else "blau"), ("rot" if c2_red else "blau")
        p1, p2 = (p_r if c1_red else p_b), stage2(c1_red, c2_red)
        P = p1 * p2
        aufgabe = lead + f" Wie groß ist die Wahrscheinlichkeit, zuerst {c1} und dann {c2} zu ziehen?"
        steps = [
            SolutionStep(text=f"Stufe 1: Wahrscheinlichkeit, {c1} zu ziehen", expr=f"P_1 = {latex(p1)}"),
            SolutionStep(text=f"Stufe 2 ({ziehung}): {c2} nach {c1}", expr=f"P_2 = {latex(p2)}"),
            SolutionStep(text="Pfadregel — entlang des Astes multiplizieren",
                         expr=f"P = {latex(p1)} \\cdot {latex(p2)} = {latex(P)}"),
        ]
    elif ask == "genau_eine":
        P_rb, P_br = p_r * stage2(True, False), p_b * stage2(False, True)
        P = P_rb + P_br
        aufgabe = lead + " Wie groß ist die Wahrscheinlichkeit, genau eine rote Kugel zu ziehen?"
        steps = [
            SolutionStep(text="günstig sind zwei Pfade: (rot, blau) und (blau, rot)"),
            SolutionStep(text="Pfad (rot, blau) — Multiplikationsregel",
                         expr=f"{latex(p_r)} \\cdot {latex(stage2(True, False))} = {latex(P_rb)}"),
            SolutionStep(text="Pfad (blau, rot) — Multiplikationsregel",
                         expr=f"{latex(p_b)} \\cdot {latex(stage2(False, True))} = {latex(P_br)}"),
            SolutionStep(text="Additionsregel — beide Pfade addieren",
                         expr=f"P = {latex(P_rb)} + {latex(P_br)} = {latex(P)}"),
        ]
    else:  # bedingt (ohne Zurücklegen)
        c1_red, c2_red = rng.random() < 0.5, rng.random() < 0.5
        c1, c2 = ("rot" if c1_red else "blau"), ("rot" if c2_red else "blau")
        P = stage2(c1_red, c2_red)
        aufgabe = lead + (f" Die erste gezogene Kugel ist {c1}. Wie groß ist die (bedingte) "
                          f"Wahrscheinlichkeit, dass die zweite Kugel {c2} ist?")
        steps = [
            SolutionStep(text=f"gegeben ist die erste Kugel ({c1}); gesucht die bedingte "
                              f"Wahrscheinlichkeit für {c2} in der 2. Stufe"),
            SolutionStep(text=f"ohne Zurücklegen ist eine {c1}e Kugel entfernt — am 2. Ast ablesen",
                         expr=f"P(2.\\,{c2} \\mid 1.\\,{c1}) = {latex(P)}"),
        ]
    answer = [_math(latex(P)), InlineRun(text=f" ≈ {_de_num(float(P), 3)}")]
    return Instance(params={"aufgabe": aufgabe}, answer=answer, steps=steps)
