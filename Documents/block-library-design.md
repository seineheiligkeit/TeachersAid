# Block library + composition — design note

**Status: v1 proposal, 25 June 2026.** Refactor the master library from *worksheets* to *blocks*:
generate and curate a library of self-contained, competence-anchored **blocks** (tasks and learn-from
texts), and build a worksheet by **composing** the right blocks for the teacher's competence targets and
time. This is the "template/shape + assembler" layer the design parked for after v0.4
([project-handoff.md](../project-handoff.md) §7; [schema v0.3](lehrplan-bundle-schema-v0.3.md) §9),
approached bottom-up. Schema and rendering barely move; the change is additive.

## 1 · Decisions (locked with the SME)

- **The block is the library unit.** A worksheet is a *composition* of blocks, not a monolith.
- **Granularity is flexible.** A block may be one micro-item *or* a full multi-step arc — whatever is
  pedagogically coherent on its own. Not constrained to "small."
- **Learn-from text is a block.** A standalone educational paragraph the student just reads
  (`InfoBlock`) is a first-class library block, alongside tasks, quizzes, experiments, figures.
- **Framing is composed, not stored.** The worksheet's *framing intro* and *transitions* (the "today we
  look at… → first… → now…") are generated at compose time, not kept in the library.
- **A richness/scope axis is first-class** (see §3) — the same block-concept exists compact → extended.
- **The composer is dumb first.** Focus now is the **library foundation**; composition starts as simple
  selection + a light connective pass. No optimizer, no difficulty solver on day one.

## 2 · What a library block is

A self-contained, competence-anchored unit of worksheet content that stands on its own:
- **TaskBlock** — an exercise (any `kind`: quiz/MC, open response, true-false-justify, data
  interpretation, experiment protocol, create/produce, …), possibly a multi-step arc.
- **InfoBlock** — learn-*from* content: a readable explanatory text, a key fact, a worked example, a
  procedure, a (code-generated) figure/data reference.

Each carries its own teacher layer (`answer_key`/`acceptable_reasoning`, `rubric`, `watch_outs`) and its
assets. What is **not** a library block: the worksheet-level framing intro and the transitions between
blocks — those are a function of *which blocks were chosen*, so they're produced by the composer.

## 3 · The selection surface (block metadata)

Most of what the composer needs is **already on every block** (schema v0.3 §4):

| Axis | Field | Meaning |
|---|---|---|
| Competence | `serves[]` (+ `relation`) | which catalog competence(s) it exercises/builds |
| Thinking depth | `cognitive_level` | remember → … → create |
| Dimension | `dimensions[]` | W/E/S, etc. (subject model) |
| Modality | `modality` | printable / oral / enactive (audio) |
| Time | `est_minutes` | for fitting the envelope |
| Constraints | `flags` | equipment_dependent / contested / freshness_decay / local |

**New, additive** (a thin library record wrapping the `Block`):
- `id`, `subject`, `klasse`, `kompetenzbereich` tags; `status` (in-review / approved); `provenance`
  (authored / LLM / harvested-from `<worksheet>`); `source` (user/ai).
- **`scope`** — the richness/width band: `compact` · `standard` · `extended`. The *content extent*, not
  the thinking depth: a single block-concept (e.g. an intro text on radioactivity, or a half-life quiz)
  exists as a short version for an Einzelstunde and a richer version for a longer block. Correlates with
  `est_minutes`; **orthogonal to `cognitive_level`** (an analyze-task can be compact or extended).
- **`family`** (optional) — groups the variants of one concept, so the composer can pick the `scope` that
  fits without treating them as separate competence coverage.

So the library is a matrix: **competence × cognitive_level × modality × scope → blocks**. That is also the
coverage/stats model (§6) — what exists, what's thin, what's empty, at block granularity.

## 4 · Composition (dumb v1)

Input: `subject`, target competences (optionally desired levels), `time envelope`, modality constraints
(printable for a worksheet), a `DepthTarget`. Algorithm (deliberately simple):
1. **Select** approved blocks whose `serves` ⊆ the targets, honouring modality and `flags`; prefer the
   `scope` that suits the envelope; pick one variant per `family`.
2. **Fit** to the time budget by `est_minutes`; satisfy the `DepthTarget` ladder (≥N at analyze+,
   resource-independent minutes).
3. **Frame** — generate only the connective tissue: a `kernfrage`, a short intro that frames the chosen
   blocks (+ any shared context they assume), and transitions. Order blocks into a coherent climb.
