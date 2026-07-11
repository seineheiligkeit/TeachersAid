# Tiefenregler („Mischpult") — derivation contract

Status: **P1 built**. This document fixes the seam that P2–P4 extend.

## 1. Product rule

The Tiefenregler changes one shared worksheet for the whole class before printing. Every fader is
a deterministic projection of **one master**; it never selects an independently authored easy/hard
twin. A control exists only when its master exposes the computed data needed to move it. Unsupported
controls fail explicitly—there are no decorative knobs.

The profile is teacher-facing and appears only in the teacher guide. Student and homework PDFs never
carry profile, lint, competence, or regulatory metadata.

## 2. P1 controls on parametric sheets

| control | low → high | derivation from the master | measured movement |
|---|---|---|---|
| **Umfang** | kompakt → erweitert | variant count around the requested neutral count (`2/3 × n` → `4/3 × n`, bounded 1–30); same recipe and seed stream | task count, total minutes |
| **Tiefe** | üben → Strategien vergleichen | only where every instance emits computed `solution_paths`; adds a two-route comparison/justification task, `evaluate`, response space and time | AFB mean/mix, C4 estimate, minutes |
| **Abstraktion** | anschaulich → formal | only where the recipe emits a student figure; the formal projection removes student figure refs/assets while retaining the same prompt, values, answer and teacher-only solution figures | tasks with figures |
| **Offenheit** | geschlossen → offen | only where the recipe emits `MCSpec`; the misconception engine still computes and validates distractors, then the open projection removes the choice payload and exposes the recipe's original computed answer plus response space | MC-task count / open-response count |

For the open projection, MC-only wording, title suffix and intro framing are removed. Misconception
diagnostics remain in the teacher guide as letter-free “Typischer Fehler” notes. Thus the projection
does not leave dangling option letters or turn distractors into an answer source.

P1 does **not** implement the Gerüst fader, formulation aids, simplified-prose twins, glosses, WSTF
movement, presets, optional star blocks, composer selection, or a dashboard. Those belong to P2–P4.

## 3. Typed seam

- `schema/mixer.py` owns `ParametricMixerProfile`, endpoint enums, metric snapshots and lint evidence.
- `pipeline/mixer.py` owns pure projection, capability rejection and endpoint measurement.
- `pipeline/parametrize.py` projects the same seeded `Instance` as misconception-MC or open response.
- `WorksheetContent.mixer_profile` carries the request; `mixer_lint` is derived evidence. Neither is in
  generation views, so an LLM cannot author a pass result.
- `library.templates.variant_worksheet(..., mixer_profile=...)` is the assembly seam.
- `POST /api/variants` accepts the same optional typed object. This is an API/review seam, not the P4
  dashboard surface.

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

`None` on Tiefe, Abstraktion, or Offenheit means “do not apply this control,” not a hidden default.
Umfang is universal and defaults to `standard`, preserving the requested count.

## 4. Regler-Lint P1

For every enabled control, lint derives both endpoints from the same template and seed stream. It
passes only if:

1. the promised metric changes;
2. the set of served competence ids is identical at both endpoints; and
3. every requested template-specific capability exists.

The output snapshot records task count, minutes, AFB mix, figure/MC/open task counts, the existing C4
difficulty estimate, and competence ids. P3 adds WSTF/text movement to this same report; it must not
create a parallel lint result.

This lint proves structural movement, not learning impact. Difficulty remains an advisory estimate;
the system collects no student response data and makes no psychometric claim.

## 5. Extension rules

- P2 Gerüst must derive from `solution_steps` and misconception records, then add one endpoint movement
  to the existing report.
- P3 Textlast must operate on an approved prose twin/gloss seam and add WSTF evidence. It may not
  simplify verbatim source text or silently rewrite factual content.
- P4 may discover capabilities and expose only supported controls. It sends the same typed profile;
  UI state must never become a second source of truth.
- A future middle setting such as “geführt” is admitted only when its response scaffold is computed
  and its movement is measurable. Adding the enum label before that engine exists is forbidden.
