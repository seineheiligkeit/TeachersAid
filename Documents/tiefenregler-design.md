# Tiefenregler („Mischpult") — derivation contract

Status: **P1 + P2 + P3 built**. This document fixes the seam that P4 extends.

## 1. Product rule

The Tiefenregler changes one shared worksheet for the whole class before printing. Every fader is
a deterministic projection of **one master**; it never selects an independently authored easy/hard
twin. A control exists only when its master exposes the computed data needed to move it. Unsupported
controls fail explicitly—there are no decorative knobs.

The profile is teacher-facing and appears only in the teacher guide. Student and homework PDFs never
carry profile, lint, competence, or regulatory metadata.

## 2. P1 + P2 + P3 controls on parametric sheets

| control | low → high | derivation from the master | measured movement |
|---|---|---|---|
| **Umfang** | kompakt → erweitert | variant count around the requested neutral count (`2/3 × n` → `4/3 × n`, bounded 1–30); same recipe and seed stream | task count, total minutes |
| **Tiefe** | üben → Strategien vergleichen | only where every instance emits computed `solution_paths`; adds a two-route comparison/justification task, `evaluate`, response space and time | AFB mean/mix, C4 estimate, minutes |
| **Abstraktion** | anschaulich → formal | only where the recipe emits a student figure; the formal projection removes student figure refs/assets while retaining the same prompt, values, answer and teacher-only solution figures | tasks with figures |
| **Offenheit** | geschlossen → offen | only where the recipe emits `MCSpec`; the misconception engine still computes and validates distractors, then the open projection removes the choice payload and exposes the recipe's original computed answer plus response space | MC-task count / open-response count |
| **Gerüst (P2)** | ohne → gestützt | only where a task exposes scaffoldable data; attaches a student-facing `TaskScaffold` per task from computed/curated data alone: a **leak-guarded** worked first step from `solution_steps[0]`, a misconception warning from the recipe's `MCSpec` distractors (curated catalog), and curated Formulierungshilfen for prose response surfaces; same recipe and seed stream, no change to prompt/answer/serves/minutes | tasks carrying a scaffold |
| **Textlast (P3)** | voll → einfach | only where the template carries an APPROVED simplified prose twin (`prompt_simple`, same {slots}); `einfach` SELECTS the twin for every task prompt and renders a student-facing Wortschatz-Kasten from the curated `glossary`; same recipe, seed stream, computed values, answer and serves | WSTF Schulstufe (Wiener Sachtextformel) over the student-facing prompt prose |

For the open projection, MC-only wording, title suffix and intro framing are removed. Misconception
diagnostics remain in the teacher guide as letter-free “Typischer Fehler” notes. Thus the projection
does not leave dangling option letters or turn distractors into an answer source.

The Gerüst scaffold is the one control whose product is **student-facing** (whole-class scaffolding the
teacher dialled in): it renders on the student AND homework sheet, while the teacher guide names what
the class received (`Gerüst (Schülerhilfe): …`). Full contract in §6.

P1–P2 do **not** implement simplified-prose twins, glosses, WSTF movement, presets, optional star
blocks, composer selection, or a dashboard. Those belong to P3–P4.

## 3. Typed seam

- `schema/mixer.py` owns `ParametricMixerProfile`, endpoint enums (incl. `Geruest`, `Textlast`), metric
  snapshots (incl. `scaffolded_tasks`/`scaffold_elements`, `wstf`) and lint evidence.
- `pipeline/mixer.py` owns pure projection, capability rejection and endpoint measurement.
- `pipeline/parametrize.py` projects the same seeded `Instance` as misconception-MC or open response,
  and — with `scaffold=True` — attaches the derived scaffold; with `textlast=einfach` fills each prompt
  from the template's twin instead of the master (same computed `params`). `pipeline/scaffold.py` builds
  the scaffold; `pipeline/textlast.py` owns the WSTF measurement (over the student-facing prompt prose,
  verbatim-exempt blocks skipped — the structural guard) and reuses the one `pipeline/readability` formula.
- `schema/blocks.py::TaskScaffold`/`Gloss`: the scaffold is DERIVED per task; the twin/glosses are the P3
  exception — **CURATED**, SME-vetted fields on `ParametricTask` (`prompt_simple`/`glossary`), SELECTED by
  the fader, never rewritten at fader time. `ParametricTask` HARD-VALIDATES that `prompt_simple` carries
  exactly the master's {slots} (a dropped/added slot is fact drift → error at registration). The selected
  Wortschatz lands on `WorksheetContent.glossary` at `einfach` (absent from generation views, like
  `mixer_profile`/`mixer_lint` — an LLM cannot author it).
- `WorksheetContent.mixer_profile` carries the request; `mixer_lint` is derived evidence. Neither is in
  generation views, so an LLM cannot author a pass result.
- `library.templates.variant_worksheet(..., mixer_profile=...)` is the assembly seam (it also SELECTS the
  glossary onto the worksheet at `einfach`).
