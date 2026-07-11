# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository. **This file is the operating
manual**: invariants, architecture, seams, rules, gotchas — with pointers to depth. Project *history*
lives in `project-handoff.md` (dated session blocks); design *depth* lives in `Documents/` (map:
`Documents/README.md`); the *plan* lives in `Documents/feature-roadmap.md`. Keep it that way — see
"Updating this file" at the end.

## What this is

**TeachersAid** — a **corpus-first generator of Austrian-Lehrplan-anchored teaching material** for AHS
secondary schools. A teacher gives a topic + grade + time; the system **assembles** a competence-anchored
bundle **from a curated, SME-gated corpus** — *correct by construction*, *provably competence-aligned*
(the derived **Nachweis**) — and renders it to ready-to-use PDFs. **Offline-first** (the Session-11
pivot — `project-handoff.md` §4, `Documents/invariants.md` §10): the LLM lives only in the **corpus
loop** (campaign generation → lints → SME gate); the **delivery loop is deterministic and LLM-free**
(serve a vetted sheet › compose from approved blocks › honest gap → demand queue; parametric/scene
instantiation is the LLM-free "live" generation). Working language of code/docs is **English**; the
product's *output* is **German** (or the target language for Fremdsprache).

**The working frame is build-for-joy:** a hobby built for intrinsic excellence — no pilots, no
releases, no GTM pressure, no teacher-feedback loops; **do not push them.** Prioritise on the intrinsic
axis: new correct-by-construction domains · deeper engines · corpus-level structure · craft.

Two layers: **design docs** (`Documents/` + `project-handoff.md` — the source of truth for intent and
data model; schema **v0.3** is the type source of truth, **v0.4** deltas are additive and implemented,
**v0.5** Lernarrangement is built) and **the engine** (`teachersaid/` — the pipeline + ReportLab
rendering + the two-stage human-in-the-loop review dashboard).

## Running

```bash
pip install -e .                       # deps: pydantic2, fastapi, uvicorn, anthropic, reportlab,
                                       #       matplotlib, pillow, pyyaml, pymupdf, sympy  (pytest for dev)
python -m pytest -q                    # fully offline, no API key (783 tests)
python -m teachersaid seed             # seed the master-library examples into the review queue
python -m teachersaid                  # dashboard → http://127.0.0.1:8000
```

Python 3.11–3.14 (the C-extension deps have 3.14 wheels). **LLM generation** (Anthropic SDK,
`claude-opus-4-8`, adaptive thinking, effort=high — `teachersaid/config.py`) activates only when
`ANTHROPIC_API_KEY` is set, and it is the **corpus-loop / campaign seam**, never a product surface.
Without a key, any master-library subject/topic is served from its curated content object — the whole
loop demos offline. Generated content lands under `runs/`.

**Persistence policy (`.gitignore`):** git owns the *content + review state* (`runs/**/*.json|.md|.txt`
— small, diffable, NOT regenerable for subagent-authored work), and ignores the rendered *binaries*
(PDFs, QA-raster PNGs, sourced/audio assets — large, rebuildable from tracked content). Artifact paths
in store JSON are absolute; renders rebuild on first dashboard load (self-healing), never relied on
from git. Drive can carry the binaries; git carries the text.

## Invariants (and their boundaries) — read `Documents/invariants.md`

The project's load-bearing rules — and crucially *what each does NOT forbid* — live in
**`Documents/invariants.md`**. Read it before you let a remembered rule block a good idea; several rules
are stated in their *strong proxy* form and the boundary matters. The one most often mis-applied:

> **"Select, never author" applies to FACTS, not to EXPRESSION.** The LLM never originates a load-bearing
> *fact* (numbers, dates, names, quotes, competences — these are selected/computed/curated). It **may**
> author *expression* — prose, narrative, framing, task wording — *as a projection over a frozen, given
> fact-set* (the same shape as rendering). Correct-by-construction has **four** mechanisms: computed ·
> selected · curated · **re-expressed-under-constraint** (authored prose over sourced facts + a
> deterministic entity-lint). So "never author" ≠ "no prose". See `invariants.md` §3.

Durable decisions are recorded in `project-handoff.md` **§4** — do not relitigate them.

## Architecture — the load-bearing idea

**Blocks → content → rendering** are three distinct actions, and the package dependency graph
enforces it:

```
schema/      typed data model (v0.3 + v0.4). Imports nothing from llm/ or rendering/.
grounding/   curated catalogs (Lehrplan, data, geo, chemistry, operators, voices) + resolvers. Imports only schema/.
pipeline/    resolve → plan → generate → verify → assemble(+derive) → render.  Only place that imports llm/.
rendering/   PURE functions over one WorksheetContent. Imports only schema/.  No HTML→PDF — ReportLab only.
llm/         Anthropic structured-output wrapper (mockable) + prompt builders.
store/ api/  the two-stage HITL review queue + FastAPI dashboard.
demo/        hand-authored hero (Strahlung) + the worked examples.
```

**Why this matters:** every projection (student / teacher / homework) is a pure function of the *same*
`WorksheetContent`, so the answer key cannot drift from the task — the mismatched-teacher-guide bug is
structurally impossible. `rendering/` importing only `schema/` is what guarantees it; **do not let
`rendering/` reach into `pipeline/` or hold its own copy of task data.**

**Retooling rendering?** The renderer is swappable (ReportLab today). The hand-off contract —
entry-point signatures, the three projection rules, what's free to change — is
**`Documents/rendering-handoff-brief.md`**.

### The pipeline (schema §7) — deterministic vs LLM

| Step | Module | Nature |
|---|---|---|
| Resolve | `pipeline/resolve.py` | **deterministic** — verbatim competences + `grade_check` (the trust feature) against curated grounding; honest gap notes for anything uncurated |
| Plan | `pipeline/plan.py` | mostly deterministic — envelope→minutes, block-spec skeleton + `DepthTarget` ladder. **The plan IS the idea-stage review artifact.** |
| Generate | `pipeline/generate.py` + `llm/` | **LLM (corpus loop only — never in the delivery path; invariants §10)** — `messages.parse()` into a recursion-free generation view, then `to_canonical()` |
| Assets | `pipeline/assets.py` | code-generated, correct-by-construction → see **Figures & assets** below |
| Verify | `pipeline/verify.py` | rules: kinds/dimensions/coverage/depth/difficulty + the lint battery (media-policy · chart-sanity · (c)-data-label · numeric-claims · prose-provenance · **readability**/`readability.py`, advisory — Wiener Sachtextformel, warns ≫ target Schulstufe; verbatim `quoted`/`source_text` exempt · **difficulty-model**/`difficulty_model.py`, advisory — computed band vs. operative difficulty, ≥1-band gap warns); LLM fact-check optional |
| Assemble + derive | `pipeline/assemble.py`, `derive.py` | **deterministic** — `derive_nachweis` (coverage + auto-surfaced gaps), `compute_depth` (DepthProfile), `printable_coverage`; `data_ground.ground_data` derives each figure's values FROM its `data_source` dataset slice + stamps the citation onto the content (rendering stays pure; select-never-author for numbers) |
| Render | `rendering/*` | **deterministic** pure projections; QA-rastered via PyMuPDF |

The lints in `verify` (details in their sections/docs): `media_policy` (content-bearing → code-gen or
vetted-sourced; decorative → content-free), `chart_lint` (misrepresentation: 0/1 data as bars, extreme
ranges, numeric/temporal x forced into bars), `figure_lint` (the (c)-label: every data figure is exactly
one of `data_source` | `illustrative`; pure-math exempt), `number_lint` (a prose number next to a SOURCED
figure must be derivable from the cited series — values · contiguous-range sums · cross-series sums/
same-range diffs · means/medians · shares & ratios in %, precision-matched, German number formats; bare
numbers <120 and years skipped; **advisory lane** — doubles as the anti-rot check on dataset refresh),
`prose_lint` (expression provenance, see the History class).

