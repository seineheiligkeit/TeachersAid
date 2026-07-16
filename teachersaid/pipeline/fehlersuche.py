"""Fehlersuche engine — worked solutions with exactly one PLANTED, catalogued error.

Roadmap item (greenlit 11 Jul 2026). The worked-example twin of the misconception-MC engine
(`pipeline/misconceive.py`): where that engine computes a wrong OPTION by applying a documented
Fehlermuster to the drawn numbers, this one computes a wrong STEP inside a complete worked
solution and PROPAGATES it — every step from the error onward is arithmetically consistent WITH
the error, so a student who follows the flawed logic reproduces exactly the numbers shown. The
genre is "Finde und korrigiere den Fehler".

Audience split (the load-bearing boundary):
  * the FLAWED chain is the STUDENT-FACING object of study → `Instance.flawed_solution`, which
    `pipeline/parametrize._instantiate` copies onto `TaskBlock.flawed_solution` (rendered on the
    student AND homework sheet);
  * the CORRECT chain → `Instance.steps` → `TaskBlock.solution_steps` (teacher-only);
  * the located wrong step + the Fehlermuster name + its literature source + the correction →
    `Instance.answer` → `TaskBlock.answer_key` (teacher-only). Deliberately NOT `watch_outs`,
    which the homework projection surfaces as a "Tipp:" and would leak the error location.
  The student sheet therefore shows the flawed chain but never which step is wrong nor the
  correct answer.

Correct by construction, all deterministic per seed and test-locked:
  * the planted step's value ≠ the correct step's value (exact, hence also post-formatting —
    every value here is an exact int/`Rational`, formatted losslessly);
  * the flawed final answer ≠ the correct final answer;
  * the flawed chain is internally consistent (honest propagation).

The Fehlermuster are SELECTED from the curated, literature-sourced catalog
(`grounding/misconceptions.py`) — the same provenance layer the MC engine draws on. No new
patterns are invented here; the four reused ids are validated against the catalog at import.
A recipe raises `Unsuitable` to reject a degenerate draw (a corruption that happens to reproduce
the correct value) and be resampled. Recipes register into the SHARED parametric registry
(`pipeline/parametrize._RECIPES`), so the curated `ParametricTask` templates drive them through
the same `variant_worksheet` path as every other parametric genre.
"""

from __future__ import annotations

import math
import random

from sympy import Rational, latex

from ..grounding import misconceptions as _cat
from ..schema.blocks import SolutionStep
from ..schema.parametric import Instance
from .parametrize import Unsuitable, _recipe

# The catalogued Fehlermuster this engine plants. Validated at import — a mistyped id fails loudly
# here (the Fehlersuche analogue of the `@_misconception` catalog check), never silently at runtime.
_USED_FEHLERMUSTER: tuple[str, ...] = (
    "sign_error", "inverse_operation", "fraction_add_across", "unit_power_ten",
)
for _mid in _USED_FEHLERMUSTER:
    _cat.get(_mid)  # raises KeyError if a referenced Fehlermuster is not in the curated catalog


# --- shared helpers ----------------------------------------------------------
def _de(value, dp: int = 2) -> str:
    """German decimal (comma), trailing zeros trimmed; a whole number prints without a decimal
    part (`_de(20) → '20'`, `_de(Rational(1, 4)) → '0,25'`)."""
    f = float(value)
    if f == int(f):
        return str(int(f))
    return f"{f:.{dp}f}".rstrip("0").rstrip(".").replace(".", ",")


def _frac(value: Rational) -> str:
    """A reduced fraction 'p/q' (integer if q == 1) for plain-text prose (the teacher answer_key —
    LaTeX `\\frac` would print literally in a non-math run)."""
    r = Rational(value)
    return str(r.p) if r.q == 1 else f"{r.p}/{r.q}"


def _fehlermuster_tag(mid: str) -> str:
    """'<German name> (<source lead>)' for the teacher answer_key — the curated name + the first
    author of the literature source (mirrors the MC engine's 'B prüft: … (Radatz)' provenance tag)."""
    m = _cat.get(mid)
    src = m.source.split("(")[0].strip().rstrip(",") or m.source
    return f"{m.name} ({src})"


def _build(*, params: dict, correct_steps: list[SolutionStep], flawed_steps: list[SolutionStep],
           wrong_index: int, mid: str, step_correct, step_flawed, correct_final, flawed_final,
           correction: str) -> Instance:
    """Assemble the `Instance`, enforcing the two hard guarantees. `step_correct`/`step_flawed`
    are the corrupted step's correct vs. planted VALUES; `correct_final`/`flawed_final` the two
    end results (all exact ints/`Rational`s). Raises `Unsuitable` if the corruption vanished (the
    planted step or the final answer equals the correct one) — we never ship a no-op error."""
    if step_flawed == step_correct or flawed_final == correct_final:
        raise Unsuitable
    answer = (f"Gepflanzter Fehler in Schritt {wrong_index}: {_fehlermuster_tag(mid)}. "
              f"{correction}")
    return Instance(params=params, answer=answer, steps=list(correct_steps),
                    flawed_solution=list(flawed_steps))


