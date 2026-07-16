"""Physics quantitative engine — the physics twin of the sympy maths + chemistry recipes.

Same contract as `pipeline/parametrize.py` / `pipeline/chemistry.py`: a recipe OWNS
sampling + solving and returns an `Instance` (slot values + the DERIVED answer + a worked
Rechenweg). The numbers are **computed**, never authored — so every variant is correct by
construction. The recipes register into the *shared* `_RECIPES` registry, so `make_variants`
/ templates / `compose_variants` drive physics exactly as they drive maths and chemistry.

**The headline feature — dimensional verification.** Every recipe computes with real
`sympy.physics.units` quantities and, before formatting, asserts the result's physical
dimension against the expected unit via `_assert_dimension` (base-SI-dimension equality
through the SI dimension system). A unit-category error — mixing an energy with a power,
a force with a torque's *magnitude* recipe, forgetting a factor of time — cannot survive:
the assertion fails at construction. Correct numbers are necessary but not sufficient; the
UNITS must also be right, and here they are guaranteed. (Caveat, stated honestly: some
distinct quantities share base dimensions — torque N·m and energy J are both
mass·length²·time⁻² — so the guard catches unit *category* errors, not a physicist's
concept confusion between two same-dimension quantities. Each recipe therefore asserts
against the unit it actually intends.)

- `uniform_motion` — v = s/t (gleichförmige Bewegung); solve for v, s or t.
- `density`        — ρ = m/V; solve for ρ, m or V; a variant identifies the material.
- `ohm`            — U = R·I (Ohm'sches Gesetz); solve for U, R or I.
- `resistors`      — Ersatzwiderstand of 2–3 resistors in Reihe / parallel.
- `lever`          — Hebelgesetz F₁·a₁ = F₂·a₂; solve for any of the four.
- `energy_power`   — W = P·t (elektrische Arbeit) and E_pot = m·g·h (Lageenergie).

Einheiten mitführen — the didactic point Austrian physics teachers drill — is visible: the
Rechenweg carries units through every step (Formel → umstellen → einsetzen → ausrechnen).
"""

from __future__ import annotations

import random

from sympy import Integer, Rational, nsimplify
from sympy.physics import units as _u
from sympy.physics.units import convert_to

from ..grounding.physics import (
    MATERIAL_DENSITIES, STANDARD_GRAVITY, density_material_for,
)
from ..schema.blocks import SolutionStep
from ..schema.parametric import Instance
# The dimensional guard is a shared primitive (pipeline/dimensions.py) — extracted so the
# Einheiten-Detektiv can INVERT the very same check this engine uses to PROVE its answers.
# Re-exported here so callers referencing `physics.DimensionError` / `physics._assert_dimension`
# keep working.
from .dimensions import DimensionError, _assert_dimension, _base_dims  # noqa: F401
from .parametrize import Unsuitable, _recipe

# --- units (local aliases; sympy.physics.units) ------------------------------
_m, _s, _kg, _g = _u.meter, _u.second, _u.kilogram, _u.gram
_cm, _h = _u.centimeter, _u.hour
_N, _V, _A, _Ohm, _W, _J = _u.newton, _u.volt, _u.ampere, _u.ohm, _u.watt, _u.joule
_kWh = _u.kilo * _u.watt * _u.hour


def _mag(qty, unit):
    """The scalar magnitude of `qty` expressed in `unit`, as an exact sympy number
    (so rounding/formatting is exact). Converts, then strips the unit."""
    return nsimplify(convert_to(qty, unit) / unit)


# --- German number + unit formatting (shared helper, local to physics) -------
_UNIT_TEX = {
    "m/s": "m/s", "km/h": "km/h", "m": "m", "km": "km", "s": "s", "h": "h",
    "kg": "kg", "g": "g", "kg/m^3": "kg/m³", "g/cm^3": "g/cm³",
    "V": "V", "A": "A", "Ohm": "Ω", "N": "N", "N*m": "N·m",
    "J": "J", "W": "W", "kW": "kW", "kWh": "kWh", "cm": "cm", "L": "l",
}


