# Lehrplan-Bundle Schema — v0.2

The data model for the project, updated to reflect what the deep dive surfaced. v0.1 defined the
bundle anatomy; **v0.2 adds the thread layer (the actual product value), an honest coverage
relation, mandatory pedagogical watch-outs, content flags, and an explicit verification stage.**

Bound to Fassung **BGBl. II Nr. 204/2024**, DokNr `NOR40264237`, valid **2024-09-01 … 2026-08-31**.

## Changelog v0.1 → v0.2 *(every change traces to a finding)*

- **`Thread` + `ThreadRack`** — the teacher-side rack is the product's value layer; a Kompetenzbereich
  is the unit of the reusable content asset. *(rack deep-dive)*
- **`Lens` enum** — the ~11 reusable lenses are the second axis of creative surface, shared across
  every subject. *(creative-surface analysis)*
- **`CoverageRelation = exercises | builds_prerequisite`** — an explainer *builds* a competence's
  prerequisite but does not *exercise* it; claiming otherwise is the generic-worksheet trap.
  Applied to both Bausteine and Threads. *(B1 fidelity gap)*
- **`watch_outs: string[]` is now required on `TeacherFace`; `Thread.watch_out`** — correct content
  can still plant a misconception invisibly; the watch-out is load-bearing infrastructure. *(B1: the UV/ionising trap)*
- **`ContentFlags { contested, freshness_decay, equipment_dependent, local }`** — the most valuable
  threads cluster exactly in contested/decay-prone/local territory. *(rack liabilities)*
- **`Asset.misleading_in_isolation`** — a content-bearing figure can be correct yet dangerous when
  extracted from its text. *(spectrum figure)*
- **`VerificationItem` + a verification pipeline stage** — contested/fresh facts need
  generate → source-verify → flag-for-refresh. *(Zwentendorf worklist)*
- **`CoverageReport`** — coverage is uneven *within* a Kompetenzbereich; the report exposes thin,
  abstract competences. *(rack coverage finding)*
- **Bundle composition** — a bundle = conservative student spine + teacher-rack threads selected and
  sized by the time envelope; `Baustein.source_thread` links the two. *(time-envelope = thread selection)*

---

## Core types *(carried from v0.1)*

```ts
type Dimension = "W" | "E" | "S";   // Fachwissen | Erkenntnisgewinnung/Experiment | Standpunkte/Bewerten
type Stufe     = "Unterstufe" | "Oberstufe";
type Schulform = "Gymnasium" | "Realgymnasium" | "Wirtschaftskundliches Realgymnasium";

interface FassungRef {
  kurztitel: string; bgbl: string; doknr: string;
  valid_from: string; valid_to: string;   // bundle/rack is stamped with this
}

interface BundleRequest {           // the ONLY thing the teacher touches
  subject: string;
  klasse: 1|2|3|4|5|6|7|8;
  stufe: Stufe;
  schulform?: Schulform;
  topic_raw: string;                // free text, e.g. "EM-Wellen"
  envelope: TimeEnvelope;
  options?: {
    ability_spread?: "homogen" | "heterogen";
    equipment?: string[];           // gates equipment_dependent threads
    prior_topics?: string[];
    language_support?: boolean;
  };
}

type TimeEnvelope =
  | { kind: "einzelstunde" } | { kind: "doppelstunde" }
  | { kind: "block"; units: number } | { kind: "custom"; minutes: number };

// Layer 0 — deterministic resolution (binding facts come from a parser, never a model)
interface LehrplanResolution {
  fassung: FassungRef;
  matched_kompetenzbereiche: { name: string; klasse: number }[];
  grade_check: {                    // the trust feature
    requested_klasse: number; lehrplan_klasse: number;
    status: "match" | "mismatch"; note?: string;
  };
  competences: ResolvedCompetence[];
  zentrale_konzepte: { name: string; basis: "verbatim" | "editorial" }[];
  uebergreifende_themen: { id: number; name: string }[]; // verbatim-tagged only
}

interface ResolvedCompetence {
  id: string;                       // "PHY.US.4.STR.02"
  kompetenzbereich: string; klasse: number;
  text: string;                     // VERBATIM
  dimensions: Dimension[];          // parsed from inline (W)/(E)/(S)
  uebergreifende_themen: number[];  // parsed from superscripts
  source_ref: string;
}
```

