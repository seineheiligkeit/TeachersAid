# Project plan — the Master Library of worksheet examples

**Status: v1, 25 June 2026.** A plan for a curated, per-subject library of *gold-standard*
worksheet examples — the quality bar, the few-shot seeds for LLM generation, the offline demo
content, and the reviewable starting stock of the material library. Complements the design docs
(`project-handoff.md`, schema v0.3) and the running engine (`teachersaid/`, see `CLAUDE.md`).

> **Direction update (see [block-library-design.md](block-library-design.md)):** the library unit is
> shifting from whole worksheets to **blocks** (tasks *and* learn-from texts); a worksheet becomes a
> *composition* of blocks for a teacher's competence targets + time. The quality bar and coverage ideas
> below still hold — now applied at block granularity (competence × cognitive level × modality × scope).
>
> **Population update (25 Jun 2026):** beyond the 3 hand-authored gold seeds (Physik/Bio/Mathe — still the
> quality bar), the library has been **populated breadth-first via subagent generation** across **all 16
> subjects** — 64 worksheets / ~404 blocks, all verify-clean, staged `in_review` for SME approval (see
> CLAUDE.md "Breadth generation" + `tools/breadth_prompt.py`/`tools/ingest_batch.py`). The plan's jobs #2
> (few-shot seeds) and #3 (review stock) are thus realized; the human review now decides what enters the
> approved library.

## 1 · Why a master library

Three jobs, one artifact:
1. **Quality bar** — concrete reference worksheets that *define* "great" for each subject, so
   generated material can be judged against something real (not a vibe).
2. **Few-shot seeds** — the LLM `generate` stage produces far better content when primed with a
   gold example in the same subject + competence model. The library is that prime.
