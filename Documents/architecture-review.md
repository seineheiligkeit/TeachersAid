# Architecture review — does the project need restructuring?

**Date: 27 June 2026.** Written after the grounded-facts data layer shipped, in response to three
big-picture questions: (1) should real-world data be supplied more *smartly* — a staged research →
ideation → task-making → consolidation → rendering pipeline? (2) has the organic growth created debt
worth restructuring? (3) will the JSON-file storage eventually need a real database? Grounded in a
three-front investigation of the persistence layer, the generation flow, and the data-model
relationships. **Verdict up front: no rewrite — the load-bearing architecture has held. Three targeted
moves, in order.**

## 1 · A smarter supply of real data + the staged pipeline

**The pipeline already is those stages.** `resolve`+`plan` (ideation), `generate` (task-making),
`assemble`+`derive` (consolidation), `render` — loosely coupled, mostly pure functions passing one
`WorksheetContent`. What's genuinely missing is **research**, and the investigation found something
sharper than "no research stage":

**The data layer is bolted onto the wrong end.** Real data is resolved at `assemble` time — *after*
task-making. The generation brief doesn't tell the model which datasets exist. So today the model
**authors the numbers, invents a citation, and `ground_citations` only overwrites the citation text**
if the `dataset_id` happens to match. A figure can therefore carry *LLM-invented values next to a real,
resolved citation* — the most dangerous state in the project (it looks verified and isn't). c0094.t2 is
honest only because its values were hand-copied; the *mechanism* is "author-then-cite," not "sourced."

**The fix is to invert the flow, not restructure the stages:**
- **Research = a library-building stage** (not per-request): demand-driven curation of datasets into the
  vetted catalog by deterministic tooling, HITL-gated. The bones exist (`tools/fetch_statistik_austria.py`
  + `DatasetStore`). Generalise it and make the catalog **discoverable by subject/topic/competence**, so
  ideation can ask "what real data exists for *Bevölkerung Österreich*?" — **data and ideas interplay**:
  the available open data *suggests* what tasks are buildable for a given Kernfrage/competence.
- **Feed that catalog into the brief**, and make `data_source` figures **derive their values from the
  dataset slice** — turning "select never author" from a *label* into a *guarantee* for numbers.

**Pushback (held):** no live, per-request web-research agent — that reintroduces the hallucination the
project exists to kill. Research stays deterministic tooling → HITL catalog; the per-request flow
*selects*. `compose.py` already proves "select from an approved pool" for blocks; we extend the same
discipline to data.

## 2 · Restructure given organic growth?

The core architecture is genuinely good and survived contact with real complexity — the
`blocks → content → rendering` dependency discipline held. **No rewrite.** The debt is concentrated:

- **~205 lines of copy-paste across 6 near-identical store classes** (`Block/Asset/Arrangement/Dataset/
  Review/Feedback`). The clearest organic-growth debt *and* the seam that decides whether a future DB
  migration is cheap. **Consolidating them into one repository is the highest-value refactor available.**
- **`ReviewItem` embeds a full snapshot of the resolution** (verbatim competences) → silently stale when
  the 2026/27 Fassung lands. A latent bug, not hypothetical (the Fassung expires 2026-08-31).
- **File paths leak out of stores** (`RenderArtifacts` stores absolute paths) — the other thing that
  would fight a backend swap.
- **Inconsistent ID schemes** — competences are namespaced + stable; asset IDs are only locally unique;
  the rest are opaque counters. Not urgent.

## 3 · When does JSON → a real database become necessary?

It's already relational — 5 mutable entity types + a read-only reference table (the ~530-competence
catalog) + several many-to-many (blocks↔competences, worksheets↔blocks, assets↔blocks) + a polymorphic
feedback FK **with no referential integrity**. A graph hiding in flat files. But "relational" ≠ "needs a
DB yet." The triggers, in the order they'll bite:

1. **Scan cost.** Every dashboard call full-scans + deserialises *all* records — no index, no cache. 592
   block files today, hit on nearly every endpoint, with multi-store "joins" done in Python (`/api/assets`
   scans blocks+items; `stats` scans all blocks; `compose` scans approved blocks). At low **thousands**,
   the dashboard starts to drag. First wall.