def _fmt_de(value, dp: int = 2) -> str:
    """German decimal formatting (comma), trailing zeros trimmed. Whole numbers print
    without a decimal part. `value` may be a sympy number or a float."""
    f = float(value)
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    s = f"{f:.{dp}f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _q(value, unit_key: str, dp: int = 2) -> str:
    """A German-formatted quantity string: number + spaced unit ("12,5 m/s")."""
    return f"{_fmt_de(value, dp)} {_UNIT_TEX.get(unit_key, unit_key)}"


# --- context frames (curated, digit-free — the blackboard test) --------------
# One plain German sentence per motion/energy scenario, keyed to the drawn scene. Same
# discipline as the chemistry contexts: selected, never authored at task time, and never
# asserting a number (the Instance validator enforces digit-freeness).
_MOTION_SCENES = [
    ("Radfahrer", "Ein Radfahrer fährt auf einer geraden Strecke gleichmäßig dahin."),
    ("Zug", "Ein Zug fährt mit konstantem Tempo über eine freie Strecke."),
    ("Läuferin", "Eine Läuferin hält beim Training ein gleichmäßiges Tempo."),
    ("Auto", "Ein Auto fährt auf der Autobahn mit gleichbleibender Geschwindigkeit."),
    ("Schnecke", "Eine Schnecke kriecht gemächlich über den Gartenweg."),
    ("Straßenbahn", "Eine Straßenbahn rollt zwischen zwei Haltestellen gleichmäßig dahin."),
]

_ENERGY_LIFT_SCENES = [
    ("Kiste", "Eine Kiste wird im Lager senkrecht nach oben gehoben."),
    ("Wassereimer", "Ein Wassereimer wird aus einem Brunnen hochgezogen."),
    ("Rucksack", "Ein Rucksack wird vom Boden auf ein Regal gehoben."),
    ("Sandsack", "Auf der Baustelle wird ein Sandsack mit einem Seil hochgezogen."),
]

# Each scene carries a REALISTIC wattage band (W) so a chosen power fits the appliance —
# a Wasserkocher draws ~2 kW, a Glühlampe ~40–100 W (magnitude realism the SME checks).
_POWER_SCENES = [
    ("Glühlampe", "Eine alte Glühlampe brennt über einen gewissen Zeitraum.", [40, 60, 100]),
    ("LED-Lampe", "Eine LED-Lampe leuchtet über einen gewissen Zeitraum.", [5, 8, 10]),
    ("Ladegerät", "Ein Ladegerät versorgt ein Handy über eine gewisse Zeit mit Strom.", [5, 10]),
    ("Staubsauger", "Ein Staubsauger läuft beim Putzen eine Weile.", [500, 1000]),
    ("Wasserkocher", "Ein Wasserkocher ist eine bestimmte Zeit lang eingeschaltet.", [2000]),
    ("Heizlüfter", "Ein Heizlüfter läuft über eine gewisse Zeit.", [1000, 2000]),
]


