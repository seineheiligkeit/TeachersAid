# KAMPAGNEN-AUFTRAG: Chemie, Klasse 4 — 1 gezieltes Ergänzungsblatt

Die Stränge dieser Klasse sind schon TEILWEISE gefüllt; es fehlen exakt diese (Strang × Band)-Kombinationen:
- **(fachübergreifender Strang ohne Bereichsnamen)** — verankere hier an: `CHE.US.x.ALL.01`, `CHE.US.x.ALL.02`, `CHE.US.x.ALL.03` (bereits 8 Aufgaben): es fehlt AB II (mittel)

**Anforderungsbereiche (Bänder)** — abgeleitet aus `cognitive_level`:
- **AB I (leicht)** = `remember` | `understand`
- **AB II (mittel)** = `apply` | `analyze`
- **AB III (anspruchsvoll)** = `evaluate` | `create`

**Auftrag:** EIN kohärentes Blatt (ein Thema, das das natürlich hergibt) mit 5–7 Aufgaben, das **je fehlender Kombination oben ≥2 Aufgaben** liefert (Strang-Zuordnung über die `serves`-Kompetenz, Band über `cognitive_level`). Übrige Aufgaben frei.
Setze im JSON `"scope_label": "<Thema>"` und `"klasse": 4` (KEIN `"kompetenzbereich"`-Feld).

Sprache: **Deutsch**, AHS-Unterstufe Klasse 4 (altersgerecht, aber nicht zu niedrig).

## Qualitätslatte — der Tafel-Test (tragend)
Jedes Blatt muss MEHR Wert liefern als das, was eine Lehrkraft in einer Minute an die Tafel schreibt: echter Kontext statt nackter Drill-Reihe, ein roter Faden mit ansteigender Struktur, Aufgaben, die ohne das Blatt nicht stellbar wären (Abbildung, Datenbezug, Fallkontext, gestufte Teilschritte). Reine Rechen-/Abfragepäckchen ("Löse: a) … b) … c) …") ohne Rahmen werden am Gate abgelehnt.

## Fach-Hinweis
Der Tafel-Test gilt hier besonders (nackte Chemie-Drills wurden bereits abgelehnt): jeder Aufgabenblock braucht einen echten Kontextrahmen (Haushalt, Labor, Umwelt, Technik), eine gestufte Struktur und Teilschritte mit eigenem Denkwert.

## Kompetenzen (verbatim — `serves.competence_id` MUSS eine dieser IDs sein)

### (ohne Bereichsname)
- `CHE.US.x.ALL.01` (Kl 4) [dims —]: Vorgänge und Phänomene in Natur, Umwelt und Technik sowie deren Auswirkungen beobachten, erfassen, beschreiben und benennen.
- `CHE.US.x.ALL.02` (Kl 4) [dims —]: unterschiedlichen Medien und Quellen fachspezifische Informationen entnehmen.
- `CHE.US.x.ALL.03` (Kl 4) [dims —]: Vorgänge und Phänomene in Natur, Umwelt und Technik in verschiedenen Formen (Grafik, Tabelle, Bild, Diagramm, …) darstellen, erklären und adressatengerecht kommunizieren.

### Erkenntnisse gewinnen und interpretieren (E)
- `CHE.US.x.ERK.01` (Kl 4) [dims —]: zu Vorgängen und Phänomenen in Natur, Umwelt und Technik Beobachtungen machen oder Messungen durchführen und diese beschreiben.
- `CHE.US.x.ERK.02` (Kl 4) [dims —]: zu Vorgängen und Phänomenen in Natur, Umwelt und Technik Fragen stellen, Vermutungen aufstellen sowie passende Untersuchungen planen, durchführen und protokollieren.
- `CHE.US.x.ERK.03` (Kl 4) [dims —]: Beobachtungen, Daten und Ergebnisse von Untersuchungen analysieren (ordnen, vergleichen, Abhängigkeiten feststellen) und interpretieren.

### Standpunkte begründen, Entscheidungen treffen und reflektiert handeln (S)
- `CHE.US.x.STA.01` (Kl 4) [dims —]: Informationen aus verschiedenen Quellen aus naturwissenschaftlicher Sicht bewerten und Schlüsse daraus ziehen.
- `CHE.US.x.STA.02` (Kl 4) [dims —]: fachlich korrekt und folgerichtig argumentieren und naturwissenschaftliche von nicht-naturwissenschaftlichen Argumentationen und Fragestellungen unterscheiden.
- `CHE.US.x.STA.03` (Kl 4) [dims —]: Bedeutung, Chancen und Risiken der Anwendungen von naturwissenschaftlichen Erkenntnissen für sich persönlich und für die Gesellschaft erkennen, um verantwortungsbewusst zu handeln.
- `CHE.US.x.STA.04` (Kl 4) [dims —]: die Bedeutung von Naturwissenschaft und Technik für verschiedene Berufsfelder erfassen, um diese Kenntnis bei der Wahl ihres weiteren Bildungsweges zu verwenden.

## Erlaubte Dimensionen (`dimensions`, primäre zuerst)
- `W` — Wissen aneignen und kommunizieren
- `E` — Erkenntnisse gewinnen und interpretieren
- `S` — Standpunkte begründen, Entscheidungen treffen und reflektiert handeln

## Erlaubte Aufgaben-`kind`-Werte
create_produce, data_interpretation, decision_scenario, experiment_protocol, matching, multiple_choice, open_response, ordering, source_critique, table_fill, true_false_justify

## Anwendungsbereiche (Themen-Ideen)
- Aggregatzustände und Eigenschaften von Stoffen · Aufbau von Atomen und Periodensystem · Bindungsmodelle, Strukturen und Wechselwirkungen · Symbolische und grafische Darstellungen auf Teilchenebene · Kennzeichen chemischer Reaktionen: stoffliche und energetische Veränderungen · Darstellung chemischer Reaktionen: Wort- und Formelgleichungen, modellhafte Darstellungen · Typen chemischer Reaktionen: Säure-Base-Reaktionen, Reduktions-Oxidations-Reaktionen, einfache organische Reaktionen · Planen, Durchführen, Beobachten, Erfassen, Auswerten und Dokumentieren von Untersuchungen: ua. Trennverfahren, einfache Nachweise, Synthesen und Analysen · Verhalten und Sicherheit im Umgang mit Chemikalien im chemischen Labor sowie im Alltag · Bedeutung der Chemie für Alltag, Wirtschaft, Gesundheit und Umwelt sowie die damit verbundene Verantwortung für eine nachhaltige Zukunft

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
Schreibe **1 Dateien**: `runs/ingest/campaign_mint_us/CHE_kl4_1.json` … `runs/ingest/campaign_mint_us/CHE_kl4_1.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Chemie", "klasse": 4,
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
