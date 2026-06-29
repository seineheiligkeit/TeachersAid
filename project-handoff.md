# Project Handoff — Austrian Lehrplan-anchored Teaching-Material Generator

**Status: design baseline from Session 2 (24 June 2026); see the dated session updates below for the
current state (latest: Session 7, 29 June 2026).** This is the single read-me-first document for a fresh
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

---

## 0 · Orientation (the 30-second version)

We are designing (not yet building) an **on-demand generator of Austrian-curriculum-anchored teaching
material** for AHS secondary schools. A teacher gives a topic + grade + time; they get a ready-to-use,
competence-anchored bundle they can trust and drop into whatever they already use. The work so far is
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

On-demand generator of Austrian-Lehrplan-anchored teaching material for AHS. Teacher inputs topic +
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
| `lehrplan-bundle-schema-v0.2.md` | Prior schema; carries Thread/Rack/Coverage/Verification/Lens/Asset/Nachweis | **SUPERSEDED by v0.3 for types** |
| `lehrplan-bundle-schema.md` | First bundle anatomy (v0.1) | **HISTORICAL** |

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