# --- lineare Gleichung: sign_error (Schritt 2) ODER inverse_operation (Schritt 3) ------------
@_recipe("fehlersuche_linear_equation")
def _fehlersuche_linear_equation(rng: random.Random) -> Instance:
    """a·x + b = c mit ganzzahliger Lösung; genau ein Umformungsschritt ist falsch.

    Der gepflanzte Fehler ist einer von zwei katalogisierten Umform-Fehlmustern, zufällig
    gewählt — so wandert die Fehlerstelle über die Varianten (Schritt 2 bzw. 3):
      * `sign_error` (Vorzeichenfehler, Radatz/Malle): der konstante Term wird beim Umstellen
        ADDIERT statt subtrahiert → x = (c+b)/a statt (c-b)/a;
      * `inverse_operation` (Umkehroperation verwechselt, Malle): statt durch den Koeffizienten
        zu dividieren, wird MULTIPLIZIERT → x = (c-b)·a statt (c-b)/a.
    b = a·k (k ≥ 1) hält beide falschen Werte ganzzahlig, damit die vorgelegte Rechnung sauber
    aussieht (der Fehler steckt in der Logik, nicht in krummen Zahlen)."""
    a = rng.randint(2, 9)
    xs = rng.randint(2, 9)
    k = rng.randint(1, 4)
    b = a * k                                     # > 0, Vielfaches von a → saubere Falschwerte
    c = a * xs + b
    eq = f"{a}x + {b} = {c}"
    correct_steps = [
        SolutionStep(text="Ausgangsgleichung", expr=eq),
        SolutionStep(text="den konstanten Term subtrahieren (auf die rechte Seite bringen)",
                     expr=f"{a}x = {c} - {b} = {c - b}"),
        SolutionStep(text="durch den Koeffizienten dividieren",
                     expr=f"x = \\frac{{{c - b}}}{{{a}}} = {xs}"),
    ]
    variante = rng.choice(["sign_error", "inverse_operation"])
    if variante == "sign_error":
        wrong = xs + 2 * k                        # (c + b)/a
        wrong_index = 2
        step_correct, step_flawed = c - b, c + b
        flawed_steps = [
            SolutionStep(text="Ausgangsgleichung", expr=eq),
            SolutionStep(text="den konstanten Term auf die rechte Seite bringen",
                         expr=f"{a}x = {c} + {b} = {c + b}"),
            SolutionStep(text="durch den Koeffizienten dividieren",
                         expr=f"x = \\frac{{{c + b}}}{{{a}}} = {wrong}"),
        ]
        correction = (f"Beim Umstellen muss {b} subtrahiert werden, nicht addiert: "
                      f"{a}x = {c} - {b} = {c - b}, also x = {xs}.")
    else:                                         # inverse_operation
        wrong = (c - b) * a                       # (c - b)·a
        wrong_index = 3
        step_correct, step_flawed = xs, wrong
        flawed_steps = [
            SolutionStep(text="Ausgangsgleichung", expr=eq),
            SolutionStep(text="den konstanten Term subtrahieren (auf die rechte Seite bringen)",
                         expr=f"{a}x = {c} - {b} = {c - b}"),
            SolutionStep(text="den Koeffizienten auf die andere Seite bringen",
                         expr=f"x = {c - b} \\cdot {a} = {wrong}"),
        ]
        correction = (f"Um x zu isolieren, muss durch {a} DIVIDIERT werden, nicht multipliziert: "
                      f"x = ({c - b}) : {a} = {xs}.")
    return _build(params={"eq": eq}, correct_steps=correct_steps, flawed_steps=flawed_steps,
                  wrong_index=wrong_index, mid=variante,
                  step_correct=step_correct, step_flawed=step_flawed,
                  correct_final=xs, flawed_final=wrong, correction=correction)


