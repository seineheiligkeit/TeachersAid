# ZUSATZ-AUFTRAG: Alle 2 Arbeitsblätter sind für **Klasse 3**, und decken die unten gelisteten Kompetenzbereiche ab (≥1 Kernfrage je KB; sei kreativ bei Titel/Kernfrage). Setze `"kompetenzbereich"` exakt auf den jeweiligen KB-Namen.

# Breiten-Generierung: Geographie und wirtschaftliche Bildung — 2 Kernfragen

Du erzeugst **2 verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-Unterstufe** auf österreichischem Lehrplan-Niveau. Sprache: **Deutsch**, AHS-Niveau (nicht zu niedrig).
Wähle **2 klar unterschiedliche Themen/Bereiche** (Breite!), nicht Varianten desselben Themas.

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein), gruppiert nach Kompetenzbereich

### Österreichische Gesellschaftsentwicklung
- `GWB.US.3.OST.01` (Kl 3) [dims —]: aktuelle demografische Strukturen und Prozesse beschreiben und deren mediale Darstellungen interpretieren sowie die Bedeutung für die eigene und gesellschaftliche Zukunft erörtern;
- `GWB.US.3.OST.02` (Kl 3) [dims —]: die Auswirkungen von Selbst- und Fremdbildern auf das gesellschaftliche Zusammenleben beschreiben und dabei die Bedeutung von biologischem Geschlecht, Gender, Alter, Bildung, Einkommen, Wohlstand, Nationalität, Religion oder Kultur hinterfragen.

### Zentren und Peripherien in Österreich
- `GWB.US.3.ZEN.01` (Kl 3) [dims —]: Zentren und Peripherien Österreichs abgrenzen, in Geomedien verorten und die Relativität jeder Abgrenzung erläutern;
- `GWB.US.3.ZEN.02` (Kl 3) [dims —]: die Gestaltung von zentralen und peripheren Lebensräumen mit Hilfe von originalen Begegnungen und Geomedien vergleichen und deren Lebensqualität individuell bewerten;
- `GWB.US.3.ZEN.03` (Kl 3) [dims —]: mit Hilfe von (Geo-)Medien die Raumnutzungen für Wohnen, Arbeit, Verkehr, Freizeitaktivitäten und Tourismus vergleichen sowie Lösungsansätze der Raumplanung bei Nutzungskonflikten erörtern.

## Erlaubte Dimensionen (`dimensions`, primäre zuerst — Teilmenge dieser Codes)
- `OK` — Orientierungskompetenz
- `UK` — Urteilskompetenz
- `HK` — Handlungskompetenz

## Erlaubte Aufgaben-`kind`-Werte
case_study, create_produce, data_interpretation, decision_scenario, map_work, matching, multiple_choice, open_response, ordering, position_argument, table_fill, true_false_justify