# ============================================================================
# uniform motion: v = s / t
# ============================================================================
@_recipe("uniform_motion")
def _uniform_motion(rng: random.Random) -> Instance:
    """Gleichförmige Bewegung v = s/t — nach v, s oder t auflösen.

    Draws whole-number-friendly (s, t) with a clean quotient, then randomly hides one of
    the three quantities (the other two are given). Distances/times are scene-appropriate
    so magnitudes stay realistic (a Schnecke is cm/s-slow, a Zug is fast)."""
    solve_for = rng.choice(["v", "s", "t"])
    scene_key, context = rng.choice(_MOTION_SCENES)

    # pick a clean velocity + time so distance is exact; scene fixes the scale
    if scene_key == "Schnecke":
        v_val = rng.choice([1, 2, 3, 4, 5])            # cm/s scale, but we work in m/s below
        v = Rational(v_val, 100) * _m / _s             # 0,01–0,05 m/s
        t_val = rng.choice([20, 30, 60, 90, 120])
    elif scene_key in ("Radfahrer", "Läuferin"):
        v_val = rng.choice([3, 4, 5, 6, 8])            # m/s (~11–29 km/h)
        v = v_val * _m / _s
        t_val = rng.choice([10, 12, 15, 20, 30, 60])
    else:                                              # Zug / Auto / Straßenbahn
        v_val = rng.choice([15, 20, 25, 30])           # m/s (~54–108 km/h)
        v = v_val * _m / _s
        t_val = rng.choice([4, 6, 8, 10, 12, 20, 30])
    t = t_val * _s
    s = v * t                                          # exact by construction

    # magnitudes for display
    s_m = _mag(s, _m)
    t_sec = _mag(t, _s)
    v_ms = _mag(v, _m / _s)

    if solve_for == "v":
        _assert_dimension(s / t, _m / _s)              # the computed quantity is a velocity
        given = (f"Dabei wird in {_q(t_sec, 's')} eine Strecke von {_q(s_m, 'm')} zurückgelegt.")
        ask = "Berechne die Geschwindigkeit v."
        steps = [
            SolutionStep(text="Formel der gleichförmigen Bewegung", expr="v = \\frac{s}{t}"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"v = \\frac{{{_fmt_de(s_m)}\\,\\text{{m}}}}{{{_fmt_de(t_sec)}\\,\\text{{s}}}}"),
            SolutionStep(text="ausrechnen", expr=f"v = {_fmt_de(v_ms)}\\,\\frac{{\\text{{m}}}}{{\\text{{s}}}}"),
        ]
        answer = f"v = {_q(v_ms, 'm/s')}"
    elif solve_for == "s":
        _assert_dimension(v * t, _m)                   # the computed quantity is a length
        given = (f"Die Geschwindigkeit beträgt {_q(v_ms, 'm/s')}, die Fahrt dauert {_q(t_sec, 's')}.")
        ask = "Berechne die zurückgelegte Strecke s."
        steps = [
            SolutionStep(text="Formel umstellen (nach s)", expr="s = v \\cdot t"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"s = {_fmt_de(v_ms)}\\,\\frac{{\\text{{m}}}}{{\\text{{s}}}} \\cdot {_fmt_de(t_sec)}\\,\\text{{s}}"),
            SolutionStep(text="ausrechnen (die Sekunden kürzen sich)", expr=f"s = {_fmt_de(s_m)}\\,\\text{{m}}"),
        ]
        answer = f"s = {_q(s_m, 'm')}"
    else:  # t
        _assert_dimension(s / v, _s)                   # the computed quantity is a time
        given = (f"Die Geschwindigkeit beträgt {_q(v_ms, 'm/s')}; zurückgelegt wird eine "
                 f"Strecke von {_q(s_m, 'm')}.")
        ask = "Berechne die dafür benötigte Zeit t."
        steps = [
            SolutionStep(text="Formel umstellen (nach t)", expr="t = \\frac{s}{v}"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"t = \\frac{{{_fmt_de(s_m)}\\,\\text{{m}}}}{{{_fmt_de(v_ms)}\\,\\frac{{\\text{{m}}}}{{\\text{{s}}}}}}"),
            SolutionStep(text="ausrechnen", expr=f"t = {_fmt_de(t_sec)}\\,\\text{{s}}"),
        ]
        answer = f"t = {_q(t_sec, 's')}"

    return Instance(params={"gegeben": given, "frage": ask}, answer=answer,
                    steps=steps, context=context)