- `POST /api/variants` accepts the same optional typed object (verified to pass `geruest`/`textlast`
  through unchanged — P4 owns the dashboard). This is an API/review seam, not the P4 dashboard surface.

Example:

```json
{
  "template_id": "mat-prozent-mc",
  "n": 6,
  "mixer_profile": {
    "umfang": "kompakt",
    "offenheit": "offen"
  }
}
```

`None` on Tiefe, Abstraktion, Offenheit or Gerüst means “do not apply this control,” not a hidden
default. Umfang is universal and defaults to `standard`, preserving the requested count.

## 4. Regler-Lint P1

For every enabled control, lint derives both endpoints from the same template and seed stream. It
passes only if:

1. the promised metric changes;
2. the set of served competence ids is identical at both endpoints; and
3. every requested template-specific capability exists.

The output snapshot records task count, minutes, AFB mix, figure/MC/open task counts, the P2
`scaffolded_tasks`/`scaffold_elements` counts, the P3 `wstf` Schulstufe, the existing C4 difficulty
estimate, and competence ids. The P2 Gerüst endpoint (`ohne` → `gestützt`, metric `scaffolded_tasks`)
and the P3 Textlast endpoint (`voll` → `einfach`, metric `wstf`) are each one more `FaderMovement` in
this **same** report — not a parallel lint. The Textlast movement is unusual in that its `moved` flag
is a **strict decrease** (`einfach.wstf < voll.wstf`), not mere inequality: a curated twin that fails to
lower the WSTF is a bad twin, so it lands as `moved=False` and fails the lint (the SME sees it) rather
than passing on any change. An `einfach` prompt with too little prose to measure the WSTF is a hard
capability failure (the fader should not have been offered).

This lint proves structural movement, not learning impact. Difficulty remains an advisory estimate;
the system collects no student response data and makes no psychometric claim.

## 5. Extension rules

- **P2 Gerüst — DONE.** Derives from `solution_steps` and misconception records and adds one endpoint
  movement (`geruest`) to the existing report. Full contract in §6.
- **P3 Textlast — DONE.** Operates on an APPROVED prose twin/gloss seam (`ParametricTask.prompt_simple`/
  `glossary`, curated + SME-vetted) and adds the WSTF movement to the SAME report. It SELECTS between two
  curated fields — it never simplifies verbatim source text (verbatim-exempt blocks are structurally
  skipped) and never rewrites a factual value (slot-set equality is validated; the twin introduces no new
  number). Full contract in §7.
- P4 may discover capabilities and expose only supported controls. It sends the same typed profile;
  UI state must never become a second source of truth.
- A future middle setting such as “geführt” (P2) or a computed intermediate register (P3) is admitted
  only when its scaffold/register is computed and its movement is measurable. Adding the enum label
  before that engine exists is forbidden — so P2 ships exactly two endpoints (`ohne` ↔ `gestützt`) and
  P3 exactly two (`voll` ↔ `einfach`), no middle label.

## 6. P2 Gerüst (scaffold) — contract

**Two endpoints, no middle.** `ohne` is the bare master; `gestützt` attaches one `TaskScaffold` per
task, projected from the SAME seeded instance (no forked content). No `geführt` label (§5).

**Three scaffold elements, each derived/curated, each leak-safe:**

- **(a) worked first step** — `solution_steps[0]` (text + inline-math expr) as student RichText. It is
  the FIRST step only, never the full Rechenweg. Admitted per task iff a deterministic **leak-guard**
  proves the answer is absent from it, and never for mapping kinds (`matching`/`ordering`, whose first
  step *is* a pairing). Leak-guard: parse the answer's numeric values FRACTION-AWARE (a `\frac{a}{b}`
  or `a/b` is one atomic value, exponents stripped) and reject if any appears in the step; for a
  pure-text answer fall back to a normalised substring test. The guard errs SAFE — a coincidental
  match merely drops that one worked step, the other elements still scaffold the task.
- **(b) misconception hint** — where the instance carries `MCSpec`, a student warning naming the trap
  CATEGORIES the recipe's distractors probe, read from the curated `grounding/misconceptions` catalog
  (names, never the answer). `hint_categories` carries the catalog names for the teacher line, so
  rendering stays pure (no catalog lookup at render time).
- **(c) Formulierungshilfen** — curated German sentence starters (Austrian school register), a **small
  table in `pipeline/scaffold.py` keyed by task kind** (`open_response` · `decision_scenario` ·
  `true_false_justify` · `modelling_task`); a bare calculation/MC gets none. This is the ONE authored
  surface in the fader — **SME must vet the table.** Everything else is derived.

**Capability rule.** A template supports Gerüst iff ≥1 variant exposes ≥1 element; else the fader
HARD-FAILS (`pipeline/mixer.py`, clear message) — never a no-op control. So a bare calculation whose
first step computes the answer and which has no MC and no prose surface (e.g. `mat-rechteck`,
`mat-kennzahlen`, `mat-kreis`) is correctly rejected.

