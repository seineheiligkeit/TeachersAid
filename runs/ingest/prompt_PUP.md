# Breiten-Generierung: Psychologie und Philosophie — 2 Kernfragen

Du erzeugst **2 verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-Oberstufe** auf österreichischem Lehrplan-Niveau. Sprache: **Deutsch**, AHS-Niveau (anspruchsvoll, Sek II).
Wähle **2 klar unterschiedliche Themen/Bereiche** (Breite!), nicht Varianten desselben Themas.

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein), gruppiert nach Kompetenzbereich

### Anthropologische Entwürfe
- `PUP.OS.8.ANT.01` (Kl 8) [dims —]: Anthropologische Konzepte unterscheiden und interpretieren
- `PUP.OS.8.ANT.02` (Kl 8) [dims —]: Wissen aus verschiedenen Fachgebieten für eine reflektierte Auseinandersetzung heranziehen

### Aspekte der Erkenntnis- und Wissenschaftstheorie
- `PUP.OS.8.ASP3.01` (Kl 8) [dims —]: Zugänge zur Wirklichkeit und ihre Interpretationsmöglichkeiten analysieren und reflektieren
- `PUP.OS.8.ASP3.02` (Kl 8) [dims —]: Erkenntnis- und wissenschaftstheoretische Fragestellungen bearbeiten

### Aspekte der Persönlichkeit
- `PUP.OS.7.ASP2.01` (Kl 7) [dims —]: Menschliches Erleben und Verhalten aus Sicht der Persönlichkeitspsychologie beschreiben
- `PUP.OS.7.ASP2.02` (Kl 7) [dims —]: Die Bedeutung von Emotionen erfassen
- `PUP.OS.7.ASP2.03` (Kl 7) [dims —]: Seelische Gesundheit und deren Beeinträchtigung diskutieren

### Aspekte der wissenschaftlichen Psychologie
- `PUP.OS.7.ASP.01` (Kl 7) [dims —]: Zentrale Begriffe (Psychologie, Experiment, Objektivität …) beschreiben
- `PUP.OS.7.ASP.02` (Kl 7) [dims —]: Unterschiede zwischen Alltagspsychologie und wissenschaftlicher Psychologie erörtern
- `PUP.OS.7.ASP.03` (Kl 7) [dims —]: Methoden der Psychologie darlegen und reflektieren
- `PUP.OS.7.ASP.04` (Kl 7) [dims —]: Beziehungen zwischen psychologischen Erkenntnissen und Lebenspraxis herstellen

### Fragen der Entwicklung und Erziehung
- `PUP.OS.7.FRA.01` (Kl 7) [dims —]: Phänomene der psychischen Entwicklung wiedergeben
- `PUP.OS.7.FRA.02` (Kl 7) [dims —]: Die Bedeutung verschiedener Einflüsse auf die Entwicklung erkennen und reflektieren

### Grundfragen der Ethik
- `PUP.OS.8.GRU2.01` (Kl 8) [dims —]: Ethische Grundpositionen erklären und kritisch hinterfragen
- `PUP.OS.8.GRU2.02` (Kl 8) [dims —]: Differenzen in ethischen Konzepten herausarbeiten
- `PUP.OS.8.GRU2.03` (Kl 8) [dims —]: Werthaltungen in privaten, politischen und ökologischen Fragen entwickeln und begründen

### Grundlagen der Philosophie
- `PUP.OS.8.GRU.01` (Kl 8) [dims —]: Charakteristika der Philosophie und philosophische Grundbegriffe beschreiben
- `PUP.OS.8.GRU.02` (Kl 8) [dims —]: Philosophische Fragestellungen beurteilen
- `PUP.OS.8.GRU.03` (Kl 8) [dims —]: Methoden des Philosophierens darlegen und anwenden

### Kognitive Prozesse und Lernen
- `PUP.OS.7.KOG.01` (Kl 7) [dims —]: Modelle zum Gedächtnis und Lernen wiedergeben
- `PUP.OS.7.KOG.02` (Kl 7) [dims —]: Eigenes Lernen mit theoretischen Erkenntnissen vergleichen und reflektieren
- `PUP.OS.7.KOG.03` (Kl 7) [dims —]: Aktuelle Erkenntnisse zum Denken erklären

### Phänomene der Wahrnehmung und Wahrnehmungsprozesse
- `PUP.OS.7.PHA.01` (Kl 7) [dims —]: Wahrnehmung als aktiven und zweckvollen Prozess beschreiben
- `PUP.OS.7.PHA.02` (Kl 7) [dims —]: Fehler in der Wahrnehmung erkennen und sich bewusst machen
- `PUP.OS.7.PHA.03` (Kl 7) [dims —]: Selektive Prozesse der Wahrnehmung erfassen und analysieren
- `PUP.OS.7.PHA.04` (Kl 7) [dims —]: Wahrnehmungsbeeinflussungen erörtern

