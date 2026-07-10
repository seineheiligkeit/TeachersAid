"""Chemistry quantitative engine — the chemistry twin of the sympy maths recipes.

Same contract as `pipeline/parametrize.py`: a recipe OWNS sampling + solving and
returns an `Instance` (slot values + the DERIVED answer + a worked Rechenweg). The
numbers are **computed from the grounded atomic masses + conservation of atoms**, never
authored — so every variant is correct by construction. The recipes register into the
*shared* `_RECIPES` registry, so `make_variants` / templates / `compose_variants` drive
chemistry exactly as they drive maths.

- `molar_mass`        — M = Σ count·atomic-weight, per-element Rechenweg.
- `equation_balance`  — balance a skeleton via the conservation matrix' nullspace (sympy).
- `stoichiometry`     — m → n → mole-ratio → n → m, the canonical four-step calculation.

Übungsreihe upgrade: `molar_mass`, `equation_balance` and `atom_count` carry a
`difficulty` (1–3) knob whose band is COMPUTED from the drawn item's structure
(`_compound_band`: binary → polyatomic → nested/hydrate; `_reaction_band`: species
count + coefficient size) — so the stamped band is derived, never asserted. Each draw
also selects the item's curated, digit-free context sentence from grounding
(`COMPOUND_CONTEXTS` / `REACTION_CONTEXTS`) as a prompt prefix. `stoichiometry` gets
the context but no knob (its hardness is the four-step method, not the reaction).
"""

from __future__ import annotations

import random
from functools import reduce
from math import gcd

from sympy import Matrix, ilcm

from ..grounding.chemistry import (
    ACID_BASE, COMPOUND_CONTEXTS, ELEMENT_NAMES, REACTION_CONTEXTS, REACTION_TYPE_REASON,
    REACTION_TYPES, SEPARATION_METHODS, SUBSTANCE_CLASSES, mass_breakdown, molar_mass,
    parse_formula, reaction_key, subscript,
)
from ..schema.blocks import SolutionStep
from ..schema.parametric import Instance
from .parametrize import Unsuitable, _recipe


