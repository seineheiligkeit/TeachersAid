# Review-Triage: adversarialer Durchgang über die Prüf-Warteschlange

Du bist ein **strenger Fachdidaktiker / eine strenge Fachdidaktikerin** (AHS, Österreich).
Unten stehen **201 Einträge**, die zur fachlichen Prüfung anstehen. Beurteile jeden
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

## Einträge (201)

### item `c0195` — „Chemie 4. Kl. — Vom Wertstoffhof zum Trinkwasser — Stoffe trennen (generiert)“ (Chemie, 4. Kl. · Stufe voll)
- Kernfrage: Wie trennst du Stoffgemische wieder in ihre Bestandteile — und warum reicht dafür nicht immer dieselbe Methode?
- Aufgaben:
  1. [matching · remember] Im Chemieunterricht wurden fünf Trennverfahren an fünf verschiedenen Gemischen ausprobiert. Ordne jedem Trennverfahren das Gemisch zu, für das es tatsächlich geeignet ist. Ordne außerdem in Gedanken zu, WELCHE Eigenschaft der beiden Stoffe jeweils genutzt wird (das hilft dir bei den späteren Aufgab…
     Lösung: Filtrieren → Sand aus trübem Bachwasser entfernen (fest/flüssig, unlöslicher Feststoff bleibt im Filter). Dekantieren → Ölfilm von der Wasseroberfläche abgießen (unterschiedliche Dichte, keine Vermischung). Eindampfen → Kochsalz aus Salzwasser gewinnen (Wasser verdampft bei 100 °C, Salz bleibt als …
  2. [true_false_justify · understand] Im Wertstoffhof deiner Gemeinde läuft der Restmüll über ein Förderband mit einem großen Magneten darüber, bevor der Rest weiter zur Sortieranlage transportiert wird. Beurteile folgende Aussagen dazu als richtig (R) oder falsch (F) und begründe kurz.
     Lösung: 1. RICHTIG. Eisen und Stahl sind ferromagnetisch und werden vom Magneten angezogen. 2. FALSCH. Aluminium ist nicht magnetisch; Aludosen bleiben auf dem Förderband liegen (sie werden in echten Anlagen mit einem Wirbelstromscheider getrennt, nicht mit einem einfachen Magneten). 3. RICHTIG. Magnetsche…
  3. [data_interpretation · analyze] Ein Trinkwasser-Notfallteam testet nach einem Unwetter drei mögliche Reinigungsverfahren an demselben trüben, salzhaltigen Flusswasser. Zusätzlich zu den gelösten Salzen enthält das Wasser auch Schwebstoffe (Sand, Schlamm): Filtrieren entfernt davon etwa 95 %, Dekantieren nur etwa 40 % (nur was sic…
     Lösung: Filtrieren entfernt fast alle Schwebstoffe (ca. 95 %), aber praktisch keine gelösten Salze (ca. 2 %) — ein Filter hält nur feste, ungelöste Teilchen zurück, gelöste Salzteilchen passen durch die Filterporen. Destillieren entfernt fast alle gelösten Salze (ca. 98 %) UND fast alle Schwebstoffe (ca. 9…
  4. [experiment_protocol · apply] Aufgabe: In einem Eimer landet versehentlich ein Gemisch aus drei Stoffen: Sand, Kochsalz und Wasser (Sand und Salz sind beide fest, aber Sand löst sich NICHT in Wasser, Salz schon). Plane ein zweistufiges Trennverfahren, mit dem du am Ende drei getrennte Stoffe erhältst: trockenen Sand, trockenes …
     Lösung: Schritt 1 — Filtrieren: Das Gemisch wird durch einen Filter gegossen. Der Sand (unlöslicher Feststoff) bleibt im Filter zurück, Salzwasser (gelöstes Salz + Wasser) läuft durch. Ergebnis: trockener Sand ist bereits abgetrennt. Schritt 2 — Eindampfen: Die durchgelaufene Salzwasser-Lösung wird erhitzt…
  5. [decision_scenario · evaluate] Eine kleine Insel-Gemeinde hat kein natürliches Süßwasser und muss ihr Trinkwasser aus Meerwasser gewinnen. Der Gemeinderat prüft zwei Verfahren: (A) Destillation — das Meerwasser wird mit Sonnenenergie erhitzt, der Dampf in Rohren aufgefangen und abgekühlt. (B) Einfaches Filtrieren durch feinste F…
     Lösung: Die Aussage des Technikers ist fachlich richtig: Salz ist im Meerwasser gelöst, also in einzelne, extrem kleine Teilchen (Ionen) aufgeteilt — kein Filter, egal wie fein, kann gelöste Teilchen von den Wasserteilchen trennen, weil Filter nur ungelöste (feste) Teilchen zurückhalten. Empfehlung: Verfah…
  6. [source_critique · analyze] In einem Online-Forum schreibt jemand: «Man muss sein Trinkwasser zu Hause nicht filtern — im Wasserwerk wird sowieso schon alles rausgefiltert, auch Kalk und gelöste Mineralien. Ein Wasserfilter zu Hause ist deshalb komplett unnötig.» Bewerte diese Aussage aus naturwissenschaftlicher Sicht: Was an…
     Lösung: Die Aussage enthält einen sachlichen Fehler: Kalk und gelöste Mineralien (z. B. Calcium- und Magnesium-Ionen) sind GELÖSTE Bestandteile des Wassers — ein herkömmlicher Filter (auch im Wasserwerk) kann sie nicht herausfiltern, da Filtration nur ungelöste, feste Teilchen zurückhält (dasselbe Prinzip …

### block `c0195.i1` — „Fast nichts, was uns im Alltag begegnet, ist ein reiner Stoff — Meerwasser, Hausmüll oder ein Glas trübes Bachwasser sind Gemische aus mehre“ (Chemie, 4. Kl. · Stufe voll)

### block `c0195.t1` — „Im Chemieunterricht wurden fünf Trennverfahren an fünf verschiedenen Gemischen ausprobiert. Ordne jedem Trennverfahren das Gemisch zu, für d“ (Chemie, 4. Kl. · Stufe voll)

### block `c0195.t2` — „Im Wertstoffhof deiner Gemeinde läuft der Restmüll über ein Förderband mit einem großen Magneten darüber, bevor der Rest weiter zur Sortiera“ (Chemie, 4. Kl. · Stufe voll)

### block `c0195.t3` — „Ein Trinkwasser-Notfallteam testet nach einem Unwetter drei mögliche Reinigungsverfahren an demselben trüben, salzhaltigen Flusswasser. Zusä“ (Chemie, 4. Kl. · Stufe voll)

### block `c0195.t4` — „Aufgabe: In einem Eimer landet versehentlich ein Gemisch aus drei Stoffen: Sand, Kochsalz und Wasser (Sand und Salz sind beide fest, aber Sa“ (Chemie, 4. Kl. · Stufe voll)

### block `c0195.t5` — „Eine kleine Insel-Gemeinde hat kein natürliches Süßwasser und muss ihr Trinkwasser aus Meerwasser gewinnen. Der Gemeinderat prüft zwei Verfa“ (Chemie, 4. Kl. · Stufe voll)

### block `c0195.t6` — „In einem Online-Forum schreibt jemand: «Man muss sein Trinkwasser zu Hause nicht filtern — im Wasserwerk wird sowieso schon alles rausgefilt“ (Chemie, 4. Kl. · Stufe voll)

### item `c0194` — „Physik 3. Kl. — Energie unterwegs — das E-Bike (generiert)“ (Physik, 3. Kl. · Stufe voll)
- Kernfrage: Wohin verschwindet die Energie, wenn ein E-Bike den Berg hochfährt — und wo kommt sie beim Bremsen wieder her?
- Aufgaben:
  1. [multiple_choice · remember] Sieh dir Abb. 1 an. Zwischen km 4 und km 8 steigt die Strecke stark an, der Elektromotor unterstützt kräftig. Welche Energieumwandlung findet in diesem Abschnitt hauptsächlich statt?
     Lösung: Richtig ist die erste Option: Beim Bergauffahren mit Motorunterstützung wandelt der Akku elektrische Energie sowohl in Bewegungsenergie (das E-Bike fährt) als auch in Höhenenergie um (das E-Bike gewinnt an Höhe).
  2. [data_interpretation · understand] Betrachte weiterhin Abb. 1. (a) In welchem Streckenabschnitt (in km) verliert das E-Bike wieder an Höhe? (b) Welche Energieform nimmt in genau diesem Abschnitt zu, wenn das E-Bike schneller wird? (c) Erkläre in eigenen Worten, warum ein E-Bike bergab kaum Akku-Energie braucht.
     Lösung: (a) Zwischen km 8 und km 12 (Höhe fällt von 80 m auf 15 m). (b) Die Bewegungsenergie nimmt zu — das E-Bike wird bergab schneller, auch ohne Motorleistung. (c) Die gespeicherte Höhenenergie wird von selbst in Bewegungsenergie umgewandelt (die Fahrt bergab beschleunigt das Rad), der Motor muss daher …
  3. [true_false_justify · apply] Ein E-Bike mit Rekuperationsbremse lädt beim Bremsen einen Teil des Akkus wieder auf. Beurteile die folgenden Aussagen dazu und begründe jeweils kurz.
     Lösung: 1: richtig — der Motor arbeitet beim Bremsen als Generator und wandelt einen Teil der Bewegungsenergie in elektrische Energie um. 2: falsch — ein Teil der Energie wird immer zu Reibungswärme (Bremsen, Luftwiderstand, Rollwiderstand); die volle Energiemenge kommt nie zurück. 3: richtig — Energie wir…
  4. [data_interpretation · analyze] Sieh dir Abb. 2 an. Die Reichweite eines E-Bike-Akkus wurde unter vier Fahrweisen gemessen. (a) Bei welcher Fahrweise ist die Reichweite am größten, bei welcher am kleinsten? (b) Um wie viele Kilometer sinkt die Reichweite, wenn man bei flacher Strecke den Motor zuschaltet? (c) Erkläre, warum berga…
     Lösung: (a) Am größten bei 'Flach, Motor aus' (60 km), am kleinsten bei 'Bergauf, Motor an, volle Unterstützung' (15 km). (b) Von 60 km auf 45 km, also ein Rückgang um 15 km. (c) Bergauf muss der Motor zusätzlich Höhenenergie liefern (nicht nur Bewegungsenergie wie auf flacher Strecke), und bei voller Unte…
  5. [decision_scenario · evaluate] Familie Berger möchte ein E-Bike kaufen und fährt hauptsächlich in einer sehr hügeligen Gegend, meist Strecken von 15 bis 20 km. Ein Verkäufer bietet zwei Modelle an: Modell A mit kleinem, günstigerem Akku (Herstellerangabe: bis zu 60 km Reichweite) und Modell B mit großem, teurerem Akku (Herstelle…
     Lösung: Sinnvolle Empfehlung: Da Herstellerangaben meist für die günstigste Fahrweise (flach, Motor aus) gelten, laut Abb. 2 aber bergauf mit Unterstützung die reale Reichweite deutlich sinkt (bis auf 15 km bei voller Unterstützung), sollte man mit der Familie klären, wie stark sie den Motor im hügeligen G…
  6. [create_produce · create] Entwirf einen kurzen Info-Zettel (nur Text, keine Zeichnung nötig) für Neukund:innen eines Fahrradgeschäfts mit dem Titel 'So holst du mehr Kilometer aus deinem E-Bike-Akku'. Nenne mindestens drei konkrete Tipps und erkläre bei jedem Tipp kurz, welche Energieform dabei geschont wird.
     Lösung: Musterlösung (Beispiel): Titel: 'So holst du mehr Kilometer aus deinem E-Bike-Akku'. Tipp 1: Motorunterstützung nur bei Steigungen einschalten, auf flacher Strecke selbst treten — spart elektrische Energie, die sonst der Akku liefern müsste. Tipp 2: Reifen richtig aufpumpen — weniger Rollreibung be…

### block `c0194.t1` — „Sieh dir Abb. 1 an. Zwischen km 4 und km 8 steigt die Strecke stark an, der Elektromotor unterstützt kräftig. Welche Energieumwandlung finde“ (Physik, 3. Kl. · Stufe voll)

### block `c0194.t2` — „Betrachte weiterhin Abb. 1.
(a) In welchem Streckenabschnitt (in km) verliert das E-Bike wieder an Höhe?
(b) Welche Energieform nimmt in gen“ (Physik, 3. Kl. · Stufe voll)

### block `c0194.t3` — „Ein E-Bike mit Rekuperationsbremse lädt beim Bremsen einen Teil des Akkus wieder auf. Beurteile die folgenden Aussagen dazu und begründe jew“ (Physik, 3. Kl. · Stufe voll)

### block `c0194.t4` — „Sieh dir Abb. 2 an. Die Reichweite eines E-Bike-Akkus wurde unter vier Fahrweisen gemessen.
(a) Bei welcher Fahrweise ist die Reichweite am “ (Physik, 3. Kl. · Stufe voll)

### block `c0194.t5` — „Familie Berger möchte ein E-Bike kaufen und fährt hauptsächlich in einer sehr hügeligen Gegend, meist Strecken von 15 bis 20 km. Ein Verkäuf“ (Physik, 3. Kl. · Stufe voll)

### block `c0194.t6` — „Entwirf einen kurzen Info-Zettel (nur Text, keine Zeichnung nötig) für Neukund:innen eines Fahrradgeschäfts mit dem Titel 'So holst du mehr “ (Physik, 3. Kl. · Stufe voll)

### item `c0193` — „Physik 2. Kl. — Senden, Empfangen, Wahrnehmen (generiert)“ (Physik, 2. Kl. · Stufe voll)
- Kernfrage: Was passiert zwischen einer Schallquelle oder Lichtquelle und deinem Ohr oder Auge – und wo lauern dabei Gefahren?
- Aufgaben:
  1. [matching · remember] Ordne dem Sender-Empfänger-Modell für SEHEN bzw. HÖREN jeweils die passenden Begriffe zu.
     Lösung: Sender (Sehen) – Lichtquelle oder beleuchteter Gegenstand. Ausbreitungsweg (Sehen) – Licht breitet sich geradlinig durch die Luft aus. Empfänger (Sehen) – Auge (Netzhaut). Sender (Hören) – Schallquelle, z. B. schwingende Stimmbänder oder Lautsprecher. Empfänger (Hören) – Ohr (Trommelfell).
  2. [decision_scenario · apply] Es dämmert bereits. Zwei Kinder gehen am Straßenrand nach Hause: Kind A trägt dunkle Kleidung ohne Reflektoren, Kind B trägt eine helle Jacke mit reflektierenden Streifen. Ein Auto nähert sich mit Abblendlicht. Erkläre mithilfe des Sender-Empfänger-Modells, welches Kind der Autofahrer früher erkenn…
     Lösung: Kind B (helle Jacke mit Reflektoren) wird deutlich früher erkannt. Das Auto-Scheinwerferlicht (Sender) trifft auf die Kleidung; reflektierende Streifen werfen das Licht gezielt zum Fahrzeug zurück, sodass viel Licht zum Auge des Fahrers (Empfänger) gelangt. Dunkle, nicht-reflektierende Kleidung sch…
  3. [data_interpretation · understand] Betrachte die Schallpegel-Skala. Ab welchem markierten Wert kann bereits kurzzeitige Belastung das Gehör schädigen, und wie viele Dezibel liegen zwischen normaler Gesprächslautstärke und der Schmerzgrenze?
     Lösung: Bereits ab etwa 85 dB (laute Kopfhörer, Dauerbeschallung) steigt das Risiko für Gehörschäden bei längerer Einwirkung deutlich, ab ca. 100 dB (Konzertlautstärke) auch bei kürzerer Einwirkung. Zwischen normaler Gesprächslautstärke (60 dB) und der Schmerzgrenze (120 dB) liegen 60 Dezibel.
  4. [true_false_justify · understand] Prüfe folgende Aussagen zum verantwortungsvollen Umgang mit Licht- und Schallquellen und begründe jeweils kurz.
     Lösung: 1) Falsch – schon ein kurzer, direkter Lasertreffer auf die Netzhaut kann diese dauerhaft schädigen; Laserpointer dürfen nie auf Augen gerichtet werden. 2) Richtig – dauerhafte hohe Lautstärke direkt am Ohr (Kopfhörer) zählt zu den häufigsten Ursachen für Lärmschwerhörigkeit bei Jugendlichen. 3) Fa…
  5. [data_interpretation · analyze] Betrachte die Abbildung zum Schattenraum hinter einer Kugel bei einer punktförmigen Lichtquelle. Erkläre mithilfe des Modells der geradlinigen Lichtausbreitung, warum der Schatten hier überall gleich scharf begrenzt ist (kein Übergangsbereich).
     Lösung: Licht breitet sich von der punktförmigen Quelle allseitig geradlinig aus. Jeder Lichtstrahl, der die Kugel gerade so streift, setzt sich danach geradlinig fort und begrenzt den Schattenraum als scharfe Kegelfläche. Weil es nur EINEN Ausgangspunkt für alle Strahlen gibt, gibt es keine Strahlen, die …
  6. [open_response · understand] Beschreibe mit eigenen Worten oder einer Skizze, wie sich Erde und Mond bewegen müssen, damit wir auf der Erde abwechselnd Tag und Nacht sowie unterschiedliche Mondphasen (z. B. Vollmond, Neumond) beobachten. Gehe auf mindestens zwei Bewegungen ein.
     Lösung: Tag und Nacht entstehen durch die Rotation der Erde um ihre eigene Achse (etwa 24 Stunden): Die jeweils der Sonne zugewandte Seite hat Tag, die abgewandte Seite Nacht. Die Mondphasen entstehen durch den Umlauf des Mondes um die Erde (etwa 29,5 Tage): Der Mond selbst leuchtet nicht, sondern wird von…
  … + 1 weitere Aufgaben

### block `c0193.t1` — „Ordne dem Sender-Empfänger-Modell für SEHEN bzw. HÖREN jeweils die passenden Begriffe zu.“ (Physik, 2. Kl. · Stufe voll)

### block `c0193.t2` — „Es dämmert bereits. Zwei Kinder gehen am Straßenrand nach Hause: Kind A trägt dunkle Kleidung ohne Reflektoren, Kind B trägt eine helle Jack“ (Physik, 2. Kl. · Stufe voll)

### block `c0193.t3` — „Betrachte die Schallpegel-Skala. Ab welchem markierten Wert kann bereits kurzzeitige Belastung das Gehör schädigen, und wie viele Dezibel li“ (Physik, 2. Kl. · Stufe voll)

### block `c0193.t4` — „Prüfe folgende Aussagen zum verantwortungsvollen Umgang mit Licht- und Schallquellen und begründe jeweils kurz.“ (Physik, 2. Kl. · Stufe voll)

### block `c0193.t5` — „Betrachte die Abbildung zum Schattenraum hinter einer Kugel bei einer punktförmigen Lichtquelle. Erkläre mithilfe des Modells der geradlinig“ (Physik, 2. Kl. · Stufe voll)

### block `c0193.t6` — „Beschreibe mit eigenen Worten oder einer Skizze, wie sich Erde und Mond bewegen müssen, damit wir auf der Erde abwechselnd Tag und Nacht sow“ (Physik, 2. Kl. · Stufe voll)

### block `c0193.t7` — „Ein rotes T-Shirt liegt in einem komplett abgedunkelten Raum, in dem nur eine grüne Lichtquelle leuchtet (kein anderes Licht vorhanden). Sag“ (Physik, 2. Kl. · Stufe voll)

### item `c0192` — „Physik 2. Kl. — Vom Leuchtpunkt zum Bild (generiert)“ (Physik, 2. Kl. · Stufe voll)
- Kernfrage: Wie entsteht aus einem Lichtpunkt ein Bild – in der Lochkamera, im Spiegel und in deinem Auge?
- Aufgaben:
  1. [true_false_justify · remember] Eine Kerzenflamme steht vor einer Lochkamera. Prüfe die folgenden Aussagen zum Leuchtpunkt-Bildpunkt-Schema und begründe jeweils.
     Lösung: 1) Richtig – ein Leuchtpunkt sendet Licht in alle Richtungen aus (Lichtbündel). 2) Richtig – nur die Strahlen, die genau die enge Öffnung treffen, gelangen weiter zur Rückwand; alle anderen werden von der Kamerawand geblockt. 3) Falsch – gerade WEIL sich die Lichtbündel im engen Loch kreuzen, entst…
  2. [table_fill · understand] Ordne jedem optischen System zu, ob das entstehende Bild reell (auf einem Schirm auffangbar) oder virtuell (nicht auffangbar, nur im Kopf) ist, und wo das Bild jeweils liegt.
     Lösung: Lochkamera: reell – das Bild liegt auf der Rückwand (Mattscheibe) und ist dort tatsächlich sichtbar/fotografierbar. Ebener Spiegel: virtuell – das Bild scheint hinter dem Spiegel zu liegen, dort kommt aber kein Licht her. Auge: reell – das Bild entsteht auf der Netzhaut (innere Rückwand des Auges),…
  3. [experiment_protocol · apply] Plane eine kleine Untersuchung: Du hältst eine Lupe (Sammellinse) zwischen eine Kerze und eine weiße Wand und verschiebst sie langsam. Beschreibe, was du beobachten und protokollieren würdest.
     Lösung: Sinnvolles Protokoll: 1) Aufbau notieren (Kerze – Linse – Wand, Abstände messen). 2) Linse langsam von der Kerze weg zur Wand hin verschieben. 3) Beobachten, bei welchem Abstand ein scharfes Bild auf der Wand erscheint (Fokussierung). 4) Feststellen, dass das scharfe Bild auf der Wand kopfstehend (…
  4. [data_interpretation · analyze] Betrachte die Abbildung zur Lochkamera (Lichtbündel von zwei Punkten der Flamme). Erkläre mithilfe der Zeichnung, warum das Bild auf der Rückwand kopfstehend ist.
     Lösung: Der obere Leuchtpunkt L sendet ein Lichtbündel aus, von dem nur der Strahl durch die enge Blende weiterkommt – dieser trifft danach auf den UNTEREN Bereich der Rückwand (Bildpunkt B). Der untere Leuchtpunkt L' erzeugt auf demselben Weg einen Bildpunkt im OBEREN Bereich der Rückwand (B'). Weil sich …
  5. [multiple_choice · understand] Weißes Sonnenlicht trifft auf ein Glasprisma und wird dahinter als Regenbogenband aus vielen Farben sichtbar. Welche Aussage beschreibt diese Beobachtung physikalisch korrekt?
     Lösung: Richtig ist B: Weißes Licht ist aus vielen Spektralfarben (Rot bis Violett) zusammengesetzt; das Prisma trennt sie räumlich auf, weil jede Farbe unterschiedlich stark gebrochen wird – es entstehen keine neuen Farben, sie waren immer schon im Licht enthalten.
  6. [source_critique · evaluate] Ein Mitschüler behauptet: Endoskope in der Medizin sind nur ein Spielzeug für Ärzte, ein normales Kamerahandy würde denselben Zweck erfüllen. Recherchiere kurz (Schulbuch, verlässliche Website) den tatsächlichen Nutzen von Endoskopen und nimm begründet Stellung. Nenne mindestens eine Chance UND ein…
     Lösung: Die Behauptung ist unzutreffend: Ein Endoskop ist eine sehr dünne, flexible optische Sonde mit eigener Lichtquelle, die durch kleine Körperöffnungen oder Schnitte ins Körperinnere eingeführt werden kann – ein Kamerahandy kann das nicht. Chance: minimalinvasive Untersuchungen/Operationen (z. B. Mage…
  … + 1 weitere Aufgaben

### block `c0192.t1` — „Eine Kerzenflamme steht vor einer Lochkamera. Prüfe die folgenden Aussagen zum Leuchtpunkt-Bildpunkt-Schema und begründe jeweils.“ (Physik, 2. Kl. · Stufe voll)

### block `c0192.t2` — „Ordne jedem optischen System zu, ob das entstehende Bild reell (auf einem Schirm auffangbar) oder virtuell (nicht auffangbar, nur im Kopf) i“ (Physik, 2. Kl. · Stufe voll)

### block `c0192.t3` — „Plane eine kleine Untersuchung: Du hältst eine Lupe (Sammellinse) zwischen eine Kerze und eine weiße Wand und verschiebst sie langsam. Besch“ (Physik, 2. Kl. · Stufe voll)

### block `c0192.t4` — „Betrachte die Abbildung zur Lochkamera (Lichtbündel von zwei Punkten der Flamme). Erkläre mithilfe der Zeichnung, warum das Bild auf der Rüc“ (Physik, 2. Kl. · Stufe voll)

### block `c0192.t5` — „Weißes Sonnenlicht trifft auf ein Glasprisma und wird dahinter als Regenbogenband aus vielen Farben sichtbar. Welche Aussage beschreibt dies“ (Physik, 2. Kl. · Stufe voll)

### block `c0192.t6` — „Ein Mitschüler behauptet: Endoskope in der Medizin sind nur ein Spielzeug für Ärzte, ein normales Kamerahandy würde denselben Zweck erfüllen“ (Physik, 2. Kl. · Stufe voll)

### block `c0192.t7` — „Entwirf ein einfaches Werbeplakat (Stichworte + Skizze in Worten) für die Lochkamera als die einfachste Kamera der Welt. Erkläre darin in ei“ (Physik, 2. Kl. · Stufe voll)

### item `c0190` — „Mathematik 4. Kl. — Baustelle Freibad — Pythagoras, Kreise und ein Rutschturm (generiert)“ (Mathematik, 4. Kl. · Stufe voll)
- Kernfrage: Wie viel Material braucht man wirklich, wenn ein rundes Becken und ein zylindrischer Turm gebaut werden sollen?
- Aufgaben:
  1. [calculation · remember] Die Wasserrutsche im Freibad braucht eine schräge Stützstrebe (siehe Abbildung 1). Der waagrechte Abstand zum Turm beträgt 4 m, die Höhe 3 m. Berechne die Länge s der Strebe mithilfe des pythagoräischen Lehrsatzes.
     Lösung: s² = 4² + 3² = 16 + 9 = 25, also s = √25 = 5 m.
  2. [calculation · apply] Das Rundbecken hat einen Radius von 5 m (siehe Abbildung 2). a) Berechne den Umfang des Beckenrands — dafür wird die Bordüre bestellt. b) Berechne den Flächeninhalt der Wasseroberfläche — dafür wird die Chemikalien-Dosierung berechnet. Runde beide Ergebnisse sinnvoll.
     Lösung: a) Umfang U = 2·π·r = 2·π·5 ≈ 31,42 m, aufgerundet z. B. 32 m Bordüre bestellen. b) Fläche A = π·r² = π·25 ≈ 78,54 m².
  3. [table_fill · analyze] Neben dem Rundbecken gibt es noch das rechteckige Nichtschwimmerbecken ABCD mit den Seiten 6 m und 4 m (siehe Abbildung 3). Vergleiche in der Tabelle die beiden Becken: Trage für jedes Becken Umfang und Flächeninhalt ein und beurteile, welches Becken bei gleichem Randmaterial (Bordürenlänge) die gr…
     Lösung: Rechteck ABCD: Umfang = 2·(6+4) = 20 m, Fläche = 6·4 = 24 m². Rundbecken (aus Aufgabe 2): Umfang ≈ 31,42 m, Fläche ≈ 78,54 m². Bei annähernd gleichem Umfang (hier nicht exakt gleich, da unterschiedliche Beckenmaße vorgegeben sind) liefert der Kreis pro Meter Rand deutlich mehr Fläche — bezogen auf …
  4. [open_response · understand] Der Rutschturm ist ein Drehzylinder mit Radius 1,5 m und Höhe 4 m, obendrauf sitzt als Dach ein Drehkegel mit derselben Grundfläche und einer Höhe von 1 m. Beschreibe in eigenen Worten, wie Zylinder und Kegel jeweils durch Drehen einer ebenen Figur entstehen, und erkläre, welche Größen du brauchst,…
     Lösung: Ein Drehzylinder entsteht, wenn man ein Rechteck um eine seiner Seiten dreht; ein Drehkegel entsteht, wenn man ein rechtwinkliges Dreieck um eine Kathete dreht. Für die Gesamtoberfläche braucht man: den Radius r (für beide Mäntel und die Grundfläche), die Zylinderhöhe h, und entweder die Kegelhöhe …
  5. [calculation · apply] Jetzt wird gerechnet: Der Kegel auf dem Rutschturm hat Radius r = 1,5 m und Höhe h = 1 m. a) Berechne zunächst die Mantellinie s des Kegels (Hinweis: r und h stehen im rechten Winkel zueinander, s ist die Hypotenuse). b) Berechne damit das Volumen des Kegels (V = ⅓·π·r²·h) UND separat das Volumen d…
     Lösung: a) s² = r² + h² = 1,5² + 1² = 2,25 + 1 = 3,25, also s = √3,25 ≈ 1,80 m. b) Kegelvolumen: V_Kegel = ⅓·π·1,5²·1 = ⅓·π·2,25 ≈ 2,36 m³. Zylindervolumen: V_Zyl = π·1,5²·4 = π·2,25·4 ≈ 28,27 m³. Der Zylinder fasst also mehr als das Zehnfache des Kegelvolumens.
  6. [decision_scenario · evaluate] Die Freibadleitung hat ein knappes Budget und muss sich zwischen zwei Varianten für ein neues Kinderbecken entscheiden: Variante A ist ein Rundbecken mit Radius 3 m, Variante B ein quadratisches Becken mit Seitenlänge 5 m. Beide Varianten sollen möglichst viel Wasserfläche für Kinder bieten, aber d…
     Lösung: Rundbecken: Umfang = 2·π·3 ≈ 18,85 m (passt ins Budget), Fläche = π·3² ≈ 28,27 m². Quadrat: Umfang = 4·5 = 20 m (passt genau), Fläche = 5² = 25 m². Beide halten das Budget ein, aber das Rundbecken bietet bei sogar etwas weniger Randmaterial mehr Wasserfläche (28,27 m² statt 25 m²) — Empfehlung: Run…