# ============================================================================
# density: ρ = m / V
# ============================================================================
@_recipe("density")
def _density(rng: random.Random) -> Instance:
    """Dichte ρ = m/V — nach ρ, m oder V auflösen, oder den Stoff bestimmen.

    Draws a curated material, then a clean volume so the mass is a tidy number; hides one
    of ρ/m/V, OR (the nice variant) gives m and V and asks which material it could be —
    the answer is the curated material whose density matches (correct by curation)."""
    solve_for = rng.choice(["rho", "m", "V", "material"])
    name = rng.choice(list(MATERIAL_DENSITIES))
    rho_val = MATERIAL_DENSITIES[name]                 # kg/m³
    rho = Integer(int(rho_val)) * _kg / _m**3          # all curated values are whole kg/m³

    # choose a volume (in cm³, school-friendly) so mass is a clean gram value
    V_cm3 = rng.choice([10, 20, 50, 100, 200, 250, 500])
    V = Integer(V_cm3) * _cm**3
    m_q = rho * V                                       # exact mass
    m_g = _mag(m_q, _g)
    # keep masses in a sane range (5 g … 5 kg) and reasonably round
    if not (Rational(1, 1) <= m_g <= Rational(5000, 1)):
        raise Unsuitable
    if (m_g * 10) != int(m_g * 10):                     # avoid ugly >1-decimal masses
        raise Unsuitable

    rho_gcm3 = _mag(rho, _g / _cm**3)                   # school unit g/cm³
    V_disp = _fmt_de(V_cm3)

    if solve_for == "rho":
        _assert_dimension(m_q / V, _kg / _m**3)
        given = (f"Ein Körper aus einem unbekannten Material hat die Masse "
                 f"{_q(m_g, 'g')} und das Volumen {V_disp} cm³.")
        ask = "Berechne seine Dichte ρ (in g/cm³)."
        steps = [
            SolutionStep(text="Formel der Dichte", expr="\\rho = \\frac{m}{V}"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"\\rho = \\frac{{{_fmt_de(m_g)}\\,\\text{{g}}}}{{{V_disp}\\,\\text{{cm}}^3}}"),
            SolutionStep(text="ausrechnen",
                         expr=f"\\rho = {_fmt_de(rho_gcm3)}\\,\\frac{{\\text{{g}}}}{{\\text{{cm}}^3}}"),
        ]
        answer = f"ρ = {_q(rho_gcm3, 'g/cm^3')}"
    elif solve_for == "m":
        _assert_dimension(rho * V, _kg)
        given = (f"{name} hat die Dichte {_q(rho_gcm3, 'g/cm^3')}. "
                 f"Ein Stück hat das Volumen {V_disp} cm³.")
        ask = "Berechne seine Masse m (in g)."
        steps = [
            SolutionStep(text="Formel umstellen (nach m)", expr="m = \\rho \\cdot V"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"m = {_fmt_de(rho_gcm3)}\\,\\frac{{\\text{{g}}}}{{\\text{{cm}}^3}} \\cdot {V_disp}\\,\\text{{cm}}^3"),
            SolutionStep(text="ausrechnen (cm³ kürzt sich)", expr=f"m = {_fmt_de(m_g)}\\,\\text{{g}}"),
        ]
        answer = f"m = {_q(m_g, 'g')}"
    elif solve_for == "V":
        _assert_dimension(m_q / rho, _m**3)
        given = (f"{name} hat die Dichte {_q(rho_gcm3, 'g/cm^3')}. "
                 f"Ein Stück hat die Masse {_q(m_g, 'g')}.")
        ask = "Berechne sein Volumen V (in cm³)."
        steps = [
            SolutionStep(text="Formel umstellen (nach V)", expr="V = \\frac{m}{\\rho}"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"V = \\frac{{{_fmt_de(m_g)}\\,\\text{{g}}}}{{{_fmt_de(rho_gcm3)}\\,\\frac{{\\text{{g}}}}{{\\text{{cm}}^3}}}}"),
            SolutionStep(text="ausrechnen", expr=f"V = {V_disp}\\,\\text{{cm}}^3"),
        ]
        answer = f"V = {V_disp} cm³"
    else:  # material — identify the curated stuff from the computed density
        _assert_dimension(m_q / V, _kg / _m**3)
        guess = density_material_for(float(rho_val))
        if guess is None:                              # should not happen for curated draws
            raise Unsuitable
        given = (f"Ein Körper hat die Masse {_q(m_g, 'g')} und das Volumen {V_disp} cm³.")
        ask = "Berechne die Dichte und bestimme, um welchen Stoff es sich handeln könnte."
        steps = [
            SolutionStep(text="Dichte berechnen", expr="\\rho = \\frac{m}{V}"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"\\rho = \\frac{{{_fmt_de(m_g)}\\,\\text{{g}}}}{{{V_disp}\\,\\text{{cm}}^3}} "
                              f"= {_fmt_de(rho_gcm3)}\\,\\frac{{\\text{{g}}}}{{\\text{{cm}}^3}}"),
            SolutionStep(text=f"Vergleich mit Tabellenwerten → {guess}"),
        ]
        answer = f"ρ = {_q(rho_gcm3, 'g/cm^3')} → {guess}"

    return Instance(params={"gegeben": given, "frage": ask}, answer=answer, steps=steps)


