# KAMPAGNEN-AUFTRAG: Biologie und Umweltbildung, Klasse 3 — 3 thematisch verschiedene Arbeitsblätter

Die Kompetenzbereiche dieses Fachs sind **Prozess-Stränge** — ein echtes Thema bedient mehrere zugleich:
- **Erkenntnisse gewinnen (E)**
- **Standpunkte begründen und reflektiert handeln (S)**
- **Wissen aneignen, anwenden und kommunizieren (W)**

**Anforderungsbereiche (Bänder)** — abgeleitet aus `cognitive_level`:
- **AB I (leicht)** = `remember` | `understand`
- **AB II (mittel)** = `apply` | `analyze`
- **AB III (anspruchsvoll)** = `evaluate` | `create`

**Grün-Kriterium (über das ganze Set von 3 Blättern gerechnet, JE STRANG):** ≥5 Aufgaben pro Strang UND alle drei Bänder pro Strang vertreten.
Praktisch heißt das: **jedes Blatt enthält Aufgaben aus allen drei Strängen** — bei echten Themen natürlich: beschreiben/erklären (W), beobachten/untersuchen/auswerten (E), bewerten/Stellung nehmen (S) — und du verteilst die Bänder bewusst so, dass am Ende jeder Strang die volle Leiter hat. Die Strang-Zuordnung einer Aufgabe entsteht über die `serves`-Kompetenz (siehe deren KB unten).
Setze im JSON `"scope_label": "<Thema>"` und `"klasse": 3` (KEIN `"kompetenzbereich"`-Feld). Wähle klar unterschiedliche Themen (Breite!).

Sprache: **Deutsch**, AHS-Unterstufe Klasse 3 (altersgerecht, aber nicht zu niedrig).

## Qualitätslatte — der Tafel-Test (tragend)
Jedes Blatt muss MEHR Wert liefern als das, was eine Lehrkraft in einer Minute an die Tafel schreibt: echter Kontext statt nackter Drill-Reihe, ein roter Faden mit ansteigender Struktur, Aufgaben, die ohne das Blatt nicht stellbar wären (Abbildung, Datenbezug, Fallkontext, gestufte Teilschritte). Reine Rechen-/Abfragepäckchen ("Löse: a) … b) … c) …") ohne Rahmen werden am Gate abgelehnt.

## Fach-Hinweis
Echte biologische Kontexte (Organismus, Lebensraum, Körper, Ökosystem) mit Beobachtungs-/Auswertungsaufgaben; wo Daten helfen, eine `data_figures`-Abbildung (intent-deklariert). Keine reinen Benenn-Listen.

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein)

### Erkenntnisse gewinnen (E)
- `BIO.US.x.ERK.01` (Kl 3) [dims —]: Lebewesen und biologische Phänomene betrachten, beobachten, bestimmen, kriteriengeleitet vergleichen und ordnen, mikroskopieren, zeichnen und messen.
- `BIO.US.x.ERK.02` (Kl 3) [dims —]: zu biologischen Vorgängen und Phänomenen naturwissenschaftliche Fragen stellen sowie Hypothesen entwickeln und formulieren.
- `BIO.US.x.ERK.03` (Kl 3) [dims —]: Beobachtungen, Versuche, Untersuchungen und Experimente zu naturwissenschaftlichen Fragestellungen planen, durchführen und protokollieren.
- `BIO.US.x.ERK.04` (Kl 3) [dims —]: Daten und Ergebnisse von Untersuchungen, Beobachtungen und Experimenten darstellen, analysieren und interpretieren.

### Standpunkte begründen und reflektiert handeln (S)
- `BIO.US.x.STA.01` (Kl 3) [dims —]: naturwissenschaftliche von nicht naturwissenschaftlichen Argumentationen unterscheiden, fachlich korrekt und folgerichtig argumentieren.
- `BIO.US.x.STA.02` (Kl 3) [dims —]: Fragestellungen im Bereich Bioethik, Sexualität, Gesundheit, Umweltschutz und Nachhaltigkeit unter Einbeziehung kontroverser Gesichtspunkte erörtern und den eigenen Standpunkt fachlich fundiert begründen.
- `BIO.US.x.STA.03` (Kl 3) [dims —]: Handlungsempfehlungen fachlich fundiert erstellen und begründen, verantwortungsbewusst und individuell sowie gesellschaftlich nachhaltig handeln.

