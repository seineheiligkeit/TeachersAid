# Difficulty as a computed, advisory quantity (roadmap C4)

**Status:** built. Code: `pipeline/difficulty_model.py` (features + model), `pipeline/difficulty_weights.json`
(the persisted, reviewable model), `tools/fit_difficulty.py` (the offline fit + report),
`pipeline/verify.py` (the advisory warning), `stats.py::difficulty_review_cues` + `GET /api/difficulty/cues`
(the Einblicke surface). Tests: `tests/test_difficulty_model.py`.

## What this is — and the discipline

`pipeline/difficulty.py` already gives every task an **effective difficulty** (1 leicht · 2 mittel · 3
anspruchsvoll): the author/SME `difficulty` if one is set, else the Anforderungsbereich of the task's
`cognitive_level`. C4 adds a **second, independent opinion** — a difficulty *estimated from the task's
own surface features* — used for exactly one thing: to **flag a task for SME review when the two
disagree by ≥1 band**.

The discipline is **DERIVED + ADVISORY**, and it is load-bearing:

> The computed estimate **never overrides** the authored `difficulty`. A ≥1-band disagreement becomes a
> verify **warning** (the advisory lane, next to readability/WSTF and number-lint) and a dashboard
> signal — a *review cue*, never a correction, never a gate.

This mirrors the readability advisory: a heuristic that *flags for a human*, chosen precisely because
the underlying quantity cannot be measured. We deliberately collect **no student-response data**, so
there is no psychometric calibration here and never will be — difficulty is an estimate, honestly bounded.

## The load-bearing finding: this model is *not learnable* from the corpus

The brief was to "load the authored labels from the block corpus and fit the ordinal model." The
corpus (`store/blockstore.py`, ~1055 approved+in_review task blocks) turns out to carry **zero authored
`difficulty` labels** — every single task block has `difficulty: null` and falls back to the
cognitive-level band. So the only "label" available to fit against is *itself a deterministic function
of one feature* (`cognitive_level`).

That has a sharp consequence, and it is the central result of C4:

- An unconstrained, accuracy-maximising fit over the full feature set (including `cognitive_rank`)
  **trivially recovers `cognitive_rank` alone**: it drives every other weight to zero and reproduces
  the label with **100 % exact accuracy and 0 disagreements**. Mathematically perfect, epistemically
  vacuous, and a **mute advisory** (an estimate that copies the band can never disagree with it).
- The reason is not a modelling failure — it is that *the label contains no information the model
  doesn't already have as a single feature*. **A difficulty model is, in the strict sense, not learnable
  from this corpus.** The honest fix is upstream: authored difficulty labels, or the prerequisite-graph
  depth feature (both are FUTURE seams below).

Rather than ship a vacuous 100 % or hide the finding, C4 ships a model designed for the job the advisory
actually needs to do.

## The design response: anchor-and-nudge

The estimate is built as a transparent weighted sum with **two roles**:

* the **cognitive level is the anchor** — a strong prior, because it *is* the operative difficulty
  signal the corpus already encodes — carried by a dominant curated weight;
* the **intrinsic surface features** are an **independent nudge** with modest curated weights.

When the nudge is strong enough to push the estimate across a band boundary, that ≥1-band disagreement
is the review cue. **The signal that fires the warning is the intrinsic features, not the anchor** — so
it is not circular. (An estimate that *included* the anchor as its only driver would be; this one uses
the anchor as a baseline and lets independent evidence move it.)

Only the **two thresholds** are fit to the data (deterministic grid search). The **weights are curated**,
with a documented didactic rationale — they cannot be learned here (see above), so pretending to learn
them would be dishonest. This is exactly the brief's own suggested shape: *"two learned thresholds over
a weighted feature sum."*

## The features (`difficulty_model.features`)

Every feature is transparent, documented, cheap, and reproducible **from the task block alone**
(no worksheet context, no external state). Each is normalised to `[0, 1]`.

| feature | what it measures | how |
|---|---|---|
| `steps` | derived Rechenweg length | `len(solution_steps) / 6`, capped |
| `math` | math-expression depth | sympy `count_ops` over `$…$` math runs, else an operator-token count; `/ 8`, capped |
| `numdom` | number domain | ℕ/none `0` < ℤ `1` < fractions/decimals `2` < irrational markers `3`, `/ 3` |
| `text` | prose reading load | WSTF (Wiener Sachtextformel) Schulstufe of the prompt, mapped `4→0 … 14→1`; a too-short prompt → neutral `0.4` |
| `kind` | inherent demand of the task genre | curated 3-tier table (`0.25` recognition · `0.55` apply/explain · `0.80` analyse/produce/argue) |
| `open` | answer-surface openness | closed self-contained payload/choices `0.0` · table/grid `0.5` · free written response `1.0` |
| `cog` | the **anchor** | `cognitive_rank / 5` (remember 0 … create 5) |

Two honest caveats:

* **`steps` and `math` are structurally 0 for every harvested library block.** Those blocks are prose
  worksheet tasks, not parametric — none carry `solution_steps` and none use `$…$` math (verified across
  the corpus). These features carry signal only for **parametric blocks** (the MAT/CHE/PHY variant
  packs, which *do* derive `solution_steps` and emit `$…$`). They are in the vector because the model
  must estimate those blocks too — not because they move the harvested corpus.
* **`text` and `numdom`** are heuristic (WSTF German syllable counting; a conservative negative-integer
  probe). They live in the same advisory lane as the readability lint — directional, never exact.

## The weights (`CURATED_WEIGHTS`) — and the didactic sanity check