### item `c0191` — „Mathematik 4. Kl. — Das Schulfest-Glücksrad — wer gewinnt wirklich? (generiert)“ (Mathematik, 4. Kl. · Stufe voll)
- Kernfrage: Lohnt sich das neue Glücksspiel am Schulfest wirklich für alle Teilnehmer:innen?
- Aufgaben:
  1. [table_fill · remember] Beim Schulfest wurde erhoben, welche Klassen am neuen Glücksrad-Spiel teilgenommen haben. Ergebnis: Von den 20 Kindern der 4a haben 12 mitgespielt, 8 nicht. Von den 24 Kindern der 4b haben 15 mitgespielt, 9 nicht. Trage diese Angaben in eine Kreuztabelle mit den Zeilen „4a“ und „4b“ sowie den Spalt…
     Lösung: 4a: 12 | 8 | 20. 4b: 15 | 9 | 24. Summe: 27 | 17 | 44.
  2. [open_response · understand] Nutze deine Kreuztabelle aus Aufgabe 1, um folgende Fragen zu beantworten: a) Wie viele Kinder insgesamt haben NICHT am Glücksrad-Spiel teilgenommen? b) In welcher Klasse haben anteilig mehr Kinder mitgespielt — der 4a oder der 4b? Begründe mit einer Rechnung, nicht nur mit den absoluten Zahlen.
     Lösung: a) 8 + 9 = 17 Kinder haben nicht mitgespielt. b) 4a: 12 von 20, das sind 60 %. 4b: 15 von 24, das sind 62,5 %. Anteilig hat die 4b etwas mehr Kinder zum Mitspielen bewegt, obwohl in absoluten Zahlen die 4b nur 3 Kinder mehr hat als die 4a bei den Teilnehmenden.
  3. [calculation · apply] So funktioniert das Glücksrad-Spiel (siehe Baumdiagramm in Abbildung 1): Zuerst dreht man ein Glücksrad, das mit Wahrscheinlichkeit 0,5 auf Rot und mit Wahrscheinlichkeit 0,5 auf Blau zeigt. Danach zieht man ein Los: Bei Rot gewinnt man mit Wahrscheinlichkeit 0,4 einen Stern, bei Blau nur mit Wahrs…
     Lösung: a) P(Rot UND Stern) = 0,5 · 0,4 = 0,20 (20 %). b) P(Blau UND Stern) = 0,5 · 0,2 = 0,10 (10 %).
  4. [calculation · apply] Berechne jetzt die Gesamtwahrscheinlichkeit, beim Glücksrad-Spiel überhaupt einen Stern zu gewinnen — egal ob über Rot oder Blau. Nutze dafür deine beiden Ergebnisse aus Aufgabe 3.
     Lösung: P(Stern gesamt) = P(Rot UND Stern) + P(Blau UND Stern) = 0,20 + 0,10 = 0,30, also 30 %.
  5. [true_false_justify · understand] Beurteile folgende Aussagen zum Glücksrad-Spiel und begründe jeweils kurz mit deinen Ergebnissen aus den vorherigen Aufgaben.
     Lösung: 1) Wahr: 0,20 (Rot-Stern) > 0,10 (Blau-Stern). 2) Falsch: Gesamtwahrscheinlichkeit für Stern ist 0,30 (30 %), also gewinnt man häufiger KEINEN Stern (70 %). 3) Falsch: bei zwei unabhängigen Drehungen wird multipliziert, nicht addiert: 0,5 · 0,5 = 0,25, nicht 1,0.
  6. [decision_scenario · evaluate] Der Elternverein überlegt, das Glücksrad-Spiel beim nächsten Schulfest wieder aufzubauen. Ein Los kostet 1 €, ein gewonnener Stern wird gegen einen kleinen Preis im Wert von 2 € eingetauscht. Nimm Stellung: Ist dieses Spiel aus Sicht der Spieler:innen eher „fair“, „großzügig“ oder „zu Ungunsten der…
     Lösung: Es gewinnen nur 30 % der Spieler:innen überhaupt einen Preis; die übrigen 70 % zahlen 1 € ohne Gegenwert. Eine vollständige Einschätzung erkennt, dass das Spiel aus reiner Gewinnchancen-Sicht eher zu Ungunsten der Spieler:innen ausfällt (nicht „fair“ im Sinne von 50:50, aber auch nicht als reine Ab…

### block `c0190.t1` — „Die Wasserrutsche im Freibad braucht eine schräge Stützstrebe (siehe Abbildung 1). Der waagrechte Abstand zum Turm beträgt 4 m, die Höhe 3 m“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0190.t2` — „Das Rundbecken hat einen Radius von 5 m (siehe Abbildung 2). a) Berechne den Umfang des Beckenrands — dafür wird die Bordüre bestellt. b) Be“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0190.t3` — „Neben dem Rundbecken gibt es noch das rechteckige Nichtschwimmerbecken ABCD mit den Seiten 6 m und 4 m (siehe Abbildung 3). Vergleiche in de“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0190.t4` — „Der Rutschturm ist ein Drehzylinder mit Radius 1,5 m und Höhe 4 m, obendrauf sitzt als Dach ein Drehkegel mit derselben Grundfläche und eine“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0190.t5` — „Jetzt wird gerechnet: Der Kegel auf dem Rutschturm hat Radius r = 1,5 m und Höhe h = 1 m. a) Berechne zunächst die Mantellinie s des Kegels “ (Mathematik, 4. Kl. · Stufe voll)

### block `c0190.t6` — „Die Freibadleitung hat ein knappes Budget und muss sich zwischen zwei Varianten für ein neues Kinderbecken entscheiden: Variante A ist ein R“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0191.t1` — „Beim Schulfest wurde erhoben, welche Klassen am neuen Glücksrad-Spiel teilgenommen haben. Ergebnis: Von den 20 Kindern der 4a haben 12 mitge“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0191.t2` — „Nutze deine Kreuztabelle aus Aufgabe 1, um folgende Fragen zu beantworten: a) Wie viele Kinder insgesamt haben NICHT am Glücksrad-Spiel teil“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0191.t3` — „So funktioniert das Glücksrad-Spiel (siehe Baumdiagramm in Abbildung 1): Zuerst dreht man ein Glücksrad, das mit Wahrscheinlichkeit 0,5 auf “ (Mathematik, 4. Kl. · Stufe voll)

### block `c0191.t4` — „Berechne jetzt die Gesamtwahrscheinlichkeit, beim Glücksrad-Spiel überhaupt einen Stern zu gewinnen — egal ob über Rot oder Blau. Nutze dafü“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0191.t5` — „Beurteile folgende Aussagen zum Glücksrad-Spiel und begründe jeweils kurz mit deinen Ergebnissen aus den vorherigen Aufgaben.“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0191.t6` — „Der Elternverein überlegt, das Glücksrad-Spiel beim nächsten Schulfest wieder aufzubauen. Ein Los kostet 1 €, ein gewonnener Stern wird gege“ (Mathematik, 4. Kl. · Stufe voll)

### item `c0189` — „Mathematik 4. Kl. — Die Diagonale des Blumenbeets — reelle Zahlen im Garten (generiert)“ (Mathematik, 4. Kl. · Stufe voll)
- Kernfrage: Warum reicht dir ein Maßband manchmal nicht, um eine Länge exakt anzugeben?
- Aufgaben:
  1. [open_response · understand] Ein quadratisches Blumenbeet hat die Seitenlänge 2 m (siehe Abbildung 2). Du willst die Diagonale des Beets ausmessen, um eine Schnur für ein Zierband zu kaufen. Stelle mithilfe des pythagoräischen Lehrsatzes einen Term für die Diagonale d auf. Musst du diesen Term schon lösen? Begründe, warum das …
     Lösung: d² = 2² + 2² = 4 + 4 = 8, also d = √8 m. Nein, man muss den Term nicht sofort lösen, um die Fragestellung zu verstehen. Da 8 keine Quadratzahl ist (nicht 1, 4, 9, 16, …), ist √8 keine ganze Zahl — vermutlich also auch kein „glatter“ Meterwert.
  2. [true_false_justify · understand] √8 lässt sich nicht als Bruch zweier ganzer Zahlen schreiben — √8 ist also eine irrationale Zahl. Beurteile die folgenden Aussagen über die Zahlenmenge, in der √8 „lebt“, und begründe jeweils kurz.
     Lösung: 1) Wahr: reelle Zahlen umfassen sowohl rationale als auch irrationale Zahlen, √8 gehört dazu. 2) Falsch: es gibt reelle Zahlen (wie √8), die nicht rational sind — die Umkehrung stimmt nicht. 3) Wahr: genau das ist die Bedeutung der Erweiterung zu den reellen Zahlen — die Zahlengerade wird lückenlos.
  3. [calculation · apply] Nähere √8 durch systematisches Probieren an, ohne die Wurzel-Taste zu benutzen. Gehe so vor: Finde zuerst zwei aufeinanderfolgende ganze Zahlen, zwischen denen √8 liegen muss (Quadratzahlen vergleichen). Verfeinere dann mit einer Nachkommastelle, dann mit zwei Nachkommastellen. Trage dein Ergebnis …
     Lösung: 2² = 4 und 3² = 9, also liegt √8 zwischen 2 und 3. 2,8² = 7,84 und 2,9² = 8,41 → zwischen 2,8 und 2,9. 2,82² = 7,9524 und 2,83² = 8,0089 → zwischen 2,82 und 2,83, also √8 ≈ 2,83 (auf zwei Nachkommastellen).
  4. [calculation · apply] Berechne jetzt mit Technologieeinsatz (Taschenrechner erlaubt) die tatsächliche Länge der Diagonale d = √8 m auf zwei Nachkommastellen genau, und vergleiche mit deiner Näherung aus Aufgabe 3. Wie viel Schnur (in cm, aufgerundet) solltest du für das Zierband kaufen, wenn du 10 cm Reserve zum Verknot…
     Lösung: √8 ≈ 2,83 m. Mit Reserve: 2,83 m + 0,10 m = 2,93 m = 293 cm. Wegen der Reserve und möglicher Messungenauigkeit sollte man aufrunden, z. B. auf 295 cm oder 300 cm Schnur kaufen.
  5. [modelling_task · analyze] Zwei Freund:innen streiten: Anna behauptet, √9 + √16 sei dasselbe wie √(9+16). Ben widerspricht. Prüfe die Behauptung rechnerisch nach und entscheide, wer recht hat. Nutze dein Ergebnis, um zu erklären, warum man beim Rechnen mit Wurzeln (und allgemein mit Näherungswerten) besonders vorsichtig sein…
     Lösung: √9 + √16 = 3 + 4 = 7. √(9+16) = √25 = 5. Da 7 ≠ 5, hat Ben recht: die Wurzel einer Summe ist im Allgemeinen NICHT die Summe der Wurzeln. Das zeigt, dass man mit Wurzeln nicht wie mit normalen Zahlen „auseinanderziehen“ darf — Rechenregeln müssen jeweils geprüft, nicht vermutet werden. Ebenso ist Vo…
  6. [create_produce · create] Erfinde eine eigene kurze Sachsituation aus deinem Alltag (Garten, Zimmer, Sportplatz, Bastelprojekt …), bei der man wie beim Blumenbeet eine Streckenlänge berechnen muss, deren Ergebnis eine irrationale Zahl ist. Beschreibe die Situation, stelle den passenden Term auf und runde das Ergebnis sinnvo…
     Lösung: Individuelle Lösungen. Muss enthalten: eine plausible Alltagssituation mit zwei rechtwinklig zueinander stehenden, ganzzahligen (oder einfachen) Streckenlängen, einen korrekt aufgestellten Term (meist über Pythagoras), ein Ergebnis, dessen Radikand keine Quadratzahl ist, und eine für die Praxis sin…

