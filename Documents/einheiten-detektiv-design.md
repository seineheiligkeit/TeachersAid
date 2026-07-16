# Einheiten-Detektiv — dimensional-analysis puzzles by inverting the units guard

*"Diese Formel kann nicht stimmen — warum?"* A target quantity is shown with a small line-up
of candidate formulas; exactly one is dimensionally correct, the rest are dimensionally
**impossible**. The student is the detective: cross out the formulas that cannot be right and
justify each **over the units**.

This is the physicist's-corner idea from the roadmap ("dimensional-analysis puzzles generated
by INVERTING the `sympy.physics.units` validator"). Module: `teachersaid/pipeline/einheiten.py`.
Recipes: `einheiten_bewegung` · `einheiten_elektrik` · `einheiten_energie`. Templates:
`phy-einheiten-{bewegung,elektrik,energie}` (`library/templates.py`, end of `PARAM_TEMPLATES`).

## The inversion contract

`pipeline/physics.py` computes a school result with `sympy.physics.units` and, before
formatting, `_assert_dimension`s it against the expected unit — a guard that a unit-category
error cannot survive. The Einheiten-Detektiv **runs the same guard backwards**:

- The **shared guard** lives in `pipeline/dimensions.py` (`_base_dims`, `_assert_dimension`,
  `DimensionError`) — extracted from physics.py so both engines build on one primitive with no
  import cycle (physics.py re-exports the names for existing callers). `_base_dims(a) ==
  _base_dims(b)` is base-SI dimensional equality, so `Ω·A` compares equal to `V`.
- A **curated `FormulaSpec`** is a target quantity plus its correct right-hand side as
  `(Quantity, exponent)` factors (e.g. `v = s·¹·t·⁻¹`). At import the composed unit
  `∏ unitᵢ^expᵢ` is `_assert_dimension`-ed against the target — the correct option is correct
  by construction, checked by the very guard we invert.
- Every **distractor** is produced by a catalogued transform applied to the correct factors,
  then **PROVEN wrong at build time**: `_prove_wrong` recomputes its dimension and asserts it
  DIFFERS from the target. A transform that — for some draw — reproduced the target dimension
  is rejected (`_prove_wrong` returns False → skipped), so **no accidental dimensional
  coincidence ever ships as a distractor**. The additive slip is proven wrong by a second
  rigorous route: its two summands carry different base dimensions, so the sum is
  dimensionally *inhomogeneous* — not a well-defined quantity at all.