### Wissen aneignen, anwenden und kommunizieren (W)
- `BIO.US.x.WIS.01` (Kl 3) [dims —]: Lebewesen, Lebensräume, biologische Phänomene und Prinzipien benennen, beschreiben, erläutern und in Beziehung setzen.
- `BIO.US.x.WIS.02` (Kl 3) [dims —]: Informationen aus unterschiedlichen Medien und Quellen fachbezogen erschließen, zusammenfassen, vergleichen und in verschiedenen Formen (Grafik, Foto, Video, Tabelle, Diagramm, ...) adressaten- und situationsgerecht darstellen und kommunizieren.
- `BIO.US.x.WIS.03` (Kl 3) [dims —]: Modelle zur Beschreibung und Erklärung biologischer Sachverhalte/Vorgänge/Beziehungen verwenden, erstellen und deren Gültigkeitsbereiche und Grenzen diskutieren.

## Erlaubte Dimensionen (`dimensions`, primäre zuerst)
- `W` — Wissen aneignen, anwenden und kommunizieren
- `E` — Erkenntnisse gewinnen
- `S` — Standpunkte begründen und reflektiert handeln

## Erlaubte Aufgaben-`kind`-Werte
cause_effect_match, concept_match, content_comprehension, create_produce, data_interpretation, decision_scenario, experiment_protocol, matching, multiple_choice, open_response, ordering, source_critique, structure_overview, table_fill, true_false_justify

## Anwendungsbereiche (Themen-Ideen)
- Ökologische Zusammenhänge, Biodiversität und anthropogene Einflüsse in Süßwasser-Lebensräumen und im Meer · Vielfalt und Angepasstheit im Wasser lebender Tiere in Körperstruktur und Verhalten, wassergebundene Fortpflanzung und Entwicklung von Lebewesen · Tracheen, Kiemen und Lungen als Atmungsorgane, Bedeutung des Sauerstoffs bei der Nutzung von Nährstoffen als Energieträger · Herz-Kreislauf-System, Zusammensetzung und Funktionen des Blutes · Zusammenwirken des Atmungssystems mit dem Blutkreislaufsystem, Ausscheidungssystem und gesundheitsbezogenes Handeln · Gesteinskreislauf und Plattentektonik, Zusammenhänge zwischen Geologie und Lebensräumen · Funktion von Mikroorganismen im Boden, Bedeutung des Bodens für die Pflanzen, anthropogene Einflüsse auf den Boden · Entstehung von Fossilien und Geschichte des Lebens auf der Erde · Darstellung von Verwandtschaftsverhältnissen in Kladogrammen

## Regeln (für jedes Blatt)
- 5–7 Aufgaben (`blocks` mit role "task") + optional 1 kurzer Info-Block. Realistische `est_minutes`.
- Verankere **jede** Aufgabe via `serves` an einer der oben gelisteten IDs; nutze mehrere verschiedene.
- `dimensions` ⊆ erlaubte Codes; `kind` ∈ erlaubte kinds; die kognitive Leiter steigt
  (remember→…→create), nicht alles „remember".
