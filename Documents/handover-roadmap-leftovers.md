# Handover — the remaining roadmap items (external-agent experiment)

You are an AI coding agent asked to complete the remaining backlog of **TeachersAid** — an
on-demand generator of Austrian-Lehrplan-anchored teaching material for AHS secondary schools.
This document is your complete brief. It was written 10 Jul 2026, immediately after a session
that closed most of the backlog (suite went 368 → **478 passed, 1 skipped**); what follows is
everything that is genuinely still open, specced the same way the previous session's (successful)
work was specced.

## 0. Read first, in this order

1. `CLAUDE.md` (repo root) — the architecture, the invariants, the conventions. **Binding.**
2. `Documents/invariants.md` — the load-bearing rules AND their boundaries (what each rule does
   NOT forbid). Read before you let a remembered rule block a good idea.
3. `Documents/feature-roadmap.md` — the "Start here" block records what just shipped; your tasks
   below are the surviving remainders.

The distilled non-negotiables (details in the two files above):

- **Select, never author — for FACTS.** Numbers, dates, names, quotes, competences, verbatim
  texts are selected/computed/curated from recorded sources, never invented. Expression (prose,
  task wording) may be authored *over a frozen fact-set*. Every dataset/text/boundary you add
  needs a **deterministic fetch tool** that records source + licence + Stand, with the parser
  unit-tested over an **offline fixture** (never live network in tests).
- **Licence gate before curation.** Only redistributable-with-attribution sources (CC BY etc.;
  AT 70-Jahre-p.m.a. PD for texts). CC BY-**SA** is refused (ShareAlike encumbers worksheets).
  If a licence is unclear: do NOT curate — document the honest verdict and pick a clean
  alternative or leave a gap.
- **Derived fields stay derived.** `Nachweis`, `DepthProfile`, `solution_steps`, rubric
  derivations — computed, never hand-written.
- **`rendering/` imports only `schema/`.** No exceptions.
- **Figures never leak answers** (labels are spec-provided strings, "O = ?" masking), and block
  assets render on EVERY projection — there is no teacher-only asset channel (this killed a
  solution-boxplot idea; tests lock it).
- Product-facing strings are **German** (Austrian school register); code/docs are English.
- The user is the SME (Austrian physicist) and fact-checks physics, maths and German at the HITL
  gate — flag anything you are unsure about instead of silently deciding.

## 1. Environment (this PC)

- Run tests ONLY with `C:/Users/sebas/Desktop/TeachersAid/.venv/Scripts/python.exe -m pytest -q`
  from the repo root. Bare `python`/`py` resolves to a different interpreter (3.12, no pytest,
  no engine deps). Do not `pip install` anything.
- Baseline: **478 passed, 1 skipped** — keep it green; add tests for everything you build.
- No `ANTHROPIC_API_KEY` (offline generation phase) — everything you build must work offline;
  the dashboard demos from the master library. Network access for FETCH TOOLS works (this PC
  reaches the Austrian sources).
- Generated content lands in `runs/` — git tracks the JSON/MD/TXT there (commit it), ignores
  binaries (PDF/PNG rebuild on dashboard load).

## 2. Work discipline

- Work on branches prefixed `ext/` (e.g. `ext/nets`, one branch per task or one for all — your
  call). **Never commit to `main`, never push.** The SME reviews your branches afterwards.
