# Lehrplan-Bundle Schema — v0.1

A declarative contract for **one generated teaching bundle** of teacher-chosen length,
grounded in the Austrian AHS Lehrplan.

**Reference instance:** Physik · Unterstufe · **4. Klasse** · Topic "EM-Wellen / Strahlung"
· **Doppelstunde (~100 min)**.

**Design rule (non-negotiable):** every *binding* fact — which competence, which grade,
which übergreifende Themen, which Fassung — originates from a **deterministic parse** of the
RIS Lehrplan HTML, never from a generative model. Generation only ever *fills* structure that
the resolver has already pinned. The only fuzzy step is mapping a teacher's loose phrase to one
of ~7 named Kompetenzbereiche per subject-grade.

Bound to Fassung **BGBl. II Nr. 204/2024** (Stammfassung BGBl. Nr. 88/1985), DokNr
`NOR40264237`, valid **2024-09-01 … 2026-08-31**. (The `valid_to` rollover is why every bundle
is stamped with the Fassung it claims compliance against.)

---

## 1 · The contract (types)

```ts
// ── shared enums ───────────────────────────────────────────
type Dimension = "W" | "E" | "S";
//   W = Fachwissen anwenden
//   E = Erkenntnisgewinnung und Experimentieren
//   S = Standpunkte begründen und aus naturwiss. Sicht bewerten
type Stufe     = "Unterstufe" | "Oberstufe";
type Schulform = "Gymnasium" | "Realgymnasium" | "Wirtschaftskundliches Realgymnasium";

// ── teacher-facing request (the only thing the teacher touches) ──
interface BundleRequest {
  subject: string;            // "Physik"
  klasse: 1|2|3|4|5|6|7|8;    // as entered by the teacher
  stufe: Stufe;               // derived from klasse, but stored
  schulform?: Schulform;      // optional; affects hours & subject set
  topic_raw: string;          // free text, e.g. "EM-Wellen", "Strahlung"
  envelope: TimeEnvelope;
  options?: {
    ability_spread?: "homogen" | "heterogen";
    equipment?: string[];     // gates E-segments: physical vs. virtual experiment
    prior_topics?: string[];
    language_support?: boolean;  // sprachsensibler Unterricht emphasis
  };
}

type TimeEnvelope =
  | { kind: "einzelstunde" }           // ~50 min
  | { kind: "doppelstunde" }           // ~100 min
  | { kind: "block"; units: number }   // n × 50 min, sequenced across lessons
  | { kind: "custom"; minutes: number };

// ── Layer 0: deterministic Lehrplan resolution ─────────────
interface LehrplanResolution {
  fassung: FassungRef;
  matched_kompetenzbereiche: { name: string; klasse: number }[];
  grade_check: {
    requested_klasse: number;
    lehrplan_klasse: number;
    status: "match" | "mismatch";
    note?: string;            // surfaced to the teacher on mismatch
  };
  competences: ResolvedCompetence[];
  zentrale_konzepte: { name: string; basis: "verbatim" | "editorial" }[];
  uebergreifende_themen: { id: number; name: string }[]; // verbatim-tagged only
}

interface ResolvedCompetence {
  id: string;                 // "PHY.US.4.STR.02"
  kompetenzbereich: string;   // "Strahlung und Radioaktivität"
  klasse: number;
  text: string;               // VERBATIM "Die Schülerinnen und Schüler können …"
  dimensions: Dimension[];    // parsed from inline (W)/(E)/(S) markers
  uebergreifende_themen: number[]; // parsed from superscripts; [] if untagged
  source_ref: string;         // citation into FassungRef
}

interface FassungRef {
  kurztitel: string;
  bgbl: string;
  doknr: string;
  valid_from: string;         // ISO date
  valid_to: string;           // ISO date — bundle is stamped with this
}

// ── Layer 1+2: the modular kit ─────────────────────────────
type ArtifactType =
  | "explainer" | "problem_set" | "experiment_protocol"
  | "model_activity" | "source_critique" | "decision_scenario" | "consolidation";

// how the segment's ANSWER-BEARING content is verified:
type VerificationStatus =
  | "computed"         // values checked by real computation (sympy/numeric)
  | "vetted_pattern"   // expected result from a vetted template (experiments, models)
  | "open_judgement";  // no single key — teacher judges against an acceptable range

interface Baustein {
  id: string;
  order: number;              // suggested sequence; teacher may reorder
  optional: boolean;          // can be dropped without breaking other segments
  title: string;
  minutes: number;
  serves: string[];           // ResolvedCompetence.id[]
  primary_dimension: Dimension;
  artifact_type: ArtifactType;
  verification: VerificationStatus;
  teacher_face: TeacherFace;
  student_face: StudentFace;
  assets: Asset[];
}

interface TeacherFace {
  throughline: string;        // conceptual spine of the segment
  misconceptions: string[];   // to preempt
  answer_key?: string;        // W: computed solutions
  expected_result?: string;   // E: what it should show + typical error sources
  acceptable_reasoning?: string; // S: the RANGE of defensible answers, not one key
  timing_notes?: string;
  differentiation?: string;
}

interface StudentFace {
  body: string;               // the handout content (markdown)
  tasks: string[];
}

// ── visual assets: role selects the generator ──────────────
type AssetRole  = "decorative" | "content_bearing";
type Generator  = "diffusion" | "code_svg" | "code_matplotlib" | "code_tikz" | "none";

interface Asset {
  id: string;
  role: AssetRole;
  generator: Generator;       // must be permitted by the subject's SubjectVisualPolicy
  spec: string;               // diffusion prompt OR code-gen description
  text_overlay?: string;      // any text is added programmatically, never by diffusion
  correctness_surface: boolean; // === (role === "content_bearing")
}

// ── per-subject visual policy (NOT a global rule) ──────────
interface SubjectVisualPolicy {
  subject: string;
  diffusion_ok: string[];        // decorative categories allowed for this subject
  diffusion_forbidden: string[]; // off-limits even if "decorative" (uncanny-valley)
  must_be_code: string[];        // content-bearing inventory for this subject
}

// ── Layer 3: the compliance ledger ─────────────────────────
interface Nachweis {
  fassung: FassungRef;
  statement: string;          // one-glance teacher-facing sentence
  competence_coverage: { competence_id: string; served_by: string[] }[];
  zentrale_konzepte: string[];
  uebergreifende_themen: { id: number; name: string; served_by: string[] }[];
}

// ── the bundle ─────────────────────────────────────────────
interface Bundle {
  request: BundleRequest;
  resolution: LehrplanResolution;
  bausteine: Baustein[];
  nachweis: Nachweis;
  generated_at: string;       // ISO timestamp
}
```

