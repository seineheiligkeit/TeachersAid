# Schema Roadmap — v0.4 (worksheet deltas) & v0.5 (Lernarrangement)

Both layers are **additive**. v0.3 (the block model, subject-parameterized dimensions, the
`CognitiveLevel` depth contract, derived `Nachweis`/`DepthProfile`, renderer-independent projection)
does **not change**. v0.4 adds fields to the worksheet; v0.5 adds a *sibling* object that composes
worksheets. Everything below traces to the subject audit or the creativity brainstorm.

---

## v0.4 — Additive worksheet deltas

### Group A — forced by the subject-coverage audit

```ts
// A1 · shareable competence models (one Naturwissenschaften model → Physik/Chemie/Biologie)
interface SubjectCompetenceModelRef { ref: string; label_overrides?: Record<string, string> }

// A2 · modality at the DIMENSION level → printable coverage becomes computable
interface CompetenceDimension { id: string; label: string; note?: string;
  modality: "printable" | "oral" | "enactive" }          // NEW
// derived: printableCoverage(model) = #printable dimensions / #dimensions   (Physik 1.0 … Sport 0.0)

// A3 · asset medium beyond visual (Fremdsprache Hören, Musik Hören u. Erfassen)
type Medium = "visual" | "audio" | "interactive";
interface MediaPolicy { subject: string;                  // generalises SubjectVisualPolicy
  per_medium: { medium: Medium; diffusion_ok?: string[]; must_be_code?: string[];
                must_be_sourced?: string[]; machine_generatable: boolean }[] }
// note: TTS for a language prompt IS generatable; music audio is NOT → machine_generatable=false

// A4 · rubric + produced-artifact response (Kunst, Technik, Musik, long Deutsch/Ethik)
interface RubricCriterion { criterion: string; levels: string[] }   // e.g. ["nicht erreicht","teilweise","erreicht"]
type ResponseSpec_v04 = /* …v0.3… */ | { mode: "artifact"; produces: string };
interface TaskBlock_A4 { /* …v0.3… */ rubric?: RubricCriterion[] }

// A5 · content language (worksheet ≠ German for Fremdsprache, Latein)
interface WorksheetMeta_A5 { /* …v0.3… */ content_language: string }   // default "de"

// A6 · task_kind_extensions catalogue (data, not new types — confirms v0.3's open set):
//   translation, listening_task, speaking_task, construction, cad_model, programming,
//   source_analysis, make_artifact, performance_task, movement_task, position_argument,
//   text_production, text_analysis
```

### Group B — surfaced by the creativity brainstorm

```ts
// B1 · richer response modes (the Mystery's causal web; "vom Schatten zum Körper"; honest re-draw)
type ResponseSpec_v04b = /* … */
  | { mode: "diagram"; kind: "causal_web" | "concept_map" | "flow"; seed_nodes?: string[] }
  | { mode: "drawing"; guide?: string };                  // sketch / construction / redraw

// B2 · intra-sheet references (prediction→reveal; "compare to your answer in §2"; five-Textsorten)
interface InlineRef { ref_block: string }                  // a RichText run that points at another block

// B3 · intentionally-flawed asset — wrong ON PURPOSE; the pipeline must NOT "fix" it.
//      Distinct from v0.2 `misleading_in_isolation` (which is correct-but-risky-out-of-context).
interface Asset_B3 { /* …v0.3… */ intentionally_flawed?: { what: string } }

// B4 · asset provenance / usage-rights (real speeches, adverts, inscriptions, songs)
interface AssetProvenance { source: string;
  rights: "public_domain" | "licensed" | "cleared" | "original" | "unverified"; note?: string }
interface Asset_B4 { /* … */ medium: Medium; machine_generatable: boolean; provenance?: AssetProvenance }

// B5 · cross-curricular dimensions (geschönte Kurve = Physik+Math; climate Mystery = GWB+Bio+Math)
interface WorksheetMeta_B5 { /* … */ subject_models: SubjectCompetenceModelRef[] }   // was single; primary first
interface TaskBlock_B5 { /* … */ dimensions: DimensionRef[] }   // DimensionRefs may resolve into >1 model
```