### block `c0189.t1` — „Ein quadratisches Blumenbeet hat die Seitenlänge 2 m (siehe Abbildung 2). Du willst die Diagonale des Beets ausmessen, um eine Schnur für ei“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0189.t2` — „√8 lässt sich nicht als Bruch zweier ganzer Zahlen schreiben — √8 ist also eine irrationale Zahl. Beurteile die folgenden Aussagen über die “ (Mathematik, 4. Kl. · Stufe voll)

### block `c0189.t3` — „Nähere √8 durch systematisches Probieren an, ohne die Wurzel-Taste zu benutzen. Gehe so vor: Finde zuerst zwei aufeinanderfolgende ganze Zah“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0189.t4` — „Berechne jetzt mit Technologieeinsatz (Taschenrechner erlaubt) die tatsächliche Länge der Diagonale d = √8 m auf zwei Nachkommastellen genau“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0189.t5` — „Zwei Freund:innen streiten: Anna behauptet, √9 + √16 sei dasselbe wie √(9+16). Ben widerspricht. Prüfe die Behauptung rechnerisch nach und e“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0189.t6` — „Erfinde eine eigene kurze Sachsituation aus deinem Alltag (Garten, Zimmer, Sportplatz, Bastelprojekt …), bei der man wie beim Blumenbeet ein“ (Mathematik, 4. Kl. · Stufe voll)

### block `c0188.t3` — „Das Streckzentrum liegt bei Z(0|0). Ein Punkt des Originaldreiecks liegt bei P1(2|1). Berechne die Koordinaten des Bildpunkts P1' nach zentr“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0188.t4` — „Das Turmmodell hat als Grundfläche das Rechteck aus der Abbildung (6 cm × 4 cm) und ist ein gerades Prisma mit der Höhe 10 cm. Berechne (a) “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0188.t5` — „Für das Turmdach plant die Modellbauerin eine Pyramide mit DERSELBEN Grundfläche (24 cm²) und DERSELBEN Höhe (10 cm) wie das Prisma aus Aufg“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0188.t6` — „Entwirf dein eigenes Modell für eine Verpackung (z. B. eine Geschenkschachtel als gerades Prisma oder ein Zeltmodell als Pyramide). Wähle si“ (Mathematik, 3. Kl. · Stufe voll)

### item `c0188` — „Mathematik 3. Kl. — Die Modellbau-Werkstatt (generiert)“ (Mathematik, 3. Kl. · Stufe voll)
- Kernfrage: Wie berechnest du Flächen und Rauminhalte von Figuren und Körpern — und was passiert damit, wenn du ein Modell verkleinerst oder vergrößerst?
- Aufgaben:
  1. [calculation · understand] Das Grundstück ABCDE in der Abbildung lässt sich in ein Rechteck ABCE' (mit E' als Hilfspunkt direkt über E auf Höhe von C) und ein Dreieck darüber zerlegen: Rechteck mit den Seiten 8 m und 4 m, darüber ein Dreieck mit Grundseite 8 m und Höhe 3 m (von der Rechteckoberkante bis zur Spitze D). Berech…
     Lösung: Rechteck: A = 8 m · 4 m = 32 m². Dreieck: A = (8 m · 3 m) : 2 = 12 m². Gesamtfläche: 32 m² + 12 m² = 44 m².
  2. [true_false_justify · understand] Das Dreieck P1P2P3 in der Abbildung wird vom Streckzentrum Z aus mit dem Faktor k = 2 zentrisch gestreckt (jeder Punkt wandert doppelt so weit von Z weg). Entscheide, ob die folgenden Aussagen über das gestreckte Dreieck richtig oder falsch sind.
     Lösung: 1) Falsch: Winkel bleiben bei einer zentrischen Streckung IMMER gleich groß, egal welcher Streckfaktor gewählt wird. 2) Richtig: Längen werden mit dem Faktor k = 2 multipliziert. 3) Falsch: die Fläche wird mit k² = 4 multipliziert, also viermal so groß, nicht doppelt.
  3. [calculation · apply] Das Streckzentrum liegt bei Z(0|0). Ein Punkt des Originaldreiecks liegt bei P1(2|1). Berechne die Koordinaten des Bildpunkts P1' nach zentrischer Streckung mit dem Faktor k = 3 (Formel: P' = k · P, da Z im Ursprung liegt). Berechne anschließend auf demselben Weg die Bildpunkte von P2(4|1) und P3(3…
     Lösung: P1' = 3 · (2|1) = (6|3). P2' = 3 · (4|1) = (12|3). P3' = 3 · (3|4) = (9|12).
  4. [calculation · apply] Das Turmmodell hat als Grundfläche das Rechteck aus der Abbildung (6 cm × 4 cm) und ist ein gerades Prisma mit der Höhe 10 cm. Berechne (a) den Oberflächeninhalt des Prismas (2 Grundflächen + 4 Seitenflächen) und (b) den Rauminhalt des Prismas.
     Lösung: Grundfläche: G = 6 cm · 4 cm = 24 cm². (a) Oberfläche: 2 Grundflächen (2 · 24 = 48 cm²) + Seitenflächen (Umfang · Höhe = (2·6 + 2·4) · 10 = 20 · 10 = 200 cm²). Gesamt: O = 48 + 200 = 248 cm². (b) Volumen: V = G · h = 24 cm² · 10 cm = 240 cm³.
  5. [true_false_justify · analyze] Für das Turmdach plant die Modellbauerin eine Pyramide mit DERSELBEN Grundfläche (24 cm²) und DERSELBEN Höhe (10 cm) wie das Prisma aus Aufgabe 4. Entscheide, ob die folgenden Aussagen richtig oder falsch sind, und begründe mit einer Rechnung.
     Lösung: 1) Richtig: bei gleicher Grundfläche und Höhe gilt immer V(Pyramide) = (1/3) · V(Prisma). 2) Richtig: V = (1/3) · G · h = (1/3) · 24 cm² · 10 cm = 80 cm³ (passt zu Aussage 1, da 240 cm³ : 3 = 80 cm³). 3) Richtig: da V = (1/3) · G · h und G konstant bleibt, ist V direkt proportional zu h — eine Verd…
  6. [create_produce · create] Entwirf dein eigenes Modell für eine Verpackung (z. B. eine Geschenkschachtel als gerades Prisma oder ein Zeltmodell als Pyramide). Wähle sinnvolle Maße (Grundfläche + Höhe), zeichne eine beschriftete Skizze, und berechne für dein Modell sowohl den Oberflächeninhalt als auch den Rauminhalt. Begründ…
     Lösung: Individuelle Lösungen. Beispiel Geschenkschachtel (Prisma, quadratische Grundfläche 5 cm × 5 cm, Höhe 12 cm): Grundfläche G = 25 cm². Oberfläche: 2 · 25 + (4 · 5) · 12 = 50 + 240 = 290 cm². Volumen: 25 · 12 = 300 cm³. Begründung: passend für ein schmales, hohes Geschenk wie einen Stift oder eine Ke…

### block `c0188.intro1` — „Eine Modellbauerin plant ein Gelände: Sie zeichnet Grundstücksflächen als Vielecke, verkleinert reale Maße auf ein Modell, und muss für ein “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0188.t1` — „Das Grundstück ABCDE in der Abbildung lässt sich in ein Rechteck ABCE' (mit E' als Hilfspunkt direkt über E auf Höhe von C) und ein Dreieck “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0188.t2` — „Das Dreieck P1P2P3 in der Abbildung wird vom Streckzentrum Z aus mit dem Faktor k = 2 zentrisch gestreckt (jeder Punkt wandert doppelt so we“ (Mathematik, 3. Kl. · Stufe voll)

### item `c0187` — „Mathematik 3. Kl. — Der Wassertank-Plan (generiert)“ (Mathematik, 3. Kl. · Stufe voll)
- Kernfrage: Wie beschreibst du mit einem Term, was in einem Tank passiert — und wie findest du heraus, wann er leer oder voll ist?
- Aufgaben:
  1. [data_interpretation · understand] Der Graph zeigt die Befüllung von Tank A. (a) Wie viel Wasser war zu Beginn (t = 0) bereits im Tank? (b) Wie viele Liter kommen pro Minute dazu? (c) Stelle einen Term W(t) auf, der den Wasserstand nach t Minuten beschreibt.
     Lösung: (a) 200 Liter (Startwert bei t=0). (b) Zwischen t=0 und t=2 steigt der Stand von 200 auf 400, also 200 Liter in 2 Minuten = 100 Liter pro Minute. (c) W(t) = 100 · t + 200.
  2. [calculation · understand] Vereinfache die folgenden Terme. Wende dabei die Potenzgesetze für positive ganzzahlige Exponenten an. (a) 3a² + 5a² − a² (b) a³ · a⁴ (c) (2a)² · a (d) 5a² · 3a − 4a³
     Lösung: (a) 3a² + 5a² − a² = 7a². (b) a³ · a⁴ = a^7 (Exponenten addieren, da gleiche Basis). (c) (2a)² · a = 4a² · a = 4a³. (d) 5a² · 3a − 4a³ = 15a³ − 4a³ = 11a³.
  3. [calculation · apply] Tank B wird entleert. Der Term für den Wasserstand lautet W(t) = 450 − 40 · t (in Litern nach t Minuten). Löse die Gleichung 450 − 40 · t = 130 durch Äquivalenzumformung und dokumentiere jeden Schritt einzeln. Was bedeutet das Ergebnis im Sachzusammenhang?
     Lösung: 450 − 40t = 130 | −450 auf beiden Seiten: −40t = −320 | : (−40) auf beiden Seiten: t = 8. Bedeutung: Nach 8 Minuten sind noch 130 Liter im Tank.
  4. [calculation · apply] Ein zweiter, kleinerer Tank C wird proportional zu Tank A befüllt, aber langsamer: In 3 Minuten kommen 210 Liter dazu (Tank C startet bei 0 Litern). (a) Stelle das Verhältnis von Wassermenge zu Zeit als Bruch dar und kürze es. (b) Wie viel Liter sind nach 10 Minuten im Tank? (c) Nach wie vielen Min…
     Lösung: (a) 210 Liter : 3 Minuten = 70 Liter je Minute (Verhältnis 210:3 gekürzt = 70:1). (b) 70 · 10 = 700 Liter. (c) 700 : 70 = 10 Minuten (also derselbe Zeitpunkt wie in (b), das ist kein Zufall, sondern folgt direkt aus der Proportionalität).
  5. [true_false_justify · analyze] Vergleiche Tank A (Befüllung, W(t) = 100t + 200), Tank B (Entleerung, W(t) = 450 − 40t) und Tank C (Proportion, W(t) = 70t). Entscheide, ob die folgenden Aussagen richtig oder falsch sind, und begründe mit den Termen.
     Lösung: 1) Richtig: beide Terme wachsen mit t, aber Tank A hat einen Startwert von 200 ≠ 0, also keine Proportion; Tank C startet bei 0, also echte Proportion. 2) Richtig: −40t sorgt dafür, dass W(t) mit wachsendem t kleiner wird — das ist ein Abnahmeprozess. 3) Falsch: mathematisch würde der Term irgendwa…
  6. [create_produce · create] Entwirf deinen eigenen Wachstums- oder Abnahmeprozess zu einem Sachthema deiner Wahl (z. B. eine Pflanze, ein Sparbuch, ein Vorrat, eine Batterie-Ladung). Gib an: (1) den Startwert, (2) die Änderung pro Zeiteinheit als Term, (3) eine Gleichung, mit der man berechnen kann, wann ein bestimmter Zielwe…
     Lösung: Individuelle Lösungen. Beispiel: Eine Pflanze ist 4 cm hoch und wächst 1,5 cm pro Woche: H(w) = 1,5w + 4. Gesucht: wann ist sie 25 cm hoch? 1,5w + 4 = 25 → 1,5w = 21 → w = 14 Wochen. Modellgrenze: Das lineare Wachstum gilt nur, solange die Pflanze jung ist — irgendwann verlangsamt sich das Wachstum…

