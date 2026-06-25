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
2. **Dumb composer.** The `compose` stage (§4) + a compose view; render composed worksheets.
3. **Richness + smarter selection.** Populate `scope` variants; better ordering/coherence; begin
   difficulty calibration on the now-reused blocks.

## 9 · Open questions (for as we build)

- `scope` as a 3-band enum vs. a finer measure — start with 3 bands.
- How aggressively to dedup near-identical blocks (a `family` + a similarity check later).
- Connective-generation quality for coherence — revisit after seeing v1 compositions.
