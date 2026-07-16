# Fermi-Werkstatt — estimation as a curated decomposition chain

**Status:** **BUILT (16 Jul 2026).** A content program in the shape of `pipeline/finanz.py`:
curated, provenance-stamped quantities drive a **computed** worked chain, point estimate and
propagated acceptable range. Modules: `schema/fermi.py` (the typed input model),
`grounding/fermi.py` (the curated anchors + 6 problems), `pipeline/fermi.py` (interval
arithmetic + `build_worksheet`), `library.seed_fermi` (the staging seam — written, never run
here), `tests/test_fermi.py` (38). Anchored to verbatim MAT competences under the **MOD**
(Modellieren und Problemlösen) handlungsdimension. Verify-clean, all three projections render,
full suite green. Author-of-record: SME + Claude.

**Scope of this doc:** the anchor provenance discipline, the range-propagation contract, the
given-vs-estimated split (and the leak guard that rests on it), and what is deliberately out.

---

## 0. The organizing principle — *the honest estimate*

A Fermi problem ("Wie viele Klavierstimmer:innen gibt es in Wien?") is the **archetype of a
selbstdifferenzierende Modellierungsaufgabe**: you decompose the unknown into a short chain of
quantities you *can* estimate, combine them arithmetically, and check the order of magnitude.
There is no single right number — a rough solver uses two crude assumptions, a fine solver
decomposes carefully and reflects on the spread. Both can be *right*, because **the answer is a
range and an order of magnitude, not a value.**

The correctness machinery (invariants §3, §4) applies with a twist. The *facts* are still
selected/curated (anchor values are cited datasets, published figures, or explicitly-flagged
vetted estimates — never bare inventions), and the *derivation* (the chain, the range) is
**computed**, never authored. But the pedagogical point is precisely that most anchors are
**reasoned estimates**, not looked-up facts. So the discipline is not "cite everything" (there
is no dataset for *sheets of paper per pupil per day*) — it is:

> **Every anchor either cites a source or is explicitly MARKED as a vetted estimate carrying a
> plausibility rationale.** No quantity is dressed as a fact it isn't. The SME fact-checks the
> rationales; the computed range keeps the teacher's grading honest.

---

## 1. The anchor provenance discipline (`schema/fermi.py`, `grounding/fermi.py`)

A **`FermiAnchor`** is one quantity: `value`, honest bounds `[low, high]`, a `unit`, and exactly
one `provenance` (a discriminated union — every anchor carries one, there is **no bare invented
fact**):

| Provenance | When | Citation | Example |
|---|---|---|---|
| **`FermiDatasetRef`** | the value is SELECTED from a curated `grounding/data/` dataset | rides the dataset's `SourceRef`; a drift test locks it | `einwohner_wien` (2 005 760, Bundesländer-Datensatz); `lebenserwartung_at` |
| **`FermiCitation`** | an everyday quantity with a real external published source | a `SourceRef` naming the authority | `personen_pro_haushalt` (~2,2, Statistik Austria) |
| **`FermiEstimate`** | no dataset exists — an **authored-then-vetted** plausibility estimate | a `rationale` that makes the value + band defensible | `wasser_pro_person_schultag`, `klavier_anteil`, … |

Hard invariant (schema-enforced): `low <= value <= high` and `low > 0` (every Fermi quantity is
strictly positive — interval division and the order-of-magnitude framing assume it).

**Exact definitional conversions** (`minuten_pro_tag`=1440, `tage_pro_jahr`=365,
`schultage_woche`=5) are modelled as `FermiEstimate` with `low == high == value` and a rationale
that says "exakt". They therefore contribute **no width** to the propagated range — correct: a
unit conversion adds no uncertainty. `anchor.is_exact()` reports this.