# ============================================================================
# Ohm's law: U = R · I
# ============================================================================
@_recipe("ohm")
def _ohm(rng: random.Random) -> Instance:
    """Ohm'sches Gesetz U = R·I — nach U, R oder I auflösen.

    Draws a clean (R, I) so U is tidy, then hides one of the three. Currents are in a
    school range (mA … a few A); resistances in Ω … kΩ. Values chosen so every solve-for
    yields a clean number."""
    solve_for = rng.choice(["U", "R", "I"])
    R_val = rng.choice([5, 10, 20, 25, 50, 100, 200, 220, 500, 1000])
    I_val = rng.choice([Rational(1, 10), Rational(1, 4), Rational(1, 2),
                        Integer(1), Integer(2), Integer(3)])
    R = R_val * _Ohm
    I = I_val * _A
    U = R * I
    U_v = _mag(U, _V)
    if not (Rational(1, 1) <= U_v <= Rational(1000, 1)):   # keep voltages sane
        raise Unsuitable

    I_disp = _fmt_de(I_val)
    R_disp = _fmt_de(R_val)
    U_disp = _fmt_de(U_v)

    if solve_for == "U":
        _assert_dimension(R * I, _V)
        given = (f"An einem Widerstand von {R_disp} Ω liegt ein Strom von {I_disp} A an.")
        ask = "Berechne die Spannung U."
        steps = [
            SolutionStep(text="Ohm'sches Gesetz", expr="U = R \\cdot I"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"U = {R_disp}\\,\\Omega \\cdot {I_disp}\\,\\text{{A}}"),
            SolutionStep(text="ausrechnen (Ω·A = V)", expr=f"U = {U_disp}\\,\\text{{V}}"),
        ]
        answer = f"U = {_q(U_v, 'V')}"
    elif solve_for == "R":
        _assert_dimension(U / I, _Ohm)
        given = (f"An einem Bauteil liegt die Spannung {U_disp} V; es fließt ein Strom "
                 f"von {I_disp} A.")
        ask = "Berechne den Widerstand R."
        steps = [
            SolutionStep(text="Ohm'sches Gesetz nach R umstellen", expr="R = \\frac{U}{I}"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"R = \\frac{{{U_disp}\\,\\text{{V}}}}{{{I_disp}\\,\\text{{A}}}}"),
            SolutionStep(text="ausrechnen (V/A = Ω)", expr=f"R = {R_disp}\\,\\Omega"),
        ]
        answer = f"R = {_q(R_val, 'Ohm')}"
    else:  # I
        _assert_dimension(U / R, _A)
        given = (f"An einem Widerstand von {R_disp} Ω liegt die Spannung {U_disp} V.")
        ask = "Berechne die Stromstärke I."
        steps = [
            SolutionStep(text="Ohm'sches Gesetz nach I umstellen", expr="I = \\frac{U}{R}"),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"I = \\frac{{{U_disp}\\,\\text{{V}}}}{{{R_disp}\\,\\Omega}}"),
            SolutionStep(text="ausrechnen (V/Ω = A)", expr=f"I = {I_disp}\\,\\text{{A}}"),
        ]
        answer = f"I = {_q(I_val, 'A')}"

    return Instance(params={"gegeben": given, "frage": ask}, answer=answer, steps=steps)


# ============================================================================
# Ersatzwiderstand: series and parallel
# ============================================================================
def _clean_parallel(vals: list[int]):
    """Parallel Ersatzwiderstand of the ohm values, as a sympy Rational (exact)."""
    total = sum(Rational(1, v) for v in vals)
    return 1 / total