## New shared types *(v0.2)*

```ts
// the reusable "lens kit" — turns any anchor into a thread; same set for every subject
type Lens =
  | "history" | "everyday_hidden" | "cosmic" | "risk_numbers"
  | "cross_domain_bridge" | "current_tech" | "current_research"
  | "society_ethics_policy" | "media_literacy" | "hands_on" | "aesthetic";

// honest competence relation — replaces a flat "serves"
type CoverageRelation = "exercises" | "builds_prerequisite";

interface ContentFlags {
  contested?: boolean;          // ⚠ needs evenhanded treatment
  freshness_decay?: boolean;    // ⏳ facts go stale; needs refresh cadence
  equipment_dependent?: boolean;// 🔬 physical vs virtual variant
  local?: boolean;              // 📍 Austria-specific (also a moat signal)
}

interface VerificationItem {
  claim: string;
  confidence: "high" | "medium" | "low";
  status: "unverified" | "verified" | "flagged";
  source?: string;              // authoritative reference, once checked
}
```

## The thread layer *(v0.2 — the product's value)*

```ts
interface Thread {
  id: string;                   // "PHY.US.4.STR.thread.zwentendorf"
  kompetenzbereich: string;
  title: string;
  hook: string;                 // concrete, specific — the actual idea, not a category
  anchors: { competence_id: string; relation: CoverageRelation }[]; // honest, no strain
  lens: Lens;
  depth_band: { min_minutes: number; max_minutes: number };
  dimensions: Dimension[];
  uebergreifende_themen: number[];
  flags: ContentFlags;
  watch_out?: string;           // the correct-but-misleading / safety / evenhandedness trap
  verification: VerificationItem[];
  cross_links: string[];        // other thread ids
}

interface ThreadRack {          // one per Kompetenzbereich; amortises across teachers & years
  kompetenzbereich: string;
  fassung: FassungRef;
  threads: Thread[];
  coverage: CoverageReport;
}

interface CoverageReport {      // derived; exposes uneven coverage WITHIN a Kompetenzbereich
  per_competence: {
    competence_id: string;
    exercised_by: number;       // # threads that exercise it
    prerequisite_by: number;
    dimensions_covered: Dimension[];
  }[];
  thin_spots: string[];         // competence ids under-served by creative threads
}
```

## The bundle layer *(v0.2 — updated)*

```ts
type ArtifactType =
  | "explainer" | "problem_set" | "experiment_protocol"
  | "model_activity" | "source_critique" | "decision_scenario" | "consolidation";
type VerificationStatus = "computed" | "vetted_pattern" | "open_judgement";

interface Baustein {
  id: string; order: number; optional: boolean;
  title: string; minutes: number;
  serves: { competence_id: string; relation: CoverageRelation }[];  // ← relation, not flat
  source_thread?: string;       // ← if this segment was instantiated from a rack thread
  primary_dimension: Dimension;
  artifact_type: ArtifactType;
  verification: VerificationStatus;
  teacher_face: TeacherFace;
  student_face: StudentFace;
  assets: Asset[];
}

interface TeacherFace {
  throughline: string;
  misconceptions: string[];
  watch_outs: string[];         // ← REQUIRED (may be empty, but always present)
  answer_key?: string;          // W
  expected_result?: string;     // E
  acceptable_reasoning?: string;// S — the RANGE, not one key
  timing_notes?: string;
  differentiation?: string;
}

interface StudentFace { body: string; tasks: string[]; }

type AssetRole = "decorative" | "content_bearing";
type Generator = "diffusion" | "code_svg" | "code_matplotlib" | "code_tikz" | "none";

interface Asset {
  id: string; role: AssetRole; generator: Generator;  // generator gated by SubjectVisualPolicy
  spec: string; text_overlay?: string;
  correctness_surface: boolean;        // === (role === "content_bearing")
  misleading_in_isolation: boolean;    // ← correct, but risky if extracted from its text
}

interface SubjectVisualPolicy {        // the decorative/informative boundary is per-subject
  subject: string;
  diffusion_ok: string[];
  diffusion_forbidden: string[];       // off-limits even if "decorative"
  must_be_code: string[];
}

interface Nachweis {
  fassung: FassungRef;
  statement: string;
  competence_coverage: { competence_id: string; relation: CoverageRelation; served_by: string[] }[];
  zentrale_konzepte: string[];
  uebergreifende_themen: { id: number; name: string; served_by: string[] }[];
}

interface Bundle {
  request: BundleRequest;
  resolution: LehrplanResolution;
  bausteine: Baustein[];        // conservative spine + threads-as-Bausteine (envelope-selected)
  nachweis: Nachweis;
  generated_at: string;
}
```

