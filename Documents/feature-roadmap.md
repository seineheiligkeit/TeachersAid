# Feature roadmap / backlog

Forward-looking *capability* features for TeachersAid. (The schema-version roadmap lives in
`schema-roadmap-v0.4-v0.5.md`; this tracks product/engine features.)

## ▶ Start here tomorrow (27 Jun 2026)

Strategy is captured; nothing is mid-build; tree is clean. Recommended order:

1. **First strike — the convergent spike** (B + data-layer phase 2 in one): build the
   **population-pyramid recipe** *and* the `Dataset`/`SourceRef`/`DataRef` schema, proven on
   **Statistik Austria population-by-age** (CC BY OGD), re-grounding **c0094** with a *real, cited*
   Bevölkerungspyramide. One dataset proves both the recipe and the data layer end-to-end.
2. **Quick parallel win — the (c) label** (data-layer phase 1): every figure's data declares
   `sourced(ref)` vs `illustrative`; `verify` warns on unlabelled real-looking numbers. Small, independent.
3. **Then the rest of B:** timeline (GPB) + Klimadiagramm dual-axis recipe (share derived-layout machinery).

Standing tracks (no build needed): **geography teacher reviews** the 9 GWB worksheets (c0089–c0097) +
earlier staged items in the dashboard; **GPB Quellenarbeit via ANNO/ALEX is buildable now** as
referenced-only (b2) — well-chosen task prompts pointing at the archives, no ingest tooling.

Details for each below ↓

## Next — agreed, deferred from the GWB figure work (26 Jun 2026)

- **Population-pyramid figure recipe** — back-to-back horizontal age/sex bars. Surfaced as a
  consistent gap by both GWB demographics worksheets (c0094, c0097); currently approximated by
  an age-group `comparison` bar and flagged in `watch_outs`.
- **Klimadiagramm figure recipe** — dual-axis: monthly temperature *line* + precipitation *bars*
  on two y-axes. The iconic climate/geography figure; not expressible by the current single-axis
  recipes (hit by c0096). A general **dual-axis combo** recipe would also serve other subjects.
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
- **Effort:** medium, incremental (one recipe at a time).

### D — Parameterized variant generation — *high-ROI architecture feature*
- **What:** one competence → N controlled variants (randomized numbers/contexts) + a matching
  worked solution per instance; enables individualized sheets, A/B versions, practice sets.
- **Why:** MAT `calculation` + language drills; broadest cross-subject reach; assessment integrity.
- **Approach:** a parameterized task template (variable slots + constraints + a solution rule);
  seeded deterministic instantiation → multiple `WorksheetContent`; the answer is *derived* from the
  same params, preserving the no-drift guarantee.
- **Effort:** medium; touches schema + `generate`.

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
1. **Ship the (c) label first** *(tiny, immediate honesty win):* every figure's data declares
   sourced-vs-illustrative; `verify` warns on unlabelled real-looking numbers. The agents already
   reach for "Schematisch" unprompted — formalize it.
2. **One-dataset design spike:** define `Dataset`/`SourceRef`/`DataRef`; prove end-to-end on a single
   flagship series — re-ground the GWB urbanization + demographics figures (c0081 / c0094) with real
   Our-World-in-Data / Statistik-Austria numbers + citations. Learn the schema's edges on something concrete.
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
