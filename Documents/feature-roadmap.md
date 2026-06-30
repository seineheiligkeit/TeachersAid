# Feature roadmap / backlog

Forward-looking *capability* features for TeachersAid. (The schema-version roadmap lives in
`schema-roadmap-v0.4-v0.5.md`; this tracks product/engine features.)

## ▶ Start here (state as of 29 Jun 2026, Sessions 4–7)

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

**Matura-backward build targets (newly specced this session — each demand map names its own next step):**

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
3. **Geometry — parametric figure emission:** wire the variant engine to *emit* a figure per instance
   (Pythagoras/area "with a figure" — an optional `figure` on `Instance` → `asset_refs`); `nets`.
4. **Scale the text libraries:** more annotated PD texts (DE + LAT) across grades (subagent-annotation +
   `tools/ingest_texts.py` proven); an **ANNO/OCR fetch tool** for real newspaper/advert media texts.
5. **More parametric recipes + a "Varianten erzeugen" dashboard surface**; expose `orch.compose_variants`.
   The Matura-backward targets above are the prioritised recipe queue.
6. **Re-ground the old invented-number figures** the (c)-label flags (c0081 urbanisation, c0096 climate,
   c0097 HDI) by curating the few datasets they need; curate **BIO/other-subject** datasets; **Tier-2
   regional** down to Bezirk.

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