## Pipeline *(prose — the stages a request flows through)*

1. **Resolve** *(deterministic)* — topic_raw + klasse → competences, grade_check, themes, Fassung.
2. **Plan** — envelope → conservative student spine + N threads pulled from the Kompetenzbereich's
   `ThreadRack`, sized to fit; threads become optional Bausteine.
3. **Generate** — fill teacher/student faces and assets (content-bearing → code; decorative → policy).
4. **Verify** — resolve every `VerificationItem` (figures, contested claims, fresh facts) against
   authoritative sources; nothing contested/fresh ships `unverified`.
5. **Assemble** — Bundle + Nachweis, stamped to the Fassung; verification status visible throughout.

**Generation posture:** tight, conservative, minimal student spine (downstream, reaches children);
deliberately *over*-produced teacher rack (upstream, expert curates). Tight downstream, generous upstream.

---

## Populated examples of the new elements

**A thread record (Zwentendorf):**
```yaml
id: PHY.US.4.STR.thread.zwentendorf
kompetenzbereich: "Strahlung und Radioaktivität"
title: "Zwentendorf: das Kraftwerk, das nie ans Netz ging"
hook: "Österreich baute ein vollständiges KKW und schaltete es nach knapper Volksabstimmung 1978
       nie ein; weil nie befeuert, ist der Reaktor bis heute begehbar und nicht radioaktiv."
anchors:
  - { competence_id: PHY.US.4.STR.04, relation: exercises }          # S: umgehen/bewerten
  - { competence_id: "Kraftwerksarten",  relation: builds_prerequisite }
lens: society_ethics_policy
depth_band: { min_minutes: 20, max_minutes: 50 }
dimensions: [S]
uebergreifende_themen: [7, 11, 13]      # Politische Bildung / Umwelt / Wirtschaft
flags: { contested: true, local: true, freshness_decay: true }
watch_out: "Anti-Atom-Haltung ist in AT nahezu Konsens — beide Seiten gleich stark behandeln,
            Lehrkraft-Meinung außen vor; Rückschaufehler vermeiden (1978-Wähler kannten Tschernobyl
            nicht); Physik-Anker sichtbar halten."
verification:
  - { claim: "Volksabstimmung 5.11.1978, ~50,5% Nein", confidence: high,   status: flagged }
  - { claim: "Reaktortyp Siedewasserreaktor, ~700 MW",  confidence: medium, status: flagged }
  - { claim: "deutscher Schwesterreaktor (Isar 1?) lief Jahrzehnte", confidence: medium, status: flagged }
cross_links: [PHY.US.4.STR.thread.kernkraft, PHY.US.4.STR.thread.tschernobyl, PHY.US.4.STR.thread.atommuell]
```

**A coverage report fragment (Strahlung rack) — exposes the thin spot:**
```yaml
per_competence:
  - { competence_id: PHY.US.4.STR.01, exercised_by: 2, prerequisite_by: 1, dimensions_covered: [W, S] }
  - { competence_id: PHY.US.4.STR.02, exercised_by: 9, prerequisite_by: 1, dimensions_covered: [E, S] }   # over-served
  - { competence_id: PHY.US.4.STR.03, exercised_by: 2, prerequisite_by: 0, dimensions_covered: [W] }       # thin/abstract
  - { competence_id: PHY.US.4.STR.04, exercised_by: 6, prerequisite_by: 0, dimensions_covered: [S] }
thin_spots: [PHY.US.4.STR.03]   # decay-as-random-process: few creative hooks → invest deliberately
```

**Still deliberately omitted:** teacher UI/dashboard, pricing, multilingual student output, Oberstufe
loose resolution, the post-2026/27 Fassung. None are load-bearing until the core loop is proven.
