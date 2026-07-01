# Breiten-Generierung: Zweite lebende Fremdsprache — 5 Kernfragen

Du erzeugst **5 verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-Unterstufe** auf österreichischem Lehrplan-Niveau. Sprache: **Deutsch**, AHS-Niveau (nicht zu niedrig).
Wähle **5 klar unterschiedliche Themen/Bereiche** (Breite!), nicht Varianten desselben Themas.

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein), gruppiert nach Kompetenzbereich

### Hören
- `FS2.US.3.HOR.01` (Kl 3) [dims HOR]: in kurzen Dialogen oder Monologen einfache Fragen und Sätze, die sich auf sie selbst und ihr persönliches Umfeld beziehen, verstehen.
- `FS2.US.3.HOR.02` (Kl 3) [dims HOR]: einfache alltägliche Kommunikation im Unterricht verstehen.
- `FS2.US.4.HOR.01` (Kl 4) [dims HOR]: Anweisungen, Fragen und Auskünfte verstehen.
- `FS2.US.4.HOR.02` (Kl 4) [dims HOR]: einfache kurze Gespräche und Texte über vertraute Themen verstehen.

### Lesen
- `FS2.US.3.LES.01` (Kl 3) [dims LES]: einfache Arbeitsanweisungen und Mitteilungen verstehen.
- `FS2.US.3.LES.02` (Kl 3) [dims LES]: sehr einfache Texte über vertraute Themen verstehen.
- `FS2.US.4.LES.01` (Kl 4) [dims LES]: kurze einfache Geschichten, Briefe, E-Mails oder bebilderte Sachtexte verstehen.
- `FS2.US.4.LES.02` (Kl 4) [dims LES]: kurzen vertrauten Alltagstexten wichtige Informationen entnehmen.

### Schreiben
- `FS2.US.3.SCH.01` (Kl 3) [dims SCH]: über sich selbst und vertraute Themen (ua. Familie, Freunde, Tagesablauf, Hobbys, Schule) in einfachen Sätzen schreiben.
- `FS2.US.3.SCH.02` (Kl 3) [dims SCH]: Informationen in geschriebener Form weitergeben (persönliche Meinungen).
- `FS2.US.4.SCH.01` (Kl 4) [dims SCH]: Aspekte des persönlichen Lebensumfeldes beschreiben (ua. Personen, Orte, Pläne, Wünsche).
- `FS2.US.4.SCH.02` (Kl 4) [dims SCH]: die eigene Meinung ausdrücken und begründen.
- `FS2.US.4.SCH.03` (Kl 4) [dims SCH]: einfache Geschichten und Gebrauchstexte (ua. E-Mails, Mitteilungen) schreiben und dabei auch über vergangene und zukünftige Ereignisse berichten.

### Sprechen (an Gesprächen teilnehmen und zusammenhängend sprechen)
- `FS2.US.3.SPR.01` (Kl 3) [dims SPR]: an Gesprächen teilnehmen und sich mit Hilfe des Gesprächspartners auf einfache Art verständigen.
- `FS2.US.3.SPR.02` (Kl 3) [dims SPR]: einfache Fragen stellen und beantworten.
- `FS2.US.3.SPR.03` (Kl 3) [dims SPR]: beim zusammenhängenden Sprechen in einfachen Sätzen über vertraute Themen (ua. Familie, Freunde, Tagesablauf, Hobbys, Schule) sprechen.
- `FS2.US.4.SPR.01` (Kl 4) [dims SPR]: kurze Gespräche über vertraute Themen führen.
- `FS2.US.4.SPR.02` (Kl 4) [dims SPR]: in Alltagssituationen einfache Informationen geben, Fragen stellen und Vereinbarungen treffen.
- `FS2.US.4.SPR.03` (Kl 4) [dims SPR]: über vertraute Themen (ua. Dinge, Orte, Personen) sprechen und dabei auch Gefühle, Vorlieben, Stärken und Meinungen auf einfache Weise ausdrücken.

## Erlaubte Dimensionen (`dimensions`, primäre zuerst — Teilmenge dieser Codes)
- `HOR` — Hören
- `LES` — Lesen
- `SPR` — Sprechen (an Gesprächen teilnehmen und zusammenhängend sprechen)
- `SCH` — Schreiben