- **Korrektheit by construction**; Fehlvorstellungen/Hinweise in `watch_outs` (tragend).
- **Abbildungen — Code-generiert, korrekt by construction** (nie freie Bilder/Diffusion): wo eine
  Abbildung die Aufgabe wirklich verbessert, fordere eine an und referenziere sie über `asset_refs`.
  Reiner Text bleibt ok, wenn keine Abbildung nötig ist.
  **Für DATEN: deklariere die ABSICHT, nicht den Diagrammtyp** — lege die Figur in `body.data_figures`;
  das System wählt die passende, lesbare Darstellung (so wird nicht alles ein Balkendiagramm).
  Form: `{"id":str,"intent":str,"title"?,"xlabel"?,"ylabel"?,"categories"?:[str],"values"?:[num],"points"?:[[x,y]],"log"?:bool,"fit"?:bool,"data_source"?:{"dataset_id":str,"series":str}}`
  mit `intent` ∈
    - `trend` — Verlauf/Entwicklung (oft über die Zeit): `categories`+`values` → Liniendiagramm
    - `comparison` — MENGEN-Vergleich zwischen Kategorien: `categories`+`values` → Balkendiagramm
    - `relationship` — Zusammenhang zweier numerischer Größen: `points` (+`fit`) → Streudiagramm
    - `distribution` — Häufigkeit/Streuung einer Größe: `values` → Histogramm
    - `spread` — Fünf-Punkte-Zusammenfassung / Verteilungen vergleichen: `values` → Boxplot
    - `scale` — Position auf einer Skala (z. B. pH-Wert): `categories`+`values` → Zahlenstrahl
    - `demographic` — Alter × Geschlecht: `categories`+`male`+`female` → Bevölkerungspyramide
  **Wähle nie selbst „Balken" für eine Zeitreihe, eine Ja/Nein-Klassifikation oder eine Skala** —
  dafür ist der `intent` da; korrekte Zahlen allein genügen NICHT, die Darstellung muss zur Aussage passen.
  **Für STRUKTUR-Abbildungen** (Geometrie, Funktionsgraph, Formel, Zahlenstrahl, Baumdiagramm) nutze
  `body.assets` mit explizitem Generator — **erlaubte Generatoren (nur diese):**
  - `matplotlib:number_line` — Zahlenstrahl — spec {"min":num,"max":num,"step"?:num,"marks"?:[{"at":num,"label"?:str}]}
  - `matplotlib:bar_chart` — Balkendiagramm für einen MENGEN-Vergleich (nicht für eine Ja/Nein-Klassifikation!) — spec {"categories":[str],"values":[num],"title"?:str,"xlabel"?:str,"ylabel"?:str,"log"?:bool}. Kurze Kategorienamen; bei Werten über mehrere Größenordnungen "log":true setzen.
  - `matplotlib:line` — Liniendiagramm für einen TREND / Verlauf über die Zeit — spec {"categories":[str]|"x":[num],"values":[num] | "series":[{"label"?,"x":[...],"y":[...]}],"xlabel"?,"ylabel"?,"title"?,"log"?}
  - `matplotlib:scatter` — Streudiagramm für einen ZUSAMMENHANG zweier numerischer Größen — spec {"points":[[x,y]],"xlabel"?,"ylabel"?,"title"?,"fit"? (Trendgerade)}
  - `matplotlib:histogram` — Histogramm für die VERTEILUNG (Form) der Rohdaten einer numerischen Größe — spec {"values":[num],"bins"?,"xlabel"?,"ylabel"?,"title"?}
  - `matplotlib:boxplot` — Boxplot/Kastenschaubild — Fünf-Punkte-Zusammenfassung (Streuung) bzw. Vergleich von Verteilungen (WS). spec {"summary":{"min","q1","median","q3","max"}} ODER {"values":[num]} ODER {"groups":[{"label","summary"|"values"}]} (z. B. Datenliste A vs. B); "xlabel"?,"title"?,"vertical"? (Standard waagrecht).
  - `matplotlib:tree_diagram` — Baumdiagramm — mehrstufiger Zufallsversuch (WS). spec {"branches":[{"label","p"? (Astbeschriftung, z. B. "0,3"),"children"?:[{"label","p"?,"children"?…}]}],"title"?}. Astwahrscheinlichkeiten sind vorgegeben — die Abbildung erfindet keine Zahlen.
  - `matplotlib:function_graph` — Koordinatensystem/Gerade — spec {"xmin"?,"xmax"?,"m"?,"b"? (Gerade y=mx+b),"points"?:[[x,y]],"connect"? (Punkte zu einer Kurve verbinden, z. B. v-t-Diagramm),"xlabel"?,"ylabel"?,"ymin"?,"ymax"?,"title"?}
  - `matplotlib:math_formula` — Formel via LaTeX — spec {"latex":str}
  - `matplotlib:population_pyramid` — Bevölkerungspyramide (Alter × Geschlecht, gegenläufige Balken) — spec {"age_groups":[str],"male":[num],"female":[num],"title"?:str,"xlabel"?:str}. NUR mit echten, zitierten Daten verwenden (data_source auf einen Datensatz setzen).
  - `matplotlib:right_triangle` — Rechtwinkliges Dreieck (Pythagoras) — spec {"a":num,"b":num,"label_a"?,"label_b"?,"label_c"?,"title"?}. Beschriftungen sind Strings (z. B. "a = 3 cm", "c = ?") — die Abbildung darf die Lösung NICHT verraten.
  - `matplotlib:rectangle` — Rechteck mit Maßen — spec {"length":num,"width":num,"label_l"?,"label_w"?,"title"?}.
  - `matplotlib:polygon` — Vieleck (Dreieck/Viereck …) — spec {"points":[[x,y]],"vertex_labels"?:[str],"side_labels"?:[str],"title"?}.
  - `matplotlib:circle` — Kreis mit Radius — spec {"radius":num,"label_r"?,"title"?}.
  - `matplotlib:coordinate_plane` — Koordinatensystem mit Punkten/Strecken — spec {"points":[{"x":num,"y":num,"label"?}],"segments"?:[[i,j]],"xmin"?,"xmax"?,"ymin"?,"ymax"?,"title"?}.
  - `matplotlib:triangle_construction` — Dreieckskonstruktion (merkwürdige Punkte) — spec {"vertices":[[x,y],[x,y],[x,y]],"stage"?:1–6,"title"?}. stage 1 Dreieck · 2 Umkreis · 3 Inkreis · 4 Schwerpunkt · 5 Höhenschnittpunkt · 6 Eulergerade+Feuerbachkreis. Mittelpunkte, Kreise und Winkel werden aus den Eckpunkten BERECHNET — die Abbildung erfindet nichts.
  - `matplotlib:function_plot` — Funktionsgraph y = f(x) (BELIEBIGE Funktion via Term) — spec {"expr":str (z. B. "0.25*x**2-1" oder "sin(x)"),"xmin"?,"xmax"?,"ymin"?,"ymax"?,"label"?,"title"?}.
  - `matplotlib:integral_area` — Fläche unter der Kurve (bestimmtes Integral) — spec {"expr":str,"a":num,"b":num,"xmin"?,"xmax"?,"show_value"?:bool (false → "A = ?" als Aufgabe),"title"?}. Der Flächenwert wird aus dem Term BERECHNET (sympy), nicht erfunden.
  - `matplotlib:tangent` — Tangente an f in x0 (Ableitung als Steigung) — spec {"expr":str,"x0":num,"xmin"?,"xmax"?,"show_slope"?:bool (false → "k = ?"),"slope_triangle"?:bool,"title"?}. Die Steigung k = f'(x0) wird BERECHNET (sympy).
  - `matplotlib:riemann_sum` — Rechteck-Näherung des Integrals (Ober-/Untersumme) — spec {"expr":str,"a":num,"b":num,"n"?:int,"mode"?:"left"|"right"|"mid","title"?}. Summe UND exakter Wert berechnet.
  - `matplotlib:extrema` — Extremstellen (Hoch-/Tiefpunkt) mit waagrechten Tangenten — spec {"expr":str,"xmin"?,"xmax"?,"title"?}. Aus f'(x)=0 berechnet und mit f''(x) klassifiziert.
  - `matplotlib:area_between` — Fläche zwischen zwei Kurven — spec {"expr":str,"expr2":str,"a"?:num,"b"?:num (Standard: äußere Schnittpunkte),"show_value"?:bool,"title"?}. A = ∫|f−g| berechnet.
  - `matplotlib:distribution` — Normalverteilung N(μ,σ) mit schraffierter Wahrscheinlichkeit (WS) — spec {"mu"?:num,"sigma"?:num,"a"?:num,"b"?:num,"mode"?:"between"|"le"|"ge","show_value"?:bool,"title"?}. Fläche = Wahrscheinlichkeit, berechnet.
  - `matplotlib:timeline` — Zeitleiste (chronologische Ereignisse, GPB) — spec {"events":[{"at":num,"label":str}],"title"?:str,"xlabel"?:str}.
  - `matplotlib:climate_diagram` — Klimadiagramm (Monats-Temperatur als Linie + Niederschlag als Balken, zwei Achsen) — spec {"months"?:[12 str],"temp":[12 num],"precip":[12 num],"title"?:str}. Echte Klimadaten zitieren (data_source), sonst illustrative=true.
  **Wichtig — eine Abbildung darf die gesuchte Lösung NICHT verraten:** keine Werte/Beschriftungen
  anzeigen, die die Schüler:innen erst bestimmen sollen (Maskierung nutzen, z. B. "c = ?").
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
Schreibe **3 Dateien**: `runs/ingest/campaign_mint_us/BIO_kl3_1.json` … `runs/ingest/campaign_mint_us/BIO_kl3_3.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Biologie und Umweltbildung", "klasse": 3,
  "scope_label": "<Thema>",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {
    "intro": [],
    "data_figures": [],
    "assets": [],
    "sections": [ { "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{"mode":"lines","n":3},"cognitive_level":"understand","dimensions":["W"],
        "serves":[{"competence_id":"<ID>","relation":"exercises"}],"est_minutes":7,"asset_refs":[],
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]} ] } ]
  }
}
```
