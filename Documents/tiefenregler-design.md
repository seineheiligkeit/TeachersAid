# Tiefenregler („Mischpult") — derivation contract

Status: **P1 + P2 built**. This document fixes the seam that P3–P4 extend.

## 1. Product rule

The Tiefenregler changes one shared worksheet for the whole class before printing. Every fader is
a deterministic projection of **one master**; it never selects an independently authored easy/hard
twin. A control exists only when its master exposes the computed data needed to move it. Unsupported
controls fail explicitly—there are no decorative knobs.

The profile is teacher-facing and appears only in the teacher guide. Student and homework PDFs never
carry profile, lint, competence, or regulatory metadata.

## 2. P1 + P2 controls on parametric sheets

| control | low → high | derivation from the master | measured movement |
|---|---|---|---|
| **Umfang** | kompakt → erweitert | variant count around the requested neutral count (`2/3 × n` → `4/3 × n`, bounded 1–30); same recipe and seed stream | task count, total minutes |
| **Tiefe** | üben → Strategien vergleichen | only where every instance emits computed `solution_paths`; adds a two-route comparison/justification task, `evaluate`, response space and time | AFB mean/mix, C4 estimate, minutes |
| **Abstraktion** | anschaulich → formal | only where the recipe emits a student figure; the formal projection removes student figure refs/assets while retaining the same prompt, values, answer and teacher-only solution figures | tasks with figures |
| **Offenheit** | geschlossen → offen | only where the recipe emits `MCSpec`; the misconception engine still computes and validates distractors, then the open projection removes the choice payload and exposes the recipe's original computed answer plus response space | MC-task count / open-response count |
| **Gerüst (P2)** | ohne → gestützt | only where a task exposes scaffoldable data; attaches a student-facing `TaskScaffold` per task from computed/curated data alone: a **leak-guarded** worked first step from `solution_steps[0]`, a misconception warning from the recipe's `MCSpec` distractors (curated catalog), and curated Formulierungshilfen for prose response surfaces; same recipe and seed stream, no change to prompt/answer/serves/minutes | tasks carrying a scaffold |

For the open projection, MC-only wording, title suffix and intro framing are removed. Misconception
diagnostics remain in the teacher guide as letter-free “Typischer Fehler” notes. Thus the projection
does not leave dangling option letters or turn distractors into an answer source.

The Gerüst scaffold is the one control whose product is **student-facing** (whole-class scaffolding the
teacher dialled in): it renders on the student AND homework sheet, while the teacher guide names what
the class received (`Gerüst (Schülerhilfe): …`). Full contract in §6.

P1–P2 do **not** implement simplified-prose twins, glosses, WSTF movement, presets, optional star
blocks, composer selection, or a dashboard. Those belong to P3–P4.

## 3. Typed seam

- `schema/mixer.py` owns `ParametricMixerProfile`, endpoint enums (incl. `Geruest`), metric snapshots
  (incl. `scaffolded_tasks`/`scaffold_elements`) and lint evidence.
- `pipeline/mixer.py` owns pure projection, capability rejection and endpoint measurement.
- `pipeline/parametrize.py` projects the same seeded `Instance` as misconception-MC or open response,
  and — with `scaffold=True` — attaches the derived scaffold; `pipeline/scaffold.py` builds it
  (leak-guard + curated Formulierungshilfen table + hint from the misconception catalog).
- `schema/blocks.py::TaskScaffold` is the student-facing scaffold; `TaskBlock.scaffold` carries it.
  Like `solution_steps` it is DERIVED — absent from generation views, so an LLM can never author it.
- `WorksheetContent.mixer_profile` carries the request; `mixer_lint` is derived evidence. Neither is in
  generation views, so an LLM cannot author a pass result.
- `library.templates.variant_worksheet(..., mixer_profile=...)` is the assembly seam.
- `POST /api/variants` accepts the same optional typed object (verified to pass `geruest` through
  unchanged — P4 owns the dashboard). This is an API/review seam, not the P4 dashboard surface.

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
`scaffolded_tasks`/`scaffold_elements` counts, the existing C4 difficulty estimate, and competence ids.
The P2 Gerüst endpoint (`ohne` → `gestützt`, metric `scaffolded_tasks`) is one more `FaderMovement` in
this **same** report — not a parallel lint. P3 adds WSTF/text movement to the same report likewise.

This lint proves structural movement, not learning impact. Difficulty remains an advisory estimate;
the system collects no student response data and makes no psychometric claim.

## 5. Extension rules

- **P2 Gerüst — DONE.** Derives from `solution_steps` and misconception records and adds one endpoint
  movement (`geruest`) to the existing report. Full contract in §6.
- P3 Textlast must operate on an approved prose twin/gloss seam and add WSTF evidence. It may not
  simplify verbatim source text or silently rewrite factual content.
- P4 may discover capabilities and expose only supported controls. It sends the same typed profile;
  UI state must never become a second source of truth.
- A future middle setting such as “geführt” is admitted only when its response scaffold is computed
  and its movement is measurable. Adding the enum label before that engine exists is forbidden — so P2
  ships exactly two endpoints (`ohne` ↔ `gestützt`), no `geführt`.

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
