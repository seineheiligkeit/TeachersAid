# KAMPAGNEN-AUFTRAG: Mathematik, Klasse 1 — 3 Arbeitsblätter, EXAKT eines je Kompetenzbereich

Dieses Set schließt gezielt Korpus-Lücken. Die Blätter:
1. Blatt 1: KB **"1: Zahlen und Maße"** — noch leer: volle Bandbreite nötig
2. Blatt 2: KB **"2: Variablen und Funktionen"** — noch leer: volle Bandbreite nötig
3. Blatt 3: KB **"3: Figuren und Körper"** — noch leer: volle Bandbreite nötig

**Anforderungsbereiche (Bänder)** — abgeleitet aus `cognitive_level`:
- **AB I (leicht)** = `remember` | `understand`
- **AB II (mittel)** = `apply` | `analyze`
- **AB III (anspruchsvoll)** = `evaluate` | `create`

**Grün-Kriterium je Blatt:** mindestens **5 Aufgaben**, alle via `serves` an Kompetenzen DIESES KBs (dieser Klasse) verankert, und (sofern oben nicht anders fokussiert) alle drei Bänder vertreten: ≥1× AB I, ≥2× AB II, ≥1× AB III.
Setze im JSON `"kompetenzbereich"` exakt auf den KB-Namen des Blatts und `"klasse": 1`. Wähle je Blatt eine eigene, kreative Kernfrage (kein KB-Namens-Echo).

Sprache: **Deutsch**, AHS-Unterstufe Klasse 1 (altersgerecht, aber nicht zu niedrig).

## Qualitätslatte — der Tafel-Test (tragend)
Jedes Blatt muss MEHR Wert liefern als das, was eine Lehrkraft in einer Minute an die Tafel schreibt: echter Kontext statt nackter Drill-Reihe, ein roter Faden mit ansteigender Struktur, Aufgaben, die ohne das Blatt nicht stellbar wären (Abbildung, Datenbezug, Fallkontext, gestufte Teilschritte). Reine Rechen-/Abfragepäckchen ("Löse: a) … b) … c) …") ohne Rahmen werden am Gate abgelehnt.

## Fach-Hinweis
Nutze Abbildungen aktiv: für *Figuren und Körper* die Geometrie-Recipes (`right_triangle`, `rectangle`, `polygon`, `circle`, `coordinate_plane`, ab der 3. Kl. auch `triangle_construction`), für *Zahlen und Maße* den `number_line`, für *Variablen und Funktionen* `function_graph`. Beschriftungen so wählen, dass die Abbildung die Lösung NICHT verrät (Maskierung: "c = ?", "A = ?").

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein)

### 1: Zahlen und Maße
- `MAT.US.1.ZAH.01` (Kl 1) [dims —]: natürliche Zahlen sowie nichtnegative Dezimal- und Bruchzahlen interpretieren, darstellen und vergleichen,
- `MAT.US.1.ZAH.02` (Kl 1) [dims —]: Rechenoperationen mit natürlichen Zahlen und mit nichtnegativen Dezimalzahlen durchführen und deuten; Überschlagsrechnungen durchführen,
- `MAT.US.1.ZAH.03` (Kl 1) [dims —]: Größen ein- und mehrnamig anschreiben, Maßangaben interpretieren und Umrechnungen durchführen.

### 2: Variablen und Funktionen
- `MAT.US.1.VAR.01` (Kl 1) [dims —]: einfache Terme, Gleichungen und Formeln aufstellen und interpretieren,
- `MAT.US.1.VAR.02` (Kl 1) [dims —]: Lösungen einfacher Gleichungen finden.

### 3: Figuren und Körper
- `MAT.US.1.FIG.01` (Kl 1) [dims —]: mit einfachen geometrischen Objekten in der Ebene arbeiten,
- `MAT.US.1.FIG.02` (Kl 1) [dims —]: Eigenschaften von Rechtecken beschreiben; Rechtecke und Figuren, die aus Rechtecken bestehen, konstruieren und maßstäblich darstellen; Formeln für den Umfang und den Flächeninhalt von Rechtecken begründen und anwenden,
- `MAT.US.1.FIG.03` (Kl 1) [dims —]: Eigenschaften von Quadern beschreiben; Formeln für den Oberflächeninhalt und Rauminhalt von Quadern begründen und anwenden.

## Erlaubte Dimensionen (`dimensions`, primäre zuerst)
- `MOD` — Modellieren und Problemlösen
- `OPE` — Operieren (Rechnen und Konstruieren)
- `DAR` — Darstellen und Interpretieren
- `BEG` — Vermuten und Begründen

## Erlaubte Aufgaben-`kind`-Werte
calculation, construction, create_produce, data_interpretation, decision_scenario, matching, modelling_task, multiple_choice, open_response, ordering, table_fill, true_false_justify

