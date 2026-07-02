# Review-Triage: adversarialer Durchgang über die Prüf-Warteschlange

Du bist ein **strenger Fachdidaktiker / eine strenge Fachdidaktikerin** (AHS, Österreich).
Unten stehen **54 Einträge**, die zur fachlichen Prüfung anstehen. Beurteile jeden
Eintrag kritisch — du suchst Schwächen, nicht Bestätigung.

**Du gibst NICHTS frei und lehnst NICHTS ab.** Das ist reine Triage: Deine Einschätzung
lenkt nur, was zuerst gelesen wird — die fachliche Endabnahme (SME) bleibt das Gate
(invariants §7).

## Prüfkriterien (je Eintrag)
1. **Didaktik** — steigt die kognitive Leiter (remember → … → create), statt alles auf
   einer Stufe zu bleiben? Sind die Aufgaben klar, eindeutig und schülergerecht gestellt?
2. **Sprachliches Register** — AHS-angemessenes Deutsch (bzw. Zielsprache): altersgerecht,
   präzise Fachsprache, keine Stilbrüche?
3. **Lösungs-Konsistenz** — beantwortet der `answer_key` TATSÄCHLICH die gestellte Frage
   (nicht eine benachbarte)? Passt die Musterlösung zur Aufgabenform?

