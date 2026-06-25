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
                                       #       matplotlib, pillow, pyyaml, pymupdf  (pytest for dev)
python -m pytest -q                    # 30 tests, fully offline (no API key required)
python -m teachersaid                  # dashboard → http://127.0.0.1:8000
```

- **LLM generation** uses the Anthropic SDK with `claude-opus-4-8`, adaptive thinking, effort=high
  (see `teachersaid/config.py`). It activates only when `ANTHROPIC_API_KEY` is set.
- **Offline fallback:** without a key, the Physik *Strahlung* hero falls back to the hand-authored
  content object (`teachersaid/demo/strahlung.py`) so the whole loop is demoable with no network.
- Generated PDFs, rasters, and the JSON review store land under `runs/` (git-ignored).

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

### The pipeline (schema §7), and what is deterministic vs LLM

| Step | Module | Nature |
|---|---|---|
| Resolve | `pipeline/resolve.py` | **deterministic** — verbatim competences + `grade_check` (the trust feature) against curated grounding; honest gap notes for anything uncurated |
| Plan | `pipeline/plan.py` | mostly deterministic — envelope→minutes, block-spec skeleton + `DepthTarget` ladder. **The plan IS the idea-stage review artifact.** |
| Generate | `pipeline/generate.py` + `llm/` | **LLM** — `messages.parse()` into a recursion-free generation view, then `to_canonical()` |
| Assets | `pipeline/assets.py` | code-generated (matplotlib), correct-by-construction; `intentionally_flawed` assets are built **wrong on purpose and never "fixed"** |
| Verify | `pipeline/verify.py` | rules (kinds/dimensions/coverage/depth/difficulty); LLM fact-check optional |
| Assemble + derive | `pipeline/assemble.py`, `pipeline/derive.py` | **deterministic** — `derive_nachweis` (coverage + auto-surfaced gaps), `compute_depth` (DepthProfile), `printable_coverage` |
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

## HITL dashboard

Two gates, one `ReviewItem` type (`stage` ∈ idea|content):

```
request → resolve → plan ─►[Gate 1: idea]─approve─► generate→verify→assemble→render ─►[Gate 2: content]─approve─► library
```

`request-changes` re-queues with feedback injected into the generation prompt. Both on-demand and
**batch** (walks the grounded competence map) feed the same gates. The store holds only review items +
the approved-material library — deliberately **no gradebook, no classroom state, no student PII**
(scope discipline: we make the material, we don't run the room).

## Testing

`tests/` mirrors the milestones; everything runs offline (LLM is mocked via an injected generator).
Key invariants under test: schema round-trip; deterministic resolution + honest gaps; the Strahlung
DepthProfile reproduces schema §8 exactly (W2/S4/E1, 78/56 min) and STR.01 surfaces as a gap; all three
projections render + rasterise; student hides keys / teacher shows them; the `intentionally_flawed`
guard; the full two-stage HITL loop + API; the three worked examples exercise the v0.4 deltas.

Run a single file: `python -m pytest tests/test_derive.py -q`.

## Conventions & gotchas

- **`Baustein` lives in `schema/worksheet.py`**, not `schema/blocks.py` (easy import slip).
- In rendering, use `rb.para(value, style)` for RichText (escapes); use `rb.raw_para(markup, style)` when
  you've **already built** inline markup (don't double-escape — that prints literal `<b>` tags).
- Carlito font is used if installed; otherwise Helvetica fallback (the demo renders anywhere).
- PDF→PNG QA uses **PyMuPDF** (`fitz`), not `pdftoppm` (no system poppler dependency).
- Match the surrounding German tone/terminology in product-facing strings; the user is the domain SME
  (physicist, Austrian) and fact-checks the physics and the German.
- Don't relitigate decisions recorded in `project-handoff.md §4`; they are durable.

## Where to look first

`project-handoff.md` (intent) → `Documents/lehrplan-bundle-schema-v0.3.md` (data model) →
`teachersaid/schema/` (the model in code) → `teachersaid/pipeline/` (the engine) →
`teachersaid/demo/strahlung.py` (a complete worked content object).
