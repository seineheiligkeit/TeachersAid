# Difficulty-Label-Vorschläge (C4 → lernbares Modell)

*Version 1 · erzeugt 2026-07-12 · 1055 Aufgabenblöcke im Korpus · Modell-Schwellen [1.7, 3.069]*

## Arbeitsablauf (SME)

1. Diese Tabelle durchsehen; die maschinenlesbare Fassung ist `difficulty_proposals.json` (identische Reihenfolge).
2. Pro Vorschlag in der JSON `accepted` setzen: `true` übernimmt `proposed_difficulty`, `false` verwirft; bei Bedarf `proposed_difficulty` vorher editieren.
3. `python tools/apply_difficulty.py runs/difficulty/difficulty_proposals.json` schreibt NUR die akzeptierten Labels in den Blockstore (Review-Status bleibt erhalten).
4. `python tools/fit_difficulty.py` neu ausführen — mit authored Labels, die vom kognitiven Fallback abweichen, wird das Modell erstmals echt evaluierbar.

Bis dahin ist nichts geschrieben: `difficulty` bleibt im Korpus überall `null`. Ein Vorschlag darf mit dem Fallback ÜBEREINSTIMMEN — eine bewusste Bestätigung ist ebenfalls Information; Divergenz wird nicht künstlich erzeugt.

## Überblick

- **Cues** (48): berechnete Einstufung weicht ≥1 Band vom operativen Band ab (die C4-Review-Cues). Davon 43 mit Vorschlag ≠ Fallback (25 niedriger, 18 höher), 5 bestätigen den Anchor trotz Modell-Flag (bewusste Fehlalarm-Einschätzung).
- **Sample** (90): Nicht-Cue-Blöcke mit dem größten intrinsischen Nudge, gestreut über Fächer/Aufgabentypen/Bänder. Hier ist die berechnete Einstufung stets gleich dem Anchor — beide Signale bestätigen einander.
- **Gesamt**: 138 Vorschläge.

Bandskala: 1 = leicht (Reproduktion) · 2 = mittel (Transfer) · 3 = anspruchsvoll (Reflexion). Spalte **Eff→Ber** = operatives Band (kognitiver Fallback) → berechnetes Band; **Vorschlag** = vorgeschlagenes authored Label.

## Cues

#### Bewegung und Sport (2)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0005.t5` | 2 | evaluate | ordering | 3→2 | **2** | Bringe die folgenden Reaktionen auf eine Schiedsrichter:innen-Fehlentscheidung in eine Re… | Fairness-Reihung mit kurzer Begründung: das Werturteil ist in ein geschlossenes Reihungsformat gefasst und eng geführt — eher Transfer (Band 2) als offene Reflexion (Band 3). Grenzfall. |
| `c0009.t4` | 4 | evaluate | training_log | 3→2 | **2** | Führe für 5 Schultage ein Mini-Bewegungstagebuch: Notiere täglich in 2–3 Stichwörtern, wi… | Bewegungstagebuch über fünf Tage: überwiegend Protokollieren mit knapper Schlussreflexion; der reale Anspruch liegt bei Transfer (Band 2), nicht bei offener Reflexion (Band 3). |

#### Biologie und Umweltbildung (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0170.t2` | 1 | apply | cause_effect_match | 2→1 | **1** | Ordne jeder Ursache die passende Folge im Teich zu. | Ursache-Folge-Paare im Teich zuordnen: geschlossene Zuordnung vorgegebener Elemente in der 1. Klasse — reproduktionsnah (Band 1) statt Transfer (Band 2). |
| `c0172.t4` | 1 | apply | matching | 2→1 | **1** | Ordne jedem Körpermerkmal den passenden Vorteil im jeweiligen Lebensraum zu. | Körpermerkmal→Vorteil zuordnen: geschlossenes Wiedererkennen erlernter Paare, geringe Textlast — Band 1 statt Band 2. |
| `c0196.t4` | 1 | apply | ordering | 2→1 | **1** | Bringe die Schritte vom Bienenbesuch bis zur fertigen Frucht in die richtige Reihenfolge. | Bekannte Abfolge (Bienenbesuch→Frucht) reihen: Abruf einer gelernten Reihenfolge — Reproduktion (Band 1). |

#### Chemie (1)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0195.t3` | 4 | analyze | data_interpretation | 2→3 | **3** | Ein Trinkwasser-Notfallteam testet nach einem Unwetter drei mögliche Reinigungsverfahren … | Drei Reinigungsverfahren anhand quantitativer Angaben vergleichen und begründet auswählen: offene Datenauswertung mit hoher Textlast — anspruchsvoll (Band 3), über der Einstufung als Transfer (Band 2). |

#### Deutsch (2)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0010.t1` | 3 | understand | text_analysis | 1→2 | **2** | Lies den folgenden Textabschnitt aufmerksam durch. --- *Kaffee gehört zu den meistgehande… | Sachtext lesen und analysieren in freier Schriftform: die offene Textanalyse mit hoher Textlast liegt über bloßem Verstehen — Transfer (Band 2). |
| `c0011.t4` | 2 | evaluate | multiple_choice | 3→2 | **2** | Welche der folgenden Aussagen ist ein **echtes Argument** für die These „Schüler:innen so… | Aus vorgegebenen Aussagen das 'echte Argument' auswählen: geschlossenes Erkennen eines Kriteriums — Transfer (Band 2), nicht offene Reflexion (Band 3). |

