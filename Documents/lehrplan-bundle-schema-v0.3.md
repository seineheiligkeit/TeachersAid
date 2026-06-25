# Lehrplan-Bundle Schema — v0.3

The data model, restructured around the **block model** and the cross-subject findings. v0.2 gave us
the thread/coverage/verification layer; **v0.3 makes the content itself a typed, renderer-independent
object** whose pedagogical depth and curricular coverage are *computable*, and whose competence axis
is *subject-parameterized* rather than hard-coded to the science W/E/S model.

Bound to Fassung **BGBl. II Nr. 204/2024**, DokNr `NOR40264237`, valid **2024-09-01 … 2026-08-31**.

## Changelog v0.2 → v0.3 *(each change traces to a finding)*

- **Block model (`InfoBlock` / `TaskBlock`) replaces `Baustein.student_face.body` + `tasks[]`.** The
  v0.2 faces were a prose blob plus a string list — too coarse to render a real worksheet *or* to
  audit. Blocks are the atom now. *(the depth + rendering work)*
- **`dimension: W|E|S` removed → `SubjectCompetenceModel`.** The cross-subject test showed W/E/S is the
  *Naturwissenschaften* model and means nothing in Deutsch (four Kompetenzbereiche), Mathematik (four
  processes × content areas), or GWB (Orientierungs-/Urteils-/Handlungskompetenz). The *slot* is
  universal; its *values* are supplied per subject. *(Deutsch/Math/GWB stress test)*
- **`TaskKind`: closed enum → core + per-subject extensions.** The nine core kinds carried most blocks;
  each subject needed a few additions (`text_production`, `calculation`, `map_work`, …). *(stress test)*
- **`CognitiveLevel` promoted to the formal depth contract**, with a documented mapping to the
  Lehrplan's own *Anforderungsbereiche*. *(the shallow-worksheet episode + GWB corroboration)*
- **`Modality` (printable / oral / enactive) on every block**, plus a stated scope boundary: oral and
  enactive competences don't fully render onto a printable sheet. *(stress test)*
- **`Nachweis` is now DERIVED from blocks; `DepthProfile` derived; `DepthTarget` added to planning.**
  "Shallow" and "coverage gap" stop being judgement calls and become data — e.g. STR.01's
  *Quellen bewerten* showing up as uncovered. *(shallow episode + the STR.01-S finding)*
- **`WorksheetContent` = renderer-independent object; renderers are pure projections.** Student sheet,
  teacher guide (and later docx) are all *views* of the same object, so they cannot drift — the
  mismatched-answer-key bug becomes structurally impossible. *(the mismatched-teacher-guide episode)*
