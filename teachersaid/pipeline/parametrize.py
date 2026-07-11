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
    Eq, Integer, Matrix, N, Rational, acos, binomial, diff, integrate,
    latex, linsolve, pi, simplify, solve, sqrt, symbols,
)

from ..schema.assets import Asset
from ..schema.blocks import MultipleChoicePayload, SolutionPath, SolutionStep, TaskBlock
from ..schema.parametric import FigureSpec, Instance, MCSpec, ParametricTask
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


def _instantiate(task: ParametricTask, seed: int, *,
                 difficulty: int | None = None) -> tuple[TaskBlock, list[Asset]]:
    """Build one concrete (TaskBlock, emitted assets) for `seed` (deterministic).

    `difficulty` (1–3) is passed only to recipes that declare the knob; others are drawn
    unchanged (the ramp request is honestly ignored). The block's `difficulty` comes from
    what the recipe DELIVERED (`Instance.difficulty`), never the request. If the recipe's
    Instance carries an `mc` request, the block is emitted as a `multiple_choice` task with
    correct-by-construction misconception distractors (see `_mc_fields`). When a recipe emits
    an `Instance.figure`, the asset gets a UNIQUE
    per-variant id (`<task>-<seed>-fig`, no '#' → a safe PNG filename) and is wired onto
    the block via `asset_refs`, so figures never collide or overwrite one another. A
    `solution_figure` gets its own unique id and is wired only to `solution_asset_refs`."""
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
        solution_paths=inst.solution_paths, difficulty=inst.difficulty,
    )
    if mc is not None:                                 # override for the MC projection
        fields.update(mc)
    block = TaskBlock(**fields)
    assets: list[Asset] = []
    if inst.figure is not None:
        asset = Asset(id=f"{task.id}-{seed}-fig", role="figure",
                      generator=inst.figure.generator, spec=inst.figure.spec)
        block.asset_refs = [asset.id]
        assets.append(asset)
    if inst.solution_figure is not None:
        solution = Asset(id=f"{task.id}-{seed}-solution-fig", role="figure",
                         generator=inst.solution_figure.generator,
                         spec=inst.solution_figure.spec)
        block.solution_asset_refs = [solution.id]
        assets.append(solution)
    return block, assets


def instantiate(task: ParametricTask, seed: int, *,
                difficulty: int | None = None) -> TaskBlock:
    """Build one concrete TaskBlock for `seed` (deterministic; see `_instantiate`)."""
    return _instantiate(task, seed, difficulty=difficulty)[0]


