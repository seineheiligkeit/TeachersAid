# Feature roadmap / backlog

Forward-looking *capability* features for TeachersAid. (The schema-version roadmap lives in
`schema-roadmap-v0.4-v0.5.md`; this tracks product/engine features.)

## ▶ Start here (state as of 10 Jul 2026)

> **Session update (11 Jul 2026) — the final geometry gap is closed.** `pipeline/nets.py` computes
> true six-face Quader/Würfel nets (two face pairs per dimension pair; five-edge connected fold tree)
> and projects them through the scene engine as `matplotlib:solid_net`. The new
> `quader_oberflaeche` parametric recipe derives `O = 2(ab+ac+bc)`, emits a masked `O = ?` net per
> variant, and is anchored to `MAT.US.1.FIG.03`. Geometry/masking/layout/render tests + specimens;
> suite **683 passed, 1 skipped**. External-experiment branch: `ext/nets`.

> **Reconciliation (10 Jul 2026, evening).** The two development machines had DIVERGED from
> `a9f03d6` — the workhorse's Sessions 11–14 (below: build-for-joy program, Wave A, Prüfen/triage,
> four-station dashboard; pushed to origin) × this machine's 9–10 Jul work (the two session blocks
> right below). Both lines independently implemented the figstyle port and a pythagoras recipe.
> Merged on this machine, preferring the workhorse's SME-reviewed recipe bodies + representation
> rules and this line's additive capabilities (figure emission, nodelink/Scene.select, physics
> scenes, Textsorten/Latein/texts/data tracks); the two Calibri fixes were UNIFIED (strip strikes
> as the root-cause fix + the `_renders_small` probe as the safety net); the two pythagoras
> recipes unified into the figure-emitting one. Lesson recorded: **`git fetch origin` at every
> session start on every machine.**