### block `c0187.intro1` — „Ein Gartenteich-Betrieb hat einen Wassertank, der zu Beginn schon teilweise gefüllt ist und dann gleichmäßig weiter befüllt oder entleert wi“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0187.t1` — „Der Graph zeigt die Befüllung von Tank A. (a) Wie viel Wasser war zu Beginn (t = 0) bereits im Tank? (b) Wie viele Liter kommen pro Minute d“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0187.t2` — „Vereinfache die folgenden Terme. Wende dabei die Potenzgesetze für positive ganzzahlige Exponenten an.
(a) 3a² + 5a² − a²
(b) a³ · a⁴
(c) (2“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0187.t3` — „Tank B wird entleert. Der Term für den Wasserstand lautet W(t) = 450 − 40 · t (in Litern nach t Minuten). Löse die Gleichung 450 − 40 · t = “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0187.t4` — „Ein zweiter, kleinerer Tank C wird proportional zu Tank A befüllt, aber langsamer: In 3 Minuten kommen 210 Liter dazu (Tank C startet bei 0 “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0187.t5` — „Vergleiche Tank A (Befüllung, W(t) = 100t + 200), Tank B (Entleerung, W(t) = 450 − 40t) und Tank C (Proportion, W(t) = 70t). Entscheide, ob “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0187.t6` — „Entwirf deinen eigenen Wachstums- oder Abnahmeprozess zu einem Sachthema deiner Wahl (z. B. eine Pflanze, ein Sparbuch, ein Vorrat, eine Bat“ (Mathematik, 3. Kl. · Stufe voll)

### item `c0185` — „Mathematik 2. Kl. — Der Schulgarten-Plan (generiert)“ (Mathematik, 2. Kl. · Stufe voll)
- Kernfrage: Wie plant ihr ein Schulgarten-Beet, das genau passt, spiegelsymmetrisch aussieht und wirklich Platz für alle Pflanzen bietet?
- Aufgaben:
  1. [data_interpretation · remember] Die Abbildung zeigt den Lageplan des Schulgartens. Gib die Koordinaten aller vier markierten Punkte an. Welche zwei Punkte liegen auf derselben Höhe (gleicher y-Wert)?
     Lösung: Wasserhahn (2|1), Gartenhütte (6|1), Zaun-Ecke (2|5), Baum (6|5). Auf derselben Höhe (y = 1) liegen Wasserhahn und Gartenhütte; auf derselben Höhe (y = 5) liegen Zaun-Ecke und Baum.
  2. [construction · apply] Zeichne im Koordinatensystem aus Aufgabe 1 (auf deinem eigenen Blatt Karopapier) den Punkt P(4|1) sowie seinen Spiegelpunkt P' an der senkrechten Geraden x = 4, die durch die Mitte des Gartens verläuft. Gib die Koordinaten von P' an und begründe, warum diese Gerade eine Symmetrieachse des Rechtecks…
     Lösung: P(4|1) liegt bereits auf der Achse x = 4, daher ist P' = P = (4|1). Die Gerade x = 4 ist eine Symmetrieachse des Rechtecks, weil sie genau in der Mitte zwischen den Punkten mit x = 2 (Wasserhahn, Zaun-Ecke) und x = 6 (Gartenhütte, Baum) verläuft – jeder Punkt links der Achse hat einen gleich weit e…
  3. [true_false_justify · analyze] Zwei Gruppen haben je ein rechteckiges Beet markiert: Gruppe 1 mit den Seiten 6 m und 4 m, Gruppe 2 mit den Seiten 4 m und 6 m. Beurteile die folgenden Aussagen zu diesen beiden Beeten.
     Lösung: 1) Richtig – Kongruenz hängt nicht von der Ausrichtung/Drehung ab, sondern nur davon, ob die Figuren durch Verschieben, Drehen oder Spiegeln zur Deckung gebracht werden können. 2) Falsch – genau das Gegenteil ist richtig, siehe Aussage 1. 3) Richtig – beide Rechtecke haben die Fläche 6 m · 4 m = 24…
  4. [calculation · apply] Beet 1 ist rechteckig. Zwei gegenüberliegende Seiten sind je 6 m lang, die Einfassung (der gesamte Umfang) benötigt 20 laufende Meter Holz. Wie lang sind die beiden fehlenden Seiten (mit '?' markiert in der Abbildung)?
     Lösung: Umfang = 2 · (Länge + Breite), also 20 m = 2 · (6 m + Breite). Daraus: 6 m + Breite = 10 m, also Breite = 4 m. Beide fehlenden (gegenüberliegenden) Seiten sind je 4 m lang.
  5. [calculation · apply] Berechne den Flächeninhalt von Beet 1 (Rechteck, Seiten 6 m und 4 m aus Aufgabe 4) und von Beet 2 (Dreieck, Grundseite EF = 5 m, Höhe 4 m, siehe Abbildung). Welches Beet bietet mehr Fläche für Pflanzen, und um wie viele Quadratmeter?
     Lösung: Beet 1 (Rechteck): 6 m · 4 m = 24 m². Beet 2 (Dreieck): (5 m · 4 m) : 2 = 10 m². Beet 1 bietet mehr Fläche, um 24 m² − 10 m² = 14 m².
  6. [decision_scenario · evaluate] Der Schulgarten hat insgesamt nur 32 m² Erde zur Verfügung. Ihr wollt Beet 1 UND Beet 2 wie oben berechnet anlegen, UND zusätzlich einen 1 Meter breiten Gehweg rund um beide Beete freihalten, der keine Erde braucht, aber ebenfalls Platz auf den 32 m² beansprucht. Reicht die Fläche? Begründe mit ein…
     Lösung: Beet 1 + Beet 2 zusammen benötigen 24 m² + 10 m² = 34 m² allein für die Erde – das ist bereits mehr als die verfügbaren 32 m², ohne den Gehweg überhaupt einzurechnen. Die Fläche reicht also nicht. Für eine genaue Antwort zum Gehweg bräuchte man zusätzlich die genaue Anordnung der beiden Beete zuein…
  … + 1 weitere Aufgaben

### item `c0186` — „Mathematik 3. Kl. — Der Fieberkurven-Fall (generiert)“ (Mathematik, 3. Kl. · Stufe voll)
- Kernfrage: Wie beschreibst du Zustände und ihre Änderungen mit rationalen Zahlen — und was bedeutet ein Minuszeichen eigentlich?
- Aufgaben:
  1. [table_fill · remember] Die Abbildung zeigt die Tiefsttemperaturen einer Woche auf der Zahlengeraden. Lies die vier markierten Werte ab und trage sie in die Tabelle ein. Ordne anschließend die vier Tage in der letzten Zeile von der kältesten zur wärmsten Nacht.
     Lösung: Montag: −8 °C, Dienstag: −3 °C, Mittwoch: 4 °C, Donnerstag: −1 °C. Reihenfolge kalt → warm: Montag (−8) < Dienstag (−3) < Donnerstag (−1) < Mittwoch (4).
  2. [true_false_justify · understand] Das Minuszeichen taucht in der Mathematik in drei verschiedenen Rollen auf. Entscheide, ob die folgenden Aussagen richtig oder falsch sind, und benenne jeweils, in welcher Rolle das Minuszeichen in der Aussage steckt.
     Lösung: 1) Richtig — Rechenzeichen (eine Subtraktion zwischen zwei Zahlen). 2) Falsch — hier ist das Minus ein Vorzeichen, es beschreibt einen Zustand (Temperatur unter null), keine Rechnung zwischen zwei Zahlen. 3) Richtig — Zeichen für das Übergehen zur Gegenzahl: −(−7) = 7.
  3. [calculation · apply] Berechne. Schreibe bei (a) und (b) die Subtraktion zuerst als Addition der Gegenzahl an, bevor du rechnest. Schreibe bei (d) die Division zuerst als Multiplikation mit dem Kehrwert an. (a) −6 − (−9) (b) −4,5 − 3,2 (c) −7 · (−2) (d) −18 : (−4)
     Lösung: (a) −6 − (−9) = −6 + 9 = 3. (b) −4,5 − 3,2 = −4,5 + (−3,2) = −7,7. (c) −7 · (−2) = 14 (Minus mal Minus ergibt Plus). (d) −18 : (−4) = −18 · (−1/4) = 4,5.
  4. [calculation · apply] Die Abbildung zeigt den Kontostand von Familie Berger. Der Startwert ist markiert, ebenso der Stand nach einer Einzahlung. (a) Wie hoch war die Einzahlung? (b) Danach hebt die Familie 45 € ab. Wie hoch ist der Kontostand jetzt? (c) Berechne den Abstand (Betrag der Differenz) zwischen dem allererste…
     Lösung: (a) Einzahlung = −70 − (−120) = −70 + 120 = 50 €. (b) −70 − 45 = −115 €. (c) |−120 − (−115)| = |−120 + 115| = |−5| = 5 €.
  5. [ordering · analyze] Ein Chemielehrer schreibt vier sehr kleine bzw. sehr große Größen in Zehnerpotenz- bzw. Gleitkommadarstellung an die Tafel. Ordne sie der Größe nach — von der kleinsten bis zur größten Zahl.
     Lösung: Von klein nach groß: 7 · 10^(−5) < 2,5 · 10^(−2) < 3 · 10^4 < 1 · 10^6. (In Dezimalschreibweise: 0,00007 < 0,025 < 30 000 < 1 000 000.)
  6. [create_produce · create] Erfinde deine eigene Kurzgeschichte zu einem Zustand mit Vorzeichen (z. B. eine Tauchgang-Tiefe, ein Kontostand, eine Höhenangabe im Gebirge). Deine Geschichte muss: (1) einen Startwert nennen, (2) mindestens eine Zustandsänderung mit einer Rechnung beschreiben (Addition ODER Subtraktion), (3) nach…
     Lösung: Individuelle Lösungen. Beispiel: Ein Taucher startet bei −4 m, taucht weitere 9 m ab (−4 − 9 = −13 m), taucht dann 6 m auf (−13 + 6 = −7 m). Abstand zwischen Start und Ende: |−4 − (−7)| = |3| = 3 m.

### block `c0185.i1` — „Eure Klasse darf ein neues Beet im Schulgarten anlegen. Ihr plant zuerst die Lage im Koordinatensystem, entwerft dann eine symmetrische Beet“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0186.intro1` — „In einer Wetterstation, einem Krankenhaus und auf einem Kontoauszug tauchen ständig Zahlen mit Vorzeichen auf: −5 °C, ein Kontostand von −12“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0186.t1` — „Die Abbildung zeigt die Tiefsttemperaturen einer Woche auf der Zahlengeraden. Lies die vier markierten Werte ab und trage sie in die Tabelle“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0186.t2` — „Das Minuszeichen taucht in der Mathematik in drei verschiedenen Rollen auf. Entscheide, ob die folgenden Aussagen richtig oder falsch sind, “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0186.t3` — „Berechne. Schreibe bei (a) und (b) die Subtraktion zuerst als Addition der Gegenzahl an, bevor du rechnest. Schreibe bei (d) die Division zu“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0186.t4` — „Die Abbildung zeigt den Kontostand von Familie Berger. Der Startwert ist markiert, ebenso der Stand nach einer Einzahlung. (a) Wie hoch war “ (Mathematik, 3. Kl. · Stufe voll)

### block `c0186.t5` — „Ein Chemielehrer schreibt vier sehr kleine bzw. sehr große Größen in Zehnerpotenz- bzw. Gleitkommadarstellung an die Tafel. Ordne sie der Gr“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0186.t6` — „Erfinde deine eigene Kurzgeschichte zu einem Zustand mit Vorzeichen (z. B. eine Tauchgang-Tiefe, ein Kontostand, eine Höhenangabe im Gebirge“ (Mathematik, 3. Kl. · Stufe voll)

### block `c0185.t1` — „Die Abbildung zeigt den Lageplan des Schulgartens. Gib die Koordinaten aller vier markierten Punkte an. Welche zwei Punkte liegen auf dersel“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0185.t2` — „Zeichne im Koordinatensystem aus Aufgabe 1 (auf deinem eigenen Blatt Karopapier) den Punkt P(4|1) sowie seinen Spiegelpunkt P' an der senkre“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0185.t3` — „Zwei Gruppen haben je ein rechteckiges Beet markiert: Gruppe 1 mit den Seiten 6 m und 4 m, Gruppe 2 mit den Seiten 4 m und 6 m. Beurteile di“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0185.t4` — „Beet 1 ist rechteckig. Zwei gegenüberliegende Seiten sind je 6 m lang, die Einfassung (der gesamte Umfang) benötigt 20 laufende Meter Holz. “ (Mathematik, 2. Kl. · Stufe voll)

### block `c0185.t5` — „Berechne den Flächeninhalt von Beet 1 (Rechteck, Seiten 6 m und 4 m aus Aufgabe 4) und von Beet 2 (Dreieck, Grundseite EF = 5 m, Höhe 4 m, s“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0185.t6` — „Der Schulgarten hat insgesamt nur 32 m² Erde zur Verfügung. Ihr wollt Beet 1 UND Beet 2 wie oben berechnet anlegen, UND zusätzlich einen 1 M“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0185.t7` — „Entwirf ein eigenes drittes Beet in Form eines Vierecks deiner Wahl (Rechteck, Quadrat oder ein anderes besonderes Viereck), das eine Fläche“ (Mathematik, 2. Kl. · Stufe voll)

### item `c0184` — „Mathematik 2. Kl. — Der Wandertag-Fonds (generiert)“ (Mathematik, 2. Kl. · Stufe voll)
- Kernfrage: Wie teilt ihr Gruppen, Vorräte und Geld gerecht auf, wenn eure Klasse einen Wandertag plant?
- Aufgaben:
  1. [calculation · remember] In deiner Klasse sind 28 Schüler:innen. Die Lehrperson möchte gleich große Gruppen bilden. Liste alle Teiler von 28 auf. In welche Gruppengrößen lässt sich die Klasse ohne Rest aufteilen?
     Lösung: Teiler von 28: 1, 2, 4, 7, 14, 28. Mögliche gleich große Gruppen ohne Rest: 1, 2, 4, 7, 14 oder 28 Schüler:innen pro Gruppe.
  2. [true_false_justify · apply] Zwei Wandergruppen sollen sich an einem gemeinsamen Rastplatz treffen: Gruppe A geht alle 6 Minuten eine Pause, Gruppe B alle 8 Minuten. Beurteile die folgenden Aussagen und begründe.
     Lösung: 1) Richtig – 24 ist das kgV(6,8), Vielfache von 6: 6,12,18,24…; Vielfache von 8: 8,16,24…; erste gemeinsame Zahl ist 24. 2) Falsch – 16 ist Vielfaches von 8, aber nicht von 6. 3) Falsch – 48 ist zwar ein gemeinsames Vielfaches, aber nicht das KLEINSTE (24 ist kleiner).
  3. [open_response · analyze] Formuliere eine eigene Teilbarkeitsregel für die Zahl 9 (wann ist eine Zahl durch 9 teilbar?) und überprüfe sie an den Zahlen 234 und 451.
     Lösung: Regel: Eine Zahl ist durch 9 teilbar, wenn ihre Quersumme durch 9 teilbar ist. 234: Quersumme 2+3+4=9, durch 9 teilbar (234:9=26) – stimmt. 451: Quersumme 4+5+1=10, nicht durch 9 teilbar – stimmt, 451:9 ergibt Rest 4.
  4. [calculation · apply] Für den Wandersnack mischt ihr Nüsse und Trockenfrüchte. Von den 28 Portionen sollen drei Viertel Nuss-Frucht-Mix sein, der Rest reiner Apfelchips. Wie viele Portionen sind Nuss-Frucht-Mix, wie viele Apfelchips? Gib beide Anteile zusätzlich als Dezimalzahl an.
     Lösung: 3/4 von 28 = 21 Portionen Nuss-Frucht-Mix. Rest: 28 − 21 = 7 Portionen Apfelchips (das ist 1/4 von 28). Als Dezimalzahl: 3/4 = 0,75 und 1/4 = 0,25.
  5. [decision_scenario · evaluate] Zwei Busunternehmen bieten Fahrten für eure 28-köpfige Gruppe an. Bus A kostet 12 Euro pro Person, aber es gibt 10 % Nachlass ab 25 Personen. Bus B kostet 14 Euro pro Person mit 25 % Nachlass ab 20 Personen. Welcher Bus ist für eure Gruppe günstiger – und um wie viel Euro insgesamt?
     Lösung: Bus A: 28 · 12 € = 336 €, davon 10 % Nachlass = 33,60 €, Endpreis 302,40 €. Bus B: 28 · 14 € = 392 €, davon 25 % Nachlass = 98 €, Endpreis 294 €. Bus B ist günstiger, um 302,40 € − 294 € = 8,40 €.
  6. [data_interpretation · understand] Die Abbildung zeigt die Temperatur an eurem Wandertag von 6 Uhr früh bis Mittag. Lies ab: Wie viel Grad wärmer ist es am Mittag als um 6 Uhr früh? Beschreibe in eigenen Worten, wie sich die Temperatur laut Zahlenstrahl entwickelt.
     Lösung: Um 6 Uhr früh zeigt der Zahlenstrahl −2 °C, am Mittag 12 °C. Differenz: 12 − (−2) = 14 Grad wärmer. Die Temperatur steigt im Lauf des Vormittags kontinuierlich von einem Minusgrad-Wert auf einen deutlichen Plusgrad-Wert.
  … + 1 weitere Aufgaben

### block `c0184.i1` — „Deine Klasse (28 Schüler:innen) organisiert einen Wandertag. Ihr müsst Gruppen einteilen, einen Wandersnack mischen, ein Busangebot vergleic“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0184.t1` — „In deiner Klasse sind 28 Schüler:innen. Die Lehrperson möchte gleich große Gruppen bilden. Liste alle Teiler von 28 auf. In welche Gruppengr“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0184.t2` — „Zwei Wandergruppen sollen sich an einem gemeinsamen Rastplatz treffen: Gruppe A geht alle 6 Minuten eine Pause, Gruppe B alle 8 Minuten. Beu“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0184.t3` — „Formuliere eine eigene Teilbarkeitsregel für die Zahl 9 (wann ist eine Zahl durch 9 teilbar?) und überprüfe sie an den Zahlen 234 und 451.“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0184.t4` — „Für den Wandersnack mischt ihr Nüsse und Trockenfrüchte. Von den 28 Portionen sollen drei Viertel Nuss-Frucht-Mix sein, der Rest reiner Apfe“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0184.t5` — „Zwei Busunternehmen bieten Fahrten für eure 28-köpfige Gruppe an. Bus A kostet 12 Euro pro Person, aber es gibt 10 % Nachlass ab 25 Personen“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0184.t6` — „Die Abbildung zeigt die Temperatur an eurem Wandertag von 6 Uhr früh bis Mittag. Lies ab: Wie viel Grad wärmer ist es am Mittag als um 6 Uhr“ (Mathematik, 2. Kl. · Stufe voll)