# --- balancing --------------------------------------------------------------
def balance_equation(reactants: list[str], products: list[str]) -> tuple[list[int], list[int]]:
    """Smallest positive integer coefficients balancing `reactants → products`.

    Builds the element×species conservation matrix (products negative) and takes its
    nullspace; a unique balance ⇔ a 1-dimensional nullspace. Raises ValueError if the
    skeleton cannot be balanced uniquely (impossible or underdetermined)."""
    species = reactants + products
    elements = sorted({e for s in species for e in parse_formula(s)})
    rows = [
        [parse_formula(s).get(el, 0) for s in reactants]
        + [-parse_formula(s).get(el, 0) for s in products]
        for el in elements
    ]
    ns = Matrix(rows).nullspace()
    if len(ns) != 1:
        raise ValueError(f"cannot balance uniquely: {reactants} -> {products}")
    vec = ns[0]
    mult = ilcm(*[t.q for t in vec])                 # clear denominators → integers
    ints = [int(t * mult) for t in vec]
    g = reduce(gcd, [abs(i) for i in ints])          # reduce to smallest set
    ints = [i // g for i in ints]
    if ints[0] < 0:
        ints = [-i for i in ints]
    if any(i <= 0 for i in ints):
        raise ValueError(f"non-positive coefficient balancing {reactants} -> {products}")
    return ints[: len(reactants)], ints[len(reactants):]


def _term(coeff: int, formula: str) -> str:
    """A reaction term for display: coefficient (omit 1) + subscripted formula."""
    return (f"{coeff} " if coeff != 1 else "") + subscript(formula)


def _side(coeffs: list[int], formulas: list[str]) -> str:
    return " + ".join(_term(c, f) for c, f in zip(coeffs, formulas))


def equation_str(rc: list[int], rs: list[str], pc: list[int], ps: list[str]) -> str:
    return f"{_side(rc, rs)} → {_side(pc, ps)}"


def _num(x: float, dp: int = 2) -> str:
    """German decimal formatting (comma), fixed dp."""
    return f"{x:.{dp}f}".replace(".", ",")


# --- curated input (the pedagogical 'select' layer — facts stay in grounding) ---
_COMPOUNDS = [
    "H2O", "CO2", "NaCl", "H2SO4", "CaCO3", "NaOH", "KOH", "HCl", "NH3", "CH4",
    "C6H12O6", "Ca(OH)2", "MgO", "Fe2O3", "Al2O3", "CuSO4", "KMnO4", "HNO3",
    "Na2CO3", "C2H5OH", "CaCl2", "ZnO",
    # nested / hydrate formulas — the anspruchsvoll end of the molar-mass ramp
    "Mg(OH)2", "Al2(SO4)3", "Ba(NO3)2", "(NH4)2SO4", "CuSO4·5H2O",
]

# Real reaction skeletons (unbalanced), all uniquely balanceable.
_REACTIONS: list[tuple[list[str], list[str]]] = [
    (["H2", "O2"], ["H2O"]),
    (["N2", "H2"], ["NH3"]),
    (["Fe", "O2"], ["Fe2O3"]),
    (["CH4", "O2"], ["CO2", "H2O"]),
    (["Al", "O2"], ["Al2O3"]),
    (["Na", "Cl2"], ["NaCl"]),
    (["C3H8", "O2"], ["CO2", "H2O"]),
    (["H2", "Cl2"], ["HCl"]),
    (["Mg", "O2"], ["MgO"]),
    (["C2H6", "O2"], ["CO2", "H2O"]),
    (["Fe", "Cl2"], ["FeCl3"]),
    (["NaN3"], ["Na", "N2"]),                     # the airbag reaction
    (["CO2", "H2O"], ["C6H12O6", "O2"]),          # photosynthesis
]


# --- difficulty bands, COMPUTED from item structure (derived, never asserted) ----
def _compound_band(formula: str) -> int:
    """1 = binary (two elements) · 2 = polyatomic (three+) · 3 = nested / hydrate."""
    if "(" in formula or "·" in formula:
        return 3
    return 1 if len(parse_formula(formula)) <= 2 else 2


def _compound_pool(pool: list[str], difficulty: int | None) -> list[str]:
    if difficulty not in (1, 2, 3):
        return pool
    return [f for f in pool if _compound_band(f) == difficulty]


_REACTION_BAND_CACHE: dict[str, int] = {}


def _reaction_band(reactants: list[str], products: list[str]) -> int:
    """1 = three species, coefficients ≤ two · 3 = multi-product with large
    coefficients · 2 = everything between. Derived from the BALANCED structure."""
    key = reaction_key(reactants, products)
    if key not in _REACTION_BAND_CACHE:
        rc, pc = balance_equation(reactants, products)
        species = len(reactants) + len(products)
        maxc = max(rc + pc)
        if species <= 3 and maxc <= 2:
            band = 1
        elif species >= 4 and maxc >= 4:
            band = 3
        else:
            band = 2
        _REACTION_BAND_CACHE[key] = band
    return _REACTION_BAND_CACHE[key]


def _reaction_pool(difficulty: int | None) -> list[tuple[list[str], list[str]]]:
    if difficulty not in (1, 2, 3):
        return _REACTIONS
    return [rp for rp in _REACTIONS if _reaction_band(*rp) == difficulty]


# --- recipes ----------------------------------------------------------------
@_recipe("molar_mass")
def _molar_mass(rng: random.Random, difficulty: int | None = None) -> Instance:
    """Berechne die molare Masse einer Verbindung — M = Σ (Anzahl · Atommasse).

    Difficulty knob: band pool by formula structure (binary → polyatomic →
    nested/hydrate). The stamped band is always the drawn item's real band."""
    formula = rng.choice(_compound_pool(_COMPOUNDS, difficulty))
    M = molar_mass(formula)
    steps: list[SolutionStep] = []
    for el, n, contrib in mass_breakdown(formula):
        name = ELEMENT_NAMES.get(el, el)
        steps.append(SolutionStep(
            text=f"{name} ({el}): {n} · {_num(molar_mass(el))} g/mol = {_num(contrib)} g/mol"))
    steps.append(SolutionStep(
        text=f"Summe der Atommassen: M = {_num(M)} g/mol"))
    return Instance(
        params={"formel": subscript(formula)},
        answer=f"M({subscript(formula)}) ≈ {_num(M)} g/mol",
        steps=steps,
        difficulty=_compound_band(formula),
        context=COMPOUND_CONTEXTS.get(formula))


@_recipe("equation_balance")
def _equation_balance(rng: random.Random, difficulty: int | None = None) -> Instance:
    """Gleiche eine Reaktionsgleichung aus (Erhaltung der Atome).

    Difficulty knob: band pool by species count + coefficient size (derived from
    the balanced structure — see `_reaction_band`)."""
    reactants, products = rng.choice(_reaction_pool(difficulty))
    rc, pc = balance_equation(reactants, products)
    if all(c == 1 for c in rc + pc):
        raise Unsuitable                              # trivial — no balancing to do
    skeleton = equation_str([1] * len(reactants), reactants, [1] * len(products), products)
    balanced = equation_str(rc, reactants, pc, products)
    elements = sorted({e for s in reactants + products for e in parse_formula(s)})
    checks = []
    for el in elements:
        left = sum(c * parse_formula(s).get(el, 0) for c, s in zip(rc, reactants))
        checks.append(f"{el}: {left}")
    steps = [
        SolutionStep(text=f"Unausgeglichenes Schema: {skeleton}"),
        SolutionStep(text="Koeffizienten so wählen, dass links und rechts jedes Element "
                          "gleich oft vorkommt (Massenerhaltung)."),
        SolutionStep(text=f"Atombilanz je Element (links = rechts): {', '.join(checks)}"),
        SolutionStep(text=f"Ausgeglichene Gleichung: {balanced}"),
    ]
    return Instance(params={"schema": skeleton}, answer=balanced, steps=steps,
                    difficulty=_reaction_band(reactants, products),
                    context=REACTION_CONTEXTS.get(reaction_key(reactants, products)))


@_recipe("stoichiometry")
def _stoichiometry(rng: random.Random) -> Instance:
    """Massenberechnung über die Reaktionsgleichung: m → n → Stoffmengenverhältnis → n → m."""
    reactants, products = rng.choice(_REACTIONS)
    rc, pc = balance_equation(reactants, products)
    gi = rng.randrange(len(reactants))                # given reactant
    ti = rng.randrange(len(products))                 # target product
    given, target = reactants[gi], products[ti]
    M_g, M_t = molar_mass(given), molar_mass(target)
    c_g, c_t = rc[gi], pc[ti]
    m_given = float(rng.choice([4, 5, 8, 10, 16, 20, 25, 40, 50]))
    n_given = m_given / M_g
    n_target = n_given * c_t / c_g
    m_target = n_target * M_t
    balanced = equation_str(rc, reactants, pc, products)
    gs, ts = subscript(given), subscript(target)
    steps = [
        SolutionStep(text=f"Reaktionsgleichung: {balanced}"),
        SolutionStep(text=f"Stoffmenge des Edukts: n({gs}) = m / M = {_num(m_given)} g / "
                          f"{_num(M_g)} g/mol = {_num(n_given, 3)} mol"),
        SolutionStep(text=f"Stoffmengenverhältnis aus der Gleichung: n({ts}) = "
                          f"{c_t}/{c_g} · n({gs}) = {_num(n_target, 3)} mol"),
        SolutionStep(text=f"Masse des Produkts: m({ts}) = n · M = {_num(n_target, 3)} mol · "
                          f"{_num(M_t)} g/mol = {_num(m_target)} g"),
    ]
    return Instance(
        params={"masse": _num(m_given, 0), "edukt": gs, "produkt": ts, "reaktion": balanced},
        answer=f"m({ts}) ≈ {_num(m_target)} g",
        steps=steps,
        context=REACTION_CONTEXTS.get(reaction_key(reactants, products)))


# --- qualitative recipes (Unterstufe) ---------------------------------------
# Still correct by construction: the answer is DERIVED (atom counts, reaction structure)
# or CURATED truth (classification, separation, pH) from grounding — never authored.

_CLASS_REASON = {
    "Element": "Ein Reinstoff aus nur einer Atomsorte.",
    "Verbindung": "Ein Reinstoff aus mehreren Atomsorten, die chemisch in einem festen "
                  "Verhältnis verbunden sind.",
    "Gemisch": "Mehrere Reinstoffe, die nicht chemisch verbunden sind und sich physikalisch "
               "trennen lassen.",
}


@_recipe("substance_classification")
def _substance_classification(rng: random.Random) -> Instance:
    """Reinstoff oder Gemisch? — ordne einen Stoff als Element, Verbindung oder Gemisch ein."""
    stoff, klasse = rng.choice(SUBSTANCE_CLASSES)
    return Instance(
        params={"stoff": stoff},
        answer=klasse,
        steps=[SolutionStep(text=f"{stoff}: {klasse} — {_CLASS_REASON[klasse]}")])


@_recipe("separation_method")
def _separation_method(rng: random.Random) -> Instance:
    """Welches Trennverfahren? — wähle die passende Methode für ein Stoffgemisch."""
    gemisch, methode = rng.choice(SEPARATION_METHODS)
    return Instance(
        params={"gemisch": gemisch},
        answer=methode,
        steps=[SolutionStep(text=f"{gemisch} → {methode}: Das Verfahren nutzt einen "
                                 "Unterschied in den Eigenschaften der Bestandteile.")])


@_recipe("acid_base_neutral")
def _acid_base_neutral(rng: random.Random) -> Instance:
    """Sauer, basisch oder neutral? — ordne eine Alltagslösung ein (pH-Charakter)."""
    stoff, charakter = rng.choice(ACID_BASE)
    note = {"sauer": "pH < 7", "basisch": "pH > 7", "neutral": "pH ≈ 7"}[charakter]
    return Instance(
        params={"stoff": stoff},
        answer=charakter,
        steps=[SolutionStep(text=f"{stoff}: {charakter} ({note}).")])


@_recipe("reaction_type")
def _reaction_type(rng: random.Random) -> Instance:
    """Reaktionstyp bestimmen — Synthese, Analyse, Verbrennung oder Säure-Base-Reaktion."""
    reactants, products, rtype = rng.choice(REACTION_TYPES)
    rc, pc = balance_equation(reactants, products)
    balanced = equation_str(rc, reactants, pc, products)
    return Instance(
        params={"reaktion": balanced},
        answer=rtype,
        steps=[
            SolutionStep(text=f"Reaktionsgleichung: {balanced}"),
            SolutionStep(text=f"{rtype}: {REACTION_TYPE_REASON[rtype]}"),
        ])


_ATOM_COUNT_FORMULAS = [
    "H2O", "CO2", "NH3", "CH4", "H2SO4", "CaCO3", "C6H12O6", "NaCl", "Ca(OH)2", "HNO3",
    "Mg(OH)2", "Al2(SO4)3",                       # nested formulas — the band-3 end
]


@_recipe("atom_count")
def _atom_count(rng: random.Random, difficulty: int | None = None) -> Instance:
    """Teilchenebene: wie viele Atome jeder Sorte (und insgesamt) enthält ein Molekül?

    Difficulty knob: the same structural ladder as `molar_mass` — counting atoms in a
    nested formula (parenthesis multiplication) is the harder skill."""
    formula = rng.choice(_compound_pool(_ATOM_COUNT_FORMULAS, difficulty))
    counts = parse_formula(formula)
    total = sum(counts.values())
    parts = ", ".join(f"{el}: {n}" for el, n in counts.items())
    rows = [SolutionStep(text=f"{ELEMENT_NAMES.get(el, el)} ({el}): {n} Atom(e)")
            for el, n in counts.items()]
    rows.append(SolutionStep(text=f"Gesamtzahl der Atome: {total}"))
    return Instance(
        params={"formel": subscript(formula)},
        answer=f"{parts} — insgesamt {total} Atome",
        steps=rows,
        difficulty=_compound_band(formula),
        context=COMPOUND_CONTEXTS.get(formula))