> **Session update (10 Jul 2026) — eight parallel build tracks (subagent-orchestrated, Opus
> workers in git worktrees, merged sequentially).** Suite **368 → 478** (pre-merge count on this
> line). What shipped:
> - **Scene engine grew up:** `Arrow` + `Node` primitives; **`Scene.select(*groups)`** — the
>   first-class density/stage selector (constructions' stage 1–6 migrated, identical output);
>   `tree_diagram·cause_effect·process_flow` consolidated onto **`pipeline/nodelink.py`** (thin
>   wrappers, frozen specs); **physics recipes** `vector_addition`/`force_diagram`
>   (`pipeline/physics_scenes.py`, resultants computed + maskable, no-arrow masked resultant) and
>   **`labeled_parts`** (`pipeline/labeled_diagram.py`, numbered/named projections; volcano flagship).
> - **Matura-backward round 1 DONE (all three demand-map targets):** MAT `exponential_model` +
>   `boxplot_from_data` + `probability_tree` (templates MAT.OS.6.REE.10/BES.01/BES.04); the **Deutsch
>   Textsorten scaffold** (`pipeline/textsorte_scaffold.py`, rubric DERIVED from the curated
>   Schreibhandlungen; Zusammenfassung/Kommentar/Interpretation seeded); the **Latein Operatorenliste**
>   (empirical 15-operator catalog, `LAT` routed) + **Wortbildung engine** (39 curated derivations).
> - **Parametric figure emission:** `Instance.figure`/`FigureSpec` → per-variant masked figure assets
>   (`pythagoras`, `kreis_umfang_flaeche`; the tree emits its Baumdiagramm; boxplot deliberately
>   figure-free — no teacher-only asset channel exists).
> - **Texts:** `tools/fetch_wikisource.py` (verbatim exact-revision fetch + permalink + rights fields)
>   → 5 annotated texts staged (Grimm/Fontane/Goethe + 2 Phaedrus), AT-70-p.m.a.-clear.
> - **Data:** c0081/c0096/c0097 **re-grounded** (4 new sources: UN WPP · UNDP HDI [CC BY 3.0 IGO
>   verified] · NOAA CO₂ · WB fertility; 12 datasets total; 5 figures cited, 3 honestly illustrative;
>   GFN refused — ShareAlike). Task-text deltas flagged for SME review in the store items.
> - **Orchestration lessons (for future multi-agent sessions):** subagents inherit the parent model —
>   pass `model` explicitly (Opus was right for these tracks); agent worktrees can pin a STALE base
>   (session-start commit) — verify `git log -1` in the worktree and merge main first; two agents
>   independently inventing the same primitive (Arrow) needs a reconciling merge — unify fields,
>   keep both consumers' tests green.

> **Session update (9 Jul 2026) — the styleguide port.** The deferred Q1 is done: all ~25 legacy
> recipes in `pipeline/assets.py` consume `figstyle` roles/ramps/type scale (`build_asset` scopes
> `house_rc()` over every build). Semantic upgrades: misleading/honest = `negative`/`positive`,
> colour-keyed Klimadiagramm axes, ramp-cycled multi-series lines. **Found + fixed: the
> Windows-Calibri embedded-bitmap-strike bug** (glyphs silently vanish at strike ppem sizes, e.g.
> 9 pt @ 150 dpi, while still measuring) — strikes stripped at font registration + a
> glyph-rendering regression test. Suite **369**. Details: `figure-styleguide.md` "What's next".
## The build-for-joy feature program (5 Jul 2026, Session 13 — workhorse line)

> **The frame, reaffirmed hard (5 Jul 2026).** TeachersAid is built **for the joy of building**: no
> pilots, no releases, no GTM clock, no teacher-feedback loop *for now*. The SME's thesis: only building
> the intrinsically best platform, as the goal itself, can later maybe become a product — premature
> productization is the failure mode AI projects die of, and the discipline here is to resist it.
> Prioritise on the intrinsic axis: **new correct-by-construction domains · deeper engines ·
> corpus-level structure · craft.** (Also recorded in assistant memory; pushing market-facing urgency
> is a frame violation, not a helpful nudge.)

The program below is the 5 Jul idea pass + SME verdicts. **Waves are themes, not a schedule — pick by
interest**; real dependencies are noted. Each item is written so a fresh build session can pick it up
cold. State at session start: 413 tests green; 967 approved blocks; coverage 95/610 cells grün.

> **✅ Wave A is COMPLETE (Session 14, 5 Jul 2026).** All seven items landed (A1·A2a·A2b·A3·A4·A5·A6·A7),
> built by a fan-out of Opus/Sonnet subagents and orchestrator-reviewed (specimens viewed, diffs read,
> SME flags collected below the wave). The CHE2 maintenance item also landed. State now: **565 tests
> green.** Design depth for the new engines is in their modules' docstrings + the Session-14 handoff
> block; a batch of **SME fact-check flags** (physics magnitudes, g=9.80665, kWh grade, misconception
> source pinning, Schrägriss foreshortening convention, a/b/c edge mapping, …) awaits the SME in
> `project-handoff.md` Session 14. Each item below is annotated with what shipped.

### Wave A — task & figure engines

- **A1 · Figure-engine rework (the port). ✅ SHIPPED S14** — all ~25 recipes draw through `figstyle`
  roles/ramps (0 hex literals, `tests/test_figstyle_port.py` locks it); `right_triangle`/`rectangle`/
  `polygon` became computed `Scene`s; a render-probe font fallback fixes a py3.14/mpl3.11 Calibri
  glyph-drop that silently blanked small labels; specimen scripts per family. Original text follows.
  Move the ~25 legacy matplotlib recipes onto `figstyle`
  (semantic roles, categorical+dash ramps, house font) — and onto `scene` composition where a recipe is
  naturally primitives. Acceptance: no hard-coded hexes outside `figstyle`; specimen scripts per family;
  `tests/test_layout.py` green. The long-deferred styleguide item — do it before new figure families
  multiply the debt. *(Design: `figure-styleguide.md`.)*
- **A2 · The Physics engine (SME: clear win). ✅ SHIPPED S14** — *(a)* `pipeline/physics.py` (6 recipes,
  answers dimensionally verified via `sympy.physics.units` — unit-category errors structurally
  impossible) + `grounding/physics.py` (g exact, cited school densities) + 7 `phy-*` templates;
  *(b)* `pipeline/optics.py` (thin-lens ray construction, drei Hauptstrahlen as stages, given/sought
  masking) + `pipeline/circuits.py` (netlist → Kirchhoff solve → schematic, per-element `mask=[…]`) +
  `matplotlib:optics_ray`/`matplotlib:circuit`. Mirrors (Hohlspiegel/Ebener Spiegel) deferred. Original:
  *(a) parametric pack* — `pipeline/physics.py` recipes with **`sympy.physics.units`** so every answer
  is **dimensionally verified** (unit errors structurally impossible): uniform motion, density,
  Ohm + series/parallel (Ersatzwiderstand), lever/torque, energy/power; US anchors (PHY Kl. 2–4) + OS
  templates, the `che-*` template pattern. Curated constants (`grounding/physics.py`, CODATA values +
  `SourceRef`) — select-never-author for constants too.
  *(b) scene families* — **optics ray construction** (Sammellinse/Zerstreuungslinse/Spiegel via thin-lens
  math; the drei Hauptstrahlen as `stage`s like `triangle_construction`; image position maskable
  "B′ = ?") and **circuits** (typed netlist → schematic from scene primitives; values computed via
  Kirchhoff linear solve — the sympy linear-algebra machinery `balance_equation` proved). Completes the
  MINT trio; pairs with the CHE-figures gap (old theme B bundle).
- **A3 · The Misconception engine (SME: love it). ✅ SHIPPED S14** — `grounding/misconceptions.py` (9
  literature-sourced error patterns: Radatz/Malle/Padberg-Wartha/Physik-/Chemiedidaktik) +
  `pipeline/misconceive.py` (`@_misconception` transforms); MC distractors COMPUTED by applying the
  misconception to the drawn values — guaranteed ≠ correct post-formatting, deduped, plausibility-gated;
  the teacher guide names each probe via `watch_outs`. MAT/PHY/CHE recipes + 4 MC templates. The
  non-parametric distractor-pattern field stays the roadmap's "later". Original text:
  Distractors correct-by-construction. A curated
  catalog `grounding/misconceptions.py` (id · domain scope · description · the classic error-analysis
  literature as source note — Radatz for arithmetic, Malle for algebra), transforms registered like
  recipes (`@_misconception` in `pipeline/misconceive.py`); a `multiple_choice` parametric variant's
  distractor = `transform(instance)` — **guaranteed ≠ the correct answer** (both computed), deduped,
  plausibility-gated. The teacher guide names **which misconception each distractor probes** ("B prüft
  den Vorzeichenfehler"). Start on MAT parametrics (sign error, forgotten carry, unit slip, percentage
  base confusion), extend to CHE/PHY; later a curated distractor-pattern field for non-parametric MC.
  `intentionally_flawed`, generalized into a theory.
- **A4 · Solution graphs (SME: yes). ✅ SHIPPED S14** — `SolutionPath` (strategy + steps) on `Instance`
  and `TaskBlock`; `linear_system_2` emits Einsetzungs-/Gleichsetzungs-/Additionsverfahren,
  `percentage`/`percentage_rate` emit Dreisatz/Operator/Formel — each path independently derived via
  sympy and asserted equal to the primary answer before shipping; teacher projection renders
  "Alternative Lösungswege", student/homework proven clean; generation-view omission lock test-locked.
  Original text: Recipes emit ONE Rechenweg; classrooms produce several. Extend
  `Instance` with optional `solution_paths` (named strategy + steps); teacher rendering "Alternative
  Lösungswege / Schüler könnten auch…". Start where strategies genuinely diverge: LGS
  (Einsetzen/Gleichsetzen/Addition), Prozentrechnung (Dreisatz/Operator/Formel). Teacher-only, DERIVED.
- **A5 · The Rätsel engine (SME: great — Rätsel are super fun for pupils). ✅ SHIPPED S14** —
  `pipeline/puzzles.py` + `schema/puzzle.py`: Kreuzworträtsel (backtracking crossing grid),
  Suchsel (with accidental-duplicate refill guard), Domino (closes iff every match correct — self-check
  by graph construction), Rechenmauern (unique-solution masking verified by propagation). One core kind
  `puzzle` (no write-space); `matplotlib:puzzle_grid`; teacher-only solved grid via
  `solution_asset_refs`; umlaut = single-cell (flip-in-one-place). Corpus-scale clue ingest is the
  follow-up. Original text: `pipeline/puzzles.py`,
  zero LLM, answers derived: **Kreuzworträtsel** (backtracking grid placement over curated clue/answer
  pairs — Sachverhalt `Concept`s, vocab annotations, chemistry curated tables feed clues across many
  subjects; decide the umlaut convention Ä vs AE), **Suchsel** (trivial), **Domino/Trimino chains**
  (from matching pairs; the chain **closes iff every match is correct** — self-checking by graph
  construction), **Rechenmauern** (parametric, derived). Design decisions: puzzle = code-gen asset
  (grid figure) + a task block wrapper; whether new `task_kind_extensions` or core kinds carry them;
  teacher-only solution grid; age scaling.
- **A6 · Readability — the Wiener Sachtextformel (SME: good). ✅ SHIPPED S14** — `pipeline/readability.py`
  (WSTF1, Bamberger/Vanecek; documented German syllable heuristic) + advisory verify warning when a
  block reads ≫ target Schulstufe + block-card badge (computed on demand, never persisted). Verbatim
  sources (`quoted`/`source_text`) are exempt — deliberately hard IS the Quellenarbeit. Scope-variant
  linguistic targets deferred (a clean 3-file signature change — chip `task_8964d0d4`). Original text:
  *The* German readability measure (and
  Austrian: Bamberger/Vanecek) as `pipeline/readability.py`: grade-level estimate per prose/info block
  (German syllable counting is heuristic → **advisory lane only**), a verify warning when block level ≫
  target Klasse, surfaced on dashboard block cards; `scope` variants gain linguistic targets (compact =
  also linguistically lighter), not just length.
- **A7 · GZ / Darstellende Geometrie — promote the 3D prototype (SME: agreed). ✅ SHIPPED S14** —
  `pipeline/scene3d.py`: `Scene3D` + axonometric projection + closed-form back-face hidden-line
  classification (raises `NotConvex` at the boundary); `axonometric_solid` (Quader/Prisma/Pyramide/
  Zylinder/Kegel, hidden edges dashed, base-rim back arc dashed) + `riss_pair` (Grund-/Aufriss,
  per-Riss visibility with the coincidence rule). Anchors found: GZ `GEZ.US.4.PRO.*`, DG
  `DGE.OS.7.ARB5.*` — a master-library flagship per Stufe is the follow-up. Original text: The validated
  machinery (`tools/plane3d_specimen.py`: `Scene3D` + axonometric `project` + closed-form hidden-line
  occlusion) → `pipeline/scene3d.py` + `@_generator` recipes per the promotion path in
  `scene3d-geometry-design.md`: `axonometric_solid` (Schrägriss of prisms/pyramids/cylinders, hidden
  edges dashed) and `riss_pair` (Grund-/Aufriss pairs). Anchors: GZ (US) + DG (OS) — a subject with
  zero coverage gets its engine.

### Wave B — the image program (design: **`illustration-design.md`**, accepted 5 Jul 2026)

The load-bearing reframe: **an image is a CLAIM (fact — curated/checkable) plus a RENDERING (expression
— authorable under constraint)** — mechanism 4 extended to pixels; the corpus model (vet once, reuse
forever) is what makes diffusion viable at all. Media policy gains a **third lane — `depictive`**
(shows a thing; no labels/numbers/text) between decorative and content; the content lane stays
code-gen/sourced **forever**. Resolution hierarchy: reuse › sourced PD/CC › diffusion › none.

- **B1 · Backend + gates:** `teachersaid/imagegen/` (the TTS cp312-subprocess pattern; **Flux.1-schnell**,
  Apache-2.0, fits the 4070 quantized) wired via the existing `register_diffusion_backend`; a stored
  **`DiffusionSpec`** (model/prompt/negative/seed/steps/cfg/size) makes every image *replayable*;
  deterministic pre-review lints (**OCR no-text** auto-reject, **photocopy-survival** grayscale check,
  resolution/alpha); the style contract + `tools/illustration_specimen.py`.
- **B2 · Warmth:** Realien backdrops first (**risk-free by construction** — invented world, invented
  picture) + worksheet header vignettes (a `theme_asset` slot); **best-of-N seed-grid review** in the
  Abbildungen tab (choosing beats judging).
- **B3 · The depictive lane + the Beschriftungs-hybrid (the flagship):** `intended_claim` + checklist
  review; labeling tasks = vetted base image + curated anchor points + a **code-drawn label layer**
  (leader lines via `figtext`, maskable `show_value=False`) — text never enters the pixel layer. Task
  spots under the seductive-details policy (relevance rule · density cap · placement · age register).
- **B4 · Compounding:** a style LoRA trained on ≥~50 SME-approved images (the style locks itself in);
  mascots as **fixed art** (not per-sheet diffusion); optional color-by-answer finishers (gimmick lane).
- **B5 · PD Bildquellen — the 6th asset class (SME: very clear win).** The visual sibling of the
  annotated texts: an `ImageSource` = a PD-by-age artwork/photo/caricature + a curated annotation layer
  (Beschreibung → Analyse → Interpretation, the Bildquellenkritik ladder) → derived GPB/BE tasks.
  Rights: the AT 70-p.m.a. gate + the **PD-work ≠ PD-reproduction** per-item caution; fetch via a
  Wikimedia Commons tool (machine-readable per-file rights — shared with B's sourced lane). Flagship
  candidate: the Isabey Wiener-Kongress engraving — ties straight into the existing Sachverhalt +
  Quellenarbeit flagships.

### Wave C — corpus structure (the holistic layer)

- **C1 · The prerequisite graph (SME: awesome — think holistic).** A curated edge catalog
  `grounding/prerequisites/<CODE>.json` (competence → its prerequisites, cross-Klasse) + loader +
  cycle/dangling-id lints. One graph, many pure queries: **Diagnose-Blätter** (one approved band-1 task
  per prerequisite ancestor of a topic), compose **warm-up injection** ("Bevor wir starten…"), **spiral
  revision** (resurface descendants at later Klassen), **campaign ordering** (fill prerequisites before
  dependents), a **difficulty feature** (graph depth), and a coverage-map overlay (an empty cell that
  BLOCKS dependents matters more than a leaf). Start with MAT (cleanest structure), then PHY/CHE.
- **C2 · Entity registry + cross-module consistency (SME: good).** Canonical entities
  (person/place/event/work: names, dates, facts, source) in `grounding/entities.py`; Sachverhalt
  `Actor`/`HistEvent` link by `entity_id`; a **corpus-level lint**: the same entity must carry
  consistent dates/attributes across ALL modules (the entity-lint promoted from module-internal to
  corpus-global — anti-drift at scale). Derived joys: "verwandte Module" links, merged epoch timelines
  per Klasse.
- **C3 · ÜT cross-subject bundles (SME: yes).** The übergreifende Themen tags already sit on
  competences; nobody composes across subjects. `compose_uet(uet, klasse, envelope)`: approved blocks
  whose serves-competences carry the ÜT across ≥2 subjects → per-subject roles → a **Lernarrangement**
  (the Projektwoche bundle; shared product as the anchor). v0.5 machinery exists and is waiting.
- **C4 · Difficulty as a computed quantity (SME: hard but wanted — exploratory).** Structural
  psychometrics, no students needed: features derivable from the task itself — **solution-step count**
  (parametrics carry the derivation!), operation depth, number-domain (ℕ < fractions < irrationals),
  **text load via A6's WSTF**, kind base-cost, scaffold presence — combined by transparent weights
  **calibrated against the SME's ~1100 authored 1–3 labels** (simple ordinal fit, offline) with the
  Matura operator×AFB data (`extract_matura`) as the external anchor. Discipline: **DERIVED +
  advisory** — never overrides the authored `difficulty`; a ≥1-band disagreement becomes a verify
  warning and a dashboard signal. If the fit is poor, that's a finding, not a failure.
- **C5 · The dramaturgy engine (SME: could be extremely powerful — PLAN CAREFULLY, design-first).**
  Track 2's acknowledged hard problem (inter-block coherence), approached didactically: a typed phase
  grammar (**Einstieg → Erarbeitung → Sicherung → Transfer**) as a plan layer; blocks carry a
  phase-affinity (harvest infers, SME corrects at review); `compose` orders against the grammar;
  bridging prose is **constrained re-expression (mechanism 4)** over the adjacent blocks' frozen
  content — vetted task content untouched, offline fallback = template transitions (the `frame.py`
  pattern). **First deliverable is a design doc** (`dramaturgy-design.md`): the phase-model choice, how
  phases interact with envelope/scope/difficulty ramps, what harvest can infer vs. what the SME tags,
  and how coherence is *measured* — no code before the doc is agreed.

### Maintenance (small, standing)

- **CHE2 routing fix:** ✅ DONE (S14) — `_DISPLAY_NAME_OVERRIDES` keyed `(stufe, code)` gives the second
  CHEMIE subject a distinct display name ("Chemie (Wirtschaftskundliches Realgymnasium)") at `_meta`
  load, so name-routed campaigns reach CHE2's 6 US cells; plain "Chemie" still routes to CHE.
- **Fassung 2026/27 watch** *(deferred by decision, Session 3 — do not relitigate)*: becomes a real
  task when the new consolidated Fassung is published in full text; then run the parser diff + the
  migration tooling (old Track-3 #8: ID map, re-anchor, re-derive, flag orphans).
- **Geosphere-Klimadiagramm re-decision** (carried from Session 12).

### Parked by decision (5 Jul 2026 — with reasons, so they don't silently resurface)

- **Music notation engine** — architecturally interesting (staff = scene primitives + Bravura/SMuFL
  glyphs; a synth backend on the TTS subprocess pattern), but ME in AHS practice is a relaxed subject
  with little worksheet demand. Revisit only if demand appears.
- **Experiment/Versuch asset class** — too dependent on what apparatus each school actually has to
  build properly. (The `experiment_protocol` task-kind demand stays visible in `subject_models.json`.)
- **Self-checking worksheets (Lösungswort/checksum)** — a nice gimmick, not load-bearing. The
  color-by-answer variant may ride illustration P4; the Trimino closed-chain self-check lives on inside
  A5, where it earns its place as a Rätsel.

### Raised 5 Jul, unranked — awaiting an SME call

Stumme Karten + cartography layers (rivers/cities from Natural Earth, label-masking) · a **Typst**
renderer (native math, German Silbentrennung; the handoff-brief contract makes it a clean parallel
build) · vision-**Blattkritik** (corpus-loop LLM critique of the QA rasters → advisory feedback lane) ·
the **Nachweis/coverage made beautiful** (per-sheet Kompetenz-Landkarte; the coverage poster).

---

## The offline-first program (2 Jul 2026) — Tracks 1–2 built; superseded as "start here" by the 5 Jul program above

*Still-live threads from this program map into the new one: Track-2 **#4 inter-block coherence** → the
**dramaturgy engine (C5, design-first)**; Track-2 **#6 "Varianten erzeugen" surface** → still open,
unranked; Track-3 **wedge campaigns** remain a standing activity (planner-driven, `/api/coverage/gaps`);
Track-3 **#8 Fassung tooling** → Maintenance. The joy lane's `figstyle` port → **A1**; 3D promotion →
**A7**; physics vectors / label-the-parts scenes → **A2(b)** / **B3**.*

> **Session update (2 Jul 2026) — THE PIVOT (Session 11).** The product is the **curated corpus +
> deterministic, LLM-free delivery**; live on-demand generation is deferred (not deleted — the `llm/`
> seam is the campaign seam). Two loops: the **corpus loop** (campaigns: briefs → feature engines →
> lints → SME gate → approved corpus) is where the LLM lives; the **delivery loop** (serve a vetted
> sheet › compose from approved blocks › honest gap → demand queue) is what a teacher touches.
> Decision + rationale: `project-handoff.md` Session 11 + §4; rule + boundary: `invariants.md` **§10**.
> **Working mode: build-for-joy** — no deadline, no GTM clock; "inherently cool" is a valid justification.

> **Status (3 Jul 2026, Session 12):** Track 1 **BUILT** (#1 planner · #2 numbers lint · #3 Prüfen gate:
> tier lanes + cascade + triage + Überarbeiten); Track 2 **#4-v1/#5 BUILT** (deliver read-path +
> Wunschliste); the dashboard is the four stations; the staged backlog is SME-cleared; figures obey the
> no-scientific-notation/unit-scale/numeric-time rule (`figstyle`); the chemistry Übungsreihen passed the
> **blackboard test** (c0167–c0169 approved; the bar: beat what a teacher writes on the board in a
> minute). **Open next:** Track 3 campaigns (`/api/coverage/gaps` anchors) · Track 2 #4 inter-block
> coherence + #6 "Varianten erzeugen" surface · geosphere-Klimadiagramm re-decision · joy lane.

**The program — three tracks + a joy lane** *(tracks are dependency order, not a schedule)*:

**Track 1 — foundations:**
1. **The coverage map as the instrument.** Define "covered" per (subject × Klasse × Kompetenzbereich):
   ≥N approved task blocks spanning the Anforderungsbereich bands + a scope variant (+ the KB's iconic
   figure type where one exists). Upgrade **Statistik** from curiosity to **campaign planner**: progress
   bars against the full catalog (US + OS), exportable gap lists that become campaign briefs
   (`suggest_from_catalog` already seeds ideas from gaps). *The corpus gets a progress bar — watching it
   fill is the game loop.*
2. **The numeric-claims lint** (the last authored-number hole, found in the 2 Jul review): every number
   in a `data_source` task's prompt/`answer_key` must be derivable from the cited dataset slice
   (± rounding/aggregation) — the entity-lint pattern applied to numbers. Doubles as the **anti-rot
   mechanism**: derived values re-ground on dataset refresh; baked values go stale silently.
3. **The review economy.** (a) **Tier the gate** by correct-by-construction mechanism — computed →
   template-level review only; selected → source spot-check; re-expressed → lint + language read; curated
   prose → full SME read. (b) An **adversarial triage agent** that ranks/flags before the SME looks
   (didactics, register, answer-key consistency) — *triage, never the gate*. (c) Review-UX polish
   (keyboard flow, lint-confidence batching) so a review session is fast and pleasant. Then **clear the
   fact-bearing backlog** (8 datasets · 10 texts · 5 Sachverhalte sit unreviewed) — it blocks whole
   corpus classes.

**Track 2 — the delivery loop:**
4. **Compose v2.** The retrieval hierarchy (**serve a vetted worksheet › compose from blocks › honest
   gap**) + **inter-block coherence**, the new hard problem (independently-vetted blocks can clash in
   context, notation, redundancy): curated block *sequences* as first-class objects, compatibility
   signals captured at review time, dedup across repeated requests.
5. **The demand queue.** A gap at request time becomes a recorded wish ("Wunschliste") feeding Track-3
   campaign briefs — the self-directing backlog, meaningful even with one user.
6. **Deterministic runtime generation, surfaced.** The "Varianten erzeugen" dashboard surface
   (`orch.compose_variants` exists); parametric/scene instantiation at delivery (Gruppe A/B for
   Schularbeiten, fresh Hausübungs-numbers) — *live generation without an LLM*, zero marginal review cost.

**Track 3 — corpus campaigns (the long game):**
7. **Wedge-to-green campaigns:** Physik + Mathematik + GWB Unterstufe to full KB coverage first (where
   correct-by-construction bites hardest), then follow curiosity. Every campaign doubles as an engine
   stress test — the GWB run surfaced two missing figure recipes; that pattern is a feature.
8. **Fassung 2026/27 migration tooling** (when the new Fassung publishes): old→new competence-ID map,
   re-anchor the corpus, re-derive every Nachweis, flag orphans. A corpus outlives its Fassung;
   hand-migrating ~1000 blocks is not an option.

**The joy lane (unscheduled — pick by interest, guilt-free by decision):** the audio **"Stimmen"** tab +
dialogue-turns emission · more scene recipes (physics vectors, label-the-parts) + the `figstyle` port of
the ~25 legacy recipes · **3D scene promotion** (`tools/plane3d_specimen.py` → `pipeline/scene3d.py`) ·
informational Realien · ANNO/OCR media texts · more parametric recipes (the Matura-backward queue below) ·
the **polish batch** from the 2 Jul review (the "Abgedeckte Lücken" label in `rendering/_document.py`,
German „…"-quotes at render time, Tiefenprofil in ladder order, `store/base.py` corrupt-file logging,
true/false table row heights).

*(Everything below predates the pivot. The backlog items remain valid — they are all corpus-loop work —
but the 1 Jul "Recommended next" ordering is superseded by the tracks above.)*

## Session log (1 Jul 2026 and earlier)

> **Session update (1 Jul 2026) — the figure engine.** A styleguide + a scene engine (design:
> `Documents/figure-styleguide.md`). **`pipeline/figstyle.py`** centralises the visual language —
> semantic colour ROLES (colour MEANS something: `focus` = the unknown/result/region of interest), a
> categorical hue ramp and a **dash ramp** (a redundant hue+dash pair per family, so a dense figure
> survives a B/W photocopy), and the document font matched to the worksheet body (Carlito/Calibri, not
> DejaVu). **`pipeline/scene.py`** makes a figure a composable `Scene` of typed primitives
> (`Polyline·Line·PointMark·CircleShape·Arc·Region·Label`) with one house-styled renderer — so a rich
> figure is *composed*, not hand-coded, and the SAME scene renders at different **densities** (a
> step-by-step construction worksheet from one computed object). First recipes, correct-by-construction
> with value labels **maskable** (task/solution split): **geometry** `triangle_construction` (the
> merkwürdige Punkte des Dreiecks, `stage` 1–6) and the **analysis family** via sympy —
> `function_plot·integral_area·tangent·riemann_sum·extrema·area_between·distribution`. Full suite **368**.
> **Next candidates:** port the ~25 legacy recipes to `figstyle` (the deferred styleguide port); more
> scene recipes (physics vectors, annotated "label-the-parts" diagrams, node-link consolidation); a
> first-class density/stage selector on scenes.

> **Session update (30 Jun 2026).** Two asset lines advanced + one infra change:
> - **Sachverhalt — Phase 3 (subagent breadth) DONE.** `tools/sachverhalt_prompt.py` +
>   `tools/ingest_sachverhalte.py`; first push = 4 verify-clean modules (GPB *Französische Revolution*/
>   *Industrialisierung*, BIO *Photosynthese*/*Verdauung*). The content layer is built P1–P3.
> - **Realien — a NEW asset class, BUILT P1–P3** (`Documents/realien-design.md`): CEFR-leveled
>   *communicative* FS reading. The load-bearing reframe is **purpose-appropriate rigor** — a Realie is a
>   *Sprechanlass, not an Aussage*, so the facts are invented-coherent fiction (an internal-consistency
>   lint, not world-grounding) and the **language** is what's load-bearing (SME-gated). 8 Realien (EN+FR,
>   A1+A2, 8 genres), each a real-artifact card with atmosphere + a reasoning task ladder; the
>   arrangement wrap (speaking as an interaction anchor); the breadth seam (`realien_prompt`/`ingest_realien`).
>   **Consciously DEFERRED:** the *informational*-genre half (news-in-levels / factual texts where
>   fact-care snaps back) — needs a sourced/dataset-grounded approach (licence-sensitive); see §"Annotated
>   Realien".
> - **Persistence policy changed.** `runs/` is no longer wholesale-ignored: **git owns the generated
>   content + review state** (`runs/**/*.json|.md|.txt`), **ignores only the binaries** (PDF/PNG renders).
>   Remote-session work now survives in git; Drive can carry the binaries. (`.gitignore` + `CLAUDE.md`.)
> - Full suite **350 passed**. Next-session candidates: SME gate-review of the staged content; informational
>   Realien (when ready); or a fresh track.

> **Big bet — the Sachverhalt content/exposition layer: Phase 1 BUILT (30 Jun 2026).** Design +
> decisions: `Documents/sachverhalt-content-layer-design.md`; codebase guide: `CLAUDE.md` "Sachverhalt".
> The measured cross-subject gap (engine task-generative, prose-thin; the Lehrplan's **Sachkompetenz**
> demands a didactic Darstellung) is closed for **History**: a curated, sourced **Sachverhalt** module
> (structured facts → grounded Darstellung + DERIVED timeline/Wirkungsgefüge + correct-by-construction
> Sachkompetenz tasks) — the **fourth** correct-by-construction mechanism (*re-expressed under constraint*,
> `invariants.md` §3): facts selected/sourced, prose authored over the *frozen* fact-set with a
> deterministic entity-lint (years machine-guaranteed). Flagship *Der Wiener Kongress*; full HITL surface +
> the **Sachverhalte** tab; 18 tests, verify-clean. **Phase 2 DONE (30 Jun 2026, Biology):** *Der
> Blutkreislauf* added the undated **`Process`/cycle** fact-type (a `matplotlib:process_flow` cycle figure +
> a process-ordering task) behind the same container — proving it isn't history-locked, with W/S
> strand-correct anchoring and the judgment kind auto-selected. **Phase 3 DONE (30 Jun 2026):** subagent
> scaling — `tools/sachverhalt_prompt.py` (grounded per-topic brief) + `tools/ingest_sachverhalte.py`
> (normalizer/facts-gate/entity-lint, the `ingest_batch` twin); first push = 4 verify-clean modules (GPB
> *Französische Revolution*/*Industrialisierung* timeline, BIO *Photosynthese*/*Verdauung* process), every
> prose year backed by a timeline event, staged `in_review`. **Geographie DONE too (the first MAP):** the GWB
> flagship *Bevölkerung in Österreichs Bundesländern* added a spatial **`Region`** fact-type + a
> correct-by-construction **choropleth** (`matplotlib:choropleth_map`) — sourced CC-BY boundaries (the new
> geo layer `grounding/geo/` + `grounding/geo_store.py` + `tools/fetch_geo_boundaries.py`, *boundaries are
> facts*) filled by the cited population dataset; pure matplotlib, **no geo dependency**.

> **Update (29 Jun 2026): Matura orientation.** The SRDP (Matura) was studied as the competence-
> model capstone. Two cheap, high-value uses agreed (NOT a new asset class — see
> `Documents/matura-operators.md`): **#2 harvest the Operatoren — DONE** (a subject-aware grounding
> table in `grounding/operators.py`, 4 authoritative CC-BY catalogs DEU/GWB/Naturwiss./MAT, wired
> into the generation brief); **#1 calibration — DONE** (`tools/extract_matura.py` extracts the
> exam archive; calibrated against 6 AHS-Math exams 2014–2025 → the cognitive_level→AFB→difficulty
> model holds, no change needed; results + the realistic-AFB-mix finding in
> `Documents/matura-calibration.md`). The **full-archive build is now done too** (next block), and
> the **accessible-Matura figure scan** added the `boxplot` + `tree_diagram` recipes (WS strand).

### ☑ DONE (home PC, 29 Jun 2026) — automated full Matura-archive extractor

Built at home (the remote session's egress proxy had blocked `matura.gv.at`/`aufgabenpool.at`;
a normal home network reaches both — aufgabenpool's 403 was only User-Agent gating). All three
parts shipped, deterministic + no-LLM, on the `matura-archive-extractor` branch:

1. **Downloader — `tools/fetch_matura.py`.** matura.gv.at `/downloads` is a TYPO3 *tx_downloads* +
   Solr archive; **each exam is a "Collection"** served as a zip (Aufgaben + Korrektur, the stable
   `KL25_PT1_AHS_MAT_00_DE_{AU,LO}.pdf` naming). Crawls `year` (2013/14…now) × `documentType`
   (Klausuren | Kompensationsprüfungen) × `subject` × `schoolType` (AHS/BHS/BRP) with pagination;
   the download URL's per-collection **`cHash`** is scraped (can't be fabricated). `--all` /
   `--standard-only` / `--list` / `--extract`; idempotent **manifest** with CC-BY (IWG 2022) +
   *"Datenquelle: BMB"*. Raw zips → `runs/matura/` (git-ignored; Drive-synced).
2. **Subject-aware `tools/extract_matura.py`.** Dispatch on the subject code (the load-bearing fix:
   the filename language slot is a CEFR code `B1/B2/A2`, not `[A-Z]{2}`). Math/AMT keep the task+point
   parser; **Deutsch** parses the Korrekturheft's labelled fields (Textsorte · Wortanzahl ·
   Schreibhandlungen · operator-headed Arbeitsaufträge → canonical `operators.DEUTSCH` forms);
   **Latein/Griechisch** the ÜT/IT split + sources + numbered IT Arbeitsaufgaben; **modern languages**
   skill × CEFR × item-formats. The **sciences/GWB have no Klausur archive** (oral/teilstandardisiert) —
   confirmed, no parser needed.
3. **Demand maps — `tools/matura_demand.py`** aggregates `runs/matura/json/` per subject (operators
   validated vs catalogs, etc.) → the `matura-<subject>-coverage.md` write-ups (Deutsch + Latein +
   languages added alongside Maths).

**Guards held:** no raw PDFs/corpus in git (`runs/` + Drive); pure-function parsers unit-tested offline
(`tests/test_fetch_matura.py`, extended `tests/test_extract_matura.py`). Re-mirror anytime via
`fetch_matura --all`.

**Corpus run (151 collections) + the demand maps it produced:**
- **Deutsch (33 exams):** 9 Textsorten + 6 Schreibhandlungen exercised; operators **100 % catalog-
  covered** across 198 Aufgaben (validates `operators.DEUTSCH` at scale). → `matura-deutsch-coverage.md`.
- **Latein (41 exams):** ÜT 36 / IT 24 pts stable across *every* exam; surfaced **9 operators with no
  catalog yet** (the empirical seed for a LAT Operatorenliste) + huge PD source-author breadth. →
  `matura-latein-coverage.md`.
- **Languages (41 Englisch booklets):** the full skill×CEFR matrix (Lesen/Hören/Schreiben/
  Sprachverwendung × B1/B2). → `matura-languages-coverage.md`.
- **AMT fix:** the 36-exam run showed `operator_set("AMT")` falling to `DEFAULT`; wired AMT→MATHEMATIK
  (+ alias resolver, locked by a test).

**Accessible-edition figure scan → two new recipes.** `fetch_matura --variant accessibility` pulls the
Blindheit/Sehbehinderung Math editions, whose linearised RTF exposes real numbers/formulas **and**
textual figure descriptions. Scanning 14 booklets surfaced two recurring **WS-strand** figure types with
no recipe — both now built correct-by-construction: **`matplotlib:boxplot`** (five-number summary /
distribution comparison; new `spread` intent in `chart_choose`) and **`matplotlib:tree_diagram`**
(Baumdiagramm, spec-provided branch probabilities). See `matura-math-coverage.md`.

**Four "asset classes" now exist** — each makes content trustworthy by finding the thing that's
correct-by-construction (or curation) and making it the durable, reusable asset:
- **Grounded-facts data layer** (Geography/MINT): real cited numbers from 8 curated CC-BY datasets →
  derived figures (population-pyramid · timeline · climate_diagram). Proven by 22 GWB/MAT/PHY worksheets.
- **Parametric Maths engine**: sympy recipes → N correct-by-construction variants + worked Rechenweg;
  10 templates across all 4 MAT KBs; inline math typesetting; **+ the geometry figure family (KB3)**
  (right_triangle · rectangle · polygon · circle · coordinate_plane).
- **Annotated authentic texts** (Deutsch + **Latein**): real PD texts + a vetted annotation layer →
  derived comprehension/analysis/Medienkritik/translation/writing tasks, line-numbered source rendering,
  the AT 70-p.m.a. rights gate, the Texte tab. Flagships: Heine *Lore-Ley*, Lessing *Rabe und Fuchs*,
  Phaedrus *Vulpes et Corvus* (Latein: `translation`/`grammar`/`culture`).
- **Audio / Hörverstehen** (modern FS): a `medium="audio"` `AnnotatedText` → spoken `audio:tts` asset +
  listening tasks (HOR) + **teacher-only transcript**. The **real TTS backend is now WIRED** — F5-TTS
  multi-voice on the local GPU, voices selected from a curated rights-gated reference library. See
  `Documents/tts-audio-engine.md`. Flagship: *Mia's school day* (A2).

Also: store consolidation (`store/base.py::JsonStore`, the future-DB seam). **265 tests green.**

**Matura-backward build targets — ✅ ALL THREE DONE (10 Jul 2026, see the session block above):**

- **Maths · WS-strand recipes** (`matura-math-coverage.md`): the figure half is done (boxplot + tree);
  the parametric half remains — a **boxplot-from-data** recipe (compute the quartiles + Rechenweg) and a
  **probability-tree → path/conditional-probability** recipe. Above those in frequency: **exponential /
  growth-decay / compound interest** (FA) is still the #1 cleanest sympy recipe to add.
- **Deutsch · genre scaffold** (`matura-deutsch-coverage.md`, step 3): wire the (already-built) Textsorten
  + Schreibhandlungen grounding into `text_tasks` — emit a *Matura-shaped but scaffolded* worksheet that
  **teaches** the Textsorte. Frequency-ranked build order (Zusammenfassung/Kommentar/Interpretation lead).
- **Latein · operator catalog + Wortbildung** (`matura-latein-coverage.md`): curate a faithful SRDP-Latein
  Operatorenliste (the 9-operator seed is in the doc) and wire `LAT`; add a deterministic **Wortbildung**
  (Präfix/Suffix) recipe — the one genuinely *computable* Latein task type.

**Recommended next, in order:**

1. **Finish the audio product surface** (engine is wired; see `tts-audio-engine.md §7`): a HITL
   **"Stimmen" review tab** (`VoiceStore`, the *Abbildungen*/*Datensätze* analogue) + call
   `audio.register()` at dashboard startup; evolve `text_tasks` to emit a **turns** spec from a dialogue
   `AnnotatedText` (needs a speaker/turn model); add **FLEURS** references + `de/fr/it/es` checkpoints.
2. **Annotated Realien for FS reading** — CEFR-leveled authentic everyday texts (menus, signs, schedules,
   short messages) via the annotated-text engine; the leveling answer for FS Lesen (confirmed B1+B2 demand,
   `matura-languages-coverage.md`).
3. ~~**Geometry — parametric figure emission + nets**~~ — ✅ **DONE (11 Jul 2026)**
   (`Instance.figure` → masked per-variant assets; `pythagoras` + `kreis_umfang_flaeche` +
   `quader_oberflaeche`; scene-based `matplotlib:solid_net` for Quader/Würfel).
4. **Scale the text libraries** — *progressed 10 Jul:* `tools/fetch_wikisource.py` + 5 staged texts;
   still open: more grades/authors, the **ANNO/OCR fetch tool** for real newspaper/advert media texts.
5. **More parametric recipes + a "Varianten erzeugen" dashboard surface**; expose `orch.compose_variants`.
   *The Matura-backward recipe queue is cleared (10 Jul);* the dashboard surface is still open.
6. ~~**Re-ground the old invented-number figures**~~ — ✅ **DONE (10 Jul 2026)** (c0081/c0096/c0097; 4 new
   sources, 12 datasets). Still open: **BIO/other-subject** datasets; **Tier-2 regional** down to Bezirk.

Standing tracks (no build needed): **geography teacher reviews** the 9 GWB worksheets (c0089–c0097),
the staged dataset, + earlier staged items in the dashboard; **GPB Quellenarbeit via ANNO/ALEX is
buildable now** as referenced-only (b2) — well-chosen task prompts pointing at the archives, no ingest tooling.

Details for each below ↓

## Languages (FS / Latein) — the asset class for languages *(planned 27 Jun 2026)*

The catalog splits the languages cleanly, so they get different treatments:

- **Latein — DONE (27 Jun 2026).** All printable (Sprach-/textbezogen + Inhalts-/Kulturkompetenz), with
  abundant PD source texts — the annotated-authentic-text engine carries it almost directly. Added
  `translation`/`grammar`/`culture` annotation kinds (dims SPR/INH; task kinds translation/text_analysis/
  open_response) + the Phaedrus *Vulpes et Corvus* flagship. The same fox-and-flattery fable as the German
  *Rabe und Fuchs* — one asset class, three languages.

- **Modern FS (Englisch/Französisch) — the trickiest, planned.** Half the Lehrplan is **oral** (Sprechen
  is the biggest KB, + Hören), it's CEFR/can-do (A1/A2), and the L2 material is the target language. Three
  structural difficulties German didn't have: (1) the oral core can't be reached on paper; (2) CEFR
  leveling fights "authentic" — native PD text is the wrong difficulty; (3) modern level-appropriate L2
  text/audio isn't PD. Two planned tracks:

### Audio — Hörverstehen (the FS breakthrough) — ✅ **engine + seam + REAL BACKEND DONE (28 Jun 2026)**
- **Content layer:** an `AnnotatedText` with `medium="audio"` → `build_worksheet` attaches a spoken
  `Asset(role="tts", generator="audio:tts", medium=audio)`, renders a printable audio cue + listening
  tasks (`listening_task`, dim HOR), and keeps the **transcript teacher-only** (oral-modality `source_text`;
  `show_transcript=True` → A1 listen-and-read). Media-policy admits `tts` as a code backend; transcript =
  printable fallback. Flagship: *Mia's school day* (A2, FS1 Kl 2).
- **Real TTS backend — WIRED (full notes: `Documents/tts-audio-engine.md`):** **F5-TTS multi-voice on the
  local GPU** (RTX 4070, ~4× real-time). Architecture: the 3.14 core drives a **separate Python 3.12**
  subprocess (CUDA torch has no cp314 wheel) — `audio/f5_backend.py` (core, no torch) resolves each turn's
  `(lang, persona)` to a curated voice and calls `audio/f5_render.py` (GPU), then ffmpeg-encodes mp3.
  Voices are **selected, never authored**: a **rights-gated reference library** (`schema/voices.py`,
  `grounding/voice_store.py`, `tools/fetch_vctk_voices.py`) of CC-BY young-adult VCTK clips. `turns` spec =
  multi-voice dialogues (the v1 capability). Proven end-to-end via `build_audio`; 8 offline tests added.
- **Still to do** (see `tts-audio-engine.md §7`): the HITL **"Stimmen" review tab** + `audio.register()` at
  startup; `text_tasks` **turns** emission from a dialogue text; **FLEURS** refs + `de/fr/it/es` checkpoints;
  a **sourced-audio path** (real recordings + rights, deferred).

### Annotated Realien — the CEFR-leveling answer (medium effort, printable, reuses the engine)
**Phase 1 + 2 + 3 BUILT (30 Jun 2026) → [`realien-design.md`](realien-design.md) (D1–D5).** The naive
"select-never-author" framing was the wrong lens; the design doc reframes it. **Two flagship genres**
(FS1, A2): *At the station* + *At the café*, each a real-artifact card with atmospheric "fluff" + a
reasoning task ladder; the **arrangement wrap** (`pipeline/realie_arrange.py`) — speaking as an
interaction anchor (covered only by the anchor, the v0.5 payoff); and the **breadth seam**
(`tools/realien_prompt.py` + `tools/ingest_realien.py`), which produced 6 more verify-clean Realien
across **EN + FR, A1 + A2, six genres** (invitation · zoo · cinema · weather · boulangerie · bus),
SME-gated for the L2 + level. The Realien asset class is **complete** through breadth.
- **The asset:** point the annotated-text engine at **level-appropriate everyday texts** — menus, signs,
  timetables, short messages/emails — exactly what the can-do Lehrplan asks ("kann einfache Alltagstexte
  verstehen"). A1/A2 where native literature is too hard. New `cefr`/`genre`/`scene` tags; the task layer
  is **communicative-first** (write-a-reply + role-play cue; scan/comprehension is warm-up).
- **The reframe — *purpose-appropriate rigor* (the load-bearing idea):** the Realie is the **Sprechanlass,
  not the Aussage** — a pretext that provokes language, not a world-claim. So the fact-discipline DEMOTES:
  the facts are invented-coherent fiction (an internal-consistency lint, not world-grounding), and
  **constructed is the DEFAULT** (no source/rights gate). What stays load-bearing is the **language** (L2
  correctness + level — SME-gated) and internal consistency. *"Invent the timetable, vet the French."*
  Fact-care snaps back only for **informational** genres (news-in-levels, a factual sign). The oral core is
  served via the **Lernarrangement interaction anchor**, not faked on paper. Scales via the Phase-3 seam
  (`realien_prompt.py` + `ingest_realien.py`).

### Supporting (not the headline)
- **Verified language-practice engine** — parametrized vocab/grammar/sentence patterns with checkable
  answers (the Maths-engine analogue). *More* defensible at A1/A2 than for German (controlled practice
  genuinely builds a language), but a supporting feature — leading with drills rebuilds the boring sheet.
- **Communicative arrangements** — role-play / info-gap / simulation for Sprechen, already partly served
  by the Lernarrangement layer (the FS1 class-trip simulation was an early hero).

## Next — agreed, deferred from the GWB figure work (26 Jun 2026)

- **Population-pyramid figure recipe** — ✅ **DONE (27 Jun 2026).** `matplotlib:population_pyramid`
  (back-to-back horizontal age×sex bars) + the `demographic` intent; proven on c0094 with real cited
  Statistik-Austria data. *(c0097 — the other demographics worksheet — can now switch to it too.)*
- **Klimadiagramm figure recipe** — ✅ **DONE (27 Jun 2026).** `matplotlib:climate_diagram` (Walter-
  Lieth: monthly temp line on the left °C axis + precip bars on the right mm axis, via `twinx`), the
  `climate` intent. Unblocks c0096. *(The general dual-axis combo for other subjects can reuse the twinx
  pattern when needed.)*
- **Locality Tier-2 — curated Austrian regional data** — a vetted Bundesländer (then Bezirke)
  dataset (Statistik Austria; provenance-stamped, HITL-gated like the Lehrplan catalog) so
  geography tasks can assert *real* local facts, not only scaffold inquiry. See memory `teachersaid-locality`.

## Subject-driven feature themes (from the 26 Jun 2026 cross-subject scan)

Evidence: the per-subject `task_kind_extensions` in `subject_models.json` are a direct signal of
unmet demand (FS1/FS2 `listening_task` → audio; GPB `source_analysis` → sourced-text; MAT
`construction` → geometric figures; CHE/PHY/BIO `experiment_protocol` → lab scaffolds; etc.).

### A — Audio generation (the modality wall) — *strategic, design-first*
- **What:** generate audio assets (listening texts, dialogues; later musical examples) — a new,
  non-PDF artifact type with a printable transcript fallback.
- **Why:** FS1, FS2, DEU, MUS declare `listening_task`/`speaking_task`/`performance_task`.
  Hörverstehen & pronunciation are *core* competences a printable sheet structurally cannot reach
  — a whole competence **modality** we don't serve (the bigger sibling of locality).
- **Approach:** an `audio:` asset backend parallel to `diffusion:`/`svg:` (pluggable TTS the SME
  wires, like diffusion); script + provenance; a vetting lane (audio analogue of *Abbildungen*);
  transcript is the always-present printable. Scope line holds: we make the material, not the session.
- **Effort:** high — breaks the PDF-only output assumption (new artifact type, player/QA, review).
  Needs a design pass before any build.

### B — Subject figure-recipe families (the Klimadiagramm gap, generalized) — *near-term track*
- **What:** extend the code-gen recipe library subject by subject: **timeline** (GPB),
  **dual-axis combo / Klimadiagramm** + **population pyramid** (GWB, queued), **geometric
  construction** (MAT/GEZ), **chemical structures/equations** (CHE), **circuit/ray** (PHY),
  **labeled diagrams** (BIO), **musical notation** (MUS), **flowchart/pseudocode** (DGB), **map** (GWB).
- **Why:** every subject has 1–2 iconic figures the engine can't yet produce; this is the proven,
  aligned extension of the intent-declared figure system we just stress-tested.
- **Approach:** same `@_generator` registry + intent-declared where data-driven; correct-by-
  construction + `chart_lint` coverage per recipe. Start with **timeline** + the two queued geo
  recipes (shared dual-axis/derived-layout machinery). Chem-structures/notation may need a domain
  lib (RDKit, LilyPond/abjad) → weigh the dependency before adding.
- **Bundle CHE + PHY figures (SME steer, 29 Jun 2026).** The chemistry *content* engine (quantitative +
  qualitative recipes) is done; **chemistry figures are the remaining CHE gap** and pair naturally with
  **physics figures** — both are diagram-heavy science visuals (reaction scheme / energy profile / Bohr
  shells · circuit / ray / vector / free-body) that likely share rendering machinery and a possible domain
  dependency. Plan them as one MINT-figure sub-track rather than piecemeal.
- **Effort:** medium, incremental (one recipe at a time).

### D — Parameterized variant generation — ✅ **DONE (27 Jun 2026, Maths)**
- **Built:** `schema/parametric.py` (`ParametricTask`/`Instance`) + `pipeline/parametrize.py` — a
  `@_recipe` registry where each recipe OWNS sampling + solving via **sympy**, returning the derived
  answer + worked `SolutionStep`s. `make_variants(task, n)` → N correct-by-construction, deterministic
  variants, each with a Rechenweg (the number is computed, never authored). Seed recipes:
  `linear_equation`, `percentage`, `fraction_add`; curated `library/templates.py`; `orch.compose_variants`
  stages a variant worksheet for review. **Inline math** shipped alongside (a `math` RichText run →
  inline mathtext PNG), killing the "fractions as code-symbols" look. See CLAUDE.md "Parametric variants".
- **Chemistry engine — ✅ DONE (29 Jun 2026).** The same engine, a second domain. `grounding/chemistry.py`
  (IUPAC atomic weights + `parse_formula`/`molar_mass`) + `pipeline/chemistry.py` (`balance_equation` via
  sympy nullspace) drive **quantitative** Oberstufe recipes (`molar_mass`, `equation_balance`,
  `stoichiometry`; `che-os-*`, Kl. 7) and **qualitative** Unterstufe recipes (`substance_classification`,
  `separation_method`, `acid_base_neutral`, `reaction_type`, `atom_count`; `che-us-*`, Kl. 4) — all
  correct-by-construction (derived or curated truth, select-never-author). `make_variants` now guarantees
  distinct prompts for small finite pools. `tests/test_chemistry.py`; see CLAUDE.md "Parametric variants".
- **Next:** more recipes (term simplification, proportions, area/volume word problems; chem: concentration
  c=n/V + dilution, percent-composition, ideal gas, limiting reactant), a dashboard "Varianten erzeugen"
  surface, and parametrized *geometry* once the geometry recipe (KB3) exists.

### Also surfaced (lower priority / folded elsewhere)
- **C — sourced-text / source-work** (GPB, DEU, LAT, FS): provided passage + provenance + leveled/
  glossed variants + analysis scaffolds. **→ subsumed by the Grounded-facts layer below.**
- **E — experiment/lab protocols** (PHY/CHE/BIO): a Versuchsprotokoll scaffold + apparatus figures
  (apparatus figures are a B recipe family).
- **F — locality generalizes** (local history, ecosystems, civics): **→ a special case of the
  Grounded-facts layer / Tier-2 regional data below.**

## Big bet — a grounded facts & data layer  *(planned 26 Jun 2026; SME-championed)*

Generalize the grounding discipline from *competences* to *facts and data*: a curated, cited,
provenance-stamped reference layer of real public data, so content states **real facts with
citations** instead of LLM-invented ("schematisch") numbers. Completes "correct by construction"
from *structure* (done: verbatim competences, mechanical figures, no-drift projections) to
*substance*. Subsumes **C** (sourced text), **F** (locality / Tier-2 regional data), and the data
behind **B**'s figures. Citation is itself curriculum (Quellenkritik, Datenkompetenz). This is the
**durable moat**: anyone can wire an LLM to a curriculum; a curated, cited, Austria-correct fact
layer + the vetting loop is an asset that compounds and is hard to copy.

### The load-bearing rule — *select, never author*
Facts live in a deterministic, vetted dataset (fetched + parsed **by tooling**, HITL-approved,
provenance-stamped). Generation **references** a dataset by stable ID — exactly as a task's `serves`
references a competence — and may *use* a datum, never *invent* one. "Research" must mean *a tool
fetches and parses a real source*, NOT *the model reads the web and writes a number* (a fabricated
citation is worse than an invented number — it looks verified). This is the line that keeps the
feature from reintroducing the hallucination risk the whole project removed.

### The invariant it creates (generalizes the media-policy gate)
Every content-bearing claim is exactly one of — and `verify` enforces it (the factual analogue of
`media_policy.check_content`):
- **(a) correct-by-construction** — math / derived (a computed result, the `derive`d Nachweis);
- **(b) vetted-sourced + cited** — references a dataset/source entry; the projection prints the citation;
- **(c) explicitly labelled illustrative** — "Beispiel/schematisch", clearly not a real figure.

A real-looking, uncited, unlabelled number becomes a verify finding.

### Schema sketch (mirrors the Lehrplan-catalog pattern)
- `grounding/data/` — curated **datasets** + **sources**: stable ID, the series/values + units, and a
  `SourceRef` (publisher, title, URL, dataset code, retrieval date, "Stand" date, licence, required
  attribution string). Deterministic ingest where possible — a small fetch+parse tool per source,
  **no LLM in the fact path** (cf. `tools/parse_lehrplan.py`).
- `SourceRef` / `DataRef` on content (cf. `FassungRef`, `Serves`): a figure/task using real data
  carries the dataset ID + the slice it uses; the projection renders the citation.
- A figure's data declares `sourced(ref)` or `illustrative` — the (c) label.

### Sources & licensing (confirmed 26 Jun 2026 — SME research)
Licensing — the #1 risk — is **solved for numbers**:
- **Statistik Austria — OGD portal `data.statistik.gv.at`** (CC BY 4.0, machine-readable, commercial
  OK): canonical primary source (demography incl. population-by-age, labour, education, prices, energy).
  Use the **OGD portal, not the STATcube REST API** (API paywalled; portal free).
- **Eurostat** (free reuse + attribution): harmonised cross-country comparability; cite by the stable
  **online data code** (e.g. "Source: Eurostat (namq_10_gdp)") — a perfect `DataRef` id. APIs return
  JSON-stat / SDMX-CSV (Python `pyjstat`). Caveat: 8-digit CN trade data is excluded from free commercial
  reuse — irrelevant for us.
- **data.gv.at** (CC BY, varies per publisher): federal/state/municipal + geospatial → the **Tier-2
  regional** backbone. Gate the licence per dataset, not per portal.
- **World Bank** (CC BY 4.0) / **Our World in Data** (CC BY): global benchmarking & clean global series
  (e.g. world urbanization for c0081).
- **OeNB / WIFO / IHS**: authoritative monetary/economic data but reuse terms less clear / partly behind
  data services → **cite/reference only, don't redistribute** unless a page-level CC notice allows.

**Refinements this forces:**
- **Licence = a first-class, per-dataset field AND an ingest gate** — only *redistribute* values under a
  recorded redistributable licence (CC BY / equiv.); otherwise reference-only.
- **`SourceRef.attribution`** = the exact citation string the licence requires; the projection renders it verbatim.
- **(b) splits:** (b1) *redistributed + cited* (needs licence) vs (b2) *referenced-only* (Tier-1 inquiry /
  teacher note — needs only attribution). Tier-1 locality is (b2).
- **Verify the licence per dataset at ingest, from the source's own terms** (not a secondary summary) —
  *select-never-author* applied to the licence itself; compliance is legal, not cosmetic.

**Spike convergence:** the **population-pyramid recipe (B)** and the **data-layer spike (phase 2)** both
want Statistik Austria *population by age & sex* — build them together as the first real proof (a real,
cited Bevölkerungspyramide on c0094).

**Scope honesty:** this greenlights the **numbers** phases (3–4). **Text & images (phase 5) remain the
harder, separate licensing question** (most modern text/images aren't freely redistributable → lean on
public-domain / clearly-licensed there).

### Media & text sources (confirmed 26 Jun 2026 — SME research)
The PD / clearly-licensed pool is **richer than the earlier "hard tail" framing — but skewed
historical**, which is exactly what GPB/DEU/LAT/KUG mostly need:
- **Wikimedia Commons** — the default workhorse; per-file rights tag travels with the file (machine-
  readable) → PD art + historical imagery.
- **Europeana** — EU heritage aggregator with *standardized* rights labels (PD Mark / CC0 / CC /
  rights-reserved) → filter to reusable; Austrian + European collections at once.
- **ÖNB (Austrian National Library)** — the deep Austrian well: **ANNO** (19M newspaper pages
  1568–1947, ~all PD), **ABO** (500k+ copyright-free prints 16th–19th c.), **ALEX** (historical legal/
  official texts), **ÖNB Digital** (picture archive — but ALSO a paid agency → per-item rights check).
- **Text:** Projekt Gutenberg-**DE** (projekt-gutenberg.org), Zeno.org, Deutsches Textarchiv, Wikisource,
  ALO (Austrian Literature Online). *Use Gutenberg-DE, not US Gutenberg* (p.m.a. caveat below).
- **Museums** (Albertina etc.) — open-access varies; what's shown online is often pre-cleared, but per-item.

**Two cautions beyond the numbers case (exactly where naive automation errs):**
- **PD work ≠ PD reproduction.** An old painting doesn't make *this scan/photo* free — some EU
  institutions assert rights in reproductions, and ÖNB's picture archive / museums run partly as paid
  agencies. Capture the **per-item rights label** (Wikimedia/Europeana expose it machine-readably); never
  infer "looks old → free".
- **Austrian 70-p.m.a., not US PD.** A title PD in the US (Gutenberg-US) may still be in copyright in
  Austria. Record the author's death year / rights basis and evaluate against the **AT** rule.

**This reframes phase 5** — sourced text/images for **history (GPB Quellenarbeit), German/Latin
literature, art history** are feasible *now* for PD material, at two speeds:
- **(b2) referenced-only — available immediately, no tooling:** point students at ANNO/ALEX/Wikimedia to
  *find & analyse* a source ("find a newspaper from [date] about [event] on ANNO"). Quellenkritik-as-
  competence; the inquiry-frame twin of Tier-1 locality.
- **(b1) redistribute (embed scan/text in the sheet):** needs the per-item rights gate + AT-p.m.a. check
  — the proper phase-5 build. These archives are the rights-clean supply for the existing **media-policy
  "vetted-sourced" class**.

### Phasing (de-risked — cheap proofs before the big build)
1. ✅ **DONE (27 Jun 2026) — the (c) label** *(honesty win):* `pipeline/figure_lint.py` warns when a
   data figure declares neither `data_source` (sourced) nor `illustrative` (schematic).
2. ✅ **DONE (27 Jun 2026) — the one-dataset spike:** `Dataset`/`SourceRef`/`DataRef` defined; proven
   end-to-end on **Statistik Austria population by age & sex (1.1.2024)**, re-grounding **c0094** with a
   real cited Bevölkerungspyramide. *(c0081 urbanization with OWID is the natural next dataset.)*
3. **Demand-driven expansion — numbers first:** curate the open-data series real worksheets need
   (CC-BY: data.gv.at / Statistik Austria, Our World in Data, World Bank, Eurostat). Numbers have the
   cleanest licensing and the highest cross-subject reuse (GWB · MAT-Statistik · PHY-Klima · BIO).
4. **Regional data (Tier-2 locality)** folds in as region-scoped datasets — see memory `teachersaid-locality`.
5. **Sourced text (C) last** — licence-sensitive; lean on public-domain primary sources + clearly-
   licensed material; the analysis scaffolds (who/when/bias, comprehension, translation aids) ride on top.
6. **Refresh cadence:** dated "Stand" stamps + a re-ingest tool, like the Lehrplan Fassung refresh.

### Costs & guardrails (this *is* "a lot of work")
- **Maintenance, not a one-off** — data goes stale; dated stamps + periodic re-ingest.
- **Licensing is the real risk** — redistributable only; numbers clean, text/images thorny (→ phase 5).
- **Bounded / demand-driven** — curate what worksheets ask for, never a speculative encyclopedia.
- **Review load** — each datum is a reviewable item (the HITL feedback loop already absorbs new target kinds).

### Effort & sequencing
High and ongoing, but it can run **in parallel** with the near-term B track: phase 1 (the label) is
independent and small, and the spike (phase 2) naturally pairs with B's geo recipes since both touch
the GWB figures. Recommended order overall: **B-first / data-layer phases 1–2 in parallel**, then A
(design-first) and D as capacity allows.
