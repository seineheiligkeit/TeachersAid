# Breiten-Generierung: Zweite lebende Fremdsprache — 2 Kernfragen

Du erzeugst **2 verschiedene** Arbeitsblatt-Inhalte (je eine eigene **Kernfrage**) für die
**AHS-Unterstufe** auf österreichischem Lehrplan-Niveau. Sprache: **Deutsch**, altersgerecht für die Unterstufe (Sek I, ~10-14 J.) — klar und konkret, aber nie trivial (der Blackboard-Test gilt trotzdem).
Wähle **2 klar unterschiedliche Themen/Bereiche** (Breite!), nicht Varianten desselben Themas.

## Korpus-Kontext — was es schon gibt
Für **Zweite lebende Fremdsprache** (Unterstufe) gibt es im Korpus schon **7** Arbeitsblätter. Wähle 2 **neue** Kernfragen, die sich davon klar unterscheiden (keine Dubletten, keine bloßen Varianten):
- [Kl 3] Boulangerie du Coin — À la boulangerie — verstehen und sprechen
- [Kl 3] Ma famille et mes loisirs — Über Familie und Hobbys schreiben — Kannst du auf Französisch über deine Familie und deine Hobbys schreiben?
- [Kl 3] Wer bist du? — Kurze Dialoge verstehen — Kannst du einfache Dialoge auf Französisch verstehen und die wichtigsten Infos herausfiltern?
- [Kl 4] Au café et en ville — Im Alltag auf Französisch kommunizieren — Kannst du dich in einfachen Alltagssituationen auf Französisch verständigen — im Café, in der Stadt, beim Einkaufen?
- [Kl 4] Horaire de bus - Ligne 5 — Les horaires de bus — verstehen und sprechen
- [Kl 4] Mon passé, mes rêves — Vergangenes und Zukünftiges schreiben — Kannst du auf Französisch über Dinge schreiben, die du erlebt hast, und über deine Pläne und Wünsche für die Zukunft?
- [Kl 4] Une lettre d'un ami — Eine E-Mail auf Französisch lesen — Kannst du einer kurzen Nachricht auf Französisch die wichtigsten Informationen entnehmen?