- **`RichText` is an inline-run model, not HTML**, and **`ResponseSpec` is an affordance, not layout**
  (the content object has no concept of a "page"). *(renderer-independence; the "don't limit to 3
  pages" point)*

---

## 1 · The architectural shift

Content and presentation are now separated. A **`WorksheetContent`** object is produced and verified
*before any document exists*; each document is a **pure projection** over it.

```ts
renderStudentSheet(content: WorksheetContent): PrintableDoc   // hides answer keys, teacher notes, oral/enactive stubs
renderTeacherGuide(content: WorksheetContent): PrintableDoc   // adds Nachweis, watch-outs, keys, acceptable reasoning, rack
// renderEditableDocx(content) — a future projection; "editable output" is just another render() target
```

Because both documents are functions of one object, the **answer key cannot fall out of sync with the
task** — the failure we hit in the Strahlung build is now unrepresentable. "Length" / "3 pages" is
likewise not a property of the content; it is decided by the renderer at projection time.

## 2 · Subject competence model *(replaces fixed W/E/S)*

```ts
interface CompetenceDimension { id: string; label: string; note?: string }

interface SubjectCompetenceModel {
  subject: string;                       // pins which dimensions & kinds apply
  stufe: Stufe;
  dimensions: CompetenceDimension[];     // the process / competence axis  (was the W/E/S enum)
  content_areas?: CompetenceDimension[]; // only where the Lehrplan has an explicit content axis
  task_kind_extensions: string[];        // subject-specific TaskKinds beyond the core
}

type DimensionRef = string;              // id into the worksheet's SubjectCompetenceModel.dimensions
```

Four **grounded instances** (verbatim from the Fassung):

```yaml
Physik (Naturwissenschaften):
  dimensions: [ {id: W, label: "Fachwissen anwenden"},
                {id: E, label: "Erkenntnisgewinnung / Experimentieren"},
                {id: S, label: "Standpunkte begründen / aus naturwiss. Sicht bewerten"} ]
  task_kind_extensions: [ experiment_protocol, source_critique ]

Deutsch:
  dimensions: [ {id: sprachbewusstsein, label: "Sprachbewusstsein und Sprachreflexion", note: "integrativ"},
                {id: zuhoeren_sprechen, label: "Zuhören und Sprechen"},
                {id: lesen,  label: "Lesen"},
                {id: schreiben, label: "Schreiben"} ]
  task_kind_extensions: [ text_production, speaking_task, text_analysis ]   # speaking_task is oral (see Modality)

Mathematik:
  dimensions: [ {id: modellieren, label: "Modellieren und Problemlösen"},
                {id: operieren,   label: "Operieren (Rechnen und Konstruieren)"},
                {id: darstellen,  label: "Darstellen und Interpretieren"},
                {id: begruenden,  label: "Vermuten und Begründen"} ]
  content_areas: [ "Zahlen und Maße", "Variablen und Funktionen",
                   "Figuren und Körper", "Daten und Zufall" ]               # Math is the one with a true 2nd axis
  task_kind_extensions: [ calculation, construction, modelling_task ]

Geographie und wirtschaftliche Bildung:
  dimensions: [ {id: orientierung, label: "Orientierungskompetenz"},
                {id: urteil,       label: "Urteilskompetenz"},
                {id: handlung,     label: "Handlungskompetenz", note: "often enactive — see Modality"} ]
  task_kind_extensions: [ map_work, case_study, position_argument ]
```

## 3 · Cognitive level — the depth contract

```ts
type CognitiveLevel = "remember" | "understand" | "apply" | "analyze" | "evaluate" | "create";
```

This is the **formal depth dimension** and it is not ours by invention: GWB's own *Anforderungsbereiche*
corroborate it.

| Anforderungsbereich (Lehrplan) | ≈ CognitiveLevel |
|---|---|
| Reproduktion | remember / understand |
| Transfer | apply |
| Reflexion | analyze / evaluate |
| Problemlösung | evaluate / create |

Every `TaskBlock` carries one, so a worksheet's **cognitive profile is computable** (§5) — "this is
shallow" becomes a measurement, not a feeling.

## 4 · The block model

```ts
type Modality = "printable" | "oral" | "enactive";   // scope boundary: oral/enactive don't fully render to paper

// inline-run model — NOT html; any renderer (PDF/docx/html) styles the marks itself
type Mark = "bold" | "italic" | "term" | "code";
type InlineRun = { text: string; mark?: Mark };
type RichText = string | InlineRun[];                // string = plain; array = marked

// affordance, not layout — the renderer turns this into space/inputs
type ResponseSpec =
  | { mode: "lines"; n: number }
  | { mode: "box"; min_height_mm: number }
  | { mode: "table"; columns: string[]; rows: number }
  | { mode: "choices"; options: string[]; select: "one" | "many" }
  | { mode: "none" };

interface BlockBase {
  id: string;
  optional?: boolean;
  modality?: Modality;          // default "printable"
  flags?: ContentFlags;         // contested | freshness_decay | equipment_dependent | local  (from v0.2)
  asset_refs?: string[];        // figures / datasets this block shows or uses
}

// A — information to LEARN FROM
type InfoKind = "prose" | "key_fact" | "example" | "procedure" | "figure" | "data_reference" | "callout";
interface InfoBlock extends BlockBase {
  role: "info";
  kind: InfoKind;
  content: RichText;
  callout_role?: "note" | "warning" | "reveal" | "tip";
  teacher_note?: RichText;      // teacher-projection only
  watch_outs?: string[];        // e.g. a figure "misleading in isolation"
}

// B — an EXERCISE
type CoreTaskKind =
  | "open_response" | "matching" | "ordering" | "multiple_choice" | "true_false_justify"
  | "table_fill" | "data_interpretation" | "decision_scenario" | "create_produce";
type TaskKind = CoreTaskKind | string;          // string = a subject's task_kind_extension

type TaskPayload =                               // kind-specific data the renderer needs
  | { kind: "matching"; left: string[]; right?: string[] }
  | { kind: "ordering"; items: string[] }
  | { kind: "multiple_choice"; options: string[]; select: "one" | "many" }
  | { kind: "true_false_justify"; statements: string[] }
  | { kind: "table_fill"; columns: string[]; rows: (string | null)[][] }   // null = blank for the student
  | { kind: "data_interpretation"; asset_ref: string }
  | { kind: "decision_scenario"; stem: RichText }
  | { kind: "other"; data?: Record<string, unknown> };                     // open/extension kinds: prompt carries it

interface TaskBlock extends BlockBase {
  role: "task";
  kind: TaskKind;
  prompt: RichText;
  payload?: TaskPayload;
  response: ResponseSpec;
  cognitive_level: CognitiveLevel;               // the depth contract (§3)
  dimensions: DimensionRef[];                    // subject-scoped (§2); primary first; usually 1, sometimes 2
  content_area?: string;                         // subject content axis where it exists (Math)
  serves: { competence_id: string; relation: CoverageRelation }[];   // exercises | builds_prerequisite
  est_minutes: number;
  answer_key?: RichText;                          // knowledge side
  acceptable_reasoning?: RichText;                // judgement side — the RANGE, not one key
  watch_outs?: string[];
}

type Block = InfoBlock | TaskBlock;
```

## 5 · Composition, derived coverage, derived depth

```ts
interface Baustein {                              // a section; ≈ a thread instantiated, or part of the spine
  id: string; title: string;
  teacher_overview: { throughline: RichText; timing_notes?: string; differentiation?: string };
  blocks: Block[];                                // info + task, interleaved
}

interface DepthProfile {                          // DERIVED over all TaskBlocks
  by_level: Partial<Record<CognitiveLevel, number>>;
  by_dimension: Record<DimensionRef, number>;
  minutes_total: number;
  minutes_resource_independent: number;           // total minus blocks flagged equipment_dependent — answers "what survives with no materials?"
}

interface DepthTarget {                           // an INPUT to planning (set the bar up front)
  min_at_or_above?: { level: CognitiveLevel; count: number };   // e.g. ≥2 analyze-or-higher per Einheit
  require_resource_independent_minutes?: number;
  dimensions_required?: DimensionRef[];
}

interface WorksheetContent {                      // the renderer-independent object — exists BEFORE any PDF
  meta: { title: string; subtitle?: string; subject: string; stufe: Stufe; klasse: number;
          kernfrage?: RichText; fassung: FassungRef; lehrplan_label: string };
  subject_model: SubjectCompetenceModel;          // pins dimensions & kinds for this content
  intro: Block[];
  sections: Baustein[];
  assets: Asset[];
  nachweis: Nachweis;                             // DERIVED — deriveNachweis(content)
  depth_profile: DepthProfile;                    // DERIVED
  rack?: ThreadRack;
}

interface Bundle { request: BundleRequest; resolution: LehrplanResolution;
                   content: WorksheetContent; generated_at: string }

// Nachweis aggregates every TaskBlock.serves across all blocks. A competence with zero exercising
// blocks surfaces automatically as a gap — this is how STR.01-S "Quellen bewerten" showed up missing.
function deriveNachweis(c: WorksheetContent): Nachweis
function computeDepth(c: WorksheetContent): DepthProfile
```

## 6 · Carried forward from v0.2 *(unchanged — signatures only)*

```ts
type Stufe = "Unterstufe" | "Oberstufe";
interface FassungRef { kurztitel; bgbl; doknr; valid_from; valid_to }
interface BundleRequest { subject; klasse; stufe; schulform?; topic_raw; envelope; options? }
type TimeEnvelope = …;                                   // einzelstunde | doppelstunde | block | custom
interface LehrplanResolution { fassung; matched_kompetenzbereiche; grade_check; competences; … }  // deterministic; grade_check is the trust feature
interface ResolvedCompetence { id; kompetenzbereich; klasse; text /*verbatim*/; source_ref; uebergreifende_themen }
type Lens = …;                                           // the reusable lens kit (creative surface)
type CoverageRelation = "exercises" | "builds_prerequisite";
interface ContentFlags { contested?; freshness_decay?; equipment_dependent?; local? }
interface VerificationItem { claim; confidence; status; source? }
interface Thread { id; kompetenzbereich; title; hook; anchors; lens; depth_band; dimensions; flags; watch_out?; verification; cross_links }
interface ThreadRack { kompetenzbereich; fassung; threads; coverage }
interface CoverageReport { per_competence; thin_spots }
interface Asset { id; role; generator; spec; correctness_surface; misleading_in_isolation }   // content-bearing → code
interface SubjectVisualPolicy { subject; diffusion_ok; diffusion_forbidden; must_be_code }
interface Nachweis { fassung; statement; competence_coverage; zentrale_konzepte; uebergreifende_themen }
```

Note: `ResolvedCompetence.dimensions` and `Thread.dimensions` now hold `DimensionRef[]` (subject-scoped),
not the old W/E/S literals.

## 7 · Pipeline

**Resolve** *(deterministic)* → **Plan** (envelope → competences + `DimensionRef`s + `DepthTarget` +
thread selection) → **Generate blocks** (content-bearing assets → code; decorative → policy) →
**Verify** (resolve every `VerificationItem`) → **Assemble** `WorksheetContent` (+ derived `Nachweis`
+ `DepthProfile`) → **Render** projections (student / teacher / docx) — pure views, guaranteed consistent.

Tight downstream, generous upstream: the student blocks are conservative; the teacher rack is
overproduced; the friction the teacher avoids is absorbed here, not pushed onto them.

## 8 · Populated examples

**A `TaskBlock` (Strahlung 2b — the penetration ≠ danger task):**
```yaml
id: str.s2.b2
role: task
kind: open_response
prompt: [{text: "WLAN-Signale gehen durch Wände, schaden dir aber nicht – Gammastrahlung dagegen ist gefährlich. Beide durchdringen Materie. Erkläre den Unterschied."}]
response: { mode: lines, n: 3 }
cognitive_level: analyze
dimensions: [ S, W ]                 # Physik model; primary = S (bewerten), also W
serves: [ { competence_id: PHY.US.4.STR.02, relation: exercises } ]
est_minutes: 6
acceptable_reasoning: "Funkwellen = niedrige Energie, durchdringen, verändern aber keine Atome (nicht-ionisierend); Gamma = extrem hohe Energie, ionisierend → Zellschaden. Kernpunkt: Durchdringung ≠ Gefahr."
watch_outs: ["Lob die Trennung 'durchdringen' vs 'schaden' — genau hier liegt die Einsicht."]
```

**A `TaskBlock` (Strahlung 3 — statements check), showing payload + the load-bearing watch-out:**
```yaml
id: str.s3
role: task
kind: true_false_justify
prompt: [{text: "Entscheide richtig/falsch und begründe oder korrigiere."}]
payload:
  kind: true_false_justify
  statements:
    - "UV-Strahlung ist ungefährlich, weil sie nicht ionisierend ist."
    - "Je höher die Energie, desto eher kann Strahlung Atome verändern (ionisieren)."
    - "Wenn ich mit dem Handy telefoniere, werde ich radioaktiv."
response: { mode: table, columns: ["Aussage","richtig / falsch","Begründung / Korrektur"], rows: 3 }
cognitive_level: evaluate
dimensions: [ S ]
serves: [ { competence_id: PHY.US.4.STR.02, relation: exercises } ]
est_minutes: 9
answer_key: "1 falsch (UV schädigt Zellen trotz nicht-ionisierend) · 2 richtig · 3 falsch (Funkwellen, kein Kernzerfall)"
watch_outs: ["Statement 1 ist die zentrale Falle — 'nicht-ionisierend' ≠ 'harmlos'."]
```

**A Deutsch `TaskBlock` — proves subject-parameterized `dimensions` + an extended `kind`:**
```yaml
id: de.arg.write
role: task
kind: text_production                 # subject extension (declared in Deutsch model)
prompt: [{text: "Schreibe in 4–5 Sätzen deine Meinung zur Handy-Regel: beginne mit deiner Behauptung, gib zwei Gründe und ein Beispiel."}]
response: { mode: box, min_height_mm: 60 }
cognitive_level: create
dimensions: [ schreiben ]             # Deutsch model — not W/E/S
serves: [ { competence_id: DE.US.1.SCHREIBEN.x, relation: exercises } ]
est_minutes: 12
```

**A `DepthProfile` (the deep Strahlung sheet) — what made "shallow → not shallow" measurable:**
```yaml
by_level:   { understand: 1, apply: 1, analyze: 2, evaluate: 2, create: 1 }   # climbs; not flat at remember/understand
by_dimension: { W: 2, S: 4, E: 1 }
minutes_total: 78
minutes_resource_independent: 56        # the experiment (E, equipment_dependent) is the only gated part
# deriveNachweis() flags PHY.US.4.STR.01 (Quellen bewerten, S) as UNCOVERED → belongs to a sibling Baustein/thread
```

## 9 · Deferred / next

- **Reusable shapes / templates (v0.4):** the renderer-independent block stream is what a *template*
  (a sequence of block-*specs* with a `DepthTarget`, no words) instantiates against a new topic. Build
  this layer on top of v0.3, not into it.
- **Editable output** is not a new format problem — it is one more `render()` target over the same object.
- **Difficulty calibration** remains the open hard problem, but it is now pinned to a small, well-defined
  surface: the *fill + verify* of each block, not the structure.
- Still deferred: the engine, teacher UI, pricing, multilingual output, Oberstufe loose resolution, the
  post-2026/27 Fassung.
