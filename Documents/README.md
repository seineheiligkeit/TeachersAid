# Documents/ — index

The design-doc set has grown; this index is the map. Each doc keeps its purpose; **superseded docs are
flagged, not deleted** (they're design history). When two docs seem to disagree, the higher tier wins, and
`invariants.md` wins on the hard rules.

## ⭐ Start here / canonical (read these first)

| doc | what it is |
|---|---|
| [`../project-handoff.md`](../project-handoff.md) | Intent + data model — the source of truth for *what* and *why*. |
| [`invariants.md`](invariants.md) | **The hard rules, their rationale, and their boundaries.** Read before letting a remembered rule block an idea. |
| [`../CLAUDE.md`](../CLAUDE.md) | Working guide for Claude Code (architecture, conventions, where-to-look). |
| [`feature-roadmap.md`](feature-roadmap.md) | Prioritised capability backlog ("start here tomorrow" at top). |
| [`lehrplan-bundle-schema-v0.3.md`](lehrplan-bundle-schema-v0.3.md) | **Schema = type source of truth** (v0.4 deltas are additive; v0.5 specced). |
| [`implementation-notes.md`](implementation-notes.md) | The runnable engine: pipeline + rendering + HITL dashboard. |

## 🔭 Active design (current / forward features)

| doc | feature |
|---|---|
| [`sachverhalt-content-layer-design.md`](sachverhalt-content-layer-design.md) | **The content/exposition layer (History first)** — Sachwissen as a first-class layer. Q1 (authoring) settled. |
| [`realien-design.md`](realien-design.md) | **CEFR-leveled communicative reading for modern FS** — the Realie as Sprechanlass (*purpose-appropriate rigor*: invent the facts, vet the language). **Phase 1 built** (A2 *At the station* flagship). |
| [`history-facts-provenance-design.md`](history-facts-provenance-design.md) | GPB expression-provenance asset class (the machinery Sachverhalt reuses). |
| [`block-library-design.md`](block-library-design.md) | The block as the durable library unit + the composer. |
| [`tts-audio-engine.md`](tts-audio-engine.md) | F5-TTS audio / Hörverstehen engine + voice library. |
| [`oberstufe-roadmap.md`](oberstufe-roadmap.md) | Extending to AHS Sek II (5.–8. Kl.). |
| [`schema-roadmap-v0.4-v0.5.md`](schema-roadmap-v0.4-v0.5.md) | Schema version roadmap (v0.5 Lernarrangement). |
| [`master-library-plan.md`](master-library-plan.md) | Quality bar + per-subject coverage plan. |
| [`rendering-handoff-brief.md`](rendering-handoff-brief.md) | Renderer-swap contract (entry points, projection rules). |
| [`diffusion-handover.md`](diffusion-handover.md) | Brief for the SME's image-gen agent (decorative assets). |

## 📚 Reference (stable lookup)

| doc | topic |
|---|---|
| [`matura-operators.md`](matura-operators.md) | The SRDP Operatoren grounding (decision rule + full write-up). |
| [`matura-calibration.md`](matura-calibration.md) | cognitive_level → AFB → difficulty calibration vs the exam archive. |
| `matura-{math,deutsch,latein,languages}-coverage.md` | Per-subject Matura demand maps. |
| [`subject-coverage-audit.md`](subject-coverage-audit.md) | Unterstufe subject-model audit against the schema. |
| [`platform-definition.md`](platform-definition.md) | Positioning — "what we are and deliberately are not". |
| [`architecture-review.md`](architecture-review.md) | Restructuring review (27 Jun 2026). |
| [`dashboard-review.md`](dashboard-review.md) | Dashboard structuring notes. |
| [`diffusion-figures-handover.md`](diffusion-figures-handover.md) | Content-figure diffusion **test-run** (experiment record, not the live path). |

## 📖 Worked-content companions (German, SME-curated)

| doc | content |
|---|---|
| [`strahlung-rack.md`](strahlung-rack.md) · [`zwentendorf-faden.md`](zwentendorf-faden.md) | Vertiefungs-Rack / -Faden for the Strahlung hero. |
| [`worked-examples-three.md`](worked-examples-three.md) | The three worked content examples at object level. |

## 🏛 Historical / superseded (kept for provenance — **not current**)

| doc | status |
|---|---|
| [`lehrplan-bundle-schema.md`](lehrplan-bundle-schema.md) | Schema **v0.1** — superseded by v0.3. |
| [`lehrplan-bundle-schema-v0.2.md`](lehrplan-bundle-schema-v0.2.md) | Schema **v0.2** — superseded by v0.3. |

## Root-level companions (outside `Documents/`)

`../README.md` (project README) · `../CLAUDE.md` (Claude guide) · `../AGENTS.md` (Codex guide — sibling to
CLAUDE.md) · `../project-handoff.md` (intent).

---

**Housekeeping notes (for a future tidy, non-urgent):** the schema v0.1/v0.2 docs could move to a
`Documents/archive/` folder; the four `matura-*-coverage` docs are a stable family and fine as-is;
`AGENTS.md` and `CLAUDE.md` are deliberately parallel (two assistants) — keep them in sync when invariants
change.