## Figures & assets

- **Pluggable registry:** `Asset(generator, spec)` is a declarative request; builders register against a
  `<backend>:<recipe>` id (`@_generator` in `pipeline/assets.py`); parameterized recipes read `spec`.
  `intentionally_flawed` assets are built **wrong on purpose and never "fixed"**. A **decorative kit**
  (`svg:badge/banner/motif`, content-free, rasterised via PyMuPDF — no extra dep) ships. The
  **`diffusion:` backend seam** exists: `register_diffusion_backend(fn)`; `build_asset` dispatches
  `diffusion:*`; offline → `DiffusionNotConfigured`, no silent slop. Batch-agent brief:
  `Documents/diffusion-handover.md`; the **illustration program** (accepted, not built: image = claim +
  rendering, a third `depictive` media-policy lane, local Flux backend, the Beschriftungs-hybrid):
  **`Documents/illustration-design.md`**.
- **Asset library:** `store/assetstore.py::AssetStore` holds the **file-backed** classes (decorative +
  sourced) with tags/status/reuse; `orch.ingest_asset` gates + materialises + stores;
  `library/decorative.py::seed_assets`. Code-gen content assets stay as **specs on blocks** (rebuildable).
- **Legibility + representation (load-bearing):** *correct numbers are necessary but NOT sufficient —
  the chart TYPE, scale, and labels must make the data legible and honest.* Recipes self-correct layout
  (auto-horizontal bars, a value label on every bar, optional log scale, wrapped titles); `chart_lint`
  flags misrepresentations. **Formatting rules:** figures never use scientific notation — unit-scaled
  axis labels ("in Mio."), German number formatting (`figstyle.unit_scale`/`fmt_de`), years on a
  numeric x-axis.
- **Intent-declared figures (not "everything is a bar"):** the generator declares WHAT the data is —
  `GenDataFigure(intent ∈ trend·comparison·relationship·composition·distribution·spread·scale·
  demographic·timeline·climate, data)` — and the **deterministic** `schema/chart_choose.py::
  choose_representation` maps intent → recipe. The LLM declares intent; code guarantees a legible
  representation. The full intent↔recipe table + recipe vocabulary (`GENERATION_RECIPES`: the data
  recipes, the geometry family, `tree_diagram`, the scene recipes) is in
  **`Documents/figure-styleguide.md`**. Labels are spec-provided so a figure never leaks the answer
  ("c = ?"). `body.data_figures` (intent) is preferred for data; `body.assets` (explicit generator) is
  for structural/geometry figures.