- Commit per task with descriptive messages. Update `CLAUDE.md` / `Documents/feature-roadmap.md`
  within your branch where the work genuinely warrants it (the repo's docs discipline is strong).
- Write a final **`Documents/external-experiment-report.md`** in your branch: per task — what
  shipped (files), test counts, decisions taken, and **SME flags** (anything needing the
  domain-expert eye: German register, didactic calls, licence verdicts, physics/maths).

## 3. The tasks

### T1 — `nets` (Körpernetze): the missing geometry figure recipe

The last open item of the geometry figure family. Build correct-by-construction **net figures
for solids** — Quader/Würfel at minimum; square pyramid and/or triangular prism are welcome.

- Compose on the **scene engine** (`pipeline/scene.py` primitives — `Polyline`/`Region`/`Label`;
  study `pipeline/labeled_diagram.py` and `pipeline/nodelink.py` for the composition pattern),
  registered in `pipeline/assets.py` (`@_generator`) + a German `GENERATION_RECIPES` entry.
  Labels are spec-provided strings so a task can mask ("O = ?", "a = 3 cm").
- The net must be geometrically TRUE (faces share the edges they fold along; equal aspect).
- **Stretch (recommended):** a parametric recipe `quader_oberflaeche` in
  `pipeline/parametrize.py` emitting the net per variant via the fresh `Instance.figure` seam
  (study `pythagoras`/`kreis_umfang_flaeche` — masked unknown, Rechenweg O = 2(ab+ac+bc)),
  template anchored to a REAL `lehrplan/MAT.json` Körper/Oberfläche competence (check the
  catalog for the honest Klasse).
- Tests: net geometry (face dimensions/adjacency), masking, `build_asset` renders, no label
  overlaps (`figtext.overlap_pairs`, see `tests/test_layout.py`). Visually inspect a PNG.

### T2 — "Varianten erzeugen" dashboard surface

`orch.compose_variants(store, template_id, n)` exists and works; it has no UI.

- Add `GET /api/templates` (list `PARAM_TEMPLATES`: id, subject, Klasse, title/anchor) and
  `POST /api/variants` (template_id + n → stage a pending content item, like `/api/compose`
  does). Follow `teachersaid/api/` conventions exactly; the form goes in the **Inhalte** tab
  next to "Arbeitsblatt zusammenstellen" (`api/static/index.html`).
- Figure-emitting templates (pythagoras etc.) must show their per-variant figures in the
  Vorschau like any other asset — verify, don't assume.
- Tests: mirror `tests/test_api.py` patterns — list endpoint, create → item staged and
  verify-clean, offline.

### T3 — ANNO fetch tool + real newspaper media texts

The annotated-text engine's missing genre: real historical newspaper/advert texts
(Medienkompetenz; GPB Quellenarbeit). ANNO (AustriaN Newspapers Online, ÖNB) hosts PD
historical newspapers with OCR full text.

- **`tools/fetch_anno.py`** — the `fetch_wikisource.py` sibling (study it first): given an
  issue/page reference, fetch the OCR text + exact permalink; record shaped for
  `TextSourceRef` (PD basis: publication age / author death; note ÖNB terms honestly).
  Throttled; parser fixture-tested offline.
- **OCR discipline:** the verbatim rule means NO silent corrections. Keep the OCR text as
  fetched; where OCR errors would derail a task, flag the span in the record/annotations for
  SME transcription-verification rather than "fixing" it yourself. Document your policy.
- Annotate 1–2 texts (e.g. a short 1848/1918 report or a historical advert) with the media/
  comprehension annotation kinds; ingest via `tools/ingest_texts.py` → staged for review.
- **Cheap adjacent win (do it):** the roadmap's standing "GPB Quellenarbeit via ANNO/ALEX,
  referenced-only (b2)" — a curated worksheet whose task prompts POINT at the archive (no
  ingest of the source itself). Study `library/gpb_wiener_kongress.py` + `orch.stage_worksheet`.

### T4 — BIO datasets + Tier-2 regional data (Bezirk)

Extend the grounded-facts data layer (`CLAUDE.md` "Grounded facts & data layer"; 12 datasets
exist; study `tools/fetch_statistik_austria.py` and the newest `tools/fetch_un_wpp.py`).

- **BIO:** curate 1–2 datasets genuinely serving `lehrplan/BIO.json` competences (candidates to
  licence-check yourself: Statistik Austria health/nutrition series, CC BY 4.0; OWID/GBIF only
  after an honest licence verdict). Cross-tag `subjects`/`competences` so discovery works.
- **Tier-2 regional:** Bezirk-level population from Statistik Austria open data (CC BY 4.0) —
  extend `fetch_statistik_austria.py` or add a sibling; ideally also a **Bezirk boundary set**
  via `tools/fetch_geo_boundaries.py` (data.gv.at, CC BY) so `matplotlib:choropleth_map` can
  render Bezirke (study how `at_bundeslaender` + the Wien enclave are handled).
- Stage datasets via `orch.ingest_dataset`; sample figure must pass `figure_lint`; parser
  fixtures offline.

### T5 (optional, design-first) — informational Realien

The consciously-deferred half of the Realien asset class (`Documents/realien-design.md`):
informational genres (news-in-levels, factual signs) where **fact-care snaps back** — the
constructed-fiction default does NOT apply. If you attempt it: write a short design note first
(how facts come from the curated datasets / sourced texts; CEFR leveling of REAL content is the
hard part), get the shape right, and build at most ONE flagship. Skip cleanly if T1–T4 consume
your budget — a good skip beats a bad build here.

### Out of scope

- **Audio/TTS** (user decision for this PC — no CUDA + Smart App Control block PyTorch).
- SME review of staged content (that is the user's role).
- FS operator curation (the FS Matura is skill×CEFR, not operator-driven — see
  `Documents/matura-languages-coverage.md`; do not invent a catalog).

## 4. Definition of done

Per task: full suite green (478+ passing, nothing skipped that wasn't), new tests locking the
new behaviour, staged content verify-clean, licence/provenance recorded for everything fetched,
docs updated, SME flags written down. Overall: branches + the report file, nothing pushed,
`main` untouched.