def ramp_bands(n: int) -> list[int]:
    """Ascending difficulty bands for an n-variant Übungsreihe, as even as possible:
    n=6 → [1,1,2,2,3,3]; n=4 → [1,1,2,3]. Deterministic in n."""
    return [1 + (3 * i) // n for i in range(n)]


def make_variants_with_assets(
    task: ParametricTask, n: int, *, seed0: int = 1, ramp: bool = False,
) -> tuple[list[TaskBlock], list[Asset]]:
    """N variants of one template, preferring distinct prompts, plus their figure assets
    (aligned: only variants that emit a figure contribute one). Recipes with a small finite
    draw space (e.g. the qualitative chemistry tables) can repeat across independent seeds;
    we skip a seed whose prompt duplicates an earlier one, then top up with repeats if the
    pool is genuinely smaller than n. Deterministic: same (task, n, seed0, ramp) → same lists.

    `ramp=True` requests ascending difficulty bands (see `ramp_bands`) from recipes
    that support the knob — the Übungsreihe form: start leicht, end anspruchsvoll.
    Recipes without the knob ignore the request, so ramp is safe on any template."""
    blocks: list[TaskBlock] = []
    assets: list[Asset] = []
    seen: set[str] = set()
    seed = seed0
    bands: list[int | None] = list(ramp_bands(n)) if ramp else [None] * n
    budget = seed0 + max(n * 20, 40)              # bounded search for distinct prompts

    def _keep(blk: TaskBlock, emitted: list[Asset]) -> None:
        blocks.append(blk)
        assets.extend(emitted)

    for band in bands:
        while seed < budget:                      # find a distinct prompt for this slot
            blk, emitted = _instantiate(task, seed, difficulty=band)
            seed += 1
            key = str(blk.prompt)
            if key not in seen:
                seen.add(key)
                _keep(blk, emitted)
                break
        else:                                     # pool exhausted → allow a repeat
            _keep(*_instantiate(task, seed, difficulty=band))
            seed += 1
    return blocks, assets


def make_variants(task: ParametricTask, n: int, *, seed0: int = 1,
                  ramp: bool = False) -> list[TaskBlock]:
    """N variant TaskBlocks of one template (see `make_variants_with_assets`)."""
    return make_variants_with_assets(task, n, seed0=seed0, ramp=ramp)[0]


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


def _assert_percent_value(res, *routes) -> None:
    """Guard the equal-answer invariant for the percentage recipes: each named strategy is
    RE-derived here by its own distinct exact arithmetic (Formel · Dreisatz · Operator) and
    must equal the primary answer `res`. Not a tautology — it recomputes each formula from the
    raw numbers, so a wrong strategy formula raises instead of shipping a diverging path."""
    for name, value in routes:
        assert value == res, f"percentage strategy {name} recomputes to {value}, expected {res}"


@_recipe("percentage")
def _percentage(rng: random.Random) -> Instance:
    """Wie viel sind p % von G? — Prozentrechnung (Grundwert → Prozentwert).

    Three genuinely different school strategies, all DERIVED (exact rationals): the PRIMARY
    is die Prozentformel (W = G · p/100); Dreisatz (über 1 %) and der Prozentoperator
    (G · Dezimalzahl) ride along as `solution_paths`. Every route ends at the same W —
    asserted here."""
    base = rng.choice([40, 50, 60, 80, 120, 150, 200, 240, 300, 400, 500])
    pct = rng.choice([5, 10, 15, 20, 25, 30, 40, 50, 75])
    res = Rational(base * pct, 100)
    frac = Rational(pct, 100)                          # p % als Bruch
    one_pct = Rational(base, 100)                      # 1 % vom Grundwert
    op = _de(float(frac))                              # der Prozentoperator (Dezimalzahl)

    steps = [                                          # primary = Prozentformel
        SolutionStep(text="Prozentformel für den Prozentwert ansetzen",
                     expr="W = G \\cdot \\frac{p}{100}"),
        SolutionStep(text=f"Grundwert {base} und Prozentsatz {pct} einsetzen",
                     expr=f"W = {base} \\cdot \\frac{{{pct}}}{{100}} = {latex(res)}"),
    ]
    paths = [
        SolutionPath(strategy="Dreisatz", steps=[
            SolutionStep(text=f"Der Grundwert {base} entspricht 100 %.",
                         expr=f"100\\,\\% \\;\\widehat{{=}}\\; {base}"),
            SolutionStep(text="1 % ist der hundertste Teil (durch 100 dividieren)",
                         expr=f"1\\,\\% \\;\\widehat{{=}}\\; \\frac{{{base}}}{{100}} = {latex(one_pct)}"),
            SolutionStep(text=f"auf {pct} % hochrechnen (mal {pct})",
                         expr=f"{pct}\\,\\% \\;\\widehat{{=}}\\; {latex(one_pct)} \\cdot {pct} = {latex(res)}"),
        ], note=("hier fällt der Dreisatz leicht: 1 % ist eine glatte Zahl"
                 if one_pct == int(one_pct) else None)),
        SolutionPath(strategy="Prozentoperator", steps=[
            SolutionStep(text=f"{pct} % als Dezimalzahl schreiben (durch 100)",
                         expr=f"{pct}\\,\\% = {latex(frac)} = {op}"),
            SolutionStep(text="den Grundwert mit diesem Operator multiplizieren",
                         expr=f"W = {base} \\cdot {op} = {latex(res)}"),
        ]),
    ]
    _assert_percent_value(res,                          # each route re-derived independently
                          ("Prozentformel", Rational(base) * pct / 100),
                          ("Dreisatz", one_pct * pct),
                          ("Prozentoperator", base * frac))
    return Instance(params={"pct": pct, "base": base},
                    answer=[_math(latex(res))], steps=steps, solution_paths=paths)


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
    """Welcher Prozentsatz? — X von Y sind wie viel %? (the Prozentsatz case).

    Three named strategies, all DERIVED (exact): PRIMARY is die Prozentformel (p = W/G · 100);
    Dreisatz (über 1) and der Prozentoperator (Anteil als Dezimalzahl · 100) are the
    `solution_paths`. Each route recomputes to the same p — asserted here."""
    base = rng.choice([20, 25, 40, 50, 80, 200, 400, 500])
    rate = rng.choice([5, 10, 15, 20, 25, 40, 50, 75])
    part = base * rate
    if part % 100:
        raise Unsuitable
    part //= 100
    anteil = Rational(part, base)                       # W/G als (gekürzter) Bruch
    per_unit = Rational(100, base)                      # wie viel % eine Einheit wert ist
    op = _de(float(anteil))                             # der Anteil als Dezimalzahl

    steps = [                                           # primary = Prozentformel
        SolutionStep(text="Prozentformel nach dem Prozentsatz ansetzen",
                     expr="p = \\frac{W}{G} \\cdot 100\\,\\%"),
        SolutionStep(text=f"Prozentwert {part} und Grundwert {base} einsetzen",
                     expr=f"p = \\frac{{{part}}}{{{base}}} \\cdot 100\\,\\% = {rate}\\,\\%"),
    ]
    paths = [
        SolutionPath(strategy="Dreisatz", steps=[
            SolutionStep(text=f"Der Grundwert {base} entspricht 100 %.",
                         expr=f"{base} \\;\\widehat{{=}}\\; 100\\,\\%"),
            SolutionStep(text="eine Einheit ist dann 100/G Prozent wert (durch G dividieren)",
                         expr=f"1 \\;\\widehat{{=}}\\; \\frac{{100}}{{{base}}}\\,\\% = {latex(per_unit)}\\,\\%"),
            SolutionStep(text=f"auf den Prozentwert {part} hochrechnen (mal {part})",
                         expr=f"{part} \\;\\widehat{{=}}\\; {latex(per_unit)}\\,\\% \\cdot {part} = {rate}\\,\\%"),
        ], note=("hier fällt der Dreisatz leicht: eine Einheit ist eine glatte Prozentzahl"
                 if per_unit == int(per_unit) else None)),
        SolutionPath(strategy="Prozentoperator", steps=[
            SolutionStep(text="den Anteil W/G als Dezimalzahl bestimmen",
                         expr=f"\\frac{{{part}}}{{{base}}} = {latex(anteil)} = {op}"),
            SolutionStep(text="mit 100 multiplizieren ergibt den Prozentsatz",
                         expr=f"{op} \\cdot 100\\,\\% = {rate}\\,\\%"),
        ]),
    ]
    _assert_percent_value(Integer(rate),                # each route re-derived independently
                          ("Prozentformel", anteil * 100),
                          ("Dreisatz", per_unit * part),
                          ("Prozentoperator", anteil * 100))
    return Instance(params={"part": part, "base": base},
                    answer=f"{rate} %", steps=steps, solution_paths=paths)


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
    """Satz des Pythagoras an einem rechtwinkligen Dreieck (ganzzahlige Tripel).

    Gefragt ist die Hypotenuse c ODER eine der Katheten (a bzw. b) — die zwei anderen
    Seiten sind gegeben. Die Skizze (`matplotlib:right_triangle`) zeigt die zwei gegebenen
    Längen ("a = 3 cm") und markiert die gesuchte Seite mit "?", verrät also die Lösung
    NICHT. Damit auch die gesuchte KATHETE nicht über eine Zeichenkoordinate durchsickert,
    werden die Zeichenlängen auf die Hypotenuse normiert (da = a/c, db = b/c ∈ (0,1)) — die
    ganzzahlige Antwort taucht so nirgends in der Figurenspezifikation auf. Rechenweg exakt."""
    a, b, c = rng.choice(_TRIPLES)
    if rng.random() < 0.5:
        a, b = b, a
    target = rng.choice(["c", "a", "b"])          # gesucht: Hypotenuse oder eine Kathete
    L = {"a": f"a = {a} cm", "b": f"b = {b} cm", "c": f"c = {c} cm"}   # side labels
    L[target] = f"{target} = ?"                    # mask the asked side on the figure
    if target == "c":                              # Hypotenuse aus den Katheten
        gegeben, gesucht = f"a = {a} cm, b = {b} cm", "die Hypotenuse c"
        steps = [
            SolutionStep(text="Satz des Pythagoras", expr="c^2 = a^2 + b^2"),
            SolutionStep(text="die Katheten einsetzen",
                         expr=f"c^2 = {a}^2 + {b}^2 = {a * a + b * b}"),
            SolutionStep(text="die Wurzel ziehen", expr=f"c = \\sqrt{{{a * a + b * b}}} = {c}"),
        ]
        ans = c
    else:                                          # Kathete aus Hypotenuse + anderer Kathete
        kath, other = (a, b) if target == "a" else (b, a)   # gesuchte / bekannte Kathete
        gegeben = f"{'b' if target == 'a' else 'a'} = {other} cm, c = {c} cm"
        gesucht = f"die Kathete {target}"
        steps = [
            SolutionStep(text="Satz des Pythagoras nach der Kathete umstellen",
                         expr=f"{target}^2 = c^2 - {'b' if target == 'a' else 'a'}^2"),
            SolutionStep(text="einsetzen",
                         expr=f"{target}^2 = {c}^2 - {other}^2 = {c * c - other * other}"),
            SolutionStep(text="die Wurzel ziehen",
                         expr=f"{target} = \\sqrt{{{c * c - other * other}}} = {kath}"),
        ]
        ans = kath
    figure = FigureSpec(generator="matplotlib:right_triangle", spec={
        "a": round(a / c, 3), "b": round(b / c, 3),        # normed → no integer leaks
        "label_a": L["a"], "label_b": L["b"], "label_c": L["c"],
        "title": "rechtwinkliges Dreieck"})
    return Instance(params={"gegeben": gegeben, "gesucht": gesucht},
                    answer=f"{target} = {ans} cm", steps=steps, figure=figure)


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


@_recipe("quader_oberflaeche")
def _quader_oberflaeche(rng: random.Random) -> Instance:
    """Oberflächeninhalt of a cuboid, derived from its computed six-face net.

    Three distinct integer edge lengths keep the congruent face pairs visually legible.
    The figure carries only the givens and ``O = ?``; the surface-area result is computed
    here from the same ``a``, ``b``, ``c`` values and never enters visible figure text.
    """
    a, b, c = rng.sample(range(2, 9), 3)
    ab, ac, bc = a * b, a * c, b * c
    surface = 2 * (ab + ac + bc)
    steps = [
        SolutionStep(text="Die sechs Flächen zu drei kongruenten Paaren ordnen",
                     expr="O = 2ab + 2ac + 2bc"),
        SolutionStep(text="Kantenlängen einsetzen",
                     expr=f"O = 2 \\cdot {a} \\cdot {b} + 2 \\cdot {a} \\cdot {c} + "
                          f"2 \\cdot {b} \\cdot {c}"),
        SolutionStep(text="Teilflächen addieren",
                     expr=f"O = {2 * ab} + {2 * ac} + {2 * bc} = {surface}"),
    ]
    figure = FigureSpec(generator="matplotlib:solid_net", spec={
        "kind": "cuboid", "a": a, "b": b, "c": c,
        "label_a": f"a = {a} cm", "label_b": f"b = {b} cm",
        "label_c": f"c = {c} cm", "result_label": "O = ?",
        "title": "Netz eines Quaders",
    })
    return Instance(params={"a": a, "b": b, "c": c},
                    answer=f"O = {surface} cm²", steps=steps, figure=figure)


@_recipe("kreis_umfang_flaeche")
def _kreis_umfang_flaeche(rng: random.Random) -> Instance:
    """Umfang U = 2·π·r und Flächeninhalt A = π·r² eines Kreises aus dem Radius.

    Exakt (sympy pi → 10π, 25π …) plus die auf zwei Stellen gerundete Dezimalzahl (im
    Klartext, mit deutschem Komma — kein Komma in der mathtext-Formel). Die Skizze
    (`matplotlib:circle`) zeigt NUR den gegebenen Radius; U und A werden nicht eingezeichnet,
    können also nicht durchsickern."""
    r = rng.randint(2, 12)
    u_exact, a_exact = 2 * pi * r, pi * r ** 2
    u_dez, a_dez = _de_num(float(N(u_exact)), 2), _de_num(float(N(a_exact)), 2)
    steps = [
        SolutionStep(text="Umfang mit der Formel U = 2·r·π berechnen",
                     expr=f"U = 2 \\cdot {r} \\cdot \\pi = {latex(u_exact)}"),
        SolutionStep(text=f"Umfang auf zwei Nachkommastellen runden: U ≈ {u_dez} cm"),
        SolutionStep(text="Flächeninhalt mit der Formel A = r²·π berechnen",
                     expr=f"A = {r}^2 \\cdot \\pi = {latex(a_exact)}"),
        SolutionStep(text=f"Flächeninhalt auf zwei Nachkommastellen runden: A ≈ {a_dez} cm²"),
    ]
    answer = [_math(f"U = {latex(u_exact)}"), InlineRun(text=f" ≈ {u_dez} cm;  "),
              _math(f"A = {latex(a_exact)}"), InlineRun(text=f" ≈ {a_dez} cm²")]
    figure = FigureSpec(generator="matplotlib:circle",
                        spec={"radius": r, "label_r": f"r = {r} cm", "title": "Kreis"})
    return Instance(params={"r": r}, answer=answer, steps=steps, figure=figure)


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


# --- LGS(2): the three Austrian-school strategies, each DERIVED (sympy, exact) ------
# For I: a1·x + b1·y = c1 and II: a2·x + b2·y = c2 (all coefficients nonzero, det ≠ 0),
# every named method is genuinely applicable. The recipe draws with all four coefficients
# nonzero precisely so all three routes are natural — otherwise Gleichsetzung/Einsetzung can
# be undefined for a variable and we would ship a broken "alternative". Each builder returns
# faithful worked steps and its OWN computed (x, y); `_linear_system_2` asserts all three
# agree with the linsolve answer before shipping (a diverging path is a bug, not a variant).

def _elim_add_steps(a1, b1, c1, a2, b2, c2, x, y):
    """Additionsverfahren: eliminate y (scale I by b2, II by b1, subtract), then solve.
    Returns (steps, (x_val, y_val))."""
    # (b2·I) − (b1·II): the y-terms cancel; coefficient of x is the determinant.
    det = a1 * b2 - a2 * b1
    rx = c1 * b2 - c2 * b1
    x_val = Rational(rx, det)
    y_val = Rational(c1 - a1 * x_val, b1)
    scaled1 = Eq(b2 * a1 * x + b2 * b1 * y, b2 * c1)
    scaled2 = Eq(b1 * a2 * x + b1 * b2 * y, b1 * c2)
    steps = [
        SolutionStep(text="I und II so erweitern, dass sich die y-Terme aufheben "
                          f"(I · {b2}, II · {b1})",
                     expr=f"{latex(scaled1)};\\quad {latex(scaled2)}"),
        SolutionStep(text="die erweiterte II von der erweiterten I subtrahieren — y fällt weg",
                     expr=f"{latex(det)}\\,x = {latex(rx)} \\Rightarrow x = {latex(x_val)}"),
        SolutionStep(text="x in I einsetzen und nach y auflösen",
                     expr=f"y = \\frac{{{latex(c1)} - ({a1})\\cdot({latex(x_val)})}}{{{b1}}} "
                          f"= {latex(y_val)}"),
    ]
    return steps, (x_val, y_val)


def _substitution_steps(a1, b1, c1, a2, b2, c2, x, y):
    """Einsetzungsverfahren: solve I for x, substitute into II, solve for y, back-substitute."""
    x_expr = (c1 - b1 * y) / a1                       # x aus I
    eq_sub = Eq(a2 * x_expr + b2 * y, c2)             # in II eingesetzt
    y_val = solve(eq_sub, y)[0]
    x_val = (c1 - b1 * y_val) / a1
    steps = [
        SolutionStep(text="Gleichung I nach x auflösen",
                     expr=f"x = {latex(x_expr)}"),
        SolutionStep(text="diesen Ausdruck für x in II einsetzen",
                     expr=f"{a2}\\left({latex(x_expr)}\\right) + {b2}\\,y = {latex(c2)}"),
        SolutionStep(text="nach y auflösen",
                     expr=f"y = {latex(y_val)}"),
        SolutionStep(text="y in die nach x umgeformte I einsetzen",
                     expr=f"x = {latex(simplify(x_val))}"),
    ]
    return steps, (simplify(x_val), simplify(y_val))


def _equate_steps(a1, b1, c1, a2, b2, c2, x, y):
    """Gleichsetzungsverfahren: solve BOTH equations for x, set the two expressions equal."""
    x1 = (c1 - b1 * y) / a1                            # x aus I
    x2 = (c2 - b2 * y) / a2                            # x aus II
    y_val = solve(Eq(x1, x2), y)[0]
    x_val = x1.subs(y, y_val)
    steps = [
        SolutionStep(text="beide Gleichungen nach x auflösen",
                     expr=f"x = {latex(x1)} \\quad\\text{{(I)}};\\qquad "
                          f"x = {latex(x2)} \\quad\\text{{(II)}}"),
        SolutionStep(text="die beiden Ausdrücke gleichsetzen (x = x)",
                     expr=f"{latex(x1)} = {latex(x2)}"),
        SolutionStep(text="nach y auflösen",
                     expr=f"y = {latex(y_val)}"),
        SolutionStep(text="y in einen der beiden x-Ausdrücke einsetzen",
                     expr=f"x = {latex(x_val)}"),
    ]
    return steps, (simplify(x_val), simplify(y_val))


@_recipe("linear_system_2")
def _linear_system_2(rng: random.Random) -> Instance:
    """Lineares Gleichungssystem in zwei Variablen (eindeutig lösbar, ganzzahlige Lösung).

    Emits the three named Austrian-school strategies: the PRIMARY Rechenweg is the
    Additionsverfahren (elimination — the method the recipe has always used), and the
    Einsetzungs- and Gleichsetzungsverfahren ride along as `solution_paths` (the teacher's
    "Alternative Lösungswege"). All three are DERIVED via sympy and must reach the identical
    (x, y) — asserted here (a diverging path is a bug, not shipped)."""
    x, y = symbols("x y")
    x0, y0 = rng.randint(-5, 5), rng.randint(-5, 5)
    a1, b1 = rng.randint(-4, 4), rng.randint(-4, 4)
    a2, b2 = rng.randint(-4, 4), rng.randint(-4, 4)
    # all four coefficients nonzero → all three strategies are genuinely applicable (see note)
    if 0 in (a1, b1, a2, b2) or a1 * b2 - a2 * b1 == 0:
        raise Unsuitable  # det ≠ 0 → genau eine Lösung; keine Null-Koeffizienten
    c1, c2 = a1 * x0 + b1 * y0, a2 * x0 + b2 * y0
    eq1, eq2 = Eq(a1 * x + b1 * y, c1), Eq(a2 * x + b2 * y, c2)
    sol = list(linsolve([eq1, eq2], [x, y]))[0]
    header = SolutionStep(text="Gleichungssystem (I, II)",
                          expr=f"{latex(eq1)};\\quad {latex(eq2)}")

    add_steps, add_xy = _elim_add_steps(a1, b1, c1, a2, b2, c2, x, y)
    sub_steps, sub_xy = _substitution_steps(a1, b1, c1, a2, b2, c2, x, y)
    equ_steps, equ_xy = _equate_steps(a1, b1, c1, a2, b2, c2, x, y)
    # every route must land on the linsolve answer — correct by construction, enforced.
    for got in (add_xy, sub_xy, equ_xy):
        assert (simplify(got[0] - sol[0]) == 0 and simplify(got[1] - sol[1]) == 0), \
            f"LGS solution path diverges: {got} vs {tuple(sol)}"

    steps = [header, *add_steps]                       # primary = Additionsverfahren
    paths = [
        SolutionPath(strategy="Einsetzungsverfahren", steps=[header, *sub_steps],
                     note=_lgs_note("Einsetzung", a1, b1, a2, b2)),
        SolutionPath(strategy="Gleichsetzungsverfahren", steps=[header, *equ_steps],
                     note=_lgs_note("Gleichsetzung", a1, b1, a2, b2)),
    ]
    return Instance(params={"eq1": latex(eq1), "eq2": latex(eq2)},
                    answer=[_math(f"x = {latex(sol[0])},\\; y = {latex(sol[1])}")],
                    steps=steps, solution_paths=paths)


def _lgs_note(method: str, a1, b1, a2, b2) -> str | None:
    """A didactic one-liner when THESE drawn coefficients make the derived path especially
    handy. Honest about the ACTUAL first step: Einsetzung here solves equation I for x, so it
    stays bruchfrei only when a1 = ±1; Gleichsetzung equates the two x-expressions, cleanest
    when the x-coefficients are betragsgleich. Returns None otherwise (the honest default)."""
    if method == "Einsetzung" and abs(a1) == 1:
        return ("hier besonders bequem: I hat für x den Koeffizienten ±1, "
                "das Auflösen bleibt bruchfrei")
    if method == "Gleichsetzung" and abs(a1) == abs(a2):
        return "hier naheliegend: die x-Koeffizienten in I und II sind betragsgleich"
    return None


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
    lang) eindeutig einzelne Datenwerte sind — keine Mittelung, saubere Ergebnisse.

    Der Lösungs-Boxplot IST die Fünf-Punkte-Zusammenfassung und darf deshalb nie in
    `figure`/`asset_refs` landen. Er wird aus denselben berechneten fünf Kennzahlen als
    `solution_figure` emittiert; die Instanziierungs-Naht verdrahtet ihn ausschließlich
    über `TaskBlock.solution_asset_refs` in die Lehrerprojektion."""
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
    solution_figure = FigureSpec(generator="matplotlib:boxplot", spec={
        "summary": {"min": mn, "q1": q1, "median": med, "q3": q3, "max": mx},
        "xlabel": "Wert", "title": "Lösung: Kastenschaubild",
    })
    return Instance(params={"daten": daten}, answer=answer, steps=steps,
                    solution_figure=solution_figure)


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
    # The Baumdiagramm is the scaffold: it labels the two FIRST-stage (directly sampled)
    # branch probabilities and draws the second stage as unlabelled structure. Every asked
    # quantity — a path product, a sum of paths, or a conditional — depends on the second
    # stage, so hiding those labels means the tree can never show the asked result (the
    # conditional case in particular: its answer IS a 2nd-stage edge). Built from the already
    # drawn r/b (no extra rng call) → the deterministic seed→answer mapping is untouched.
    def _stage2() -> list[dict]:
        return [{"label": "rot"}, {"label": "blau"}]     # outcomes only; probabilities hidden
    branches = [
        {"label": "rot", "p": f"{r}/{n}", "children": _stage2()},
        {"label": "blau", "p": f"{b}/{n}", "children": _stage2()},
    ]
    figure = FigureSpec(generator="matplotlib:tree_diagram", spec={
        "branches": branches, "title": f"Urne: {r} rote, {b} blaue Kugeln ({ziehung})"})
    return Instance(params={"aufgabe": aufgabe}, answer=answer, steps=steps, figure=figure)


# Latin Wortbildung recipes — same registry, same wiring (see pipeline/latin.py).
from . import latin as _latin  # noqa: E402,F401
from . import physics as _physics  # noqa: E402,F401