@_recipe("resistors")
def _resistors(rng: random.Random) -> Instance:
    """Ersatzwiderstand von 2–3 Widerständen in Reihe oder parallel.

    Series is always clean (a sum). Parallel draws are constrained so the result is a
    tidy number (an integer or a one-decimal value) — ugly fractions are rejected and
    resampled (`Unsuitable`), the pedagogical-ugliness discipline."""
    mode = rng.choice(["reihe", "parallel"])
    n = rng.choice([2, 2, 3])                           # favour pairs, allow triples
    # a curated pool that yields many clean parallel combinations
    pool = [2, 3, 4, 6, 10, 12, 20, 30, 60, 100, 200]
    vals = [rng.choice(pool) for _ in range(n)]

    Rq_units = [v * _Ohm for v in vals]
    if mode == "reihe":
        Rges = sum(Rq_units, 0 * _Ohm)
        R_val = _mag(Rges, _Ohm)
        terms = " + ".join(f"{v}\\,\\Omega" for v in vals)
        steps = [
            SolutionStep(text="Reihenschaltung: die Widerstände addieren sich",
                         expr="R_{ges} = R_1 + R_2" + (" + R_3" if n == 3 else "")),
            SolutionStep(text="Werte mit Einheiten einsetzen", expr=f"R_{{ges}} = {terms}"),
            SolutionStep(text="ausrechnen", expr=f"R_{{ges}} = {_fmt_de(R_val)}\\,\\Omega"),
        ]
        listing = " und ".join(f"{_fmt_de(v)} Ω" for v in vals)
        given = f"In einer Reihenschaltung liegen die Widerstände {listing}."
        answer = f"R_ges = {_q(R_val, 'Ohm')}"
    else:  # parallel
        Rges = _clean_parallel(vals)                   # a Rational number of ohms (value only)
        R_val = Rges
        # pedagogical-ugliness guard: reject results worse than one decimal place
        if (R_val * 10) != int(R_val * 10):
            raise Unsuitable
        _assert_dimension(_clean_parallel(vals) * _Ohm, _Ohm)
        inv_terms = " + ".join(f"\\frac{{1}}{{{v}\\,\\Omega}}" for v in vals)
        steps = [
            SolutionStep(text="Parallelschaltung: die Kehrwerte addieren sich",
                         expr="\\frac{1}{R_{ges}} = \\frac{1}{R_1} + \\frac{1}{R_2}"
                              + (" + \\frac{1}{R_3}" if n == 3 else "")),
            SolutionStep(text="Werte mit Einheiten einsetzen",
                         expr=f"\\frac{{1}}{{R_{{ges}}}} = {inv_terms}"),
            SolutionStep(text="Kehrwert bilden und ausrechnen",
                         expr=f"R_{{ges}} = {_fmt_de(R_val)}\\,\\Omega"),
        ]
        listing = " und ".join(f"{_fmt_de(v)} Ω" for v in vals)
        given = f"In einer Parallelschaltung liegen die Widerstände {listing}."
        answer = f"R_ges = {_q(R_val, 'Ohm')}"

    ask = "Berechne den Ersatzwiderstand R_ges."
    return Instance(params={"gegeben": given, "frage": ask}, answer=answer, steps=steps)


