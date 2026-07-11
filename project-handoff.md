# Project Handoff — Austrian Lehrplan-anchored Teaching-Material Generator

**Status: design baseline from Session 2 (24 June 2026); see the dated session updates below for the
current state (latest: Session 14, 5 July 2026 — Wave A built end-to-end: task & figure engines, 565 tests green).** This is the single read-me-first document for a fresh
session taking the project over. Working language is English; the *product's* output is German (or a
target language for Fremdsprache). Read this, then the docs in the order given in §6.

> **Update (Session 3, 25 June 2026): the design is now a working, populated system.** Everything below
> describes the *design*, which remains the source of truth for intent — but the "engine / UI deferred"
> statements in §3, §7, §8 are **superseded**. What now exists (see **[CLAUDE.md](CLAUDE.md)** for the
> codebase guide, **[Documents/implementation-notes.md](Documents/implementation-notes.md)** for the
> design↔code map):
>
> 1. **Engine + dashboard** — the `teachersaid/` Python package: resolve→plan→generate→verify→assemble
>    (+derive Nachweis/DepthProfile)→render pipeline, pure ReportLab projections, a two-stage HITL review
>    dashboard. ~52 offline tests.
> 2. **Grounding** — the full **16-subject Unterstufe catalog** (`lehrplan/`, ~571 verbatim competences)
>    wired into the engine.
> 3. **Block library** — the master-library unit is the **block** (not the worksheet); worksheets are
>    *compositions* of blocks. A **composer** (`pipeline/compose.py`) assembles approved blocks for a
>    Kompetenzbereich + time-envelope. (Design: [Documents/block-library-design.md].)
> 4. **Projection audience split** — student/homework sheets carry only student-facing content; the
>    teacher guide is a *guide* (expected answers + talking points + extensions, no write-space).
> 5. **Breadth library — generated AND SME-approved** — **64 worksheets / 425 blocks** across **all 16
>    subjects** (incl. Englisch/Französisch/Latein), produced by subagent generators, validated through the
>    real seam (`orch.ingest_generated`; tooling `tools/breadth_prompt.py` + `tools/ingest_batch.py`), and
>    all approved by the SME (catalog coverage ~33%). Generated content lives in `runs/` (git-ignored).
> 6. **Phase-3 composer refinements — 3a + 3c built.** *3c:* assets travel with blocks (figures render in
>    composed sheets). *3a:* scope/richness variants — `compact`/`standard`/`extended` siblings in a
>    `family`, so an envelope picks the matching depth (einzelstunde→compact … block→extended); seam
>    `orch.ingest_scope_variant` + `tools/scope_variants.py` (demoed on Physik *Strahlung*).
> 7. **Phase 4 — assets — COMPLETE (26 June 2026).** A pluggable, spec-driven **code-generator library**
>    (`pipeline/assets.py`; generator id `<backend>:<recipe>`; `matplotlib:` content recipes + `svg:`
>    decorative kit; `diffusion:` seam for the SME's image-gen agent — see
>    **[Documents/diffusion-handover.md]**), **math-as-asset** (mathtext), asset-bearing generation re-enabled,
>    a **`MediaPolicy` entry-gate** (`pipeline/media_policy.py`, runs in `verify`: content→code-gen/sourced,
>    decorative→content-free), an **asset library** for the file-backed classes (`store/assetstore.py`,
>    parallel to the block library), and the dashboard **Abbildungen** asset-review tab. Roadmap +
>    product principle: [Documents/schema-roadmap-v0.4-v0.5.md].
>
> 8. **Phase 5 (Lernarrangement v0.5) COMPLETE + all Phase-3 carry-overs (3a–3e) done (26 June 2026).**
>    The v0.5 sibling object ships end-to-end: schema → the GWB Gemeinderat-Planspiel hero →
>    `renderTeacherOrchestration` → dashboard **Arrangements** tab → generation (`ingest_arrangement`; a first
>    subagent push of 4 arrangements). Composer refinements 3a–3e are all built (angle-aware + difficulty-
>    calibrated selection + an optional LLM framing pass).
>
> **Where to pick up next (fresh session):** the engine is feature-complete through v0.5; the live frontiers
> are **HITL review of the staged library** (the breadth worksheets, figure worksheets, scope-variants,
> decorative assets, and arrangements all sit `in_review` in the dashboard) and the **content-figure diffusion
> experiment** (brief at [Documents/diffusion-figures-handover.md] — gauge the hallucination rate, then build
> the vetting lane). The **2026/27 Fassung refresh** (§2) is **intentionally deferred**: the next Fassung
> arrives with the new school year and is expected to be a tiny increment; it becomes a real task only when new
> *foundational* guidelines are published in full text (not yet available). No `ANTHROPIC_API_KEY` needed —
> generation runs via subagents. Run: `pip install -e ".[dev]"`, `python -m pytest -q` (98 tests),
> `python -m teachersaid` (dashboard).
>
> **Update (Session 4, 27 June 2026): two big capabilities shipped — the grounded-facts data layer and
> the parametric Maths engine.** See **[CLAUDE.md](CLAUDE.md)** (sections "Grounded facts & data layer"
> and "Parametric variants + solution engine") and **[Documents/architecture-review.md]** (the no-rewrite
> verdict + the 3 sequenced moves).
>
> 1. **Grounded facts & data layer** — the SME-championed "big bet" (now built): generalises grounding from
>    *competences* to *facts*. `schema/datasets.py` (`SourceRef`/`DataRef`/`Dataset`); `grounding/data/`
>    catalog written by **deterministic, LLM-free fetch tools** with per-source licence checks
>    (`tools/fetch_{statistik_austria,worldbank,geosphere}.py`) — **8 curated CC-BY datasets**. The flow is
>    *inverted*: the catalog is discoverable (`data_store.relevant_datasets`) and feeds generation briefs, and
>    `data_ground.ground_data` (in `assemble`) **derives each figure's values from the dataset slice** so
>    *select-never-author* holds for numbers, not "author-then-cite". `figure_lint` enforces the (c) sourced-vs-
>    illustrative label in `verify`; "Quelle: …" renders. HITL **Datensätze** tab. New figure recipes:
>    `population_pyramid`, `timeline`, `climate_diagram`. **Proven** by a 22-worksheet GWB/MAT/PHY content pass.
> 2. **Parametric Maths engine** — `schema/parametric.py` + `pipeline/parametrize.py`: a `@_recipe` registry
>    (sympy) where each recipe owns sampling + solving → N **correct-by-construction** variants, each with a
>    derived worked **Rechenweg** (`TaskBlock.solution_steps`). 10 curated templates across all four MAT KBs
>    (`library/templates.py`); `orch.compose_variants` stages a variant sheet. **Inline math** (a `math`
>    RichText run → inline mathtext PNG) ends the "fractions as code-symbols" look. Adds **sympy** as a dep.
> 3. **Architecture review (no rewrite):** the `blocks→content→rendering` discipline held; the only structural
>    cleanup done was consolidating the 6 stores onto one `store/base.py::JsonStore` (the future-DB seam).
>    SQLite is deferred until a trigger fires (slow listing / cross-entity queries / multi-user).
>
> **Pick up next:** more parametric recipes + a "Varianten erzeugen" dashboard surface; the **geometry/
> construction recipe family (KB3)** — the biggest remaining Maths coverage gap; more datasets for other
> subjects (re-ground the old invented-number figures the (c)-label flags); **audio** (the unserved
> Hörverstehen modality) as the next strategic, design-first track. Run: `python -m pytest -q` (149 tests).
>
> **Update (Session 5, 27 June 2026): the Deutsch asset class — annotated authentic texts — shipped.**
> The reading/writing analogue of the data layer: an **`AnnotatedText`** (`schema/texts.py`) = a real,
> rights-cleared text + a *curated annotation layer*; `pipeline/text_tasks.build_worksheet` derives a
> worksheet whose task answers come FROM the vetted annotations (correct by curation, never authored), with
> the text rendered as a line-numbered `source_text` block. A **rights gate** (`orch.ingest_text`,
> `TextSourceRef.is_clear`) enforces AT 70-Jahre-p.m.a. / CC. HITL: `TextStore` + the **Texte** tab
> (`/api/texts*`, "Arbeitsblatt erzeugen") + feedback kind `text`. Flagships (`library/texts.py`): Heine
> *Die Lore-Ley* (literary) + Lessing *Der Rabe und der Fuchs* (Medienkompetenz/Schmeichelei); a subagent
> annotation pass + `tools/ingest_texts.py` proved scaling (Grimm *Der süße Brei* staged). The key insight:
> the Deutsch Lehrplan integrated grammar/orthography into the other KBs (no drill-block to chase) — the
> real demand is authentic-text reading, media analysis, and source-based writing. 159 tests.
> **Pick up next (Deutsch):** an **ANNO/OCR fetch tool** for real newspaper/advert media texts; more
> annotated texts across grades; an optional LLM phrasing pass over derived questions.