**All eleven deltas are additive.** A v0.3 worksheet is a valid v0.4 worksheet (single subject, all
`printable`, visual assets, no rubric, German). Nothing is removed.

---

## v0.5 — Lernarrangement *(a composite sibling, not a worksheet field)*

A `Lernarrangement` is a new object at the **orchestration layer** that *contains* worksheets. The
relation is **has-a**, so the worksheet stays the modeled primitive and a plain worksheet is simply the
**n = 1** case of an arrangement (one role, one phase, no interaction). We don't tax the 90% case with
roles/phases, and we don't pollute the worksheet abstraction with multi-learner fields.

```ts
type ArrangementFormat = "role_debate" | "mystery" | "jigsaw" | "simulation_game" | "stations" | string;

interface Lernarrangement {
  meta: { title: string; subject: string; klasse: number; fassung: FassungRef; format: ArrangementFormat };
  common_material?: Block[];               // shared briefing every role receives (no duplication)
  roles: { id: string; label: string; share: "all" | number | "fraction";
           private?: boolean;              // asymmetric info (jigsaw / mystery)
           material: WorksheetContent }[]; // each role's sheet IS a worksheet (reuses everything)
  phases: { id: string; label: string;
            grouping: "individual" | "role_group" | "home_group" | "plenary";
            minutes: number; what_happens: RichText }[];
  shared_product?: { description: RichText; rubric?: RubricCriterion[] };
  debrief: Block[];                        // where the social/oral competence usually lands
  competence_anchors: { competence_id: string; dimension: DimensionRef;
                        served_by: "interaction" | "debrief" | "shared_product" | `role:${string}` }[];
  nachweis: Nachweis;                      // DERIVED: ⋃ role Nachweise  +  arrangement-level anchors
  depth_profile: DepthProfile;             // DERIVED aggregate
}
```

**Rendering reuses v0.3/v0.4 entirely** — no second rendering path:
```ts
renderArrangement(a) = renderTeacherOrchestration(a) + a.roles.map(r => renderStudentSheet(r.material))
```
So the mismatched-drift guarantee carries straight over to every role's material.

**Why this is more than stapled worksheets:** the arrangement-level `competence_anchors` are exactly the
**oral / social / enactive** competences the subject audit said a worksheet can't reach — a mock trial's
*politische Handlungskompetenz*, a debate's *Zuhören und Sprechen*, GWB's *Handlungskompetenz*. They're
served by the phases, the interaction, and the debrief, not by any single printable sheet. The
arrangement layer is therefore precisely what **extends competence coverage into the band the worksheet
structurally couldn't** — while the worksheet stays the printable atom inside it.

**Scope discipline (hard line):** we generate the **material bundle + a teacher run-guide** for the
activity. We do **not** run it — no live grouping, no timing the room, no student tracking. The teacher
owns and runs the activity; our product hands them the artifacts to run it well. The moment
"orchestration" drifts toward live classroom management, we've rebuilt the everything-platform that
failed. Generating the artifacts is in scope; orchestrating the room is not.

**Honest cost:** an arrangement is a genuinely harder artifact than a worksheet (orchestration,
asymmetric materials, contingencies, a good debrief = real teaching judgement). It's earned only after
the worksheet core and the template layer are proven — hence **deferred**, recorded here as the frontier.

---

## Sequencing
v0.4 (additive worksheet deltas) → the template/shape layer on top of v0.3/v0.4 → **then** v0.5
(arrangement). Still deferred throughout: the engine, difficulty calibration, Oberstufe resolution.

---

## Post-breadth implementation roadmap (agreed 2026-06-26)