A `cited` or `dataset` anchor may sit on the **estimated** side of a problem (the student
estimates the average household size; the citation is our *defensible ground truth* for the
teacher's range, not a value we hand the student). Provenance is about *where the number comes
from*, orthogonal to *who estimates it on the sheet* (§3).

**Anti-rot.** `tests/test_fermi.py` locks the dataset-backed anchors against the live dataset
(`einwohner_wien` == the Wien count; `lebenserwartung_at` within the cited m/w band), so a
dataset refresh can't silently rot an anchor — the same discipline as the `number_lint` anti-rot
check on figures.

---

## 2. The range-propagation contract (`pipeline/fermi.py`)

Two things are DERIVED from the chain (never authored):

**The point estimate + worked chain.** The chain is evaluated at every anchor's `value` as an
exact `Decimal` product/quotient/sum, producing the teacher-only `solution_steps` (the
Rechenweg) and the headline `Bezugswert`. `evaluate_chain` and an independent reference
evaluator agree (test-locked), and the chain reproduces hand-computed points
(`herzschlaege_leben` = 70·1440·365·82 = 3 016 944 000 exactly).

**The acceptable range** — the anchor `[low, high]` bands propagated through the SAME chain by
**interval arithmetic** (all quantities strictly positive):

```
multiply:  [a,b] · [c,d] = [a·c, b·d]
divide:    [a,b] / [c,d] = [a/d, b/c]
add:       [a,b] + [c,d] = [a+c, b+d]      (the first step must be multiply — it seeds from 1)
```

Each anchor appears **once** per chain, so there is no interval-dependency over-widening — the
propagated `[low, high]` is the honest plausible band.

**Convention (what the teacher sees).** We present three nested honesty frames, coarsest last:

1. **Bezugswert** — the point estimate (`answer_key`, at `problem.sig` significant figures; Fermi
   answers are honest to ~1–2 sig figs, precision beyond that is fake).
2. **Plausibler Bereich** — the raw propagated interval (`acceptable_reasoning` — the "RANGE"
   field's intended use).
3. **Größenordnung** — the order-of-magnitude *span* of the interval (floor of log₁₀ of each
   endpoint). This is the coarsest, most defensible grading frame: *"richtig = richtige
   Größenordnung; der Rechenweg zählt mehr als die Zahl."* When the band spans several powers of
   ten, that is stated ("die Schätzungen streuen über N Zehnerpotenzen") — honest about how wide
   "plausible" really is.

The range is **monotone**: widening any anchor's band widens the result (test-locked — the
selbstdifferenzierend payoff is that the *machinery* proves it). Per-anchor **sanity lines**
(`{label}: Bezugswert X (plausibel low–high) — {provenance}`) are derived for the teacher so the
width is legible: *where* the spread comes from.

---

## 3. The given-vs-estimated split + the leak guard

Each `ChainStep` carries `given: bool` — a **per-problem curated choice** (the same anchor may be
given in one problem, estimated in another). It is the load-bearing distinction for the
projection split:

- **Given** anchors (a known fact the problem provides — Wien's population, the min/day
  conversion) are printed on the student sheet in a "Das ist gegeben" box, rounded.
- **Estimated** anchors are the quantities the student must decompose to and estimate themselves.
  Their values — and the point estimate and the range — are **teacher-only**.

The student/homework projection therefore gets: the Fermi question, the given facts, a **blank
Annahmen-Raster** (`table_fill`, five empty rows — invites decomposition WITHOUT dictating the
chain: fill two rows rough or five rows fine) and a **compute box** (`modelling_task`,
`BoxResponse`). The estimated anchor *labels* are never printed student-facing — the student is
not told *which* quantities to estimate (that is the modelling work); the teacher scaffolds live
(the `teacher_overview` talking-points say so).

**The leak guard** (test-locked, `tests/test_fermi.py`): render each projection to PDF, extract
text, and assert the point estimate, both range bounds, and every estimated anchor label are
**present in the teacher guide and absent from BOTH the student and homework sheets**. Homework
is student-facing, so secret values are kept out of `watch_outs` too (which render on homework) —
the per-problem `watch_outs` are qualitative over-/under-estimate *patterns*, never a value.

This works structurally because the renderer gates `answer_key` / `acceptable_reasoning` /
`solution_steps` to the teacher projection (invariants §1) — the same reason the answer key can't
drift from the task.

---

## 4. Anchoring — verbatim MAT competences under MOD

The dimension is always **MOD** (Modellieren und Problemlösen) — a Fermi problem *is* a modelling
task, and the kind is `modelling_task` (a MAT `task_kind_extension`). The **served competence** is
the content competence whose quantities the chain computes (the honest anchor, following the
`mat-dreisatz` precedent of a modelling task serving a ZAH competence):

| Problem | Klasse | Competence (verbatim) |
|---|---|---|
| Papierverbrauch der Schule | 2 | `MAT.US.2.ZAH.04` (Proportionalitäten und Prozente) |
| Trinkwasser der Schule · Schulweg-km · Herzschläge | 3 | `MAT.US.3.ZAH.01` (rationale Zahlen, Rechenoperationen) |
| Luftballons im Klassenzimmer | 3 | `MAT.US.3.FIG.03` (Rauminhalt — the room is a Quader) |
| Klavierstimmer:innen in Wien | 4 | `MAT.US.4.ZAH.01` (reelle Zahlen, **Näherungswerte**) |

Anchor mode is `competence` (these genuinely exercise the competence). `build_worksheet` narrows
the Nachweis with `resolve_kompetenzbereich` (like `finanz` inflation), so coverage is clean.
There is no MOD *competence* to serve (MOD is a handlungsdimension, not a Kompetenzbereich) — the
dimension carries the modelling claim, the served competence carries the arithmetic/Größen claim.

---

## 5. Deliberately out

- **No grading engine.** The range is **teacher-judgment support**, not an auto-grader. We compute
  a defensible band and an order of magnitude; the teacher judges the student's *reasoning*. (We
  make the material, we don't run the room — invariants §7.)
- **No parametric variants.** Each problem is a single curated decomposition, not a seeded family
  (unlike `library/templates.py`). The selbstdifferenzierung comes from the open scaffold, not
  from N seeds.
- **No figures.** A Fermi sheet is prose + a blank table; adding a chart would only invite a
  number-lint/figure-lint surface for no didactic gain. (A future volume sketch for
  `klassenzimmer_ballons` is a possible enrichment, not a requirement.)
- **`add` is supported but unused** by the six curated problems (all are multiply/divide chains);
  it is in the op vocabulary + evaluator + tests for the occasional additive component.

## 6. Breadth

New problem = one `FermiProblem` (question + chain) over existing or new anchors; new anchor =
one `FermiAnchor` with its provenance. No engine change. The natural next seams: a
`tools/fermi_prompt.py` / `ingest_fermi.py` breadth pair (subagents propose problems + anchor
rationales → SME gate), and pulling more anchors from the growing `grounding/data/` catalog as
dataset-backed givens.