- The **answer and Begründung are DERIVED**: the impossible set is `{c : dim(c) ≠ dim(target)}`,
  computed; each solution step's unit chain (`[s·t] = m·s, gesucht ist aber m/s → kann nicht
  stimmen`) is built from the same computed dimensions, never authored.

The guarantee is the load-bearing test (`tests/test_einheiten.py`): over 250 seeds × 9 specs,
every distractor's dimension ≠ the target's, the correct option's dimension == the target's,
and exactly one correct option per item.

## The transform catalog (the wrongness layer)

Mirrors the discipline of `grounding/misconceptions.py`: each transform is a **named,
didactically-motivated** way a student mis-assembles a formula, with a curated German label +
one-line description (teacher-guide register) + a provenance note. It lives in
**einheiten.py's own `TRANSFORM_CATALOG`**, not in `grounding/misconceptions.py` (owned by the
MC-distractor track; the Einheiten-Detektiv's wrongness is *dimensional*, a different axis from
the numeric Fehlermuster there — and the transform operates on a formula's structure, not on
drawn numbers).

| id | German name | what it does |
|---|---|---|
| `ratio_inverted` | Zähler und Nenner vertauscht | `t/s` for `s/t` (ratio flipped) |
| `product_for_quotient` | Mal statt geteilt | `s·t` for `s/t` |
| `quotient_for_product` | Geteilt statt mal | `R/I` for `R·I` |
| `sum_for_product` | Plus statt mal (Einheiten ungleich) | `R+I` for `R·I` (inhomogeneous) |
| `factor_dropped` | Eine Größe vergessen | `s` for `s/t` |
| `wrongly_squared` | Größe fälschlich quadriert | `s²/t` for `s/t` (unit-power slip) |

A transform returns `None` when it does not apply to a formula's shape (`sum_for_product` only
for a two-factor product of unlike units; `product_for_quotient` only when there is a
division; …). Each spec yields ≥ 3 applicable, distinct, proven-wrong distractors, so a line-up
of 3–4 candidates (1 correct + 2–3 wrong) is always available; `build_item` raises `Unsuitable`
if fewer than two survive (never fires for the curated specs, but keeps the recipe honest).

## Task kind — open_response (the honest fit)

The candidates are listed, lettered, **in the prompt**, and the response is **ruled lines**:
the student crosses out the impossible formulas and justifies each over the units. Why not the
alternatives:

- `multiple_choice` (the MCSpec machinery) is a self-contained tick-box — it affords **no
  write-space**, but the Begründung ("weil m·s ≠ m/s") is the whole point.
- `true_false_justify` would fit the "judge each + justify" shape, but its candidates live in a
  *payload*, off the prompt — and the variant engine dedups on `str(prompt)`, so a payload-only
  design collapses every same-quantity draw to one prompt (the distinctness test needs 5 of 5).
  Putting the candidates in the prompt keeps every seed's prompt distinct *and* gives genuine
  write-space with a core kind — no engine change, matching the established physics-recipe
  pattern (`{aufgabe}` → `open_response` + `LinesResponse`).

## Anchors

Verbatim Unterstufe PHY competences (`lehrplan/PHY.json`), Klasse 3, `cognitive_level=analyze`
(checking a formula is an Erkenntnis/analysis act — AFB II):

- `phy-einheiten-bewegung` → **PHY.US.3.MEC.01** (Bewegungsgrößen anwenden), dim W —
  `v = s/t`, `s = v·t`, `t = s/v`.
- `phy-einheiten-elektrik` → **PHY.US.3.ELE.01** (Zusammenhang der Grundgrößen der Elektrizität),
  dim E — `U = R·I`, `R = U/I`, `I = U/R`.
- `phy-einheiten-energie` → **PHY.US.3.ENE.01** (Energie, Energieformen), dim W —
  `W = F·s`, `E = P·t`, `P = E/t`.

Ids are `phy-einheiten-*` (not `phy-us-*`) so the locked `test_physics` exact-set assertions
for the `phy-us-`/`phy-os-` packs stay green; the templates still ride the generic `phy-`
family the pack tests iterate.

## What's out (scope)

- **Symbols with compound units** (e.g. `g = 9,81 m/s²`, `E_kin = ½mv²`): excluded so the
  composed unit strings stay legible (every given uses a simple unit symbol — m, s, kg, A, Ω,
  N, J, W). A quantity symbol never coincides with a unit symbol on the same sheet (Energie
  uses `E`, so the Watt unit `W` is never mistaken for the Arbeit symbol). This keeps the
  altitude middle-school; the roadmap's "drop a square" theme is covered by `wrongly_squared`
  (adding a square is the same unit-power lesson) without needing a squared school formula.
- **Numeric evaluation**: the puzzle is purely qualitative (units only) — no numbers to
  compute, so no `_mag`/formatting path. It complements the physics *quantitative* pack rather
  than duplicating it.
- **The Mischpult faders**: the recipe emits no `solution_paths` (Tiefe), no student figure
  (Abstraktion), no `MCSpec` (Offenheit), and the templates carry no `prompt_simple` twin
  (Textlast) — so those faders honestly report *unsupported* via `discover_capabilities`
  (Gerüst's Formulierungshilfen do apply). The capability-drift test locks discovery to the
  mixer's real accept/reject, registry-wide.