- **`pipeline/figstyle.py` — the styleguide.** One source of truth: **semantic colour ROLES** (`focus`
  is *always* the unknown/result/region of interest), a categorical ramp + a **dash ramp**
  (`line_kind` pairs hue+dash per family — *redundant*, so a dense figure survives a **B/W photocopy**),
  a type scale, and the document font (Carlito/Calibri, same discovery as `reportlab_base`, so figures
  stop reading as "pasted in"). `house_rc()` **scopes** the style (each `assets.py` recipe wraps its
  build in `rc_context(house_rc())`); the A1 port is **done** — **no hard-coded hexes remain in
  `assets.py`** (`tests/test_figstyle_port.py` regex-locks it). **The Windows-Calibri font fix is two-layered
  (unified 10 Jul from both machines' independent fixes):** Calibri ships EBDT/EBLC embedded-bitmap
  strikes; FreeType selects them at exactly their ppem sizes (e.g. 9 pt @ 150 dpi) and Agg draws EMPTY
  outlines while the text still *measures*. `_register_font` **strips the strike tables** at
  registration (fontTools; the strike-carrying originals are purged from the font manager — the
  root-cause fix, so Calibri keeps matching the worksheet body) AND **render-probes** each candidate
  (`_renders_small`: 9 pt probe text must lay down real ink; falls through Carlito → Calibri → DejaVu)
  as the measured safety net. Locked by `tests/test_layout.py::test_house_font_renders_glyphs_at_every_size`.
- **`pipeline/scene.py` — the scene engine.** A figure as data: `Scene` = `Canvas` + ordered typed
  layers (`Polyline·Line·PointMark·CircleShape·Arc·Region·Label`); one `render_scene` draws it in house
  style; the SAME scene renders at different **stages/densities**. **Two-tier, like
  `choose_representation`: the LLM never authors a Scene** (it could draw a wrong tangent or leak an
  answer) — a **didactic recipe COMPUTES it** from a small correct-by-construction spec:
  `pipeline/constructions.py` (`triangle_construction` — the merkwürdigen Punkte, all computed from 3
  vertices, `stage` 1–6), `pipeline/calculus.py` (the sympy analysis family:
  `function_plot·integral_area·tangent·riemann_sum·extrema·area_between·distribution`), and the
  **physics families** `pipeline/optics.py` (thin-lens ray construction — drei Hauptstrahlen as stages;
  givens shown, image `b`/`B` maskable) + `pipeline/circuits.py` (series/parallel netlist → Kirchhoff
  solve via sympy → DIN schematic; per-element `mask=[…]`). Value labels **mask** (`show_value=False` →
  "A = ?") so one scene serves the student task and the teacher solution. `tests/test_{scene,calculus,
  optics,circuits}.py` lock defining properties; visual reference: `tools/*_specimen.py`.
- **3D (`pipeline/scene3d.py` — promoted, roadmap A7):** model in ℝ³, project via a fixed axonometric map
  into ordinary 2D scene primitives — renderer + figstyle reused, print-first. Recipes
  `matplotlib:axonometric_solid` (Schrägriss of Quader/Prisma/Pyramide/Zylinder/Kegel; hidden edges
  dashed) + `matplotlib:riss_pair` (Grund-/Aufriss). **Hidden-line occlusion is closed-form for CONVEX
  bodies** (an edge is hidden iff both adjacent faces back-face; `classify_edges` raises `NotConvex`
  otherwise — the design-doc boundary, enforced); riss visibility is computed **per Riss** with the
  **coincidence rule** (visible wins on coinciding projected segments); a smooth base rim splits
  front-solid/back-dashed. `tools/plane3d_specimen.py` keeps the plane/conic prototype (un-promoted).
  Design: `Documents/scene3d-geometry-design.md`.
- **Scene additions (10 Jul 2026):** two more primitives — **`Arrow`** (filled head; physics vector AND
  node-link edge in one type: `family` ramp hue, midpoint `label`+offset, `curve` arc3 bend,
  `shrink_a/b`) and **`Node`** (rounded-box label; `edge_role=None` → a white p-chip). **Every layer
  takes a `group` tag; `Scene.select(*groups)` is the first-class density/stage selector** (untagged
  always kept, order preserved) — `constructions.py`'s stage 1–6 selects from one grouped scene,
  identical output. **`pipeline/nodelink.py`** composes `tree_diagram·cause_effect·process_flow` (the
  assets.py builders are thin wrappers, frozen ids + specs); **`pipeline/physics_scenes.py`**
  (`vector_addition`/`force_diagram` — resultants computed + maskable; a masked/zero resultant renders
  as a label with NO arrow so a ruler can't leak the magnitude; angles CCW from +x; Unterstufe
  simplification: forces from the body's centre) and **`pipeline/labeled_diagram.py`**
  (`labeled_parts` — "Beschrifte die Teile", numbered-student/named-teacher projections from ONE scene;
  volcano flagship). Tests: `test_{nodelink,physics_scenes,labeled_diagram}.py`.
- **Körpernetze (`pipeline/nets.py`):** `cuboid_net` computes a six-face Quader/Würfel net with
  explicit dimensions and exactly five fold adjacencies; `matplotlib:solid_net` is only its scene
  projection (`Region·Line·Label`). Labels are spec-provided and maskable (`"O = ?"`). The
  `quader_oberflaeche` parametric recipe derives `O = 2(ab+ac+bc)` from the same dimensions and emits
  the net per variant; template `mat-quader-oberflaeche` honestly anchors `MAT.US.1.FIG.03`.

## Grounding catalogs — one discipline, many catalogs

**The pattern (everywhere):** a **deterministic, LLM-free tool** fetches + parses a real source → a
curated in-repo **catalog** (stable ids + licence/`SourceRef`) → a **resolver** with honest gap notes →
HITL-reviewable items. **No LLM in the fact path** — a fabricated citation is worse than an invented
number. Adding a source = adding a fetch tool; correcting content = editing the catalog, no engine change.

- **Lehrplan Unterstufe** (`lehrplan/`, from `tools/parse_lehrplan.py` over RIS HTML): all 16
  Pflichtgegenstände, ~571 verbatim competences. `_meta.json` carries the Fassung (BGBl. II 204/2024,
  DokNr NOR40264237, valid 2024-09-01…**2026-08-31**; `FassungRef` is stamped on every content object
  and `resolve` checks the date window), the ÜT legend,
  the subject registry; `<CODE>.json` per-subject competences (stable ids like `PHY.US.4.STR.01`;
  `klasse: null` = cross-class) + `anwendungsbereiche`; `subject_models.json` per-subject dimensions/
  modality/content_areas/`task_kind_extensions`. `grounding/lehrplan_store.py` maps subject name →
  catalog code (alias table + registry) and resolves a DimensionRef per competence (inline W/E/S, the
  KB-is-the-dimension case, or a `(T)`/`(H1)` tag). RIS source files are git-ignored; the parser
  regenerates (2026/27 Fassung re-run: **deferred by decision until published in full text**).
- **Lehrplan Oberstufe** (`lehrplan/oberstufe/`, from `tools/parse_lehrplan_oberstufe.py` — the
  Oberstufe is semesterised into Kompetenzmodule): 18 subjects, ~1360 competences, each with `kind` ∈
  `descriptor` (grade-independent Kompetenzmodell, id `<C>.OS.x.<KB>.nn`) | `lehrstoff` (carries
  klasse+semester+kompetenzmodul). `tools/build_oberstufe_meta.py` → the curated judgment layer
  (mirrors the Lehrplan's own dimensions per SME decision — **Chemie uses WO/EG/KZ, not W/E/S**).
  The store + resolver are **stage-aware**: functions take `stufe`; **`stufe_for_klasse(klasse)` is the
  authority** (1–4 → US, 5–8 → OS); `ResolvedCompetence` carries `semester`/`kompetenzmodul`/`kind`
  (None for US); `resolve_grade(..., kompetenzmodul=, semester=)` + `resolve_kompetenzmodul` narrow to
  one module while keeping cross-cutting descriptors. The Unterstufe path is unchanged.
- **SRDP Operatoren** (`grounding/operators.py`): the Matura's standardized task verbs as a controlled
  vocabulary injected into the generation brief (`llm/prompts.build_system`) — *select, never author*.
  Four authoritative CC-BY catalogs, each in its true shape: Deutsch + GWB (AFB-banded + definitions),
  Naturwissenschaften (BIO/PHY/CHE share one base; AFB **and** W/E/S), Mathematik/AMT (flat, +
  Antwortformat→`kind` map: `mc→multiple_choice · z→matching · k→construction · l→table_fill ·
  o/ho→open_response`). `_RANK_TO_AFB` is kept identical to `difficulty._RANK_TO_BAND` (one ladder, two
  surfaces; test-locked). **Routing is by canonical code** (`_code_for`), not display name. Uncurated
  subjects get a flagged generic palette. **Latein curated (10 Jul 2026):** an **empirical 15-operator
  catalog** (`LATEIN` — ÜT `übersetzen` + 14 IT operators harvested from the Klausur corpus; definitions
  authored-then-vetted, provenance recorded as empirical) routed `LAT → LATEIN` for BOTH Stufen. Still
  to curate: FS/GZ/Ethik. The
  cognitive_level→AFB→difficulty model is calibrated against the real exam archive and holds
  (`Documents/matura-calibration.md`; decision rule + write-up: `Documents/matura-operators.md`).
- **The Matura archive tools** (deterministic, no-LLM; corpus in `runs/matura/`, git-ignored):
  `tools/fetch_matura.py` (the full public SRDP archive; `--list` dry-run · `--all` crawl ·
  `--standard-only` skips translation/accessibility editions · `--extract` chains the extractor;
  per-collection `cHash` links are scraped, never fabricated; idempotent manifest with CC-BY
  attribution; re-mirror anytime — but matura.gv.at/aufgabenpool.at are blocked by the remote-session
  egress proxy (aufgabenpool's 403 is only User-Agent gating), so run it from a home network),
  `tools/extract_matura.py` (subject-aware
  parser — the filename's language slot is a CEFR code, not `[A-Z]{2}`; Deutsch operators mapped by
  *earliest match* = the imperative head), `tools/matura_demand.py` (per-subject demand maps → the
  `Documents/matura-*-coverage.md` write-ups). The sciences/GWB have **no** Klausur archive
  (oral/teilstandardisiert) — confirmed, no parser. **Matura-backward design** (mine SRDP endpoints into
  material for earlier grades) is a live corpus-strategy thread. **First Matura-backward deliverables
  shipped (10 Jul 2026):** the Maths WS/FA parametric pack (`exponential_model·boxplot_from_data·
  probability_tree`, templates MAT.OS.6.REE.10/BES.01/BES.04); the **Deutsch Textsorten scaffold**
  (`grounding/textsorten.py` extended with struktur/typical_operators/sprachregister +
  `pipeline/textsorte_scaffold.py::build_worksheet` — teach-the-Textsorte sheets for Zusammenfassung/
  Kommentar/Interpretation, anchored DEU.US.3/4.SCH; the capstone's **rubric is DERIVED** from the
  curated Schreibhandlungen+Struktur+Wortanzahl, never authored; `seed_textsorten()` stages them); and
  the **Latein Wortbildung engine** (`grounding/latin.py` — 12 prefixes × 9 bases → 39 attested
  derivations, no synthesized Latin ever; `pipeline/latin.py` recipes in the shared registry;
  `lat-us-*` templates).
- **Grounded facts & data** (`grounding/data/`, `schema/datasets.py`): `SourceRef` (the data analogue of
  `FassungRef`: publisher/title/url/licence/attribution/Stand), `DataRef` (figure → {dataset_id,
  series}), `Dataset` (+ discovery tags: subjects/keywords/competences). Curated CC-BY datasets from
  per-source fetch tools (`tools/fetch_{statistik_austria,statistik_austria_health,
  statistik_austria_regional,worldbank,geosphere,un_wpp,undp_hdi,noaa_co2}.py` — **14 datasets**
  as of 11 Jul 2026), licence verified at
  ingest (**redistribute only under a recorded redistributable licence + attribution**; UNDP HDI
  verified CC BY 3.0 IGO; GFN footprint REFUSED — CC BY-SA). **The last (c)-flagged invented-number
  figures (c0081/c0096/c0097) are re-grounded** (`tools/reground.py` — 5 figures `data_source`-cited,
  3 honestly `illustrative`; the forced task-text deltas are flagged in the store items for SME review).
  `grounding/data_store.py`: `resolve_dataref` fills the citation from the vetted SourceRef —
  **overwriting** any hand-written attribution (no faked citations); `relevant_datasets` is the
  deterministic discovery query. **The flow is inverted:** the catalog feeds GENERATION (citable
  datasets injected into briefs + live prompts), and at assemble `ground_data` **derives figure values
  FROM the dataset slice** (overwriting authored numbers) + stamps the citation — select-never-author
  for numbers, not "author then cite". Citations render as "Quelle: …", student-visible (Quellenkritik
  is curriculum).
- **Geo** (`grounding/geo/` + `geo_store.py`, via `tools/fetch_geo_boundaries.py`): *boundaries are
  facts* — sourced CC-BY GeoJSON, licence-gated, attributed; feeds the choropleth (pure matplotlib
  PathPatch, even-odd holes for the Wien-in-NÖ enclave, latitude-corrected aspect — **no geo dependency**).
  `at_bezirke_2025` comes directly from Statistik Austria's official WFS, is deterministically
  simplified for print, and excludes only the redundant whole-Wien overlay (`900`) while retaining
  Gemeindebezirke `901–923`: 116 non-overlapping regions join exactly to the Bezirk population series.
- **Chemistry** (`grounding/chemistry.py`): curated IUPAC standard atomic weights + cited `SourceRef`;
  `parse_formula` (nesting/hydrates: `Ca(OH)2` → `{Ca:1,O:2,H:2}`), `molar_mass`, `subscript`; curated
  truth tables (substance classification · separation methods · acid/base). Add an element = one cited
  row; add a reaction/substance = one curated entry.
- **Voices** (`schema/voices.py`, `grounding/voices/`, `tools/fetch_vctk_voices.py`): a rights-gated
  reference library of CC-BY young-adult VCTK clips — **voices are selected, never authored** (the audio
  twin of the data layer). Provenance JSON tracked in git; audio binaries not.

## The asset classes

Each class finds the thing that is correct-by-**construction** (or by **curation**) in its domain and
makes it the durable, reusable asset. Design depth lives in the named doc; the rules live here.

**Parametric variants + solution engine (MAT + CHE)** — `schema/parametric.py`,
`pipeline/parametrize.py` + `pipeline/chemistry.py`, templates in `library/templates.py`. A
`ParametricTask` = a prompt with `{slots}` + a `recipe` id; recipes register like asset generators
(`@_recipe`) and **own both sampling and solving** via sympy: a seeded RNG → an `Instance` (slot values
+ the DERIVED answer + worked `SolutionStep`s). `make_variants(task, n)` → N correct-by-construction,
deterministic-per-seed variants, each with its **Rechenweg** — the number is computed, never authored.
A recipe raises `Unsuitable` to reject a degenerate draw and resample; **distinct prompts are
guaranteed** where the draw space allows (small curated pools top up with repeats only if genuinely
< n). `variant_worksheet` wraps N variants into a `WorksheetContent` (stage-aware);
`orch.compose_variants(store, template_id, n, ramp=)` stages it for Gate-2 review. The four-station
dashboard exposes this deterministic production path in **Korpus → Arbeitsblätter** (`GET /api/templates`,
`POST /api/variants`); figure-emitting variants open directly in the ordinary PDF preview.
`TaskBlock.solution_steps` is the canonical worked-solution field — teacher-only, **DERIVED,
never LLM-authored**. Chemistry rides the same registry: `balance_equation` (element×species
conservation matrix → sympy **nullspace** → smallest positive integers; unique balance ⇔ 1-D nullspace)
drives quantitative recipes (`molar_mass`/`equation_balance`/`stoichiometry`, Oberstufe) and
qualitative Unterstufe recipes that are **derived** (`reaction_type`, `atom_count`) or **curated truth**
(`substance_classification`, `separation_method`, `acid_base_neutral`). **Inline math:** a `RichText`
run with `math=True` carries LaTeX → small inline PNG via mathtext, embedded with `<img>` in
`richtext_markup`; a `$…$` span in a parametric prompt template becomes a math run.
**Physics rides the same registry** (`pipeline/physics.py`, `grounding/physics.py`, `phy-*` templates):
recipes compute with **`sympy.physics.units`** and `_assert_dimension` the result against its expected
unit BEFORE formatting — a unit-category error is structurally impossible (uniform_motion·density·ohm·
resistors·lever·energy_power). Constants are curated + cited (g exact per CGPM 1901; school densities).
**Misconception distractors** (`pipeline/misconceive.py`, `grounding/misconceptions.py`): a
`multiple_choice` recipe's `Instance` carries an `MCSpec`; `@_misconception` transforms compute each
wrong option by applying a curated, literature-sourced Fehlermuster to the SAME drawn values —
**guaranteed ≠ the correct answer** (both computed, compared post-formatting), deduped, plausibility-
gated; the teacher guide names each probe via `watch_outs` ("B prüft: Vorzeichenfehler (Radatz)").
**Solution graphs** (A4): `Instance`/`TaskBlock` carry optional `solution_paths` (named strategy +
steps) — the *alternative* Rechenwege beside the primary `solution_steps` (LGS: Einsetzung/
Gleichsetzung/Addition; Prozent: Dreisatz/Operator/Formel), each independently derived and asserted
equal to the answer; **teacher-only**, rendered as "Alternative Lösungswege", absent from generation
views like `solution_steps`.

**Matura pack + figure emission (10 Jul 2026).** Three SRDP-demand recipes joined the registry
(`exponential_model` [FA — growth/decay/Zinseszins, evaluate/solve-t/find-rate], `boxplot_from_data`
[WS — exclusive school-convention quartiles, odd n so they're clean], `probability_tree` [WS — Urne
mit/ohne Zurücklegen, exact sympy fractions, Pfad-/Additionsregel]) with templates anchored
MAT.OS.6.REE.10/BES.01/BES.04. **A recipe can now EMIT A FIGURE per instance:** `Instance.figure`
(`FigureSpec` = generator + spec) → `_instantiate` builds a per-variant Asset (unique id
`<task>-<seed>-fig`) wired via `asset_refs`; `variant_worksheet` collects them. The invariant: **the
figure masks the asked unknown** ("c = ?") — `pythagoras` (triples, ask hypotenuse OR leg; drawing
lengths normed so the answer never surfaces even as a coordinate) and `kreis_umfang_flaeche`
(MAT.US.4.FIG.01/.02) prove it; `probability_tree` emits its Baumdiagramm (stage-1 labels only —
leak-safe). **`boxplot_from_data` deliberately emits NO figure:** `Instance.figure` assets render on
EVERY projection, so a solution boxplot would hand students the five-number answer — locked by tests.
**Teacher-only computed figures:** `Instance.solution_figure` emits an asset wired only through
`TaskBlock.solution_asset_refs`; `boxplot_from_data` uses it for the derived five-number solution plot,
so student/homework receive no image while the teacher guide does. **Latein rides the same engine** (`pipeline/latin.py` +
`grounding/latin.py`): a `wortbildung` recipe over **curated real derivations** (12 prefixes ×
9 base verbs → 39 attested words with meanings + assimilation notes — select-never-author: no
synthesized Latin, ever), templates `lat-us-*` anchored LAT.US.3/4.SPR.01.

**Inline math** — a `RichText` run with `math=True` carries LaTeX, typeset to a small inline PNG via
mathtext (`rendering/inline_math.py`, the `math_formula` engine) and embedded with ReportLab `<img>`
in `richtext_markup` (so fractions/exponents/roots stop reading as "code-symbols"). `inline_math.configure`
is called once per `build_pdf`; results cache by content hash. A `$…$` span in a parametric prompt
template becomes a math run.

**Rätsel engine (cross-subject)** — `pipeline/puzzles.py`, `schema/puzzle.py`, `matplotlib:puzzle_grid`;
zero LLM, answers **derived**. Kreuzworträtsel (backtracking crossing grid), Suchsel (with an
accidental-duplicate refill guard), Domino/Trimino (**closes iff every match is correct** — self-check
by graph construction), Rechenmauern (unique-solution masking verified by constraint propagation). A
puzzle is a code-gen grid asset + a `TaskBlock` wrapper of the **core kind `puzzle`** (no write-space —
the grid IS the answer surface); the SOLVED grid rides `TaskBlock.solution_asset_refs`, **teacher
projection only** (student sees the empty grid via `asset_refs`). Umlaut convention = single-cell (one
module constant flips to AE/OE/UE). Corpus-scale clue ingest is a follow-up seam.

**Annotated authentic texts (DEU · LAT · FS)** — `schema/texts.py`, `pipeline/text_tasks.py`,
`store/textstore.py`, `library/texts.py`. An `AnnotatedText` = a real, rights-cleared text + a curated
annotation layer; `build_worksheet` derives tasks whose **answers come FROM vetted annotations, never
authored at task time** (no hallucinated Erwartungshorizont); the text renders as a line-numbered
`source_text` block so tasks reference "Zeile N". Correct by **curation** — there's no sympy for German.
**Rights gate** (`orch.ingest_text`): `TextSourceRef.is_clear` enforces **AT 70-Jahre-p.m.a.** (not US
PD; a PD work ≠ a PD scan) or CC; author death year captured. Latein reuses the engine
(`translation`/`grammar`/`culture` kinds; `_serves_for` matches by dimension code, so the engine is
subject-agnostic). Scaling: subagents annotate a *provided verbatim* PD text → `tools/ingest_texts.py`.
**`tools/fetch_wikisource.py` (10 Jul 2026)** is the deterministic verbatim-text fetch (MediaWiki API:
exact-revision text + permalink + rights fields shaped for `TextSourceRef`; throttled; strips
`PageNumber` scan-markers so "Zeile N" anchoring holds; parser fixture-tested offline). First batch
staged via it: Grimm *Die Sternthaler* (Kl. 1) · Fontane *Herr von Ribbeck* (Kl. 3) · Goethe *Der
Zauberlehrling* 1827 (Kl. 4) · Phaedrus *Lupus et Agnus* + *Rana Rupta et Bos* (LAT Kl. 3/4) — all
AT-70-p.m.a.-clear, historical orthography preserved verbatim. **`tools/fetch_anno.py` (11 Jul 2026)**
adds the newspaper/OCR path through the official ÖNB IIIF manifest + ALTO resources. It targets the
ÖNB Labs Public-Domain-Mark subset, records the exact canvas URL, preserves OCR verbatim (including
errors, line and block boundaries; no silent correction/dehyphenation), and marks it
`machine_ocr_unverified`. The first staged source is the 1871 *Leitmeritzer Zeitung* report on a
Lehrertag; its annotated text and referenced-only GPB Quellenarbeit are both verify-clean.

**Audio / Hörverstehen (modern FS)** — a listening text is an `AnnotatedText` with `medium="audio"`:
`build_worksheet` attaches `Asset(role="tts", generator="audio:tts")`, renders a printable audio cue +
listening tasks (dim HOR), and keeps the **transcript teacher-only** (an `oral`-modality `source_text`
dropped on the student sheet; `show_transcript=True` = the A1 listen-and-read variant; the transcript is
the always-present printable fallback). Media-policy admits `tts` as a code backend. Scripts are
**authored-then-vetted** (no PD A1/A2 L2 audio to select). Backend: **F5-TTS multi-voice on the local GPU** — CUDA torch has no cp314 wheel, so the 3.14
core drives a **separate Python 3.12 subprocess**: `audio/f5_backend.py` (core, no torch — normalizes
dialogue `turns`, resolves each turn's `(lang, persona)` to a curated voice) calls `audio/f5_render.py`
(the GPU worker, *executed* never *imported*), then ffmpeg → mp3. `register()` wires it; offline →
`AudioNotConfigured`. Config: `TTS_PYTHON`/`TTS_PYTHON_SITE`/`TTS_FFMPEG`. Full notes + open items:
`Documents/tts-audio-engine.md`.

**Realien (modern FS)** — extends `AnnotatedText` (`cefr`/`origin`/`scene`/`facts` + `communicative`/
`roleplay` kinds); design: `Documents/realien-design.md`. The load-bearing reframe is
***purpose-appropriate rigor***: a Realie is the **Sprechanlass, not the Aussage** — so the fact
discipline DEMOTES (**constructed is the default**, no source/rights gate; facts are invented-coherent
fiction guarded by `pipeline/realie_lint.py`, an *internal-consistency* check whose per-answer universe
includes the task's own prompt — a shown sum like "£2.00 + £3.00 = £5.00" is exempt, a bare wrong price
is caught) while the **language stays load-bearing** (L2 correctness + CEFR level, SME-gated). Tasks are
communicative-first: scan warm-up (Lesen) → boxed write task (Schreiben) → a **Sprechkarte**
(`RolePlayPayload` → `rb.cue_cards`, oral, **no write-space**, served via the Lernarrangement
interaction anchor — `pipeline/realie_arrange.py`). A Realie renders as a real artifact — a paper-tinted
`rb.material_card` (no line numbers) — and atmospheric "fluff" is welcome *as long as it touches no
datum a task uses*. Fact-care snaps back for **informational** genres (deferred). *"Invent the
timetable, vet the French."* Breadth seam: `tools/realien_prompt.py` + `tools/ingest_realien.py`
(constructed-aware: drops a stray source).

**History / expression provenance (GPB)** — design: `Documents/history-facts-provenance-design.md`.
The third provenance axis: **where the wording came from** (copyright protects expression, not facts —
a block authored *fresh from facts* carries no CC-BY-SA obligation; a paraphrase/quote does).
`BlockProvenance` on `BlockBase`: `expression_origin ∈ original·adapted·quoted` + `sources`
(`role ∈ facts·expression`). The obligation booleans (`attribution_required`/`share_alike_applies`) are
**DERIVED** `@computed_field`s — present in the serialization schema, absent from validation (a
`mode="before"` validator strips echoed booleans so the JsonStore round-trip stays clean).
**Mandatory-internal twist:** an `original` history fact block MUST record a `role="facts"` source (the
fact is fact-checked at the gate, not asserted). `pipeline/prose_lint.py` (advisory): (A) wherever
provenance is present — `adapted`/`quoted` needs an expression source, a long quote exceeds Zitatrecht,
CC-BY-SA trips ShareAlike; (B) scoped to GPB ∪ `ContentFlags.historical_fact` (GPB detected by served
competence-id prefix) — an `original` fact block needs a facts source; a fact-bearing InfoBlock
(`callout` exempt) needs *some* provenance. Rendering is pure: student/homework get "Quelle … Lizenz …"
**only when** `attribution_required` (`original` renders clean); teacher gets the full sources incl.
the facts records. **Ingest rights gate** (before assemble): embedding `adapted`/`quoted` needs CC /
explicit-redistributable / AT-70-p.m.a.-PD; a short quote (≤`SHORT_QUOTE_MAX_CHARS`=300) rides the
Austrian **Zitatrecht (§42f öUrhG)**; non-clear raises → nothing staged. `tools/fetch_wikipedia.py` is
**metadata-only** (permalink to the exact revision; no article prose — no LLM in the fact path).
**Policy: `adapted` is discouraged** (ShareAlike can encumber the whole worksheet) — prefer
original-from-facts + a short PD quote. Quotations are **selected, not authored** — verified verbatim;
never fabricate historical wording.

**Sachverhalt — the content/exposition layer** — design + decisions:
`Documents/sachverhalt-content-layer-design.md`. A curated module of structured **Sachwissen** about one
topic; one module → three projections. This is the **fourth mechanism** in action: the facts
(`HistEvent`/`Actor`/`CausalLink`/`Concept`, plus **`Process`**/cycle [Bio] and **`Region`** [Geo →
choropleth]) are *selected/sourced*; the connective **Darstellung is authored over the frozen fact-set**
— guarded by the deterministic **entity-lint** (`pipeline/sachverhalt_lint.py`, run **at ingest on the
Sachverhalt, NOT in worksheet verify** where the fact-set is gone): **years are the HARD guarantee**
(every 3–4-digit year in the Darstellung must be in the fact-set); **names are ADVISORY** (German
capitalises every noun, so only a multi-word phrase with no fact-set token is flagged).
`pipeline/sachverhalt.py::build_worksheet` derives: Darstellung → InfoBlocks with grounded
`original` provenance attached *by construction*; **DERIVED figures** (timeline · Wirkungsgefüge via
`cause_effect` · `process_flow` · `choropleth_map` — the map is correct on BOTH axes: sourced boundaries
+ values filled from the cited dataset at assemble); and Sachkompetenz tasks whose **`answer_key` is
COMPUTED from the fact-set** (`chronology` = sort by `at`; `cause_effect_match`/`concept_match` = the
pairing itself, prompt list deterministically reordered — *no grader engine; the module IS the key*),
plus open comprehension/structure tasks and an `urteilsfrage` high-band task (judgment kind
auto-selected per subject; strands served via `sach_dimension`/`urteil_dimension` hints). Ingest gate:
≥1 `role="facts"` source + entity-lint clean. Breadth seam: `tools/sachverhalt_prompt.py` +
`tools/ingest_sachverhalte.py`. Registry: `library/sachverhalte.py`.

*(Planned next: **PD Bildquellen** — roadmap B5; the **illustration program** — `illustration-design.md`.)*

## Master library, blocks, and composition

- **Master library** (`teachersaid/library/`): curated, gold-standard `WorksheetContent` examples — the
  quality bar, the few-shot seeds, the offline demo stock. Each `build_content()` is grounded in
  `lehrplan/` (real competence ids, dims ⊆ subject model, verify-clean); `registry`/`find()`/
  `seed_library()`. `_generate_content` serves a registered example when there's no API key; with a key
  it generates seeded by the example — either way output lands in the **review queue** (corpus loop;
  nothing generated reaches delivery ungated). `orch.stage_worksheet` stages a pre-built curated
  `WorksheetContent` — the ingest seam for hand-curated flagships. `tests/test_library.py` locks every example verify-clean
  against catalog drift — keep it green when editing the catalog. **The quality bar is the blackboard
  test:** corpus content must beat what a teacher writes on the board in a minute — bare drills fail,
  even as Übungsreihe. Don't author shallow examples (match `demo/strahlung.py`; plan:
  `Documents/master-library-plan.md`).
- **Block library** (`library/block.py`, design: `Documents/block-library-design.md`): the **block** is
  the durable library unit; a worksheet is a *composition*. `LibraryBlock` = a schema `Block` + metadata:
  subject/Klasse/KB, `serves`, `cognitive_level`, `dimensions`, `modality`, **`scope`**
  (compact|standard|extended — *orthogonal to* `cognitive_level`), `family` (groups richness variants),
  `status`, `provenance`, and an honest, never-measured **`difficulty`** (1–3, author/SME estimate; when
  unset, derived from the cognitive level's Anforderungsbereich; surfaced in
  `DepthProfile.by_difficulty`, warned on when flat). A **computed advisory cross-checks it** (roadmap
  C4, `pipeline/difficulty_model.py` + the reviewable `difficulty_weights.json`, fit by
  `tools/fit_difficulty.py`): transparent surface features (text load · kind cost · number domain ·
  answer-surface openness · steps/math for parametric) **nudge a cognitive-level anchor**; a ≥1-band
  disagreement with the operative difficulty is a verify **warning** (advisory lane) + an Einblicke cue
  (`stats.difficulty_review_cues`). DERIVED + ADVISORY — it **never** overrides the authored value. The
  honest finding: the corpus has **zero** authored `difficulty` labels, so the model is *not learnable*
  (an accuracy-max fit trivially recovers `cognitive_rank`) — hence **curated weights + fitted
  thresholds**, not a learned model. Depth: `Documents/difficulty-model.md`. `harvest(content)` extracts a worksheet's blocks
  (a learn-text is a block; framing intro/transitions are not) and **captures asset specs** so figures
  travel. `store/blockstore.py`: `upsert` is idempotent and **preserves review status** (re-seeding
  never un-approves); `seed_blocks` seeds the SME-reviewed examples as `approved`. `stats.py` is the
  block matrix.
- **Composition** (`pipeline/compose.py`): builds a worksheet from **approved** blocks — select by
  target competences, one per `family`, prefer the `scope` matching the envelope, greedy time-fit, ≤2
  readable info blocks, template framing (no LLM). **Targeting:** an explicit `kompetenzbereich`
  (`resolve_kompetenzbereich` — the robust path; a worksheet *title* needn't echo the KB name) or
  free-text `topic` matching (works when the title echoes a KB/Anwendungsbereich; **fails** for catchy
  titles — that's why the KB path exists). `topic` is always the display title. **Angle-aware:**
  competences fix WHICH blocks are eligible; the topic/Kernfrage is the *angle* — deterministic term
  overlap (angle = topic minus the KB's own words) prefers on-angle blocks, so two Kernfragen on one KB
  compose **different** sheets. **Difficulty-calibrated:** seeds one block per band so a tight budget
  spans easy→stretch. An optional **LLM framing pass** (`pipeline/frame.py`, graceful no-op offline)
  writes a coherent Kernfrage + intro + one-line lead-ins AROUND the fixed blocks — **no new
  tasks/facts; vetted task content untouched** (no-drift). Scope variants via
  `orch.ingest_scope_variant` + `tools/scope_variants.py`.

## Delivery loop + campaign planner

- **`pipeline/deliver.py::deliver`** — the LLM-free delivery read-path (invariants §10): serve a
  **vetted library worksheet** (deterministic match: KB-competence overlap ×3 + topic-term overlap +
  envelope fit) › **compose** from approved blocks (assemble+verify run; still no LLM) › an **honest
  gap** recorded in the demand queue. Read-only against the corpus — the only write is the gap's
  `DemandRecord`. `POST /api/deliver`; test form in the dashboard. Inter-block coherence is deliberately
  NOT here yet (→ roadmap C5, the dramaturgy engine).
- **`store/demandstore.py`** — the **Wunschliste**: a gap becomes an `open` wish (subject·Klasse·
  topic/KB·envelope + the honest reason), lifecycle open→planned→fulfilled/dismissed. Demand feeds the
  next campaign — the corpus loop's intake.
- **`stats.coverage_map` / `campaign_gaps`** — the campaign planner: one cell per
  (Stufe·Fach·Klasse·Kompetenzbereich); status **gruen** (≥`GREEN_MIN_TASKS`=4 task blocks AND all 3
  Anforderungsbänder — the floor compose needs) / **teil** / **leer**. `GET /api/coverage`;
  `GET /api/coverage/gaps` exports non-green cells WITH verbatim competence ids — the campaign-brief
  anchors `tools/breadth_prompt.py` consumes.

## Lernarrangement (schema v0.5 — built)

A `Lernarrangement` (`schema/arrangement.py`) is a composite sibling that **contains** worksheets: each
`ArrangementRole.material` IS a `WorksheetContent` (the worksheet stays the primitive; a plain worksheet
is the n=1 case). `competence_anchors` capture the **oral/social/enactive** competences a printable
sheet can't reach — served by the `interaction`, `debrief`, or `shared_product`, not by any task.
`nachweis`/`depth_profile` are **DERIVED** (`pipeline/arrange.py`): arrangement Nachweis = ⋃ role
exercised competences **+ the anchors** (a competence covered *only* by an anchor is the v0.5 payoff);
`verify_arrangement` verifies every role as a worksheet + arrangement rules. **Rendering reuses the
worksheet path entirely** (no second renderer): `rendering/arrangement.py::render_teacher_orchestration`
is PURE over schema (the run-guide); the asset-building bundle `render_arrangement` lives in the
**pipeline** (it builds asset images; renderers stay pure). **Scope line: we make the material bundle +
a teacher run-guide; we do not run the room.** Hero: `demo/gwb_standort.py` (GWB Gemeinderat-Planspiel).
Generation: `GenArrangementBody` → `arrangement_body_to_canonical`, `arrange.ingest_arrangement`;
briefs `tools/arrangement_prompt.py`, ingest `tools/ingest_arrangements.py`. Arrangements use their
**own store** (`ArrangementStore`), not `ReviewItem`.

**Fächerübergreifende Bündel (Wave C3 — the Projektwoche).** One übergreifendes Thema (ÜT —
Umweltbildung, Medienbildung, …) approached from EACH subject that carries it. `resolve_uet(uet, klasse)`
(`pipeline/resolve.py`) is the cross-subject analogue of `resolve_grade`: every verbatim competence
carrying the ÜT across ALL Pflichtgegenstände of the stage (legend via `lehrplan_store.uebergreifende_themen`).
`pipeline/compose_uet.py::compose_uet` is the **corpus** half — deterministic + LLM-free, the delivery-loop
discipline: select APPROVED blocks serving those competences, one small worksheet per subject (a *station*),
wrapped as a `Lernarrangement` (format `stations`) whose shared Projektwoche product anchors an **anchor-only**
ÜT competence (the v0.5 payoff). Requires ≥2 subjects with approved blocks, else an honest `UetResult` gap →
demand queue. **Cross-subject wrinkle:** each role assembles/verifies against its OWN subject-grade resolution
(`assemble_arrangement`/`verify_arrangement`/`stage_arrangement` take an optional `role_resolutions` map — a
single-subject arrangement passes none), while the arrangement Nachweis derives against the ÜT resolution.
Seam: `orch.compose_uet_arrangement` → `POST /api/compose-uet` (+ `GET /api/uebergreifende-themen`, Korpus
compose form); flagship `library.seed_uet_arrangements` (ÜT 11 Umweltbildung × Kl 4 — Physik · Geographie ·
Technik · Biologie · Chemie).

## Breadth generation — subagents → ingest (the seam, no API key)

Scaling the corpus uses **subagents as the generator** (they run via Claude Code; no `ANTHROPIC_API_KEY`).
Each emits a `GenWorksheetBody` JSON anchored to **real** catalog competences, validated through the
real generation seam, staged for HITL review.

- `tools/breadth_prompt.py` writes a fully-grounded per-subject brief (verbatim competences by KB across
  grades, allowed dims/kinds, the JSON shape + a worked example, N **distinct Kernfragen**). Per-subject
  config in `SUBJECTS` (anchor kb|grade; `practical` → enactive/oral modality; `target_language` for
  FS1/FS2/LAT → target-language *material*, German instructions + German teacher layer).
- `tools/ingest_batch.py --dir` validates (`--dry-run`) or persists. **Its first-pass normalizer is
  load-bearing** — hand-written JSON is the real fragility, so it deterministically absorbs the
  recurring agent slips rather than re-spawning: `„…"` typographic-open/straight-close repair
  (`(?<!\\)`-guarded), literal control chars (`json.loads(strict=False)`), info-blocks shaped like
  tasks, invalid info `kind` → prose, `answer_text`→`answer_key`, German rubric keys,
  `{label,description}` levels, off-enum `serves.relation`, nested multi-question `multiple_choice`
  folded into the prompt. **Extend the normalizer when a new slip class appears; don't re-spawn agents.**
- `orch.ingest_generated(..., render=False)` is the backbone: `body_to_canonical → assemble → verify`
  (+ render only if asked — **breadth is render-free**; blocks are inspected structurally), stage a
  pending content item + harvest blocks `in_review` — **only if verify-clean** (an invented competence
  id / kind / dimension surfaces as an error here, never a silent bad block). Anchors via
  `resolve_kompetenzbereich` (content-KB subjects) or `resolve_grade` (strand-KB subjects); a too-narrow
  KB auto-widens to the grade when serves cross strands. `GenTaskBlock` carries `rubric`.
- **Sibling seams, same pattern** (normalize → schema → gates/lints → build → assemble → verify → stage
  *only if clean*): `ingest_sachverhalte`, `ingest_realien`, `ingest_texts`, `ingest_arrangements`,
  `ingest_triage`, `scope_variants`.

## HITL dashboard (`api/` + `api/static/index.html`)

Two review gates, one `ReviewItem` type (`stage` ∈ **brainstorm** | **content**); four stations:

- **Planen** — rough ideas (`orch.submit_brainstorm` / `orch.suggest_from_catalog`) + the
  Kampagnen-Planer + the Wunschliste + the delivery probe (whose gaps feed the Wunschliste). Approve →
  `orch.flesh_out` (offline: served from the master library; with a key: generated — both land in Gate 2,
  never delivery).
- **Prüfen** — the unified tier-laned gate (all content kinds; lanes = the four correct-by-construction
  mechanisms; keyboard flow; **triage-ordered** — `pipeline/triage.py` heuristic + the adversarial pass
  `tools/triage_prompt.py`/`ingest_triage.py`; **triage is never the gate**). Worksheet→block approval
  **cascades**; the **Überarbeiten** decision is status-preserving with a mandatory note →
  revise-flagged feedback, held from bulk release. Artifacts self-heal cross-machine (absolute paths →
  rebuild on load).
- **Korpus** — the approved library: Arbeitsblätter (structural **Blöcke** view + **Vorschau** PDFs) ·
  Bausteine · Arrangements · Abbildungen (file-backed assets for review + every code-gen figure rendered
  inline, deduped by generator+spec) · Datensätze (source/licence/Stand + figure preview) · Texte
  (text + rights + annotations; "Arbeitsblatt erzeugen") · Sachverhalte — plus the compose form.
- **Einblicke** — the feedback digest + the block-coverage matrix.

**Rich feedback loop** (`store/feedbackstore.py`): every review surface carries rating (1–5) + comment +
quick tags, **decoupled from the decision** (partial review still accrues signal). ONE central
append-only store keyed `(target_kind, target_id)`; `digest()` is a single read → the "zu überarbeiten"
worklist. `request_changes` regenerates a worksheet with the note injected; other kinds carry a `revise`
flag. Further routes: `POST /api/compose` + `GET /api/kompetenzbereiche`,
`POST /api/blocks/approve-all`, `/api/demand*`, `/api/feedback*` (post · query · digest · tags),
`/api/datasets*`, `/api/texts*`, `/api/sachverhalte*`, `/api/arrangements*`.

```
Planen (rough idea) ─approve─► flesh_out (resolve→plan→generate→verify→assemble→render)
   ─► Content [Gate 2: Prüfen] ─approve─► Korpus (the material library)
```

The store holds review items + the approved library — deliberately **no gradebook, no classroom state,
no student PII** (we make the material, we don't run the room).

## Schema conventions (important)

- **Two model layers, one seam.** `schema/` holds full-fidelity canonical Pydantic models;
  `schema/generation_views.py` holds flattened, recursion-free mirrors the LLM emits, plus
  `to_canonical()` — the single up-conversion point. **All LLM↔storage conversion goes through there.**
- **`RichText`** is `str | list[InlineRun]` canonically; generation views use plain `str`. A bare string
  normalises to one run; single unmarked runs collapse back.
- **`Nachweis` / `DepthProfile` are DERIVED**, never authored by hand or LLM — absent from generation
  views, populated only by `pipeline/assemble.py`. **Never let the model produce them.** (Same for
  `solution_steps` and the provenance obligation booleans.)
- **Open sets** (`TaskKind`, `cognitive_level`) are plain strings validated against the subject model at
  assemble time; the allowed set is injected into the *prompt*, not encoded as a closed JSON enum.
- `kind ∈ core ∪ subject_model.task_kind_extensions`; `dimensions ⊆ subject_model.dimension_ids()`.
- **`Baustein.teacher_overview` is a typed `TeacherOverview`** (throughline · talking_points ·
  extensions · differentiation · timing_notes) — authored/LLM-generated (NOT derived), teacher-only.

## Projection audience split (load-bearing)

- **Student & homework = student-facing only.** No Fassung stamp, no competence ids, no Nachweis, no
  teacher layer. They keep the **write-in space**.
- **Teacher = a guide, not a filled-in clone.** It **omits the write-space**, and shows the expected
  answer + `acceptable_reasoning` + rubric + `watch_outs`, the section `teacher_overview` (Roter Faden +
  talking points + extensions), and the appended Nachweis/DepthProfile. The Fassung stamp + per-task
  competence meta are teacher-only.
- **Generation focuses on the student side + answers**; the teacher layer is a generated section layer
  seeded by the curated examples. (Full table: `Documents/rendering-handoff-brief.md` §2c.)

## Testing

`tests/` mirrors the milestones; everything runs offline (the LLM is mocked via an injected generator).
Key invariants under test: schema round-trip; deterministic resolution + honest gaps; the Strahlung
DepthProfile reproduces schema §8 exactly (W2/S4/E1, 78/56 min) and STR.01 surfaces as a gap; all three
projections render + rasterise; student hides keys / teacher shows them; the `intentionally_flawed`
guard; the two-stage HITL loop + API; the worked examples exercise the v0.4 deltas; layout lints
(no label overlaps, no table overflow). Run one file: `python -m pytest tests/test_derive.py -q`.

## Conventions & gotchas (the index)

**Schema & derivation**
- `Baustein` lives in `schema/worksheet.py`, **not** `schema/blocks.py` (easy import slip).
- Anything DERIVED (Nachweis, DepthProfile, `solution_steps`, provenance obligations, grounded figure
  values) is never authored by hand or model — assemble fills it.
- A task's **affordance is its kind**, not a separate field: `_SELF_CONTAINED_PAYLOADS`
  (`ordering`/`matching`/`multiple_choice`) get **no** generic write-space by construction —
  `true_false_justify` is NOT one (its justification needs lines). Don't pair an ordering/matching task
  with a `LinesResponse` and expect lines. Generated prompts fit the topic's *nature* (event → "warum
  war X wichtig", process → "wie X abläuft", regions → "was die Karte zeigt"), not one template.

**Rendering & text**
- `rb.para(value, style)` escapes RichText; `rb.raw_para(markup, style)` is for **already-built** inline
  markup — don't double-escape (that prints literal `<b>` tags).
- Carlito (or Calibri, its metric twin) is discovered on Linux **and** Windows; else Helvetica fallback.
  **Sub/superscripts don't depend on the font**: `richtext_markup` normalises ₂/² → ReportLab
  `<sub>`/`<super>` over the plain digit (no tofu in Helvetica).
- PDF→PNG QA uses **PyMuPDF** (`fitz`), not `pdftoppm` (no poppler dependency).
- **Text fitting is measured, not guessed.** `rb.grid_table` wraps every cell in a Paragraph and its
  `weights` sum column widths to the frame — content can't overflow a cell. **Never hand a raw string to
  a ReportLab `Table`** (no wrap → overflow); route through `grid_table`/`wrapped_table`.
  `pipeline/figtext.py` is the figure twin: measure → fit → de-collide (the timeline lane-packs measured
  labels; the choropleth font-fits big regions and leaders tiny enclaves out). A leader is two artists
  (line + plain `ax.text`), **not** an arrow-annotation — so a label's measured bbox is the text alone.
  `figtext.overlap_pairs` + `tests/test_layout.py` catch regressions.

**Math & figures**
- The renderer's matplotlib **mathtext is a LaTeX subset**: `\leq`/`\geq` (not `\le`/`\ge`),
  `\binom{a}{b}` for column vectors (NOT `\begin{pmatrix}`), no `\begin{cases}` (join inline), avoid
  `ℝ` (U+211D) in plain-text titles (Carlito tofu).
- **Assemble/verify don't render** — new figure/math paths need a *render* test (that's how a `\le`
  slip once hid).
- Figures: never scientific notation; unit-scaled labels ("in Mio."); German number formats
  (`fmt_de`); years belong on a numeric x-axis. Every data figure is exactly one of `data_source` |
  `illustrative` (pure-math figures exempt).
- `inline_math.configure` is called once per `build_pdf`; results cache by content hash.

**Grounding & ingest**
- `stufe_for_klasse(klasse)` is the stage authority (1–4 US, 5–8 OS). `klasse: null` = cross-class.
- Oberstufe **Chemie dims are WO/EG/KZ**, not W/E/S. Operator routing is by canonical code, not display
  name. The two "CHEMIE" subjects (CHE, CHE2) are disambiguated by `_DISPLAY_NAME_OVERRIDES` in
  `lehrplan_store` — CHE2 carries a distinct display name ("Chemie (Wirtschaftskundliches
  Realgymnasium)") so name-routed campaigns reach it; plain "Chemie" routes to CHE.
- `resolve` checks the Fassung date window; the 2026/27 re-parse is deferred by decision until the new
  Fassung is published in full text.
- Malformed subagent JSON → **extend the ingest normalizer** (deterministic absorption), don't re-spawn.
- Locality: Tier-1 anchoring is **inquiry-frame** (students investigate their own region) — **never
  assert unvetted local facts**; asserted local data needs the curated Tier-2 path (regional datasets).
- Lint lanes: deterministic lints *guarantee* (entity-lint years, media policy, (c)-label); advisory
  lints *flag* for the SME (number-lint, prose-lint, chart-lint warnings, name checks, readability/WSTF,
  difficulty-model band gap). Triage is never the gate.

**Stores & process**
- **All stores subclass `store/base.py::JsonStore`** (shared file-I/O + id counter + status-preserving
  `upsert`). Add a store by setting `model` + `subdir` + a typed `list()`, **not** by copy-paste.
  Library stores (Block/Asset/Arrangement/Dataset) use `upsert`; Review uses `create`; Feedback is
  append-only `add`. This is the seam a
  future SQLite backend swaps behind (`Documents/architecture-review.md`).
- `intentionally_flawed` assets are wrong on purpose — never "fix" them.
- Match the surrounding German tone/terminology in product-facing strings; the user is the domain SME
  (physicist, Austrian) and fact-checks the physics and the German.
- Don't relitigate `project-handoff.md` §4. Don't push pilots/releases/GTM (build-for-joy).

## Where to look first

`project-handoff.md` (intent + session history) → `Documents/README.md` (the doc map) →
`Documents/lehrplan-bundle-schema-v0.3.md` (data model) → `teachersaid/schema/` (the model in code) →
`teachersaid/pipeline/` (the engine) → `teachersaid/demo/strahlung.py` (a complete worked content
object).

**What's next:** `Documents/feature-roadmap.md` — the build-for-joy feature program (Wave A task/figure
engines · Wave B the image program · Wave C corpus structure), "▶ Start here" at the top.

## Updating this file

CLAUDE.md is the **operating manual** — keep it lean and load-bearing:

- A new feature earns **one tight paragraph** in the right section: its rule, its seams/modules, its
  gotchas, and a pointer to its design doc. Not a walkthrough.
- **History** (what shipped when, session narratives) goes to `project-handoff.md` as a dated session
  block. **Design depth** goes to `Documents/<feature>-design.md` (+ an entry in `Documents/README.md`).
- No dates, no "DONE/new", no rotting counts in this file (the test count above is the one exception —
  update it when you touch this file).
- If a section outgrows ~15 lines, that's the signal to extract a design doc and compress the section
  to rules + pointer.
- `AGENTS.md` defers to this file — don't duplicate content there.