_Abdeckung (Kompetenzbereich-Zellen): 3 grün · 3 teilweise · 2 leer von 8._

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
create_produce, data_interpretation, decision_scenario, listening_task, matching, multiple_choice, open_response, ordering, puzzle, speaking_task, table_fill, text_production, true_false_justify
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
  - `matplotlib:histogram` — Histogramm für die VERTEILUNG (Form) der Rohdaten einer numerischen Größe — spec {"values":[num],"bins"?,"xlabel"?,"ylabel"?,"title"?}
  - `matplotlib:boxplot` — Boxplot/Kastenschaubild — Fünf-Punkte-Zusammenfassung (Streuung) bzw. Vergleich von Verteilungen (WS). spec {"summary":{"min","q1","median","q3","max"}} ODER {"values":[num]} ODER {"groups":[{"label","summary"|"values"}]} (z. B. Datenliste A vs. B); "xlabel"?,"title"?,"vertical"? (Standard waagrecht).
  - `matplotlib:vector_addition` — Vektor-/Kräfteaddition (Pfeile maßstabsgetreu; Vektoren aneinandergehängt oder Kräfteparallelogramm) — spec {"vectors":[{"magnitude":num,"angle_deg":num (0° = nach rechts, gegen den Uhrzeigersinn)} ODER {"dx":num,"dy":num}, je "label"?:str],"method"?:"tip_to_tail"|"parallelogram" (nur bei genau 2 Vektoren),"show_resultant"?:bool,"show_value"?:bool (false → "F_R = ?" als Aufgabe),"unit"?:str (Standard "N"),"resultant_name"?:str,"title"?}. Die Resultierende wird aus der Komponentensumme BERECHNET — die Abbildung erfindet nichts und verrät mit show_value:false keine Lösung.
  - `matplotlib:force_diagram` — Kräfteplan (Freikörperbild): Körper mit Kraftpfeilen vom Mittelpunkt aus, Längen maßstabsgetreu — spec {"forces":[{"magnitude":num,"angle_deg":num (0° = nach rechts, 90° = nach oben),"label"?:str (z. B. "F_G")}],"body_label"?:str,"show_magnitudes"?:bool,"show_resultant"?:bool,"show_value"?:bool (false → "F_res = ?"),"unit"?:str,"title"?}. Die resultierende Kraft wird BERECHNET (Komponentensumme; Kräftegleichgewicht → "F_res = 0 N").
  - `matplotlib:labeled_parts` — Beschriftungs-Abbildung ("Beschrifte die Teile"): schematischer Querschnitt/Aufbau aus einfachen Formen, Teile mit nummerierten Hinweislinien — spec {"shapes":[{"kind":"region"|"circle"|"polyline"|"line",…,"color"?:str}],"parts":[{"at":[x,y],"name":str,"side"?:"left"|"right"}],"show_names"?:bool (false → nummerierte Aufgabe zum Beschriften, true → beschriftete Lösung),"title"?}. Nummerierung, Hinweislinien und Lösungsnamen werden aus derselben Teile-Liste ABGELEITET — Schülerblatt und Lösung können nicht auseinanderlaufen. Die Formen sind schematisch (kein Datendiagramm).
  - `matplotlib:homology_schema` — Homologie-Schema (Wirbeltier-Vergleich, Biologie): schematische Seitenansichten von Tieren, bei denen das VORDERgliedmaßenpaar in EINER Farbe und das HINTERgliedmaßenpaar in einer ANDEREN markiert ist — dieselben zwei Farben bei jedem Tier, damit „gleicher Bauplan, verschiedene Werkzeuge" (homologe Gliedmaßen → gemeinsame Abstammung) auf einen Blick lesbar ist. spec {"title"?:str}; ohne Angabe die vier Standard-Wirbeltiere (Fisch, Frosch, Vogel, Hund). Die Gliedmaßen-Homologien sind KURIERTE Fakten (jedes Tier genau zwei Vorder- + zwei Hintergliedmaßen; unpaarige Flossen bleiben neutral grau) — keine erfundenen Zahlen, ein schematisches Bild statt eines Balkendiagramms.
  - `matplotlib:tree_diagram` — Baumdiagramm — mehrstufiger Zufallsversuch (WS). spec {"branches":[{"label","p"? (Astbeschriftung, z. B. "0,3"),"children"?:[{"label","p"?,"children"?…}]}],"title"?}. Astwahrscheinlichkeiten sind vorgegeben — die Abbildung erfindet keine Zahlen.
  - `matplotlib:function_graph` — Koordinatensystem/Gerade — spec {"xmin"?,"xmax"?,"m"?,"b"? (Gerade y=mx+b),"points"?:[[x,y]],"connect"? (Punkte zu einer Kurve verbinden, z. B. v-t-Diagramm),"xlabel"?,"ylabel"?,"ymin"?,"ymax"?,"title"?}
  - `matplotlib:math_formula` — Formel via LaTeX — spec {"latex":str}
  - `matplotlib:population_pyramid` — Bevölkerungspyramide (Alter × Geschlecht, gegenläufige Balken) — spec {"age_groups":[str],"male":[num],"female":[num],"title"?:str,"xlabel"?:str}. NUR mit echten, zitierten Daten verwenden (data_source auf einen Datensatz setzen).
  - `matplotlib:right_triangle` — Rechtwinkliges Dreieck (Pythagoras) — spec {"a":num,"b":num,"label_a"?,"label_b"?,"label_c"?,"title"?}. Beschriftungen sind Strings (z. B. "a = 3 cm", "c = ?") — die Abbildung darf die Lösung NICHT verraten.
  - `matplotlib:rectangle` — Rechteck mit Maßen — spec {"length":num,"width":num,"label_l"?,"label_w"?,"title"?}.
  - `matplotlib:polygon` — Vieleck (Dreieck/Viereck …) — spec {"points":[[x,y]],"vertex_labels"?:[str],"side_labels"?:[str],"title"?}.
  - `matplotlib:solid_net` — Körpernetz eines Quaders/Würfels — spec {"kind"?:"cuboid"|"cube","a"?:num,"b"?:num,"c"?:num | "side"?:num,"label_a"?:str,"label_b"?:str,"label_c"?:str,"result_label"?:str,"title"?:str}. Die sechs Flächen und fünf Faltkanten werden geometrisch BERECHNET; Beschriftungen sind vorgegeben (z. B. "a = 3 cm", "O = ?"), damit die Abbildung keine Lösung verrät.
  - `matplotlib:circle` — Kreis mit Radius — spec {"radius":num,"label_r"?,"title"?}.
  - `matplotlib:coordinate_plane` — Koordinatensystem mit Punkten/Strecken — spec {"points":[{"x":num,"y":num,"label"?}],"segments"?:[[i,j]],"xmin"?,"xmax"?,"ymin"?,"ymax"?,"title"?}.
  - `matplotlib:triangle_construction` — Dreieckskonstruktion (merkwürdige Punkte) — spec {"vertices":[[x,y],[x,y],[x,y]],"stage"?:1–6,"title"?}. stage 1 Dreieck · 2 Umkreis · 3 Inkreis · 4 Schwerpunkt · 5 Höhenschnittpunkt · 6 Eulergerade+Feuerbachkreis. Mittelpunkte, Kreise und Winkel werden aus den Eckpunkten BERECHNET — die Abbildung erfindet nichts.
  - `matplotlib:axonometric_solid` — Körper im Schrägriss (Kabinettprojektion, GZ/DG) — spec {"kind":"quader"|"prism"|"pyramid"|"cylinder"|"cone","a"?,"b"?,"c"? (Quader) | "n"?,"r"?,"h"? (Prisma/Pyramide/Zylinder/Kegel),"labels"?:{"a"|"b"|"c"|"r"|"h":str},"show_measures"?:bool (false → "h = ?" als Aufgabe),"title"?}. Verdeckte Kanten werden BERECHNET (strichliert), Maße sind maskierbar — die Abbildung erfindet keine verdeckte Kante und verrät kein Maß.
  - `matplotlib:riss_pair` — Grund- und Aufriss eines Körpers (zugeordnete Normalrisse, GZ/DG) — spec {"kind":… (wie axonometric_solid),Maße,"ordnungslinien"?:bool (Standard true),"title"?}. Grundriss unten, Aufriss oben, gemeinsame Rissachse und Ordnungslinien; beide Risse im selben Maßstab (die x-Zuordnung ist exakt), aus der Körpergeometrie berechnet.
  - `matplotlib:function_plot` — Funktionsgraph y = f(x) (BELIEBIGE Funktion via Term) — spec {"expr":str (z. B. "0.25*x**2-1" oder "sin(x)"),"xmin"?,"xmax"?,"ymin"?,"ymax"?,"label"?,"title"?}.
  - `matplotlib:integral_area` — Fläche unter der Kurve (bestimmtes Integral) — spec {"expr":str,"a":num,"b":num,"xmin"?,"xmax"?,"show_value"?:bool (false → "A = ?" als Aufgabe),"title"?}. Der Flächenwert wird aus dem Term BERECHNET (sympy), nicht erfunden.
  - `matplotlib:tangent` — Tangente an f in x0 (Ableitung als Steigung) — spec {"expr":str,"x0":num,"xmin"?,"xmax"?,"show_slope"?:bool (false → "k = ?"),"slope_triangle"?:bool,"title"?}. Die Steigung k = f'(x0) wird BERECHNET (sympy).
  - `matplotlib:riemann_sum` — Rechteck-Näherung des Integrals (Ober-/Untersumme) — spec {"expr":str,"a":num,"b":num,"n"?:int,"mode"?:"left"|"right"|"mid","title"?}. Summe UND exakter Wert berechnet.
  - `matplotlib:extrema` — Extremstellen (Hoch-/Tiefpunkt) mit waagrechten Tangenten — spec {"expr":str,"xmin"?,"xmax"?,"title"?}. Aus f'(x)=0 berechnet und mit f''(x) klassifiziert.
  - `matplotlib:area_between` — Fläche zwischen zwei Kurven — spec {"expr":str,"expr2":str,"a"?:num,"b"?:num (Standard: äußere Schnittpunkte),"show_value"?:bool,"title"?}. A = ∫|f−g| berechnet.
  - `matplotlib:distribution` — Normalverteilung N(μ,σ) mit schraffierter Wahrscheinlichkeit (WS) — spec {"mu"?:num,"sigma"?:num,"a"?:num,"b"?:num,"mode"?:"between"|"le"|"ge","show_value"?:bool,"title"?}. Fläche = Wahrscheinlichkeit, berechnet.
  - `matplotlib:optics_ray` — Bildkonstruktion an einer dünnen Linse (Physik) — spec {"kind":"sammellinse"|"zerstreuungslinse","f":num,"g":num,"G":num,"stage"?:1–6,"show_value"?:bool (false → NUR die gesuchten Bildgrößen maskiert: "b = ?","B = ?","B′ = ?" — die Angaben g/G bleiben sichtbar),"title"?}. f/g/G sind positive Beträge; das Bild (Bildweite b, Bildgröße B) wird aus der Abbildungsgleichung 1/f = 1/g + 1/b BERECHNET (sympy). stage 1 Achse+Linse+Gegenstand+Brennpunkte · 2 Parallelstrahl · 3 Mittelpunktstrahl · 4 Brennpunktstrahl · 5 Bildpfeil · 6 Maße.
  - `matplotlib:pinhole_camera` — Lochkamera-Strahlengang (Physik, geradlinige Lichtausbreitung) — spec {"G":num,"a":num,"b":num (positive Beträge: Gegenstandsgröße, Gegenstandsweite, Bildweite),"show_value"?:bool (false → nur die gesuchte Bildgröße "B = ?" maskiert),"title"?}. Gegenstand, Lochblende (ein Loch) und umgekehrtes Bild werden gezeichnet; die Strahlen KREUZEN im Loch, daher steht das Bild kopf (Konstruktion). Bildgröße B = G·b/a aus ähnlichen Dreiecken BERECHNET — keine Koordinatenachsen.
  - `matplotlib:shadow_cone` — Schattenraum/Kernschatten hinter einer Kugel bei PUNKTförmiger Lichtquelle (Physik) — spec {"source"?:[x,y],"center"?:[x,y],"r":num,"screen_x"?:num|null (Wand rechts; null = keine Wand),"show_screen"?:bool,"title"?}. Die zwei Tangentenstrahlen und der schraffierte Kernschatten werden GERECHNET (geschlossene Tangentenkonstruktion). Eine Punktquelle liefert genau eine Tangente je Seite → ein scharfer Schattenrand (kein Halbschatten) — keine Koordinatenachsen.
  - `matplotlib:circuit` — Stromkreis-Schaltbild aus einer Netzliste (Physik) — spec {"net":{Baum aus {"type":"series"|"parallel","children":[…]} und Blättern {"type":"resistor"|"lamp","ohm":num,"label":str}},"volt"?:num,"mask"?:[str] (maskiert GENAU diese Werte — Element-Labels bzw. "U"/"I"/"Rers", z. B. ["R₂","Rers"]; die Angaben bleiben sichtbar — die kanonische Aufgabe „gegeben U, R₁, R₃, I — berechne R₂"),"show_value"?:bool (false ohne mask → ALLES maskiert),"ask"?:str (Fokus, z. B. "R₂"/"U"/"I"),"title"?}. Ersatzwiderstand, Ströme und Spannungen werden nach Kirchhoff BERECHNET (sympy, exakt) — nichts erfunden.
  - `matplotlib:timeline` — Zeitleiste (chronologische Ereignisse, GPB) — spec {"events":[{"at":num,"label":str}],"title"?:str,"xlabel"?:str}.
  - `matplotlib:climate_diagram` — Klimadiagramm (Monats-Temperatur als Linie + Niederschlag als Balken, zwei Achsen) — spec {"months"?:[12 str],"temp":[12 num],"precip":[12 num],"title"?:str}. Echte Klimadaten zitieren (data_source), sonst illustrative=true.
  - `matplotlib:star_chart` — Sternkarte (der sichtbare Abendhimmel) — spec {"date"?:"JJJJ-MM-TT","time"?:"HH:MM","utc_offset"?:num (Std., Standard +1 = MEZ),"lat"?:num,"lon"?:num (Standard Wien),"mag_limit"?:num (Standard 4,5),"show_star_labels"?:bool,"show_constellation_labels"?:bool (beide standardmäßig MASKIERT — eine „Welches Sternbild ist das?"-Aufgabe verrät nichts),"highlight"?:str (Sternbild-Kürzel, hervorgehoben),"show_moon"?:bool,"title"?}. Sternpositionen sind FAKTEN aus dem kuratierten Katalog (grounding/astro); der sichtbare Himmel wird aus Datum/Zeit/Ort BERECHNET (Sternzeit → Horizontsystem → azimutale Projektion mit Horizontkreis N/O/S/W). Markergröße ← Helligkeit.
  - `matplotlib:moon_phase` — Mondphase (korrekt geformte Mondscheibe) — spec {"date"?:"JJJJ-MM-TT" (+utc_offset) → Phase BERECHNET, ODER "illuminated_fraction":num (0..1)+"waxing":bool direkt vorgegeben,"show_label"?:bool (false → „?" als Aufgabe),"phase_name"?:str,"title"?}. Zunehmender Mond ist RECHTS beleuchtet (Nordhalbkugel); der Terminator ist die exakte projizierte Halbellipse zum beleuchteten Anteil. Der beleuchtete Anteil wird aus dem Datum BERECHNET (Meeus, taggenau) — nichts erfunden.
  **Wichtig — eine Abbildung darf die gesuchte Lösung NICHT verraten:** z. B. KEINE Funktionsgleichung
  als Diagramm-`title`, wenn die Aufgabe ist, sie abzulesen; keine Werte/Beschriftungen anzeigen, die die
  Schüler:innen erst ablesen/bestimmen sollen. Die Abbildung zeigt das Material, nicht die Antwort.
  Keine freien Bilder/Diffusion, kein `data_interpretation`-Payload,
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
Schreibe **2 Dateien**, eine pro Kernfrage, nach `runs/ingest/gen_us_2/FS2_1.json` … `runs/ingest/gen_us_2/FS2_2.json`.
Jede Datei ist **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune):

```json
{
  "subject": "Zweite lebende Fremdsprache", "klasse": <1-4, eine Klasse mit Kompetenzen im gewählten Bereich>,
  "kompetenzbereich": "<KB-Name>",
  "title": "<prägnanter Titel>", "kernfrage": "<eine Schüler-Kernfrage in Du-Form>",
  "body": {
    "intro": [],
    "data_figures": [ /* bevorzugt für Daten: {"id":"abb1","intent":"trend","title":"...","xlabel":"Jahr","ylabel":"%","categories":["1990","2010","2024"],"values":[29,43,57]} */ ],
    "assets": [ /* nur Struktur-Figuren: {"id":"abb2","role":"figure","generator":"matplotlib:function_graph","spec":{"m":2,"b":1}} */ ],
    "sections": [ { "id":"s1","title":"...","throughline":"...","talking_points":["..."],"extensions":["..."],
      "blocks":[ {"role":"task","id":"t1","kind":"<kind>","prompt":"...","payload":null,
        "response":{"mode":"lines","n":3},"cognitive_level":"understand","dimensions":["HOR"],
        "serves":[{"competence_id":"<ID>","relation":"exercises"}],"est_minutes":7,"asset_refs":[],
        "answer_key":"...","acceptable_reasoning":null,"watch_outs":["..."],"rubric":[]} ] } ]
  }
}
```