#### Erste lebende Fremdsprache (1)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0050.t4` | 2 | apply | matching | 2→1 | **1** | Your teacher reads five short sentences aloud. Match each sentence (1–5) to the correct s… | Gehörte Sätze Situationen zuordnen: rezeptives Wiedererkennen im geschlossenen Format, sehr geringe Textlast — Band 1 statt Band 2. |

#### Ethik (1)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0138.t2` | 7 | understand | text_analysis | 1→2 | **2** | Schau dir die Zeitleiste (Abbildung 1) zur rechtlichen Entwicklung der Sterbehilfe an. a)… | Zeitleiste auswerten: Teile a/b sind Ablesen (reproduktiv), Teil c offene Reflexion; der offene Schreibanteil hebt die Aufgabe knapp auf Transfer (Band 2). Grenzfall — überwiegend Abruf. |

#### Geographie und wirtschaftliche Bildung (16)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0032.t1` | 3 | apply | multiple_choice | 2→1 | **2** *(bestätigt Anchor)* | Ein plötzlicher Frost zerstört in Spanien fast die gesamte Erdbeernte. Was passiert mit d… | CONFIRM: Trotz geschlossenem MC-Format verlangt das 'und warum' echtes Anwenden des Angebot-Nachfrage-Mechanismus — Transfer (Band 2) ist berechtigt; der Modell-Hinweis auf Band 1 greift zu kurz. |
| `c0034.t3` | 4 | apply | matching | 2→1 | **2** *(bestätigt Anchor)* | Ordne jedes Alltagsbeispiel der passenden EU-Grundfreiheit zu. | CONFIRM: Alltagsbeispiele den EU-Grundfreiheiten zuordnen heißt, abstrakte Kategorien auf neue Fälle anzuwenden — echter Transfer (Band 2); das geschlossene Format senkt den Anspruch nicht auf Band 1. |
| `c0081.t4` | 4 | evaluate | true_false_justify | 3→2 | **2** | Beurteile, ob die folgenden Aussagen über Bevölkerungsdynamik und Urbanisierung richtig o… | R/F zu Bevölkerungsdynamik entscheiden und je in einem Satz begründen: eng geführte Beurteilung — Transfer (Band 2) statt offener Reflexion (Band 3). |
| `c0082.t4` | 2 | evaluate | true_false_justify | 3→2 | **2** | Beurteile, ob die folgenden Aussagen zu Energie und Klimawandel richtig oder falsch sind,… | R/F zu Energie und Klimawandel mit Ein-Satz-Begründung: scaffolded, die Beurteilung ist vorstrukturiert — Band 2 statt Band 3. |
| `c0090.t4` | 1 | analyze | case_study | 2→3 | **3** | Fallbeispiel: Die Sahelzone (Westafrika) Die Sahelzone ist eine Übergangszone zwischen de… | Fallstudie Sahelzone eigenständig analysieren, sehr hohe Textlast, offene Schriftform — anspruchsvoll (Band 3), über dem Transfer-Anchor (Band 2). |
| `c0093.t3` | 2 | analyze | case_study | 2→3 | **3** | **Fallbeispiel: Das Verschwinden der Bankfiliale** In einer Kleinstadt mit 4.000 Einwohne… | Fallstudie Bankfiliale mehrteilig analysieren (betroffene Gruppen, Folgen): offene Analyse — Band 3. Grenzfall wegen moderater Textlänge. |
| `c0094.t2` | 3 | understand | data_interpretation | 1→2 | **2** | Sieh dir die Bevölkerungspyramide Österreichs (Stand 1.1.2024) an. Welche Altersgruppen s… | Bevölkerungspyramide lesen und Folgen für die Sozialversicherung frei erklären: offene Deutung über bloßem Verstehen — Transfer (Band 2). |
| `c0107.t2` | 3 | understand | open_response | 1→2 | **2** | Österreich hatte am 1.1.2024 insgesamt 9.158.750 Einwohnerinnen und Einwohner. Nenne die … | Die drei stärksten Jahrgänge nennen und ihre Ursachen erklären: offene Erklärung — Transfer (Band 2), nicht bloße Reproduktion. |
| `c0108.t2` | 3 | understand | open_response | 1→2 | **2** | Berechne auf Basis der Gesamtbevölkerung von 9.158.750 Personen, wie viele Menschen in Ös… | Anteil der ≥75-Jährigen aus der Gesamtzahl berechnen und Rechenweg zeigen: eine offene Rechenaufgabe — Transfer (Band 2), trotz Einstufung als Verstehen. |
| `c0109.t4` | 3 | evaluate | multiple_choice | 3→2 | **2** | Welche der folgenden Maßnahmen kann dazu beitragen, die finanzielle Belastung des Pension… | Maßnahmen aus einer Liste auswählen und kurz begründen: geschlossene Auswahl mit knapper Begründung — Transfer (Band 2), nicht Reflexion (Band 3). |
| `c0111.t4` | 4 | evaluate | true_false_justify | 3→2 | **2** | Beurteile die folgenden Aussagen als richtig oder falsch und begründe deine Entscheidung … | R/F entscheiden und je kurz begründen: eng geführtes Beurteilungsformat — Band 2 statt Band 3. |
| `c0112.t4` | 4 | analyze | open_response | 2→3 | **3** | Nigeria stößt nur 0,6 t CO₂ pro Kopf aus — einen der niedrigsten Werte weltweit. Trotzdem… | Erklären, warum Nigerias geringe Pro-Kopf-Emission bei hoher Betroffenheit ein Gerechtigkeitsproblem ist: offene argumentative Analyse — anspruchsvoll (Band 3). |
| `c0112.t5` | 4 | evaluate | true_false_justify | 3→2 | **2** | Beurteile die folgenden Aussagen als richtig oder falsch und begründe kurz. | R/F entscheiden und kurz begründen: scaffolded — Transfer (Band 2) statt offener Reflexion (Band 3). |
| `c0118.t5` | 3 | analyze | case_study | 2→3 | **3** | Die Gemeinde Hallstatt (Oberösterreich, ca. 800 Einwohner:innen) ist bekannt als beliebte… | Fallstudie Hallstatt analysieren, sehr hohe Textlast, offene Schriftform — Band 3, über dem Transfer-Anchor (Band 2). |
| `c0145.t3` | 7 | evaluate | true_false_justify | 3→2 | **2** | Beurteile die folgenden Aussagen: Sind sie richtig oder falsch? Begründe deine Einschätzu… | R/F mit Ein-Satz-Begründung: die Beurteilung ist eng geführt — Band 2 statt Band 3. |
| `c0146.t2` | 8 | evaluate | multiple_choice | 3→2 | **2** | Welche der folgenden Aussagen zur wirtschaftlichen Globalisierung sind zutreffend? Wähle … | Zutreffende Aussagen zur Globalisierung auswählen und begründen: geschlossene Auswahl mit knapper Begründung — Transfer (Band 2), nicht Reflexion (Band 3). |

