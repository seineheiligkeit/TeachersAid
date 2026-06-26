# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository.

## What this is

**TeachersAid** — an on-demand generator of **Austrian-Lehrplan-anchored teaching material** for AHS
secondary schools. A teacher gives a topic + grade + time; the system produces a competence-anchored
bundle that is *correct by construction*, *provably competence-aligned* (the derived **Nachweis**), and
renders to ready-to-use PDFs. Working language of the code/docs is **English**; the product's *output*
is **German** (or a target language for Fremdsprache).

The repository has two layers:

1. **Design docs** (`Documents/`, `project-handoff.md`) — the source of truth for *intent and data model*.
   Read `project-handoff.md` first. Schema **v0.3** is the type source of truth; **v0.4** deltas are
   additive and implemented; **v0.5** (Lernarrangement) is specced but out of scope.
2. **The demo engine** (`teachersaid/`) — a runnable Python implementation of the design: engine
   pipeline + ReportLab rendering + a two-stage human-in-the-loop (HITL) review dashboard.

## Running

```bash
pip install -e .                       # deps: pydantic2, fastapi, uvicorn, anthropic, reportlab,
                                       #       matplotlib, pillow, pyyaml, pymupdf  (pytest for dev)
python -m pytest -q                    # 35 tests, fully offline (no API key required)
python -m teachersaid seed             # seed the master-library examples into the review queue
python -m teachersaid                  # dashboard → http://127.0.0.1:8000
```

(Python 3.11–3.14; the C-extension deps — reportlab/pymupdf/matplotlib — have 3.14 wheels.)

- **LLM generation** uses the Anthropic SDK with `claude-opus-4-8`, adaptive thinking, effort=high
  (see `teachersaid/config.py`). It activates only when `ANTHROPIC_API_KEY` is set.
- **Offline fallback:** without a key, a request for any **master-library** subject/topic
  (`teachersaid/library/`) is served from its curated content object, so the whole loop is demoable
  with no network. `seed` pushes all examples into the dashboard's review queue.
- Generated PDFs, rasters, and the JSON review store land under `runs/` (git-ignored).

## Architecture — the load-bearing idea

The design separates **blocks → content → rendering** as three distinct actions, and the package
**dependency graph enforces it**:

```
schema/      typed data model (v0.3 + v0.4). Imports nothing from llm/ or rendering/.
grounding/   curated Lehrplan facts (YAML) + resolve lookup. Imports only schema/.
pipeline/    resolve → plan → generate → verify → assemble(+derive) → render.  Only place that imports llm/.
rendering/   PURE functions over one WorksheetContent. Imports only schema/.  No HTML→PDF — ReportLab only.
llm/         Anthropic structured-output wrapper (mockable) + prompt builders.
store/ api/  the two-stage HITL review queue + FastAPI dashboard.
demo/        hand-authored hero (Strahlung) + the 3 worked examples.
```

**Why this matters:** because every projection (student / teacher / homework) is a pure function of the
*same* `WorksheetContent`, the answer key cannot drift from the task — the mismatched-teacher-guide bug
is structurally impossible. `rendering/` importing only `schema/` is what guarantees it; **do not let
`rendering/` reach into `pipeline/` or hold its own copy of task data.**

**Retooling rendering?** The renderer is swappable (ReportLab today; HTML→PDF / Typst / docx are fair
game). The hand-off contract — entry-point signatures, the three projection rules, and what's free to
change — is in **`Documents/rendering-handoff-brief.md`**.

### The pipeline (schema §7), and what is deterministic vs LLM