### Soziale Phänomene und Kommunikation
- `PUP.OS.7.SOZ.01` (Kl 7) [dims —]: Soziale Phänomene beschreiben und reflektieren
- `PUP.OS.7.SOZ.02` (Kl 7) [dims —]: Formen von Aggression und Gewalt erkennen und analysieren
- `PUP.OS.7.SOZ.03` (Kl 7) [dims —]: Kommunikationsprozesse darstellen und differenziert beurteilen

## Erlaubte Dimensionen (`dimensions`, primäre zuerst — Teilmenge dieser Codes)
- `WIS` — Wissen reproduzieren
- `TRA` — Wissen verknüpfen und transferieren
- `REF` — Reflektieren

## Erlaubte Aufgaben-`kind`-Werte
argumentation, create_produce, data_interpretation, decision_scenario, dilemma, matching, multiple_choice, open_response, ordering, table_fill, text_analysis, true_false_justify
## Verankerung
Jede Kernfrage gehört zu **einem** Kompetenzbereich; setze im JSON `"kompetenzbereich": "<exakter KB-Name>"` und die passende `klasse` (eine Klasse, in der dieser KB Kompetenzen hat). Alle Aufgaben dieser Kernfrage dienen Kompetenzen aus diesem (KB, Klasse).


## Regeln (für jede der 2 Kernfragen)
- 5–7 Aufgaben (`blocks` mit role "task") + optional 1 kurzer Info-Block. Realistische `est_minutes`.
- Verankere **jede** Aufgabe via `serves` an einer der oben gelisteten IDs; nutze mehrere verschiedene.
- `dimensions` ⊆ erlaubte Codes; `kind` ∈ erlaubte kinds; `cognitive_level` steigt
  (remember→…→create; baue analyze/evaluate/create ein), nicht alles „remember".