3. **Offline demo + review stock** — they make the whole content→render→review loop demoable with
   **no API key** (the engine's offline path serves them), and they seed the dashboard's review
   queue so the HITL flow has real material to act on from minute one.

The library is **content objects** (renderer-independent `WorksheetContent`), never PDFs — the
content/rendering split means each example yields student / teacher / homework projections that
cannot drift.

## 2 · What "great" means — the quality bar (acceptance criteria)

An example earns a place in the library only if it is:
- **Grounded** — every `serves` cites a real catalog competence ID (`lehrplan/*.json`); dimensions ⊆
  the subject model; stamped to the Fassung. (`verify` must return **0 problems**.)
- **Deep, not recall** — tasks climb the cognitive ladder (understand → apply → analyze → evaluate →
  create); ≥2 tasks at *analyze* or higher; "shallow" is measured by the derived `DepthProfile`.
- **Resource-independent core** — the worksheet stands without equipment; experiments are *one*
  optional, `equipment_dependent` task at most (the Physik hero's t7, the Biologie titre task).
- **AI-resistant where natural** — prompts that reward reasoning/relevance over retrieval
  (apply-a-mechanism, weigh-a-real-claim, write-for-an-audience), especially for the homework view.
- **Correct & Austria-specific** — verbatim-correct German, scientifically sound, AHS-Unterstufe
  level; the SME (physicist) fact-checks physics + German. The dashboard review gate is exactly this.
- **Teacher depth-layer present** — `answer_key`/`acceptable_reasoning`, `watch_outs` for
  misconceptions, and a derived `Nachweis` (coverage + honest gaps).
- **Honest gaps** — it need not cover a whole Kompetenzbereich; uncovered competences surface in the
  Nachweis and belong to sibling Bausteine (e.g. Physik leaves STR.01 a deliberate gap).

## 3 · Where it lives (structure)

```
teachersaid/library/__init__.py     registry: EXAMPLES[] + find() + seed_library()
teachersaid/library/<subject>_<topic>.py   one build_content() per example (grounded)
teachersaid/demo/strahlung.py, worked_examples.py   the original hero + v0.4-delta demos
lehrplan/*.json                     the grounding every example anchors to
```

- The **persistent library is the version-controlled builder modules** + the registry. They are
  reviewed, diffed, and tested like code (`tests/test_library.py` locks every example
  build/assemble/verify-clean against catalog drift).
- The **review store (`runs/`, git-ignored) is just the surface** the dashboard reviews on.
  `python -m teachersaid seed` runs every example through the pipeline into the store as a *pending
  content item*; the dashboard shows it with rendered PDFs + the Nachweis for approval.
- The engine's offline `_generate_content` consults the registry, so a normal dashboard request for a
  registered subject/topic produces the curated example even without a key.

## 4 · How examples get generated

Two interchangeable paths into the *same* review gates — the architecture doesn't care which:

| | **Authored / curated (now, offline)** | **LLM-generated (with `ANTHROPIC_API_KEY`)** |
|---|---|---|
| Generator | Claude/human authors the content object | `generate` stage (`claude-opus-4-8`) emits a `GenWorksheetBody`, primed with the subject's gold example |
| Cost / speed | slow to author, free | fast, per-call cost |
| Use | the gold seeds; the quality bar | scale to any subject/topic/Klasse on demand + batch over the competence map |
| Quality control | verify-clean by construction | `verify` + the **HITL review gates** (idea + content) catch issues |

**The plan is to use both:** hand-author a small gold set per subject (the library), then let the LLM
generate at scale *seeded by* those gold examples, with every output passing through the dashboard's
two review gates before it can enter the approved material library.

## 5 · Coverage target (wedge-first)

Lead where a printable worksheet has ~full coverage and correctness matters most (MINT), per the
subject-coverage audit:

- **Phase 1 — MINT seed (done).** Physik (Strahlung), Biologie (Immunsystem), Mathematik (unfaires
  Spiel / Wahrscheinlichkeit). Mechanism + dashboard live.
- **Phase 2 — complete the wedge.** Chemie, complete a 2nd Physik/Math/Bio topic each; align the two
  existing worked examples (English listening, "geschönte Kurve") to the catalog and admit them.
  Target: 2–3 gold examples per ● subject (the cognitive subjects).
- **Phase 3 — broaden.** GWB, Geschichte u. pol. Bildung, Deutsch (written strand), Latein. Then the
  ◐ subjects (Fremdsprache with audio, Digitale Grundbildung) as audio/interactive support matures.
- **Phase 4 — scale via LLM.** With a key: batch-generate across the competence map, review, and
  promote the best into the library. Don't target the ○ subjects (Musik/Sport/Kunst/Technik) for
  printable worksheets — the audit says a worksheet structurally can't reach their core competences.

A worksheet is "covered" for a (subject, Klasse, Kompetenzbereich) when ≥1 verify-clean gold example
exists and has been SME-approved in the dashboard.

## 6 · Workflow (the running pipeline + dashboard)

```
Brainstorm (rough idea: you or "Vorschläge aus Lehrplan") ─approve─► flesh out
   (resolve → plan → generate[LLM or library] → verify → assemble(+derive) → render)
   ─► Content [review Blöcke + Vorschau] ─approve─► Bibliothek (library)
```
- Four dashboard tabs: **Brainstorm**, **Inhalte** (Blöcke = structured content, Vorschau = rendered
  PDFs), **Bibliothek**, **Statistik** (coverage vs the catalog — see §1/§5). `request-changes`
  regenerates with the note injected; "Vorschläge aus Lehrplan" seeds brainstorm ideas for uncovered
  Kompetenzbereiche, so ideation and the coverage stats feed each other.
- The store holds only review items + the approved library — no gradebook, no student PII.

## 7 · Open items / dependencies

- **Live LLM generation needs an `ANTHROPIC_API_KEY`** (not set in this environment). Until then the
  library is authored offline; the LLM path is wired and smoke-tested via the `FakeGenerator`.
- **Difficulty calibration** — the open hard problem; `DepthProfile` makes depth measurable but does
  not yet calibrate AHS-grade difficulty. Bounded to per-block fill+verify.
- **Align the legacy worked examples** (English, geschönte Kurve) to the catalog dimension codes /
  competence IDs before admitting them to the library (they currently use pre-catalog refs).
- **Homework projection** as a first-class library facet (AI-resistant by design) once the homework
  profile is specced.
- **Fassung expiry 2026-08-31** — the catalog (and thus every example's grounding) must be
  regenerated for the 2026/27 Fassung; `tools/parse_lehrplan.py` does this.
