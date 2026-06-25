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