Every weight is **positive**: each feature makes a task *harder* as it grows. That single sign is the
property the SME can sanity-check at a glance.

| feature | weight | didactic reading (does the sign make sense?) |
|---|---:|---|
| `cog` | **3.00** | the anchor — the cognitive level dominates; the estimate starts from the operative band. ✔ higher Anforderungsbereich → harder |
| `kind` | 0.70 | a produce/argue task is inherently more demanding than a matching drill. ✔ |
| `text` | 0.50 | denser prose raises the reading load before any thinking starts. ✔ |
| `steps` | 0.60 | a longer derived Rechenweg is more to get right. ✔ (parametric only) |
| `math` | 0.60 | a deeper expression is harder to manipulate. ✔ (parametric only) |
| `numdom` | 0.40 | irrationals > fractions > integers > naturals in numeric load. ✔ |
| `open` | 0.30 | a blank page demands more than picking an option. ✔ |

The intrinsic weights are deliberately small relative to the anchor: the estimate should agree with the
cognitive band *most* of the time and diverge only when the surface features push hard.

## The fit and its quality (`tools/fit_difficulty.py`)

The tool reads the corpus, computes features + the effective-difficulty label for every task block, fits
the two thresholds by an exhaustive O(n²) prefix-count scan (deterministic), writes
`difficulty_weights.json`, and prints the report. Re-run it after a corpus refresh; `--check` guards the
shipped JSON in CI, `--dry-run` reports without writing.

**Three fits tell the whole honest story** (same features, same corpus, thresholds fit each time):

| model | exact | adjacent | disagreements | reading |
|---|---:|---:|---:|---|
| **cog-only** (anchor, others 0) | **1.000** | 1.000 | **0** | the circularity — the label *is* the cognitive band |
| **intrinsic-only** (anchor off) | 0.562 | 0.938 | 462 (44 %) | surface features alone are a weak, noisy proxy |
| **shipped anchor-and-nudge** | **0.955** | **1.000** | **48 (4.5 %)** | anchored, nudged — a focused review list |

The shipped confusion matrix (true → predicted):

| true \ pred | 1 | 2 | 3 |
|---|---:|---:|---:|
| **1** | 344 | 10 | 0 |
| **2** | 13 | 344 | 9 |
| **3** | 0 | 16 | 319 |

**Adjacent accuracy is 100 %** — the estimate never disagrees by two bands (no 1↔3 confusions). That is
exactly the property an advisory needs: it nudges by at most one band, never shouts. The 48 off-diagonal
cells are the review cues.

## What a disagreement looks like (the review cues)

The 48 cues split ≈ 29 "looks easier than assigned" (band 2→1: 13, band 3→2: 16) and ≈ 19 "looks harder"
(band 1→2: 10, band 2→3: 9). They are didactically legible — the model is really catching
**cognitive-level / task-format mismatches**:

* **`evaluate`-labelled tasks in a closed format** (e.g. an `ordering` or `true_false_justify` task, or a
  `training_log`) read as band 2, not 3: the assigned Anforderungsbereich says *Reflexion*, but the task
  surface is a scaffolded, low-openness format. *Is this really anspruchsvoll, or is the format doing the
  work?* — a real SME judgment.
* **`understand`/`apply` open tasks with heavy prose** read a band up: an open `data_interpretation` or
  `text_analysis` at Schulstufe-13 text load looks harder than its assigned level implies.

Neither is a defect; each is a prompt to reconsider the Einstufung — precisely the value C4 adds.

## The advisory surface

* **verify** (`pipeline/verify.py`): for each task block, if `|estimate − effective_difficulty| ≥ 1`,
  a German warning is appended — naming the computed band, the operative band, whether the operative
  value is an SME estimate or cognitive-fallback, the direction, and the *maßgebliche Merkmale*
  (top intrinsic drivers). It is a **warning, never a problem** (`ok` is unaffected), and it **never
  writes back** onto the block (test-locked). On the gold-standard master-library flagships it is silent
  — that content is well-calibrated; the 48 cues live in the broader harvested corpus.
* **Einblicke** (`GET /api/difficulty/cues` → the dashboard digest): the corpus-wide review-cue list,
  sorted by disagreement size, with the drivers per block. Minimal by design.

## What would improve it (FUTURE seams — not depended upon)

1. **Authored difficulty labels.** The real fix. The moment the SME authors even a few dozen `difficulty`
   values that *diverge* from the cognitive fallback, the model becomes genuinely evaluable (and the
   intrinsic weights become genuinely fittable, not just curated). The advisory is already wired to
   compare against the authored value when present.
2. **A prerequisite-graph depth feature (Wave C1).** Once a concept/prerequisite graph exists, "how deep
   in the prerequisite chain does this task sit" is a strong, *independent* difficulty signal — the kind
   of feature that could carry real weight against a proper label. This is a **documented future seam**;
   C4 does **not** depend on Wave C1, and adds a slot for it rather than a stub.
3. **Curation of the kind-cost table** as the genre vocabulary grows (it degrades gracefully — unlisted
   kinds default to the middle tier).

## Rules (for anyone touching this)

* The estimate is **advisory** — never let it override, gate, or mutate the authored `difficulty`.
* The **weights are curated** (they are not learnable from this corpus); only the **thresholds are fit**.
  Change a weight → re-run `tools/fit_difficulty.py` (the thresholds re-fit; the JSON round-trip test
  locks `weights == CURATED_WEIGHTS`).
* `steps`/`math` being 0 on harvested blocks is **expected**, not a bug.
* Keep the advisory in the **warning** lane. If you find yourself wanting it to fail a build, stop — that
  is not what an unmeasurable, heuristic quantity is for.