### block `c0184.t7` — „Entwirf für eine fiktive Nachmittags-Wanderung eine eigene Preis- ODER Temperaturaufgabe (deine Wahl), die genauso aufgebaut ist wie Aufgabe“ (Mathematik, 2. Kl. · Stufe voll)

### item `c0182` — „Mathematik 1. Kl. — Die Taschengeld-Sparbüchse (generiert)“ (Mathematik, 1. Kl. · Stufe voll)
- Kernfrage: Wie kannst du mit einem Buchstaben für eine unbekannte Zahl rechnen, um herauszufinden, wie viel Taschengeld du bekommst?
- Aufgaben:
  1. [open_response · understand] Lukas bekommt jede Woche 3 Euro Taschengeld. Außerdem hat er schon 2 Euro in seiner Sparbüchse. Stelle einen Term auf, der zeigt, wie viel Geld Lukas nach w Wochen insgesamt gespart hat.
     Lösung: Term: 3w + 2 (oder gleichwertig 3 · w + 2). Nach w Wochen hat Lukas 3w Euro aus dem Taschengeld plus die 2 Euro Startgeld.
  2. [multiple_choice · remember] Welche der folgenden Terme beschreiben Mias Sparsituation richtig: Sie hat 5 Euro Startgeld und bekommt jede Woche 4 Euro dazu?
     Lösung: Richtig sind: 4w + 5, 4 · w + 5 und 5 + w · 4 (alle gleichwertig, da Addition und Multiplikation vertauschbar sind). Falsch ist 5w + 4 — dort wäre 5 die wöchentliche Rate und 4 das Startgeld, das ist vertauscht.
  3. [calculation · apply] Lukas möchte wissen, nach wie vielen Wochen er 20 Euro gespart hat. Löse die Gleichung 3w + 2 = 20 durch schrittweises Umkehren der Rechenoperationen. Schreibe jeden Schritt einzeln auf.
     Lösung: 3w + 2 = 20 | −2 → 3w = 18 | ÷3 → w = 6. Probe: 3·6+2 = 20 ✓. Lukas hat also nach 6 Wochen 20 Euro gespart.
  4. [data_interpretation · apply] Die Abbildung zeigt Lukas' Sparverlauf als Graph (Wochen auf der waagrechten Achse, Ersparnis in Euro auf der senkrechten Achse). Lies aus dem Graphen ab, wie viel Geld Lukas nach 4 Wochen gespart hat, und überprüfe dein Ergebnis, indem du den Term 3w + 2 für w = 4 berechnest.
     Lösung: Abgelesen: ca. 14 Euro nach 4 Wochen. Berechnung: 3·4+2 = 12+2 = 14 Euro. Ablesung und Rechnung stimmen überein.
  5. [true_false_justify · evaluate] Entscheide, ob die folgenden Aussagen wahr oder falsch sind, und begründe jeweils kurz.
     Lösung: 1) Wahr: 3·0+2 = 2 ✓. 2) Falsch: Multipliziert man mit 0, ergibt sich 0 = 0, was keine sinnvolle Äquivalenzumformung mehr ist (die Information über w geht verloren). 3) Wahr: Bei w größer als 0 ist 3w immer größer als 0, also ist 3w+2 immer größer als 2.
  6. [create_produce · create] Erfinde eine eigene Sparsituation (mit Startgeld und wöchentlicher Rate), sodass die passende Gleichung 5w + 10 = 45 lautet. Erkläre, was w in deiner Geschichte bedeutet, und löse die Gleichung, um herauszufinden, nach wie vielen Wochen das Ziel erreicht ist.
     Lösung: Jede sinnvolle Geschichte mit 10 Euro Startgeld und 5 Euro wöchentlicher Rate passt, z. B.: »Paul hat 10 Euro geschenkt bekommen und spart jede Woche 5 Euro dazu, bis er 45 Euro für ein Spiel hat.« Lösung: 5w+10=45 | −10 → 5w=35 | ÷5 → w=7. Nach 7 Wochen ist das Ziel erreicht.

### item `c0183` — „Mathematik 1. Kl. — Der Gemüsegarten-Plan (generiert)“ (Mathematik, 1. Kl. · Stufe voll)
- Kernfrage: Wie berechnest du Umfang und Fläche eines Gartenbeets — und wie viel Erde passt in eine Hochbeet-Kiste?
- Aufgaben:
  1. [calculation · remember] Das Karotten-Beet (Abbildung) ist 5 m lang und 3 m breit. Berechne den Umfang (für den Zaun) und den Flächeninhalt (für die Erde) des Beets.
     Lösung: Umfang: U = 2·(5+3) = 2·8 = 16 m. Flächeninhalt: A = 5·3 = 15 m².
  2. [table_fill · understand] Begründe die Umfangsformel U = 2·(l+b) für ein Rechteck: Trage in die Tabelle ein, wie lang jede der vier Seiten eines Rechtecks mit Länge l und Breite b ist, und erkläre in einem Satz, warum man am Ende verdoppelt.
     Lösung: Seite 1: l, Seite 2: b, Seite 3: l, Seite 4: b. Ein Rechteck hat zwei Paare gleich langer, gegenüberliegender Seiten (l, l und b, b) — deshalb rechnet man erst l+b und verdoppelt dann, statt alle vier Seiten einzeln zu addieren.
  3. [calculation · apply] Das L-förmige Beet (Abbildung) lässt sich in zwei Rechtecke zerlegen. Zerlege die Figur gedanklich in zwei Rechtecke, berechne die Fläche jedes Teilrechtecks einzeln und addiere sie zur Gesamtfläche.
     Lösung: Zerlegung z. B. auf Höhe von C waagrecht durchtrennen: unteres Rechteck A-B-C-(Punkt darüber von A) mit 4 m × 2 m = 8 m². Oberes Rechteck (restliche Fläche bis D-E-F) mit 6 m × 3 m = 18 m². Gesamtfläche: 8 + 18 = 26 m².
  4. [construction · apply] Bevor der Gärtner das rechteckige Kräuter-Beet (4 m lang, 2 m breit) anlegt, plant er es maßstäblich auf Papier. Zeichne das Beet im Maßstab 1:100 (1 cm in der Zeichnung entspricht 1 m in Wirklichkeit). Mit welcher Länge und Breite in Zentimetern zeichnest du das Rechteck? Fertige die maßstäbliche …
     Lösung: Im Maßstab 1:100 entspricht 1 m genau 1 cm. Man zeichnet also ein Rechteck mit 4 cm Länge und 2 cm Breite und beschriftet die Seiten mit den echten Maßen (4 m bzw. 2 m).
  5. [true_false_justify · analyze] Ein Hochbeet hat die Form eines Quaders mit Länge 2 m, Breite 1 m und Höhe 0,5 m. Entscheide, ob die folgenden Aussagen wahr oder falsch sind, und begründe jeweils kurz.
     Lösung: 1) Wahr: V = 2·1·0,5 = 1 m³. 2) Wahr: V = l·b·h; verdoppelt man h, verdoppelt sich V (2·1·1 = 2 m³, das ist doppelt so viel wie 1 m³). 3) Wahr: Oberflächeninhalt O = 2·(l·b + l·h + b·h) = 2·(2 + 1 + 0,5) = 2·3,5 = 7 m², das ist größer als der Rauminhalt (1 m³) als reiner Zahlenwert — allerdings sin…
  6. [modelling_task · create] Plane dein eigenes Hochbeet: Wähle Länge, Breite und Höhe (jeweils zwischen 0,5 m und 2 m) so, dass genau 2 m³ Erde hineinpassen. Berechne zur Kontrolle den Rauminhalt deines gewählten Hochbeets, und gib zusätzlich an, wie viel Quadratmeter Holz du für die vier Seitenwände (ohne Boden und Deckel) b…
     Lösung: Individuelle Lösung, z. B. l = 2 m, b = 1 m, h = 1 m: V = 2·1·1 = 2 m³ ✓. Seitenwände (4 Stück, ohne Boden/Deckel): 2 Wände mit l·h = 2·1 = 2 m² und 2 Wände mit b·h = 1·1 = 1 m². Gesamt: 2·2 + 2·1 = 6 m² Holz.

### block `c0182.t1` — „Lukas bekommt jede Woche 3 Euro Taschengeld. Außerdem hat er schon 2 Euro in seiner Sparbüchse. Stelle einen Term auf, der zeigt, wie viel G“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0182.t2` — „Welche der folgenden Terme beschreiben Mias Sparsituation richtig: Sie hat 5 Euro Startgeld und bekommt jede Woche 4 Euro dazu?“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0182.t3` — „Lukas möchte wissen, nach wie vielen Wochen er 20 Euro gespart hat. Löse die Gleichung 3w + 2 = 20 durch schrittweises Umkehren der Rechenop“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0182.t4` — „Die Abbildung zeigt Lukas' Sparverlauf als Graph (Wochen auf der waagrechten Achse, Ersparnis in Euro auf der senkrechten Achse). Lies aus d“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0182.t5` — „Entscheide, ob die folgenden Aussagen wahr oder falsch sind, und begründe jeweils kurz.“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0182.t6` — „Erfinde eine eigene Sparsituation (mit Startgeld und wöchentlicher Rate), sodass die passende Gleichung 5w + 10 = 45 lautet. Erkläre, was w “ (Mathematik, 1. Kl. · Stufe voll)

### block `c0183.t1` — „Das Karotten-Beet (Abbildung) ist 5 m lang und 3 m breit. Berechne den Umfang (für den Zaun) und den Flächeninhalt (für die Erde) des Beets.“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0183.t2` — „Begründe die Umfangsformel U = 2·(l+b) für ein Rechteck: Trage in die Tabelle ein, wie lang jede der vier Seiten eines Rechtecks mit Länge l“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0183.t3` — „Das L-förmige Beet (Abbildung) lässt sich in zwei Rechtecke zerlegen. Zerlege die Figur gedanklich in zwei Rechtecke, berechne die Fläche je“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0183.t4` — „Bevor der Gärtner das rechteckige Kräuter-Beet (4 m lang, 2 m breit) anlegt, plant er es maßstäblich auf Papier. Zeichne das Beet im Maßstab“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0183.t5` — „Ein Hochbeet hat die Form eines Quaders mit Länge 2 m, Breite 1 m und Höhe 0,5 m. Entscheide, ob die folgenden Aussagen wahr oder falsch sin“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0183.t6` — „Plane dein eigenes Hochbeet: Wähle Länge, Breite und Höhe (jeweils zwischen 0,5 m und 2 m) so, dass genau 2 m³ Erde hineinpassen. Berechne z“ (Mathematik, 1. Kl. · Stufe voll)

### item `c0181` — „Mathematik 1. Kl. — Der Radweg-Tracker — Zahlen unterwegs (generiert)“ (Mathematik, 1. Kl. · Stufe voll)
- Kernfrage: Wie liest und ordnest du Zahlen, die dir eine Fahrrad-App auf einer Tour anzeigt?
- Aufgaben:
  1. [data_interpretation · remember] Drei Freund:innen machen eine Radtour. Ihre App zeigt die bisher zurückgelegte Strecke am Zahlenstrahl (Abbildung). Lies aus der Abbildung ab: Wer ist am weitesten gefahren, wer am wenigsten weit? Schreibe alle drei Streckenlängen der Größe nach geordnet auf (kleinste zuerst).
     Lösung: Geordnet (kleinste zuerst): Tim 3,5 km, Anna 7 km, Ben 12,25 km. Am weitesten: Ben. Am wenigsten weit: Tim.
  2. [calculation · understand] Die App zeigt Bens Gesamtstrecke als 12,25 km an. Schreibe diese Zahl als gemischte Zahl (ganze Kilometer + Bruch) und erkläre in einem Satz, was die Nachkommastellen bedeuten.
     Lösung: 12,25 km = 12 1/4 km (0,25 = 25/100 = 1/4). Die Nachkommastellen geben den Anteil des nächsten Kilometers an, den Ben schon zurückgelegt hat.
  3. [calculation · apply] Annas App zeigt zusätzlich die Anzahl der Pedaltritte: 4528 Tritte für die ersten 7 km. Schreibe diese Zahl im Stellenwertsystem auf (Tausender, Hunderter, Zehner, Einer) und runde sie auf die nächsten vollen Hunderter (Überschlagsrechnung).
     Lösung: 4528 Tritte: 4 Tausender, 5 Hunderter, 2 Zehner, 8 Einer. Gerundet auf volle Hunderter: 4500 Tritte.
  4. [table_fill · apply] Tim möchte seine Strecke von 3,5 km auch in Metern angeben, weil sein kleiner Bruder Meter besser versteht. Rechne um und trage die fehlenden Werte in die Tabelle ein: 3,5 km = ___ m; 750 m = ___ km; 1/2 km = ___ m.
     Lösung: 3,5 km = 3500 m. 750 m = 0,75 km. 1/2 km = 500 m.
  5. [true_false_justify · analyze] Entscheide, ob die folgenden Aussagen über die drei Radfahrer:innen wahr oder falsch sind, und begründe jeweils kurz mit einer Rechnung oder einem Argument.
     Lösung: 1) Falsch: 3,5 + 7 = 10,5 km, das ist WENIGER als Bens 12,25 km. 2) Wahr: 3/4 von 12,25 km = 9,1875 km, das ist mehr als 9 km. 3) Wahr: Bei gleicher Geschwindigkeit bedeutet die längste Strecke (12,25 km) auch die längste Fahrzeit.
  6. [modelling_task · create] Plane für nächste Woche eine eigene Radtour: Wähle eine Gesamtstrecke zwischen 8 und 15 km. Teile sie in drei Etappen ein (z. B. 1/3, 1/4 und den Rest) und gib jede Etappe sowohl als Bruch als auch als Dezimalzahl in km an. Prüfe mit einer Überschlagsrechnung, ob deine drei Etappen wirklich die Ges…
     Lösung: Individuelle Lösung, z. B. Gesamtstrecke 12 km: Etappe 1 = 1/3 von 12 km = 4 km, Etappe 2 = 1/4 von 12 km = 3 km, Etappe 3 = Rest = 12 − 4 − 3 = 5 km. Kontrolle: 4 + 3 + 5 = 12 km ✓.

### block `c0181.t1` — „Drei Freund:innen machen eine Radtour. Ihre App zeigt die bisher zurückgelegte Strecke am Zahlenstrahl (Abbildung). Lies aus der Abbildung a“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0181.t2` — „Die App zeigt Bens Gesamtstrecke als 12,25 km an. Schreibe diese Zahl als gemischte Zahl (ganze Kilometer + Bruch) und erkläre in einem Satz“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0181.t3` — „Annas App zeigt zusätzlich die Anzahl der Pedaltritte: 4528 Tritte für die ersten 7 km. Schreibe diese Zahl im Stellenwertsystem auf (Tausen“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0181.t4` — „Tim möchte seine Strecke von 3,5 km auch in Metern angeben, weil sein kleiner Bruder Meter besser versteht. Rechne um und trage die fehlende“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0181.t5` — „Entscheide, ob die folgenden Aussagen über die drei Radfahrer:innen wahr oder falsch sind, und begründe jeweils kurz mit einer Rechnung oder“ (Mathematik, 1. Kl. · Stufe voll)

### block `c0181.t6` — „Plane für nächste Woche eine eigene Radtour: Wähle eine Gesamtstrecke zwischen 8 und 15 km. Teile sie in drei Etappen ein (z. B. 1/3, 1/4 un“ (Mathematik, 1. Kl. · Stufe voll)

### item `c0178` — „Biologie und Umweltbildung 3. Kl. — Der Boden unter unseren Füßen – lebendig und verletzlich (generiert)“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)
- Kernfrage: Warum ist eine Handvoll Erde eigentlich voller Leben, und wie schützen wir das?
- Aufgaben:
  1. [table_fill · remember] Beobachte die Abbildung/Beschreibung einer Bodenprobe mit Regenwurm, Pilzfäden und Wurzelresten. Trage für jeden Bestandteil ein, ob er ein Lebewesen ist und welche Aufgabe er im Boden hat.
     Lösung: Regenwurm: Lebewesen (ja) – lockert den Boden durch Gänge und mischt organisches Material ein. Pilzfäden: Lebewesen (ja) – zersetzen abgestorbenes Pflanzenmaterial und liefern Pflanzen Nährstoffe. Wurzelreste: kein Lebewesen (nein) – dienen als Nahrung für Bodenlebewesen bei der Zersetzung.
  2. [open_response · understand] Erkläre, warum eine Pflanze auf völlig totem, sterilem Sand deutlich schlechter wächst als auf lebendigem Gartenboden, obwohl beide 'fest' und 'braun bzw. hell' aussehen.
     Lösung: In sterilem Sand fehlen Mikroorganismen und Pilze, die abgestorbenes Material zersetzen und dadurch Nährstoffe wie Stickstoff oder Phosphor freisetzen, welche die Pflanze über die Wurzeln aufnehmen kann. Ohne diese Zersetzer bleiben kaum Nährstoffe verfügbar, außerdem speichert lebendiger Boden mei…
  3. [data_interpretation · apply] Das Diagramm zeigt, wie viele Regenwürmer je Quadratmeter je nach Bodennutzung leben. Beschreibe den Zusammenhang zwischen Nutzungsart und Regenwurmanzahl und leite eine mögliche Erklärung ab.
     Lösung: Je intensiver und stärker versiegelt die Nutzung, desto weniger Regenwürmer leben im Boden: von 180/m² auf der Naturwiese über 95 (Bio-Acker) und 40 (konventioneller Acker) bis zu nur 2/m² auf versiegeltem Boden. Eine mögliche Erklärung ist, dass Pflügen, Chemikalieneinsatz und vor allem Versiegelu…
  4. [cause_effect_match · analyze] Ordne jeder menschlichen Einwirkung auf den Boden die passende Folge zu.
     Lösung: Asphaltierung → Boden für Wasser/Luft undurchlässig, kein Leben mehr möglich. Kunstdünger/Pestizide → Bodenlebewesen sterben ab, Nährstoffkreisläufe brechen zusammen. Monokultur ohne Fruchtwechsel → Boden wird einseitig ausgelaugt, Nährstoffe fehlen zunehmend.
  5. [source_critique · evaluate] Ein Mitschüler behauptet: 'Zerstörter Boden erholt sich genauso schnell wieder wie eine gemähte Wiese nachwächst.' Prüfe diese Behauptung wie ein Forscher/eine Forscherin: Ist das eine naturwissenschaftlich haltbare Aussage? Begründe mit Fachwissen, warum die Behauptung stimmt oder nicht.
     Lösung: Die Behauptung ist naturwissenschaftlich nicht haltbar. Eine Wiese wächst innerhalb weniger Wochen nach, weil nur die oberirdischen Pflanzenteile entfernt wurden und Wurzeln sowie Bodenleben intakt bleiben. Fruchtbarer Boden dagegen entsteht durch jahrzehnte- bis jahrhundertelange Verwitterungs- un…
  6. [structure_overview · apply] Auf einem Bio-Bauernhof werden Felder abwechselnd mit verschiedenen Pflanzen bepflanzt (Fruchtwechsel) statt jedes Jahr dieselbe Pflanze anzubauen. Wende dein Wissen über Bodenleben an: Erstelle eine kurze Übersicht, welche Vorteile diese Methode für den Boden hat.
     Lösung: Fruchtwechsel verhindert, dass immer dieselben Nährstoffe einseitig verbraucht werden, da unterschiedliche Pflanzen unterschiedliche Nährstoffmengen und -arten benötigen. Manche Pflanzen (z. B. Klee, Bohnen) reichern den Boden sogar mit Stickstoff an. Zusätzlich werden Schädlinge und Krankheitserre…
  … + 1 weitere Aufgaben