**Deliberately omitted (v0.1):** UI/teacher dashboard, pricing, multilingual student output,
and the looser Oberstufe resolution (its Lehrstoff isn't per-grade or competence-tagged). None
are load-bearing until the core loop is proven.

---

## 2 · Reference instance — Strahlung, 4. Klasse, Doppelstunde

```yaml
request:
  subject: Physik
  klasse: 4
  stufe: Unterstufe
  schulform: Realgymnasium
  topic_raw: "EM-Wellen"          # teacher's loose phrase
  envelope: { kind: doppelstunde }
  options:
    ability_spread: heterogen
    equipment: ["UV-Perlen", "Sonnencreme", "Beamer/Internet"]  # → physical UV experiment possible
    prior_topics: ["Energie (3. Kl.)"]
    language_support: true

resolution:
  fassung:
    kurztitel: "Lehrpläne – allgemeinbildende höhere Schulen"
    bgbl: "BGBl. II Nr. 204/2024 (Stammf. BGBl. Nr. 88/1985)"
    doknr: "NOR40264237"
    valid_from: "2024-09-01"
    valid_to: "2026-08-31"
  matched_kompetenzbereiche:
    - { name: "Strahlung und Radioaktivität", klasse: 4 }
  grade_check:
    requested_klasse: 4
    lehrplan_klasse: 4
    status: match
  competences:
    - id: PHY.US.4.STR.01
      kompetenzbereich: "Strahlung und Radioaktivität"
      klasse: 4
      text: "Informationen zur Energie- und Informationsübertragung durch Strahlung
              recherchieren (W) und die Verlässlichkeit der Quellen bewerten (S)."
      dimensions: [W, S]
      uebergreifende_themen: []
      source_ref: "NOR40264237 · 8. Teil · Physik US · 4. Kl. · KB Strahlung u. Radioaktivität"
    - id: PHY.US.4.STR.02
      kompetenzbereich: "Strahlung und Radioaktivität"
      klasse: 4
      text: "die Interaktion unterschiedlicher Strahlungsarten (ua. sichtbare Strahlung,
              UV-Strahlung, IR-Strahlung, ionisierende Strahlung) mit Materie anhand
              geeigneter (auch virtueller) Untersuchungen analysieren (E) und daraus
              Konsequenzen für die Risikobewertung ziehen (S)."
      dimensions: [E, S]
      uebergreifende_themen: [11]      # 11 = Umweltbildung für nachhaltige Entwicklung (verbatim superscript)
      source_ref: "NOR40264237 · 8. Teil · Physik US · 4. Kl. · KB Strahlung u. Radioaktivität"
    - id: PHY.US.4.STR.03
      kompetenzbereich: "Strahlung und Radioaktivität"
      klasse: 4
      text: "den radioaktiven Zerfall als Zufallsprozess im Atomkern verstehen und mit
              Hilfe von Modellen darstellen. (W)"
      dimensions: [W]
      uebergreifende_themen: []
      source_ref: "NOR40264237 · 8. Teil · Physik US · 4. Kl. · KB Strahlung u. Radioaktivität"
    - id: PHY.US.4.STR.04
      kompetenzbereich: "Strahlung und Radioaktivität"
      klasse: 4
      text: "mit altersgemäßen Informationen zu aktueller physikalischer Forschung umgehen.
              (W, E, S)"
      dimensions: [W, E, S]
      uebergreifende_themen: []
      source_ref: "NOR40264237 · 8. Teil · Physik US · 4. Kl. · KB Strahlung u. Radioaktivität"
  zentrale_konzepte:
    # subject-level list is verbatim; binding them to THIS bundle is our editorial call
    - { name: "Energie", basis: editorial }
    - { name: "Schwingungen und Wellen", basis: editorial }
    - { name: "Teilchen", basis: editorial }     # supported by Anwendungsbereich "Teilchenmodelle ... Kernphysik"
  uebergreifende_themen:
    - { id: 11, name: "Umweltbildung für nachhaltige Entwicklung" }

bausteine:
  - id: B1
    order: 1
    optional: false
    title: "Strahlung trägt Energie und Information"
    minutes: 20
    serves: [PHY.US.4.STR.01]
    primary_dimension: W
    artifact_type: explainer
    verification: vetted_pattern
    teacher_face:
      throughline: "Strahlung überträgt Energie/Information; die Arten (IR→sichtbar→UV→
                     ionisierend) unterscheiden sich durch ihre Energie, nicht durch
                     'natürlich vs. gefährlich'. Anknüpfung an Anwendungen in Medizin/Technik."
      misconceptions:
        - "'Strahlung' = nur Radioaktivität"
        - "UV ist 'die Wärme der Sonne' (Verwechslung mit IR)"
      answer_key: "Kurzantworten zu den 3 Check-Fragen (s. student_face.tasks)."
      timing_notes: "5 min Einstieg über Alltagsgeräte, 10 min Aufbau, 5 min Check."
    student_face:
      body: "Kurzer Erklärtext: Strahlung als Energie-/Informationsträger; geordnete Familie
              IR–sichtbar–UV–ionisierend mit Alltagsquellen (Fernbedienung, Sonne, Mikrowelle,
              Röntgen)."
      tasks:
        - "Ordne 4 Alltagsquellen ihrer Strahlungsart zu."
        - "Welche Eigenschaft steigt von IR zu ionisierend? Begründe."
        - "Nenne je eine medizinische und eine technische Anwendung."
    assets:
      - id: A1
        role: content_bearing
        generator: code_svg
        spec: "Horizontale Energieachse IR→sichtbar→UV→ionisierend; Alltagsquellen als
                beschriftete Marker; Achsen/Beschriftung programmatisch overlaid."
        text_overlay: "IR · sichtbar · UV · ionisierend; Energie →"
        correctness_surface: true
      - id: A2
        role: decorative
        generator: diffusion
        spec: "Warme Fotoszene: Sonnenlicht fällt durch ein Fenster auf einen Schreibtisch.
                Keine Apparatur, kein Diagramm, kein Text."
        correctness_surface: false

  - id: B2
    order: 2
    optional: false
    title: "Strahlung trifft Materie — Untersuchung & Risiko"
    minutes: 30
    serves: [PHY.US.4.STR.02]
    primary_dimension: E
    artifact_type: experiment_protocol
    verification: vetted_pattern
    teacher_face:
      throughline: "UV-Perlen verfärben sich unter UV; Sonnencreme/Glas/Stoff schwächen
                     unterschiedlich → von der Beobachtung zur Risikobewertung (S)."
      misconceptions:
        - "Bewölkung = kein UV"
        - "Glas schützt vollständig vor UV"
      expected_result: "Perlen verfärben sich im direkten Sonnenlicht; unter Sonnencreme/
                         Karton kaum; hinter Fensterglas teilweise. Fehlerquellen: zu kurze
                         Belichtung, indirektes Licht, ungleichmäßiges Eincremen.
                         Virtuelle Alternative (PhET) falls kein Sonnenlicht."
      differentiation: "Leistungsstärkere: quantitativer Vergleich (Verfärbungsstufen);
                         schwächere: 3 Bedingungen qualitativ."
    student_face:
      body: "Protokoll: Material, Durchführung, Messtabelle (Bedingung → Verfärbung),
              Auswertung, Schlussfolgerung für den Alltag."
      tasks:
        - "Fülle die Messtabelle für 4 Bedingungen aus."
        - "Leite 2 Schutzmaßnahmen ab und begründe sie."
    assets:
      - id: A3
        role: content_bearing
        generator: code_svg
        spec: "Versuchsaufbau-Skizze: Perlenschale, Bedingungen (frei / Creme / Glas /
                Karton), Sonne. Beschriftung programmatisch."
        correctness_surface: true

  - id: B3
    order: 3
    optional: true
    title: "Zerfall als Zufall — Würfelmodell"
    minutes: 20
    serves: [PHY.US.4.STR.03]
    primary_dimension: W
    artifact_type: model_activity
    verification: computed
    teacher_face:
      throughline: "Jeder 'Kern' (Würfel) zerfällt pro Runde mit fester Wahrscheinlichkeit
                     → Halbwertszeit als statistisches, nicht deterministisches Konzept."
      misconceptions:
        - "Man kann vorhersagen, WANN ein einzelner Kern zerfällt"
      expected_result: "Mittelwert über die Klasse folgt der Exponentialkurve; einzelne
                         Gruppen streuen. Erwartete Kurve wird aus p und N berechnet (computed)."
    student_face:
      body: "Anleitung: N Würfel, pro Runde entfernen wer '6' zeigt, Anzahl notieren,
              gegen Rundenzahl auftragen."
      tasks:
        - "Trage deine Daten ein und vergleiche mit der Klassenkurve."
        - "Warum ist die Klassenkurve glatter als deine?"
    assets:
      - id: A4
        role: content_bearing
        generator: code_matplotlib
        spec: "Erwartete Zerfallskurve N·(5/6)^t plus Platz für eingetragene Messdaten;
                Werte berechnet."
        correctness_surface: true

  - id: B4
    order: 4
    optional: false
    title: "Was stimmt? Strahlungs-Mythen im Netz"
    minutes: 30
    serves: [PHY.US.4.STR.01, PHY.US.4.STR.04]
    primary_dimension: S
    artifact_type: source_critique
    verification: open_judgement
    teacher_face:
      throughline: "Zwei kontrastierende Online-Aussagen zu 'Strahlung' (z. B. Handy/5G,
                     Solarium) auf Quellenverlässlichkeit prüfen; eine aktuelle
                     Forschungsmeldung altersgemäß einordnen."
      misconceptions:
        - "Was oft geteilt wird, ist gut belegt"
      acceptable_reasoning: "BANDBREITE statt Musterlösung: akzeptabel sind Antworten, die
                              Quelle/Autor/Beleg unterscheiden, Energie der Strahlungsart
                              berücksichtigen und Unsicherheit benennen. NICHT akzeptabel:
                              reines Bauchgefühl ohne Quellenkriterium."
    student_face:
      body: "Zwei kurze Online-Schnipsel + eine Forschungsmeldung; Bewertungsraster
              (Wer? Beleg? Plausibel laut Strahlungsart?)."
      tasks:
        - "Bewerte beide Quellen mit dem Raster."
        - "Formuliere eine begründete Empfehlung an eine:n Mitschüler:in."
    assets:
      - id: A5
        role: decorative
        generator: diffusion
        spec: "Stimmungsbild: Jugendliche schauen auf ein Smartphone. Keine Diagramme,
                kein lesbarer Text, keine Messgeräte."
        correctness_surface: false

nachweis:
  fassung: { doknr: "NOR40264237", valid_from: "2024-09-01", valid_to: "2026-08-31" }
  statement: "Diese Doppelstunde bedient alle 4 Kompetenzbeschreibungen des Kompetenzbereichs
              'Strahlung und Radioaktivität' (Physik, 4. Klasse Unterstufe) gemäß
              BGBl. II Nr. 204/2024 und deckt die Handlungsdimensionen W, E und S ab."
  competence_coverage:
    - { competence_id: PHY.US.4.STR.01, served_by: [B1, B4] }
    - { competence_id: PHY.US.4.STR.02, served_by: [B2] }
    - { competence_id: PHY.US.4.STR.03, served_by: [B3] }
    - { competence_id: PHY.US.4.STR.04, served_by: [B4] }
  zentrale_konzepte: ["Energie", "Schwingungen und Wellen", "Teilchen"]
  uebergreifende_themen:
    - { id: 11, name: "Umweltbildung für nachhaltige Entwicklung", served_by: [B2] }
  # Editorially evident but NOT verbatim-tagged in the Lehrplan (shown separately, not asserted
  # as compliance): Medienbildung (B4), Gesundheitsförderung (B2/B4).

generated_at: "2026-06-24T00:00:00Z"
```

---

## 3 · `grade_check` in action — the trust feature

Same topic phrase, wrong grade. This is what the resolver returns if the teacher enters
**3. Klasse** for "EM-Wellen / Strahlung":

```yaml
grade_check:
  requested_klasse: 3
  lehrplan_klasse: 4
  status: mismatch
  note: >
    "Strahlung und Radioaktivität" ist im Lehrplan der 4. Klasse zugeordnet (inkl.
    "Anwendungen von elektromagnetischer Strahlung in Medizin und Technik"). In der
    3. Klasse umfasst Physik: Mechanik, Elektrizität und Magnetismus, Energie.
    Möchten Sie (a) das Material für die 4. Klasse, oder (b) ein 3.-Klasse-Thema
    (z. B. Elektrizität und Magnetismus)?
```

---

## 4 · Per-subject visual policy — Physik vs. Geographie

The decorative/content-bearing split is universal; **the boundary is the subject's call.**

```yaml
- subject: Physik
  diffusion_ok:
    - "Stimmungs-/Kontextszenen ohne Apparatur (Alltagssettings, die ein Problem motivieren)"
  diffusion_forbidden:
    - "alles, was nach Apparatur, Schaltkreis, Strahlengang, Spektrum oder Messgerät aussieht"
    - "beschriftete Strukturen; jedes Bild, aus dem ein Wert/Zusammenhang ablesbar wäre"
  must_be_code:
    - "Spektren & Energieachsen; Schaltkreis- & Strahlengangskizzen; Graphen/Plots;
       Kraft-/Vektordiagramme; Zerfallskurven"

- subject: Geographie und wirtschaftliche Bildung
  diffusion_ok:
    - "stilisierte Landschaften / Biom-Stimmungsbilder; Stadt-/Kulturszenen-Atmosphäre"
  diffusion_forbidden:
    - "Karten jeder Art (Grenzen, Küstenlinien, Ortslagen)"
    - "Choroplethen / thematische Karten; Profile & Querschnitte; Klimadiagramme;
       alles mit Ortsnamen oder Datenbeschriftung"
  must_be_code:
    - "alle Karten & Choroplethen (aus echten Geodaten); Klimadiagramme (aus Klimadaten);
       Querschnitte; Bevölkerungspyramiden; Diagramme"
```
