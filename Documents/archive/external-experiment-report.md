# External-agent experiment report

Branch: `ext/nets`

Baseline: 674 passed, 1 skipped

Current: **702 passed, 1 skipped**

## T1 — `nets` (Körpernetze) — complete

### What shipped

- `teachersaid/pipeline/nets.py` — a computed `NetLayout`/`NetFace` model for Quader and Würfel.
  The canonical layout has six true rectangular faces and five full shared fold edges; rendering is
  a separate `solid_net_scene` projection through `Region`, `Line`, and `Label` primitives.
- `teachersaid/pipeline/assets.py` — registered safe generation recipe
  `matplotlib:solid_net` with a German spec contract and maskable, caller-provided labels.
- `teachersaid/pipeline/parametrize.py` — `quader_oberflaeche`, deriving
  `O = 2(ab+ac+bc)` and its worked steps from the same sampled dimensions used by the net.
- `teachersaid/library/templates.py` — `mat-quader-oberflaeche`, Klasse 1, honestly anchored to the
  verbatim competence `MAT.US.1.FIG.03`.
- `tests/test_nets.py` — 9 tests covering face dimensions/areas, the connected fold tree, Würfel
  congruence, scene structure, registry/rendering, label collisions, answer masking, derived results,
  competence anchor, assembly, and verification.
- `tools/geometry_specimen.py` — realistic Quader and Würfel specimens. Rendered binaries live under
  `runs/specimens/geometry/` and remain git-ignored/rebuildable.

### Verification

- Focused geometry + neighbouring regression set: **52 passed**.
- Full offline suite: **683 passed, 1 skipped**.
- Visual inspection: both specimens preserve equal aspect, expose all six faces, distinguish fold
  edges, keep labels readable, and show only `O = ?` rather than the computed result.

### Decisions

- One canonical cross net is computed instead of accepting arbitrary authored polygons. This makes
  face dimensions and fold adjacency testable and prevents a plausible-looking but false net.
- Würfel reuse the Quader construction with `a = b = c`; they are not a second renderer path.
- The optional pyramid/prism extension was not added: the complete minimum plus the recommended
  parametric stretch was preferred over widening the first recipe without a dedicated task need.
- Dimension labels appear once on representative outer edges. Repetition on all congruent faces adds
  clutter without adding geometric information.

### SME flags

- Please confirm the classroom notation **`O`** for `Oberflächeninhalt` and the dashed presentation of
  fold edges match your preferred Austrian register. The mathematics and Lehrplan anchor are exact.

## Remaining brief

- T2 — Varianten dashboard/API: complete (details below).
- T2b — teacher-only boxplot solution figure: complete (details below).
- T3 — ANNO fetch + media texts + referenced-only Quellenarbeit: complete (details below).
- T4 — BIO datasets + Bezirk regional data/boundaries: complete (details below).
- T5 — informational Realien: deliberately skipped (optional; design-first).

## T2 — “Varianten erzeugen” dashboard surface — complete

### What shipped

- `GET /api/templates` exposes the curated parametric templates with subject, Klasse, title, recipe,
  Kompetenzbereich, and real competence anchors.
- `POST /api/variants` validates `n` (1–30), accepts `ramp`, and stages a pending Gate-2 content item;
  unknown templates return 404.
- `orch.compose_variants(..., ramp=)` now carries the difficulty request into `variant_worksheet` and
  identifies an ascending series in the review title.
- The form lives in **Korpus → Arbeitsblätter**, next to deterministic composition. It loads the catalog,
  exposes count + ramp, and opens the staged item directly in the existing PDF preview.
- `tests/test_variants_api.py` covers catalog shape, figure-emitting staging, all three PDF endpoints,
  verify-clean content, the 1→2→3 ramp, unknown ids, and count bounds.

### Verification

- Focused API/parametric/composition set: **30 passed**.
- In-app browser: catalog populated; `mat-quader-oberflaeche`, `n=2`, ramp enabled staged `c0198`;
  pending item opened at `/api/items/c0198/pdf/student` with all projection controls; no console errors.

### SME flags

- None for correctness. The product wording “ansteigend (leicht → anspruchsvoll)” and placement in
  Korpus are UX judgments worth a quick glance during the ordinary dashboard review.

## T2b — teacher-only boxplot solution figure — complete

### What shipped

- `Instance.solution_figure` is an explicit pipeline-internal request separate from the all-projection
  `figure` field.
- Parametric instantiation assigns a unique solution asset id, collects the asset on the worksheet,
  and wires only `TaskBlock.solution_asset_refs`.
- `boxplot_from_data` emits `matplotlib:boxplot` from its already-derived minimum, Q₁, median, Q₃,
  and maximum. The all-projection `asset_refs` remain empty.
- Teacher rendering uses the existing solution channel; puzzle tasks retain “Lösungsraster”, while
  other computed visuals use “Lösungsabbildung”.

### Verification