# --- Bruchaddition: fraction_add_across (Schritt 2) ------------------------------------------
@_recipe("fehlersuche_fraction_add")
def _fehlersuche_fraction_add(rng: random.Random) -> Instance:
    """a/b + c/d (verschiedene Nenner); der gepflanzte Fehler ist die hartnäckigste
    Bruch-Fehlvorstellung `fraction_add_across` (Padberg & Wartha): Zähler und Nenner werden
    getrennt addiert → (a+c)/(b+d) statt über den gemeinsamen Nenner. Die richtige Rechnung
    erweitert, addiert die Zähler und kürzt."""
    b0 = rng.choice([2, 3, 4, 5, 6, 8])
    d0 = rng.choice([2, 3, 4, 5, 6, 8])
    a0 = rng.randint(1, b0 - 1)
    c0 = rng.randint(1, d0 - 1)
    # Reduce FIRST, then work from the reduced numerators/denominators, so the SHOWN fractions
    # and the add-across arithmetic use the SAME numbers (a student following the flawed "Zähler
    # +Zähler / Nenner+Nenner" step must reproduce the shown values). `Rational` auto-reduces, so
    # a raw draw like 3/6 would otherwise display "1/2" but compute over 3 and 6 — a leak of
    # inconsistency. Reduced proper fractions have q ≥ 2.
    f1, f2 = Rational(a0, b0), Rational(c0, d0)
    a, b, c, d = f1.p, f1.q, f2.p, f2.q
    if b == d:
        raise Unsuitable                          # different denominators (also rejects f1 == f2)
    total = f1 + f2
    lcm = b * d // math.gcd(b, d)
    n1, n2 = a * (lcm // b), c * (lcm // d)
    expanded = f"\\frac{{{n1}}}{{{lcm}}} + \\frac{{{n2}}}{{{lcm}}}"
    correct_steps = [
        SolutionStep(text="auf den gemeinsamen Nenner erweitern",
                     expr=f"{latex(f1)} + {latex(f2)} = {expanded}"),
        SolutionStep(text="die Zähler addieren", expr=f"= \\frac{{{n1 + n2}}}{{{lcm}}}"),
        SolutionStep(text="so weit wie möglich kürzen", expr=f"= {latex(total)}"),
    ]
    wrong = Rational(a + c, b + d)                # Zähler+Zähler / Nenner+Nenner
    flawed_steps = [
        SolutionStep(text="Ausgangsterm", expr=f"{latex(f1)} + {latex(f2)}"),
        SolutionStep(text="Zähler und Nenner jeweils getrennt addieren",
                     expr=f"= \\frac{{{a} + {c}}}{{{b} + {d}}} = \\frac{{{a + c}}}{{{b + d}}}"),
        SolutionStep(text="das Ergebnis", expr=f"= {latex(wrong)}"),
    ]
    correction = (f"Brüche werden nicht durch getrenntes Addieren von Zähler und Nenner addiert, "
                  f"sondern über den gemeinsamen Nenner ({lcm}): "
                  f"{_frac(f1)} + {_frac(f2)} = {_frac(total)}.")
    return _build(params={"f1": latex(f1), "f2": latex(f2)}, correct_steps=correct_steps,
                  flawed_steps=flawed_steps, wrong_index=2, mid="fraction_add_across",
                  step_correct=total, step_flawed=wrong, correct_final=total, flawed_final=wrong,
                  correction=correction)


# --- Prozentrechnung: unit_power_ten als Komma-/Stellenwertfehler (Schritt 2) ----------------
@_recipe("fehlersuche_percentage")
def _fehlersuche_percentage(rng: random.Random) -> Instance:
    """p % von G; der gepflanzte Fehler ist ein Stellenwert-/Kommafehler `unit_power_ten`
    (Radatz): beim Umwandeln in eine Dezimalzahl wird durch 10 statt durch 100 dividiert
    (Komma um eine Stelle verschoben) → der Prozentwert wird um den Faktor 10 zu groß. Die
    Dezimalzahlen stehen als Klartext (deutsches Komma), nicht in der mathtext-Formel."""
    base = rng.choice([40, 60, 80, 120, 140, 160, 200, 240, 300, 400])
    pct = rng.choice([5, 10, 15, 20, 25, 50])
    if (base * pct) % 100 != 0:
        raise Unsuitable                          # W ganzzahlig halten (saubere Anzeige)
    w = base * pct // 100
    w_wrong = base * pct // 10                     # 10·W
    d, d_wrong = Rational(pct, 100), Rational(pct, 10)
    d_str, dw_str, w_str = _de(d), _de(d_wrong), _de(w)
    formula = "W = G \\cdot \\frac{p}{100}"
    correct_steps = [
        SolutionStep(text="Prozentwert-Formel ansetzen", expr=formula),
        SolutionStep(text=f"{pct} % als Dezimalzahl (durch 100 dividieren): {d_str}"),
        SolutionStep(text=f"den Grundwert mit der Dezimalzahl multiplizieren: "
                          f"{base} · {d_str} = {w_str}"),
    ]
    flawed_steps = [
        SolutionStep(text="Prozentwert-Formel ansetzen", expr=formula),
        SolutionStep(text=f"{pct} % als Dezimalzahl: {dw_str}"),
        SolutionStep(text=f"den Grundwert mit der Dezimalzahl multiplizieren: "
                          f"{base} · {dw_str} = {_de(w_wrong)}"),
    ]
    correction = (f"{pct} % sind {d_str} (durch 100, nicht durch 10 — {dw_str} wäre "
                  f"{pct * 10} %): {base} · {d_str} = {w_str}.")
    return _build(params={"pct": pct, "base": base}, correct_steps=correct_steps,
                  flawed_steps=flawed_steps, wrong_index=2, mid="unit_power_ten",
                  step_correct=d, step_flawed=d_wrong, correct_final=w, flawed_final=w_wrong,
                  correction=correction)