- **Korrektheit by construction**; Fehlvorstellungen/Hinweise in `watch_outs` (tragend).
- **Abbildungen — Code-generiert, korrekt by construction** (nie freie Bilder/Diffusion): wo eine
  Abbildung die Aufgabe wirklich verbessert (v.a. Mathematik, Physik, Daten), fordere eine an und
  referenziere sie aus einer Aufgabe/Info über `asset_refs`. Reiner Text bleibt völlig ok, wenn keine
  Abbildung nötig ist.
  **Für DATEN: deklariere die ABSICHT, nicht den Diagrammtyp** — lege die Figur in `body.data_figures`;
  das System wählt daraus die passende, lesbare Darstellung (so wird nicht alles ein Balkendiagramm).
  Form: `{"id":str,"intent":str,"title"?,"xlabel"?,"ylabel"?,"categories"?:[str],"values"?:[num],"points"?:[[x,y]],"log"?:bool,"fit"?:bool,"data_source"?:{"dataset_id":str,"series":str}}`
  mit `intent` ∈
    - `trend` — Verlauf/Entwicklung (oft über die Zeit): `categories`+`values` → Liniendiagramm
    - `comparison` — MENGEN-Vergleich zwischen Kategorien: `categories`+`values` → Balkendiagramm
    - `relationship` — Zusammenhang zweier numerischer Größen: `points` (+`fit` für Trendgerade) → Streudiagramm
    - `distribution` — Häufigkeit/Streuung einer Größe: `values` → Histogramm
    - `scale` — Position auf einer Skala (z. B. pH-Wert): `categories`+`values` → Zahlenstrahl
    - `demographic` — Alter × Geschlecht: `categories` (Altersgruppen)+`male`+`female` → Bevölkerungspyramide
  **Wähle nie selbst „Balken" für eine Zeitreihe, eine Ja/Nein-Klassifikation oder eine Skala** —
  dafür ist der `intent` da; korrekte Zahlen allein genügen NICHT, die Darstellung muss zur Aussage passen.
  **Für STRUKTUR-Abbildungen** (Funktionsgraph, Formel, fertiger Zahlenstrahl) nutze `body.assets` mit
  explizitem Generator — **erlaubte Generatoren (nur diese):**
  - `matplotlib:number_line` — Zahlenstrahl — spec {"min":num,"max":num,"step"?:num,"marks"?:[{"at":num,"label"?:str}]}
  - `matplotlib:bar_chart` — Balkendiagramm für einen MENGEN-Vergleich (nicht für eine Ja/Nein-Klassifikation!) — spec {"categories":[str],"values":[num],"title"?:str,"xlabel"?:str,"ylabel"?:str,"log"?:bool}. Kurze Kategorienamen; bei Werten über mehrere Größenordnungen "log":true setzen.
  - `matplotlib:line` — Liniendiagramm für einen TREND / Verlauf über die Zeit — spec {"categories":[str]|"x":[num],"values":[num] | "series":[{"label"?,"x":[...],"y":[...]}],"xlabel"?,"ylabel"?,"title"?,"log"?}
  - `matplotlib:scatter` — Streudiagramm für einen ZUSAMMENHANG zweier numerischer Größen — spec {"points":[[x,y]],"xlabel"?,"ylabel"?,"title"?,"fit"? (Trendgerade)}
  - `matplotlib:histogram` — Histogramm für die VERTEILUNG einer numerischen Größe — spec {"values":[num],"bins"?,"xlabel"?,"ylabel"?,"title"?}
  - `matplotlib:function_graph` — Koordinatensystem/Gerade — spec {"xmin"?,"xmax"?,"m"?,"b"? (Gerade y=mx+b),"points"?:[[x,y]],"connect"? (Punkte zu einer Kurve verbinden, z. B. v-t-Diagramm),"xlabel"?,"ylabel"?,"ymin"?,"ymax"?,"title"?}
  - `matplotlib:math_formula` — Formel via LaTeX — spec {"latex":str}
  - `matplotlib:population_pyramid` — Bevölkerungspyramide (Alter × Geschlecht, gegenläufige Balken) — spec {"age_groups":[str],"male":[num],"female":[num],"title"?:str,"xlabel"?:str}. NUR mit echten, zitierten Daten verwenden (data_source auf einen Datensatz setzen).
  - `matplotlib:right_triangle` — Rechtwinkliges Dreieck (Pythagoras) — spec {"a":num,"b":num,"label_a"?,"label_b"?,"label_c"?,"title"?}. Beschriftungen sind Strings (z. B. "a = 3 cm", "c = ?") — die Abbildung darf die Lösung NICHT verraten.
  - `matplotlib:rectangle` — Rechteck mit Maßen — spec {"length":num,"width":num,"label_l"?,"label_w"?,"title"?}.
  - `matplotlib:polygon` — Vieleck (Dreieck/Viereck …) — spec {"points":[[x,y]],"vertex_labels"?:[str],"side_labels"?:[str],"title"?}.
  - `matplotlib:circle` — Kreis mit Radius — spec {"radius":num,"label_r"?,"title"?}.
  - `matplotlib:coordinate_plane` — Koordinatensystem mit Punkten/Strecken — spec {"points":[{"x":num,"y":num,"label"?}],"segments"?:[[i,j]],"xmin"?,"xmax"?,"ymin"?,"ymax"?,"title"?}.
  - `matplotlib:timeline` — Zeitleiste (chronologische Ereignisse, GPB) — spec {"events":[{"at":num,"label":str}],"title"?:str,"xlabel"?:str}.
  - `matplotlib:climate_diagram` — Klimadiagramm (Monats-Temperatur als Linie + Niederschlag als Balken, zwei Achsen) — spec {"months"?:[12 str],"temp":[12 num],"precip":[12 num],"title"?:str}. Echte Klimadaten zitieren (data_source), sonst illustrative=true.
  **Wichtig — eine Abbildung darf die gesuchte Lösung NICHT verraten:** z. B. KEINE Funktionsgleichung
  als Diagramm-`title`, wenn die Aufgabe ist, sie abzulesen; keine Werte/Beschriftungen anzeigen, die die
  Schüler:innen erst ablesen/bestimmen sollen. Die Abbildung zeigt das Material, nicht die Antwort.
  Keine freien Bilder/Diffusion, kein `data_interpretation`-Payload,
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
Schreibe **2 Dateien**, eine pro Kernfrage, nach `runs/ingest/gen_os/PUP_1.json` … `runs/ingest/gen_os/PUP_2.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Psychologie und Philosophie", "klasse": <5-8, eine Klasse mit Kompetenzen im gewählten Bereich>,
  "kompetenzbereich": "<KB-Name>",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {
    "intro": [],
    "data_figures": [ /* bevorzugt für Daten: {"id":"abb1","intent":"trend","title":"...","xlabel":"Jahr","ylabel":"%","categories":["1990","2010","2024"],"values":[29,43,57]} */ ],
    "assets": [ /* nur Struktur-Figuren: {"id":"abb2","role":"figure","generator":"matplotlib:function_graph","spec":{"m":2,"b":1}} */ ],
    "sections": [ { "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{"mode":"lines","n":3},"cognitive_level":"understand","dimensions":["WIS"],
        "serves":[{"competence_id":"<ID>","relation":"exercises"}],"est_minutes":7,"asset_refs":[],
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]} ] } ]
  }
}
```