- Figure/Matura/parametric/puzzle/render regression set: **75 passed**.
- Lock test: summary values in the figure spec equal the answer key; student PDF contains no image;
  teacher PDF contains the solution plot.
- Full offline suite after T2/T2b: **688 passed, 1 skipped**.

### SME flags

- The quartile convention remains the existing exclusive school convention (odd sample size; overall
  median excluded from both halves). No mathematical convention changed in this task.

## T3 — ANNO/OCR source workflow + Quellenarbeit — complete

### What shipped

- `tools/fetch_anno.py` resolves an official ÖNB IIIF manifest to its canvas, ALTO OCR, and image;
  requests are throttled and records carry the exact canvas URL.
- ALTO extraction preserves `String/@CONTENT` verbatim, including OCR errors and line/block
  boundaries. It never silently corrects spelling or dehyphenates; the source policy explicitly says
  `machine_ocr_unverified`.
- `TextSourceRef` admits `public_domain_mark` only when the licence field explicitly names a Public
  Domain Mark. Generic or missing rights claims fail closed.
- `deu-anno-lehrertag-1871` is a sourced, annotated Klasse-4 newspaper extract with six vetted
  comprehension/analysis annotations; fetched and staged text equality is lock-tested.
- `gpb_anno_quellenarbeit.py` stages a referenced-only Klasse-3 worksheet (`c0199`): students identify
  the source, compare scan and OCR, analyse political metaphor, and judge evidential limits. No source
  scan or OCR is embedded in the item.
- Offline IIIF-manifest and ALTO fixtures cover resolution, exact OCR preservation, rights gating, and
  ingestion equality.

### Verification

- Text ingestion dry run: **7 clean, 0 problems**; the new source is verify-clean and in review.
- Focused fetch/text/GPB regression sets: **31 passed** and **22 passed**.
- Full offline suite after T3: **695 passed, 1 skipped**.

### Rights verdict

- The workflow deliberately targets the ÖNB Labs historical-newspaper subset whose selected items are
  labelled with the Public Domain Mark. The mark must be present in each staged source record; the tool
  does not infer public domain from age or from appearing in ANNO.

### SME flags

- The 1871 OCR is intentionally quite noisy, which is useful for OCR/source criticism but demanding as
  a first flagship. Please decide whether to retain it, or pair/replace it with a cleaner Vienna title.
- *Leitmeritzer Zeitung* is an Austrian-Hungarian historical source from Bohemia, not a present-day
  Austrian regional title; the provenance is exact, but that framing should stay explicit.

## T4 — BIO data + Tier-2 Bezirk data — complete

### What shipped

- `tools/fetch_statistik_austria_health.py` selects life expectancy at birth for Austria by sex from
  the official OGD table `OGD_ind003_HVD_IND_1`. The curated 2002–2024 dataset is discoverable for
  BIO/GWB/MAT and directly cross-tagged to `BIO.US.x.WIS.02` and `BIO.US.x.ERK.04`.
- `tools/fetch_statistik_austria_regional.py` aggregates the existing 2024 municipality/age/sex fact
  table by Statistik Austria's three-digit district code. Its 116 counts sum exactly to the locked
  national total **9,158,750**.
- `at_bezirke_2025` is fetched from Statistik Austria's official WFS in EPSG:4326, validated at 117
  source features, and deterministically simplified from 21.6 MB to about 331 KB for print. The WFS's
  redundant whole-city Wien overlay (`900`) is removed; Gemeindebezirke `901–923` remain, yielding
  116 non-overlapping map regions that join exactly to the population dataset.
- Dense choropleths can set `show_labels=false`; this avoids manufacturing an unreadable 116-label
  map while preserving all geometry, values, colour scale, and both citations.
- Both new datasets are staged `in_review`. The dashboard chooses `matplotlib:choropleth_map` for the
  district series instead of a 116-bar chart.

### Verification

- Offline fixtures cover health selection/decimal parsing, district aggregation, population/boundary
  code divergence, and deterministic ring simplification.
- Focused dataset/layout suite: **39 passed**; both a life-expectancy line and the district choropleth
  render to real PNGs and pass `figure_lint` as sourced data.
- Visual inspection: readable axes/colour scale, correct Austrian outline, district subdivisions and
  Vienna detail; no overlaid whole-Wien polygon.
- Full offline suite after T4: **702 passed, 1 skipped**.

### Licence verdict

- Population, life expectancy, and district boundaries are all first-party Statistik Austria open
  data carrying **CC BY 4.0** with the required attribution recorded in each curated source record.

### SME flags

- Life expectancy is a strong data-literacy/health dataset, not a causal nutrition dataset. The BIO
  competence fit is exact for reading, comparing and interpreting biological/health data; tasks must
  not infer causes from the sex/time differences without an additional causal source.

## T5 — informational Realien — skipped cleanly

The task was explicitly optional and design-first. After completing T1–T4, no flagship was added:
fact-preserving CEFR simplification of real informational content needs a dedicated design pass, and a
rushed build would blur the project's source-text and constructed-fiction boundaries.