2. **Cross-entity queries** for richer composition/selection ("approved task blocks serving competence X,
   difficulty 2, with a sourced figure") — today a full scan + Python filter.
3. **Concurrency.** A single-process `threading.Lock` only; two processes (even the CLI while the server
   runs) can clobber a file. This turns "slow" into "data loss" — and it's exactly what the
   institutional/multi-user GTM implies.

**Recommendation: SQLite, not Postgres** — single embedded file, zero-ops, ACID, real indexes + joins +
JSON columns. Keep the Pydantic models as a JSON column + a few indexed columns for the query keys.
**Not now.** Triggers: dashboard listing feels slow, OR cross-entity queries are needed, OR multi-user.
**Buy the cheap insurance now:** consolidate the stores (move #2) + stop leaking absolute paths — then
the migration is a contained backend swap. **Never migrate the `lehrplan`/`grounding` catalog** — it's
read-only reference data, already `lru_cache`'d, fine as files forever. Only the mutable, growing,
cross-referenced `runs/` stores (blocks especially) eventually want SQLite.

## Decisions & sequencing

1. **Invert the data flow (in progress, started 27 Jun 2026).** Make the dataset catalog discoverable by
   subject/topic/competence; feed it into the generation brief; derive `data_source` figure values from
   the dataset. Makes "select never author" true for numbers; data and ideas interplay. *(This document's
   companion build.)*
2. **Consolidate the 6 stores into one repository — DONE 27 Jun 2026.** `store/base.py::JsonStore`
   (Generic[T]) holds the shared file-I/O + sequential-id counter + status-preserving `upsert`; each
   store subclasses it (model + subdir + its own typed `list()`). ~210 lines of duplication removed,
   behavior identical (132 tests green), per-instance lock (was a shared module lock). Review (create)
   and Feedback (append-only) keep their own lifecycles on the same base — not force-fit. This is the
   seam a future SQLite backend swaps behind. *(Path-leak in `RenderArtifacts` deferred — separate change.)*
3. **Figure-recipe families** (timeline, Klimadiagramm) — feature work on a cleaner base.
4. **SQLite migration** — only when a trigger above actually fires. Do it *separately* from #2.

Out of scope deliberately: rewriting the stage architecture; a live research agent; migrating the
read-only catalog; Postgres/a server DB.

---

# Architecture review II — 19 July 2026

**Written after the Session-19–24 feature wave** (Mischpult, Fermi, Zeitband, scene3d, the content
programs, five breadth campaigns). Grounded in a three-front empirical audit: the import graph,
the persistence/API layer, and the extension seams (registries, ingest tools, tests). **Verdict up
front: the June verdict stands — no rewrite. The layered core held under heavy growth.** But two of
June's predictions have now *fired*, and the new debt is concentrated in three hub files. Six moves,
in order.

## What held (the good news, verified)

- **`schema/`, `grounding/`, `rendering/` are import-clean** — rendering still imports only schema,
  exactly as the projection guarantee requires. `pipeline/` is still the only importer of `llm/`.
- **The recipe/scene domains are a clean star, not a mesh.** `wahl` does not import `finanz`;
  physics does not import chemistry. All ~22 domain modules (8 recipe domains, 14 scene families)
  fan in to two hubs (`parametrize`, `assets`) and nothing else. Domains can keep multiplying
  without cross-contamination — the risk lives entirely in the hubs.
- **The June store consolidation held with zero drift.** All 10 mutable stores subclass `JsonStore`;
  the two stores added since (`ImageSourceStore`, `DemandStore`) subclassed rather than copy-pasted.

## What fired since June

- **The scan wall arrived.** Blocks: 592 → **1606** (2.7× in three weeks — breadth campaigns work).
  Every dashboard call still full-scans with zero caching; `/api/review-queue` scans SEVEN stores
  per request; the coverage trio each re-scan all blocks independently. June said "drag at low
  thousands" — we are at low thousands.
- **The path leak is proven broken, not hypothetical.** 246 store records carry dead absolute
  artifact paths from *three different machines* (`C:\Users\sebas\…`, `C:\Users\Sebas\…\Claude\…`,
  `/home/user/…`). The system stays usable only via the lazy self-heal — which re-renders 3 PDFs +
  rasterises + spins up a *fresh* `AssetStore()` full scan per stale item viewed, then writes the
  next machine-specific path back in. The self-heal is masking the bug at real compute cost.
- **The Fassung snapshot bug is now on a 43-day fuse.** Both `_meta.json` say
  `valid_to: 2026-08-31`. **250 ReviewItems embed a frozen `LehrplanResolution`** (verbatim
  competence texts); nothing in the codebase ever re-resolves a stored item; `resolve()` only
  appends a soft German note after expiry — it never blocks or flags. After 1 Sept the corpus
  silently claims anchoring against an expired catalog. This is a *calendar* bug, independent of
  corpus size.

## The new debt (from the growth wave)

- **`pipeline/orchestrator.py` is a god-module and the layer-inversion epicenter.** 954 lines,
  24 public functions, **42 deferred imports** pulling `store/` and `library/` — the documented
  "top" layers — *down into* pipeline to dodge cycles. Every new content type bolted another
  `ingest_*`/`compose_*` trio onto it; it grows linearly with content types. `wahl.py` even calls
  back up into it (`from .orchestrator import stage_worksheet`).
- **One true layering violation:** `llm/prompts.py:13` imports `pipeline.plan.WorksheetPlan` at top
  level (plus deferred grounding imports). The one-directional pipeline→llm story is currently false.
- **The 3-place-edit domain onboarding.** A new parametric domain edits (1) its own module,
  (2) the `# noqa: E402` side-effect import block at the *bottom* of `parametrize.py`, and (3) the
  central 731-line `library/templates.py`. Forget #2 and the failure is a *runtime* `ValueError`
  in `instantiate`, not an import-time error. `assets.py` (1810 lines, 51 generators) has the same
  centralized-pull shape: scene modules live in their own files but assets.py wraps each in a local
  `@_generator`, so every new figure still edits the monolith. These two hubs + templates.py are the
  files every parallel domain effort collides in.
- **Ingest tools are copy-paste:** `_repair_text` + `_GERMAN_QUOTE_FIX` are byte-identical in 4
  `tools/ingest_*.py`; each re-implements the normalize/load/dry-run/persist skeleton. The sole
  reuse is `ingest_arrangements.py` importing from `ingest_batch` via `sys.path` — fragile.
- **No shared test infrastructure:** 93 test files, no `conftest.py`; ~70 files touch
  rendering/matplotlib and each re-does its own build setup.
- **`api/app.py` (76 routes) is accreting domain logic** (`_dataset_figure_asset` ≈ 50 lines of
  figure-recipe dispatch; the re-render self-heal orchestration lives in HTTP handlers), and
  `index.html` is a 1184-line vanilla-JS monolith — the client-side twin.
- **Writes are not atomic** (`write_text`, no tmp+rename) and locks are per-*instance* while several
  code paths construct fresh store instances — so even single-process locking is weaker than
  intended; two processes (CLI + server) can clobber.

## Decisions & sequencing

1. **Fassung refresh path — before 1 Sept (highest severity, calendar-bound).** Build a
   re-resolve pass: a tool + orchestrator function that re-resolves every stored item against the
   current catalog, diffs competence ids/texts, and flags changed items for SME re-review (the same
   status-preserving discipline as everywhere else). Make `resolve()` escalate an expired Fassung
   from a soft note to a verify-visible warning. This is the prerequisite for the 2026/27 re-parse
   whenever it lands.
2. **Store insurance — one contained change to `store/base.py` + `store/models.py`.**
   (a) mtime-keyed in-memory cache for `_list` (kills the scan wall for years at this scale);
   (b) atomic writes (tmp + `os.replace`); (c) module-level store singletons so the per-instance
   lock actually guards; (d) **repo-relative artifact paths** (relative to `RUNS_DIR`, resolved at
   read; one-time migration script for the 246 stale records). Together these keep June's
   "contained SQLite swap" promise. SQLite itself: still only when a trigger *survives* (a) — the
   June triggers and the never-migrate-the-catalog rule stand.
3. **Extract orchestration OUT of pipeline.** New top-level package (e.g. `teachersaid/orch/`)
   *above* store/library, split per concern (ideation/gate-1 · ingest per content kind · compose ·
   review transitions). `pipeline/` becomes pure engine again; the 42 deferred imports become
   ordinary top-level imports in a layer that is *allowed* to see stores; the `wahl → orchestrator`
   back-edge dies. Mechanical, high-value, enables everything after it.
4. **Fix the llm back-edge.** Move `WorksheetPlan` (pure data, no behavior that needs pipeline) into
   `schema/` — `llm/` then depends only downward and the documented discipline is true again. Small.
5. **Harden the registration seams — before the next domain wave.** (a) pkgutil auto-discovery of
   recipe/scene domain modules (kills the bottom-of-file import block); (b) domain-owned templates —
   `wahl.py` already proves the pattern — with `library/templates.py` reduced to an aggregator;
   (c) an import-time drift test asserting every template's recipe is registered (the
   capabilities-drift test is the model); (d) split `assets.py` into the registry/dispatch core +
   `pipeline/figures/*` recipe modules that self-register next to their scene families.
6. **Small consolidations, opportunistic:** `tools/ingest_common.py` (the shared normalizer +
   skeleton); move `_dataset_figure_asset` and the self-heal orchestration from `api/app.py` into
   orch; a shared `tests/conftest.py` with cached build/render fixtures.

**Non-moves (deliberate):** no rewrite; no Postgres; no frontend framework (split `index.html` into
per-tab scripts at most, only when it actually hurts); grounding catalogs stay read-only files
forever; no plugin system beyond auto-discovery — the domain star is healthy, don't over-abstract it.
