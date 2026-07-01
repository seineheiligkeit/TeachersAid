# Breiten-Generierung: Geometrisches Zeichnen — 5 Kernfragen

Du erzeugst **5 verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-Unterstufe** auf österreichischem Lehrplan-Niveau. Sprache: **Deutsch**, AHS-Niveau (nicht zu niedrig).
Wähle **5 klar unterschiedliche Themen/Bereiche** (Breite!), nicht Varianten desselben Themas.

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein), gruppiert nach Kompetenzbereich

### Geometrische Objekte und ihre Eigenschaften (I1)
- `GEZ.US.4.GEO.01` (Kl 4) [dims H1]: geometrische Objekte analysieren, ihre Eigenschaften erfassen und beschreiben sowie die Verwendung eines bestimmten geometrischen Objekts begründen. (H1)
- `GEZ.US.4.GEO.02` (Kl 4) [dims H2]: unterschiedliche Darstellungsformen von geometrischen Objekten erstellen. (H2)
- `GEZ.US.4.GEO.03` (Kl 4) [dims H3]: die Gestalt von Objekten aus unterschiedlichen Darstellungsformen erkennen und beschreiben. (H3)

### Projektionen und Risse (I3)
- `GEZ.US.4.PRO.01` (Kl 4) [dims H1]: Projektionen und Risse und ihre grundlegenden Eigenschaften beschreiben und erkennen sowie die Wahl eines bestimmten Risses begründen. (H1)
- `GEZ.US.4.PRO.02` (Kl 4) [dims H2]: Risse herstellen. (H2)
- `GEZ.US.4.PRO.03` (Kl 4) [dims H3]: Risse lesen. (H3)

### Transformationen von Objekten und Relationen zwischen Objekten (I2)
- `GEZ.US.4.TRA.01` (Kl 4) [dims H1]: Beziehungen zwischen Objekten, die durch Transformationen und Relationen entstehen, erfassen sowie die Verwendung bestimmter Transformationen und Relationen begründen. (H1)
- `GEZ.US.4.TRA.02` (Kl 4) [dims H2]: Objekte mithilfe von Transformationen und Relationen erzeugen und bearbeiten. (H2)
- `GEZ.US.4.TRA.03` (Kl 4) [dims H3]: Transformationen und Relationen, durch die Objekte entstehen, erkennen und beschreiben. (H3)

## Erlaubte Dimensionen (`dimensions`, primäre zuerst — Teilmenge dieser Codes)
- `H1` — Analysieren, Abstrahieren und Argumentieren
- `H2` — Darstellen und Operieren
- `H3` — Interpretieren und Reflektieren

## Erlaubte Aufgaben-`kind`-Werte
cad_model, construction, create_produce, data_interpretation, decision_scenario, matching, multiple_choice, open_response, ordering, table_fill, true_false_justify

## Anwendungsbereiche (Themen-Ideen für die Kernfragen)
- Kl 4: Räumliches kartesisches Koordinatensystem · Punkt, Gerade, Ebene, Polygon, Kreis, Ellipse · Prisma, Pyramide, Polyeder, Kugel, Drehkegel, Drehzylinder · Transformationen: Schiebung, Drehung, Spiegelung, Streckung · Ebene Schnitte, Boolesche Operationen: Vereinigung, Differenz, Durchschnitt · Maßbestimmungen, Lagebeziehungen · Parallelprojektion, Zentralprojektion · Grund-, Auf- und Kreuzriss, Frontal- und Horizontalriss, allgemeiner Parallelriss, Zentralriss
## Verankerung
Jede Kernfrage gehört zu **einem** Kompetenzbereich; setze im JSON `"kompetenzbereich": "<exakter KB-Name>"` und die passende `klasse` (eine Klasse, in der dieser KB Kompetenzen hat). Alle Aufgaben dieser Kernfrage dienen Kompetenzen aus diesem (KB, Klasse).


## Regeln (für jede der 5 Kernfragen)
- 5–7 Aufgaben (`blocks` mit role "task") + optional 1 kurzer Info-Block. Realistische `est_minutes`.
- Verankere **jede** Aufgabe via `serves` an einer der oben gelisteten IDs; nutze mehrere verschiedene.
- `dimensions` ⊆ erlaubte Codes; `kind` ∈ erlaubte kinds; `cognitive_level` steigt
  (remember→…→create; baue analyze/evaluate/create ein), nicht alles „remember".
- **Korrektheit by construction**; Fehlvorstellungen/Hinweise in `watch_outs` (tragend).
- **Keine Bilder/Assets**: kein `kind:"figure"`, kein `data_interpretation`, keine `asset_refs`,
  keine `response.mode` ∈ {diagram, drawing, artifact}. Reiner Text (modality "printable").
- **Schülertext ist für Schüler:innen** — niemals Kompetenz-IDs/Dimensionen/„Lehrplan" im `prompt`/Intro.
- Pro Aufgabe `answer_key` + `watch_outs`; optional `acceptable_reasoning` und `rubric`
  (Liste von `{"criterion":"...","levels":["...","..."]}`, **englische Schlüssel**).
- Pro Section die Lehrkraft-Ebene: `throughline` (Roter Faden), `talking_points` (2–4), `extensions` (1–3).

## Antwort-Formen (`response`): `{"mode":"lines","n":<int>}` · `{"mode":"box","min_height_mm":<float>}` ·
`{"mode":"table","columns":[...],"rows":<int>}` · `{"mode":"choices","options":[...],"select":"one"|"many"}` · `{"mode":"none"}`
## Payload (`payload`, optional, sonst null): multiple_choice `{"kind":"multiple_choice","options":[...],"select":"one"}` ·
true_false_justify `{"kind":"true_false_justify","statements":[...]}` · ordering `{"kind":"ordering","items":[...]}` ·
matching `{"kind":"matching","left":[...],"right":[...]}` · decision_scenario `{"kind":"decision_scenario","stem":"..."}`

## Ausgabe
Schreibe **5 Dateien**, eine pro Kernfrage, nach `runs/ingest/gen/GEZ_1.json` … `runs/ingest/gen/GEZ_5.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Geometrisches Zeichnen", "klasse": <1-4, eine Klasse mit Kompetenzen im gewählten Bereich>,
  "kompetenzbereich": "<KB-Name>",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {
    "intro": [],
    "sections": [ { "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{"mode":"lines","n":3},"cognitive_level":"understand","dimensions":["H1"],
        "serves":[{"competence_id":"<ID>","relation":"exercises"}],"est_minutes":7,
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]} ] } ]
  }
}
```
