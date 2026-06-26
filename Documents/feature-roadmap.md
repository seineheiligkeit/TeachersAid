# Feature roadmap / backlog

Forward-looking *capability* features for TeachersAid. (The schema-version roadmap lives in
`schema-roadmap-v0.4-v0.5.md`; this tracks product/engine features.)

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

## Under investigation — subject-driven features (26 Jun 2026)

Cross-subject scan started: the per-subject `task_kind_extensions` in `subject_models.json` are a
direct signal of unmet demand (e.g. FS1/FS2 `listening_task` → audio; GPB `source_analysis` →
sourced-text work; MAT `construction` → geometric figures). Themes to prioritise — see the
session discussion; this section fills in once we pick the near-term track.