4. Emit a `WorksheetContent` → the **existing** `assemble`(derive Nachweis/DepthProfile) → `verify` →
   `render`. Nothing downstream changes.

No optimizer; no difficulty calibration inside the composer (still the open hard problem — but the block
library *helps* it: per-block difficulty gets tagged and validated through reuse). Flagship worksheets
can still be authored bespoke; composition is the path to breadth.

**Coherence is the thing to watch:** a worksheet is more than on-target blocks. v1 mitigates with the
framing/transition pass + ordering; if that's not enough, blocks can declare shared-context needs.

## 5 · Architecture delta

- **Schema (`schema/`):** thin additions — a `LibraryBlock` record (a `Block` + the §3 metadata) and a
  small composition manifest (chosen block ids + order + the generated framing). `Block`/`Baustein`/
  `WorksheetContent` are otherwise unchanged.
- **Store/dashboard:** a **block library** with its own review queue + the competence×level×modality×scope
  stats matrix; a **"Arbeitsblatt zusammenstellen"** (compose) view. The brainstorm→content flow we built
  adapts: a brainstorm idea is *fleshed out into blocks* (one or more), reviewed as Blöcke, approved into
  the library. The "Inhalte" content view becomes the **block** review; worksheets are a compose output.
- **Pipeline:** `generate` targets *blocks* (per competence × level × scope) instead of whole sheets; a
  new **`compose`** stage (§4); `assemble`/`derive`/`verify`/`render` unchanged.
- **Rendering:** **untouched.** A composition is a `WorksheetContent` → the pure projections render it as
  now. The [rendering-handoff-brief.md](rendering-handoff-brief.md) stands.
- **Catalog/grounding:** unchanged (still the competence anchor).

## 6 · Coverage / statistics (block-level)

The Statistik tab shifts from "N worksheets" to the **library matrix**: per subject → per competence →
how many approved blocks at each cognitive level / modality / scope; what is **covered** (≥1 approved
block) vs **empty**. This is the populate-and-track view, but sharp — and it directly drives "Vorschläge
aus Lehrplan" (suggest blocks for the empty cells).

## 7 · Migration — nothing wasted

- **Harvest the three example worksheets** (Strahlung, Immunsystem, unfaires Spiel) into the library:
  each task is already a verify-clean, competence-anchored block (~21 blocks) — they become the seed.
  Their intros stay as either library `InfoBlock`s (the readable ones) or example framing.
- The dashboard, brainstorm flow, stats, and launcher all carry over (extended, not replaced).

## 8 · Phasing

1. **Library foundation — ✅ built (25 Jun 2026).** `LibraryBlock` (`library/block.py`) + `scope`/`family`;
   `BlockStore` (`store/blockstore.py`); `harvest`/`seed_blocks` (the 3 examples → ~21 blocks); the
   **Bausteine** review tab + the block-level **Statistik** matrix; `tests/test_blocks.py`.
2. **Dumb composer — ✅ built (25 Jun 2026).** `pipeline/compose.py` (select approved blocks → time-fit
   → ladder order → template framing → `WorksheetContent`); `orch.compose_worksheet`; the **Inhalte**
   "Arbeitsblatt zusammenstellen" form + `POST /api/compose`; `tests/test_compose.py`. Verified:
   einzelstunde → 4 tasks/~46 min, block → 7 tasks/~78 min, both verify-clean. (Assets don't travel with
   blocks yet → figure-info-blocks skipped in composition.)
   - **2.1 — ✅ built (25 Jun 2026).** Composition targets a **Kompetenzbereich** directly
     (`resolve_kompetenzbereich`) instead of only a fuzzy topic-string match, so subjects whose KBs are
     numbered content areas (MAT *"4: Daten und Zufall"*) or W/E/S strands (BIO) compose reliably — the
     topic stays the display title. KB picker in the form + `GET /api/kompetenzbereiche`. Found + fixed a
     pre-existing rendering escape bug along the way (response-spec product hints printed literal `<i>`
     tags — `rb.para` → `rb.raw_para` with the dynamic part escaped).
