# Übungsreihe upgrade — build brief (blackboard test)

**Status: agreed with SME 2 Jul 2026, build pending** (first attempt hit the session usage limit
before any edit; relaunch this brief as-is). Origin: SME review of the staged chemistry variant
series — *"just doing 6 reaction equations any teacher can write on the blackboard — they don't
really need our service for it."* The durable principle (memory `teachersaid-blackboard-test`):
**corpus content must deliver what a teacher cannot trivially produce on the board** — the
expensive layer around the computed core, not task enumeration.

Read first: CLAUDE.md ("Parametric variants + solution engine" + "Chemistry quantitative engine"),
`pipeline/parametrize.py`, `pipeline/chemistry.py`, `library/templates.py` (incl. the
`variant_worksheet` builder). Conventions: German product strings; select-never-author (numbers and
chemistry COMPUTED, context sentences CURATED — a context never asserts an uncomputed fact; guard:
context strings contain no digits); tests offline; full suite green; do not commit without review.

## Build (all four)

1. **Genre-honest framing.** `variant_worksheet` labels itself: subtitle "Übungsreihe — N Varianten,
   aufsteigend"; an intro InfoBlock naming the purpose (Automatisierung / Schularbeit-Vorbereitung;
   Gruppe A/B = jede Variante ein eigener Zahlensatz); `teacher_overview.throughline` states the value
   = ramp + per-variant Rechenweg, explicitly NOT a didactic ladder worksheet.
2. **Difficulty ramp.** Recipes gain an optional `difficulty` (1–3) knob where natural — `molar_mass`
   (binary → polyatomic → nested/hydrate), `equation_balance` (species count/triviality), one maths
   recipe (`linear_equation` by coefficient size/steps); others ignore the param (documented).
   `make_variants(task, n, ramp=True)` distributes bands ascending (n=6 → 2/2/2), preserving the
   distinctness guarantee and per-seed determinism; each Instance sets the task `difficulty` field so
   `DepthProfile.by_difficulty` shows the spread.
3. **Curated context frames.** Keyed to the drawn item where pools are curated: each reaction/substance
   entry in `grounding/chemistry.py` gains one vetted, plain, digit-free German sentence about where it
   occurs (Airbag-Natriumazid · Kalkbrennen · Photosynthese · Verbrennung …), rendered as a prompt
   prefix; numeric maths recipes get a neutral per-template frame in `templates.py`. SME vets the
   sentences at the gate.
4. **Refresh the staged proof.** Restage the three chemistry series via `orch.compose_variants`
   (che-os-molmasse, che-os-reaktionsgleichung, the US atom-count template — exact ids in
   `library/templates.py`) with ramp + contexts so the improved form lands in Prüfen next to the old
   c0159/c0160/c0165 (which the SME rejects as "Engine-Beleg, kein Arbeitsblatt").

## Tests

Extend `tests/test_chemistry.py` + parametrize tests: ascending effective-difficulty bands + distinct
prompts + per-seed determinism under `ramp=True`; context sentence prefixes the prompt and contains no
digits; `variant_worksheet` carries the Übungsreihe framing. `python -m pytest -q` green throughout.