| Step | Module | Nature |
|---|---|---|
| Resolve | `pipeline/resolve.py` | **deterministic** — verbatim competences + `grade_check` (the trust feature) against curated grounding; honest gap notes for anything uncurated |
| Plan | `pipeline/plan.py` | mostly deterministic — envelope→minutes, block-spec skeleton + `DepthTarget` ladder. **The plan IS the idea-stage review artifact.** |
| Generate | `pipeline/generate.py` + `llm/` | **LLM** — `messages.parse()` into a recursion-free generation view, then `to_canonical()` |
| Assets | `pipeline/assets.py` | code-generated (matplotlib), correct-by-construction; `intentionally_flawed` assets are built **wrong on purpose and never "fixed"**. **Pluggable registry (Phase 4):** `Asset(generator, spec)` is a declarative request; builders register against a `<backend>:<recipe>` id (`@_generator`). Parameterized recipes read `spec` (`number_line`, `bar_chart`, `function_graph`, `math_formula` via mathtext); the **`diffusion:` backend** (Phase 4 #4) plugs in the same way: `register_diffusion_backend(fn)` wires the SME's image-gen agent; `build_asset` dispatches `diffusion:*` to it (offline → `DiffusionNotConfigured`, no silent slop). The agent's brief (contract + content-free rule + manifest) is **`Documents/diffusion-handover.md`**. A **decorative kit** (`svg:badge/banner/motif`, content-free, rasterised via PyMuPDF — no extra dep) ships now. **Entry-gate (Phase 4 #3):** `pipeline/media_policy.py` enforces the invariant — *content-bearing visuals must be code-gen or vetted-sourced; decorative must be content-free* — by classifying each asset's role+source against `DEFAULT_MEDIA_POLICY`; runs inside `verify`. **Asset library (Phase 4 #4):** `store/assetstore.py::AssetStore` (parallel to `BlockStore`) holds the **file-backed** classes (decorative + sourced) with tags/status/reuse; `orch.ingest_asset` gates + materialises + stores; `library/decorative.py::seed_assets` seeds the kit. Code-gen content assets stay as specs on blocks. |
| Verify | `pipeline/verify.py` | rules (kinds/dimensions/coverage/depth/difficulty/**media-policy**); LLM fact-check optional |
| Assemble + derive | `pipeline/assemble.py`, `pipeline/derive.py` | **deterministic** — `derive_nachweis` (coverage + auto-surfaced gaps), `compute_depth` (DepthProfile), `printable_coverage` |
| Render | `rendering/*` | **deterministic** pure projections; QA-rastered via PyMuPDF |

## Schema conventions (important)

- **Two model layers, one seam.** `schema/` holds full-fidelity canonical Pydantic models.
  `schema/generation_views.py` holds flattened, recursion-free mirrors the LLM emits, plus
  `to_canonical()` — the single up-conversion point. **All LLM↔storage conversion goes through there.**
- **`RichText`** is `str | list[InlineRun]` canonically; generation views use plain `str` (avoid the
  brittle string|array union). A bare string normalises to one run; single unmarked runs collapse back.
- **`Nachweis` / `DepthProfile` are DERIVED**, never authored by hand or LLM. They are absent from
  generation views and populated only by `pipeline/assemble.py`. **Never let the model produce them.**
- **Open sets** (`TaskKind`, `cognitive_level`) are plain strings validated against the subject model at
  assemble time; the allowed set is injected into the *prompt*, not encoded as a closed JSON enum.
- `kind ∈ core ∪ subject_model.task_kind_extensions`; `dimensions ⊆ subject_model.dimension_ids()`.
- **`Baustein.teacher_overview` is a typed `TeacherOverview`** (throughline · `talking_points` ·
  `extensions` · differentiation · timing_notes) — authored/LLM-generated (NOT derived), teacher-only.
  Generation views mirror throughline/talking_points/extensions; `to_canonical` builds the model.

## Projection audience split (load-bearing)

The three projections are pure functions of one `WorksheetContent`, but **what each shows is split by
audience** (see `Documents/rendering-handoff-brief.md` §2c for the table):

- **Student & homework = student-facing only.** No Fassung stamp, no competence ids, no Nachweis, no
  teacher layer. They keep the **write-in space** (response lines/box/table).
- **Teacher = a guide, not a filled-in clone.** It **omits the write-space** (the topic is known), and
  shows the expected answer + `acceptable_reasoning` + rubric + `watch_outs`, plus the section
  `teacher_overview` "rough guide" (Roter Faden + talking points + extensions) and the appended
  Nachweis/DepthProfile. The Fassung stamp + per-task competence meta are teacher-only.
- **Generation focuses on the student side + answers**; the teacher talking-points/extensions are a
  generated section layer (prompts.py asks for them), seeded by the curated examples.

## Grounding

The engine grounds in the **full competence catalog** at the repo root (`lehrplan/`), produced by a
deterministic RIS-HTML parser (`tools/parse_lehrplan.py`) — **all 16 Unterstufe Pflichtgegenstände,
~571 verbatim competences**. `teachersaid/grounding/lehrplan_store.py` reads it and adapts it to the
engine schema:

- `lehrplan/_meta.json` — Fassung (BGBl. II 204/2024, DokNr NOR40264237, valid 2024-09-01…**2026-08-31**;
  `FassungRef` is stamped on every content object and `resolve` checks the date window) + the ÜT legend
  + subject registry.
- `lehrplan/<CODE>.json` — per-subject verbatim competences (id, kompetenzbereich, klasse, text,
  dimensions, ÜT) + `anwendungsbereiche`. IDs are stable (`PHY.US.4.STR.01`).
- `lehrplan/subject_models.json` — per-subject `SubjectCompetenceModel` (dimensions + modality +
  content_areas + task_kind_extensions).

`lehrplan_store.py` maps subject **name → catalog code** (alias table + the registry), resolves a
DimensionRef per competence (inline W/E/S; or the kompetenzbereich where it *is* the dimension; or a
`(T)`/`(H1)` tag in the text), and treats `klasse: null` as a cross-class competence. The RIS source
HTML/PDF are git-ignored; the parser regenerates the catalog (re-run for the 2026/27 Fassung).

**To add/correct a subject:** edit the catalog (re-run the parser, or edit `lehrplan/*.json` /
`subject_models.json`) — no engine code change. *(The earlier Physik-only `grounding/data/*.yaml` stub
has been removed now that the store reads the full catalog.)*

## Master library (`teachersaid/library/`)

Curated, gold-standard **`WorksheetContent` examples** — the quality bar, the few-shot seeds for LLM
generation, and the offline demo/review stock. `library/__init__.py` holds a `registry` (`EXAMPLES` +
`find()` + `seed_library()`); each `library/<subject>_<topic>.py` is a `build_content()` grounded in
`lehrplan/` (real competence IDs, dimensions ⊆ subject model, verify-clean). The MINT seed:
Physik *Strahlung*, Biologie *Immunsystem*, Mathematik *Daten/Zufall*.

- `_generate_content` (orchestrator) serves a registered example when there's **no API key**, so the
  normal dashboard flow demos offline; with a key it generates fresh content seeded by the example.
- `python -m teachersaid seed` runs every example through the pipeline into the store as a **pending
  content item** (→ dashboard review queue). `tests/test_library.py` locks every example
  build/assemble/**verify-clean** against catalog drift — keep it green when editing the catalog.
- The quality bar + per-subject coverage plan: **`Documents/master-library-plan.md`**. Don't author
  shallow examples; match the depth of `demo/strahlung.py`.

## Block library — the unit of the master library (`teachersaid/library/block.py`)

Per **`Documents/block-library-design.md`**, the **block** (not the whole worksheet) is the durable
library unit; a worksheet will become a *composition* of blocks (the composer is a later phase).
Phase 1 (built):
- `LibraryBlock` (`library/block.py`) = a schema `Block` + library metadata: subject/Klasse/
  Kompetenzbereich, `serves` competences, `cognitive_level`, `dimensions`, `modality`, **`scope`**
  (content richness compact|standard|extended — *orthogonal to* `cognitive_level`), `family` (groups
  richness variants), `status`, `provenance`. `harvest(content)` extracts a worksheet's blocks into
  LibraryBlocks (a learn-from text is a block too; only the worksheet's framing intro/transitions are not).
- `store/blockstore.py::BlockStore` — JSON under `runs/blocks/`; `upsert` is idempotent and **preserves
  review status** (re-seeding never un-approves). `python -m teachersaid seed` harvests the example
  worksheets' blocks (~21) as the seed; `library.seed_blocks()`.
- Dashboard **Bausteine** tab reviews blocks (approve → library; **"Alle in Prüfung freigeben"** =
  `POST /api/blocks/approve-all`). The curated seed blocks come from the SME-reviewed examples, so
  `seed_blocks` seeds them **`approved`** (idempotent `upsert` preserves status). **Statistik**
  (`teachersaid/stats.py`) is the **block matrix**: per subject — task/info blocks, catalog competences
  covered (≥1 approved task block), cognitive-level spread, what's empty.

## Composition — worksheet from blocks (Phase 2, dumb v1)

`pipeline/compose.py::compose(subject, klasse, topic, envelope, *, kompetenzbereich=None, block_store)`
builds a worksheet from **approved** library blocks: select blocks serving the target competences
(printable), order by cognitive level, one per `family`, prefer the `scope` matching the envelope,
**greedy time-fit** to the envelope budget, pull ≤2 readable info blocks, and add a *template* framing
(Kernfrage + intro — no LLM). Result is a `WorksheetContent` → the existing `assemble`/`verify`/`render`.

**Targeting (Phase 2.1):** competences come either from an explicit **`kompetenzbereich`**
(`resolve_kompetenzbereich` — deterministic, the robust path: a worksheet *title* needn't textually echo
the catalog's KB name) or, when none is given, from matching the free-text `topic` (`resolve` — works
when the title echoes a KB name like Physik *Strahlung* or an Anwendungsbereich like Biologie
*Immunsystem*; **fails** for catchy titles like Mathematik *"Das unfaire Spiel"* vs the KB *"4: Daten und
Zufall"* — that's why the KB path exists). `topic` is always the display title.

`orch.compose_worksheet` lands it as a content item (`source="compose"`); dashboard **Inhalte** has an
"Arbeitsblatt zusammenstellen" form with a **Kompetenzbereich** picker (`GET /api/kompetenzbereiche`);
`POST /api/compose` (accepts `topic` and/or `kompetenzbereich`). **No optimizer, no difficulty
calibration yet** (Phase 3d). A composed sheet is a `WorksheetContent`, so rendering is unchanged.

**Phase 3 progress** (see `Documents/block-library-design.md §8`): **3a** (scope/richness variants) and
**3c** (assets travel with blocks) are built. *3a:* `compact`/`standard`/`extended` siblings share a
`family`; the composer picks the variant matching the envelope (einzelstunde→compact … block→extended),
so envelopes differ in depth. Produce variants via `orch.ingest_scope_variant` + `tools/scope_variants.py`.
*3c:* `LibraryBlock` carries its `Asset` spec(s); `harvest` captures them; `compose` aggregates the chosen
blocks' assets so figures (e.g. the Strahlung spectrum) now render in composed sheets.

## Lernarrangement (schema v0.5 — Phase 5, in progress)

A **`Lernarrangement`** (`schema/arrangement.py`) is a composite sibling that *contains* worksheets
(**has-a**): each `ArrangementRole.material` IS a `WorksheetContent`, so the worksheet stays the
primitive and a plain worksheet is the n=1 case. Beyond stapled sheets, `competence_anchors` capture the
**oral/social/enactive** competences a printable sheet can't reach — served by the `interaction`, the
`debrief`, or the `shared_product` (not by any task). `nachweis`/`depth_profile` are **DERIVED**
(`pipeline/arrange.py`): `assemble_arrangement` assembles each role's material, then the arrangement
Nachweis = ⋃ role exercised competences **+ the anchors** (a competence covered *only* by an anchor is the
v0.5 payoff); `verify_arrangement` verifies every role as a worksheet + arrangement rules (groupings,
anchor served_by/competence). **Rendering reuses the worksheet path entirely (no second renderer):**
`render_teacher_orchestration` (`rendering/arrangement.py`, PURE over schema — the run-guide: case,
phase timeline, roles, shared product + rubric, debrief, the anchor table, derived Nachweis) + each role
via `render_student_sheet`/`render_teacher_guide`. The asset-building bundle `render_arrangement`
(`pipeline/arrange.py`) = orchestration + per-role student handout + teacher copy — it lives in the
pipeline (not `rendering/`) because it builds asset images; the renderers stay pure. **Scope line:** we
make the material bundle + a teacher run-guide; we do **not** run the room.
**Hero:** `demo/gwb_standort.py` — a GWB grade-3 Gemeinderat-Planspiel (4 roles; ENT.03/06/07+ZEN.03 on
the sheets; ENT.05 via the debate, ENT.01 via the council decision as anchors). **Phase 5a–5c done:**
schema + derive/assemble/verify + the hero + the run-guide renderer + the dashboard review surface
(`store/arrangementstore.py`, `orch.stage_arrangement`/`seed_arrangements`, the **Arrangements** tab,
`/api/arrangements*`), verify-clean & rasterised (`tests/test_arrangement.py`). **Next:** 5d generation
(subagent → `stage_arrangement`, like worksheets).

## Breadth generation — subagents → ingest (the seam, no API key)

Scaling the library across subjects uses **subagents as the generator** (no `ANTHROPIC_API_KEY` needed —
they run via Claude Code). Each emits a `GenWorksheetBody` JSON anchored to **real** catalog competences;
it is validated through the real generation seam and staged for HITL review.

- `tools/breadth_prompt.py` writes a fully-grounded per-subject brief (`runs/ingest/prompt_<CODE>.md`):
  verbatim competences grouped by KB across grades, allowed dims/kinds, the JSON shape + worked example,
  and an instruction to produce N **distinct Kernfragen** (one worksheet each). Per-subject config in
  `SUBJECTS` (anchor kb|grade; `practical` → enactive/oral modality; `target_language` for FS1/FS2/LAT,
  which adds a clause: target-language *material*, German instructions + German teacher layer). Subagents
  (one per subject, Sonnet) write `runs/ingest/<gendir>/<CODE>_<n>.json`.
- `tools/ingest_batch.py --dir <folder>` validates (`--dry-run`: resolve → to_canonical → assemble →
  verify) or persists. **Its first-pass normalizer is load-bearing** — hand-written JSON is the real
  fragility, so it deterministically absorbs the recurring agent slips rather than re-spawning: `„…"`
  typographic-open/straight-close (a `(?<!\\)`-guarded text repair), literal control chars
  (`json.loads(strict=False)`), info-blocks shaped like tasks, invalid info `kind` (→ prose),
  `answer_text`→`answer_key`, German rubric keys, `{label,description}` levels, off-enum
  `serves.relation`, and nested multi-question `multiple_choice` (folded into the prompt).
- `orch.ingest_generated(..., render=False)` is the backbone: `body_to_canonical → assemble → verify`
  (+ render only if asked — **breadth is render-free**; blocks are inspected structurally), stage a
  pending content item (`source="generated"`) + harvest blocks (`in_review`) — **only if verify-clean**
  (an invented competence id / kind / dimension surfaces as an error here, never a silent bad block).
  Anchors via `resolve_kompetenzbereich` (content-KB subjects) or `resolve_grade` (strand-KB subjects);
  a too-narrow KB auto-widens to the grade when serves cross strands (Sport/Musik). `GenTaskBlock` carries
  `rubric` so generated worksheets author teacher rubrics.
- **Run to date (25 Jun 2026):** all 16 subjects → **64 worksheets / ~404 blocks**, verify-clean, staged
  `in_review` for SME approval. Feasibility lesson: subagent *content* is excellent; the constraint is
  JSON well-formedness, handled by the normalizer (structured output would remove that class at scale).

## HITL dashboard (`api/` + `api/static/index.html`)

Two review gates, one `ReviewItem` type (`stage` ∈ **brainstorm** | **content**); seven tabs
(Brainstorm · **Bausteine** · Inhalte · Bibliothek · **Arrangements** · **Abbildungen** · Statistik — see
the Block library section below). **Abbildungen** is the asset-review surface (Phase 4 #2/#4): file-backed
library assets (decorative/sourced, with approve/reject) on top, and below, every code-generated content
figure rendered inline (deduped by generator+spec, built on demand) for fächerübergreifende review.
**Arrangements** (Phase 5c) reviews Lernarrangements (`ArrangementStore`): the run-guide + each role's
student/teacher PDF (Vorschau) and a structural view (phases · roles · shared product · anchors · Nachweis),
approve/reject. (Arrangements use their own store, not `ReviewItem`.)

```
Brainstorm (rough idea: topic + note, you or AI) ─approve─► flesh_out
   (resolve→plan→generate→verify→assemble→render) ─► Content [Gate 2: Blöcke + Vorschau]
   ─approve─► Bibliothek (material library)
```

- **Brainstorm** — rough ideas. `orch.submit_brainstorm` (you) or `orch.suggest_from_catalog` (one per
  not-yet-covered Kompetenzbereich; `source="ai"`). Approve → `orch.flesh_out` develops it into a content item.
- **Inhalte** — fleshed-out worksheets shown two ways: **Blöcke** (the structured `WorksheetContent` —
  blocks, dimensions, `serves`, derived Nachweis/Tiefenprofil — *independent of any rendered document*)
  and **Vorschau** (the rendered student/teacher/homework PDFs). Approve → library; `request-changes`
  regenerates with the note injected.
- **Bibliothek** — approved worksheets. **Bausteine** + **Statistik** are the block library (see below);
  Statistik is the block-coverage matrix.

Offline, `flesh_out` is served from the master library; with a key it generates live. The store holds
only review items + the approved library — deliberately **no gradebook, no classroom state, no student
PII** (we make the material, we don't run the room).

## Testing

`tests/` mirrors the milestones; everything runs offline (LLM is mocked via an injected generator).
Key invariants under test: schema round-trip; deterministic resolution + honest gaps; the Strahlung
DepthProfile reproduces schema §8 exactly (W2/S4/E1, 78/56 min) and STR.01 surfaces as a gap; all three
projections render + rasterise; student hides keys / teacher shows them; the `intentionally_flawed`
guard; the full two-stage HITL loop + API; the three worked examples exercise the v0.4 deltas.

Run a single file: `python -m pytest tests/test_derive.py -q`.

## Conventions & gotchas

- **`Baustein` lives in `schema/worksheet.py`**, not `schema/blocks.py` (easy import slip).
- In rendering, use `rb.para(value, style)` for RichText (escapes); use `rb.raw_para(markup, style)` when
  you've **already built** inline markup (don't double-escape — that prints literal `<b>` tags).
- Carlito font is used if installed; otherwise Helvetica fallback (the demo renders anywhere).
- PDF→PNG QA uses **PyMuPDF** (`fitz`), not `pdftoppm` (no system poppler dependency).
- Match the surrounding German tone/terminology in product-facing strings; the user is the domain SME
  (physicist, Austrian) and fact-checks the physics and the German.
- Don't relitigate decisions recorded in `project-handoff.md §4`; they are durable.

## Where to look first

`project-handoff.md` (intent) → `Documents/lehrplan-bundle-schema-v0.3.md` (data model) →
`teachersaid/schema/` (the model in code) → `teachersaid/pipeline/` (the engine) →
`teachersaid/demo/strahlung.py` (a complete worked content object).