## Erlaubte Aufgaben-`kind`-Werte
create_produce, data_interpretation, decision_scenario, listening_task, matching, multiple_choice, open_response, ordering, speaking_task, table_fill, text_production, true_false_justify
## Verankerung
Jede Kernfrage gehört zu **einem** Kompetenzbereich; setze im JSON `"kompetenzbereich": "<exakter KB-Name>"` und die passende `klasse` (eine Klasse, in der dieser KB Kompetenzen hat). Alle Aufgaben dieser Kernfrage dienen Kompetenzen aus diesem (KB, Klasse).


## Regeln (für jede der 5 Kernfragen)
- 5–7 Aufgaben (`blocks` mit role "task") + optional 1 kurzer Info-Block. Realistische `est_minutes`.
- Verankere **jede** Aufgabe via `serves` an einer der oben gelisteten IDs; nutze mehrere verschiedene.
- `dimensions` ⊆ erlaubte Codes; `kind` ∈ erlaubte kinds; `cognitive_level` steigt
  (remember→…→create; baue analyze/evaluate/create ein), nicht alles „remember".
- **Korrektheit by construction**; Fehlvorstellungen/Hinweise in `watch_outs` (tragend).
- **Keine Bilder/Assets**: kein `kind:"figure"`, kein `data_interpretation`, keine `asset_refs`,
  keine `response.mode` ∈ {diagram, drawing, artifact}. Sprech-/Hör-Aufgaben dürfen `modality` "oral" sein, schriftliche "printable". Beschreibe alles in Worten (keine Audiodateien).
- **Schülertext ist für Schüler:innen** — niemals Kompetenz-IDs/Dimensionen/„Lehrplan" im `prompt`/Intro.
- Pro Aufgabe `answer_key` + `watch_outs`; optional `acceptable_reasoning` und `rubric`
  (Liste von `{"criterion":"...","levels":["...","..."]}`, **englische Schlüssel**).
- Pro Section die Lehrkraft-Ebene: `throughline` (Roter Faden), `talking_points` (2–4), `extensions` (1–3).

## Sprache (WICHTIG)
Das **Sprachmaterial** (Texte, Dialoge, Wortschatz, Beispielsätze, die die Schüler:innen bearbeiten) ist in **Französisch**. Arbeitsanweisungen dürfen Deutsch oder Französisch sein (Unterstufe: oft Deutsch als Gerüst, später mehr Französisch). Die **Lehrkraft-Ebene** (throughline/talking_points/extensions) und `watch_outs` bleiben **Deutsch**. `answer_key` in Französisch (Modelllösung), bei Bedarf mit kurzer deutscher Notiz.

## Antwort-Formen (`response`): `{"mode":"lines","n":<int>}` · `{"mode":"box","min_height_mm":<float>}` ·
`{"mode":"table","columns":[...],"rows":<int>}` · `{"mode":"choices","options":[...],"select":"one"|"many"}` · `{"mode":"none"}`
## Payload (`payload`, optional, sonst null): multiple_choice `{"kind":"multiple_choice","options":[...],"select":"one"}` ·
true_false_justify `{"kind":"true_false_justify","statements":[...]}` · ordering `{"kind":"ordering","items":[...]}` ·
matching `{"kind":"matching","left":[...],"right":[...]}` · decision_scenario `{"kind":"decision_scenario","stem":"..."}`

## Ausgabe
Schreibe **5 Dateien**, eine pro Kernfrage, nach `runs/ingest/gen_lang/FS2_1.json` … `runs/ingest/gen_lang/FS2_5.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Zweite lebende Fremdsprache", "klasse": <1-4, eine Klasse mit Kompetenzen im gewählten Bereich>,
  "kompetenzbereich": "<KB-Name>",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {
    "intro": [],
    "sections": [ { "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{"mode":"lines","n":3},"cognitive_level":"understand","dimensions":["HOR"],
        "serves":[{"competence_id":"<ID>","relation":"exercises"}],"est_minutes":7,
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]} ] } ]
  }
}
```