## Anwendungsbereiche (Themen-Ideen)
- grafisches Darstellen von Zahlen als Punkte am Zahlenstrahl und Ablesen von Zahlen; Lesen großer Zahlen · Verstehen und Anwenden des dezimalen Stellenwertsystems, dh. des Prinzips „Bündeln in Zehner-Schritten“ · Deuten von Brüchen als Anteile eines Ganzen bzw. als Anteile von mehreren Ganzen; Ergänzen von Brüchen auf Ganze · Erweitern und Kürzen von Brüchen, insbesondere mit Hilfe von Visualisierungen · Deuten von Brüchen als Quotienten · Wechseln zwischen Bruch- und Dezimaldarstellung in einfachen Fällen (zB ; ; ) · Vergleichen und Ordnen natürlicher Zahlen sowie nichtnegativer Dezimal- und Bruchzahlen · Lesen und allenfalls Schreiben römischer Zahldarstellungen; Erkennen der Vorteile des dezimalen Stellenwertsystems im Vergleich zur römischen Zahldarstellung · schriftliches Durchführen der vier Grundrechenoperationen mit natürlichen Zahlen und nichtnegativen Dezimalzahlen, in einfachen Fällen auch im Kopf · Beschreiben der Algorithmen für die Grundrechenoperationen anhand konkreter Beispiele; allenfalls Begründen der Algorithmen anhand konkreter Beispiele mit Hilfe von Rechenregeln und Eigenschaften des dezimalen Stellenwertsystems

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

## Verfügbare echte Datensätze (für `data_source` — echte, zitierte Zahlen)
Zeigt eine Abbildung echte Zahlen, **erfinde sie nicht**: setze auf der Figur `"data_source": {"dataset_id":"<id>","series":"<serie>"}`. Das System übernimmt dann die echten Werte aus dem Datensatz und zeigt die Quelle an. Wähle Kernfragen/Aufgaben ruhig danach, welche dieser Daten gut passen:
- `statistik_austria_bevstand_2024` — Bevölkerung Österreichs nach Alter und Geschlecht (1.1.2024). Serien: `pyramide_5j` (Bevölkerung nach 5-Jahres-Altersgruppen und Geschlecht) · `altersgruppen_breit` (Bevölkerung nach breiten Altersgruppen). Datenquelle: Statistik Austria – data.statistik.gv.at (CC BY 4.0)
- `statistik_austria_bundeslaender_2024` — Bevölkerung der österreichischen Bundesländer (1.1.2024). Serien: `bevoelkerung` (Bevölkerung je Bundesland). Datenquelle: Statistik Austria – data.statistik.gv.at (CC BY 4.0)
- `worldbank_at_alterung` — Anteil der über 65-Jährigen in Österreich. Serien: `verlauf` (Anteil der über 65-Jährigen in Österreich). Datenquelle: World Bank – data.worldbank.org (SP.POP.65UP.TO.ZS, CC BY 4.0)
- `worldbank_at_bevoelkerung` — Bevölkerung Österreichs im Zeitverlauf. Serien: `verlauf` (Bevölkerung Österreichs im Zeitverlauf). Datenquelle: World Bank – data.worldbank.org (SP.POP.TOTL, CC BY 4.0)
- `worldbank_bip_pro_kopf` — BIP pro Kopf im Ländervergleich. Serien: `vergleich` (BIP pro Kopf im Ländervergleich). Datenquelle: World Bank – data.worldbank.org (NY.GDP.PCAP.CD, CC BY 4.0)
- `worldbank_co2_pro_kopf` — CO₂-Ausstoß pro Kopf im Ländervergleich. Serien: `vergleich` (CO₂-Ausstoß pro Kopf im Ländervergleich). Datenquelle: World Bank – data.worldbank.org (EN.GHG.CO2.PC.CE.AR5, CC BY 4.0)
- `worldbank_urbanisierung` — Verstädterung im Ländervergleich (Anteil Stadtbevölkerung). Serien: `vergleich` (Verstädterung im Ländervergleich (Anteil Stadtbevölkerung)). Datenquelle: World Bank – data.worldbank.org (SP.URB.TOTL.IN.ZS, CC BY 4.0)
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
Schreibe **3 Dateien**: `runs/ingest/campaign_mint_us/MAT_kl1_1.json` … `runs/ingest/campaign_mint_us/MAT_kl1_3.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Mathematik", "klasse": 1,
  "kompetenzbereich": "<exakter KB-Name dieses Blatts>",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {
    "intro": [],
    "data_figures": [],
    "assets": [],
    "sections": [ { "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{"mode":"lines","n":3},"cognitive_level":"understand","dimensions":["MOD"],
        "serves":[{"competence_id":"<ID>","relation":"exercises"}],"est_minutes":7,"asset_refs":[],
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]} ] } ]
  }
}
```