# ============================================================================
# Hebelgesetz: F1 · a1 = F2 · a2
# ============================================================================
@_recipe("lever")
def _lever(rng: random.Random) -> Instance:
    """Hebelgesetz F₁·a₁ = F₂·a₂ — eine der vier Größen berechnen.

    Draws three of the four quantities so the fourth is a clean number; forces in N, arms
    in cm. The unknown is hidden at random."""
    solve_for = rng.choice(["F1", "a1", "F2", "a2"])
    # draw the product (torque) cleanly: pick F1,a1 then F2,a2 with equal moment
    F1_val = rng.choice([10, 12, 15, 20, 24, 30, 40, 50, 60])
    a1_val = rng.choice([10, 12, 15, 20, 24, 30, 40, 60])       # cm
    moment = F1_val * a1_val                                    # N·cm
    # choose a2 that divides the moment cleanly → clean F2
    a2_candidates = [d for d in [5, 6, 8, 10, 12, 15, 16, 20, 24, 30, 40, 50, 60, 80]
                     if moment % d == 0 and d != a1_val and 5 <= (moment // d) <= 400]
    if not a2_candidates:
        raise Unsuitable
    a2_val = rng.choice(a2_candidates)
    F2_val = moment // a2_val

    F1 = F1_val * _N
    a1 = Rational(a1_val, 100) * _m
    F2 = F2_val * _N
    a2 = Rational(a2_val, 100) * _m

    labels = {
        "F1": ("die Kraft F₁", f"F₁ = {_q(F1_val, 'N')}"),
        "a1": ("den Kraftarm a₁", f"a₁ = {_fmt_de(a1_val)} cm"),
        "F2": ("die Kraft F₂", f"F₂ = {_q(F2_val, 'N')}"),
        "a2": ("den Kraftarm a₂", f"a₂ = {_fmt_de(a2_val)} cm"),
    }
    known = {
        "F1": f"F₁ = {_fmt_de(F1_val)} N", "a1": f"a₁ = {_fmt_de(a1_val)} cm",
        "F2": f"F₂ = {_fmt_de(F2_val)} N", "a2": f"a₂ = {_fmt_de(a2_val)} cm",
    }
    given_bits = [known[k] for k in ("F1", "a1", "F2", "a2") if k != solve_for]
    given = ("An einem Hebel herrscht Gleichgewicht. Gegeben: "
             + ", ".join(given_bits) + ".")
    ask = f"Berechne {labels[solve_for][0]}."

    # the rearranged formula + a dimensional check on the computed quantity
    if solve_for == "F1":
        _assert_dimension(F2 * a2 / a1, _N)
        formel = "F_1 = \\frac{F_2 \\cdot a_2}{a_1}"
        einsetzen = (f"F_1 = \\frac{{{_fmt_de(F2_val)}\\,\\text{{N}} \\cdot "
                     f"{_fmt_de(a2_val)}\\,\\text{{cm}}}}{{{_fmt_de(a1_val)}\\,\\text{{cm}}}}")
        result = f"F_1 = {_fmt_de(F1_val)}\\,\\text{{N}}"
    elif solve_for == "F2":
        _assert_dimension(F1 * a1 / a2, _N)
        formel = "F_2 = \\frac{F_1 \\cdot a_1}{a_2}"
        einsetzen = (f"F_2 = \\frac{{{_fmt_de(F1_val)}\\,\\text{{N}} \\cdot "
                     f"{_fmt_de(a1_val)}\\,\\text{{cm}}}}{{{_fmt_de(a2_val)}\\,\\text{{cm}}}}")
        result = f"F_2 = {_fmt_de(F2_val)}\\,\\text{{N}}"
    elif solve_for == "a1":
        _assert_dimension(F2 * a2 / F1, _m)
        formel = "a_1 = \\frac{F_2 \\cdot a_2}{F_1}"
        einsetzen = (f"a_1 = \\frac{{{_fmt_de(F2_val)}\\,\\text{{N}} \\cdot "
                     f"{_fmt_de(a2_val)}\\,\\text{{cm}}}}{{{_fmt_de(F1_val)}\\,\\text{{N}}}}")
        result = f"a_1 = {_fmt_de(a1_val)}\\,\\text{{cm}}"
    else:  # a2
        _assert_dimension(F1 * a1 / F2, _m)
        formel = "a_2 = \\frac{F_1 \\cdot a_1}{F_2}"
        einsetzen = (f"a_2 = \\frac{{{_fmt_de(F1_val)}\\,\\text{{N}} \\cdot "
                     f"{_fmt_de(a1_val)}\\,\\text{{cm}}}}{{{_fmt_de(F2_val)}\\,\\text{{N}}}}")
        result = f"a_2 = {_fmt_de(a2_val)}\\,\\text{{cm}}"

    steps = [
        SolutionStep(text="Hebelgesetz (Drehmoment-Gleichgewicht)",
                     expr="F_1 \\cdot a_1 = F_2 \\cdot a_2"),
        SolutionStep(text="nach der gesuchten Größe umstellen", expr=formel),
        SolutionStep(text="Werte mit Einheiten einsetzen", expr=einsetzen),
        SolutionStep(text="ausrechnen", expr=result),
    ]
    return Instance(params={"gegeben": given, "frage": ask},
                    answer=labels[solve_for][1], steps=steps)


# ============================================================================
# energy / power: W = P · t   and   E_pot = m · g · h
# ============================================================================
@_recipe("energy_power")
def _energy_power(rng: random.Random) -> Instance:
    """Energie und Leistung: elektrische Arbeit W = P·t, oder Lageenergie E_pot = m·g·h.

    Two sub-kinds drawn at random. Electrical work is shown in J and (for larger values)
    kWh — the household-energy unit. Lageenergie uses the curated g. Values are chosen so
    the result is clean; magnitudes stay age-appropriate."""
    kind = rng.choice(["work", "epot"])

    if kind == "work":
        scene_key, context, watts = rng.choice(_POWER_SCENES)
        P_val = rng.choice(watts)                              # W, realistic for the scene
        # kWh only makes sense for higher-power appliances over hours; small gadgets → J/s
        use_kwh = P_val >= 500 and rng.random() < 0.6
        P = P_val * _W
        if not use_kwh:                                        # → Joule, seconds
            t_val = rng.choice([10, 20, 30, 60, 120, 300])
            t = t_val * _s
            _assert_dimension(P * t, _J)
            W_J = _mag(P * t, _J)
            given = (f"Ein Gerät ({scene_key}) hat die Leistung {_q(P_val, 'W')} und ist "
                     f"{_q(t_val, 's')} lang in Betrieb.")
            ask = "Berechne die verrichtete elektrische Arbeit W (in Joule)."
            steps = [
                SolutionStep(text="elektrische Arbeit", expr="W = P \\cdot t"),
                SolutionStep(text="Werte mit Einheiten einsetzen (1 W·s = 1 J)",
                             expr=f"W = {_fmt_de(P_val)}\\,\\text{{W}} \\cdot {_fmt_de(t_val)}\\,\\text{{s}}"),
                SolutionStep(text="ausrechnen", expr=f"W = {_fmt_de(W_J)}\\,\\text{{J}}"),
            ]
            answer = f"W = {_q(W_J, 'J')}"
        else:                                                  # → kWh, hours (household unit)
            t_val = rng.choice([1, 2, 3, 4, 5])
            t = t_val * _h
            _assert_dimension(P * t, _J)
            W_kwh = _mag(P * t, _kWh)
            P_kw = _mag(P, _u.kilo * _u.watt)
            given = (f"Ein Gerät ({scene_key}) mit der Leistung {_q(P_kw, 'kW')} läuft "
                     f"{_q(t_val, 'h')} lang.")
            ask = "Berechne die verbrauchte Energie in Kilowattstunden (kWh)."
            steps = [
                SolutionStep(text="elektrische Arbeit", expr="W = P \\cdot t"),
                SolutionStep(text="Leistung in kW, Zeit in h (1 kW · 1 h = 1 kWh)",
                             expr=f"W = {_fmt_de(P_kw)}\\,\\text{{kW}} \\cdot {_fmt_de(t_val)}\\,\\text{{h}}"),
                SolutionStep(text="ausrechnen", expr=f"W = {_fmt_de(W_kwh)}\\,\\text{{kWh}}"),
            ]
            answer = f"W = {_q(W_kwh, 'kWh')}"
        return Instance(params={"gegeben": given, "frage": ask}, answer=answer,
                        steps=steps)

    # E_pot = m · g · h (Lageenergie), curated g
    scene_key, scene_desc = rng.choice(_ENERGY_LIFT_SCENES)
    m_val = rng.choice([2, 3, 5, 8, 10, 12, 20, 25])           # kg
    h_val = rng.choice([1, 2, 3, 4, 5, 6, 10])                 # m
    m = m_val * _kg
    h = h_val * _m
    g = Rational(int(round(STANDARD_GRAVITY * 100000)), 100000) * _m / _s**2  # 9,80665 exact
    Epot = m * g * h
    _assert_dimension(m * g * h, _J)
    E_J = _mag(Epot, _J)
    given = (f"{scene_desc} Die Masse beträgt {_q(m_val, 'kg')}, die Höhe {_q(h_val, 'm')}.")
    ask = "Berechne die zugeführte Lageenergie E_pot (in Joule; g = 9,80665 m/s²)."
    steps = [
        SolutionStep(text="Lageenergie (potenzielle Energie)", expr="E_{pot} = m \\cdot g \\cdot h"),
        SolutionStep(text="Werte mit Einheiten einsetzen",
                     expr=f"E_{{pot}} = {_fmt_de(m_val)}\\,\\text{{kg}} \\cdot "
                          f"9{{,}}80665\\,\\frac{{\\text{{m}}}}{{\\text{{s}}^2}} \\cdot {_fmt_de(h_val)}\\,\\text{{m}}"),
        SolutionStep(text="ausrechnen (kg·m²/s² = J)", expr=f"E_{{pot}} \\approx {_fmt_de(E_J)}\\,\\text{{J}}"),
    ]
    answer = f"E_pot ≈ {_q(E_J, 'J')}"
    return Instance(params={"gegeben": given, "frage": ask}, answer=answer, steps=steps)
