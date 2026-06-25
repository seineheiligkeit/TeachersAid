# Subject-Coverage Audit — AHS Unterstufe *(against schema v0.3, toward v0.4)*

Every Unterstufe Pflichtgegenstand of the reformed AHS Lehrplan, read from the Fassung
(BGBl. II Nr. 204/2024) and tested against the v0.3 block model. The question for each: **does its
competence model pour into the schema seamlessly, or does it force a modification?**

Headline: the block model + subject-parameterized dimensions hold for **all 16 subjects** — I was
never confused about where a piece goes. But the audit forces **one structural addition** (modality
must live at the *dimension* level, not just the block level), **one new asset medium** (audio), and
**one new response type** (produced-artifact / rubric) — and it draws a hard, honest line about which
subjects a printable worksheet can actually serve.

## The audit

Verdicts: ● seamless (cognitive/printable competences) · ◐ works with a specific modification ·
○ schema is fine, but a worksheet covers only a thin slice (the core competences are performed/made).

| Subject (Klassen) | Competence axis — *verbatim from the Fassung* | 2nd axis | New TaskKinds | Media / modality need | |
|---|---|---|---|---|:--:|
| **Physik** (2–4) | W · E · S (Naturwissenschaften) | — | experiment_protocol, source_critique | — | ● |
| **Chemie** (4) | W · E · S — *identical model* | Inhaltsdimension | (shares Physik's) | — | ● |
| **Biologie u. Umweltbildung** (1–4) | W · E · S — *identical model* | — | (shares Physik's) | — | ● |
| **Mathematik** (1–4) | Modellieren·Operieren·Darstellen·Begründen | Zahlen/Variablen/Figuren/Daten | calculation, construction, modelling_task | — | ● |
| **Geometrisches Zeichnen** (4, RG) | geometr. Handlungsdim. | I1 Objekte · I2 Transformationen · I3 Projektionen/Risse | construction, cad_model | Geometrie-Software (interactive, optional) | ● |
| **Geographie u. wirtschaftl. Bildung** (1–4) | Orientierungs- · Urteils- · Handlungskompetenz | Anforderungsbereiche | map_work, case_study, position_argument | — | ● |
| **Geschichte u. politische Bildung** (2–4) | hist. Frage/Methoden/Orientierung/Sach · pol. Urteils/Methoden/Handlungs/Sach | — | source_analysis (De-/Re-Konstruktion), position_argument | (Handlung partly simulativ) | ● |
| **Ethik** (1–4) | 5 Bereiche: Wahrnehmen u. Perspektiven · Analysieren u. Reflektieren · Argumentieren/Urteilen · … | — | text_analysis, position_argument | (discussion = oral) | ● |
| **Deutsch** (1–4) | Sprachbewusstsein · Zuhören u. Sprechen · Lesen · Schreiben | — | text_production, text_analysis, **speaking_task** | **Sprechen = oral** | ● |
| **Latein** (3–4) | Sprach-/textbezogene · Kultur-/Sachkompetenz | — | **translation**, text_analysis | content in target language | ● |
| **Lebende Fremdsprache** (1–4) | Hören · Lesen · Sprechen (Gespräch + zusammenhängend) · Schreiben · Sprachmittlung | GeR/CEFR levels | listening_task, **speaking_task**, text_production | **Hören = audio asset · Sprechen = oral · target language** | ◐ |
| **Digitale Grundbildung** (1–4) | Orientierung · Information · Kommunikation · Produktion (+ Programmieren) · Handeln | — | **programming**, media_analysis | Kommunikation/Produktion/Programmieren = **enactive on device** | ◐ |
| **Technik und Design** (1–4) | Entwicklung · **Herstellung** · Reflexion | — | design_task, **make_artifact** | Herstellung = **enactive (making)** | ○ |
| **Kunst und Gestaltung** (1–4) | **bildnerische Praxis** (largest) · Wahrnehmen/Erschließen · Reflektieren | bildende Kunst, gestaltete Umwelt, visuelle Komm. | **make_artifact**, image_analysis | Praxis = **enactive (producing)** | ○ |
| **Musik** (1–4) | **Singen u. Musizieren** · **Tanzen, Bewegen, Darstellen** · Hören u. Erfassen | — | **performance_task**, listening_task | 2/3 dims **enactive/performed**; Hören = **audio** | ○ |
| **Bewegung und Sport** (1–4) | physisch/psychisch/sozial/kognitiv — movement competences | — | movement_task, training_log | **almost entirely enactive (physical)** | ○ |
| *Religion* | governed separately (Konkordat/recognised churches) — not in this competence format | — | — | — | — |

## What the audit revealed

**1. The three sciences share one model.** Physik, Chemie, and Biologie all use the identical
*Naturwissenschaften* W/E/S triad (only the glosses differ: "Fachwissen anwenden" / "Wissen aneignen
und kommunizieren" / "Aneignen, Anwenden und Kommunizieren von Wissen"). That's an economy, not a gap:
**one `SubjectCompetenceModel` serves three subjects.** The v0.3 model just needs to be *shareable/
referenceable* across subjects, with optional per-subject label overrides.

**2. Modality must move up to the *dimension* level.** v0.3 put `modality` on the block. But the
audit shows the decisive fact is *per competence dimension*: in Physik all three dimensions are
printable; in Musik two of three are performed; in Sport essentially none are. Promoting `modality`
onto `CompetenceDimension` lets us **compute, before generating anything, what fraction of a subject a
worksheet can even address** — turning the ●/◐/○ verdict from my judgement into a derived number:

```
printable_coverage(subject) = printable dimensions / all dimensions
  Physik / Chemie / Biologie / Math / GWB / GPB / Ethik / Latein ≈ 1.0   ●
  Deutsch ≈ 0.75 (Sprechen oral)                                          ●
  Fremdsprache ≈ 0.5 (Hören audio, Sprechen oral)                         ◐
  Digitale Grundbildung ≈ 0.4 (Produktion/Programmieren/Handeln enactive) ◐
  Technik u. Design ≈ 0.33  ·  Kunst ≈ 0.33  ·  Musik ≈ 0.33              ○
  Bewegung und Sport ≈ 0.0                                                ○
```

**3. The asset model is visual-only — Fremdsprache and Musik need audio.** Listening comprehension and
*Hören und Erfassen* require an **audio** asset; our `Asset` + `SubjectVisualPolicy` assume visuals.
This also reopens the correctness boundary: TTS for a language prompt is generatable correct-by-
construction, **music audio is not** — so the per-medium policy must flag what can and can't be
machine-produced safely.

**4. Production & performance need a produced-artifact response.** Kunst's *gestalte…*, Technik's
*stelle her…*, Musik's *musiziere…*, and long Deutsch/Ethik writing have no answer key — the "answer"
is an artifact judged against criteria. v0.3's `acceptable_reasoning` covers open judgement; these need
a structured **`rubric`** and a `ResponseSpec {mode:"artifact"}` (the student produces something off
the sheet).

**5. The honest scope line.** This is the most decision-relevant output, and it's a *product* finding,
not just a schema one. A printable, competence-anchored worksheet is:
- **strong** for the cognitive subjects — the three sciences, Mathematik, GWB, Geschichte, Ethik,
  Latein, and Deutsch's written strand (≈ 8–9 subjects at ~full coverage);
- **partial** for Fremdsprache, Digitale Grundbildung, Geometrisches Zeichnen (need audio / oral /
  enactive-on-device / dynamic-software handling);
- **marginal** for Bewegung und Sport, Musik, Kunst, Technik und Design — the schema can represent the
  *analysis / planning / reflection* slice, but the subject's core competences are performed or made,
  and a worksheet structurally touches little of them.

This maps cleanly onto the wedge: lead where coverage is ~1.0 (the cognitive subjects, MINT sharpest),
extend into the ◐ subjects as audio/oral support matures, and don't pretend a worksheet is the right
instrument for the ○ subjects.

## Schema deltas toward v0.4 *(each traced to its forcing subjects)*

- **`SubjectCompetenceModel` becomes shareable** (one Naturwissenschaften model → Physik/Chemie/Bio),
  with optional per-subject label overrides. *(sciences)*
- **`CompetenceDimension.modality: printable | oral | enactive`**, and a derived
  `printable_coverage` per subject. *(Musik, Sport, FS, Deutsch, DigGrund)*
- **`Asset.medium: visual | audio | interactive`**; generalise `SubjectVisualPolicy` → `MediaPolicy`
  with a `machine_generatable` flag per medium. *(Fremdsprache, Musik)*
- **`TaskBlock.rubric?: RubricCriterion[]`** + **`ResponseSpec {mode:"artifact"}`**. *(Kunst, Technik,
  Musik, long Deutsch/Ethik)*
- **`meta.content_language`** (worksheet language ≠ German). *(Fremdsprache, Latein)*
- **Populate the `task_kind_extensions` catalogue**: translation, listening_task, speaking_task,
  construction, cad_model, programming, source_analysis, make_artifact, performance_task, movement_task,
  position_argument, text_production, text_analysis. *(confirms v0.3's open-set decision; all subjects)*

None of these breaks v0.3 — they are additive. The block model, `CognitiveLevel` depth contract,
subject-parameterized dimensions, derived `Nachweis`/`DepthProfile`, and renderer-independent
projection all survive the full Unterstufe unchanged.

## Open / next
Fold these six deltas into **v0.4**, then the audit's positioning consequence (lead with the ●
subjects) feeds the eventual subject-rollout order. Still deferred: the template/shape layer, the
engine, difficulty calibration, Oberstufe (looser, legacy-prose resolution).
