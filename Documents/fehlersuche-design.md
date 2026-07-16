# Fehlersuche — worked solutions with a planted, catalogued error

**Status: built.** Module `teachersaid/pipeline/fehlersuche.py`; schema field
`TaskBlock.flawed_solution`; renderer `rendering/blocks_to_flowables._flawed_chain_flowables`;
three templates at the end of `library/templates.py::PARAM_TEMPLATES`; tests
`tests/test_fehlersuche.py`. This doc is the contract; history lives in `project-handoff.md`.

## The genre

A complete worked solution in which **exactly one step is wrong**; the student finds the wrong
step and corrects it ("Finde und korrigiere den Fehler"). It is the **worked-example twin of the
misconception-MC engine** (`pipeline/misconceive.py`): where that engine computes a wrong
*option* by applying a documented Fehlermuster to the drawn numbers, this one computes a wrong
*step* inside a full worked chain and **propagates** it — every step from the error onward is
arithmetically consistent WITH the error, so a student who follows the flawed logic reproduces
exactly the numbers shown on the sheet.

It rides the parametric engine: a `ParametricTask` + a `recipe` registered into the shared
`_RECIPES` registry, driven through the ordinary `variant_worksheet` path (N deterministic
variants per template). No new pipeline stage, no bespoke worksheet builder.

## The four correct-by-construction guarantees (all test-locked)

1. **The planted step's value ≠ the correct step's value** — the corruption genuinely changes a
   value. Checked exact (every value is an exact `int`/`Rational`), which for lossless formatting
   is *also* a post-formatting inequality (the discipline the MC engine states explicitly).
2. **The flawed final answer ≠ the correct final answer** — the error reaches the result.
3. **The flawed chain is internally consistent** — honest propagation (a student following the
   flawed step reproduces the shown numbers; the tests recompute the shown values independently
   from the drawn numbers and the named Fehlermuster).
4. **Deterministic per seed** — same seed → identical flawed chain, correct chain, answer_key.

A recipe raises `Unsuitable` (in the shared `_build` helper) if a draw makes the corruption a
no-op (the planted step or the final equals the correct one) — we never ship a no-op "error".

## The audience split (the load-bearing boundary)

The flawed chain is the **object of study**; everything that would give the game away is
teacher-only. The split is enforced by *which field* each piece lands on and the existing pure
projection rules in `rendering/blocks_to_flowables.py`:

| Piece | Field | Renders on |
|---|---|---|
| the flawed worked chain | `TaskBlock.flawed_solution` (`list[SolutionStep]`) | **student + homework + teacher** (`_flawed_chain_flowables`, on every projection — the teacher sees the same artifact to point at) |
| the correct worked chain | `TaskBlock.solution_steps` | teacher only ("Rechenweg") |
| the located wrong step + Fehlermuster name + source + the correction | `TaskBlock.answer_key` | teacher only ("Lösung: …") |
| the student's answer surface (name + correct the error) | `response = LinesResponse(n=3)` | student + homework (open_response is not self-contained) |

**Why the located step rides `answer_key`, not `watch_outs`.** `watch_outs` is *not* strictly
teacher-only: the homework projection surfaces every watch-out as a "Tipp:" (a deliberate
"no-teacher-present" hint). A watch-out naming "Schritt 2" would therefore **leak the error
location onto the homework sheet**. So the recipe leaves `watch_outs` empty and folds the whole
teacher-facing message — `"Gepflanzter Fehler in Schritt N: <Fehlermuster> (<Quelle>). <fix>"` —
into `answer_key`, which renders only under the teacher branch. (This is why `Instance.watch_outs`
was considered and dropped.) The student/homework sheets show the flawed chain but never the word
"Gepflanzter Fehler", the "Rechenweg", nor the correct answer — locked by the render test.

The flawed chain never marks *which* step is wrong: it renders identically on all three
projections (a plain numbered "Vorgelegte Lösung — genau ein Schritt ist falsch:" list). The
teacher finds the step from `answer_key`.