The engine, block library (425 SME-approved blocks, 16 subjects, ~33% coverage), and composer are proven,
so the two frontiers are **Phase 4 — assets** and **Phase 5 — Lernarrangements** (the v0.5 object above,
now *unblocked*: its precondition "earned after the worksheet core + template layer are proven" is met).

**Product principle (load-bearing, decided with the SME):** the platform is primarily a **consolidator of
human-vetted library content**, not a live generator. Generation (LLM *and* diffusion) happens in the
**library-building stage with a human in the loop**; the *platform* composes from the approved library.
⇒ Discipline about generation is a **library-entry gate, not a generation ban**. The durable invariant:
**content-bearing visuals must be correct** (code-generated, or vetted-sourced) — code-gen beats review,
because subtle wrongness survives a skim — **while decorative visuals must be content-free** (then any
source, incl. diffusion, vetted once and reused).

### Phase 4 — Asset architecture
Three asset classes, distinguished by *what is durable*:

| class | examples | production | durable artifact | entry gate |
|---|---|---|---|---|
| content / code-gen | number line, graph, geometry, data table, timeline, Punnett, **math formula** | parameterized recipe (reads `Asset.spec`) | the `{generator, spec}` on the block (rebuilt) | auto — it builds ⇒ structurally right |
| content / sourced | photos, sources, artworks, song/text | external + provenance | the vetted file + rights | human-vet |
| decorative / content-free | mascots, motifs, icons, spot illustrations | SVG/code · diffusion · curated | the vetted file, tagged + reusable | human-vet once, reuse |

- **Code-generator library (priority muscle):** parameterized, correct-by-construction recipes. Dispatch is
  **pluggable by backend** — generator id is `<backend>:<recipe>` (`matplotlib:`/`svg:` now; **`diffusion:`**
  later, fulfilled by the SME's image-gen agent). `Asset(generator, spec)` is the clear declarative request
  a diffusion pipeline plugs into without touching the model.
- **Math = a content asset** (`matplotlib:math_formula` via mathtext); store math semantically (LaTeX) so a
  future HTML renderer could typeset via KaTeX. Audit need first — most Unterstufe math is inline-simple.
- **Asset-as-reviewed-library** for the decorative + sourced classes (the *file* is durable): an asset store
  with status + tags + reuse, parallel to the block library. Code-gen assets stay as specs on blocks.
- **`MediaPolicy` operationalized** as the per-subject entry-gate config (`must_be_code` / `must_be_sourced`
  / `diffusion_ok`); it also steers generation. **DONE (Phase 4 #3):** `pipeline/media_policy.py` —
  `DEFAULT_MEDIA_POLICY` partitions roles per medium; `classify_source` → code/sourced/diffusion/none;
  `check_content` runs inside `verify`, so a mis-sourced content asset (or a decorative asset claiming
  content) blocks library entry like any verify problem. All 76 stored items + 33 block specs pass clean.
- Re-enable **asset-bearing task generation** (breadth was text-only by *constraint*; now un-handbraked).
- **Decorative kit:** content-free, reusable; SVG/code first, diffusion (SME agent) when wired — both vetted.

### Phase 5 — Lernarrangement (v0.5 above, now unblocked)
Build order: schema → **one hand-authored hero exemplar in Geographie (GWB)** to set the quality bar →
`renderTeacherOrchestration` (the run-guide; role materials reuse `renderStudentSheet`) → generation. GWB
chosen because it has rich content KBs *and* the *Handlungskompetenz* dimension a worksheet can't reach —
showcasing the oral/social/enactive coverage arrangements unlock (extends the Nachweis past
`printableCoverage`). Hard scope line stands: we generate the material bundle + run-guide; we do **not** run
the room.

Carry-over from Phase 3: 3b (angle-aware composition), 3d (difficulty), 3e (coherence framing) fold in where
natural, reprioritized behind Phase 4/5.