## Ausgabe
Schreibe **ausschließlich** dieses JSON (kein Fließtext, keine ``` Zäune) nach
`runs/triage/verdicts.json` — eine Liste, ein Objekt pro beurteiltem Eintrag:

```json
[
  {"kind": "item", "id": "c0001", "rating": 2, "attention": "hoch",
    "reasons": ["Kognitive Leiter flach", "Lösung zu Aufgabe 3 beantwortet die Frage nicht"],
    "watch": "answer_key von Aufgabe 3 gegen den Prompt lesen"}
]
```

- `rating` 1–5 — erwartete Qualität (1 = gravierende Mängel erwartet, 5 = sehr wahrscheinlich solide)
- `attention` ∈ `"hoch"` | `"mittel"` | `"niedrig"` — wie dringend das gelesen werden muss
- `reasons` — höchstens 3 kurze deutsche Begründungen
- `watch` — eine Zeile: worauf beim Lesen zuerst zu achten ist

## Einträge (54)

### item `c0009` — „Geschichte und politische Bildung 3. Kl. — Die Industrialisierung“ (Geschichte und politische Bildung, 3. Kl. · Stufe sprache)
- ⚠ asset 'sv-timeline': Zahlen ohne Quellenangabe — als echte Daten data_source (zitierter Datensatz) setzen, sonst illustrative=true (schematisch). Unbelegte echte Zahlen wirken geprüft, sind es aber nicht.
- Kernfrage: Wie verändert die Maschine Arbeit, Stadt und Gesellschaft?
- Aufgaben:
  1. [ordering · remember] Bringe die Ereignisse in die richtige zeitliche Reihenfolge.
     Lösung: Hargreaves baut die Spinning Jenny – eine frühe mechanische Spinnmaschine (1764) → James Watt verbessert die Dampfmaschine entscheidend (1769) → Eröffnung der ersten öffentlichen Dampf-Eisenbahn (Stockton-Darlington) (1825) → Eröffnung der Bahn Liverpool-Manchester (1830) → Erster Dampfzug in Öster…
  2. [cause_effect_match · analyze] Ordne jeder Ursache die passende Folge zu.
     Lösung: James Watt verbessert die Dampfmaschine → Maschinen können überall mit Dampfkraft angetrieben werden, nicht mehr nur am Fluss; Maschinen ersetzen die Handarbeit in der Produktion → Die Arbeit wandert aus der Werkstatt zu Hause in große Fabriken; Fabriken brauchen viele Arbeitskräfte an einem Ort → …
  3. [concept_match · understand] Ordne jedem Begriff die richtige Erklärung zu.
     Lösung: Industrialisierung: der Übergang von der Handarbeit zur Herstellung von Waren mit Maschinen in Fabriken; Dampfmaschine: eine Maschine, die aus erhitztem Wasserdampf Kraft gewinnt und damit andere Maschinen antreibt; Fabrik: ein großer Betrieb, in dem viele Menschen mit Maschinen gemeinsam Waren her…
  4. [content_comprehension · understand] Erkläre in eigenen Worten, warum „Die Industrialisierung“ wichtig war.
     Lösung: Die Industrialisierung veränderte das Leben tiefgreifender als fast jede Umwälzung zuvor: Maschinen, Fabriken und Eisenbahnen schufen neue Berufe, ließen Städte wachsen und steigerten die Menge der hergestellten Waren gewaltig. Zugleich entstand eine große Arbeiterschaft, deren harte Lebensbedingun…
  5. [structure_overview · understand] Nenne die wichtigsten Akteure und beschreibe kurz, wodurch sie sich auszeichnen.
     Lösung: James Watt: schottischer Ingenieur; verbesserte 1769 die Dampfmaschine entscheidend und machte sie als Antrieb für Fabriken brauchbar; James Hargreaves: englischer Weber und Erfinder; baute mit der Spinning Jenny eine frühe mechanische Spinnmaschine, die viele Fäden zugleich spann; George Stephenso…
  6. [position_argument · evaluate] Die Industrialisierung brachte neue Waren, Eisenbahnen und Arbeitsplätze, aber auch lange Arbeitstage, niedrige Löhne und Kinderarbeit in den Fabriken. War sie für die Menschen damals eher ein Fortschritt oder eher ein Rückschritt? Wäge das Für und Wider ab und begründe am Ende dein eigenes Urteil.
     Lösung: —

### item `c0008` — „Geschichte und politische Bildung 3. Kl. — Die Französische Revolution“ (Geschichte und politische Bildung, 3. Kl. · Stufe sprache)
- ⚠ asset 'sv-timeline': Zahlen ohne Quellenangabe — als echte Daten data_source (zitierter Datensatz) setzen, sonst illustrative=true (schematisch). Unbelegte echte Zahlen wirken geprüft, sind es aber nicht.
- Kernfrage: Wie stürzt das Volk eine jahrhundertealte Ordnung — und was setzt es an ihre Stelle?
- Aufgaben:
  1. [ordering · remember] Bringe die Ereignisse in die richtige zeitliche Reihenfolge.
     Lösung: Sturm auf die Bastille (14. Juli) (1789) → Erklärung der Menschen- und Bürgerrechte (1789) → Erste Verfassung – Frankreich wird konstitutionelle Monarchie (1791) → Ausrufung der Ersten Republik – Ende des Königtums (1792) → Hinrichtung Ludwigs XVI. (1793) → Staatsstreich Napoleons – Ende der Revolu…
  2. [cause_effect_match · analyze] Ordne jeder Ursache die passende Folge zu.
     Lösung: Die Ständegesellschaft teilte die Menschen in privilegierte Stände und einen rechtlosen Dritten Stand → im Volk wuchs der Wunsch nach Gleichheit und nach einem Ende der alten Ordnung; Der Staat hatte hohe Schulden, und es kam zu Hunger und teurem Brot → die Not trieb das Volk auf die Straße und lie…
  3. [concept_match · understand] Ordne jedem Begriff die richtige Erklärung zu.
     Lösung: Revolution: ein rascher, grundlegender Umsturz, bei dem eine bestehende Herrschaft und Ordnung von Grund auf verändert wird; Ständegesellschaft: eine Gesellschaft, in der die Menschen von Geburt an in Gruppen (Stände) eingeteilt sind, die sehr unterschiedliche Rechte und Pflichten haben; Absolutism…
  4. [content_comprehension · understand] Erkläre in eigenen Worten, warum „Die Französische Revolution“ wichtig war.
     Lösung: Die Französische Revolution beendete die jahrhundertealte Herrschaft eines absoluten Königs und stellte die Forderung nach Freiheit und Gleichheit für alle in den Mittelpunkt. Die Erklärung der Menschen- und Bürgerrechte wurde zum Vorbild für viele spätere Verfassungen und Bewegungen.
  5. [structure_overview · understand] Nenne die wichtigsten Akteure und beschreibe kurz, wodurch sie sich auszeichnen.
     Lösung: Ludwig XVI.: König von Frankreich; als absoluter Herrscher gestürzt und 1793 hingerichtet; Der Dritte Stand: das einfache Volk — Bauern, Handwerker, Bürger; trug nahezu alle Steuern und hatte kaum Rechte; Die Nationalversammlung: die Versammlung der Abgeordneten, die sich für das Volk zu sprechen e…
  6. [position_argument · evaluate] Die Revolution versprach Freiheit und Gleichheit für alle — zugleich kam es zu Gewalt und zur Schreckensherrschaft. Nimm Stellung: Wog der Gewinn an Rechten die Gewalt auf? Bedenke beide Seiten und begründe am Ende dein eigenes Urteil.
     Lösung: —

### item `c0002` — „Physik 4. Kl. — Strahlung und Radioaktivität“ (Physik, 4. Kl. · Stufe voll)
- Kernfrage: Was macht Strahlung gefährlich – und was nicht?
- Aufgaben:
  1. [open_response · understand] Beim radioaktiven Zerfall kann man für ein einzelnes Atom nicht sagen, wann es zerfällt – für sehr viele Atome aber sehr genau, wie viele pro Sekunde zerfallen. Erkläre, warum das kein Widerspruch ist.
     Lösung: Zerfall ist ein Zufallsprozess pro Atom; über große Zahlen mittelt sich der Zufall zu einer stabilen Rate (Halbwertszeit) — Statistik, kein Plan.
  2. [create_produce · create] Entwirf eine kleine Info-Karte (5–6 Sätze) für jüngere Schüler:innen zu einer aktuellen Anwendung von Strahlung (z. B. PET im Krankenhaus, Bestrahlung von Lebensmitteln, C-14-Datierung). Erkläre Nutzen UND Grenze.
     Lösung: —
  3. [open_response · analyze] WLAN-Signale gehen durch Wände, schaden dir aber nicht – Gammastrahlung dagegen ist gefährlich. Beide durchdringen Materie. Erkläre den Unterschied.
     Lösung: —
  4. [true_false_justify · evaluate] Entscheide richtig/falsch und begründe oder korrigiere.
     Lösung: 1 falsch (UV schädigt Zellen trotz nicht-ionisierend) · 2 richtig · 3 falsch (Funkwellen, kein Kernzerfall)
  5. [open_response · analyze] Dosen zum Vergleich: 1 Banane ≈ 0,1 µSv · Thorax-Röntgen ≈ 20 µSv · Transatlantikflug ≈ 40 µSv · natürliche Jahresdosis in Österreich ≈ 2–3 mSv. Ordne 'eine Banane essen', 'einmal fliegen' und 'ein Jahr leben' nach Dosis und erkläre, warum Größenordnungen wichtiger sind als Bauchgefühl.
     Lösung: —
  6. [decision_scenario · evaluate] Eine Schlagzeile behauptet: 'Handystrahlung macht krank!'. Welche EINE Frage würdest du stellen, bevor du das glaubst – und warum entscheidet gerade diese Frage über die Glaubwürdigkeit?
     Lösung: —
  … + 1 weitere Aufgaben

### item `c0006` — „Mathematik 4. Kl. — Daten und Zufall“ (Mathematik, 4. Kl. · Stufe voll)
- Kernfrage: Wann ist ein Glücksspiel fair?
- Aufgaben:
  1. [modelling_task · create] Erfinde ein einfaches Würfel- oder Münzspiel für zwei Personen, das auf den ersten Blick fair wirkt, in Wahrheit aber eine Person bevorzugt. Beschreibe die Regeln und begründe mit Wahrscheinlichkeiten, warum es unfair ist.
     Lösung: —

### item `c0015` — „Erste lebende Fremdsprache 1. Kl. — You're Invited! Tom's Birthday Party“ (Erste lebende Fremdsprache, 1. Kl. · Stufe voll)
- Kernfrage: Eine Einladung — verstehen und sprechen
- Aufgaben:
  1. [open_response · understand] What time does the party start?
     Lösung: At 3:00 p.m.
  2. [open_response · analyze] You play football and you love games. Is this a good party for you? Write yes or no and say why (one sentence in English).
     Lösung: Ja. Erwartet z.B.: "Yes, because there are games and we play in the garden." (Begruendung muss aus dem Text kommen: games / garden / music / cake.)
  3. [text_production · apply] Write a short reply to Tom. Say thank you, say you can come, and ask one question about the party (3-4 sentences in English).
     Lösung: Modelltext: „Hi Tom, thank you for the invitation! I can come to your party. Can I bring my friend Anna? See you on Saturday. From Lisa“ (kurze, korrekte Saetze; danken + zusagen + eine Frage).
  4. [speaking_task · apply] Work with a partner. One of you invites a friend to the party, the other one says thank you and accepts. Then swap roles.
     Lösung: Erwartet: A - "It's my birthday. Can you come to my party on Saturday at 3 o'clock? Please bring your trainers." B - "Thank you! Yes, I can come. Where is the party?" (Nuetzliche Wendungen: Can you come ...? / Thank you / Yes, I can. / Where ...? / What can I bring?)

### item `c0016` — „Erste lebende Fremdsprache 3. Kl. — This week's weather in Greenhaven“ (Erste lebende Fremdsprache, 3. Kl. · Stufe voll)
- Kernfrage: Das Wetter — verstehen und sprechen
- Aufgaben:
  1. [open_response · understand] What is the weather like on Wednesday, and how warm is it?
     Lösung: It is windy on Wednesday, and it is 15 degrees C.
  2. [open_response · analyze] You want to have a picnic in the park. Which day is best, and why?
     Lösung: Friday is best. It is sunny and 22 degrees C, the warmest day of the week, so it is perfect for a picnic. Monday is also good (sunny, 21 degrees C).
  3. [open_response · evaluate] What should you wear and take with you on Thursday? Explain why.
     Lösung: Take an umbrella, because it is rainy on Thursday. It is also cool (13 degrees C), so wear a warm jacket too.
  4. [text_production · apply] Write a short message to a friend (3-4 sentences). Suggest a good day this week to meet outside, and say why (use the weather and the temperature).
     Lösung: Modelltext: "Hi! Let's meet on Friday. It is sunny and 22 degrees C, so it is a great day to go to the park. See you then!" (3-4 kurze, korrekte Saetze; ein Wetterwort und eine Temperatur aus dem Text; Vorschlag mit Begruendung).
  5. [speaking_task · apply] Work in pairs. You are two friends. Use the forecast to plan one activity for the weekend.
     Lösung: Erwartet: A begruesst und macht einen Vorschlag ("Let's...", "Why don't we...?"), begruendet mit dem Wetter (warm and sunny); B stimmt zu ("Good idea!", "That sounds great"), schlaegt eine Aktivitaet vor und fragt nach dem Tag ("Saturday or Sunday?"); beide einigen sich auf einen Tag. Nuetzliche We…

### item `c0017` — „Erste lebende Fremdsprache 2. Kl. — Sunnyfield Zoo“ (Erste lebende Fremdsprache, 2. Kl. · Stufe voll)
- Kernfrage: Im Zoo — verstehen und sprechen
- Aufgaben:
  1. [open_response · understand] What time is the lion feeding?
     Lösung: At 13:00.
  2. [open_response · analyze] A family of two adults and one child want tickets. How much do they pay together?
     Lösung: £12 + £12 + £8 = £32 altogether.
  3. [open_response · evaluate] You arrive at the zoo at 15:30. Can you still go in? Why or why not?
     Lösung: No. The last entry is at 16:00, so 15:30 is fine to go in - yes, you can still go in, because it is before 16:00.
  4. [text_production · apply] Write a short message to a friend. Tell them when the zoo opens and one feeding time you want to see.
     Lösung: Modelltext: „Hi! Let's go to Sunnyfield Zoo on Saturday. It opens at 09:00. I want to see the penguins at 11:00. See you there!“ (kurze, korrekte Saetze; eine Uhrzeit aus dem Text).
  5. [speaking_task · apply] Work in pairs. Act out buying tickets at the zoo ticket desk.
     Lösung: Erwartet: Besucher:in begruesst, fragt nach Karten („Can I have...?“, „How much is...?“) und nach der Fuetterungszeit; Personal nennt die Preise von der Tafel (Adult: £12, Child: £8) und „15:00“ fuer die Affenfuetterung, reagiert hoeflich.

### item `c0012` — „Zweite lebende Fremdsprache 3. Kl. — Boulangerie du Coin“ (Zweite lebende Fremdsprache, 3. Kl. · Stufe voll)
- Kernfrage: À la boulangerie — verstehen und sprechen
- Aufgaben:
  1. [open_response · understand] Combien coûte un croissant ?
     Lösung: 1,20 €.
  2. [open_response · analyze] Tu as 5 €. Est-ce que tu peux acheter une tarte aux pommes ET un éclair au chocolat ? Pourquoi ?
     Lösung: Non : 3,00 € + 2,80 € = 5,80 €, et c'est plus de 5 €.
  3. [open_response · evaluate] Ton ami n'aime pas le chocolat. Qu'est-ce que tu recommandes ? Pourquoi ?
     Lösung: La baguette (1,10 €), le croissant (1,20 €) ou la tarte aux pommes (3,00 €) — il n'y a pas de chocolat, mais le pain au chocolat et l'éclair au chocolat en ont.
  4. [text_production · apply] Tu as 4 €. Écris une petite commande à la boulangère : choisis deux produits de la carte et écris le total.
     Lösung: Modelltext: „Bonjour ! Je voudrais un croissant et un pain au chocolat, s'il vous plaît. Ça fait 1,20 € + 1,50 € = 2,70 €. Merci !“ (zwei Produkte von der Karte; Summe gezeigt; kurze, korrekte A1-Sätze).
  5. [speaking_task · apply] Travaillez à deux. Jouez la scène à la boulangerie.
     Lösung: Erwartet: Kund:in grüßt, bestellt („Je voudrais …“, „Je prends …“) und fragt nach dem Preis („Ça fait combien ?“); Bäckerin nennt den Preis von der Karte (z. B. „Ça fait 1,20 €.“) und reagiert höflich („Voilà“, „Bonne journée !“). Eine Summe darf gebildet werden.

### item `c0013` — „Zweite lebende Fremdsprache 4. Kl. — Horaire de bus - Ligne 5“ (Zweite lebende Fremdsprache, 4. Kl. · Stufe voll)
- Kernfrage: Les horaires de bus — verstehen und sprechen
- Aufgaben:
  1. [open_response · understand] A quelle heure part le bus pour la Gare le matin ?
     Lösung: A 09:00.
  2. [open_response · analyze] Tu veux aller a la plage et tu dois etre la-bas avant 14:00. Quel bus prends-tu ? Pourquoi tu ne prends pas le bus suivant pour la plage ?
     Lösung: Tu prends le bus de 13:20 pour la Plage. Le bus suivant pour la plage part a 14:50, donc apres 14:00 - tu arrives trop tard.
  3. [text_production · apply] Ton amie veut aller a la plage avec toi cet apres-midi. Ecris-lui un petit message (3-4 phrases) : dis quel bus vous prenez, a quelle heure il part et ou est l'arret.
     Lösung: Modelltext: „Salut ! Cet apres-midi, on prend le bus de la Ligne 5 pour la plage. Il part a 13:20 a l'arret Place du Marche. A bientot !“ (3-4 einfache Sätze; Uhrzeit + Haltestelle aus dem Fahrplan; korrektes, einfaches A2-French).
  4. [speaking_task · apply] Travaillez a deux. Jouez une petite scene a l'arret de bus : un voyageur demande une information au chauffeur.
     Lösung: Erwartet: A fragt z. B. „Pardon, a quelle heure part le bus pour la plage ?“, „C'est quelle ligne ?“; B antwortet mit Uhrzeit + Linie aus dem Plan (13:20, Ligne 5). Nützliche Wendungen: „Pardon / Excusez-moi…“, „Le prochain bus part a…“, „C'est la Ligne 5“, „Bon voyage !“

### item `c0014` — „Erste lebende Fremdsprache 3. Kl. — Now Showing at the Star Cinema“ (Erste lebende Fremdsprache, 3. Kl. · Stufe voll)
- Kernfrage: Im Kino — verstehen und sprechen
- Aufgaben:
  1. [open_response · understand] What time does the film Football Heroes start?
     Lösung: At 20:00.
  2. [open_response · analyze] You only have £8 and you must be inside the cinema by 21:00. You want to see the LATEST film you can. Which film do you choose? Say why (one sentence in English).
     Lösung: Football Heroes. Erwartet z.B.: "I choose Football Heroes. It starts at 20:00 (before 21:00) and the ticket is £7.50, so I have enough money." (The Dark Forest faellt weg: Beginn 21:15 ist nach 21:00.)
  3. [text_production · apply] You have £15 for two tickets. Text a friend: suggest TWO films you can see today and write the total price. (3-4 sentences in English.)
     Lösung: Modelltext: „Hi! Let's go to the cinema today. We can see The Lost Robot and then Football Heroes. That is £6.00 + £7.50 = £13.50 for two tickets, so we have enough. See you there!“ (zwei Filme von der Tafel; Summe gezeigt; kurze, korrekte Saetze).
  4. [speaking_task · apply] Work in pairs at the box office. One of you buys a ticket, the other one sells it. Then swap roles.
     Lösung: Erwartet: A - "Hello! One ticket for Football Heroes, please. What time does it start? How much is it?" B - "Hello! It starts at 20:00 and the ticket is £7.50, please. Enjoy the film!" (Nuetzliche Wendungen: One ticket, please. / What time ...? / How much is it? / Here you are. / Enjoy the film!)

### arrangement `gwb-standort` — „Wohin mit dem neuen Verteilzentrum?“ (Geographie und wirtschaftliche Bildung, 3. Kl. · Stufe voll)

### item `c0004` — „Biologie 4. Kl. — Immunsystem und Impfungen“ (Biologie, 4. Kl. · Stufe voll)
- Kernfrage: Was hilft gegen einen Erreger – und warum hilft es manchmal gerade nicht?
- Aufgaben:
  1. [open_response · understand] Jemand mit einer normalen Erkältung (durch Viren ausgelöst) verlangt vom Arzt ein Antibiotikum. Erkläre in eigenen Worten, warum das Antibiotikum hier nicht helfen kann – und beziehe dich dabei auf den Unterschied zwischen Viren und Bakterien.
     Lösung: Antibiotika greifen Strukturen/Stoffwechsel bakterieller Zellen an (z. B. Zellwand). Viren sind keine Zellen und besitzen diese Angriffspunkte nicht; sie vermehren sich in körpereigenen Zellen. Daher kann ein Antibiotikum den Virus nicht treffen – gegen die Erkältung hilft das eigene Immunsystem.
  2. [open_response · apply] Modell 'Immungedächtnis': Beim ersten Kontakt mit einem Erreger reagiert der Körper langsam; danach merkt er sich den Erreger und reagiert beim nächsten Mal schnell und stark. Erkläre mit diesem Modell, (a) warum eine Impfung schützt, obwohl man dabei nicht richtig krank wird, und (b) nenne EINE Gr…
     Lösung: —
  3. [data_interpretation · apply] Im Schullabor habt ihr (vereinfacht) den Antikörper-Spiegel im Blut nach einer Impfung über die Zeit aufgenommen. Messwerte (relative Einheiten): Tag 0 → 1 · Tag 7 → 3 · Tag 14 → 9 · Tag 28 → 8 · nach Auffrischung an Tag 60 → 30. Beschreibe den Verlauf, benenne den Effekt der Auffrischung und erklä…
     Lösung: Erstkontakt: langsamer Anstieg (Tag 7–14), dann leichtes Absinken (Tag 28). Die Auffrischung führt zu einem viel höheren, schnelleren Anstieg (30) – Beleg für das Immungedächtnis: Der Körper 'kennt' das Antigen schon und reagiert kräftiger. Größenordnungen vergleichen, nicht Einzelwerte.
  4. [true_false_justify · analyze] Vier Aussagen aus einer Internetdiskussion über Impfungen. Entscheide jeweils, ob die Aussage naturwissenschaftlich überprüfbar ist oder nicht, und begründe kurz (es geht NICHT darum, ob sie dir gefällt).
     Lösung: 1 ja (empirisch prüfbar: Daten, Häufigkeiten) · 2 nein ('unnatürlich → falsch' ist ein Werturteil/Naturalistischer Fehlschluss, nicht messbar) · 3 ja (Menge ist messbar) · 4 nein (Unterstellung über Motive, kein naturwissenschaftlicher Satz).
  5. [open_response · analyze] In einem Krankenhaus tauchen plötzlich Bakterien auf, gegen die ein bestimmtes Antibiotikum kaum noch wirkt. Erkläre Schritt für Schritt, wie so eine Antibiotikaresistenz entsteht – verwende dabei die Begriffe 'zufällige Veränderung (Mutation)', 'Selektion' und 'Vermehrung'. Warum ist das ein Beisp…
     Lösung: —
  6. [decision_scenario · evaluate] Ein Familienmitglied sagt: 'Mir geht es nach drei Tagen schon besser, ich höre mit dem Antibiotikum jetzt auf und hebe den Rest für das nächste Mal auf.' Beurteile beide Teile dieser Entscheidung fachlich und gib eine begründete Empfehlung. Verknüpfe deine Begründung mit dem, was du über Resistenze…
     Lösung: —
  … + 1 weitere Aufgaben

### dataset `geosphere_klima_normal_1991_2020` — „Klimanormalwerte österreichischer Stationen (1991–2020)“ (— · Stufe quelle)

### dataset `statistik_austria_bevstand_2024` — „Bevölkerung Österreichs nach Alter und Geschlecht (1.1.2024)“ (— · Stufe quelle)

### dataset `statistik_austria_bundeslaender_2024` — „Bevölkerung der österreichischen Bundesländer (1.1.2024)“ (— · Stufe quelle)

### dataset `worldbank_at_alterung` — „Anteil der über 65-Jährigen in Österreich“ (— · Stufe quelle)

### dataset `worldbank_at_bevoelkerung` — „Bevölkerung Österreichs im Zeitverlauf“ (— · Stufe quelle)

### dataset `worldbank_bip_pro_kopf` — „BIP pro Kopf im Ländervergleich“ (— · Stufe quelle)

### dataset `worldbank_co2_pro_kopf` — „CO₂-Ausstoß pro Kopf im Ländervergleich“ (— · Stufe quelle)

### dataset `worldbank_urbanisierung` — „Verstädterung im Ländervergleich (Anteil Stadtbevölkerung)“ (— · Stufe quelle)

### text `fs-realie-weather` — „This week's weather in Greenhaven“ (Erste lebende Fremdsprache, 3. Kl. · Stufe sprache)

### text `fs-realie-zoo` — „Sunnyfield Zoo“ (Erste lebende Fremdsprache, 2. Kl. · Stufe sprache)

### text `fs-realie-boulangerie` — „Boulangerie du Coin“ (Zweite lebende Fremdsprache, 3. Kl. · Stufe sprache)

### text `fs-realie-bus` — „Horaire de bus - Ligne 5“ (Zweite lebende Fremdsprache, 4. Kl. · Stufe sprache)

### text `fs-realie-cinema` — „Now Showing at the Star Cinema“ (Erste lebende Fremdsprache, 3. Kl. · Stufe sprache)

### text `fs-realie-invitation` — „You're Invited! Tom's Birthday Party“ (Erste lebende Fremdsprache, 1. Kl. · Stufe sprache)

### item `c0011` — „Biologie und Umweltbildung 2. Kl. — Die Verdauung des Menschen“ (Biologie und Umweltbildung, 2. Kl. · Stufe sprache)
- Kernfrage: Welchen Weg nimmt das Essen — und was passiert auf jeder Station?
- Aufgaben:
  1. [ordering · remember] Bringe die Schritte von „Der Weg der Nahrung“ in die richtige Reihenfolge.
     Lösung: Mund → Speiseröhre → Magen → Dünndarm → Dickdarm → Ausscheidung
  2. [cause_effect_match · analyze] Ordne jeder Ursache die passende Folge zu.
     Lösung: Die Zähne zerkleinern die Nahrung → es entsteht eine größere Oberfläche, an der die Verdauungssäfte angreifen können; Der Speichel durchfeuchtet den Bissen und enthält ein Enzym → die Nahrung wird gleitfähig und die Stärke wird schon im Mund angedaut; Der Magen mischt die Nahrung mit saurem Magensa…
  3. [concept_match · understand] Ordne jedem Begriff die richtige Erklärung zu.
     Lösung: Verdauung: die Zerlegung der Nahrung in so winzige Bausteine, dass der Körper sie aufnehmen und nutzen kann; Enzym: ein Eiweißstoff, der die Nahrung in ihre kleinen Bausteine zerlegt — wie ein winziges Werkzeug; Nährstoff: ein verwertbarer Baustein der Nahrung wie Kohlenhydrate, Eiweiß oder Fett, d…
  4. [content_comprehension · understand] Erkläre in eigenen Worten, wie „Der Weg der Nahrung“ abläuft und warum das wichtig ist.
     Lösung: Erst die Verdauung macht aus dem Essen das, was der Körper wirklich brauchen kann: Sie zerlegt jede Mahlzeit in winzige Nährstoffe und nimmt sie ins Blut auf. So bekommt jede Zelle Energie und Bausteine zum Wachsen, Bewegen und Reparieren. Ohne diesen Weg durch Mund, Magen und Darm könnten wir aus …
  5. [structure_overview · understand] Nenne die wichtigsten Strukturen und beschreibe kurz, wodurch sie sich auszeichnen.
     Lösung: Mund: hier beginnt die Verdauung: die Zähne zerkleinern die Nahrung, der Speichel macht sie gleitfähig und beginnt, die Stärke zu zersetzen; Speiseröhre: ein muskulöser Schlauch, der den Speisebrei durch wellenförmige Bewegungen vom Mund in den Magen schiebt; Magen: ein muskulöser Sack, der die Nah…
  6. [open_response · evaluate] „Hauptsache, es schmeckt — was gesund ist, kann mir egal sein.“ Nimm zu dieser Aussage Stellung: Welche Rolle spielt eine ausgewogene Ernährung für eine gut funktionierende Verdauung und unsere Gesundheit? Begründe deinen Standpunkt und überlege, was du selbst dafür tun kannst.
     Lösung: —

### item `c0010` — „Biologie und Umweltbildung 3. Kl. — Die Photosynthese“ (Biologie und Umweltbildung, 3. Kl. · Stufe sprache)
- Kernfrage: Wie macht eine Pflanze aus Licht, Wasser und Luft ihre Nahrung?
- Aufgaben:
  1. [ordering · remember] Bringe die Schritte von „Wie eine Pflanze Nahrung herstellt“ in die richtige Reihenfolge.
     Lösung: Sonnenlicht trifft das Blatt → Chlorophyll fängt das Licht ein → Wasser und Kohlenstoffdioxid kommen an → Lichtenergie treibt den Aufbau an → Traubenzucker wird aufgebaut → Sauerstoff wird abgegeben
  2. [cause_effect_match · analyze] Ordne jeder Ursache die passende Folge zu.
     Lösung: Sonnenlicht trifft auf das grüne Blatt → das Chlorophyll kann Lichtenergie einfangen; Die Wurzel nimmt Wasser aus dem Boden auf → in den Blättern steht Wasser als Baustoff bereit; Die Spaltöffnungen sind geöffnet → Kohlenstoffdioxid aus der Luft gelangt ins Blatt; Lichtenergie treibt den Aufbau in …
  3. [concept_match · understand] Ordne jedem Begriff die richtige Erklärung zu.
     Lösung: Photosynthese: der Vorgang, bei dem grüne Pflanzen mit Hilfe von Licht aus Wasser und Kohlenstoffdioxid Traubenzucker aufbauen und dabei Sauerstoff abgeben; Chlorophyll: der grüne Farbstoff der Pflanze, der das Sonnenlicht einfängt und seine Energie nutzbar macht; Chloroplast: das winzige grüne Kör…
  4. [content_comprehension · understand] Erkläre in eigenen Worten, wie „Wie eine Pflanze Nahrung herstellt“ abläuft und warum das wichtig ist.
     Lösung: Die Photosynthese ist die Grundlage fast allen Lebens auf der Erde: Pflanzen sind die einzigen Lebewesen, die aus Licht, Wasser und Luft selbst Nahrung aufbauen können. Von diesem Traubenzucker ernähren sich am Ende auch Tiere und Menschen. Gleichzeitig liefert die Photosynthese den Sauerstoff, den…
  5. [structure_overview · understand] Nenne die wichtigsten Strukturen und beschreibe kurz, wodurch sie sich auszeichnen.
     Lösung: Blatt: der grüne, meist flache Pflanzenteil, in dem die Photosynthese hauptsächlich abläuft; Chloroplast: winziges grünes Körperchen in den Blattzellen, in dem die Photosynthese stattfindet; Chlorophyll: der grüne Farbstoff in den Chloroplasten, der das Sonnenlicht einfängt; Spaltöffnungen: winzige…
  6. [open_response · evaluate] „Wälder zu schützen ist eine der wirksamsten Maßnahmen gegen den Klimawandel.“ Nimm zu dieser Aussage Stellung: Warum ist es für das Klima und die Luft so wichtig, dass Pflanzen Photosynthese betreiben? Begründe deinen Standpunkt und überlege, was jede und jeder selbst für mehr Grün tun kann.
     Lösung: —

### sachverhalt `sv-verdauung` — „Die Verdauung des Menschen“ (Biologie und Umweltbildung, 2. Kl. · Stufe sprache)

### sachverhalt `sv-photosynthese` — „Die Photosynthese“ (Biologie und Umweltbildung, 3. Kl. · Stufe sprache)

### sachverhalt `sv-industrialisierung` — „Die Industrialisierung“ (Geschichte und politische Bildung, 3. Kl. · Stufe sprache)

### sachverhalt `sv-franzoesische-revolution` — „Die Französische Revolution“ (Geschichte und politische Bildung, 3. Kl. · Stufe sprache)

### item `c0007` — „Der Wiener Kongress“ (Geschichte und politische Bildung, 3. Kl. · Stufe sprache)
- Kernfrage: Wie ordnet der Wiener Kongress Europa neu — und woher wissen wir das?
- Aufgaben:
  1. [ordering · remember] Bringe die drei Ereignisse in die richtige zeitliche Reihenfolge.
     Lösung: 1. Niederlage Napoleons → 2. Beginn des Wiener Kongresses (1814/15) → 3. Gründung des Deutschen Bundes (Bundesakte, 8. Juni 1815).
  2. [source_analysis · analyze] Der verlinkte Wikipedia-Artikel „Wiener Kongress“ ist eine Darstellung — ein späterer, zusammenfassender Bericht, keine Quelle aus der Zeit. Untersuche ihn: (a) Nach welchem Leitprinzip wird Europa neu geordnet? (b) Woran erkennst du, dass es sich um eine Darstellung und nicht um eine Quelle handel…
     Lösung: (a) Gleichgewicht der Mächte. (b) Merkmale einer Darstellung: rückblickende Einordnung und Wertung (z. B. „Restauration“, „Epoche“), Zusammenfassung über lange Zeiträume, keine zeitgenössische Stimme, belegende Verweise/Literatur.
  3. [source_analysis · analyze] Lies Quelle 1 (Auszug aus der Deutschen Bundesakte von 1815). (a) Welches Ziel der Fürsten wird darin ausdrücklich genannt? Belege mit einer Wendung aus dem Text. (b) Welches Wort im Text passt zum Leitprinzip des Kongresses aus dem Lerntext?
     Lösung: (a) Sich „zu einem beständigen Bunde zu vereinigen“ — zur Sicherheit und Unabhängigkeit sowie zur „Ruhe“. (b) „Gleichgewicht“ (Europa's) — dasselbe Leitprinzip, das der Lerntext nennt.
  4. [open_response · analyze] Vergleiche Quelle 1 (Bundesakte, 1815) mit dem Wikipedia-Artikel (Darstellung): Was kann dir die Quelle sagen, was die Darstellung NICHT kann — und umgekehrt? Gib je ein Beispiel.
     Lösung: —
  5. [position_argument · evaluate] „Der Wiener Kongress brachte vor allem Stabilität.“ Nimm zu dieser Aussage Stellung: Was spricht dafür, was dagegen (denke an die zurückgekehrten Fürsten und an die Menschen, die sich mehr Mitbestimmung wünschten)? Begründe am Ende dein eigenes Urteil.
     Lösung: —

### text `deu-loreley` — „Die Lore-Ley“ (Deutsch, 3. Kl. · Stufe sprache)

### text `deu-rabe-fuchs` — „Der Rabe und der Fuchs“ (Deutsch, 2. Kl. · Stufe sprache)

### text `fs1-mia-schoolday` — „Mia's school day“ (Erste lebende Fremdsprache, 2. Kl. · Stufe sprache)

### text `lat-vulpes-corvus` — „Vulpes et Corvus“ (Latein, 4. Kl. · Stufe sprache)

### sachverhalt `sv-wiener-kongress` — „Der Wiener Kongress“ (Geschichte und politische Bildung, 3. Kl. · Stufe sprache)

### asset `kit-badge-deu` — „kit-badge-deu“ (— · Stufe bestaetigen)

### asset `kit-badge-gwb` — „kit-badge-gwb“ (— · Stufe bestaetigen)

### asset `kit-badge-mat` — „kit-badge-mat“ (— · Stufe bestaetigen)

### asset `kit-badge-phy` — „kit-badge-phy“ (— · Stufe bestaetigen)

### asset `kit-banner-cool` — „kit-banner-cool“ (— · Stufe bestaetigen)

### asset `kit-banner-warm` — „kit-banner-warm“ (— · Stufe bestaetigen)

### asset `kit-motif-blue` — „kit-motif-blue“ (— · Stufe bestaetigen)

### asset `kit-motif-green` — „kit-motif-green“ (— · Stufe bestaetigen)

### item `c0162` — „Chemie 4. Kl. — Reinstoff oder Gemisch? (6 Varianten)“ (Chemie, 4. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Reinstoff oder Gemisch?
- Aufgaben:
  1. [open_response · apply] Ordne den folgenden Stoff ein: Ist Wasserstoff (H₂) ein Element, eine Verbindung oder ein Gemisch? Begründe deine Entscheidung.
     Lösung: Element
  2. [open_response · apply] Ordne den folgenden Stoff ein: Ist Eisen (Fe) ein Element, eine Verbindung oder ein Gemisch? Begründe deine Entscheidung.
     Lösung: Element
  3. [open_response · apply] Ordne den folgenden Stoff ein: Ist Stickstoff (N₂) ein Element, eine Verbindung oder ein Gemisch? Begründe deine Entscheidung.
     Lösung: Element
  4. [open_response · apply] Ordne den folgenden Stoff ein: Ist Mineralwasser ein Element, eine Verbindung oder ein Gemisch? Begründe deine Entscheidung.
     Lösung: Gemisch
  5. [open_response · apply] Ordne den folgenden Stoff ein: Ist Granit ein Element, eine Verbindung oder ein Gemisch? Begründe deine Entscheidung.
     Lösung: Gemisch
  6. [open_response · apply] Ordne den folgenden Stoff ein: Ist Kohlenstoffdioxid (CO₂) ein Element, eine Verbindung oder ein Gemisch? Begründe deine Entscheidung.
     Lösung: Verbindung

### item `c0163` — „Chemie 4. Kl. — Trennverfahren wählen (6 Varianten)“ (Chemie, 4. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Trennverfahren wählen
- Aufgaben:
  1. [open_response · apply] Mit welchem Trennverfahren lässt sich das Gemisch „Eisenspäne und Sand“ trennen? Erkläre, welche Eigenschaft der Bestandteile dabei genutzt wird.
     Lösung: Magnetscheidung (mit einem Magneten)
  2. [open_response · apply] Mit welchem Trennverfahren lässt sich das Gemisch „Sand und Wasser“ trennen? Erkläre, welche Eigenschaft der Bestandteile dabei genutzt wird.
     Lösung: Filtrieren
  3. [open_response · apply] Mit welchem Trennverfahren lässt sich das Gemisch „Alkohol und Wasser“ trennen? Erkläre, welche Eigenschaft der Bestandteile dabei genutzt wird.
     Lösung: Destillation
  4. [open_response · apply] Mit welchem Trennverfahren lässt sich das Gemisch „Sand und Kies (verschiedene Korngrößen)“ trennen? Erkläre, welche Eigenschaft der Bestandteile dabei genutzt wird.
     Lösung: Sieben
  5. [open_response · apply] Mit welchem Trennverfahren lässt sich das Gemisch „Salz in Wasser gelöst“ trennen? Erkläre, welche Eigenschaft der Bestandteile dabei genutzt wird.
     Lösung: Eindampfen (Verdampfen des Wassers)
  6. [open_response · apply] Mit welchem Trennverfahren lässt sich das Gemisch „Öl und Wasser“ trennen? Erkläre, welche Eigenschaft der Bestandteile dabei genutzt wird.
     Lösung: Dekantieren / Scheidetrichter

### item `c0164` — „Chemie 4. Kl. — Reaktionstyp bestimmen (6 Varianten)“ (Chemie, 4. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Reaktionstyp bestimmen
- Aufgaben:
  1. [open_response · apply] Bestimme den Reaktionstyp der folgenden Reaktion: 2 H₂O → 2 H₂ + O₂. Begründe deine Zuordnung.
     Lösung: Analyse (Zersetzung)
  2. [open_response · apply] Bestimme den Reaktionstyp der folgenden Reaktion: Fe + S → FeS. Begründe deine Zuordnung.
     Lösung: Synthese (Vereinigung)
  3. [open_response · apply] Bestimme den Reaktionstyp der folgenden Reaktion: CaCO₃ → CaO + CO₂. Begründe deine Zuordnung.
     Lösung: Analyse (Zersetzung)
  4. [open_response · apply] Bestimme den Reaktionstyp der folgenden Reaktion: 2 HgO → 2 Hg + O₂. Begründe deine Zuordnung.
     Lösung: Analyse (Zersetzung)
  5. [open_response · apply] Bestimme den Reaktionstyp der folgenden Reaktion: N₂ + 3 H₂ → 2 NH₃. Begründe deine Zuordnung.
     Lösung: Synthese (Vereinigung)
  6. [open_response · apply] Bestimme den Reaktionstyp der folgenden Reaktion: CH₄ + 2 O₂ → CO₂ + 2 H₂O. Begründe deine Zuordnung.
     Lösung: Verbrennung (Oxidation)

### item `c0165` — „Chemie 4. Kl. — Atome auf der Teilchenebene zählen (6 Varianten)“ (Chemie, 4. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Atome auf der Teilchenebene zählen
- Aufgaben:
  1. [open_response · apply] Wie viele Atome jeder Sorte enthält ein Molekül NH₃? Wie viele Atome sind es insgesamt?
     Lösung: N: 1, H: 3 — insgesamt 4 Atome
  2. [open_response · apply] Wie viele Atome jeder Sorte enthält ein Molekül H₂O? Wie viele Atome sind es insgesamt?
     Lösung: H: 2, O: 1 — insgesamt 3 Atome
  3. [open_response · apply] Wie viele Atome jeder Sorte enthält ein Molekül CH₄? Wie viele Atome sind es insgesamt?
     Lösung: C: 1, H: 4 — insgesamt 5 Atome
  4. [open_response · apply] Wie viele Atome jeder Sorte enthält ein Molekül HNO₃? Wie viele Atome sind es insgesamt?
     Lösung: H: 1, N: 1, O: 3 — insgesamt 5 Atome
  5. [open_response · apply] Wie viele Atome jeder Sorte enthält ein Molekül CaCO₃? Wie viele Atome sind es insgesamt?
     Lösung: Ca: 1, C: 1, O: 3 — insgesamt 5 Atome
  6. [open_response · apply] Wie viele Atome jeder Sorte enthält ein Molekül NaCl? Wie viele Atome sind es insgesamt?
     Lösung: Na: 1, Cl: 1 — insgesamt 2 Atome

### item `c0166` — „Chemie 4. Kl. — Sauer, basisch oder neutral? (6 Varianten)“ (Chemie, 4. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Sauer, basisch oder neutral?
- Aufgaben:
  1. [open_response · apply] Ist die Lösung von „Magensaft“ sauer, basisch oder neutral? Begründe deine Einschätzung.
     Lösung: sauer
  2. [open_response · apply] Ist die Lösung von „Zitronensaft“ sauer, basisch oder neutral? Begründe deine Einschätzung.
     Lösung: sauer
  3. [open_response · apply] Ist die Lösung von „Salzsäure“ sauer, basisch oder neutral? Begründe deine Einschätzung.
     Lösung: sauer
  4. [open_response · apply] Ist die Lösung von „reines Wasser“ sauer, basisch oder neutral? Begründe deine Einschätzung.
     Lösung: neutral
  5. [open_response · apply] Ist die Lösung von „Seifenlauge“ sauer, basisch oder neutral? Begründe deine Einschätzung.
     Lösung: basisch
  6. [open_response · apply] Ist die Lösung von „Rohrreiniger“ sauer, basisch oder neutral? Begründe deine Einschätzung.
     Lösung: basisch

### item `c0159` — „Chemie 7. Kl. — Molare Masse einer Verbindung (6 Varianten)“ (Chemie, 7. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Molare Masse einer Verbindung
- Aufgaben:
  1. [calculation · apply] Berechne die molare Masse der Verbindung CaCO₃. Verwende die Atommassen aus dem Periodensystem.
     Lösung: M(CaCO₃) ≈ 100,09 g/mol
  2. [calculation · apply] Berechne die molare Masse der Verbindung CO₂. Verwende die Atommassen aus dem Periodensystem.
     Lösung: M(CO₂) ≈ 44,01 g/mol
  3. [calculation · apply] Berechne die molare Masse der Verbindung HCl. Verwende die Atommassen aus dem Periodensystem.
     Lösung: M(HCl) ≈ 36,46 g/mol
  4. [calculation · apply] Berechne die molare Masse der Verbindung HCl. Verwende die Atommassen aus dem Periodensystem.
     Lösung: M(HCl) ≈ 36,46 g/mol
  5. [calculation · apply] Berechne die molare Masse der Verbindung C₂H₅OH. Verwende die Atommassen aus dem Periodensystem.
     Lösung: M(C₂H₅OH) ≈ 46,07 g/mol
  6. [calculation · apply] Berechne die molare Masse der Verbindung Na₂CO₃. Verwende die Atommassen aus dem Periodensystem.
     Lösung: M(Na₂CO₃) ≈ 105,99 g/mol

### item `c0160` — „Chemie 7. Kl. — Reaktionsgleichung ausgleichen (6 Varianten)“ (Chemie, 7. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Reaktionsgleichung ausgleichen
- Aufgaben:
  1. [calculation · apply] Gleiche die folgende Reaktionsgleichung aus (Massenerhaltung): Fe + O₂ → Fe₂O₃
     Lösung: 4 Fe + 3 O₂ → 2 Fe₂O₃
  2. [calculation · apply] Gleiche die folgende Reaktionsgleichung aus (Massenerhaltung): H₂ + O₂ → H₂O
     Lösung: 2 H₂ + O₂ → 2 H₂O
  3. [calculation · apply] Gleiche die folgende Reaktionsgleichung aus (Massenerhaltung): CH₄ + O₂ → CO₂ + H₂O
     Lösung: CH₄ + 2 O₂ → CO₂ + 2 H₂O
  4. [calculation · apply] Gleiche die folgende Reaktionsgleichung aus (Massenerhaltung): CH₄ + O₂ → CO₂ + H₂O
     Lösung: CH₄ + 2 O₂ → CO₂ + 2 H₂O
  5. [calculation · apply] Gleiche die folgende Reaktionsgleichung aus (Massenerhaltung): C₂H₆ + O₂ → CO₂ + H₂O
     Lösung: 2 C₂H₆ + 7 O₂ → 4 CO₂ + 6 H₂O
  6. [calculation · apply] Gleiche die folgende Reaktionsgleichung aus (Massenerhaltung): C₂H₆ + O₂ → CO₂ + H₂O
     Lösung: 2 C₂H₆ + 7 O₂ → 4 CO₂ + 6 H₂O

### item `c0161` — „Chemie 7. Kl. — Stöchiometrische Massenberechnung (6 Varianten)“ (Chemie, 7. Kl. · Stufe bestaetigen)
- ⚠ Anforderungsniveau flach: alle 6 Aufgaben auf 'mittel (Transfer)' — kein Spektrum
- Kernfrage: Übung: Stöchiometrische Massenberechnung
- Aufgaben:
  1. [calculation · apply] Bei der Reaktion 4 Fe + 3 O₂ → 2 Fe₂O₃ werden 5 g Fe vollständig umgesetzt. Berechne die Masse an Fe₂O₃, die dabei entsteht.
     Lösung: m(Fe₂O₃) ≈ 7,15 g
  2. [calculation · apply] Bei der Reaktion 2 H₂ + O₂ → 2 H₂O werden 20 g H₂ vollständig umgesetzt. Berechne die Masse an H₂O, die dabei entsteht.
     Lösung: m(H₂O) ≈ 178,72 g
  3. [calculation · apply] Bei der Reaktion CH₄ + 2 O₂ → CO₂ + 2 H₂O werden 40 g CH₄ vollständig umgesetzt. Berechne die Masse an H₂O, die dabei entsteht.
     Lösung: m(H₂O) ≈ 89,83 g
  4. [calculation · apply] Bei der Reaktion CH₄ + 2 O₂ → CO₂ + 2 H₂O werden 25 g O₂ vollständig umgesetzt. Berechne die Masse an CO₂, die dabei entsteht.
     Lösung: m(CO₂) ≈ 17,19 g
  5. [calculation · apply] Bei der Reaktion 2 C₂H₆ + 7 O₂ → 4 CO₂ + 6 H₂O werden 50 g O₂ vollständig umgesetzt. Berechne die Masse an H₂O, die dabei entsteht.
     Lösung: m(H₂O) ≈ 24,13 g
  6. [calculation · apply] Bei der Reaktion 2 C₂H₆ + 7 O₂ → 4 CO₂ + 6 H₂O werden 16 g C₂H₆ vollständig umgesetzt. Berechne die Masse an H₂O, die dabei entsteht.
     Lösung: m(H₂O) ≈ 28,76 g