## Select-never-author: the Fehlermuster are catalogued

The engine **plants** errors, but it does not **invent** them. Each corruption is one of the
curated, literature-sourced Fehlermuster in `grounding/misconceptions.py` — the same provenance
layer the MC engine draws on. `fehlersuche._USED_FEHLERMUSTER` names the four ids used and
validates them against the catalog **at import** (a mistyped id fails loudly, the Fehlersuche
analogue of the `@_misconception` check). No new catalog entries were needed:

| Template (recipe) | Fehlermuster (catalog id) | planted at | the error |
|---|---|---|---|
| lineare Gleichung (`fehlersuche_linear_equation`) | `sign_error` (Radatz/Malle) **or** `inverse_operation` (Malle), chosen per draw | Schritt 2 / Schritt 3 | `x=(c+b)/a` (added, not subtracted) / `x=(c−b)·a` (multiplied, not divided) |
| Bruchaddition (`fehlersuche_fraction_add`) | `fraction_add_across` (Padberg & Wartha) | Schritt 2 | `(a+c)/(b+d)` instead of over the common denominator |
| Prozentrechnung (`fehlersuche_percentage`) | `unit_power_ten` (Radatz) | Schritt 2 | `p%` → `p/10` instead of `p/100` (Komma-/Stellenwertfehler, ×10) |

The linear-equation recipe randomly plants one of two Fehlermuster, so the **error location varies
across the variant series** (Schritt 2 vs. 3) — a student cannot learn "it's always step 2".

The correct chain (`solution_steps`), the located step and the correction (`answer_key`) are all
**derived** from the same drawn numbers — never hand- or LLM-authored. `flawed_solution` is absent
from the generation view (`GenTaskBlock`), so the model literally cannot emit it (like
`solution_steps`/`scaffold`).

## Seams / modules

- **`pipeline/fehlersuche.py`** — the engine: three `@_recipe` recipes + the shared `_build`
  (guarantee gate + `Instance` assembly) + the German/fraction formatters + the catalog-id check.
  Imported at the end of `pipeline/parametrize.py` (append-only, like `chemistry`/`finanz`/`wahl`).
- **`schema/blocks.py`** — `TaskBlock.flawed_solution: list[SolutionStep]` (student-facing,
  derived; sibling of `solution_steps`/`scaffold`).
- **`schema/parametric.py`** — `Instance.flawed_solution` (the recipe's channel to the block).
- **`pipeline/parametrize.py::_instantiate`** — copies `inst.flawed_solution` onto the block.
- **`rendering/blocks_to_flowables.py::_flawed_chain_flowables`** — renders the numbered flawed
  chain on every projection, reusing the Rechenweg step layout (text + inline-math `expr`), so a
  fraction/equation typesets. A **new render path**, so it carries a render test (the CLAUDE
  "assemble/verify don't render" rule).
- **`library/templates.py`** — three templates at the end of `PARAM_TEMPLATES`, anchored to the
  verbatim MAT.US competences their arithmetic-drill twins use (VAR.02, ZAH.03, ZAH.04); kind
  `open_response`, cognitive_level `analyze`.

## Deliberately out (scope)

- **No new task kind.** `open_response` honestly affords "name the step + correct it" on the
  lines; a bespoke kind would need wiring in assemble/render/prompts for no gain.
- **No new Fehlermuster.** The catalog already covered the three strongest MAT cases; adding
  entries would mean new provenance to SME-vet for no coverage win. (Extending the catalog for a
  future PHY/CHE Fehlersuche is the natural growth path.)
- **One error per chain.** "Find *all* the errors" / multi-error chains are out — the single
  planted, catalogued error is the whole correct-by-construction claim.
- **The flawed chain masks nothing beyond the answer.** Unlike a figure that masks the asked
  unknown, here the flawed *result* is shown (it is the object of study); only the *correct* chain
  and the *location* are withheld.
- **No LLM.** Fully deterministic; `flawed_solution` is absent from generation views.
