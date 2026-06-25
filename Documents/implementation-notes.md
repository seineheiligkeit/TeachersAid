# Implementation Notes — the TeachersAid demo engine

**Status: current as of 25 June 2026.** This documents the first *runnable* implementation built on top
of the design phase: the engine, the rendering layer, the generation pipeline, and the two-stage
human-in-the-loop (HITL) review dashboard. It complements (does not replace) `project-handoff.md`, which
remains the source of truth for intent and decisions.

## 0 · What was built (the 30-second version)

A Python package `teachersaid/` that takes the design from "specced" to "running":

- the **schema v0.3 + v0.4 deltas** as Pydantic models (also the structured-output contract for the LLM);
- a deterministic **Lehrplan resolution** over hand-curated grounding;
- the **engine pipeline** (resolve → plan → generate → verify → assemble(+derive) → render) from schema §7;
- **ReportLab** rendering of three pure projections (student / teacher / homework), QA-rastered;
- a **two-stage HITL dashboard** (FastAPI) with on-demand and batch generation feeding a review queue;
- the MINT **hero** (Physik *Strahlung*) and the **three worked examples**, rendered end-to-end.

30 tests, all offline. Live LLM generation activates with `ANTHROPIC_API_KEY`; without it the hero falls
back to a hand-authored content object so the loop is fully demoable. Run instructions: `README.md` / `CLAUDE.md`.

## 1 · How the implementation maps to the design

| Design (docs) | Implementation |
|---|---|
| Block model, subject-parameterized dimensions, CognitiveLevel depth contract (`schema v0.3`) | `teachersaid/schema/` (canonical Pydantic) |
| v0.4 additive deltas (modality-at-dimension, audio medium, rubric/artifact, intra-sheet refs, cross-curricular models, intentionally-flawed assets) | folded into `schema/` — required because the worked examples are authored at the v0.4 level |
| Renderer-independent `WorksheetContent`; renderers are pure projections | `schema/worksheet.py` + `rendering/` (imports only `schema/`) |
| Derived `Nachweis` / `DepthProfile` | `pipeline/derive.py` (the only producer; never authored) |
| Deterministic resolver + `grade_check` (the trust feature) | `pipeline/resolve.py` over `grounding/` |
| Pipeline §7 | `pipeline/{resolve,plan,generate,verify,assemble,derive}.py` + `orchestrator.py` |
| Content-bearing assets = code, not diffusion (MediaPolicy) | `pipeline/assets.py` (matplotlib) |
| 16-subject competence models, science-model sharing | `grounding/data/competence_models.yaml` + aliasing |
| Strahlung rack / worked examples | `demo/strahlung.py`, `demo/worked_examples.py` |

## 2 · Notable engineering decisions

- **Two model layers, one seam.** Canonical models (`schema/`) are full-fidelity; *generation views*
  (`schema/generation_views.py`) are flattened/recursion-free for Anthropic structured output, with a
  single `to_canonical()` up-conversion. This keeps the LLM contract robust and keeps derived fields
  un-authorable.
- **Dependency rule enforces no-drift.** `rendering/` imports only `schema/`; all projections derive from
  one object, so the mismatched-answer-key bug (flagged on `strahlung_lehrkraft.pdf` in the handoff) is
  structurally impossible — and there is a test asserting it.
- **DepthProfile reproduces schema §8 exactly.** The hand-authored hero yields
  `by_level {understand1, apply1, analyze2, evaluate2, create1}`, `by_dimension {W2,S4,E1}`,
  `78 min / 56 resource-independent`, and `deriveNachweis` auto-surfaces `PHY.US.4.STR.01` ("Quellen
  bewerten") as the uncovered gap — exactly the design's worked numbers.
- **Intentionally-flawed assets stay flawed.** The geschönte-Kurve truncated-axis graph is generated wrong
  on purpose; an asset-builder guard prevents the "correct" generator from ever being used for it.
- **Rasteriser is PyMuPDF**, not `pdftoppm` (no system poppler dependency in this environment).

## 3 · Milestones (all complete)

- **M0** scaffold · **M1** schema + generation views · **M2** grounding + resolve · **M3** derivation +
  rendering (first visible artifact, LLM-free) · **M4** LLM generation (mockable) · **M5** store + API +
  dashboard + two-stage orchestration · **M6** the three worked examples + polish.

The critical path to the first visible artifact (M1→M3) is deliberately LLM-free, so the architecture's
core claim is provable before any model dependency.

## 4 · Known limits / next steps

- **Grounding is curated for the demo subjects only** (Physik 4. Kl. fully). Adding subjects = adding YAML
  under `grounding/data/`. A real RIS-HTML parser (Achter Teil) remains out of scope.
- **Difficulty calibration** is bounded in `verify.py` (sanity checks), not solved — it remains the open
  hard problem; the DepthProfile makes "shallow" measurable but doesn't calibrate AHS-grade difficulty.
- **Fassung expires 2026-08-31.** Resolution stamps and date-checks the window; the post-2026/27 Fassung
  is future work.
- **Live LLM generation is wired but only smoke-tested offline** (no API key in the build environment).
  Set `ANTHROPIC_API_KEY` to generate for real and re-run the worked examples through the LLM path.
- **v0.5 Lernarrangement** intentionally not implemented.
- **Use-ready polish / editable docx** — the student/teacher/homework PDFs clear the use-ready bar on the
  hero; an editable `render()` target (docx) and a decorative layer remain the documented weak flank.