#### Geschichte und politische Bildung (2)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0141.t5` | 7 | evaluate | true_false_justify | 3→2 | **2** | Entscheide, ob die folgenden Aussagen zum nationalsozialistischen System und zum Holocaus… | R/F zu NS-System und Holocaust mit kurzer Begründung: inhaltlich schwer, aber die Aufgabenoperation (entscheiden + knapp begründen) bleibt Transfer (Band 2). Grenzfall wegen der inhaltlichen Tiefe. |
| `c0142.t5` | 7 | evaluate | multiple_choice | 3→2 | **2** | Welche der folgenden Erklärungen für den Zusammenbruch der Sowjetunion werden in der Gesc… | Diskutierte Erklärungen zum Zerfall der UdSSR ankreuzen und begründen: geschlossene Auswahl mit kurzer Begründung — Band 2 statt Band 3. |

#### Griechisch (1)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0144.t5` | 7 | evaluate | true_false_justify | 3→2 | **2** | Entscheide für jede Aussage, ob sie richtig (R) oder falsch (F) ist, und begründe deine E… | R/F entscheiden und in einem Satz begründen: eng geführtes Format — Transfer (Band 2) statt Reflexion (Band 3). |

#### Haushaltsökonomie und Ernährung (2)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0147.t3` | 6 | analyze | data_analysis | 2→3 | **3** | Schau dir die beiden Grafiken (Abb. 1 und Abb. 2) an: Sie zeigen einerseits die empfohlen… | Zwei Grafiken (Empfehlung vs. Konsum) vergleichen und Abweichungen deuten: offene Datenanalyse, hohe Textlast — anspruchsvoll (Band 3). |
| `c0148.t4` | 6 | analyze | data_analysis | 2→3 | **3** | Die Abbildung zeigt, wie häufig Jugendliche verschiedene Lebensmittelgruppen täglich kons… | Konsumhäufigkeiten vergleichen und soziale/sensorische Faktoren deuten: offene Analyse, höchste Textlast — Band 3. |