**Lint metric.** `scaffolded_tasks` (count of tasks carrying a scaffold), measured `ohne` (0) →
`gestützt` (>0) from the same template + seed stream. Scaffolding never touches `serves`/`kind`/
`est_minutes`, so the competence-id set is identical at both endpoints by construction (coverage
intact) and only the scaffold count moves.

**Projection.** The scaffold is STUDENT-FACING and renders on the student AND homework sheet
(`Hilfestellung` box, before the unchanged write-space); the teacher guide gets a `Gerüst
(Schülerhilfe): …` line naming what the class received. The profile stamp stays teacher-only (§1).
Because every element is leak-safe by construction, the scaffolded student sheet never carries the
answer (`tests/test_mixer.py::test_geruest_scaffold_never_leaks_the_answer` locks this across the
corpus).

## 7. P3 Textlast (simplified prose twin + glosses) — contract

**Two endpoints, no middle.** `voll` is the unchanged master (full register); `einfach` SELECTS the
template's curated simplified twin for every task prompt and renders a student-facing Wortschatz-Kasten.
No computed intermediate register exists, so no third label (§5).

**The twin seam is CURATED, not fader-authored.** The Textlast fader is the one control that moves by
SELECTING between two curated, SME-vetted fields — never by rewriting at fader time (which would be the
LLM authoring a fact-bearing surface). Both fields live on `ParametricTask`:

- **`prompt_simple`** — the approved simplified twin, carrying the master's EXACT `{slots}` so the SAME
  computed `Instance.params` fill it (shorter sentences, common words, active voice; simpler German).
  A new twin lands SME-flagged like any curated German. Slot-set equality is **HARD-VALIDATED** at model
  construction (registration time): a dropped or added slot would either crash the fill or silently change
  what the student is asked, so it is a `ValueError`, not a warning. This is the guard against the fact
  drift the contract forbids — combined with the no-leak test proving the twin introduces no NUMBER the
  master prompt did not already carry.
- **`glossary`** — a small curated list of `Gloss(term, explanation)`. Each gloss is **term-definitional**:
  it explains a Fachbegriff, never a value. A constant template gloss cannot contain a per-variant computed
  answer by construction (locked: glosses are digit-free, so they cannot carry a numeric answer, and never
  repeat a text answer verbatim).

**Capability rule.** A template supports Textlast iff it carries an approved `prompt_simple` AND the twin
measurably lowers the WSTF. Otherwise the fader HARD-FAILS (`pipeline/mixer.py` / `pipeline/parametrize.py`,
clear message) at BOTH endpoints — never a no-op control. So a terse calculation whose prompt is already
simple (e.g. `mat-dreisatz`) is correctly rejected.

**Verbatim-text guard (structural).** The fader's only writable input is `prompt_simple`, which exists
solely on parametric templates (authored, never verbatim). The WSTF measurement additionally EXCLUDES any
block the readability lint marks `advisory_exempt` (a `source_text` block, a `quoted`-provenance block) —
verbatim selected material is not ours to simplify. Locked by
`tests/test_mixer.py::test_textlast_verbatim_text_is_never_twinned`.

**Lint metric + threshold.** `wstf` (the Wiener Sachtextformel Schulstufe over the concatenated
student-facing task-prompt prose — measured over the whole variant set so a short single prompt clears the
formula's word threshold; math runs and numbers do not count, so the metric moves on REGISTER, not on the
drawn values), measured `voll` → `einfach` from the same template + seed stream. **The threshold is a
STRICT mean decrease**: `einfach.wstf < voll.wstf`. Honest choice — because all N variants share one twin
template, the aggregate WSTF is stable and a strict decrease means the twin template genuinely reads
easier; a twin that fails to lower it fails the lint (the SME sees a bad twin, not a broken engine). The
one readability formula the project already has is reused — no second formula. Selecting the twin never
touches `serves`/`kind`/`est_minutes`/the computed answer, so the competence-id set is identical at both
endpoints by construction.

**Authored twins (Stand P3 build).** `fin-lohnzettel` and `fin-handyvertrag` (the Finanz pack; `fin-inflation`
is honestly EXCLUDED — its recipe builds the whole prompt into one `{aufgabe}` slot, so there is no template
prose to twin), plus four MAT Sachaufgaben-style templates: `mat-pythagoras`, `mat-kreis`, `mat-kennzahlen`,
`mat-rechteck`. Every twin lowers the WSTF by ≥6 Schulstufen (measured). Every twin and gloss is SME-flagged
curated German.

**Projection.** At `einfach` the twin REPLACES the prompt on every projection (the teacher guide shows the
same simplified prompt plus the unchanged Rechenweg); the Wortschatz-Kasten renders as a student-facing box
between the intro and the tasks (student, homework AND teacher — the teacher sees what the class received).
The teacher-only profile stamp names the register (`Textlast: einfach (vereinfachte Angabe + Wortschatz)`).
The master's hardest vocabulary (e.g. „Steuerbemessungsgrundlage“) is absent from the einfach student sheet
by construction.