### block `c0178.i1` — „Boden wirkt auf den ersten Blick unspannend – graubraune Erde eben. Tatsächlich leben in einer einzigen Handvoll gesunder Erde Milliarden vo“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0179.i1` — „Kohlenstoff wandert ständig zwischen Atmosphäre, Pflanzen, Ozeanen und Böden – ein natürlicher Kreislauf, der seit Jahrmillionen läuft: Pfla“ (Biologie und Umweltbildung, 4. Kl. · Stufe voll)

### block `c0178.t1` — „Beobachte die Abbildung/Beschreibung einer Bodenprobe mit Regenwurm, Pilzfäden und Wurzelresten. Trage für jeden Bestandteil ein, ob er ein “ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0178.t4` — „Ordne jeder menschlichen Einwirkung auf den Boden die passende Folge zu.“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0178.t5` — „Ein Mitschüler behauptet: 'Zerstörter Boden erholt sich genauso schnell wieder wie eine gemähte Wiese nachwächst.' Prüfe diese Behauptung wi“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0179.t1` — „Der Kohlenstoffkreislauf besteht aus mehreren Stationen und Vorgängen, die Kohlenstoff (in Form von CO2 oder gebundenem Kohlenstoff) zwische“ (Biologie und Umweltbildung, 4. Kl. · Stufe voll)

### block `c0179.t2` — „Hier sind acht Vorgänge, bei denen CO2 in die Atmosphäre gelangt oder aus ihr entfernt wird:
(1) Ein Waldbrand nach einem Blitzeinschlag · (“ (Biologie und Umweltbildung, 4. Kl. · Stufe voll)

### block `c0178.t6` — „Eine Gemeinde plant, ein letztes großes Wiesenstück am Ortsrand für einen neuen Supermarkt-Parkplatz zu versiegeln. Erstelle eine begründete“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0178.t7` — „Auf einem Bio-Bauernhof werden Felder abwechselnd mit verschiedenen Pflanzen bepflanzt (Fruchtwechsel) statt jedes Jahr dieselbe Pflanze anz“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0179.t3` — „Beurteile für jede Aussage, ob sie naturwissenschaftlich fachlich korrekt argumentiert (R) oder nicht (F) ist, und begründe kurz.“ (Biologie und Umweltbildung, 4. Kl. · Stufe voll)

### block `c0179.t4` — „Vier Aussagen zum Klimawandel stehen links, drei Einordnungen rechts. Ordne jeder Aussage die passende Einordnung zu (eine Einordnung kann m“ (Biologie und Umweltbildung, 4. Kl. · Stufe voll)

### block `c0178.t2` — „Erkläre, warum eine Pflanze auf völlig totem, sterilem Sand deutlich schlechter wächst als auf lebendigem Gartenboden, obwohl beide 'fest' u“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0178.t3` — „Das Diagramm zeigt, wie viele Regenwürmer je Quadratmeter je nach Bodennutzung leben. Beschreibe den Zusammenhang zwischen Nutzungsart und R“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0179.t6` — „In der Einleitung wurde der Kohlenstoffkreislauf als Modell mit wenigen Stationen (Atmosphäre, Pflanzen, Tiere, Böden, Ozeane) und wenigen V“ (Biologie und Umweltbildung, 4. Kl. · Stufe voll)

### block `c0179.t7` — „Deine Schule möchte den CO2-Ausstoß der Schulgemeinschaft senken und bittet die 4. Klassen um einen begründeten Vorschlag. Du hast in dieser“ (Biologie und Umweltbildung, 4. Kl. · Stufe voll)

### item `c0176` — „Biologie und Umweltbildung 3. Kl. — Angepasst ans Wasser – Leben in Bach, See und Meer (generiert)“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)
- Kernfrage: Wie schaffen es Tiere, im Wasser zu leben – und was passiert, wenn wir Menschen ihren Lebensraum verändern?
- Aufgaben:
  1. [table_fill · remember] Betrachte eine Forelle, eine Ente und einen Frosch. Trage in die Tabelle ein, welches Körpermerkmal jedes Tier fürs Schwimmen nutzt und wozu es dient.
     Lösung: Forelle: Stromlinienform + Flossen – gleiten mit wenig Widerstand durchs Wasser. Ente: Schwimmhäute zwischen den Zehen – vergrößern die Fläche beim Rudern. Frosch: lange, kräftige Hinterbeine mit Schwimmhäuten – Antrieb durch kräftiges Abstoßen.
  2. [open_response · understand] Ein Fisch hat eine stromlinienförmige Körperform, ein Krokodil dagegen einen eher flachen, breiten Körper – beide leben im Wasser. Erkläre, warum trotzdem beide Formen im Wasser funktionieren.
     Lösung: Die Stromlinienform des Fisches verringert den Wasserwiderstand beim schnellen, dauerhaften Schwimmen. Das Krokodil bewegt sich meist langsam an der Oberfläche oder lauert bewegungslos; sein flacher Körper hält es dabei stabil im Gleichgewicht und lässt nur Augen und Nase aus dem Wasser ragen. Beid…
  3. [data_interpretation · analyze] Sieh dir das Diagramm zum Sauerstoffgehalt verschiedener Gewässer an. Welches Gewässer bietet sauerstoffliebenden Tieren wie der Bachforelle die besten Bedingungen, und welches am wenigsten? Begründe mit den Werten.
     Lösung: Der Gebirgsbach bietet mit rund 11,2 mg/l den höchsten Sauerstoffgehalt – am besten für die Bachforelle, die viel Sauerstoff braucht. Der stehende Teich hat mit rund 5,1 mg/l den niedrigsten Wert – dort würde die Forelle kaum überleben, nur sauerstoffarme Tiere sind angepasst.
  4. [open_response · apply] Frösche legen ihren Laich (Eier) direkt ins Wasser, wo er sich frei entwickelt – ganz anders als z. B. ein Vogelei im geschützten Nest. Stelle eine begründete Vermutung auf: Warum legen viele Wassertiere sehr viel mehr Eier als Landtiere mit Brutpflege?
     Lösung: Frosch-Laich wird nicht bewacht oder gewärmt, deshalb fressen viele Fressfeinde die Eier oder Kaulquappen, und viele überleben Trockenheit oder Strömung nicht. Je mehr Eier ein Tier legt, desto größer ist die Chance, dass trotz hoher Verluste einige wenige Nachkommen überleben und sich fortpflanzen…
  5. [decision_scenario · evaluate] Eine Gemeinde will einen naturnahen Bach begradigen und betonieren, um Hochwasser schneller abzuleiten. Nimm Stellung: Welche Auswirkungen hätte das auf die Wasserlebewesen, und würdest du dieser Maßnahme zustimmen? Begründe fachlich.
     Lösung: Eine Betonierung entfernt Steine, Pflanzen und Kurven, die Verstecke und Laichplätze bieten; das Wasser fließt schneller und gleichförmiger, wodurch Sauerstoffverwirbelung und Lebensraumvielfalt sinken. Viele Tierarten (Insektenlarven, Forellen) würden verschwinden. Eine fundierte Stellungnahme wäg…
  6. [create_produce · create] Entwirf ein kurzes Info-Plakat (Stichworte + Skizze) mit dem Titel 'Mein Lieblings-Wassertier', das mindestens zwei Körpermerkmale zeigt und erklärt, wie sie beim Leben im Wasser helfen.
     Lösung: Individuelle Lösung. Ein gutes Plakat nennt das Tier, zeigt (auch als einfache Skizze) mindestens zwei Anpassungsmerkmale und erklärt in eigenen Worten kurz und fachlich richtig, wozu jedes Merkmal dient.
  … + 1 weitere Aufgaben

### item `c0177` — „Biologie und Umweltbildung 3. Kl. — Sauerstoff unterwegs – Atmung und Blutkreislauf (generiert)“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)
- Kernfrage: Wie kommt der Sauerstoff, den du einatmest, bis in deine Zehenspitzen?
- Aufgaben:
  1. [matching · remember] Ordne jedem Tier sein passendes Atmungsorgan zu.
     Lösung: Forelle – Kiemen; Grille – Tracheen; Mensch – Lunge; Regenwurm – Haut (Hautatmung).
  2. [open_response · understand] Kiemen, Tracheen und Lunge sehen sehr unterschiedlich aus. Erkläre, was diese drei Atmungsorgane trotzdem gemeinsam haben müssen, damit Sauerstoff überhaupt aufgenommen werden kann.
     Lösung: Alle drei besitzen eine große, dünne und feuchte Oberfläche, durch die Sauerstoff leicht hindurchtreten (diffundieren) kann. Bei Kiemen und Lunge liegen zusätzlich feine Blutgefäße direkt an dieser Oberfläche, die den Sauerstoff sofort aufnehmen und weitertransportieren.
  3. [data_interpretation · analyze] Das Diagramm zeigt den Puls einer Person vor, während und nach dem Treppensteigen. Beschreibe den Verlauf und erkläre, warum das Herz während der Anstrengung schneller schlägt.
     Lösung: Der Puls steigt von rund 72 auf einen Höchstwert von etwa 150 Schlägen pro Minute an, bleibt kurz hoch und sinkt danach langsam wieder Richtung Ruhewert. Während der Anstrengung verbrauchen die Muskeln deutlich mehr Sauerstoff und produzieren mehr Kohlenstoffdioxid; das Herz schlägt schneller, um m…
  4. [experiment_protocol · apply] Plane eine einfache Untersuchung: Wie verändert sich dein eigener Puls durch 1 Minute Kniebeugen? Halte fest, was du misst, wie oft, und welches Ergebnis du erwartest (Hypothese), bevor du misst.
     Lösung: Ein vollständiges Protokoll enthält: (1) Ruhepuls messen (15 Sekunden zählen × 4), (2) 1 Minute Kniebeugen durchführen, (3) sofort danach erneut den Puls messen, (4) Hypothese vorab formulieren, z. B. 'Ich erwarte, dass der Puls nach den Kniebeugen deutlich höher ist als der Ruhepuls', und die Wert…
  5. [true_false_justify · understand] Beurteile die folgenden Aussagen und begründe jeweils kurz, warum sie richtig oder falsch sind.
     Lösung: Aussage 1 ist falsch: sauerstoffarmes Blut fließt vom Herzen ZUR Lunge, sauerstoffreiches Blut fließt von der Lunge ZURÜCK zum Herzen und wird von dort in den Körper gepumpt. Aussage 2 ist richtig: Der rote Blutfarbstoff Hämoglobin bindet Sauerstoff und färbt sauerstoffreiches Blut hellrot.
  6. [decision_scenario · evaluate] Ein Mitschüler sagt: 'Rauchen betrifft nur meine eigene Lunge, das geht niemand anderen etwas an.' Nimm dazu begründet Stellung und beziehe dabei die Wirkung auf Lunge UND Blutkreislauf mit ein.
     Lösung: Rauchen schädigt die feinen, dünnen Oberflächen der Lungenbläschen und verringert dadurch dauerhaft die Sauerstoffaufnahme; das belastet auch das Herz, das stärker pumpen muss, um den Körper trotzdem ausreichend zu versorgen. Zusätzlich betrifft Passivrauch auch andere Personen in der Nähe – die Au…

### block `c0176.i1` — „Ob klarer Gebirgsbach, stiller See oder das offene Meer – überall im Wasser haben sich Tiere an ihre besonderen Lebensbedingungen angepasst.“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0177.i1` — „Fische atmen mit Kiemen, Insekten mit Tracheen, wir Menschen mit einer Lunge – aber am Ende geht es bei allen um dasselbe: Sauerstoff muss d“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0176.t1` — „Betrachte eine Forelle, eine Ente und einen Frosch. Trage in die Tabelle ein, welches Körpermerkmal jedes Tier fürs Schwimmen nutzt und wozu“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0176.t3` — „Sieh dir das Diagramm zum Sauerstoffgehalt verschiedener Gewässer an. Welches Gewässer bietet sauerstoffliebenden Tieren wie der Bachforelle“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0176.t4` — „Frösche legen ihren Laich (Eier) direkt ins Wasser, wo er sich frei entwickelt – ganz anders als z. B. ein Vogelei im geschützten Nest. Stel“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0177.t3` — „Das Diagramm zeigt den Puls einer Person vor, während und nach dem Treppensteigen. Beschreibe den Verlauf und erkläre, warum das Herz währen“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0177.t4` — „Plane eine einfache Untersuchung: Wie verändert sich dein eigener Puls durch 1 Minute Kniebeugen? Halte fest, was du misst, wie oft, und wel“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0176.t5` — „Eine Gemeinde will einen naturnahen Bach begradigen und betonieren, um Hochwasser schneller abzuleiten. Nimm Stellung: Welche Auswirkungen h“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0176.t7` — „Zwei Mitschüler:innen diskutieren: 'Fische können im Wasser atmen, weil sie ans Wasser gewöhnt sind.' – 'Nein, das liegt an ihren Kiemen.' B“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0177.t6` — „Ein Mitschüler sagt: 'Rauchen betrifft nur meine eigene Lunge, das geht niemand anderen etwas an.' Nimm dazu begründet Stellung und beziehe “ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0176.t2` — „Ein Fisch hat eine stromlinienförmige Körperform, ein Krokodil dagegen einen eher flachen, breiten Körper – beide leben im Wasser. Erkläre, “ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0176.t6` — „Entwirf ein kurzes Info-Plakat (Stichworte + Skizze) mit dem Titel 'Mein Lieblings-Wassertier', das mindestens zwei Körpermerkmale zeigt und“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0177.t1` — „Ordne jedem Tier sein passendes Atmungsorgan zu.“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0177.t2` — „Kiemen, Tracheen und Lunge sehen sehr unterschiedlich aus. Erkläre, was diese drei Atmungsorgane trotzdem gemeinsam haben müssen, damit Saue“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### block `c0177.t5` — „Beurteile die folgenden Aussagen und begründe jeweils kurz, warum sie richtig oder falsch sind.“ (Biologie und Umweltbildung, 3. Kl. · Stufe voll)

### item `c0174` — „Biologie und Umweltbildung 2. Kl. — Wie das Gehirn aus Reizen eine Welt macht (generiert)“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)
- Kernfrage: Warum können sich zwei Menschen bei gleichem Reiz auf unterschiedliche Wahrnehmungen einigen – oder auch nicht?
- Aufgaben:
  1. [content_comprehension · understand] Erkläre in eigenen Worten den Unterschied zwischen 'einen Reiz aufnehmen' und 'einen Reiz wahrnehmen'. Nenne dazu ein Beispiel mit dem Auge.
     Lösung: Das Auge nimmt den Lichtreiz auf (die Sinneszelle wandelt Licht in ein elektrisches Signal um). Wahrnehmen bedeutet: Das Gehirn verarbeitet dieses Signal, vergleicht es mit Erfahrungen und macht daraus ein bewusstes Bild. Beispiel: Das Auge nimmt Lichtwellen einer roten Ampel auf, aber erst das Geh…
  2. [matching · remember] Ordne jedes Sinnesorgan der Reizart zu, die es hauptsächlich aufnimmt.
     Lösung: Auge → Lichtreize. Ohr → Schallwellen. Haut → Druck, Temperatur, Schmerz. Nase → Duftstoffe (chemisch). Zunge → Geschmacksstoffe (chemisch).
  3. [data_interpretation · analyze] Betrachte das Diagramm zu den Reaktionszeiten. Auf welchen Reiz reagieren Menschen im Schnitt am langsamsten, auf welchen am schnellsten? Formuliere eine mögliche Erklärung, warum das so sein könnte.
     Lösung: Am langsamsten: Sehreiz (ca. 190 ms). Am schnellsten: Tastreiz (ca. 155 ms). Mögliche Erklärung: Ein Lichtsignal muss vom Auge über den Sehnerv einen längeren Weg zu den zuständigen Hirnbereichen zurücklegen und dort stärker verarbeitet werden (Bildererkennung), während ein Tastreiz von der Haut üb…
  4. [create_produce · create] Entwirf ein einfaches Modell (Skizze mit Beschriftung), das zeigt, wie ein Reiz vom Sinnesorgan bis zur bewussten Wahrnehmung im Gehirn 'wandert'. Nutze Pfeile und mindestens vier Stationen (z.B. Reiz, Sinneszelle, Nerv, Gehirn).
     Lösung: Eine vollständige Skizze enthält mindestens: 1) Reiz (z.B. Lichtwelle) → 2) Sinnesorgan/Sinneszelle (z.B. Auge, Sehzelle) → 3) Nervenbahn (z.B. Sehnerv) → 4) Gehirn (Verarbeitung, z.B. Sehrinde) → bewusste Wahrnehmung. Pfeile zeigen die Reihenfolge, Beschriftungen benennen jede Station korrekt.
  5. [true_false_justify · understand] Beurteile: Wenn zwei Personen dieselbe optische Täuschung unterschiedlich beschreiben, muss eine der beiden 'falsch sehen' bzw. ein krankes Auge haben. Richtig oder falsch – begründe.
     Lösung: Falsch. Optische Täuschungen entstehen, weil das Gehirn Erfahrungswissen und Interpretationsregeln nutzt, um aus mehrdeutigen Signalen ein Bild zu konstruieren – das ist bei gesunden Augen normal und sagt nichts über einen Sehfehler aus.
  6. [source_critique · evaluate] Ein Werbevideo behauptet: 'Unser neues Konzentrationsgetränk verdoppelt sofort die Reaktionsgeschwindigkeit deines Gehirns – wissenschaftlich bewiesen!' Prüfe diese Aussage kritisch: Welche Informationen fehlen, um sie naturwissenschaftlich beurteilen zu können?
     Lösung: Es fehlen u.a.: Wer hat das untersucht (unabhängige Studie oder nur die Firma selbst)? Wie viele Personen wurden getestet? Wurde mit einer Kontrollgruppe (ohne Getränk) verglichen? Wie wurde 'Reaktionsgeschwindigkeit' überhaupt gemessen? Eine Verdopplung ist ein sehr extremer Wert, der besonders kr…
  … + 1 weitere Aufgaben