#### Latein (4)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0060.t5` | 3 | apply | ordering | 2→1 | **2** *(bestätigt Anchor)* | Bringe die Wörter in eine sinnvolle lateinische Satzreihenfolge (Subjekt — Objekt — Verb … | CONFIRM: Lateinische Wörter zu korrekter Satzstellung ordnen und übersetzen wendet Syntaxregeln an — echter Transfer (Band 2); trotz Reihungsformat nicht auf Band 1 zu senken. |
| `c0062.t4` | 3 | apply | matching | 2→1 | **1** | Verbinde das lateinische Wort mit seiner Bedeutung auf Deutsch und suche ein modernes deu… | Lateinvokabel↔deutsche Bedeutung verbinden: im Kern Vokabelabruf (das Erbwort-Suchen ist ein kleiner Zusatz) — reproduktionsnah (Band 1) statt Transfer (Band 2). |
| `c0063.t4` | 4 | evaluate | true_false_justify | 3→2 | **2** | Sind die folgenden Aussagen über das Fortleben des Lateinischen richtig (R) oder falsch (… | R/F zum Fortleben des Lateinischen mit kurzer Begründung: scaffolded — Transfer (Band 2) statt Reflexion (Band 3). |
| `c0151.t3` | 8 | understand | translation | 1→2 | **2** | Lies den folgenden Ausschnitt aus Senecas Brief an Lucilius sorgfältig durch und übersetz… | Authentische Seneca-Passage idiomatisch übersetzen: die Übersetzung eines Originaltexts mit hoher Textlast ist Transfer (Band 2), nicht bloßes Verstehen (Band 1). |

#### Lebende Fremdsprache (1)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0140.t1` | 8 | understand | writing_task | 1→2 | **2** | Think about a job or profession that interests you — one you might want to do in the futu… | Einen zusammenhängenden Absatz über einen Beruf und KI schreiben: freie Textproduktion in der L2 — Transfer (Band 2), über der Einstufung als Verstehen. |

#### Mathematik (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0181.t2` | 1 | understand | calculation | 1→2 | **1** *(bestätigt Anchor)* | Die App zeigt Bens Gesamtstrecke als 12,25 km an. Schreibe diese Zahl als gemischte Zahl … | CONFIRM: 12,25 als gemischte Zahl schreiben und den Stellenwert in einem Satz erklären: elementare Umwandlung der 1. Klasse; die kurze Erklärung hebt sie nicht auf Transfer — Band 1 bestätigt, der Modell-Hinweis auf Band 2 überschätzt das offene Format. |
| `c0189.t5` | 4 | analyze | modelling_task | 2→3 | **3** | Zwei Freund:innen streiten: Anna behauptet, √9 + √16 sei dasselbe wie √(9+16). Ben widers… | √9+√16 vs. √25 rechnerisch prüfen und daraus eine allgemeine Vorsicht bei Wurzeln/Näherungen ableiten: offene Argumentation im irrationalen Zahlenbereich — anspruchsvoll (Band 3). |
| `c0197.t4` | 4 | understand | open_response | 1→2 | **2** | Der Rutschturm ist ein Drehzylinder mit Radius 1,5 m und Höhe 4 m, obendrauf sitzt als Da… | Beschreiben, wie Zylinder/Kegel durch Rotation entstehen, und die für die Oberfläche nötigen Größen benennen: offene konzeptuelle Erklärung — Transfer (Band 2). |

#### Physik (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0086.t5` | 3 | evaluate | true_false_justify | 3→2 | **2** | Beurteile die folgenden Aussagen über das Elektronengasmodell. Kreuze an (richtig / falsc… | R/F zum Elektronengasmodell ankreuzen und kurz begründen: eng geführte Beurteilung — Band 2 statt Band 3. |
| `c0123.t3` | 4 | analyze | open_response | 2→3 | **3** | Beide Städte haben ähnliche Jahresmitteltemperaturen (Wien ca. 11,8 °C, Bregenz ca. 10,2 … | Bei ähnlicher Temperatur die Ursache des großen Niederschlagsunterschieds begründet vermuten: offene, hypothesenbildende Analyse — anspruchsvoll (Band 3). |
| `phy-strahlung.str.t4` | 4 | evaluate | true_false_justify | 3→2 | **2** | Entscheide richtig/falsch und begründe oder korrigiere. | R/F entscheiden und begründen/korrigieren: vorstrukturiertes Beurteilungsformat — Transfer (Band 2) statt offener Reflexion (Band 3). |

#### Technik und Design (1)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0049.t2` | 4 | understand | open_response | 1→2 | **2** | Beschreibe, wie ein normales Fahrrad die Kraft der Beine auf das Hinterrad überträgt. Geh… | Die Kraftübertragung am Fahrrad mit allen Fachbegriffen strukturiert beschreiben: offene Erklärung mit sehr hoher Textlast — Transfer (Band 2), über bloßem Verstehen. |

#### Zweite lebende Fremdsprache (5)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0055.t4` | 3 | apply | matching | 2→1 | **1** | Ordne die Fragen (1–4) den passenden Antworten (A–D) zu. Lehrkraft liest die Sätze zweima… | Fragen↔Antworten zuordnen (Hörtext): rezeptives Wiedererkennen, minimale Textlast — Band 1 statt Band 2. |
| `c0056.t4` | 4 | apply | matching | 2→1 | **1** | Lies diese neue kurze Nachricht. Ordne dann die unterstrichenen Wörter ihrer deutschen Be… | Unterstrichene Wörter ihrer deutschen Bedeutung zuordnen: Vokabelabruf im geschlossenen Format — Reproduktion (Band 1). |
| `c0057.t2` | 3 | apply | table_fill | 2→1 | **1** | Ergänze die Sätze mit dem richtigen Possessivpronomen: mon, ma oder mes. Denke an das Gen… | Possessivbegleiter (mon/ma/mes) einsetzen: weitgehend mechanische Ein-Regel-Anwendung — reproduktionsnah (Band 1) statt Transfer (Band 2). |
| `c0057.t4` | 3 | apply | matching | 2→1 | **1** | Verbinde das Hobby mit dem passenden französischen Satz. Hobbys: 1. Fußball spielen \| 2. … | Hobby↔französischer Satz verbinden: geschlossenes Wiedererkennen, minimale Textlast — Band 1. |
| `c0059.t2` | 4 | apply | table_fill | 2→1 | **2** *(bestätigt Anchor)* | Ergänze die passé-composé-Sätze. Wähle das richtige Hilfsverb (avoir oder être) und schre… | CONFIRM: Passé composé bilden verlangt Hilfsverbwahl (avoir/être) UND Partizipangleichung — mehrschrittige Regelanwendung, echter Transfer (Band 2); nicht auf Band 1 zu senken. |

## Sample (informative Bestätigungen)

#### Bewegung und Sport (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0005.t4` | 2 | analyze | open_response | 2→2 | **2** | Denk an einen Moment im Sport (Schulsport, Vereinssport, Zuschauen), in dem du unfaires V… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0006.t6` | 3 | create | create_produce | 3→3 | **3** | Entwirf einen 2-Wochen-Trainingsplan (Überblick) für eine/n Mitschüler:in, der/die in 6 W… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0009.t2` | 4 | understand | open_response | 1→1 | **1** | Schreibe 3–5 Sätze darüber, welche körperliche Aktivität dir am meisten Spaß macht — und … | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |

#### Biologie (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `bio-immunsystem.imm.t1` | 4 | understand | open_response | 1→1 | **1** | Jemand mit einer normalen Erkältung (durch Viren ausgelöst) verlangt vom Arzt ein Antibio… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `bio-immunsystem.imm.t5` | 4 | analyze | open_response | 2→2 | **2** | In einem Krankenhaus tauchen plötzlich Bakterien auf, gegen die ein bestimmtes Antibiotik… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `bio-immunsystem.imm.t7` | 4 | create | create_produce | 3→3 | **3** | Eine Schülerzeitung diskutiert: 'Sollte es für bestimmte Berufe (z. B. in Krankenhäusern)… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Biologie und Umweltbildung (4)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0132.t2` | 6 | understand | open_response | 1→1 | **1** | Der Kohlenstoffkreislauf ist eines der wichtigsten biogeochemischen Systeme der Erde. a) … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0172.t7` | 1 | apply | create_produce | 2→2 | **2** | Schreibe einen kurzen Steckbrief-Text (5–6 Sätze) für eine Tierheim-Broschüre, der zukünf… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0176.t5` | 3 | evaluate | decision_scenario | 3→3 | **3** | Eine Gemeinde will einen naturnahen Bach begradigen und betonieren, um Hochwasser schnell… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0178.t5` | 3 | evaluate | source_critique | 3→3 | **3** | Ein Mitschüler behauptet: 'Zerstörter Boden erholt sich genauso schnell wieder wie eine g… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Chemie (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0003.t4` | 4 | analyze | open_response | 2→2 | **2** | Ein Wissenschaftsmagazin berichtet: «Saurer Regen hat in manchen Regionen Deutschlands ei… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0134.t2` | 8 | understand | open_response | 1→1 | **1** | Die Gleichung in Abb. 5 zeigt die Zellatmung. Erkläre in eigenen Worten: Welche Funktion … | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0134.t4` | 8 | evaluate | source_critique | 3→3 | **3** | Lies die folgende Schlagzeile aus einem Online-Artikel: „E-Nummern sind Chemie pur – desh… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Deutsch (5)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0010.t3` | 3 | understand | text_analysis | 1→1 | **1** | Im Text stehen Fachbegriffe. Erkläre in eigenen Worten, was die folgenden Wörter im Zusam… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0012.t4` | 4 | create | text_production | 3→3 | **3** | Formuliere denselben Sachverhalt zweimal: einmal in **Umgangssprache**, einmal in **Bildu… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0014.t3` | 4 | create | text_production | 3→3 | **3** | Schreibe eine **formelle E-Mail** an eine Lehrperson deiner Schule. Du möchtest höflich a… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0135.t3` | 7 | analyze | textanalyse | 2→2 | **2** | Untersuche das Gedicht auf sprachliche Mittel (z. B. Metaphern, Personifikationen, Vergle… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0136.t4` | 7 | analyze | open_response | 2→2 | **2** | Wähle einen der beiden analysierten Texte und untersuche seine Überschrift genauer: Welch… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |

#### Digitale Grundbildung (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0015.t4` | 4 | evaluate | decision_scenario | 3→3 | **3** | Lena nutzt eine kostenlose Fitness-App. Bei der Installation fragt die App nach Zugriff a… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0018.t2` | 1 | understand | open_response | 1→1 | **1** | Nenn drei Beispiele für persönliche Informationen, die du im Internet über dich teilst – … | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0018.t5` | 1 | apply | open_response | 2→2 | **2** | Digitale Werkzeuge ermöglichen neue Formen der Zusammenarbeit. Nenne zwei konkrete Beispi… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |

#### Erste lebende Fremdsprache (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0052.t4` | 4 | apply | text_production | 2→2 | **2** | Write a short forum posting (50–70 words) on the following question: "Should teenagers ha… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0052.t6` | 4 | create | create_produce | 3→3 | **3** | Your school magazine is asking students: "What is the most important thing young people c… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0053.t2` | 1 | understand | speaking_task | 1→1 | **1** | Practise with a partner. Ask each other these questions and answer them about yourself. T… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |

#### Ethik (4)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0137.t1` | 5 | understand | data_interpretation | 1→1 | **1** | Schau dir die Grafik zum CO₂-Fußabdruck verschiedener Produkte an (Abbildung 1). a) Welch… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0138.t5` | 7 | evaluate | argumentation | 3→3 | **3** | Das österreichische Verfassungsgericht (VfGH) hat 2020 entschieden, dass das generelle Ve… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0138.t6` | 7 | analyze | open_response | 2→2 | **2** | Was bedeutet es, 'in Würde zu sterben'? Dieser Begriff wird von verschiedenen Menschen se… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0138.t7` | 7 | create | create_produce | 3→3 | **3** | Du bist Mitglied einer fiktiven Ethikkommission, die einen Leitfaden zum Thema 'Sterbebeg… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Geographie und wirtschaftliche Bildung (8)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0090.t2` | 1 | understand | data_interpretation | 1→1 | **1** | Schau dir Abbildung 1 (CO₂-Äquivalente von Lebensmitteln) an. a) Welches Lebensmittel ver… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0090.t5` | 1 | evaluate | data_interpretation | 3→3 | **3** | Schau dir Abbildung 3 (Emissionen nach Ernährungsweise) an. a) Welche Ernährungsweise erz… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0091.t5` | 1 | evaluate | case_study | 3→3 | **3** | Fallbeispiel: Erdbeben in Haiti (2010) und in Chile (2010) Im Januar 2010 erschütterte ei… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0091.t6` | 1 | evaluate | decision_scenario | 3→3 | **3** | Du bist Mitglied eines fiktiven österreichischen Hilfskomitees. Nach einer schweren Übers… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0094.t5` | 3 | evaluate | position_argument | 3→3 | **3** | Abbildung 4 zeigt einen schematischen Zusammenhang zwischen Bildungsabschluss und Einkomm… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0097.t5` | 4 | evaluate | position_argument | 3→3 | **3** | Die folgende These wird diskutiert: *„Einzelne Jugendliche können durch ihr Handeln globa… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0106.t4` | 3 | evaluate | decision_scenario | 3→3 | **3** | Das Bundesministerium hat 10 Millionen Euro für regionale Infrastruktur zur Verfügung. Es… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0117.t4` | 3 | analyze | case_study | 2→2 | **2** | Das österreichische Pensionssystem funktioniert nach dem 'Umlageverfahren': Die Beiträge … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |

#### Geometrisches Zeichnen (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0020.t3` | 4 | understand | true_false_justify | 1→1 | **1** | Beurteile die folgenden Aussagen über geometrische Körper. Schreibe jeweils „wahr“ oder „… | Oberflächenmerkmale (offenes Antwortformat, Textlast) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0022.t5` | 4 | evaluate | decision_scenario | 3→3 | **3** | Ein Maschinenteil soll für ein Ersatzteilkatalog dokumentiert werden. Der Konstrukteur üb… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0024.t4` | 4 | apply | construction | 2→2 | **2** | Zeichne den Frontalriss (Normalprojektion von vorne) und den Horizontalriss (Normalprojek… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |

#### Geschichte und politische Bildung (5)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0025.t2` | 2 | understand | source_analysis | 1→1 | **1** | Lies den folgenden Ausschnitt aus einem ägyptischen Grabtext (ca. 1800 v. Chr.), der im O… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0028.t6` | 3 | evaluate | position_argument | 3→3 | **3** | These: „Migration hat Österreich und Europa hauptsächlich bereichert.“ Nimm Stellung: Ist… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0029.t2` | 4 | analyze | source_analysis | 2→2 | **2** | Lies diesen Ausschnitt aus dem Österreichischen Staatsvertrag, Artikel 1, unterzeichnet a… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0141.t4` | 7 | analyze | source_analysis | 2→2 | **2** | Deine Lehrperson stellt dir einen zeitgenössischen Text oder ein Propagandaplakat aus der… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0141.t6` | 7 | evaluate | argumentation | 3→3 | **3** | Lies die folgende These aufmerksam und nimm schriftlich Stellung: *'Das Erinnern an den H… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Griechisch (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0143.t2` | 5 | understand | translation | 1→1 | **1** | Deine Lehrkraft zeigt dir die folgenden griechischen Wörter an der Tafel (oder auf einem … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0144.t2` | 7 | analyze | text_analysis | 2→2 | **2** | Deine Lehrkraft stellt dir einen kurzen deutschen Sachtext (oder eine Übersetzung) zu Tha… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0144.t6` | 7 | evaluate | open_response | 3→3 | **3** | Heraklit soll gesagt haben: πάντα ῥεῖ καὶ οὐδὲν μένει (alles fließt und nichts bleibt). D… | Oberflächenmerkmale (Zahlenbereich, Aufgabentyp) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Haushaltsökonomie und Ernährung (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0147.t5` | 6 | remember | table_fill | 1→1 | **1** | Fülle die Tabelle aus: Ordne jedem Nährstoff seine Hauptfunktion im Körper, einen typisch… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Erinnern) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0148.t5` | 6 | apply | calculation | 2→2 | **2** | Lisa ist 16 Jahre alt, 165 cm groß und wiegt 58 kg. Sie treibt an drei Tagen pro Woche Sp… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0148.t7` | 6 | evaluate | source_critique | 3→3 | **3** | Lies die folgenden zwei Textausschnitte zum Thema 'Superfoods' und bewerte sie kritisch. … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Informatik (4)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0149.t1` | 5 | understand | true_false_justify | 1→1 | **1** | Entscheide für jede Aussage, ob sie wahr oder falsch ist, und begründe deine Entscheidung… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0149.t4` | 5 | create | create_produce | 3→3 | **3** | Schreibe einen Algorithmus in Pseudocode, der eine Liste von fünf Ganzzahlen einliest und… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0150.t4` | 5 | apply | decision_scenario | 2→2 | **2** | Du entwickelst zwei Anwendungen: – **Anwendung A**: Eine App, die Musikdateien von einem … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0150.t6` | 5 | evaluate | argumentation | 3→3 | **3** | Netzneutralität bedeutet, dass Internetanbieter alle Datenpakete gleich behandeln müssen … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Kunst und Gestaltung (4)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0035.t4` | 2 | apply | make_artifact | 2→2 | **2** | Stimmungsbild: Wähle eine Emotion (z.B. Aufregung, Traurigkeit, Geborgenheit oder Angst).… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0036.t2` | 1 | understand | make_artifact | 1→1 | **1** | Konturzeichnung: Wähle einen einfachen Gegenstand vor dir (Stift, Radiergummi, Lineal ode… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0036.t3` | 1 | apply | make_artifact | 2→2 | **2** | Beobachtungszeichnung: Zeichne jetzt denselben Gegenstand nochmals — diesmal darfst du zw… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0037.t4` | 3 | evaluate | decision_scenario | 3→3 | **3** | Das Plakat soll für zwei verschiedene Filme verwendet werden: Version A — ein politischer… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Latein (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0061.t5` | 3 | analyze | text_analysis | 2→2 | **2** | Lies den folgenden kurzen lateinischen Text. Unterstreiche alle Verben und schreibe daneb… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0064.t2` | 4 | understand | translation | 1→1 | **1** | Übersetze die folgenden Sätze ins Deutsche. Gib jeweils an, ob das Verb Aktiv (A) oder Pa… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0151.t7` | 8 | create | create_produce | 3→3 | **3** | Schreibe auf Deutsch einen kurzen Ratgeber-Text (8–10 Sätze) im Stil Senecas für eine Per… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Lebende Fremdsprache (4)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0139.t4` | 7 | remember | reading_task | 1→1 | **1** | Now read Text B. --- **Text B: The Architecture of Connection** For most of human history… | Oberflächenmerkmale (Textlast, offenes Antwortformat) stützen die kognitive Einstufung (Erinnern) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0140.t3` | 8 | evaluate | writing_task | 3→3 | **3** | Read the following prompt carefully, then write your response. **Situation:** A national … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0140.t4` | 8 | analyze | create_produce | 2→2 | **2** | Before you write your essay, complete this brief planning grid. It will help you organise… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0140.t5` | 8 | create | writing_task | 3→3 | **3** | Write a discursive essay of 220–260 words on the following title: **"Artificial intellige… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Mathematik (7)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0153.t1` | 8 | apply | calculation | 2→2 | **2** | Gegeben ist die Funktion f(x) = x² auf dem Intervall [0, 2]. Teile das Intervall in n = 4… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0154.t5` | 6 | apply | calculation | 2→2 | **2** | In einer Sportabteilung werden 200 Schüler:innen auf eine seltene Erkrankung getestet. 10… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0189.t2` | 4 | understand | true_false_justify | 1→1 | **1** | √8 lässt sich nicht als Bruch zweier ganzer Zahlen schreiben — √8 ist also eine irrationa… | Oberflächenmerkmale (Zahlenbereich, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0189.t3` | 4 | apply | calculation | 2→2 | **2** | Nähere √8 durch systematisches Probieren an, ohne die Wurzel-Taste zu benutzen. Gehe so v… | Oberflächenmerkmale (Zahlenbereich, Aufgabentyp) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0189.t4` | 4 | apply | calculation | 2→2 | **2** | Berechne jetzt mit Technologieeinsatz (Taschenrechner erlaubt) die tatsächliche Länge der… | Oberflächenmerkmale (Zahlenbereich, Aufgabentyp) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0189.t6` | 4 | create | create_produce | 3→3 | **3** | Erfinde eine eigene kurze Sachsituation aus deinem Alltag (Garten, Zimmer, Sportplatz, Ba… | Oberflächenmerkmale (Aufgabentyp, Zahlenbereich) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0197.t5` | 4 | apply | calculation | 2→2 | **2** | Jetzt wird gerechnet: Der Kegel auf dem Rutschturm hat Radius r = 1,5 m und Höhe h = 1 m.… | Oberflächenmerkmale (Zahlenbereich, Aufgabentyp) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |

#### Musik (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0042.t2` | 3 | understand | open_response | 1→1 | **1** | Die Lehrerin / der Lehrer beschreibt einen einfachen Volkstanz (z. B. einen Dreischritt-W… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0042.t5` | 3 | create | performance_task | 3→3 | **3** | Choreografie in der Kleingruppe (3–4 Personen): Eure Gruppe erfindet eine kurze Tanzseque… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0043.t3` | 4 | analyze | open_response | 2→2 | **2** | Beethoven (1770–1827) war ein Zeitgenosse der Französischen Revolution (1789). Seine 3. S… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |

#### Physik (5)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0088.t6` | 4 | create | decision_scenario | 3→3 | **3** | Österreich plant, bis 2030 seinen Strom zu 100 % aus erneuerbaren Quellen zu erzeugen. Ei… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0124.t3` | 4 | understand | open_response | 1→1 | **1** | Indien stößt 2,2 Tonnen CO₂ pro Kopf aus — weit weniger als die USA (13,6 t). Trotzdem ge… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0192.t6` | 2 | evaluate | source_critique | 3→3 | **3** | Ein Mitschüler behauptet: Endoskope in der Medizin sind nur ein Spielzeug für Ärzte, ein … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0193.t5` | 2 | analyze | data_interpretation | 2→2 | **2** | Betrachte die Abbildung zum Schattenraum hinter einer Kugel bei einer punktförmigen Licht… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `phy-strahlung.str.t5` | 4 | analyze | open_response | 2→2 | **2** | Dosen zum Vergleich: 1 Banane ≈ 0,1 µSv · Thorax-Röntgen ≈ 20 µSv · Transatlantikflug ≈ 4… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |

#### Psychologie und Philosophie (4)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0157.t2` | 7 | understand | text_analysis | 1→1 | **1** | Lies den folgenden Kurztext und beantworte danach die Fragen. --- „Maya lernt für eine Pr… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0157.t6` | 7 | evaluate | argumentation | 3→3 | **3** | Stell dir vor, deine Schule überlegt, das Lernen mit Karteikarten durch eine App zu erset… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
| `c0158.t4` | 8 | analyze | dilemma | 2→2 | **2** | Lies das folgende Dilemma und beantworte die Fragen. --- Sophia weiß, dass ihre beste Fre… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0158.t6` | 8 | evaluate | decision_scenario | 3→3 | **3** | Ein Unternehmen kann durch eine Produktionsumstellung seinen CO₂-Ausstoß um 40 % senken, … | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Technik und Design (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0047.t3` | 3 | analyze | open_response | 2→2 | **2** | Analysiere zwei unterschiedliche Gebäude: ein Einfamilienhaus und eine Turnhalle. Verglei… | Oberflächenmerkmale (Textlast, Aufgabentyp) stützen die kognitive Einstufung (Analysieren) — mittel (Transfer) (Band 2) bestätigt. |
| `c0047.t5` | 3 | understand | open_response | 1→1 | **1** | Erkläre den Unterschied zwischen diesen drei Darstellungsarten in der Architektur: Grundr… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0048.t4` | 4 | evaluate | decision_scenario | 3→3 | **3** | Du möchtest dir neue Sportschuhe kaufen. Du hast zwei Optionen: Option A: Marken-Sportsch… | Oberflächenmerkmale (Aufgabentyp, Textlast) stützen die kognitive Einstufung (Bewerten) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |

#### Zweite lebende Fremdsprache (3)

| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | Aufgabe (Auszug) | Begründung |
|---|---|---|---|---|---|---|---|
| `c0056.t3` | 4 | understand | open_response | 1→1 | **1** | Suche im Text die französischen Ausdrücke für folgende deutsche Bedeutungen. Schreibe sie… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Verstehen) — leicht (Reproduktion) (Band 1) bestätigt. |
| `c0058.t3` | 4 | apply | speaking_task | 2→2 | **2** | Partnerübung: Spielt ein Gespräch im Café nach. Eine Person ist Kellner:in, die andere is… | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Anwenden) — mittel (Transfer) (Band 2) bestätigt. |
| `c0059.t4` | 4 | create | create_produce | 3→3 | **3** | Schreibe 4–5 Sätze über ein Wochenende, das du hattest (oder erfunden hast). Benutze das … | Oberflächenmerkmale (Aufgabentyp, offenes Antwortformat) stützen die kognitive Einstufung (Erschaffen) — anspruchsvoll (Reflexion) (Band 3) bestätigt. |