3. **Richness + smarter selection (the "compose well" phase).** Independently-shippable items, each
   grounded in a limitation hit during the breadth build (25 Jun 2026). The library is now SME-approved
   (425 blocks, 64 worksheets, 16 subjects, ~33% catalog coverage), so these operate on real stock.
   - **3a · Scope/richness variants — the "width" axis — ✅ built (25 Jun 2026).** *Was:* every block
     `scope="standard"`, so **doppelstunde == block**. The composer's scope-preference + family-dedup were
     already built (Phase 2); the missing piece was variants-with-families. Added `orch.ingest_scope_variant`
     (validate a generated `compact`/`extended` task through the verify seam → store as a LibraryBlock with
     `family`=original id + the given `scope`, and stamp the original's `family` so the trio is one family)
     and `tools/scope_variants.py` (brief → subagent → ingest). Demo (Physik *Strahlung*, 7 families):
     einzelstunde→compact (~45 min) · doppelstunde→standard (~78) · block→extended (~114) — same concepts,
     scaled richness. `tests/test_compose.py` locks both the composer differentiation and the seam.
   - **3b · Angle/Kernfrage-aware composition.** *Problem:* compose-by-KB takes *all* KB blocks and is
     deterministic → two einzelstunde composes of one KB give the **identical** sheet; no notion of the
     Kernfrage/angle. *Change:* `compose(..., kernfrage=?, competences=?)` selects only blocks serving the
     chosen angle and frames with that Kernfrage. *Unlocks:* many distinct, focused worksheets per theme.
     *Size:* medium.
   - **3c · Assets travel with blocks — ✅ built (25 Jun 2026).** *Problem:* assets are code-generated at the worksheet
     level, not attached to harvested blocks → the composer **skips figure-info-blocks** (e.g. the
     Strahlung spectrum never appears in a composed sheet). *Change:* `LibraryBlock` carries the `Asset`
     spec(s) for its `asset_refs`; `harvest()` captures them; `compose()` aggregates the chosen blocks'
     assets into `WorksheetContent.assets`; the renderer (already asset-aware) builds them. *Unlocks:*
     composed sheets include their figures/data. *Size:* small–medium, self-contained.
   - **3d · Difficulty calibration (the open hard problem).** *Problem:* no difficulty signal beyond
     `cognitive_level` + `est_minutes`. *Change (honest, staged):* a `difficulty` field
     (LLM/author-estimated, SME-adjustable, e.g. 1–3) surfaced in selection + the DepthProfile; a
     `DepthTarget` can request a mix. *Caveat:* real psychometric calibration needs student-response data,
     which we deliberately don't collect — so this stays an SME-refined estimate, not a measured value.
     *Size:* medium, inherently approximate.
   - **3e · Coherence & framing pass.** *Problem:* compose framing is a fixed template + generic Kernfrage,
     no transitions; cross-source coherence is untested. *Change:* an optional LLM framing pass (Kernfrage
     + intro + transitions for the *chosen* set) — a deliberate shift from the no-LLM composer. *Unlocks:*
     sheets that read as a lesson, not a pile of on-target tasks. *Size:* medium.
4. **Assets (Phase 4) — ✅ COMPLETE (26 Jun 2026).** The asset layer is operationalized: a parameterized,
   correct-by-construction **code-generator library** (pluggable backends — `matplotlib:` content recipes +
   `svg:` decorative kit now; `diffusion:` seam ready for the SME's image-gen agent, brief in
   **[diffusion-handover.md](diffusion-handover.md)**), **math-as-asset** (mathtext), re-enabled asset-bearing
   generation (#1), a **`MediaPolicy` entry-gate** (`pipeline/media_policy.py`, in `verify`: content-bearing →
   code-gen/sourced, decorative → content-free) (#3), the **asset-review surface** (dashboard *Abbildungen*) +
   an **asset library** for the file-backed decorative/sourced classes (`store/assetstore.py`, parallel to the
   block library) (#2/#4). Design + product principle ("platform consolidates a vetted library, not
   live-generates") in **[schema-roadmap-v0.4-v0.5.md](schema-roadmap-v0.4-v0.5.md)** (Post-breadth roadmap).
5. **Lernarrangements (Phase 5 = v0.5).** Now unblocked. schema → hand-authored **Geographie (GWB)** hero →
   `renderTeacherOrchestration` → generation. Reaches the oral/social/enactive competences worksheets can't.

## 9 · Open questions (for as we build)

- `scope` as a 3-band enum vs. a finer measure — start with 3 bands.
- How aggressively to dedup near-identical blocks (a `family` + a similarity check later).
- Connective-generation quality for coherence — revisit after seeing v1 compositions.
