# External-agent experiment report

Branch: `ext/nets`

Baseline: 674 passed, 1 skipped

Current: **683 passed, 1 skipped**

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
- T2b — teacher-only boxplot solution figure: not started.
- T3 — ANNO fetch + media texts + referenced-only Quellenarbeit: not started.
- T4 — BIO datasets + Bezirk regional data/boundaries: not started.
- T5 — informational Realien: optional, not started.

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
