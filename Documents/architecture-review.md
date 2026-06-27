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