> **Update (Session 6, 28 June 2026): the Oberstufe (Sek II) expansion begins — foundation + first build.**
> The handoff's "Oberstufe is largely legacy prose → deferred" is **superseded**: the consolidated
> Lehrplan organises the Oberstufe into **semesterised Kompetenzmodule (KM 3–7)**, fully competence-
> oriented (Physik even reuses the exact W/E/S model). Roadmap + opportunity map:
> **[Documents/oberstufe-roadmap.md]** (output of a 5-cluster subagent brainstorm over the whole
> Oberstufe Lehrplan). SME decisions recorded there: mirror the Lehrplan's own dimensions (not the
> Reifeprüfung Grundkompetenzen-Katalog); the **dilemma asset class is general-purpose** (cross-curricular);
> curated-code execution (Informatik) is OK.
>
> 1. **Phase 0 — the enabler (DONE).** A new parser `tools/parse_lehrplan_oberstufe.py` → the **Oberstufe
>    catalog** `lehrplan/oberstufe/<CODE>.json` (18 subjects, ~1360 competences) with a typed
>    `descriptor` (grade-independent Kompetenzmodell competences) / `lehrstoff` (per-semester
>    Inhaltsbereiche, carrying klasse+Semester+Kompetenzmodul) split; `tools/build_oberstufe_meta.py` →
>    `lehrplan/oberstufe/_meta.json` + `subject_models.json` (curated per-subject dimension models —
>    incl. Chemie's **WO/EG/KZ**, not W/E/S). The engine is now **stage-aware**: `grounding/lehrplan_store.py`
>    takes a `stufe` (default Unterstufe), `stufe_for_klasse` drives it (1–4 US, 5–8 OS); `ResolvedCompetence`
>    gained `semester`/`kompetenzmodul`/`kind`; `resolve` drives the stage from Klasse and `resolve_grade`
>    takes `kompetenzmodul`/`semester` filters. Unterstufe untouched.
> 2. **Phase 1 — Mathematik parametric pack (DONE).** 6 sympy recipes covering all 4 Inhaltsbereiche
>    (Kurvendiskussion, bestimmtes Integral, LGS 2×/3 Variablen, Binomialverteilung, Skalarprodukt+Winkel)
>    + 6 curated templates (`mat-os-*`) serving real OS competences; correct-by-construction, renders
>    SME-clean. **mathtext gotcha**: matplotlib mathtext is a LaTeX subset — `\leq` not `\le`, `\binom`
>    for column vectors (no `\begin{pmatrix}`/`{cases}`), avoid `ℝ` in plain-text titles.
> 3. **Breadth push (in progress).** `breadth_prompt.py`/`ingest_batch.py`/`orch.ingest_generated` made
>    stage-aware; subagents generate Oberstufe worksheets per subject → `runs/ingest/gen_os/` →
>    `ingest_batch` stages them `in_review` for SME review (the Unterstufe breadth pattern).
>
> **Infra (this session):** the repo was cloned to a second PC (offline phase, no API key); the
> git-ignored generated content (`runs/`) syncs between PCs via **Google Drive** (not GitHub). The
> **audio/F5-TTS backend can't run on this PC** (no CUDA GPU + Windows Smart App Control blocks torch) —
> audio stays on the workhorse PC. Run: `python -m pytest -q` (**216 tests**).
>
> **Update (Session 7, 29 June 2026): Matura orientation + the full SRDP-archive build.** The Matura
> (SRDP) was adopted as the competence-model **horizon that shapes the ladder** — harvested as
> **grounding, not a new asset class** (the rule + write-up: **[Documents/matura-operators.md]**).
> What shipped:
> 1. **SRDP Operatoren grounding** (`grounding/operators.py`) — 4 authoritative CC-BY operator catalogs
>    (Deutsch/GWB/Naturwiss./Mathematik+AMT), injected into the generation brief; *select, never author*.
>    **#1 calibration done** ([Documents/matura-calibration.md]): the cognitive_level→AFB→difficulty model
>    holds (no change); real exams run ~70/25/5 across AFB 1/2/3, validating the `DepthTarget` philosophy.
> 2. **Full-archive build** (the home-PC TODO, now closed): `tools/fetch_matura.py` (downloads the TYPO3
>    *tx_downloads*+Solr archive — per-collection `cHash` scraped, CC-BY manifest), the **subject-aware**
>    `tools/extract_matura.py` (Math/AMT · Deutsch · Latein · modern languages — sciences/GWB have no
>    Klausur archive, oral), and `tools/matura_demand.py` (per-subject demand maps). Corpus → `runs/matura/`
>    (git-ignored, Drive-synced). Ran 151 collections → **[Documents/matura-{math,deutsch,latein,languages}-
>    coverage.md]** (the *Matura-backward design* spec: mine the endpoint, build the scaffolded path earlier).
> 3. **Accessible-edition figure scan → 2 new recipes.** The Blindheit/Sehbehinderung Math editions
>    linearise the vector math (real numbers/formulas) + describe figures in words; scanning them surfaced
>    two WS-strand figure types with no recipe — now built correct-by-construction: **`matplotlib:boxplot`**
>    (new `spread` intent) + **`matplotlib:tree_diagram`** (Baumdiagramm).
>
> **Infra:** all on `main` (pushed). The home network reaches matura.gv.at (the remote session's egress had
> blocked it). Run: `python -m pytest -q` (**265 tests**).

> **Update (Session 8, 30 Jun 2026): the Sachverhalt content/exposition layer — Phase 1 shipped.** The
> measured gap (the engine is task-generative and prose-thin everywhere, while the Lehrplan's
> **Sachkompetenz** pillar demands a didactic *Darstellung*) is closed for History via the **fourth**
> correct-by-construction mechanism — *re-expressed under constraint* (`Documents/invariants.md` §3): the
> facts (timeline · actors · cause→effect · Begriffe) are selected/sourced like the data layer's numbers,
> and the connective **Darstellung is authored over the frozen fact-set**, guarded by a deterministic
> **entity-lint** (every year in the prose must be in the fact-set — years are a hard guarantee; names are
> advisory, since German capitalises every noun). One `Sachverhalt` → three projections (Darstellung ·
> DERIVED timeline + a new `matplotlib:cause_effect` Wirkungsgefüge · Sachkompetenz tasks whose answers are
> **COMPUTED** from the facts). Built end-to-end: `schema/sachverhalt.py`, `pipeline/sachverhalt{,_lint}.py`,
> the GPB Sachkompetenz task kinds, the *Der Wiener Kongress* flagship (alongside the method flagship), and
> the full HITL surface (`SachverhaltStore` · ingest/seed/compose · `/api/sachverhalte*` · the
> **Sachverhalte** tab · feedback kind). See `CLAUDE.md` "Sachverhalt" + `Documents/sachverhalt-content-
> layer-design.md` (Phase 1+2 BUILT). **Phase 2 (same session) — the container generalises to Biology:**
> *Der Blutkreislauf* added a `Process`/cycle fact-type (the undated sibling of the timeline → a
> `matplotlib:process_flow` cycle figure + a process-ordering task), with W/S strand-correct anchoring and
> the judgment kind auto-selected (Bio → core `open_response`). **Geography (same session) — the 3rd
> subject + the first MAP:** the GWB flagship *Bevölkerung in Österreichs Bundesländern* added a spatial
> `Region` fact-type → a correct-by-construction **choropleth** (`matplotlib:choropleth_map`); the map's
> **boundaries** are a sourced CC-BY GeoJSON (the new geo layer `grounding/geo/` + `geo_store.py` +
> `tools/fetch_geo_boundaries.py`, *boundaries are facts*) and its **values** the cited population dataset —
> both cited on the figure, no geo dependency. Run: `python -m pytest -q` (**315 tests**). **Next:** Phase 3
> — subagent scaling (`tools/ingest_sachverhalte.py`).

> **Update (Session 10, 1 Jul 2026): the figure engine — a styleguide + a composable scene engine.**
> Design + full guide: `Documents/figure-styleguide.md` (+ a new `CLAUDE.md` subsection). Two problems were
> separated and fixed: figures looked the same (palette hard-coded in ~25 recipes) AND couldn't be composed
> (monolithic recipes).
> - **`pipeline/figstyle.py` — the styleguide.** One source of truth: **semantic colour ROLES** (colour
>   MEANS something — `focus` is *always* the unknown/result/region of interest), a **categorical hue ramp**
>   (multi-series stops using matplotlib defaults) and a **dash ramp** (`DASHES`/`line_kind` — a hue+dash
>   PAIR per family, *redundant* so a dense figure survives a **black-and-white photocopy**), a type scale,
>   and the **document font** matched to the worksheet body (Carlito/Calibri, not DejaVu — figures stop
>   reading as "pasted in"). `house_rc()` scopes it (the scene renderer uses it); `use_house_style()` is the
>   global apply for the eventual **port** of the legacy recipes.
> - **`pipeline/scene.py` — the scene engine.** A figure as data: a `Scene` = `Canvas` + ordered typed
>   layers (`Polyline·Line·PointMark·CircleShape·Arc·Region·Label`), one `render_scene`. A rich figure is
>   **composed** from primitives, not written as a new recipe, and the SAME scene renders at different
>   **densities** (a step-by-step construction worksheet from one computed object). **Two-tier** like
>   `choose_representation`: the LLM never authors a Scene; a **didactic recipe COMPUTES** it.
> - **First recipes (correct-by-construction; value labels maskable → task/solution split):**
>   `pipeline/constructions.py::triangle_construction` (the *merkwürdige Punkte des Dreiecks* — Umkreis/
>   Inkreis/Schwerpunkt/Höhenschnittpunkt/Eulergerade/Feuerbachkreis, all from 3 vertices; `stage` 1–6) and
>   the `pipeline/calculus.py` **analysis family** via **sympy** (`tangent_slope`/`definite_integral` the
>   tested core): `function_plot·integral_area·tangent·riemann_sum·extrema·area_between·distribution`.
> - Run: `python -m pytest -q` (**368 tests**; `tests/test_scene.py`+`test_calculus.py` lock geometry
>   properties + computed values vs ground truth). **Next candidates:** port the ~25 legacy recipes to
>   `figstyle`; more scene recipes (physics vectors, annotated "label-the-parts" diagrams); a density/stage
>   selector on scenes.

> **Update (Session 9, 30 Jun 2026): Sachverhalt Phase 3 + a NEW asset class (Realien) + a persistence
> policy change.**
> - **Sachverhalt — Phase 3 (subagent breadth) DONE.** `tools/sachverhalt_prompt.py` (grounded brief) +
>   `tools/ingest_sachverhalte.py` (normalizer · facts-gate · entity-lint, the `ingest_batch` twin); first
>   push = 4 verify-clean modules (GPB *Französische Revolution*/*Industrialisierung* timeline, BIO
>   *Photosynthese*/*Verdauung* process). The content layer is built P1–P3.
> - **Realien — CEFR-leveled *communicative* FS reading, a new asset class, BUILT P1–P3**
>   (`Documents/realien-design.md`; extends the `AnnotatedText` engine). The load-bearing reframe is
>   **purpose-appropriate rigor**: a Realie is a *Sprechanlass, not an Aussage* — a pretext that provokes
>   language, not a world-claim — so the fact-discipline DEMOTES (facts are invented-coherent fiction guarded
>   by an *internal-consistency* lint `pipeline/realie_lint.py`, NOT world-grounding; **constructed is the
>   default**, no source/rights gate), and what stays load-bearing is the **language** (L2 + CEFR level,
>   SME-gated) and the **communicative-first** task layer (scan · write · a `RolePlayPayload` **Sprechkarte**,
>   oral). Built: the schema extension + `rb.material_card` (a Realie renders as a real-artifact card, no line
>   numbers) + the derivation + the lint + **8 Realien** (EN FS1 + FR FS2, A1+A2, 8 genres) with atmosphere +
>   a reasoning task ladder; the **arrangement wrap** (`pipeline/realie_arrange.py` — speaking as a
>   `competence_anchor` served by the interaction, the v0.5 payoff); the **breadth seam**
>   (`tools/realien_prompt.py` + `tools/ingest_realien.py`). *"Invent the timetable, vet the French."*
>   **DEFERRED by decision:** the *informational*-genre half (news-in-levels / factual texts where fact-care
>   snaps back — sourced or dataset-grounded; licence-sensitive).
> - **Persistence policy changed (`.gitignore`).** `runs/` is no longer wholesale-ignored: **git owns the
>   generated content + review state** (`runs/**/*.json|.md|.txt` — small, diffable, not regenerable for
>   subagent work, so remote-session output survives in git) and **ignores only the rendered binaries**
>   (PDF/PNG — large, rebuildable). Same split as `grounding/voices`. Run: `python -m pytest -q`
>   (**350 tests**). **Next candidates:** SME gate-review of the staged content; informational Realien
>   (when ready); or a fresh track.

> **Update (Session 11, 2 Jul 2026): THE OFFLINE-FIRST PIVOT — the product is the corpus; delivery is
> LLM-free.** A full fresh-eyes review of the system (369 tests green; layering verified mechanically;
> hero + generated artifacts inspected page-by-page) surfaced two decisive facts: the live-generation
> path had **zero production mileage** (every artifact came through the subagent/campaign seam), and
> live on-demand delivery is **structurally incompatible with the human-final-gate decision** (a
> live-delivered sheet is by definition un-gated). The SME confirmed the pivot — it extends his own
> 26 Jun product principle (*"the platform consolidates a human-vetted library, it does not
> live-generate"*) from assets to the whole product. Recorded durably: §4 below ·
> `Documents/invariants.md` **§10** · `Documents/feature-roadmap.md` (the program) ·
> `Documents/platform-definition.md` (thesis reframe).
>
> - **Two loops.** The **corpus loop** (offline, campaign-shaped: Lehrplan gaps + demand queue → grounded
>   briefs → LLM/subagent generation through the feature engines → lints → SME gate → approved corpus) is
>   where the LLM lives; cost is campaign capex, not per-request opex. The **delivery loop** (what a
>   teacher touches) is **deterministic and LLM-free**: request (topic × Klasse × envelope × scope) →
>   serve a vetted worksheet › compose from approved blocks › **honest gap** into the demand queue →
>   render. Long-tail wishes are fulfilled **async** through the corpus loop (request → campaign → gate →
>   deliver), never live. Deterministic runtime generation (parametric variants, scene stages/densities)
>   stays at delivery — computed, hence gate-cheap: infinite variants at zero marginal review cost.
> - **Why.** AHS demand is a **closed, parsed set** (~571 US + ~1360 OS competences) — coverage is
>   *computable*, so "a corpus that fits any AHS topic" is a finite program with a progress bar, not a
>   content treadmill. Every delivered sheet has passed the human gate ("jedes Blatt von Menschen
>   geprüft" becomes literal). Delivery becomes instant, reproducible, and free of per-request API
>   cost/latency/truncation failure modes.
> - **What it changes.** `compose` graduates to the product core (**inter-block coherence** is the new
>   hard problem); the **review economy** becomes the scaling constraint (tiers keyed to the four
>   correct-by-construction mechanisms; adversarial agents triage, deterministic lints guarantee, the SME
>   gate stays); the **Statistik coverage matrix** becomes the roadmap driver; **Fassung migration
>   tooling** becomes a requirement (a corpus outlives its Fassung — re-anchor, re-derive, flag orphans).
>   The `llm/` seam **stays in code** as the campaign seam; any later live reintroduction is
>   expression-only re-projection over vetted facts, decided explicitly (invariants §10 boundary).
> - **Working mode (recorded).** The project is currently **built for the joy of building** — no launch
>   deadline, no GTM clock; "interesting and powerful" outranks "marketable"; the business/competitive
>   framing (`platform-definition.md`) is retained for a possible later phase, not driving priorities.
>
> The build program (3 tracks + a joy lane): `Documents/feature-roadmap.md` "Start here". Run:
> `python -m pytest -q` (**369 tests**).

> **Update (Session 12, 2–3 Jul 2026): the program's first build wave — and the review economy proven
> in a live SME session.**
> - **Track 1 BUILT:** #1 the **campaign planner** (`stats.coverage_map`/`campaign_gaps`, per-KB cells ×
>   Anforderungsband, 610 cells, gap export = brief anchors) · #2 the **numeric-claims lint**
>   (`pipeline/number_lint.py` — prose numbers next to a SOURCED figure must derive from the cited
>   series; calibrated on the corpus; caught real discrepancies, e.g. c0119's stale Bundesland counts) ·
>   #3 the unified **Prüfen gate** — ONE tier-laned queue over all seven stores (`store/reviewqueue.py`;
>   lanes = the four correct-by-construction mechanisms), keyboard focus mode, worksheet→block approval
>   **cascade** (SME decision), deterministic + adversarial **triage** (`pipeline/triage.py` +
>   `tools/triage_prompt.py`/`ingest_triage.py`; first pass 54/54 verdicts, found i.a. a NaCl-"Molekül"
>   Fachfehler), and the SME's **Überarbeiten** decision (status-preserving, mandatory note →
>   revise-flagged feedback; bulk release holds flagged entries).
> - **Track 2 STARTED:** the LLM-free delivery read-path `pipeline/deliver.py` (vetted sheet › composed ›
>   honest gap) + the `DemandStore` Wunschliste (invariants §10 in code).
> - **Dashboard collapsed 12 tabs → the 4 stations** (Planen · Prüfen · Korpus · Einblicke); every kind
>   judgeable inline in the focus card; **self-healing artifacts** (PDFs, assets, arrangement bundles
>   rebuild when stored absolute paths came from another machine — git carries content, not binaries).
> - **The blackboard test** (SME quality bar, durable): corpus content must beat what a teacher writes on
>   the board in a minute. The chemistry variant series were upgraded accordingly (Übungsreihe genre
>   framing · structure-derived difficulty ramp · curated digit-free context frames —
>   `Documents/uebungsreihe-upgrade-brief.md`); old series rejected, new c0167–c0169 SME-approved.
> - **The staged backlog is CLEARED** (first full SME session: 11 texts · 5 Sachverhalte · arrangements ·
>   datasets 5:3), and its findings landed as fixes: figures never use scientific notation (unit-scaled
>   "(in Mio.)" labels, German tick/value formatting, years on a numeric x-axis —
>   `figstyle.unit_scale`/`fmt_de`, rule in the figstyle docstring); decision notes persist for every kind.
>
> Run: `python -m pytest -q` (**413 tests**). **Open next:** Track 3 wedge campaigns (planner-driven, via
> `/api/coverage/gaps`) · Track 2's compose-coherence hard problem + the "Varianten erzeugen" surface ·
> the geosphere-Klimadiagramm re-decision · informational Realien / the joy lane.

> **Update (Session 13, 5 Jul 2026): a strategy session — the build-for-joy feature program.** No code;
> three doc deliverables. Corpus state at session start: 967 approved blocks (+176 MINT `in_review`),
> 155 approved content items, coverage 95/610 cells grün, demand queue empty.
> - **The frame, reaffirmed hard (durable).** The SME firmly corrected a pilot/storefront-first
>   recommendation: TeachersAid is a hobby built for the joy of building — **no pilots, no releases, no
>   deadlines, no teacher-feedback loop for now**; his thesis is that only building the *intrinsically
>   best* platform, as the goal itself, can later maybe become a product, and the discipline is to
>   resist premature productization (the failure mode of most AI projects). Product/outward framing
>   returns only when HE declares the building done. Assistant memory updated so the frame leads recall.
> - **The idea pass + SME verdicts** (full write-ups: `feature-roadmap.md` "▶ Start here (5 Jul 2026)").
>   **Accepted:** the Physics engine (units-verified parametrics via `sympy.physics.units` +
>   optics/circuit scene families — "clear win") · GZ via scene3d promotion · **PD Bildquellen** as the
>   6th asset class ("very clear win") · the **misconception engine** (computed distractors from a
>   curated Fehlermuster catalog; teacher guide names the probed misconception — "love it") · solution
>   graphs (alternative Rechenwege) · the **Rätsel engine** (Kreuzworträtsel/Suchsel/Trimino/
>   Rechenmauern, zero LLM, derived answers — "super fun for pupils") · Wiener-Sachtextformel
>   readability lint · the **prerequisite graph** ("awesome — think holistic": Diagnose-Blätter,
>   warm-ups, spiral revision, campaign ordering) · entity registry + cross-module consistency ·
>   ÜT cross-subject bundles · **difficulty-as-computed** (exploratory, advisory-only, calibrated on
>   the SME's own labels) · the **dramaturgy engine** ("could be extremely powerful — plan carefully":
>   design-doc-first; it IS Track-2 #4 coherence) · the **figure-engine rework** (the figstyle port, A1).
>   **Parked with reasons:** music engine (ME = relaxed subject, little worksheet demand) ·
>   experiment class (school-equipment-dependent) · self-checking sheets (gimmick; Trimino self-check
>   survives inside the Rätsel engine). **Unranked, awaiting a call:** stumme Karten/cartography ·
>   Typst renderer · vision-Blattkritik · Nachweis/coverage visualisation.
> - **Illustrations — direction DECIDED** (SME: "precisely the way we should think about it"; design:
>   **`Documents/illustration-design.md`**). The reframe: an image is a **CLAIM (fact — curated,
>   checkable) plus a RENDERING (expression — authorable under constraint)**, mechanism 4 extended to
>   pixels; the corpus model (generate once, **vet once, reuse forever**) converts diffusion's runtime
>   risk into a review-time cost, which is what makes it viable at all. Media policy gains a **third
>   lane `depictive`** (shows a thing; no labels/numbers/text; `intended_claim` + checklist gate)
>   between decorative and content; the content lane stays code-gen/sourced **forever**. Resolution
>   hierarchy: reuse › sourced PD/CC › diffusion › none (prefer real PD art where sources exist —
>   history gets Isabey, not a diffusion ballroom). Build: local **Flux.1-schnell** (Apache-2.0) on the
>   4070 via the TTS cp312-subprocess pattern; replayable `DiffusionSpec` provenance; deterministic
>   pre-review lints (OCR no-text, photocopy-survival); best-of-N review; **Realien backdrops as the
>   risk-free beachhead** (fictional world ⇒ zero world-claims) and the **Beschriftungs-hybrid**
>   (vetted base + curated anchors + code label layer, maskable) as the flagship; hard no-go list
>   (historical likenesses, maps, photoreal humans, text in pixels).
> - **CLAUDE.md rewritten as the operating manual** (853 → ~460 lines; SME-approved editorial
>   contract: *no rule lost* — cuts are history/narrative/duplication only, verified by an adversarial
>   lost-rule diff pass). History → handoff session blocks; design depth → the design docs; scattered
>   gotchas consolidated into one "Conventions & gotchas" index; a new "Updating this file" section
>   prevents organic regrowth (one paragraph per feature + pointer; extract a design doc at ~15 lines).
>   The figure intent→recipe system relocated to `figure-styleguide.md` (new "data-figure system"
>   section). **`AGENTS.md` is now a thin deferral to CLAUDE.md** (it was a stale parallel copy —
>   one manual, no drift). **`Documents/README.md` refreshed as the doc map** (six shelves:
>   canonical · live design · reference · agent briefs · worked content · historical);
>   schema v0.1/v0.2 + the stray `project-handoff (1).md` moved to **`Documents/archive/`**;
>   `implementation-notes.md` + `dashboard-review.md` marked historical in place.
>
> Run: `python -m pytest -q` (**413 tests**, unchanged — docs only). **Open next:** pick from the
> roadmap waves by interest; A1 (figure rework) unblocks the figure-heavy items; C5 (dramaturgy) and
> B-anything start with their design docs.

---

> **Update (Session 14, 5 Jul 2026): Wave A built end-to-end — the task & figure engines.** A subagent
> fan-out (Opus/Sonnet builders, orchestrator-reviewed: specimens viewed, diffs read, follow-ups sent
> back) shipped **all of Wave A** plus the CHE2 maintenance fix. **413 → 565 tests green.** Twelve
> commits (`30c7f6e`…`b8f550d`) on `main`. What landed:
> - **A1 · Figure-engine port.** All ~25 recipes now draw through `figstyle` roles/ramps — **0 hard-coded
>   hexes** (was 72; `tests/test_figstyle_port.py` locks it via regex). `right_triangle`/`rectangle`/
>   `polygon` became computed `Scene`s. Caught + fixed a real bug: a **py3.14 / mpl3.11 Calibri
>   small-glyph drop** silently blanked number-line/timeline labels — `figstyle._register_font` now
>   render-probes each candidate and falls through to a font that actually inks 9 pt text. Specimen
>   scripts per family (`tools/{charts,geometry,diagrams,maps}_specimen.py`).
> - **A2a · Physics parametric pack.** `pipeline/physics.py` (uniform_motion·density·ohm·resistors·
>   lever·energy_power) computing with `sympy.physics.units` — every answer **dimensionally verified**
>   before formatting (`_assert_dimension` over the SI dimension system; a unit-category error can't
>   ship), units carried through every Rechenweg step. `grounding/physics.py` (g exact per CGPM 1901;
>   cited school densities + reverse "welcher Stoff?" lookup). 7 `phy-*` templates on real US/OS anchors.
> - **A2b · Physics scene families.** `pipeline/optics.py` (thin-lens ray construction; drei
>   Hauptstrahlen as stages 1–6; givens g/G stay shown, image b/B maskable) + `pipeline/circuits.py`
>   (series/parallel netlist → Kirchhoff solve via sympy Rationals → DIN schematic; **per-element
>   `mask=[…]`** so "gegeben U,R₁,R₃,I — finde R₂" shows the givens and hides only the unknown).
>   `matplotlib:optics_ray`/`matplotlib:circuit`. **Mirrors (Hohlspiegel/Ebener Spiegel) deferred.**
> - **A3 · Misconception engine.** `grounding/misconceptions.py` (9 patterns; Radatz/Malle/
>   Padberg-Wartha for MAT, descriptive Physik-/Chemiedidaktik notes for PHY/CHE) +
>   `pipeline/misconceive.py` (`@_misconception` transforms). An MC distractor = the misconception
>   applied to the same drawn values → **guaranteed ≠ correct** (post-formatting), deduped,
>   plausibility-gated; the teacher guide names each probe via `watch_outs` ("B prüft:
>   Vorzeichenfehler (Radatz)"). `Instance.mc`/`mc_distractors` (pipeline-internal, derivation-safe).
> - **A4 · Solution graphs.** `SolutionPath` on `Instance`+`TaskBlock`; LGS emits Einsetzungs-/
>   Gleichsetzungs-/Additionsverfahren, Prozent emits Dreisatz/Operator/Formel — each path independently
>   sympy-derived and **asserted equal to the primary answer** before shipping; teacher renders
>   "Alternative Lösungswege", student/homework proven clean; the generation-view omission lock is now
>   test-locked.
> - **A5 · Rätsel engine.** `pipeline/puzzles.py` + `schema/puzzle.py`: Kreuzworträtsel (backtracking
>   crossings), Suchsel (accidental-duplicate refill guard), Domino (**closes iff every match correct** —
>   self-check by graph construction), Rechenmauern (unique-solution masking verified by propagation).
>   One core kind `puzzle` (no write-space); `matplotlib:puzzle_grid`; teacher-only solved grid via
>   `TaskBlock.solution_asset_refs`; umlaut = single-cell (flip in one constant). Corpus-scale clue
>   ingest is the follow-up.
> - **A6 · Wiener Sachtextformel.** `pipeline/readability.py` (WSTF1, Bamberger/Vanecek; documented
>   German syllable heuristic — advisory lane only) + a verify warning when a block reads ≫ target
>   Schulstufe + a computed-on-demand block-card badge. **Verbatim sources (`quoted`/`source_text`) are
>   exempt** — deliberately hard IS the Quellenarbeit (orchestrator fix; the GPB flagship test treats
>   Lesbarkeit as flag-not-gate). Scope-variant linguistic targets deferred (chip `task_8964d0d4`).
> - **A7 · scene3d promotion.** `pipeline/scene3d.py`: `Scene3D` + axonometric projection + closed-form
>   back-face hidden-line classification (raises `NotConvex` at the boundary). `axonometric_solid`
>   (Quader/Prisma/Pyramide/Zylinder/Kegel; hidden edges dashed) + `riss_pair` (Grund-/Aufriss with
>   Ordnungslinien). **Orchestrator Sichtbarkeit fixes** (the A7 agent was rate-limited before applying
>   them): smooth-body base rim splits front-solid/back-dashed; riss visibility is computed **per Riss**
>   (Grundriss looks down +z, Aufriss from −y) with the **coincidence rule** (visible wins) — fixing the
>   pyramid Grundriss diagonals and hex-prism Aufriss verticals that were wrongly dashed. Anchors found:
>   GZ `GEZ.US.4.PRO.*`, DG `DGE.OS.7.ARB5.*` — a master-library flagship per Stufe is the follow-up.
> - **CHE2 routing fix (maintenance).** `_DISPLAY_NAME_OVERRIDES` keyed `(stufe, code)` gives the second
>   "CHEMIE" subject a distinct display name at `_meta` load — name-routed campaigns now reach CHE2's 6
>   US cells; plain "Chemie" still routes to CHE. (Rescued from an orphaned Session-13 worktree.)
>
> **⚠️ SME FACT-CHECK QUEUE (physics/German/didactics — the SME is the domain authority; nothing here
> blocks, all is verify-clean):**
> 1. **g = 9.80665** exact (not 9.81) → E_pot results ~2 % higher than a 9.81 hand-calc. One-line flip
>    in `STANDARD_GRAVITY` if Unterstufe should use 9.81.
> 2. **kWh introduced at Kl. 3** (US energy template) — confirm or push to OS-only.
> 3. **`phy-os-arbeit-leistung`** mixes E_pot into the "Elektrische Energie" KB — defensible as
>    energy-form review; say if the OS template should be electrical-only.
> 4. **Density anchored to OS Thermodynamik** (`PHY.OS.5.THE.01`) — no Dichte descriptor exists in the
>    PHY Unterstufe Lehrplan; confirm the anchor or point at a better one.
> 5. **Magnitude ranges** to eyeball: motion (Schnecke cm/s … Zug ~30 m/s), Ohm (mA…3 A, 1–1000 V),
>    resistors (2–200 Ω), lever (5–400 N), power (Glühlampe 40 W … Wasserkocher 2 kW).
> 6. **Circuit phrasing** "In einer Reihenschaltung liegen die Widerstände …" — slightly stiff.
> 7. **Misconception sources for PHY/CHE** cited descriptively, not pinned to a page — tighten if you
>    have a preferred reference.
> 8. **`resistors_mc`** yields 2–3 options (parallel-as-series always; ×10 slip only when distinct).
> 9. **Optics sign convention:** f/g/G entered as positive magnitudes, lens type carries the sign
>    (Sammellinse +f, Zerstreuungslinse −f); g=f drawn as parallel emerging rays ("kein Bild").
> 10. **Schrägriss foreshortening:** strict Kabinett (½ at 45°) per the design doc — some AT texts use
>     Kavalier (full length). And the **a/b/c → edge mapping** (a=x-width, b=y-depth, c=z-height) —
>     check against your Länge/Breite/Höhe convention.
> 11. **GZ/DG coverage gap** (honest): scene3d does parallel Grund-/Aufriss only — no Kreuzriss,
>     no Zentralprojektion yet.
>
> Run: `python -m pytest -q` (**565 tests**). **Open next:** Wave B (the image program — B1 Flux backend
> starts it) or Wave C (C1 prerequisite graph, or C5 dramaturgy design-doc-first); the physics/GZ
> engines invite master-library flagships (PHY worked sheets, a GZ "Risse herstellen" + DG "Sichtbarkeit"
> sheet) and a corpus-scale Rätsel ingest seam. **Worktree note:** three merged worktree dirs under
> `../TeachersAid-wt/` + `.git/worktrees/{a2b,a5,a7,blissful-rosalind-5bbcdb}` are Windows-lock-stuck on
> disk (branches deleted, `git worktree list` clean) — `git worktree prune` + delete the dirs once the
> locks clear.

> **Update (Session 15, 11 Jul 2026): the remaining geometry gap — Körpernetze — shipped on the
> external-experiment branch `ext/nets`.** `pipeline/nets.py` separates computed geometry from its
> scene projection: a Quader/Würfel net has the true two `a×b`, two `a×c`, two `b×c` faces and exactly
> five shared fold edges forming a connected tree. `matplotlib:solid_net` registers the maskable figure;
> `quader_oberflaeche` derives `O = 2(ab+ac+bc)` from the same dimensions and emits one `O = ?` net per
> variant, honestly anchored to `MAT.US.1.FIG.03`. Both Quader and Würfel specimens were visually
> inspected; geometry, masking, layout and render tests landed. Suite: **683 passed, 1 skipped**.
> **Track-2 #6 shipped in the same experiment:** `GET /api/templates` + `POST /api/variants`, optional
> difficulty ramp wired through `compose_variants`, and the **Korpus → Arbeitsblätter** production form.
> The browser verification staged the two-variant Quader series `c0198`, opened its student PDF preview,
> and found no console errors.
> **Boxplot follow-up shipped:** parametric `Instance.solution_figure` is the minimal teacher-only
> emission seam; `boxplot_from_data` derives a solution figure from the same five values as its answer
> key and wires it through `solution_asset_refs`. Student/homework never traverse that channel.
> **ANNO/OCR follow-up shipped:** `tools/fetch_anno.py` resolves official ÖNB IIIF manifests to ALTO,
> throttles requests, records the exact canvas, and keeps OCR bytes semantically verbatim—errors and
> line/block boundaries included, with no silent correction or dehyphenation. Rights-clear admission is
> limited to an explicit **Public Domain Mark**. The first annotated 1871 newspaper extract is in review;
> referenced-only GPB Quellenarbeit `c0199` points students to the scan without embedding it. Suite:
> **695 passed, 1 skipped**. SME review should decide whether the intentionally noisy Leitmeritz OCR is
> the best flagship, and whether a Vienna title should replace or join it.
> **Grounded-data T4 shipped:** two official Statistik-Austria CC-BY pipelines add a BIO-discoverable
> life-expectancy dataset (2002–2024, `BIO.US.x.WIS.02`/`ERK.04`) and population for 116 Bezirk/
> Gemeindebezirk regions (1.1.2024, total lock 9,158,750). `at_bezirke_2025` is fetched from the official
> WFS and deterministically simplified; the duplicate whole-Wien overlay is excluded while 901–923 stay.
> Both datasets are staged `in_review`; line and choropleth specimens are visually clean and
> `figure_lint`-clean. Suite: **702 passed, 1 skipped**. Optional informational Realien was deliberately
> skipped after T1–T4, as the brief permits; it needs its own fact-preserving CEFR design pass.

> **Update (Session 16, 11 Jul 2026): Wave C4 — difficulty as a computed, ADVISORY quantity — built on
> its own branch.** `pipeline/difficulty_model.py` estimates a task's difficulty band from a transparent,
> task-only feature vector (solution-step count · math-expression depth via sympy · number domain ℕ<ℤ<
> fractions<irrational · WSTF text load · a curated kind base-cost · answer-surface openness · the
> cognitive-level rank), reads the reviewable `difficulty_weights.json`, and is fit offline by
> `tools/fit_difficulty.py`. **The load-bearing finding, surfaced not hidden:** the ~1055-block corpus
> carries **zero** authored `difficulty` labels — every label is the cognitive-level fallback, so the
> only label is a deterministic function of one feature. An accuracy-max fit therefore trivially recovers
> `cognitive_rank` (100 % exact, 0 disagreements — mathematically perfect, a mute advisory). **A
> difficulty model is not learnable from this corpus.** The design response is *anchor-and-nudge*: the
> cognitive level is a dominant curated anchor, the intrinsic surface features are an independent nudge,
> and only the two thresholds are fit — 95.5 % exact / **100 % adjacent** agreement with the operative
> band, flagging **48 blocks (4.5 %)** where surface features disagree ≥1 band (the SME review-cue list).
> Adjacent-100 % means the estimate never disagrees by two bands — appropriate for an advisory. It is
> **DERIVED + ADVISORY**: a verify **warning** + an Einblicke cue (`GET /api/difficulty/cues`), never a
> gate, and test-locked to **never** mutate the authored value. `steps`/`math` are structurally 0 on
> harvested blocks (live only for parametric packs) — documented, not a bug. Design + honest numbers:
> `Documents/difficulty-model.md`. Suite: **714 passed, 1 skipped**. SME review: the 48-cue list (mostly
> `evaluate`-labelled closed-format tasks reading as band 2, and open high-text-load tasks reading a band
> up) is the first place authored `difficulty` labels would pay off — which is the real fix.

> **Update (Session 17, 11 Jul 2026): both waves merged · the idea pass for the NEXT program · docs
> tidied.** (a) The external agent's **Wave B image program** (reviewed clean: depictive lane, honest
> `GenerationRecord` provenance, raster preflight, best-of-N review, Commons/`ImageSource` with the
> Isabey flagship c0200, the `RasterImage` Beschriftungs-hybrid c0201) and the five supervised Opus
> **Wave C** tracks (C1 prerequisite graph · C2 entity registry · C3 ÜT-Projektwoche · C4 advisory
> difficulty · C5 dramaturgy design doc) merged in one pass; one integration fix (C4's LaTeX cleanup:
> grouping braces → parentheses). Suite **783 passed, 1 skipped**; pushed. (b) A free **brainstorm with
> per-idea SME verdicts** produced the next program — headline decisions: the **three-tier anchoring**
> frame shift (competence | ÜT | honest „Horizont"); the **Tiefenregler/Mischpult** as flagship
> (teacher-tuned depth faders over ONE master; the per-class simultaneous-level Zwillinge variant was
> REJECTED for classroom-sorting stigma — levers yes, levels no); greenlights for Fermi-Werkstatt,
> Fehlersuche, Messdaten-Werkstatt, Beweis-Puzzles, Kontrafaktik, Finanzführerschein, Wahl-Werkstatt,
> Alltagsdokumente, Gesundheits-DATEN (hard data only — no health preaching), the physicist's corner
> (Sternkarten!) and the MUS/KUG/TED/BUS openings; design-first parking for Manipulations-Museum,
> Schularbeiten-Generator, KI-Bildung and the whole Lernarrangement family (dedicated future session).
> Full verdict ledger: the rewritten **`Documents/feature-roadmap.md`**. (c) Docs cleanup: the built-out
> 26 Jun–10 Jul roadmap + both executed external-agent handovers + the pre-Wave-B diffusion briefs +
> the executed audit/schema-roadmap moved to `Documents/archive/`; README map + CLAUDE.md pointers
> updated.

> **Update (Session 18, 11 Jul 2026): the enabler, the flagship's P1, and the first three programs.**
> The external agent delivered **three-tier anchoring** (`competence | uet | horizont`; honest Nachweis
> incl. the Fassung-bound ÜT hook; record `Documents/anchoring-modes.md`) and **Mischpult P1**
> (`schema/mixer.py`/`pipeline/mixer.py`: Umfang/Tiefe/Abstraktion/Offenheit as pure derivations of one
> master + the Regler-Lint with identical-competence-set guarantee; "no decorative knobs"; contract
> `Documents/tiefenregler-design.md`) — both reviewed and merged. Three supervised Opus programs built
> on top and merged the same day: **Finanzführerschein** (2026 tax/SV tables three-source-verified,
> VPI dataset, lohnzettel/inflation/handyvertrag recipes), **Wahl-Werkstatt** (BMI NRW-2024 CC BY 4.0,
> d'Hondt reproducing the official Mandate as compare-and-discuss, coalition arithmetic, the
> Ermittlungsverfahren honesty note), **Sternkarten** (BSC5-curated catalog, Meeus-grade ephemerides
> reference-tested, star_chart/moon_phase scenes, Orion-over-Wien visually verified — the first real
> `horizont` Nachweis). Suite **793 → 882 passed**. SME queue additions: tax values + pinned nettos,
> official-Mandate fact, star-catalog spot-check, ÜT-7 catalog-tag correction (GPB).

> **Update (Session 18, 11 Jul 2026): three-tier anchoring — the new program's enabler — BUILT.**
> `AnchorMode = competence | uet | horizont` now travels on `BundleRequest` + `WorksheetContent`
> (old JSON defaults to competence) through idea/API → deterministic resolve → plan → corpus-loop
> prompt → verify → derived Nachweis → teacher PDF/review summary. **Kompetenz** preserves the full
> coverage/gap table. **ÜT** requires one exact numbered subject/grade hook from the 13-item verbatim
> legend; its generic plan emits no fake `serves`, while any optional secondary competence must itself
> carry that ÜT and never creates a completeness claim. **Horizont** deliberately resolves with zero
> competences and hard-rejects any hidden `serves`; its Nachweis says voluntary teacher-choice
> enrichment beyond the Lehrplan. The Planen idea form exposes the choice. Contract:
> `Documents/anchoring-modes.md`. **783 → 793 tests passed, 1 skipped.** The enabler is closed; the
> natural next frontier is Tiefenregler P1 or a narrow correct-by-construction engine.

> **Update (Session 19, 11 Jul 2026): Tiefenregler P1 — pure parametric Mischpult — BUILT.**
> `ParametricMixerProfile` now projects one seeded master across four computation-backed controls:
> Umfang (count/time), Tiefe (computed `solution_paths` → strategy comparison + AFB movement),
> Abstraktion (computed student figure → formal no-figure projection), and Offenheit (the same
> `MCSpec` instance as misconception-MC or clean open response). Unsupported controls hard-fail; no
> decorative faders. The derived Regler-Lint measures both endpoints, C4/AFB/task/figure/response
> metrics, and requires competence coverage to remain identical. The teacher guide alone stamps the
> profile and pass state; student/homework remain clean. `POST /api/variants` accepts the typed profile;
> P4 UI remains deliberately unbuilt. Contract: `Documents/tiefenregler-design.md`. **793 → 803 tests
> passed, 1 skipped.** Next in the accepted sequence: P2 Gerüst from computed solution steps and
> misconception hints.

---

## 0 · Orientation (the 30-second version)

We are designing (not yet building) an **on-demand generator of Austrian-curriculum-anchored teaching
material** for AHS secondary schools. A teacher gives a topic + grade + time; they get a ready-to-use,
competence-anchored bundle they can trust and drop into whatever they already use. *(Session-11 note:
this baseline is historical — the system is built, and since 2 Jul 2026 it is **corpus-first**: bundles
are assembled on demand from a vetted corpus, never live-generated; see the update blocks above + §4.)* The work so far is
**design**: a data model, a competitive/positioning analysis, a full subject audit, and worked content
examples. The current source of truth for the data model is **schema v0.3**; v0.4 and v0.5 are specced
in the roadmap; an engine and any UI are deferred.

**Three things to internalise immediately:**
1. The architecture separates **blocks → content → rendering** as three distinct actions (§3). This is
   the central design idea and it has paid off repeatedly.
2. **Competence-anchoring is what makes creativity safe to ship** — every creative tangent is provably
   on-curriculum. That is the product's whole thesis, not a feature.
3. There is a **hard scope line**: we generate *material* (+ activity run-guides + homework material).
   The teacher runs the room and owns grading/collection/tracking. We are **not** a workspace, LMS,
   workflow-owner, or general chatbot. Crossing that line is how the incumbent (Teachino) failed.

---

## 1 · What this project is (vision / thesis)

On-demand generator of Austrian-Lehrplan-anchored teaching material for AHS *(since Session 11:
"on demand" = assembled from the vetted corpus, LLM-free at delivery — §4)*. Teacher inputs topic +
grade + time → ready-to-use bundle (conservative student material + a curated teacher depth-layer) that
is **correct by construction**, **provably competence-aligned** (the derived *Nachweis*), and **drops
into existing tools**. We sell a *"creative curriculum partner + compliance guarantee,"* **not** an
"AI worksheet." **Modest promise, ruthless execution.**

- **Tight downstream, generous upstream:** the student-facing spine is conservative; the teacher rack is
  overproduced; we absorb the curation cost so the teacher experiences near-zero friction.
- **MINT-first is the wedge, not the ceiling.** MINT is where the incumbent is weakest × our
  correctness advantage is sharpest. But the product's identity is the **function across subjects**, not
  one subject. We expand *by subject*, never by *platform features*.
- **Teacher-in-the-loop, always.** The product helps the teacher; it does not replace or compete with
  them.

---

## 2 · The grounding: the Lehrplan (facts not to rediscover)

- **Fassung:** consolidated AHS Lehrplan, RIS — **BGBl. II Nr. 204/2024** (Stammfassung 88/1985),
  **DokNr NOR40264237**, valid **2024-09-01 … 2026-08-31**. ⚠ **Expires at the end of this school
  year**; rollout is staggered class-by-class, so a **new Fassung will be needed for 2026/27** —
  versioning the resolution against Fassung windows is a real requirement, not a nicety.
- **Source file:** `RIS_Dokument.html` (the uploaded consolidated Lehrplan, ~2.7 MB). A plain-text
  extraction is produced at `/home/claude/plain.txt` (session-local; regenerate by stripping tags — see
  the parsing one-liner used in Session 2). Subject curricula live in the **Achter Teil**.
- **Structure:** Anlage A, 8 Teile; 2 stages (**Unterstufe** = Sek I, **Oberstufe** = Sek II) × 3
  Schulformen (Gymnasium / Realgymnasium / Wirtschaftskundliches RG).
- **Reform state:** **Unterstufe is fully competence-oriented and deterministically parseable** (this is
  where we work). **Oberstufe is largely legacy prose → deferred.**
- **Science competence model W/E/S** — *Fachwissen anwenden (W) · Erkenntnisgewinnung/Experimentieren
  (E) · Standpunkte begründen/bewerten (S)* — is **shared verbatim by Physik, Chemie, and Biologie**
  (glosses differ slightly). One model, three subjects.
- **Übergreifende-Themen legend (1–13):** 1 Berufsorientierung · 2 Entrepreneurship · 3 Gesundheits­
  förderung · 4 Informatische Bildung · 5 Interkulturelle Bildung · 6 Medienbildung · 7 Politische
  Bildung · 8 Geschlechterpädagogik · 9 Sexualpädagogik · 10 Sprachliche Bildung/Lesen · 11 Umwelt­
  bildung · 12 Verkehrs-/Mobilitätsbildung · 13 Wirtschafts-/Finanzbildung.
- **Physik Unterstufe grade map (grounded):** 2. Kl = Sehen und Hören, Optische Systeme · 3. Kl =
  Mechanik, Elektrizität und Magnetismus, Energie · 4. Kl = Wetter und Klima, **Strahlung und
  Radioaktivität**.
- **The full per-subject competence models for all 16 Unterstufe subjects are captured in
  `subject-coverage-audit.md`.** This is **gold and expensive to extract — do not re-derive it.**

---

## 3 · The design as it stands (architecture)

**Three separable layers / actions: blocks → content → rendering.**

- **Block** = the atom, in two families:
  - `InfoBlock` — information to learn *from* (prose / key_fact / example / procedure / figure /
    data_reference / callout). *(We learned in Session 2 that info blocks must be first-class and that a
    sheet should not be all-tasks; depth comes from task design, but learners still need something to
    learn from.)*
  - `TaskBlock` — an exercise. Carries: `kind`, `prompt` (RichText), `payload`, `response`
    (a *ResponseSpec* affordance — lines/box/table/choices — **not** layout), `cognitive_level`,
    subject-scoped `dimensions[]`, `serves[]` ({competence_id, relation}), `est_minutes`, `answer_key`,
    `acceptable_reasoning` (the *range* for judgement tasks), `watch_outs`, `modality`, `flags`,
    `asset_refs`.
- **WorksheetContent** = a **renderer-independent object** (meta, intro, sections = Bausteine, assets,
  **derived Nachweis**, **derived DepthProfile**, rack). It exists **before any document**. It has no
  concept of a "page."
- **Rendering** = **pure projections** of that one object: student sheet, teacher guide, [homework],
  [docx]. Because all views derive from one object, **they cannot drift** — this structurally kills the
  mismatched-answer-key bug we hit early in Session 2.
- **Competence axis is subject-parameterized** (`SubjectCompetenceModel`) — **not** the science-only
  W/E/S. Each subject supplies its own dimensions (Deutsch's four Kompetenzbereiche, Math's four
  processes × content areas, GWB's Orientierungs-/Urteils-/Handlungskompetenz, …).
- **CognitiveLevel** (remember → understand → apply → analyze → evaluate → create) is the **formal depth
  contract** — corroborated by the Lehrplan's own *Anforderungsbereiche* (Reproduktion/Transfer/
  Reflexion/Problemlösung). It makes "shallow" a *measurement*, not a vibe.
- **Modality** (printable / oral / enactive). At v0.4 it moves to the **dimension** level, which makes
  **`printable_coverage` computable per subject** (Physik ≈ 1.0 … Sport ≈ 0.0).
- **Worksheet vs Lernarrangement:** a worksheet is the **single-learner printable atom**. A
  *Lernarrangement* (v0.5) is a **composite sibling** that *contains* worksheets (has-a composition) and
  anchors the **oral/social/enactive** competences a worksheet structurally can't reach. A plain
  worksheet is simply the **n = 1** arrangement.
- **Homework** (decided in Session 2, **not yet specced**): the **same block machinery** under a
  homework *purpose + constraint profile* + a **third projection**. Its defining design axis is
  **AI-resistance via relevance/personalization** (measure-in-your-kitchen, ask-a-grandparent — not
  retrievable facts). Needs a `self_check` (no teacher present), migrates teacher watch-outs into
  student-facing text, drops teacher-present blocks. We generate homework *material* only — no
  collection/grading/tracking. Equity caveat: resource-independence is a *requirement*.

**Schema lineage:** v0.1 → v0.2 → **v0.3 = CURRENT (source of truth for types)**. **v0.4 & v0.5 are
specced in `schema-roadmap-v0.4-v0.5.md`** (additive; not yet folded into a schema doc). **Homework is
decided but not yet written up.**

---

## 4 · Key decisions & findings (durable — do not relitigate)

**The offline-first pivot (Session 11, 2 Jul 2026) — supersedes the "on-demand live generation" framing
wherever older docs use it:**
- **The product is the curated corpus + deterministic delivery.** Generation (LLM or subagent) happens
  only in the campaign-shaped **corpus loop**, upstream of the SME gate; the **delivery loop is LLM-free**
  (vetted sheet › composed-from-blocks › honest gap + demand queue; async fulfillment for the long tail).
  Rationale: a closed curriculum ⇒ finite, computable coverage; live delivery is structurally un-gated
  (it conflicts with the human-final-gate decision below); campaign capex instead of per-request opex.
  Rule + boundary: `Documents/invariants.md` §10.
- **Live LLM generation is deferred, not deleted** — the `llm/` seam remains as the campaign seam; a later
  reintroduction would be expression-only re-projection over vetted facts and gets decided explicitly.
- **Working mode: build-for-joy.** No deadline, no business pressure; a feature is justified by being
  inherently interesting/powerful. Competitive/GTM concerns deferred (kept in `platform-definition.md`).

**Positioning / strategy (from the Teachino pilot study, `platform-definition.md`):**
- Teachino *validated the concept but execution killed it* (~32% used it regularly; Math 9% usage; "too
  text-heavy," "must reformat in Word," examples "zu niedrig für AHS," stale Einstiege, AI didn't grasp
  the *intendierte Aufgabenlogik*).
- Lessons we hold: **don't be a platform**; **don't compete with general-purpose AI** (the structure-
  seeker, not the ChatGPT power user, is our audience); **near-zero onboarding**; **MINT is the open
  wedge**; **use-ready output is the weak flank**; **modest promise**; DSGVO/EU-hosting is table-stakes
  trust. The realistic GTM is institutional / ecosystem-plugin, not viral.

**Design principles (earned across the session):**
- **Competence-anchoring makes creativity safe to ship.** This is the core.
- **Correctness ≠ pedagogical safety.** A correct figure can plant a misconception (the EM-spectrum
  figure can imply "UV = non-ionizing = safe") → teacher watch-outs are load-bearing.
- **Depth = cognitive demand, not word count.** Tasks must climb a ladder
  (predict → reason-with-data → evaluate-claims → transfer). Resource-independent tasks carry the load;
  experiments/equipment are enrichment, never the substance.
- **Separate blocks / content / rendering.** One content object → many consistent projections.
- **Competence dimensions are subject-parameterized**; `kind` is a **core + per-subject extensions**
  open set; `cognitive_level` is the depth contract.
- **Modality at the dimension level** turns "what can a worksheet even serve?" into a number.
- **Content-bearing visuals are code-generated** (correct by construction); decorative may be diffusion;
  the boundary is per-subject (MediaPolicy). Audio is a real medium (Fremdsprache, Musik) and music
  audio is *not* machine-generatable.
- **Lernarrangement is a composite sibling, not a worksheet field** (rejected: bolting roles on the
  worksheet; rejected: making everything an arrangement).
- **Homework = purpose-profile + third projection on the same blocks**, defined by AI-resistance.

**Subject scope (from `subject-coverage-audit.md`):** worksheet coverage tiers — **strong** for the
cognitive subjects (Physik/Chemie/Biologie [shared W/E/S], Mathematik, GWB, Geschichte+pol. Bildung,
Ethik, Latein, written Deutsch); **partial** for Fremdsprache, Digitale Grundbildung, Geometrisches
Zeichnen (need audio/oral/enactive/dynamic-software handling); **marginal** for Bewegung und Sport,
Musik, Kunst, Technik und Design (core competences are performed/made — **don't target these for
worksheets**). English listening (historic speech + tasks) is explicitly a sweet spot.

---

## 5 · Session 2 (24 June 2026) — what changed today

Worked from a consolidated v0.2 + first PDFs, through to v0.3 + a full audit + roadmap. The arc:
1. **Teachino pilot study** read closely → demand is real but execution killed it; extracted the
   failure-mode map.
2. **`platform-definition.md` (v0.1)** — thesis, who-for/who-not-for, MINT-as-wedge-not-ceiling, the
   anti-scope, an honest pain-point gap-check.
3. **Use-ready Strahlung PDFs** built (ReportLab + Carlito), QA'd via raster, defects fixed — proving we
   *can* clear the use-ready bar that the study says is the weak flank.
4. **Shallowness critique → deep rebuild** (`strahlung_schueler_v2.pdf`): a real cognitive ladder, fully
   resource-independent, experiment demoted to optional. Established "depth = cognitive demand."
5. **Methodical pivot:** stop hand-building documents; design the **data structure first**.
6. **Block model** invented (InfoBlock/TaskBlock + cognitive_level + dimension + response + serves).
7. **Cross-subject stress test** (Deutsch/Math/GWB) → block model holds; `dimension W/E/S` breaks
   (subject-specific); `kind` must be extensible; `cognitive_level` corroborated by Anforderungsbereiche;
   oral/enactive scope boundary surfaced.
8. **`lehrplan-bundle-schema-v0.3.md`** — folded all of that in (subject-parameterized dimensions,
   depth contract, modality, RichText/ResponseSpec, derived Nachweis/DepthProfile, renderer-independent
   content object + pure projections). Changelog traces each change to its finding.
9. **Full 16-subject audit** (`subject-coverage-audit.md`) → sciences share one model; **modality must
   move to the dimension level** (printable_coverage); **audio medium** + **rubric/artifact response**
   needed; the green/amber/red scope tiering.
10. **Creativity brainstorm** — 20+ pedagogically rich, competence-anchored ideas across subjects;
    surfaced more deltas (diagram/drawing responses, intra-sheet refs, intentionally-flawed asset, asset
    provenance/rights, cross-subject dimensions) and the **Lernarrangement** frontier.
11. **Lernarrangement** decided as a **composite sibling** (side-by-side, has-a; worksheet = n=1).
12. **`schema-roadmap-v0.4-v0.5.md`** — v0.4 = 11 additive worksheet deltas; v0.5 = the Lernarrangement
    interface + the "we make the material, not run the room" scope line.
13. **`worked-examples-three.md`** — English listening / Physik "geschönte Kurve" / Math "unfair game"
    built at the content-object level, validating v0.4 and exposing the real v0.5 seam.
14. **Homework** agreed as in-scope: a purpose-profile + third projection, AI-resistant via relevance;
    decided, **not yet specced**.
15. This handoff rewritten.

---

## 6 · Artifact inventory (all in `/mnt/user-data/outputs/`)

**Read in this order (new session):** `project-handoff.md` (this) → `platform-definition.md` →
`lehrplan-bundle-schema-v0.3.md` → `subject-coverage-audit.md` → `schema-roadmap-v0.4-v0.5.md` →
`worked-examples-three.md` → reference: `strahlung-rack.md`, `zwentendorf-faden.md`, the Strahlung PDFs.

| File | What it is | Status |
|---|---|---|
| `project-handoff.md` | This master takeover doc | **CURRENT** |
| `platform-definition.md` | Positioning, who-for/not-for, MINT-wedge, anti-scope, Teachino gap-check | **CURRENT (v0.1)** |
| `lehrplan-bundle-schema-v0.3.md` | The data model — **source of truth for types** | **CURRENT** |
| `subject-coverage-audit.md` | 16-subject audit + **the per-subject competence models** + tiering + v0.4 deltas | **CURRENT (gold)** |
| `schema-roadmap-v0.4-v0.5.md` | v0.4 (11 additive worksheet deltas) + v0.5 (Lernarrangement) | **CURRENT (specced, not folded)** |
| `worked-examples-three.md` | 3 content-object examples (English/Physik/Math) validating v0.4 | **CURRENT** |
| `strahlung-rack.md` | 25-thread Vertiefungs-Rack for KB Strahlung (German) | **CURRENT reference** |
| `zwentendorf-faden.md` | One thread built to full teacher-deliverable depth (contested + local) | **CURRENT reference** |
| `spectrum.png` / `spectrum.svg` | Code-generated EM-spectrum figure (matplotlib) | **CURRENT (reused)** |
| `strahlung_schueler_v2.pdf` | **Best** student worksheet — deep, cognitive ladder, resource-independent | **CURRENT** |
| `strahlung_schueler.pdf` | v1 student worksheet (pre-block-model render) | **SUPERSEDED by v2** |
| `strahlung_lehrkraft.pdf` | v1 teacher guide | ⚠ **MISMATCHED to v2's tasks — regenerate when revisiting Strahlung** |
| `archive/lehrplan-bundle-schema-v0.2.md` | Prior schema; carries Thread/Rack/Coverage/Verification/Lens/Asset/Nachweis | **SUPERSEDED by v0.3 for types** |
| `archive/lehrplan-bundle-schema.md` | First bundle anatomy (v0.1) | **HISTORICAL** |

*Note:* the Strahlung PDFs predate the block model — they are valid rendered proof-of-concept, but the
canonical representation is now the content object. Strahlung has **not** been re-expressed as
`WorksheetContent` (the worked examples in §6 cover *other* topics).

---

## 7 · Open questions / pending decisions

- **Two-subject Nachweis/Fassung** (cross-curricular worksheets, from the "geschönte Kurve" example):
  proposed answer = cite **both** competence sources and stamp to **both** subjects' Fassung windows —
  decide explicitly when v0.4 is formalised.
- **Fold v0.4 into a schema doc** vs. **build a concrete homework example first.** Current lean: build a
  Strahlung *homework* example to test AI-resistance / self-containment before committing it to schema.
- **Strahlung teacher guide** must be regenerated to match the deep v2 student sheet.
- **The template/shape layer** (between v0.3 blocks and generation — reusable skeletons like
  predict→reason→evaluate→transfer, with a `DepthTarget` and assembler rules). Not yet designed; intended
  *after* v0.4, *before* v0.5.
- **The engine** (deterministic resolver + generator + verifier + auto-formatter) — deferred / unbuilt.
- **Difficulty calibration** — the persistent open hard problem; now pinned to per-block *fill + verify*,
  but unsolved (and it's the unproven core of the MINT claim).
- **Oberstufe** loose resolution; the **post-2026/27 Fassung**.
- **Use-ready output polish / decorative layer / editable docx** — documented weak flank; editable output
  is "just another `render()` target."

---

## 8 · Next steps (a menu for tomorrow)

- **Build one creative *homework* example** for an existing topic (Strahlung) at the content-object
  level, to pressure-test AI-resistance and self-containment — then fold the homework profile + a
  `self_check` field + the homework projection into v0.4. *(recommended first.)*
- **Settle the two-subject `Nachweis`/`Fassung` question**, then **fold v0.4** into a proper schema doc.
- **Design the template/shape layer** on top of v0.3/v0.4.
- **Regenerate the Strahlung teacher guide** against the deep v2 student sheet (and/or re-express
  Strahlung as a `WorksheetContent` object to dogfood the model end-to-end).

---

## 9 · Working norms (how this collaboration runs)

Rigor with honest caveats. **Agree on the approach before building; batch changes rather than iterating
one at a time; flag inconsistencies explicitly; avoid over-engineering and premature complexity; always
be Austria-specific.** On contested topics, present the strongest form of each side and stay neutral.
Verify facts and flag uncertainty rather than fabricating. **The user is a physicist (Austrian) and the
domain SME — he fact-checks the physics and the German, and values genuine pushback over agreement.** The
network is disabled (no web search); the Lehrplan source is the uploaded `RIS_Dokument.html`. Deliverables
go to `/mnt/user-data/outputs/`. Read the relevant `SKILL.md` before producing files (the PDF skill is
ReportLab-based — no HTML→PDF in this environment; QA PDFs by rasterising with pdftoppm before
presenting).
