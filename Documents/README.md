# Documents/ — the map

Every doc in one of six shelves. **Superseded docs are archived, not deleted** (`archive/` — design
history). When two docs seem to disagree, the higher shelf wins, and `invariants.md` wins on the hard
rules. *(Maintained by hand — add a line here when you add a doc; see CLAUDE.md "Updating this file".)*

## ⭐ Canonical (read these first)

| doc | what it is |
|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | **The operating manual** — invariants, architecture, seams, gotchas. Start here for any work. |
| [`../project-handoff.md`](../project-handoff.md) | Intent + the dated session history (§4 = durable decisions — do not relitigate). |
| [`invariants.md`](invariants.md) | **The hard rules, their rationale, and their boundaries.** Read before letting a remembered rule block an idea. |
| [`feature-roadmap.md`](feature-roadmap.md) | The plan — the build-for-joy feature program ("▶ Start here" at top). |
| [`lehrplan-bundle-schema-v0.3.md`](lehrplan-bundle-schema-v0.3.md) | **Schema = type source of truth** (v0.4 deltas additive + implemented; v0.5 built). |

## 🔭 Live design docs (each governs a feature's rules)

| doc | feature |
|---|---|
| [`block-library-design.md`](block-library-design.md) | The block as the durable library unit + the composer (phases 1–3 built). |
| [`difficulty-model.md`](difficulty-model.md) | **Difficulty as a computed ADVISORY** (roadmap C4) — transparent features, anchor-and-nudge weights, the honest "not learnable from this corpus" finding. |
| [`dramaturgy-design.md`](dramaturgy-design.md) | **The dramaturgy engine (C5, design-only)** — a phase grammar (Einstieg→Erarbeitung→Sicherung→Transfer) over `compose`; phase-affinity on blocks, grammar ordering, bridging prose, coherence measurement. |
| [`figure-styleguide.md`](figure-styleguide.md) | **The figure engine**: figstyle (semantic colour roles, dash ramp, house font) + the scene engine + the data-figure intent→recipe system. |
| [`scene3d-geometry-design.md`](scene3d-geometry-design.md) | 3D analytic geometry as projected Schrägriss scenes — validated prototype; promotion path (roadmap A7). |
| [`sachverhalt-content-layer-design.md`](sachverhalt-content-layer-design.md) | The content/exposition layer — Sachwissen as a first-class curated module (History · Bio · Geo built). |
| [`realien-design.md`](realien-design.md) | CEFR-leveled communicative FS reading — *purpose-appropriate rigor* ("invent the timetable, vet the French"). |
| [`history-facts-provenance-design.md`](history-facts-provenance-design.md) | Expression provenance (GPB) — original/adapted/quoted, rights gates, the machinery Sachverhalt reuses. |
| [`tts-audio-engine.md`](tts-audio-engine.md) | The F5-TTS audio backend + voice library (built; open items in §7). |
| [`illustration-design.md`](illustration-design.md) | **The image program** (accepted 5 Jul 2026, not built): image = claim + rendering; decorative/depictive/content lanes; Flux backend; Beschriftungs-hybrid. |
| [`illustration-style-contract.md`](illustration-style-contract.md) | The versioned agent-time generation prefix, print-first warmth, age register, seductive-details limits, and best-of-N review contract. |
| [`external-experiment-report-images.md`](external-experiment-report-images.md) | Wave B implementation report: gates, candidates, prompts, staged flagships, binary sync paths, and SME decisions still open. |
| [`schema-roadmap-v0.4-v0.5.md`](schema-roadmap-v0.4-v0.5.md) | Schema version roadmap (v0.4 fields + v0.5 Lernarrangement — both implemented; kept as the design record). |
| [`oberstufe-roadmap.md`](oberstufe-roadmap.md) | The Sek-II expansion map (Phase 0/1 built; the rest is opportunity inventory). |
| [`master-library-plan.md`](master-library-plan.md) | The quality bar (blackboard test) + per-subject coverage plan. |

## 📚 Reference (stable lookup)

| doc | topic |
|---|---|
| [`rendering-handoff-brief.md`](rendering-handoff-brief.md) | The renderer-swap contract (entry points, the three projection rules, what's free to change). |
| [`matura-operators.md`](matura-operators.md) | The SRDP Operatoren grounding — decision rule + full write-up. |
| [`matura-calibration.md`](matura-calibration.md) | cognitive_level → AFB → difficulty, calibrated against the exam archive (model holds). |
| `matura-{math,deutsch,latein,languages}-coverage.md` | Per-subject Matura demand maps (from the full-archive extraction). |
| [`platform-definition.md`](platform-definition.md) | Positioning — "what we are and deliberately are not". **Dormant by decision** (build-for-joy); retained for a possible later phase. |
| [`subject-coverage-audit.md`](subject-coverage-audit.md) | Unterstufe subject-model audit against the schema (forced `modality` + audio). |
| [`architecture-review.md`](architecture-review.md) | The no-rewrite verdict + the three sequenced moves (two done; SQLite awaits a trigger). |

## 🤖 Agent briefs (self-contained contracts for a sub/external agent)

| doc | for |
|---|---|
| [`diffusion-handover.md`](diffusion-handover.md) | The SME's image-gen agent — decorative, content-free assets (the operative batch brief; the wider program is `illustration-design.md`). |
| [`diffusion-figures-handover.md`](diffusion-figures-handover.md) | The content-figure diffusion **experiment** (data-collection brief; not the live path — the illustration program's hard lines supersede its ambitions). |
| [`uebungsreihe-upgrade-brief.md`](uebungsreihe-upgrade-brief.md) | The chemistry Übungsreihen upgrade (executed — c0167–c0169 approved; kept as the genre-framing reference). |

## 📖 Worked-content companions (German, SME-curated)

| doc | content |
|---|---|
| [`strahlung-rack.md`](strahlung-rack.md) · [`zwentendorf-faden.md`](zwentendorf-faden.md) | Vertiefungs-Rack / -Faden for the Strahlung hero (deliberately overproduced for selection). |
| [`worked-examples-three.md`](worked-examples-three.md) | The three worked content examples at object level (exercise the v0.4 deltas). |

## 🗄 Historical (superseded — in [`archive/`](archive/), kept for provenance)

| doc | status |
|---|---|
| `archive/lehrplan-bundle-schema.md` | Schema **v0.1** — superseded by v0.3. |
| `archive/lehrplan-bundle-schema-v0.2.md` | Schema **v0.2** — superseded by v0.3. |
| `archive/project-handoff (1).md` | A stray Session-2 snapshot of the root handoff (says so itself); the root `project-handoff.md` is the live one. |
| [`implementation-notes.md`](implementation-notes.md) | The first-implementation snapshot (design↔code map). **Largely superseded by CLAUDE.md**; kept in place because the handoff references it. |
| [`dashboard-review.md`](dashboard-review.md) | Dashboard structuring notes — predates the four-station rework; historical. |

## Root-level companions (outside `Documents/`)

`../README.md` (project README) · `../CLAUDE.md` (**the** operating manual) · `../AGENTS.md` (thin
deferral to CLAUDE.md — one manual, no parallel copy) · `../project-handoff.md` (intent + history).