### item `c0175` — „Biologie und Umweltbildung 2. Kl. — Pilze – die heimlichen Netzwerker des Waldes (generiert)“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)
- Kernfrage: Wie kann ein Pilz einem Baum beim Überleben helfen, obwohl er selbst keine Fotosynthese betreibt?
- Aufgaben:
  1. [structure_overview · remember] Benenne die zwei Hauptbestandteile eines Pilzes und beschreibe kurz, welche Aufgabe jeder Teil hat: den Fruchtkörper (das, was man oberirdisch sieht, z.B. beim Steinpilz) und das Myzel (das unterirdische Fadengeflecht).
     Lösung: Fruchtkörper: dient der Fortpflanzung, bildet und verbreitet die Sporen (die 'Samen' der Pilze). Myzel: das eigentliche, meist unsichtbare Fadengeflecht im Boden oder Holz, nimmt Wasser und Nährstoffe auf und kann sehr groß und alt werden.
  2. [content_comprehension · understand] Betrachte das Diagramm zu den geschätzten Pilzarten nach Lebensweise. Welche Lebensweise ist demnach am häufigsten? Erkläre, was 'saprophytisch' bedeutet.
     Lösung: Am häufigsten ist die saprophytische (zersetzende) Lebensweise mit geschätzt 70.000 Arten. Saprophytisch bedeutet, dass der Pilz sich von totem organischem Material ernährt (z.B. abgestorbenem Holz, Laub) und es dabei zersetzt – er ist also ein 'Recycler' im Ökosystem.
  3. [cause_effect_match · analyze] Ordne jeder Pilz-Lebensweise die passende Beschreibung der Beziehung zu anderen Lebewesen zu.
     Lösung: Symbiontisch → beide Partner profitieren voneinander. Parasitisch → der Pilz schadet einem lebenden Wirt zu seinem eigenen Vorteil. Saprophytisch → der Pilz ernährt sich von totem Material.
  4. [experiment_protocol · apply] Du willst untersuchen, ob Mykorrhiza-Pilze das Wachstum junger Bäume tatsächlich fördern. Skizziere einen einfachen Versuchsaufbau mit zwei Gruppen von Baumsetzlingen, der diese Frage prüfen könnte.
     Lösung: Zwei möglichst gleiche Gruppen junger Baumsetzlinge (gleiche Art, gleiches Alter, gleicher Boden, gleicher Standort, gleiche Wassermenge) werden gebildet. Gruppe A erhält Erde mit Mykorrhiza-Pilzen (z.B. aus Waldboden geimpft), Gruppe B (Kontrollgruppe) erhält sterile bzw. pilzfreie Erde. Nach eini…
  5. [create_produce · create] Zeichne ein einfaches Modell einer Mykorrhiza-Symbiose zwischen einer Baumwurzel und einem Pilz-Myzel. Beschrifte, was der Baum dem Pilz gibt und was der Pilz dem Baum gibt.
     Lösung: Ein vollständiges Modell zeigt eine Baumwurzel, die von Pilzfäden (Myzel) umgeben bzw. durchzogen ist, mit zwei beschrifteten Pfeilen: Baum → Pilz: Zucker (Traubenzucker aus der Fotosynthese). Pilz → Baum: Wasser und Mineralstoffe (z.B. Phosphat, Stickstoff), die der Pilz mit seinem feinen Fadengef…
  6. [true_false_justify · remember] Beurteile die folgende Aussage als richtig oder falsch und begründe: 'Pilze sind eine besondere Art von Pflanzen, weil sie im Boden wachsen und nicht weglaufen können.'
     Lösung: Falsch. Pilze bilden ein eigenes biologisches Reich, das weder zu den Pflanzen noch zu den Tieren gehört. Anders als Pflanzen betreiben sie keine Fotosynthese und haben keine Zellwände aus Zellulose, sondern aus Chitin (wie auch Insektenpanzer).
  … + 1 weitere Aufgaben

### block `c0174.intro1` — „Deine Augen, Ohren, deine Haut und deine Nase liefern ständig Signale – aber erst dein Gehirn macht daraus eine Wahrnehmung. Manchmal täusch“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.intro1` — „Wenn du an einen Pilz denkst, siehst du wahrscheinlich einen Fruchtkörper wie einen Steinpilz vor dir. Doch das ist nur die 'Spitze des Eisb“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0174.t2` — „Ordne jedes Sinnesorgan der Reizart zu, die es hauptsächlich aufnimmt.“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0174.t3` — „Betrachte das Diagramm zu den Reaktionszeiten. Auf welchen Reiz reagieren Menschen im Schnitt am langsamsten, auf welchen am schnellsten? Fo“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0174.t4` — „Entwirf ein einfaches Modell (Skizze mit Beschriftung), das zeigt, wie ein Reiz vom Sinnesorgan bis zur bewussten Wahrnehmung im Gehirn 'wan“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.t2` — „Betrachte das Diagramm zu den geschätzten Pilzarten nach Lebensweise. Welche Lebensweise ist demnach am häufigsten? Erkläre, was 'saprophyti“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.t3` — „Ordne jeder Pilz-Lebensweise die passende Beschreibung der Beziehung zu anderen Lebewesen zu.“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.t4` — „Du willst untersuchen, ob Mykorrhiza-Pilze das Wachstum junger Bäume tatsächlich fördern. Skizziere einen einfachen Versuchsaufbau mit zwei “ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0174.t5` — „Beurteile: Wenn zwei Personen dieselbe optische Täuschung unterschiedlich beschreiben, muss eine der beiden 'falsch sehen' bzw. ein krankes “ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0174.t6` — „Ein Werbevideo behauptet: 'Unser neues Konzentrationsgetränk verdoppelt sofort die Reaktionsgeschwindigkeit deines Gehirns – wissenschaftlic“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0174.t7` — „Formuliere eine Handlungsempfehlung für Jugendliche zum Thema Kopfhörer-Nutzung, basierend auf dem, was du über Sinnesorgane gelernt hast.“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.t6` — „Beurteile die folgende Aussage als richtig oder falsch und begründe: 'Pilze sind eine besondere Art von Pflanzen, weil sie im Boden wachsen “ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.t7` — „Beim Waldspaziergang entdeckt eine Gruppe Jugendlicher ein großes Pilzgeflecht (Myzel) unter der Laubstreu, als sie nach Stöcken graben. Ers“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0174.t1` — „Erkläre in eigenen Worten den Unterschied zwischen 'einen Reiz aufnehmen' und 'einen Reiz wahrnehmen'. Nenne dazu ein Beispiel mit dem Auge.“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.t1` — „Benenne die zwei Hauptbestandteile eines Pilzes und beschreibe kurz, welche Aufgabe jeder Teil hat: den Fruchtkörper (das, was man oberirdis“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0175.t5` — „Zeichne ein einfaches Modell einer Mykorrhiza-Symbiose zwischen einer Baumwurzel und einem Pilz-Myzel. Beschrifte, was der Baum dem Pilz gib“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### item `c0172` — „Biologie und Umweltbildung 1. Kl. — Gebaut fürs Wasser, gebaut für die Luft: Wirbeltiere im Vergleich (generiert)“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)
- Kernfrage: Was verrät der Körperbau eines Tieres über seinen Lebensraum – und was bedeutet das für unsere Verantwortung als Halter:innen?
- Aufgaben:
  1. [table_fill · remember] Fülle die Tabelle aus: Trage für Fisch, Frosch und Vogel jeweils ein typisches Merkmal ein, das zeigt, wie der Körper an den Lebensraum angepasst ist.
     Lösung: Fisch – Wasser – Flossen zum Schwimmen, Kiemen zur Sauerstoffaufnahme aus dem Wasser. Frosch – Wasser und Land – Schwimmhäute an den Hinterbeinen, Haut zur zusätzlichen Atmung. Vogel – Luft/Land – Flügel und leichte, hohle Knochen zum Fliegen, Federn zur Isolierung.
  2. [content_comprehension · understand] Fisch, Frosch, Eidechse, Vogel und Hund gehören alle zu den Wirbeltieren. Sie haben eine Wirbelsäule und meistens zwei Paar Gliedmaßen (Flossen, Beine oder Flügel) – auch wenn diese sehr unterschiedlich aussehen und genutzt werden. Erkläre, warum Biolog:innen einen Fisch und einen Vogel trotz ihres…
     Lösung: Beide teilen den gleichen Grundbauplan der Wirbeltiere: eine Wirbelsäule als Innenskelett und zwei Paar Gliedmaßen (bei Fisch: Flossenpaare, bei Vogel: Flügel und Beine). Das ähnliche äußere Aussehen ist nicht entscheidend – die gemeinsame innere Bauplan-Struktur zeigt die Verwandtschaft.
  3. [true_false_justify · understand] Ein Tierarzt sagt: 'Fakten kann man überprüfen, Meinungen nicht.' Lies die vier Aussagen über Haustierhaltung. Kreuze bei jeder an, ob sie eine überprüfbare Tatsache oder eine persönliche Meinung ist.
     Lösung: 1 ja (beobachtbar/messbar über Verhalten und Tierarztdaten) · 2 nein (persönlicher Geschmack, keine messbare Größe) · 3 ja (anatomisch/tierärztlich belegbar, z. B. Atemfrequenz, Tierarztbefunde) · 4 nein (Werthaltung/Meinung, nicht naturwissenschaftlich prüfbar).
  4. [matching · apply] Ordne jedem Körpermerkmal den passenden Vorteil im jeweiligen Lebensraum zu.
     Lösung: Hohle Knochen → geringeres Gewicht erleichtert das Fliegen. Schwimmhäute → größere Fläche verbessert den Vortrieb beim Schwimmen. Seitenlinienorgan → erkennt Wasserbewegungen und Beute auch bei schlechter Sicht. Dichtes Fell → hält Körperwärme in kalter Umgebung besser zurück.
  5. [create_produce · apply] Schreibe einen kurzen Steckbrief-Text (5–6 Sätze) für eine Tierheim-Broschüre, der zukünftigen Hundehalter:innen verantwortungsvolles Handeln nahelegt: Nenne mindestens zwei konkrete Bedürfnisse eines Hundes (z. B. Bewegung, Beschäftigung, tierärztliche Versorgung) und erkläre jeweils kurz, warum d…
     Lösung: Erwarteter Text nennt mindestens zwei konkrete, fachlich richtige Bedürfnisse (z. B. ausreichend Bewegung passend zur Rasse, geistige Beschäftigung, regelmäßige tierärztliche Kontrollen, artgerechte Ernährung) mit je einer kurzen, sachlich richtigen Begründung, warum ein Nichterfüllen dem Tier scha…
  6. [data_interpretation · analyze] Das Balkendiagramm zeigt die Anzahl der Extremitätenpaare (Flossen/Beine/Flügel-Beinpaar) bei fünf Wirbeltieren. Was fällt dir auf, wenn du die Werte vergleichst? Was zeigt dieses Ergebnis über die Verwandtschaft dieser fünf sehr unterschiedlich aussehenden Tiere?
     Lösung: Alle fünf Tiere haben denselben Wert: 2 Paar Gliedmaßen (Flossen, Beinpaare bzw. Flügel+Beine). Trotz sehr unterschiedlichem Aussehen und Lebensraum zeigt dieser gemeinsame Grundwert den gemeinsamen Bauplan der Wirbeltiere – ein Beleg für ihre Verwandtschaft.
  … + 1 weitere Aufgaben

### item `c0173` — „Biologie und Umweltbildung 2. Kl. — Der Wald als Lebensgemeinschaft (generiert)“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)
- Kernfrage: Warum ist ein artenreicher Wald stabiler als eine Fichten-Monokultur?
- Aufgaben:
  1. [structure_overview · remember] Ein Wald besteht aus mehreren übereinanderliegenden Schichten. Ordne die vier Waldschichten von unten nach oben: Strauchschicht, Baumschicht, Kraut- und Moosschicht, Wurzel- und Bodenschicht.
     Lösung: Von unten nach oben: 1) Wurzel- und Bodenschicht, 2) Kraut- und Moosschicht, 3) Strauchschicht, 4) Baumschicht.
  2. [content_comprehension · understand] Betrachte das Diagramm 'Baumartenanteile in zwei österreichischen Waldtypen'. Wie viele verschiedene Baumarten wurden auf der Testfläche in der Fichten-Monokultur gezählt, wie viele im naturnahen Mischwald? Erkläre in eigenen Worten, was der Unterschied über die beiden Waldtypen aussagt.
     Lösung: Monokultur: 1 Baumart (nur Fichte). Mischwald: 7 Baumarten. Der Mischwald bietet also viel mehr unterschiedliche Lebensräume und Nahrungsquellen als die Monokultur, die nur aus einer einzigen Baumart besteht.
  3. [experiment_protocol · apply] Plane eine einfache Untersuchung: Du willst herausfinden, ob es auf einer 1x1-Meter-Fläche im Wald mehr verschiedene Pflanzenarten gibt als auf einer 1x1-Meter-Fläche auf einer Wiese. Beschreibe in Stichworten: Was brauchst du, was zählst du, wie hältst du die Ergebnisse fest?
     Lösung: Materialien: Maßband oder Schnur (1x1 m abstecken), Bestimmungsbuch/App, Stift, Protokollblatt. Vorgehen: Fläche abstecken, jede sichtbare Pflanzenart notieren und zählen (auch wenn eine Art mehrfach vorkommt, nur einmal in der Artenliste), Ergebnisse in einer Tabelle festhalten (Artname, Anzahl de…
  4. [cause_effect_match · analyze] Ordne jede Ursache der passenden Folge für das Wald-Ökosystem zu.
     Lösung: Fichten-Monokultur → weniger ökologische Nischen, geringere Artenvielfalt. Trockener Sommer bei geschwächten Fichten → Borkenkäfer vermehrt sich stark. Absterben eines alten Baumes im Mischwald → neuer Lebensraum für Pilze, Insekten, höhlenbrütende Vögel.
  5. [true_false_justify · apply] Beurteile die folgenden Aussagen zum Wald-Ökosystem als richtig oder falsch und begründe deine Entscheidung jeweils in einem Satz.
     Lösung: 1) Falsch – Totholz ist Lebensraum für Pilze, Insekten und Höhlenbrüter und sollte im Wald bleiben. 2) Richtig – Vielfalt bedeutet mehr 'Ausweichmöglichkeiten', wenn eine Art ausfällt oder bedroht ist. 3) Falsch – Fichten-Monokulturen wurden vor allem wegen des schnellen Wachstums und der wirtschaf…
  6. [decision_scenario · evaluate] Eine Gemeinde besitzt ein Waldstück und muss entscheiden, wie es in den nächsten Jahren bewirtschaftet werden soll. Nimm Stellung zu folgendem Szenario und begründe deine Empfehlung fachlich.
     Lösung: Eine fachlich fundierte Empfehlung nennt: Mischwald ist widerstandsfähiger gegen Klimawandel, Trockenheit und Borkenkäfer (siehe t1-t4); Monokultur bringt zwar schnelleren, aber riskanteren Ertrag. Eine gute Antwort wägt Ertragszeitpunkt gegen Ausfallrisiko ab und empfiehlt in der Regel Option B, k…
  … + 1 weitere Aufgaben

