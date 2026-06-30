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
                                       #       matplotlib, pillow, pyyaml, pymupdf, sympy  (pytest for dev)
python -m pytest -q                    # 265 tests, fully offline (no API key required)
python -m teachersaid seed             # seed the master-library examples into the review queue
python -m teachersaid                  # dashboard → http://127.0.0.1:8000
```

(Python 3.11–3.14; the C-extension deps — reportlab/pymupdf/matplotlib — have 3.14 wheels.)

- **LLM generation** uses the Anthropic SDK with `claude-opus-4-8`, adaptive thinking, effort=high
  (see `teachersaid/config.py`). It activates only when `ANTHROPIC_API_KEY` is set.
- **Offline fallback:** without a key, a request for any **master-library** subject/topic
  (`teachersaid/library/`) is served from its curated content object, so the whole loop is demoable
  with no network. `seed` pushes all examples into the dashboard's review queue.
- Generated content lands under `runs/`. **Persistence policy (`.gitignore`): git owns the
  *content + review state* (all `runs/**/*.json|.md|.txt` — the generated modules and the HITL
  store — small, diffable, and NOT regenerable for subagent-authored work, so remote-session
  output survives in git), and ignores only the rendered *binaries* (`runs/**` PDFs + QA-raster
  PNGs + sourced asset images — large, churny, rebuildable from the tracked content). Same split
  as `grounding/voices` (provenance JSON tracked, audio not). Drive can carry the binaries; git
  carries the text — complementary, not competing. Artifact paths in store JSON are absolute, so
  renders rebuild on first dashboard load rather than being relied on from git.

## Invariants (and their boundaries) — read `Documents/invariants.md`

The project's load-bearing rules — and crucially *what each does NOT forbid* — live in
**`Documents/invariants.md`**. Read it before you let a remembered rule block a good idea; several rules in
this file are stated in their *strong proxy* form and the boundary matters. The one most often mis-applied:

> **"Select, never author" applies to FACTS, not to EXPRESSION.** The LLM never originates a load-bearing
> *fact* (numbers, dates, names, quotes, competences — these are selected/computed/curated). It **may** author
> *expression* — prose, narrative, framing, task wording — *as a projection over a frozen, given fact-set*
> (the same shape as rendering). Correct-by-construction has **four** mechanisms: computed · selected ·
> curated · **re-expressed-under-constraint** (authored prose over sourced facts + a deterministic
> entity-lint). So "never author" ≠ "no prose". See `invariants.md` §3 + `sachverhalt-content-layer-design.md`.

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
| Assets | `pipeline/assets.py` | code-generated (matplotlib), correct-by-construction; `intentionally_flawed` assets are built **wrong on purpose and never "fixed"**. **Pluggable registry (Phase 4):** `Asset(generator, spec)` is a declarative request; builders register against a `<backend>:<recipe>` id (`@_generator`). Parameterized recipes read `spec` (`number_line`, `bar_chart`, `function_graph`, `math_formula` via mathtext); the **`diffusion:` backend** (Phase 4 #4) plugs in the same way: `register_diffusion_backend(fn)` wires the SME's image-gen agent; `build_asset` dispatches `diffusion:*` to it (offline → `DiffusionNotConfigured`, no silent slop). The agent's brief (contract + content-free rule + manifest) is **`Documents/diffusion-handover.md`**. A **decorative kit** (`svg:badge/banner/motif`, content-free, rasterised via PyMuPDF — no extra dep) ships now. **Entry-gate (Phase 4 #3):** `pipeline/media_policy.py` enforces the invariant — *content-bearing visuals must be code-gen or vetted-sourced; decorative must be content-free* — by classifying each asset's role+source against `DEFAULT_MEDIA_POLICY`; runs inside `verify`. **Asset library (Phase 4 #4):** `store/assetstore.py::AssetStore` (parallel to `BlockStore`) holds the **file-backed** classes (decorative + sourced) with tags/status/reuse; `orch.ingest_asset` gates + materialises + stores; `library/decorative.py::seed_assets` seeds the kit. Code-gen content assets stay as specs on blocks. **Legibility + representation (load-bearing):** *correct numbers are necessary but NOT sufficient — the chart TYPE, scale, and labels must make the data legible and honest.* Recipes self-correct layout (`bar_chart` auto-horizontal for long/many labels, a value label on every bar so none is "invisible", optional `log` for orders-of-magnitude ranges, wrapped titles, `constrained_layout`); `pipeline/chart_lint.py` (run in `verify`) flags misrepresentations — a 0/1 "classification" plotted as bars, an extreme range that begs a log/table decision, or numeric/temporal x-values forced into bars (those are a trend/relationship → line/scatter). **Intent-declared figures (not "everything is a bar"):** the generator declares WHAT the data is, not the chart type — `GenDataFigure(intent ∈ trend·comparison·relationship·composition·distribution·spread·scale, data)` (gen view), and the **deterministic** `schema/chart_choose.py::choose_representation` maps it to the right recipe (trend→`line`, relationship→`scatter` +optional fit, distribution→`histogram`, **spread→`boxplot`** [five-number summary / compare distributions], scale→`number_line`, comparison/composition→`bar_chart`, **demographic→`population_pyramid`**, **timeline→`timeline`**, **climate→`climate_diagram`** [dual-axis temp-line + precip-bar Klimadiagramm]). Same split as everywhere: the LLM declares intent, code guarantees a legible representation. The recipe vocabulary is `number_line·bar_chart·line·scatter·histogram·boxplot·function_graph·math_formula·population_pyramid·timeline·climate_diagram` plus the **geometry family (KB3)** `right_triangle·rectangle·polygon·circle·coordinate_plane` and the **probability tree** `tree_diagram` (Baumdiagramm — structural, via `body.assets`) (labels are spec-provided so a figure never leaks the answer, e.g. "c = ?") — all in `GENERATION_RECIPES`; `body.data_figures` (intent) is preferred for data, `body.assets` (explicit generator) is for structural/geometry figures. **`boxplot`+`tree_diagram` were added from the accessible-Matura figure scan (WS strand);** see `Documents/matura-math-coverage.md`. |
| Verify | `pipeline/verify.py` | rules (kinds/dimensions/coverage/depth/difficulty/**media-policy**/**chart-sanity**/**(c)-data-label**); LLM fact-check optional. The **(c)-label gate** (`pipeline/figure_lint.py`) warns when a data figure carries real-looking numbers but declares neither `data_source` (sourced+cited) nor `illustrative` (schematic) — the grounded-facts honesty rule. |
| Assemble + derive | `pipeline/assemble.py`, `pipeline/derive.py` | **deterministic** — `derive_nachweis` (coverage + auto-surfaced gaps), `compute_depth` (DepthProfile), `printable_coverage`; **`data_ground.ground_data`** derives each figure's real values FROM its `data_source` dataset slice + stamps the citation onto the content (so rendering stays pure; *select-never-author* for numbers) |
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

## Oberstufe (Sek II) — stage-aware grounding (Phase 0/1)

The Oberstufe (Klassen 5–8) is a second catalog under **`lehrplan/oberstufe/`** (18 subjects, ~1360
competences), produced by a sibling parser **`tools/parse_lehrplan_oberstufe.py`** (the Oberstufe is
structurally different — semesterised into Kompetenzmodule). Each competence carries a **`kind`**:
`descriptor` (the grade-independent Kompetenzmodell competences — W/E/S etc., id `<C>.OS.x.<KB>.nn`) or
`lehrstoff` (per-semester Inhaltsbereiche, carrying `klasse`+`semester`+`kompetenzmodul`). The curated
judgment layer is built by **`tools/build_oberstufe_meta.py`** → `lehrplan/oberstufe/_meta.json` +
`subject_models.json` (mirrors the Lehrplan's own dimensions per SME decision — note **Chemie uses
WO/EG/KZ, not W/E/S**).

**The store + resolver are stage-aware.** `grounding/lehrplan_store.py` functions take a `stufe`
(default `"Unterstufe"`); **`stufe_for_klasse(klasse)`** is the authority (1–4 → Unterstufe `lehrplan/`,
5–8 → Oberstufe `lehrplan/oberstufe/`). `ResolvedCompetence` gained `semester`/`kompetenzmodul`/`kind`
(None for Unterstufe). `pipeline/resolve.py` derives the stage from the requested Klasse;
`resolve_grade(..., kompetenzmodul=, semester=)` (+ `resolve_kompetenzmodul`) narrow to one module while
keeping the cross-cutting `descriptor`s. Ingest (`orch.ingest_generated`, `tools/ingest_batch.py`) and
`library/templates.variant_worksheet` are stage-aware too. The Unterstufe path is unchanged.

**Phase 1 — Mathematik parametric pack.** 6 Oberstufe sympy recipes in `pipeline/parametrize.py`
(`polynomial_curve`, `definite_integral`, `linear_system_2`, `linear_system_3`, `binomial_distribution`,
`vector_dot_angle`) + 6 templates (`mat-os-*` in `library/templates.py`) across all 4 Inhaltsbereiche.
**Inline-math gotcha (load-bearing):** the renderer's matplotlib **mathtext is a LaTeX subset** — use
`\leq`/`\geq` (not `\le`/`\ge`), `\binom{a}{b}` for column vectors (NOT `\begin{pmatrix}`), no
`\begin{cases}` (join inline), and avoid `ℝ` (U+211D) in plain-text titles (Carlito tofu). `tests/test_oberstufe.py`
locks resolution + the pack + a **render** test (assemble/verify don't render, which is how the `\le` slip hid).

## SRDP Operatoren — Matura-orientation vocabulary (`teachersaid/grounding/operators.py`)

The Austrian **Matura** (SRDP) is the competence-model capstone; its standardized **Operatoren**
(task verbs, banded by Anforderungsbereich) shape *what our tasks ask*. Harvested as **grounding,
not an asset class** (the decision rule + the full Matura write-up: `Documents/matura-operators.md`):
a controlled vocabulary injected into the generation brief (`llm/prompts.build_system`) —
*select, never author*. **Four authoritative CC-BY catalogs**, each stored in its true shape (they
don't share one): **Deutsch** + **GWB** (AFB-banded + definitions), **Naturwissenschaften**
(BIO/PHY/CHE — AFB **and** the W/E/S model, read from the source grid; the three sciences share one
base — SME decision), **Mathematik/AMT** (flat, *not* AFB-banded, + a preferred Antwortformat that
maps to our `kind`: `mc→multiple_choice·z→matching·k→construction·l→table_fill·o/ho→open_response`).
`_RANK_TO_AFB` is kept identical to `pipeline/difficulty._RANK_TO_BAND` (one ladder, two surfaces; a
test locks it). **Routing is by canonical code** (`lehrplan_store._code_for`), not display name, since
`model.subject` carries the caller's string. Other subjects fall back to a flagged generic palette;
still to curate: FS/Latein/GZ/Ethik. **Calibration (#1) done** (`tools/extract_matura.py` +
`Documents/matura-calibration.md`): the cognitive_level→AFB→difficulty model holds, no change. The
live thread is **Matura-backward design** — mine the SRDP endpoints into rich parametrized worksheets
for earlier grades; the Maths demand map + recipe-build order is `Documents/matura-math-coverage.md`.

### Matura archive downloader + subject-aware extractor (the full-archive build)

The home-PC TODO from `feature-roadmap.md` is **done**: the whole public SRDP archive is now reachable
and parseable (the remote session's egress proxy had blocked `matura.gv.at`/`aufgabenpool.at`; a home
network reaches both — aufgabenpool's 403 was only User-Agent gating). Three deterministic, **no-LLM**
tools (the `fetch_*`/`parse_lehrplan` precedent — a tool fetches & parses, the model never invents an
exam fact):

- **`tools/fetch_matura.py`** — the downloader. matura.gv.at `/downloads` is a TYPO3 *tx_downloads* +
  Solr archive where **each exam is a "Collection"** served as a zip (e.g. `KL25_PT1_AHS_MAT_00_DE_
  {AU,LO}.pdf`). Facets: `year` (2013/14…now) × `documentType` (Klausuren | Kompensationsprüfungen) ×
  `subject` × `schoolType` (AHS/BHS/BRP); results paginate. The download URL carries a per-collection
  **`cHash`** anti-tamper token (cannot be fabricated → we scrape the real hrefs). `--list` dry-runs,
  `--all` crawls the curated leaf subjects (`SUBJECT_CODE`), `--standard-only` skips translation/
  accessibility editions, `--extract` chains the extractor. Idempotent via a **manifest** recording
  CC-BY (IWG 2022) + *"Datenquelle: Bundesministerium für Bildung"*. Output → `runs/matura/`
  (git-ignored; Drive-synced). Pure parsing functions are unit-tested offline (`tests/test_fetch_matura.py`).
- **`tools/extract_matura.py`** — now **subject-aware** (dispatch on the filename's subject code; the
  load-bearing fix was the language slot, a CEFR code `B1/B2/A2` not `[A-Z]{2}`). Math/AMT keep the
  task+point parser; **Deutsch** parses the Korrekturheft's labelled fields (Textsorte · Wortanzahl ·
  Schreibhandlungen · operator-headed Arbeitsaufträge — operators mapped to canonical `operators.DEUTSCH`
  forms by *earliest-match* = the imperative head, so a trailing adverb can't outvote the lead verb);
  **Latein/Griechisch** parse the ÜT/IT point split + sources + the numbered IT Arbeitsaufgaben;
  **modern languages** parse skill × CEFR × item-formats (skill-split booklets, not operator-driven).
- **`tools/matura_demand.py`** — aggregates `runs/matura/json/` into a per-subject **demand map**:
  operators validated against the catalogs, Textsorten/Schreibhandlungen (DEU), ÜT/IT + operators (LAT),
  skill×CEFR coverage (FS), operator×AFB mix (MAT/AMT). Feeds the `matura-<subject>-coverage.md` write-ups.

The sciences/GWB are **not** in this Klausur archive (their Matura is oral/teilstandardisiert) — confirmed,
no parser. The corpus stays in `runs/` (no raw PDFs in git); re-mirror anytime with `fetch_matura --all`.

## Grounded facts & data layer (`teachersaid/grounding/data/`)

Generalises the grounding discipline from **competences** to **facts**: content states *real,
cited numbers* instead of LLM-invented ("schematisch") ones — completing "correct by construction"
from structure to substance. Mirrors the Lehrplan-catalog pattern exactly. **Load-bearing rule:
select, never author** — facts come from a deterministic tool fetching+parsing a real source, never
from the model; generation *references* a dataset by stable id (like `serves` → a competence) and may
*use* a datum, never *invent* one.

- **Schema** (`schema/datasets.py`): `SourceRef` (publisher/title/url/licence/attribution/Stand — the
  data analogue of `FassungRef`), `DataRef` (a figure pointing at {dataset_id, series}; resolved
  citation fields cached on it), `Dataset` (the curated in-repo record + **discovery metadata**:
  `subjects`/`keywords`/`competences` curated tags). `Asset` gains `data_source: DataRef` (→ (b)
  sourced+cited) and `illustrative: bool` (→ (c) schematic).
- **Catalog** (`grounding/data/_catalog.json` + `<id>.json`): written by **deterministic, LLM-free**
  fetch tools (the `parse_lehrplan.py` precedent), one per source, each verifying its licence:
  `tools/fetch_statistik_austria.py` (population by age×sex + per-Bundesland aggregation, CC BY 4.0),
  `tools/fetch_worldbank.py` (AT population/aging time series + multi-country urbanisation/GDP-pc/CO₂-pc,
  CC BY 4.0), `tools/fetch_geosphere.py` (1991–2020 monthly climate normals per station → Klimadiagramm,
  CC BY 4.0). **8 datasets curated, cross-tagged to serve GWB + MAT (Daten und Zufall) + PHY (Wetter
  und Klima)** — one curated series is discoverable by every subject whose competences it fits. Add a
  source = add a fetch tool; each datum is a reviewable item. Numbers only (licensing-clean); text/
  images are the harder, deferred phase 5.
- **Resolver** (`grounding/data_store.py`): the data twin of `resolve.py`. `resolve_dataref` fills the
  citation from the vetted SourceRef (*overwriting* any hand-written attribution — no faked citations);
  `series_to_spec` maps a series → the recipe's value fields; `relevant_datasets(subject/topic/
  competences)` is the **discovery** query (deterministic, mirrors compose's angle-scoring) so data ⇄
  ideas can interplay; honest gap notes for unknown dataset/series.
- **Data flow is inverted (not bolted on the tail).** The catalog feeds GENERATION: `relevant_datasets`
  + `format_available_datasets` inject the citable datasets into the brief (`tools/breadth_prompt.py`,
  subject-scoped) and the live prompt (`llm/prompts.build_user`, topic/competence-scoped) — so tasks are
  built AROUND real data. At `assemble`, `data_ground.ground_data` then **derives each `data_source`
  figure's values FROM the dataset slice** (overwriting any authored numbers) and stamps the citation.
  This makes *select-never-author* true for numbers — not "author then cite".
- **The invariant `verify` enforces** (`pipeline/figure_lint.py`, the (c)-label gate): every data figure
  (`bar_chart·line·scatter·histogram·population_pyramid`) is exactly one of (b) `data_source` set /
  (c) `illustrative=True`; a real-looking unlabelled figure is a warning. Pure-math figures are exempt.
- **Citations render** purely: `ground_data` (in `assemble`) puts real values + the resolved citation ON
  the content object; `rendering/` prints "Quelle: …" under the figure (student-visible — Quellenkritik
  is curriculum).
- **HITL**: `store/datasetstore.py::DatasetStore` (mirrors `AssetStore`), `orch.ingest_dataset` (gates
  licence: only redistribute under a recorded redistributable licence + attribution) + `seed_datasets`,
  the dashboard **Datensätze** tab (`/api/datasets*`, figure preview, approve/reject), `feedback`
  target kind `dataset`. **Proven end-to-end** by re-grounding GWB **c0094.t2** to a *real, cited
  Bevölkerungspyramide*, then by a **15-worksheet GWB content pass** (`runs/ingest/gwb_data/`, staged
  c0104–c0118, 102 blocks) where subagents wrote data-required Kernfragen across all 8 datasets —
  every figure `data_source`-cited, values derived at assemble, all verify-clean. The full chain held:
  catalog → brief (`relevant_datasets`/`format_available_datasets` inject citable datasets, subject-
  scoped) → subagent declares intent + `data_source` (no authored numbers) → `ground_data` fills real
  values + citation → (c)-label clean → "Quelle: …" renders.

**Where the data layer goes next** (`Documents/feature-roadmap.md`): demand-driven dataset curation
(numbers first — cleanest licensing), Tier-2 regional data (locality), then sourced text/images (phase
5, licence-sensitive). Confirmed source/licence research is in the roadmap's "big bet" section.

## Parametric variants + solution engine (Maths + Chemistry)

The Maths analogue of "correct by construction" extended from the *answer* to the *method*. A
`ParametricTask` (`schema/parametric.py`) = a prompt with `{slots}` + a `recipe` id. Recipes register
like asset generators (`@_recipe` in `pipeline/parametrize.py`) and **own both sampling and solving**
via **sympy**: given a seeded RNG a recipe returns an `Instance` (slot values + the DERIVED answer +
worked `SolutionStep`s). So `make_variants(task, n)` yields **N correct-by-construction variants**, each
deterministic per seed and carrying its **Rechenweg** — the number is computed, never authored (directly
counters the incumbent's "math is wrong" failure). A recipe raises `Unsuitable` to reject a degenerate
draw (non-integer solution) and resample. Seed recipes: `linear_equation`, `percentage`, `fraction_add`.
Curated templates live in `library/templates.py` (anchored to real MAT competences); `variant_worksheet`
wraps N variants into a `WorksheetContent`; `orch.compose_variants(store, template_id, n)` stages it for
Gate-2 review. `TaskBlock.solution_steps` is the canonical worked-solution field (teacher-guide only,
DERIVED — never LLM-authored).

**Inline math** — a `RichText` run with `math=True` carries LaTeX, typeset to a small inline PNG via
mathtext (`rendering/inline_math.py`, the `math_formula` engine) and embedded with ReportLab `<img>`
in `richtext_markup` (so fractions/exponents/roots stop reading as "code-symbols"). `inline_math.configure`
is called once per `build_pdf`; results cache by content hash. A `$…$` span in a parametric prompt
template becomes a math run.

### Chemistry quantitative engine (the same engine, a second domain)

The chemistry twin of the Maths recipes — **same contract, same `_RECIPES` registry**, so
`make_variants` / templates / `compose_variants` drive chemistry unchanged. The facts side mirrors the
data layer: **`grounding/chemistry.py`** is the periodic grounding (curated **IUPAC** standard atomic
weights + a cited `SourceRef`) plus the load-bearing primitive `parse_formula` (handles nesting/hydrates,
`Ca(OH)2` → `{Ca:1,O:2,H:2}`), `molar_mass`, and `subscript` (display H₂O via the renderer's sub/super
normalisation). **`pipeline/chemistry.py`** holds `balance_equation` (the element×species conservation
matrix' **sympy nullspace** → smallest positive integer coefficients; a unique balance ⇔ 1-D nullspace)
and three recipes registered into the shared engine: **`molar_mass`** (M = Σ count·weight, per-element
Rechenweg), **`equation_balance`** (resamples trivial all-1 draws via `Unsuitable`), **`stoichiometry`**
(m→n→mole-ratio→n→m). *Select-never-author for numbers* holds: atomic masses come from grounding, every
result is computed from them + conservation. Templates `che-os-{molmasse,reaktionsgleichung,stoechiometrie}`
(`library/templates.py`) anchor to real **Oberstufe Chemie** competences (Kl. 7, KB *Substanz und Energie*,
dims WO/EG/KZ — **not** W/E/S). **Qualitative recipes (Unterstufe, 4. Kl.)** extend the same idea to
non-numeric tasks that are *still* correct by construction — DERIVED (`reaction_type` from the balanced
structure, `atom_count` from `parse_formula`) or CURATED truth (`substance_classification`,
`separation_method`, `acid_base_neutral` — curated tables in `grounding/chemistry.py`, select-never-author).
Templates `che-us-*` (Kl. 4, KBs *Erkenntnisse gewinnen (E)* / *Standpunkte begründen (S)*, kind
`open_response`). **`make_variants` now guarantees distinct prompts** where the draw space allows (small
finite pools like the qualitative tables would otherwise repeat across independent seeds) — deterministic,
tops up with repeats only if the pool is genuinely < n. Locked by `tests/test_chemistry.py` (parser, molar
masses, balancing, curated-truth correctness, variant distinctness, full assemble→verify→**render** for
both stages). Add an element = one cited row; add a reaction/substance = one curated entry.

## Annotated authentic texts (the Deutsch asset class)

The reading/writing analogue of the data layer (the Deutsch breakthrough). An **`AnnotatedText`**
(`schema/texts.py`) = a real, rights-cleared text + a curated annotation layer. Same discipline as the
data layer: the text is **select-never-author** (an actual PD/licensed text, cited via `TextSourceRef`),
and each task's answer is **derived from a vetted `Annotation`, never authored at task time** (no
hallucinated Erwartungshorizont). `pipeline/text_tasks.build_worksheet(at)` → a `WorksheetContent`: the
text renders as a line-numbered `source_text` block (so tasks reference "Zeile N"), and annotation kinds
map to tasks — `vocab`→Wortschatz scaffold, `comprehension`/`structure`/`stilmittel`/`argument_move`/
`media_technique`→analysis tasks (answer = the annotation), `erwartungshorizont`→an open interpretation/
writing task. "Correct by **curation**" (HITL-vetted), not computation — there's no sympy for German.
One annotated text → many tasks across grades; it compounds like the catalogs.

- **Rights gate** (the other load-bearing piece): `orch.ingest_text` only stages a text on a clear basis
  — `TextSourceRef.is_clear(year)` enforces **PD by the AT 70-Jahre-p.m.a. rule** (not US PD; a PD work
  ≠ a PD scan) or CC. Author death year is captured.
- **HITL**: `store/textstore.py::TextStore` + the **Texte** tab (`/api/texts*`; review text + rights +
  annotations; "Arbeitsblatt erzeugen" = `orch.compose_text_worksheet` → a content item in Inhalte);
  `feedback` target kind `text`. `seed_texts` stages the curated flagships.
- **Curated flagships** (`library/texts.py`): Heine *Die Lore-Ley* (literary — Stilmittel/Interpretation)
  and Lessing *Der Rabe und der Fuchs* (the persuasion/Medienkompetenz angle — the fox's Schmeichelei).
- **Latein reuses the same engine** (the language where it transfers cleanest): the `translation` /
  `grammar` / `culture` annotation kinds (dims SPR/INH → task kinds `translation` · `text_analysis` ·
  `open_response`) drive Übersetzung + Formen/Konstruktion + Inhalt/Kultur. Flagship: Phaedrus *Vulpes et
  Corvus* (the *same* fox-and-flattery fable as the German one). `_serves_for` matches by dimension code
  (`.SPR./.INH./.LES./.SCH.`), so the engine is subject-agnostic.
- **Scaling**: subagents add the annotation layer to a *provided verbatim* PD text → `AnnotatedText` JSON
  → `tools/ingest_texts.py` (validate → rights gate → build → verify → stage); the text is never authored,
  only annotated. A true newspaper/advert media text needs an ANNO/OCR fetch tool (next).
- **Audio / Hörverstehen (modern FS)** — a listening text is an `AnnotatedText` with `medium="audio"`:
  `build_worksheet` attaches a spoken `Asset(role="tts", medium=audio, generator="audio:tts")`, renders a
  printable audio cue + listening tasks (`listening_task`, dim HOR), and makes the transcript **teacher-
  only** (an `oral`-modality `source_text` → dropped on the student sheet; `show_transcript=True` gives an
  A1 listen-and-read variant). Media-policy admits `tts` as a code backend; the transcript is the always-
  present printable fallback. Scripts are **authored-then-vetted** (no PD A1/A2 L2 audio to select).
  Flagship: *Mia's school day* (A2). **The `audio:` backend is now IMPLEMENTED** (full notes:
  `Documents/tts-audio-engine.md`): **F5-TTS multi-voice on the local GPU**. Because CUDA torch has no
  cp314 wheel, the 3.14 core drives a **separate Python 3.12** subprocess — `teachersaid/audio/f5_backend.py`
  (core, no torch) normalizes the spec into dialogue **`turns`**, resolves each turn's `(lang, persona)` to a
  curated voice via `grounding/voice_store.py`, calls `teachersaid/audio/f5_render.py` (the GPU worker,
  *executed* never *imported*), then ffmpeg-encodes mp3. **Voices are selected, never authored:** a rights-
  gated **voice reference library** (`schema/voices.py` · `grounding/voices/` · `tools/fetch_vctk_voices.py`)
  of CC-BY young-adult VCTK clips — the audio twin of the data layer. `register()` wires it; offline it stays
  `AudioNotConfigured` (transcript fallback). Config: `TTS_PYTHON`/`TTS_PYTHON_SITE`/`TTS_FFMPEG`.
- **Realien — CEFR-leveled communicative reading for modern FS (Phase 1 BUILT, `Documents/realien-design.md`).**
  Extends this same `AnnotatedText` engine (no new top-level type). The load-bearing reframe is
  ***purpose-appropriate rigor*:** a Realie is the **Sprechanlass, not the Aussage** — a pretext that
  provokes language, not a world-claim — so the fact-discipline DEMOTES (facts are invented-coherent fiction
  guarded by `pipeline/realie_lint.py`, an *internal-consistency* check — a scan answer can't cite data the
  Realie lacks — NOT world-grounding; **constructed is the default**, no source/rights gate). What stays
  load-bearing is the **language** (L2 correctness + CEFR level, SME-gated) and the *communicative-first* task
  layer: `AnnotatedText` gains `cefr`/`origin`/`scene`/`facts` + optional `source` and the `communicative`
  (write-a-reply) / `roleplay` annotation kinds; the derivation builds a scan warm-up (Lesen) + a boxed
  write task (Schreiben) + a **Sprechkarte** (Sprechen — the new `RolePlayPayload`→`rb.cue_cards`, oral, **no
  write-space**, served via the Lernarrangement interaction anchor). *"Invent the timetable, vet the French."*
  **Two genre flagships** (FS1, A2): `library/realie_bahnhof.py` (*At the station*, a departure board) and
  `library/realie_cafe.py` (*At the café*, a menu — Phase 2a, the **price** path; the lint exempts a *shown*
  sum like "£2.00 + £3.00 = £5.00" but still catches a bare wrong price). Both render as a **real artifact**
  — a paper-tinted `rb.material_card` (no line numbers; `InfoBlock.numbered=False`) — carry atmospheric
  "fluff" (taglines, status, flavour notes) that gives "life" *without touching any datum a task uses*
  (lint-safe by construction; the *constructed* model intact), and ladder the tasks beyond lookup
  (decide-under-constraint · recommend · use the live status — Lever 1; the lint's per-answer universe
  includes the task's own prompt so a stated deadline/budget is consistent). **Phase 2b — the arrangement
  wrap (`pipeline/realie_arrange.py`):** a Realie → a `Lernarrangement` (the worksheet as role material, the
  role-play as the `interaction`, a broader Sprechen competence as a `competence_anchor` served_by the
  interaction — covered ONLY by the anchor, the v0.5 payoff); seeded via `library.seed_arrangements`
  (`realie-bahnhof`/`realie-cafe`). Fact-care snaps back only for **informational** genres. Scales via the
  Phase-3 seam (`realien_prompt`/`ingest_realien`, not yet built).
- **Still trickier / planned** — the audio **HITL "Stimmen" review tab** + `text_tasks` dialogue-**turns**
  emission + **FLEURS** refs/`de/fr/it/es` checkpoints; and a sourced-audio path; see `feature-roadmap.md`
  "Languages" + `tts-audio-engine.md §7`.

## History / expression provenance (the GPB asset class)

The History analogue of the data layer (the **5th asset class**; design: `Documents/history-facts-provenance-
design.md`). Where the data layer tracks *fact* provenance for numbers and `TextSourceRef` tracks *rights*
provenance for whole texts, this adds the third axis — **expression provenance**: *where the wording came
from*. Copyright protects expression, not facts — so a block authored *fresh from facts* (read off Wikipedia)
carries no CC-BY-SA obligation, while a paraphrase/quote of the article's wording does. The load-bearing
reconciliation with *select-never-author*: history prose has no parseable dataset, so it's **correct by
curation** (like the annotated texts), with a **mandatory-internal** twist — an `original` history fact block
MUST record a `role="facts"` source so the fact is fact-checked at the review gate, not asserted unchecked.

- **Schema** (`schema/provenance.py`): `BlockProvenance` on `BlockBase` — `expression_origin ∈
  original·adapted·quoted` + `sources: [ProvenanceSource]` (each `role ∈ facts·expression`). The obligation
  booleans `attribution_required`/`share_alike_applies` are **DERIVED** `@computed_field`s (present in the
  serialization schema for the API, absent from the validation schema so the model can't author them; a
  `mode="before"` validator strips echoed booleans so the JsonStore round-trip stays clean). The generation
  view mirrors `provenance`; `ContentFlags.historical_fact` is the cross-subject opt-in.
- **The invariant `verify` enforces** (`pipeline/prose_lint.py`, the prose (c)-label, advisory/warning-lane):
  **(A)** wherever provenance is present — `adapted`/`quoted` must name a `role="expression"` source, a long
  `quoted` span exceeds Zitatrecht, CC-BY-SA trips ShareAlike; **(B)** scoped to **GPB ∪ `historical_fact`**
  (GPB detected by the served competence-id prefix `GPB.`) — an `original` fact block needs a `role="facts"`
  source, and a fact-bearing InfoBlock (`prose/key_fact/example/source_text`; `callout` exempt) needs *some*
  provenance.
- **Rendering** is a pure projection (`rendering/blocks_to_flowables._provenance_flowables`): student/homework
  get a `Quelle: … Lizenz: …` line **only** when `attribution_required` (`original` renders clean); teacher
  gets the full sources list incl. the `role="facts"` records hidden from students. No new imports — still
  schema-only.
- **Ingest rights gate** (`orch._check_provenance_rights`, run before assemble — the `ingest_text` analogue):
  `BlockProvenance.rights_gate(year)` / `ProvenanceSource.rights_clear(year)` — embedding `adapted`/`quoted`
  needs a CC / explicit-redistributable / **AT-70-Jahre-p.m.a.-PD** basis; a short `quoted` span
  (≤`SHORT_QUOTE_MAX_CHARS=300`) rides the Austrian **Zitatrecht (§42f öUrhG)**. A non-clear block raises →
  nothing staged/harvested. `tools/fetch_wikipedia.py::fetch_source` is the **deterministic, metadata-only**
  source-record helper (a permalink to the exact revision; no article prose, **no LLM in the fact path**).
  The dashboard `prov(b)` panel surfaces provenance for SME fact-checking. **Policy: `adapted` is discouraged**
  (CC-BY-SA ShareAlike can encumber the whole worksheet) — prefer original-from-facts + a short PD quote.
- **Flagship** (`library/gpb_wiener_kongress.py`, `library.seed_history()`): GPB 3. Kl. *Der Wiener Kongress*
  — an original-from-Wikipedia-facts learn text + a real PD primary source (Deutsche Bundesakte Art. I, 1815,
  Wikisource) `quoted` under Zitatrecht, driving *Quellen und Darstellungen unterscheiden*. Staged via the new
  `orch.stage_worksheet` (stage a pre-built curated `WorksheetContent`). The quotation is **selected, not
  authored** (verified verbatim — do NOT fabricate historical wording).

## Sachverhalt — the content / exposition layer (`teachersaid/schema/sachverhalt.py`)

The **third grounding/provenance sibling** (next to the grounded-facts data layer and the annotated
texts; design + decisions: `Documents/sachverhalt-content-layer-design.md`). It closes a *measured*
cross-subject gap — the engine was task-generative and **prose-thin** everywhere, while the Lehrplan's
**Sachkompetenz** pillar demands a didactic *Darstellung* (what happened/works and why it matters). A
**`Sachverhalt`** is a curated module of structured **Sachwissen** about one topic; **one module → three
projections** (the same shape as `WorksheetContent` → student/teacher/homework), so the substance stops
drifting and starts compounding.

The reconciliation with *select, never author* is the **fourth correct-by-construction mechanism**
(`invariants.md` §3, *re-expressed under constraint*): the **facts** (timeline · actors · cause→effect ·
Begriffe) are *selected/sourced* exactly like the data layer's numbers (copyright protects expression,
not facts), and the connective **Darstellung is authored over the *frozen* fact-set** — a projection that
cannot reach back and invent — guarded by a **deterministic entity-lint**. *"Select the facts, author the
expression."*

- **Schema** (`schema/sachverhalt.py`): `Sachverhalt` (id · subject · `klasse_range` · discovery tags ·
  `sources` [role="facts" mandatory] · `sensitive` · `sach_dimension`/`urteil_dimension` hints) + the
  structured facts `HistEvent`/`Actor`/`CausalLink`/`Concept` (+ a **`Process`/cycle** [Bio] · **`Region`** [Geo, → choropleth] fact-type for
  content-heavy sciences, Phase 2) + `bedeutung`/`gegenwartsbezug`/`urteilsfrage`
  + the authored `DarstellungSection`s (`grounded_by` fact keys). Reuses `provenance.ProvenanceSource`/
  `BlockProvenance` wholesale.
- **Derivation** (`pipeline/sachverhalt.py::build_worksheet`, the `text_tasks` twin): Darstellung →
  `InfoBlock`s with a grounded `expression_origin="original"` provenance attached *by construction* (so
  the existing `prose_lint` passes); **DERIVED figures** (timeline ← `timeline`; **Wirkungsgefüge** ←
  `causes` via `matplotlib:cause_effect`; **process/cycle** ← `process` via `matplotlib:process_flow`; **choropleth map** ← `regions` via `matplotlib:choropleth_map`, the
  Phase-2 sibling); and **Sachkompetenz tasks whose
  `answer_key` is COMPUTED from the fact-set** — `chronology` (kind `ordering`) = sort by `at`,
  `cause_effect_match`/`concept_match` = the pairing straight from `causes`/`concepts` (the prompt shows a
  deterministically-reordered list; *no grader engine — the module IS the key*), plus open
  `content_comprehension`/`structure_overview` and an `urteilsfrage`→`position_argument` high-band task
  (a real Anforderungs-spread). New GPB `task_kind_extensions` (`lehrplan/subject_models.json`):
  `cause_effect_match · concept_match · content_comprehension · structure_overview`.
- **The entity-lint** (`pipeline/sachverhalt_lint.py`, the correct-by-construction guard on *authoring*;
  runs at ingest on the `Sachverhalt`, **not** in worksheet `verify` where the fact-set is gone):
  **years are the HARD guarantee** (every 3–4-digit year in the Darstellung must be in the fact-set —
  catches the 1815→1851 garble); **names are ADVISORY** (German capitalises *every* noun, so the English
  "capitalised = name" heuristic is useless — only a multi-word phrase with *no* fact-set token is
  flagged); quoted spans + `grounded_by` are advisory. Numbers are machine-guaranteed; tone/names lean on
  the SME gate.
- **HITL**: `store/sachverhaltstore.py::SachverhaltStore` (mirrors `TextStore`); `orch.ingest_sachverhalt`
  (gate: ≥1 `role="facts"` source + entity-lint clean), `seed_sachverhalte`, `compose_sachverhalt_worksheet`
  (→ a Gate-2 content item); the dashboard **Sachverhalte** tab (`/api/sachverhalte*`, facts/Darstellung
  review + "Arbeitsblatt erzeugen"); `feedback` target kind `sachverhalt`. Registry: `library/sachverhalte.py`.
- **Flagship** (`library/sachverhalt_wiener_kongress.py`): GPB 3./4. Kl. *Der Wiener Kongress*, rebuilt
  **content-first** (Darstellung + timeline + Wirkungsgefüge + 6 Sachkompetenz-Aufgaben) **alongside** the
  method flagship `gpb_wiener_kongress.py` (Quelle ≠ Darstellung). Facts sourced `role="facts"` to
  Wikipedia (the SME fact-checks history + German at the gate; the entity-lint forces every prose date into
  the timeline first). `tests/test_sachverhalt.py` locks schema · verify-clean · the computed answers · the
  figures · render-purity · the entity-lint (clean + catches a planted year) · the store/ingest/seed/API
  loop. **Phase 1 (History) + Phase 2 (Biology + Geography) done.** Two flagships prove the container
  isn't history-locked: the Bio `library/sachverhalt_blutkreislauf.py` (*Der Blutkreislauf*) carries an
  undated **`Process`/cycle** (`matplotlib:process_flow`) instead of a dated timeline; the GWB
  `library/sachverhalt_bundeslaender.py` (*Bevölkerung in Österreichs Bundesländern*, 4. Kl.) carries a
  spatial **`Region`** fact-type → a **choropleth map** + a rank-by-value task. The derivation
  auto-selects the judgment kind (science → core `open_response`; GWB has `position_argument`) and serves
  the subject-correct strands (Bio W/S, GWB OK/UK, via `sach_dimension`/`urteil_dimension`/`urteil_competence`).
  **The map is correct-by-construction on BOTH axes:** the **boundaries** are a sourced CC-BY GeoJSON — the
  new **geo layer** (`grounding/geo/` + `grounding/geo_store.py`, fetched by `tools/fetch_geo_boundaries.py`,
  the spatial twin of the data layer; *boundaries are facts* — licence-gated, attributed) — and the **fill
  values** come from the cited population dataset (`ground_data` fills them at assemble via the new
  `_series_spec` choropleth case). `matplotlib:choropleth_map` is a first-class data figure (in
  `figure_lint`'s (c)-label set; pure matplotlib `PathPatch` with even-odd holes for the Wien-in-NÖ enclave,
  latitude-corrected aspect — **no geo dependency**).
- **Phase 3 — subagent scaling (the breadth seam, no API key).** The content-layer twin of the worksheet
  breadth pattern: `tools/sachverhalt_prompt.py` writes a per-topic grounded brief (real competences for the
  grade · the fact-type block timeline|process · the load-bearing dimension hints · the every-prose-year-must-
  be-a-timeline-event rule · a fact-type-shaped JSON example); a subagent authors one `Sachverhalt` JSON;
  `tools/ingest_sachverhalte.py` (the `ingest_batch` twin) **normalizes the recurring agent slips** (German-quote
  repair · stray keys vs `extra="forbid"` · `klasse_range` int→range · source `role`→`facts` · off-enum causal
  `kind`→`folge` · authored section `provenance` stripped), then JSON→schema→**facts gate**→**entity-lint**→
  `build_worksheet`→`assemble`→`verify` and stages via `orch.ingest_sachverhalt`+`compose_sachverhalt_worksheet`
  — **only if clean** (a bad year / missing facts source surfaces here, never silently). **First push:** 4
  subagent-authored Sachverhalte — GPB *Französische Revolution* & *Industrialisierung* (timeline), BIO
  *Photosynthese* & *Verdauung* (process) — Wikipedia-sourced, every prose year backed by a timeline event,
  verify-clean with zero entity-lint warnings, staged `in_review` (`runs/`, git-ignored). The facts are
  *selected/sourced*, the Darstellung *authored-then-vetted*; the SME fact-checks at the gate.
  `tests/test_ingest_sachverhalte.py` locks the normalizer + the facts gate + the entity-lint offline.

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
`POST /api/compose` (accepts `topic` and/or `kompetenzbereich`). **No optimizer**, but selection is
now angle-aware (3b) and **difficulty-calibrated** (3d), and an **optional LLM framing pass** (3e,
`pipeline/frame.py`, used by `orch.compose_worksheet` when a key/generator is available) writes a coherent
Kernfrage + intro + per-task transitions AROUND the vetted blocks (tasks untouched → no-drift; offline ⇒
the template framing stands). A composed sheet is a `WorksheetContent`, so rendering is unchanged.

**Phase 3 progress** (see `Documents/block-library-design.md §8`): **3a** (scope/richness variants),
**3b** (angle-aware composition), **3c** (assets travel with blocks), **3d** (difficulty calibration), and **3e** (coherence/LLM framing)
are built — **all Phase-3 composer refinements done.** *3e:* an optional LLM pass (`pipeline/frame.py`,
graceful no-op offline) writes a coherent Kernfrage + orienting intro + a one-line lead-in before each
task, purely as connective framing around the fixed blocks — no new tasks/facts, vetted task content
untouched. *3d:* an honest, never-measured `difficulty` (1–3,
author/SME estimate; `pipeline/difficulty.py`) — when unset, derived from the cognitive level's
Anforderungsbereich (Reproduktion 1 / Transfer 2 / Reflexion 3). Surfaced in `DepthProfile.by_difficulty`,
warned on when flat (verify), and used by `compose` to **seed one block per band** so a tight budget spans
easy→stretch instead of greedily filling from the easy end. *3a:* `compact`/
`standard`/`extended` siblings share a `family`; the composer picks the variant matching the envelope
(einzelstunde→compact … block→extended), so envelopes differ in depth. Produce variants via
`orch.ingest_scope_variant` + `tools/scope_variants.py`. *3b:* competences fix WHICH blocks are eligible;
the requested **topic/Kernfrage is the angle** that picks among them — `compose` scores each block by
deterministic term overlap (no LLM; angle = topic minus the KB's own words) and prefers on-angle blocks,
so two Kernfragen on one Kompetenzbereich compose **different** sheets (empty/echoes-KB angle ⇒ the old
cognitive ordering, unchanged). *3c:* `LibraryBlock` carries its `Asset` spec(s); `harvest` captures them;
`compose` aggregates the chosen blocks' assets so figures (e.g. the Strahlung spectrum) render in composed sheets.

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
the sheets; ENT.05 via the debate, ENT.01 via the council decision as anchors). **Phase 5 COMPLETE (5a–5d):**
schema + derive/assemble/verify + the hero + the run-guide renderer + the dashboard review surface
(`store/arrangementstore.py`, `orch.stage_arrangement`/`seed_arrangements`, the **Arrangements** tab,
`/api/arrangements*`) + **generation** — `GenArrangementBody`→`arrangement_body_to_canonical`,
`arrange.ingest_arrangement` (the v0.5 analogue of `ingest_generated`); briefs `tools/arrangement_prompt.py`,
ingest `tools/ingest_arrangements.py` (reuses the worksheet normalizer on each role's `material`). **First
push:** 4 subagent-generated arrangements (GPB NATO/Neutralität debate, DEU Handyverbot Streitgespräch, GWB
EU jigsaw, FS1 English class-trip simulation), verify-clean, staged `in_review` (`runs/`, git-ignored).

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
- **Run to date (26 Jun 2026):** all 16 subjects → **73 worksheets / ~477 blocks**, verify-clean, staged
  `in_review` for SME approval. **GWB completed to all 14 Kompetenzbereiche** (the 8 gap KBs, +9 worksheets:
  per-grade subagent briefs from `tools/breadth_prompt` machinery, **Tier-1 local anchoring** — students
  investigate their own region, no asserted local facts — and **intent-declared figures**; verify-clean with
  zero chart-lint warnings). The run doubled as a figure stress test: it cleanly surfaced two missing geography
  recipes — **population pyramid** and **Klimadiagramm (dual-axis temp-line + precip-bar)** — which the agents
  approximated honestly and flagged rather than faked. Feasibility lesson: subagent *content* is excellent; the
  constraint is JSON well-formedness, handled by the normalizer (structured output would remove that class at scale).

## HITL dashboard (`api/` + `api/static/index.html`)

Two review gates, one `ReviewItem` type (`stage` ∈ **brainstorm** | **content**); ten tabs
(Brainstorm · **Bausteine** · Inhalte · Bibliothek · **Arrangements** · **Abbildungen** ·
**Datensätze** · **Texte** · Statistik · **Insights** — see the Block library section below). **Datensätze**
reviews grounded-facts datasets (`DatasetStore`): source/licence/Stand + a figure preview, approve/reject
(see the Grounded facts & data layer section). **Texte** reviews annotated authentic texts (`TextStore`):
text + rights + the annotation layer, approve/reject + "Arbeitsblatt erzeugen" (see the Annotated texts section). **Abbildungen** is the asset-review surface (Phase 4
#2/#4): file-backed library assets (decorative/sourced, with approve/reject) on top, and below, every
code-generated content figure rendered inline (deduped by generator+spec, built on demand) for
fächerübergreifende review. **Arrangements** (Phase 5c) reviews Lernarrangements (`ArrangementStore`): the
run-guide + each role's student/teacher PDF (Vorschau) and a structural view (phases · roles · shared product
· anchors · Nachweis), approve/reject. (Arrangements use their own store, not `ReviewItem`.)

**Rich feedback loop (`store/feedbackstore.py`).** Beyond approve/reject, every review surface (block ·
worksheet item · arrangement · asset · dataset) carries a feedback panel — a **rating (1–5) + free comment + quick
tags** — **decoupled from the decision** (you can rate/comment without approving, so partial review still
accrues signal). It's ONE central append-only store keyed by `(target_kind, target_id)` (not a field on each
model), so `FeedbackStore.digest()` is a single read. The **Insights** tab renders that digest — a priority
"zu überarbeiten" worklist (low-rated / revise-flagged / Sachfehler), tag frequencies, per-subject averages,
and what's working — which the AI consumes between sessions to drive refinement. "Mit Feedback überarbeiten"
on a worksheet reuses `request_changes` (regenerate with the comment as the note); on other kinds it carries a
`revise` flag into the digest. API: `POST /api/feedback`, `GET /api/feedback?target_kind&target_id`,
`GET /api/feedback/digest`, `GET /api/feedback/tags`.

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

- **All stores subclass `store/base.py::JsonStore`** (shared file-I/O + sequential-id counter +
  status-preserving `upsert`). Add a store by setting `model` + `subdir` + a typed `list()`, **not** by
  copy-paste. Library stores (Block/Asset/Arrangement/Dataset) use `upsert`; Review uses `create`;
  Feedback is append-only `add` — each keeps its lifecycle on the same base. This is the seam a future
  SQLite backend swaps behind (see `Documents/architecture-review.md`).
- **`Baustein` lives in `schema/worksheet.py`**, not `schema/blocks.py` (easy import slip).
- In rendering, use `rb.para(value, style)` for RichText (escapes); use `rb.raw_para(markup, style)` when
  you've **already built** inline markup (don't double-escape — that prints literal `<b>` tags).
- Carlito (or Calibri, its metric twin) is used if found — `_register_fonts` searches Linux **and
  Windows** font dirs; else Helvetica fallback (the demo renders anywhere). **Subscripts/superscripts
  (CO₂, m²) don't depend on the font:** `richtext_markup` normalises sub/super Unicode → ReportLab
  `<sub>`/`<super>` markup over the plain digit, so they render correctly even in Helvetica (which has no
  ₂ glyph → was a tofu box before).
- PDF→PNG QA uses **PyMuPDF** (`fitz`), not `pdftoppm` (no system poppler dependency).
- **Text fitting is measured, not guessed (legibility discipline — the layout analogue of the lints).**
  *Tables:* `rb.grid_table` wraps every cell in a Paragraph and its `weights` sum column widths to the
  frame — so content **can't overflow a cell** (it grows vertically). Never hand a raw string to a ReportLab
  `Table` (it won't wrap → overflow); route content through `grid_table`/`wrapped_table`. *Figures:*
  `pipeline/figtext.py` is the shared *measure → fit → de-collide* helper — recipes **measure** label extent
  (`measure_widths`) instead of a magic `textwrap` count; the **timeline lane-packs** measured labels (year
  folded into each, no colliding axis ticks) and the **choropleth** font-fits big regions and **leaders tiny
  enclaves out** (Wien below the map). *The lint:* `figtext.overlap_pairs(fig)` + `tests/test_layout.py`
  assert no label overlaps (per axes) and no table exceeds the frame — so legibility regressions are caught,
  not eyeballed. A leader is two artists (a line + a plain `ax.text`), **not** an arrow-annotation, so a
  label's measured bbox is the text alone.
- **A task's affordance is its kind, not a separate field (didactic discipline).** A *self-contained*
  payload IS its own response surface — `ordering` (numbers in `____` blanks) · `matching` (draw lines on
  `rb.connect_blocks` loose blocks) · `multiple_choice` (tick-boxes) — so `_task_flowables` adds **no**
  generic write-space for those (`blocks_to_flowables._SELF_CONTAINED_PAYLOADS`); `true_false_justify` is
  NOT one (its justification needs lines). Don't pair an ordering/matching task with a `LinesResponse` and
  expect lines — the renderer suppresses them by construction. Likewise generated **prompts** fit the
  topic's nature, not one template: the Sachverhalt `content_comprehension` close reads "warum war X
  wichtig" for a `timeline` (event), "wie X abläuft" for a `process`, "was die Karte zeigt" for `regions`.
- Match the surrounding German tone/terminology in product-facing strings; the user is the domain SME
  (physicist, Austrian) and fact-checks the physics and the German.
- Don't relitigate decisions recorded in `project-handoff.md §4`; they are durable.

## Where to look first

`project-handoff.md` (intent) → `Documents/lehrplan-bundle-schema-v0.3.md` (data model) →
`teachersaid/schema/` (the model in code) → `teachersaid/pipeline/` (the engine) →
`teachersaid/demo/strahlung.py` (a complete worked content object).

**What's next / forward-looking features:** `Documents/feature-roadmap.md` — the prioritised capability
backlog (figure-recipe families · audio · parameterized variants · the **grounded facts & data layer**
big bet, with confirmed Austrian data + media sources). Has a "Start here tomorrow" section at the top.