## Anwendungsbereiche (Themen-Ideen für die Kernfragen)
- Kl 1: Materielle und immaterielle Bedürfnisse (ausgehend von der Lebenswelt der Schülerinnen und Schüler); · Lebensqualität und Nachhaltigkeit; · Kommunikation und räumliche Orientierung mit Geomedien; · Produktion und Konsum von Gütern und Dienstleistungen durch Haushalte, Unternehmen und weitere Wirtschaftsteilnehmer · Verantwortungsvoller Umgang mit Geld; · Wohnen, Arbeit und Mobilität aus Zentren und Peripherien; · Reichtum und Armut; · Grundlagen des Klimawandels;
- Kl 2: Energieträger in Zusammenhang mit Nachhaltigkeit und Klimawandel; · Umgang mit natürlichen Ressourcen und Rohstoffkreisläufe; · Arbeitswelt und Berufsorientierung; · Sparen und Risiko; · Arbeitsteiliges und spezialisiertes nachhaltiges Wirtschaften; · Digitalisierung und ihre Folgen; · Projektplanung und -durchführung im Rahmen der Entrepreneurship Education · Unternehmerisches Denken und Handeln.
- Kl 3: Demographie, gesellschaftliche Diversität und Altersversorgung; · Bildungswege und Berufsbilder; · Arbeit, Einkommen und Konsumentenschutz; · Standortfaktoren und Standortentscheidungen; · Wirtschaftsteilnehmerinnen und Wirtschaftsteilnehmer; · Preise und Wettbewerb in der sozialen Marktwirtschaft; · Armut, Reichtum und Einkommensverteilung; · Nachhaltige und zukunftsfähige Entwicklung des Wirtschaftsstandorts Österreich;
- Kl 4: Mensch-Umweltverhältnis im Anthropozän; · Belastungsgrenzen der Erde; · Werte und zentrale Themen der EU; · Europäische Integration einschließlich gesellschaftliche und wirtschaftliche Folgen; · Globale Bevölkerungsdynamik, Urbanisierung; · Wirtschaftlicher und gesellschaftlicher Wandel durch Globalisierung und Deglobalisierung; · Gemeinsame Herausforderungen in Gesellschaft, Wirtschaft, Politik und Umwelt; · Eigene Chancen und Perspektiven in einer globalisierten Welt.
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
  Form: `{"id":str,"intent":str,"title"?,"xlabel"?,"ylabel"?,"categories"?:[str],"values"?:[num],"points"?:[[x,y]],"log"?:bool,"fit"?:bool}`
  mit `intent` ∈
    - `trend` — Verlauf/Entwicklung (oft über die Zeit): `categories`+`values` → Liniendiagramm
    - `comparison` — MENGEN-Vergleich zwischen Kategorien: `categories`+`values` → Balkendiagramm
    - `relationship` — Zusammenhang zweier numerischer Größen: `points` (+`fit` für Trendgerade) → Streudiagramm
    - `distribution` — Häufigkeit/Streuung einer Größe: `values` → Histogramm
    - `scale` — Position auf einer Skala (z. B. pH-Wert): `categories`+`values` → Zahlenstrahl
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
Schreibe **2 Dateien**, eine pro Kernfrage, nach `runs/ingest/gwb_full/GWB_kl3_1.json` … `runs/ingest/gwb_full/GWB_kl3_2.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Geographie und wirtschaftliche Bildung", "klasse": <1-4, eine Klasse mit Kompetenzen im gewählten Bereich>,
  "kompetenzbereich": "<exakter KB-Name>",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {
    "intro": [],
    "data_figures": [ /* bevorzugt für Daten: {"id":"abb1","intent":"trend","title":"...","xlabel":"Jahr","ylabel":"%","categories":["1990","2010","2024"],"values":[29,43,57]} */ ],
    "assets": [ /* nur Struktur-Figuren: {"id":"abb2","role":"figure","generator":"matplotlib:function_graph","spec":{"m":2,"b":1}} */ ],
    "sections": [ { "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{"mode":"lines","n":3},"cognitive_level":"understand","dimensions":["OK"],
        "serves":[{"competence_id":"<ID>","relation":"exercises"}],"est_minutes":7,"asset_refs":[],
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]} ] } ]
  }
}
```


## Lokaler Bezug (WICHTIG für dieses Set)
Mindestens die Hälfte der Aufgaben soll einen **lokalen Bezug** haben — aber nach dem
Forschungs-Prinzip: die Schüler:innen **erkunden ihre eigene Region selbst** (Schulgemeinde,
Bezirk, Bundesland). Das Arbeitsblatt **behauptet KEINE konkreten Ortsfakten** (keine
erfundenen Einwohnerzahlen, Flüsse, Betriebe, Höhen) — es liefert nur das Gerüst, die Daten
holen sich die Schüler:innen (Atlas, Statistik-Austria-Seite, eigene Beobachtung, Lehrkraft).
GUT: „Trage die Einwohnerzahl deiner Schulgemeinde ein (Quelle: …) und vergleiche mit …",
„Ordne drei Betriebe in deiner Umgebung den Wirtschaftssektoren zu", „Markiere auf der Karte,
was du als Zentrum und was als Peripherie deiner Region siehst".
NICHT TUN: konkrete Ortsfakten behaupten („Salzburg hat 156.000 Einwohner"). Formuliere
region-agnostisch („deine Region/Gemeinde/dein Bundesland"), damit das Blatt für jede Schule passt.


## Abbildungen (Schwerpunkt dieses Sets)
Setze die intent-deklarierten `data_figures` großzügig ein, wo sie eine Aufgabe TRAGEN — GWB
lebt von Diagrammen. Wähle den **intent** nach der Aussage der Daten (nicht „immer Balken"):
Bevölkerungsentwicklung → `trend` (Linie); Indikatoren wie BIP vs. Lebenserwartung →
`relationship` (Streu, gern mit `fit`); Einkommens-/Wert-Skalen → `scale` (Zahlenstrahl);
Häufigkeiten (z. B. Naturereignisse pro Jahr) → `distribution` (Histogramm); Sektoren-Anteile
→ `comparison`/`composition` (Balken).
**Wenn die ideale Geo-Abbildung NICHT in den erlaubten Recipes ist** (z. B. ein **Klimadiagramm**
= Temperatur-Linie + Niederschlags-Balken auf zwei Achsen, oder eine **Bevölkerungspyramide**):
**nicht faken und nicht in einen Balken zwängen**. Mach die ehrliche Annäherung mit den
erlaubten Mitteln (z. B. Temperatur als eigene `trend`-Linie UND Niederschlag als eigener
`comparison`-Balken; oder die Altersstruktur als liegende Balken) und schreibe in `watch_outs`
oder `teacher_note` einen Satz, welche Darstellung eigentlich ideal wäre. (Wir prüfen damit
gezielt, wo unser Diagramm-Vokabular noch Lücken hat.)