### block `c0173.intro1` — „Ein Wald ist mehr als eine Ansammlung von Bäumen – er ist ein Beziehungsgeflecht aus Pflanzen, Tieren, Pilzen und Boden. In diesem Arbeitsbl“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0172.t2` — „Das Balkendiagramm zeigt die Anzahl der Extremitätenpaare (Flossen/Beine/Flügel-Beinpaar) bei fünf Wirbeltieren. Was fällt dir auf, wenn du “ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0173.t2` — „Betrachte das Diagramm 'Baumartenanteile in zwei österreichischen Waldtypen'. Wie viele verschiedene Baumarten wurden auf der Testfläche in “ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0173.t3` — „Plane eine einfache Untersuchung: Du willst herausfinden, ob es auf einer 1x1-Meter-Fläche im Wald mehr verschiedene Pflanzenarten gibt als “ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0173.t4` — „Ordne jede Ursache der passenden Folge für das Wald-Ökosystem zu.“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0172.t5` — „Ein Tierarzt sagt: 'Fakten kann man überprüfen, Meinungen nicht.' Lies die vier Aussagen über Haustierhaltung. Kreuze bei jeder an, ob sie e“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0172.t6` — „Eine Familie möchte einen Hund anschaffen und hat zwei Rassen zur Auswahl: Rasse A ist sehr aktiv, braucht täglich mehrere Stunden Auslauf; “ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0172.t7` — „Schreibe einen kurzen Steckbrief-Text (5–6 Sätze) für eine Tierheim-Broschüre, der zukünftigen Hundehalter:innen verantwortungsvolles Handel“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0173.t5` — „Beurteile die folgenden Aussagen zum Wald-Ökosystem als richtig oder falsch und begründe deine Entscheidung jeweils in einem Satz.“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0173.t6` — „Eine Gemeinde besitzt ein Waldstück und muss entscheiden, wie es in den nächsten Jahren bewirtschaftet werden soll. Nimm Stellung zu folgend“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0172.t1` — „Fisch, Frosch, Eidechse, Vogel und Hund gehören alle zu den Wirbeltieren. Sie haben eine Wirbelsäule und meistens zwei Paar Gliedmaßen (Flos“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0172.t3` — „Fülle die Tabelle aus: Trage für Fisch, Frosch und Vogel jeweils ein typisches Merkmal ein, das zeigt, wie der Körper an den Lebensraum ange“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0172.t4` — „Ordne jedem Körpermerkmal den passenden Vorteil im jeweiligen Lebensraum zu.“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0173.t1` — „Ein Wald besteht aus mehreren übereinanderliegenden Schichten. Ordne die vier Waldschichten von unten nach oben: Strauchschicht, Baumschicht“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### block `c0173.t7` — „Übertrage die Werte aus dem Diagramm 'Baumartenanteile in zwei österreichischen Waldtypen' in eine Tabelle mit den Spalten 'Waldtyp' und 'An“ (Biologie und Umweltbildung, 2. Kl. · Stufe voll)

### item `c0170` — „Biologie und Umweltbildung 1. Kl. — Wer braucht wen? Der Teich als Lebensraum (generiert)“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)
- Kernfrage: Wie hängen die Lebewesen in einem Teich voneinander ab?
- Aufgaben:
  1. [content_comprehension · understand] Ein Teich sieht auf den ersten Blick ruhig aus, aber es passiert ständig etwas: Algen und Wasserpflanzen wachsen im Licht, kleine Krebstiere und Kaulquappen fressen Algen, Libellenlarven und Fische fressen die Krebstiere, und Frösche und Vögel fressen wiederum kleine Fische oder Insekten. Stirbt ei…
     Lösung: Ein Beziehungsnetz, weil jedes Lebewesen von anderen abhängt: Pflanzen liefern Nahrung und Sauerstoff, kleine Tiere fressen Pflanzen, größere Tiere fressen kleinere. Fällt eine Gruppe aus, fehlt Nahrung für die nächste Stufe oder es gibt zu viele Tiere einer anderen Stufe – der ganze Teich veränder…
  2. [multiple_choice · understand] Eine Mitschülerin will herausfinden, ob Frösche lieber im Schatten oder in der Sonne sitzen. Welche der folgenden Fragen ist eine gute naturwissenschaftliche Frage, die man durch Beobachtung tatsächlich beantworten kann?
     Lösung: Richtig ist Option 2 ('An wie vielen von 20 beobachteten Tagen...'): Sie ist konkret, zählbar und durch Beobachtung überprüfbar. Die anderen Fragen fragen nach Gefühlen, Schönheit oder persönlicher Meinung – das lässt sich nicht durch Beobachtung der Natur beantworten.
  3. [cause_effect_match · apply] Ordne jeder Ursache die passende Folge im Teich zu.
     Lösung: Trockener Sommer → weniger Lebensraum am Ufer, Pflanzen/Tiere sterben. Dünger im Wasser → Algen wachsen stark, Wasser trüb. Fische entnommen → Beutetiere (Kaulquappen) vermehren sich stärker. Bäume gefällt → mehr Sonne, Temperatur steigt.
  4. [data_interpretation · evaluate] Das Diagramm zeigt, wie oft eure Klasse verschiedene Tiergruppen bei einer 30-minütigen Beobachtung am Teichrand gesehen hat. Welche Tiergruppe wurde am häufigsten gesichtet? Beurteile dann: Wie verlässlich ist diese Beobachtungsmethode, um zu sagen, welches Tier am Teich WIRKLICH am häufigsten vor…
     Lösung: Am häufigsten gesichtet: Wasserläufer (14). Beobachtung ≠ tatsächliche Häufigkeit: kleine, schnelle oder gut versteckte Tiere (z. B. Fische unter Wasser, Frösche im Schilf) werden leicht unterschätzt; auffällige, sich viel bewegende Tiere (Wasserläufer an der Oberfläche) werden überschätzt. Auch Ta…
  5. [experiment_protocol · apply] Plane eine einfache Beobachtung: Du willst herausfinden, ob am Teich mehr Tiere am Vormittag oder am Nachmittag aktiv sind. Notiere: (a) welche Tiergruppen du zählst, (b) wie lange du jeweils beobachtest, (c) was du gleich hältst, damit der Vergleich fair ist (z. B. gleiche Stelle, gleiches Wetter).
     Lösung: Beispielprotokoll: (a) dieselben Tiergruppen wie in t3 zählen; (b) z. B. je 20 Minuten Vormittag und Nachmittag; (c) gleiche Beobachtungsstelle, ähnliches Wetter, gleiche Beobachtungsperson/Methode – damit nur die Tageszeit als Unterschied bleibt (faire, kontrollierte Beobachtung).
  6. [decision_scenario · evaluate] Eine Gemeinde will einen kleinen Teich zuschütten, um dort einen Parkplatz zu bauen. Ein anderer Vorschlag ist, den Parkplatz 50 Meter weiter auf einer bereits versiegelten Fläche zu bauen. Beurteile beide Vorschläge aus Sicht des Lebensraums Teich und gib eine begründete Empfehlung ab.
     Lösung: Begründete Empfehlung: die versiegelte Fläche nutzen, da der Teich als ganzer Lebensraum (mit vielen voneinander abhängigen Arten) sonst vollständig verloren geht, während die Alternative keinen zusätzlichen Lebensraum zerstört. Ein Parkplatz kann an vielen Stellen entstehen, ein funktionierender T…
  … + 1 weitere Aufgaben

### item `c0171` — „Biologie und Umweltbildung 1. Kl. — Ohne Bienen keine Kirschen? Die Blüte als Werkzeug (generiert)“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)
- Kernfrage: Warum haben Blüten Farben, Duft und Nektar – und was hat das mit Früchten zu tun?
- Aufgaben:
  1. [structure_overview · understand] Eine Blüte hat mehrere Teile mit unterschiedlichen Aufgaben: die Blütenblätter (Krone) fallen durch Farbe auf, die Staubblätter tragen Pollen (männliche Geschlechtszellen), der Stempel mit Narbe und Fruchtknoten enthält die Samenanlagen (weibliche Geschlechtszellen), und Nektarien am Blütengrund pr…
     Lösung: Blütenblätter (Krone): durch Farbe/Form Bestäuber anlocken. Staubblätter: Pollen (männliche Geschlechtszellen) produzieren und anbieten. Stempel (Narbe, Griffel, Fruchtknoten): Pollen auffangen, zu den Samenanlagen leiten, Samenanlagen (weibliche Geschlechtszellen) enthalten. Nektarien: Nektar als …
  2. [open_response · understand] Erkläre den Unterschied zwischen Bestäubung und Befruchtung in eigenen Worten. Verwende dabei die Begriffe 'Pollen', 'Narbe', 'Samenanlage' und 'Verschmelzung'.
     Lösung: Bestäubung: Pollen gelangt auf die Narbe des Stempels (z. B. durch Wind oder Tiere). Befruchtung: Der Pollen bildet einen Schlauch zur Samenanlage, dort verschmelzen männliche und weibliche Zelle – daraus entsteht ein Samen. Bestäubung ist also der Transport, Befruchtung die eigentliche Vereinigung…
  3. [data_interpretation · analyze] Das Diagramm zeigt: Je mehr eine Apfelblüte innerhalb einer Stunde von Bienen besucht wurde, desto häufiger hat sich später eine Frucht gebildet. Beschreibe den Zusammenhang. Erkläre dann mit deinem Wissen über Bestäubung, WARUM mehr Bienenbesuche zu mehr Fruchtansatz führen könnten – und nenne ein…
     Lösung: Zusammenhang: mit steigender Anzahl an Bienenbesuchen steigt der Anteil an Blüten mit Fruchtansatz (von 4 % bei 0 Besuchen auf 81 % bei 6 Besuchen). Erklärung: mehr Besuche bedeuten mehr Gelegenheiten, dass Pollen auf die Narbe gelangt (Bestäubung) und damit auf Befruchtung folgt. Bei 0 Besuchen ka…
  4. [ordering · apply] Bringe die Schritte vom Bienenbesuch bis zur fertigen Frucht in die richtige Reihenfolge.
     Lösung: 1. Eine Biene sammelt Nektar und bleibt dabei Pollen an ihr haften. 2. Die Biene fliegt zu einer anderen Blüte, Pollen bleibt auf der Narbe hängen (Bestäubung). 3. Der Pollenschlauch wächst bis zur Samenanlage, Verschmelzung findet statt (Befruchtung). 4. Ein Same reift im Fruchtknoten heran. 5. De…
  5. [open_response · evaluate] Modell: 'Je mehr Bienenbesuche eine Blüte bekommt, desto sicherer entsteht daraus eine Frucht.' Beurteile dieses Modell: Für welche Pflanzen passt es gut, und nenne EINE Pflanzenart oder Situation, für die dieses Modell NICHT (oder nur schlecht) gilt (z. B. windbestäubte Pflanzen, sich selbst bestä…
     Lösung: —
  6. [experiment_protocol · apply] Ihr wollt untersuchen, ob Apfelblüten ohne Insektenbesuch überhaupt Früchte bilden können. Plant dazu einen einfachen Vergleich: (a) was macht ihr mit einer Blütengruppe, damit KEINE Insekten hinkommen können, (b) welche zweite Blütengruppe braucht ihr zum Vergleich, (c) was zählt ihr am Ende und v…
     Lösung: Beispielprotokoll: (a) Blüten mit einem feinmaschigen Netz oder Stoffbeutel abdecken, sodass Insekten nicht hinkommen; (b) eine gleich große Gruppe unbedeckter Blüten am selben Baum als Vergleich; (c) nach einigen Wochen bei beiden Gruppen zählen, wie viele Blüten Früchte gebildet haben, und die An…
  … + 1 weitere Aufgaben

### block `c0170.t1b` — „Eine Mitschülerin will herausfinden, ob Frösche lieber im Schatten oder in der Sonne sitzen. Welche der folgenden Fragen ist eine gute natur“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0170.t3` — „Das Diagramm zeigt, wie oft eure Klasse verschiedene Tiergruppen bei einer 30-minütigen Beobachtung am Teichrand gesehen hat. Welche Tiergru“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0170.t4` — „Plane eine einfache Beobachtung: Du willst herausfinden, ob am Teich mehr Tiere am Vormittag oder am Nachmittag aktiv sind. Notiere: (a) wel“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0171.t3` — „Das Diagramm zeigt: Je mehr eine Apfelblüte innerhalb einer Stunde von Bienen besucht wurde, desto häufiger hat sich später eine Frucht gebi“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0171.t5` — „Ihr wollt untersuchen, ob Apfelblüten ohne Insektenbesuch überhaupt Früchte bilden können. Plant dazu einen einfachen Vergleich: (a) was mac“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0170.t5` — „Eine Gemeinde will einen kleinen Teich zuschütten, um dort einen Parkplatz zu bauen. Ein anderer Vorschlag ist, den Parkplatz 50 Meter weite“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0170.t6` — „Beurteile: Sind folgende Aussagen über den Teich naturwissenschaftlich überprüfbar oder nicht? Begründe kurz.“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0171.t6` — „Ein Nachbar will in seinem Garten alle 'wilden' Blühpflanzen (z. B. Löwenzahn, Klee) entfernen, damit der Rasen 'ordentlich' aussieht. Schre“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0170.t1` — „Ein Teich sieht auf den ersten Blick ruhig aus, aber es passiert ständig etwas: Algen und Wasserpflanzen wachsen im Licht, kleine Krebstiere“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0170.t2` — „Ordne jeder Ursache die passende Folge im Teich zu.“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0171.t1` — „Eine Blüte hat mehrere Teile mit unterschiedlichen Aufgaben: die Blütenblätter (Krone) fallen durch Farbe auf, die Staubblätter tragen Polle“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0171.t2` — „Erkläre den Unterschied zwischen Bestäubung und Befruchtung in eigenen Worten. Verwende dabei die Begriffe 'Pollen', 'Narbe', 'Samenanlage' “ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0171.t4` — „Bringe die Schritte vom Bienenbesuch bis zur fertigen Frucht in die richtige Reihenfolge.“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### block `c0171.t4b` — „Modell: 'Je mehr Bienenbesuche eine Blüte bekommt, desto sicherer entsteht daraus eine Frucht.' Beurteile dieses Modell: Für welche Pflanzen“ (Biologie und Umweltbildung, 1. Kl. · Stufe voll)

### item `c0179` — „Biologie und Umweltbildung 4. Kl. — Der Kohlenstoffkreislauf aus dem Takt — CO2, Klimawandel und was Daten zeigen (generiert)“ (Biologie und Umweltbildung, 4. Kl. · Stufe quelle)
- Kernfrage: Wie verändert der Mensch den natürlichen Kohlenstoffkreislauf, und woran erkennst du eine seriöse Aussage zum Klimawandel?
- Aufgaben:
  1. [structure_overview · understand] Der Kohlenstoffkreislauf besteht aus mehreren Stationen und Vorgängen, die Kohlenstoff (in Form von CO2 oder gebundenem Kohlenstoff) zwischen ihnen bewegen: Atmosphäre, Pflanzen, Tiere/Menschen, Böden, Ozeane. Die Vorgänge dazwischen sind: Fotosynthese, Atmung (Zellatmung), Verwesung/Zersetzung, Ve…
     Lösung: Beispielweg: CO2 in der Atmosphäre → wird von einer Pflanze bei der Fotosynthese aufgenommen und in Zucker/Biomasse gebunden → die Pflanze wird von einem Tier gefressen, der Kohlenstoff geht in dessen Körper über → das Tier atmet (Zellatmung) einen Teil als CO2 wieder in die Atmosphäre aus, oder es…
  2. [table_fill · understand] Hier sind acht Vorgänge, bei denen CO2 in die Atmosphäre gelangt oder aus ihr entfernt wird: (1) Ein Waldbrand nach einem Blitzeinschlag · (2) Ein Kohlekraftwerk erzeugt Strom · (3) Ein Baum wächst und bildet neues Holz · (4) Ein Vulkan bricht aus · (5) Ein Auto fährt mit Benzin · (6) Der Ozean nim…
     Lösung: Natürlich: (1) Waldbrand durch Blitzeinschlag, (3) Baumwachstum (Senke), (4) Vulkanausbruch, (6) CO2-Aufnahme im Ozean (Senke), (7) Verdauung der Kuh. Menschgemacht: (2) Kohlekraftwerk, (5) Auto mit Benzin, (8) Flugzeugflug.
  3. [true_false_justify · understand] Beurteile für jede Aussage, ob sie naturwissenschaftlich fachlich korrekt argumentiert (R) oder nicht (F) ist, und begründe kurz.
     Lösung: 1 – R: Das ist eine überprüfbare, datenbasierte Aussage (Messstationen, Zeitreihe, reproduzierbar). 2 – F: Das verwechselt lokales, kurzfristiges WETTER (ein einzelner Wintertag) mit langfristigem, globalem KLIMA (Durchschnitt über Jahrzehnte) — ein einzelnes kaltes Ereignis widerlegt keinen langfr…
  4. [matching · understand] Vier Aussagen zum Klimawandel stehen links, drei Einordnungen rechts. Ordne jeder Aussage die passende Einordnung zu (eine Einordnung kann mehrfach passen).
     Lösung: 1 → A (Satellitenmessungen, Zeitreihe seit 1993). 2 → B (keine Belege, reine Meinungsäußerung). 3 → A (mehrere unabhängige Institute, Messreihe seit 1900). 4 → C (das Klima hat sich in der Erdgeschichte tatsächlich verändert, aber die AKTUELLE Erwärmung läuft geologisch gesehen extrem schnell und i…
  5. [data_interpretation · apply] Die Grafik zeigt den CO2-Ausstoß pro Kopf und Jahr für acht Länder (Datenquelle: World Bank). (a) Nenne das Land mit dem höchsten und das Land mit dem niedrigsten Pro-Kopf-Ausstoß. Berechne, um das Wievielfache der höhere Wert über dem niedrigeren liegt. (b) Vergleiche Österreich mit Indien: Beschr…
     Lösung: (a) Höchster Wert: USA mit 13,6 t CO2/Kopf. Niedrigster Wert: Nigeria mit 0,6 t CO2/Kopf. Das Wievielfache: 13,6 : 0,6 ≈ 22,7-fach (also rund 23-mal so hoch). (b) Österreich liegt bei 6,3 t CO2/Kopf, Indien bei 2,2 t CO2/Kopf — Österreich stößt somit knapp dreimal so viel CO2 pro Kopf aus wie Indie…
  6. [open_response · evaluate] In der Einleitung wurde der Kohlenstoffkreislauf als Modell mit wenigen Stationen (Atmosphäre, Pflanzen, Tiere, Böden, Ozeane) und wenigen Vorgängen (Fotosynthese, Atmung, Verwesung, Verbrennung, Lösung im Wasser) beschrieben. (a) Nenne zwei Dinge, die dieses vereinfachte Modell GUT erklären kann. …
     Lösung: (a) Das Modell erklärt gut: den grundsätzlichen Weg des Kohlenstoffs zwischen Lebewesen, Luft und Boden (z. B. warum Pflanzen wichtig für die CO2-Bindung sind); warum das Verbrennen fossiler Rohstoffe den Kreislauf aus dem Gleichgewicht bringt (weil dabei 'alter', lange gespeicherter Kohlenstoff pl…
  … + 1 weitere Aufgaben

### block `c0179.t5` — „Die Grafik zeigt den CO2-Ausstoß pro Kopf und Jahr für acht Länder (Datenquelle: World Bank).

(a) Nenne das Land mit dem höchsten und das L“ (Biologie und Umweltbildung, 4. Kl. · Stufe quelle)
